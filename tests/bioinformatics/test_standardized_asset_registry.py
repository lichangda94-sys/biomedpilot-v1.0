from __future__ import annotations

import json
from pathlib import Path

import pytest

import app.bioinformatics.project_standardization as project_standardization
from app.bioinformatics.project_analysis_tasks import load_analysis_task_center
from app.bioinformatics.project_recognition import run_project_recognition
from app.bioinformatics.project_standardization import (
    ANALYSIS_READY_MANIFEST,
    DATA_PROCESSING_TASK_PLAN,
    STANDARDIZED_REGISTRY,
    generate_standardized_assets,
)
from app.bioinformatics.project_workflow_orchestrator import run_project_stage
from app.bioinformatics.project_workspace import create_bioinformatics_project


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    return create_bioinformatics_project("Standardized Registry Project", tmp_path).project_root


def _write_integrated_rnaseq_csv(path: Path, *, comparison: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "gene_id,A1_count,A2_count,B1_count,B2_count,A1_fpkm,A2_fpkm,B1_fpkm,B2_fpkm,"
                f"{comparison}_log2FoldChange,{comparison}_pvalue,{comparison}_padj,"
                "gene_name,gene_start,gene_end,gene_biotype,gene_description",
                "ENSMUSG00000026193,10,11,20,21,1.1,1.2,2.1,2.2,1.5,0.01,0.04,"
                "Sox17,4490931,4497354,protein_coding,SRY-box transcription factor 17",
                "ENSMUSG00000064351,30,31,18,17,3.1,3.2,1.8,1.7,-1.6,0.02,0.03,"
                "mt-Nd1,2751,3707,protein_coding,mitochondrially encoded NADH",
            ]
        ),
        encoding="utf-8",
    )
    return path


def test_standardized_asset_ids_are_unique_across_multiple_integrated_files(project_root: Path) -> None:
    first = _write_integrated_rnaseq_csv(project_root / "raw_data" / "local_import" / "integrated_a.csv", comparison="PFFvsPBS")
    second = _write_integrated_rnaseq_csv(project_root / "raw_data" / "local_import" / "integrated_b.csv", comparison="MMP3vsPBS")
    run_project_recognition(project_root)

    standardization = generate_standardized_assets(project_root)
    assets = [asset for asset in standardization["registry"]["assets"] if isinstance(asset, dict)]  # type: ignore[index]
    asset_ids = [str(asset.get("asset_id") or "") for asset in assets]
    by_type: dict[str, list[dict[str, object]]] = {}
    for asset in assets:
        by_type.setdefault(str(asset.get("asset_type") or ""), []).append(asset)

    assert len(asset_ids) == len(set(asset_ids))
    assert len(by_type["count_matrix"]) == 2
    assert len(by_type["normalized_expression_matrix"]) == 2
    assert len(by_type["deg_result_table"]) == 2
    assert len(by_type["gene_annotation"]) == 2
    assert {Path(str(asset.get("source_file") or "")).name for asset in by_type["count_matrix"]} == {first.name, second.name}
    assert [asset["asset_id"] for asset in by_type["count_matrix"]] == ["count_matrix_001", "count_matrix_002"]
    assert [asset["asset_id"] for asset in by_type["deg_result_table"]] == ["deg_results_001", "deg_results_002"]

    capabilities = load_analysis_task_center(project_root)["capabilities"]
    count_capabilities = [
        item
        for item in capabilities  # type: ignore[union-attr]
        if isinstance(item, dict)
        and item.get("task_id") == "differential_expression_recompute"
        and item.get("source_asset_type") == "count_matrix"
    ]
    assert len(count_capabilities) == 2


def test_standardization_manifests_are_written_with_atomic_helper(project_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_integrated_rnaseq_csv(project_root / "raw_data" / "local_import" / "integrated_a.csv", comparison="PFFvsPBS")
    run_project_recognition(project_root)
    original_atomic_write = project_standardization._atomic_write_json
    written_paths: list[Path] = []

    def tracked_atomic_write(path: Path, payload: dict[str, object]) -> None:
        written_paths.append(path)
        original_atomic_write(path, payload)

    monkeypatch.setattr(project_standardization, "_atomic_write_json", tracked_atomic_write)

    generate_standardized_assets(project_root)

    expected = {project_root / STANDARDIZED_REGISTRY, project_root / ANALYSIS_READY_MANIFEST, project_root / DATA_PROCESSING_TASK_PLAN}
    assert set(written_paths) == expected
    for path in expected:
        assert json.loads(path.read_text(encoding="utf-8"))


def test_workflow_orchestrator_standardization_input_points_to_current_run(project_root: Path) -> None:
    _write_integrated_rnaseq_csv(project_root / "raw_data" / "local_import" / "integrated_a.csv", comparison="PFFvsPBS")
    run_project_recognition(project_root)

    stage = run_project_stage(project_root, "standardization")

    input_text = "\n".join(str(item) for item in stage["input"])  # type: ignore[index]
    assert "recognized_data/current.json" in input_text
    assert "logs/recognition/recognition_report.json" not in input_text
