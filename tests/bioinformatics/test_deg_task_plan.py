from __future__ import annotations

from pathlib import Path

from app.bioinformatics.comparison_config import ComparisonSampleAssignment, build_comparison_config_text, comparison_config_path
from app.bioinformatics.deg_task_plan import DEG_PREFLIGHT_MANIFEST, build_deg_preflight, load_deg_preflight_manifest
from app.bioinformatics.project_recognition import run_project_recognition
from app.bioinformatics.project_standardization import generate_standardized_assets
from app.bioinformatics.project_workspace import create_bioinformatics_project
from app.bioinformatics.project_workspace_binding import register_acquisition


def _project_root(tmp_path: Path) -> Path:
    return create_bioinformatics_project("B2 DEG Preflight", tmp_path).project_root


def _write_comparison_config(project_root: Path) -> None:
    text = build_comparison_config_text(
        comparison_id="case_vs_control",
        group_column="group",
        case_group="case",
        control_group="control",
        assignments=(
            ComparisonSampleAssignment("case_1", "case"),
            ComparisonSampleAssignment("case_2", "case"),
            ComparisonSampleAssignment("control_1", "control"),
            ComparisonSampleAssignment("control_2", "control"),
        ),
    )
    path = comparison_config_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_deg_preflight_passes_with_expression_and_confirmed_comparison(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path)
    expression_file = tmp_path / "counts_matrix.tsv"
    expression_file.write_text(
        "gene\tcase_1\tcase_2\tcontrol_1\tcontrol_2\n"
        "TP53\t10\t12\t2\t3\n"
        "EGFR\t4\t5\t9\t10\n",
        encoding="utf-8",
    )
    register_acquisition(
        project_root,
        source_type="local_import",
        source_label="counts",
        strategy="reference",
        selected_paths=[expression_file],
    )
    _write_comparison_config(project_root)
    run_project_recognition(project_root)
    generate_standardized_assets(project_root)

    result = build_deg_preflight(project_root)

    assert result.status == "passed"
    assert result.manifest["semantic_boundary"] == "input_preflight_only_not_deg_result"
    assert result.manifest["execution"] == "not_run"
    assert result.manifest["not_a_result"] is True
    assert (project_root / DEG_PREFLIGHT_MANIFEST).is_file()
    assert not (project_root / "results" / "tables").exists()
    loaded = load_deg_preflight_manifest(project_root)
    assert loaded is not None
    assert loaded["status"] == "passed"


def test_deg_preflight_blocks_missing_group_and_does_not_use_imported_deg_as_input(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path)
    imported_deg = tmp_path / "imported_deg_results.csv"
    imported_deg.write_text("gene,logFC,P.Value,adj.P.Val\nTP53,1.2,0.01,0.05\n", encoding="utf-8")
    register_acquisition(
        project_root,
        source_type="local_import",
        source_label="imported DEG",
        strategy="reference",
        selected_paths=[imported_deg],
    )
    run_project_recognition(project_root)
    generate_standardized_assets(project_root)

    result = build_deg_preflight(project_root)

    assert result.status == "blocked"
    assert result.manifest["input_summary"]["imported_deg_detected"] is True  # type: ignore[index]
    assert any("缺 count matrix" in item for item in result.manifest["blockers"])  # type: ignore[index]
    assert any("导入差异结果不能作为重新计算 DEG" in item for item in result.manifest["warnings"])  # type: ignore[index]
    assert not (project_root / "results" / "tables").exists()
