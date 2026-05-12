from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.bioinformatics.analysis_task_runs import (
    ANALYSIS_RUNS_ROOT,
    build_deg_task_run_context,
    create_deg_task_run,
    list_analysis_task_runs,
    load_analysis_task_run,
)
from app.bioinformatics.deg_task_plan import DEG_TASK_PLAN, save_deg_task_plan
from app.bioinformatics.group_comparison_design import load_group_design_context, save_group_comparison_design
from app.bioinformatics.project_analysis_tasks import load_analysis_task_center
from app.bioinformatics.project_recognition import run_project_recognition
from app.bioinformatics.project_standardization import generate_standardized_assets
from app.bioinformatics.project_workspace import create_bioinformatics_project


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    return create_bioinformatics_project("Analysis Task Run Project", tmp_path).project_root


def _write_integrated_csv(path: Path, *, comparison: str = "PFFvsPBS", groups: tuple[str, str] = ("A", "B")) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    left, right = groups
    path.write_text(
        "\n".join(
            [
                f"gene_id,{left}1_count,{left}2_count,{right}1_count,{right}2_count,"
                f"{left}1_fpkm,{left}2_fpkm,{right}1_fpkm,{right}2_fpkm,"
                f"{comparison}_log2FoldChange,{comparison}_pvalue,{comparison}_padj,"
                "gene_name,gene_biotype,gene_description",
                "ENSMUSG00000026193,10,11,20,21,1.1,1.2,2.1,2.2,1.5,0.01,0.04,Sox17,protein_coding,SRY-box transcription factor 17",
                "ENSMUSG00000064351,30,31,18,17,3.1,3.2,1.8,1.7,-1.6,0.02,0.03,mt-Nd1,protein_coding,mitochondrially encoded NADH",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _prepare_project(project_root: Path, *, multiple_count_assets: bool = False) -> None:
    _write_integrated_csv(project_root / "raw_data" / "local_import" / "integrated_a.csv", comparison="PFFvsPBS", groups=("A", "B"))
    if multiple_count_assets:
        _write_integrated_csv(project_root / "raw_data" / "local_import" / "integrated_b.csv", comparison="MMP3vsPBS", groups=("X", "Y"))
    run_project_recognition(project_root)
    generate_standardized_assets(project_root)


def _save_confirmed_design(project_root: Path) -> None:
    context = load_group_design_context(project_root)
    groups = []
    for item in context["sample_groups"]:  # type: ignore[index]
        row = dict(item)
        if row["inferred_group_id"] == "A":
            row["user_group_name"] = "PBS"
            row["group_role"] = "control"
        elif row["inferred_group_id"] == "B":
            row["user_group_name"] = "PFF"
            row["group_role"] = "treatment"
        groups.append(row)
    save_group_comparison_design(
        project_root,
        groups,
        [
            {
                "comparison_name": "PFF_vs_PBS",
                "case_group": "PFF",
                "control_group": "PBS",
                "case_inferred_group_id": "B",
                "control_inferred_group_id": "A",
                "status": "confirmed",
                "source": "user_confirmed",
            }
        ],
    )


def test_create_deg_task_run_from_valid_plan_writes_dry_run_manifest(project_root: Path) -> None:
    _prepare_project(project_root)
    _save_confirmed_design(project_root)
    save_deg_task_plan(project_root)

    payload = create_deg_task_run(project_root)
    run_dir = Path(str(payload["run_dir"]))
    loaded = load_analysis_task_run(project_root, "deg", str(payload["run_id"]))
    history = list_analysis_task_runs(project_root, task_family="deg")
    center = load_analysis_task_center(project_root)
    recompute = next(item for item in center["capabilities"] if item["task_id"] == "differential_expression_recompute")  # type: ignore[index]

    assert payload["schema_version"] == "bioinformatics_analysis_task_run.v1"
    assert payload["status"] == "skipped_dry_run"
    assert payload["execution_mode"] == "dry_run"
    assert payload["source_task_plan"] == "manifests/analysis_tasks/deg_task_plan.json"
    assert payload["source_assets"] == [{"asset_id": "count_matrix_001", "asset_type": "count_matrix", "role": "primary_count_matrix"}]
    assert payload["source_group_design"] == "manifests/group_comparison_design.json"
    assert payload["comparisons"] == [{"comparison_name": "PFF_vs_PBS", "case_group": "PFF", "control_group": "PBS"}]
    assert payload["parameters"] == {"method": "DESeq2", "method_status": "planned_placeholder", "padj_threshold": 0.05, "abs_log2fc_threshold": 1.0}
    assert payload["outputs"] == []
    assert run_dir.is_dir()
    assert (run_dir / "task_run.json").is_file()
    assert (run_dir / "inputs.json").is_file()
    assert (run_dir / "parameters.json").is_file()
    assert json.loads((run_dir / "outputs_manifest.json").read_text(encoding="utf-8"))["outputs"] == []
    assert (run_dir / "logs" / "task.log").is_file()
    assert loaded is not None
    assert history and history[0]["run_id"] == payload["run_id"]
    assert recompute["status"] == "skipped_dry_run"
    assert "尚未执行真实差异表达分析" in recompute["reason"]
    assert not (project_root / "results" / "summaries" / "result_index.json").exists()


def test_deg_task_run_id_is_unique_and_stays_under_allowed_directory(project_root: Path) -> None:
    _prepare_project(project_root)
    _save_confirmed_design(project_root)
    save_deg_task_plan(project_root)

    first = create_deg_task_run(project_root)
    second = create_deg_task_run(project_root)

    assert first["run_id"] != second["run_id"]
    for payload in (first, second):
        run_dir = Path(str(payload["run_dir"])).resolve()
        allowed = (project_root / ANALYSIS_RUNS_ROOT / "deg").resolve()
        assert allowed in run_dir.parents


def test_deg_task_run_requires_existing_plan(project_root: Path) -> None:
    _prepare_project(project_root)
    _save_confirmed_design(project_root)

    context = build_deg_task_run_context(project_root)

    assert "deg_task_plan" in context["missing"]
    with pytest.raises(ValueError, match="请先配置 DEG 分析任务"):
        create_deg_task_run(project_root)


def test_deg_task_run_requires_default_count_asset(project_root: Path) -> None:
    _prepare_project(project_root, multiple_count_assets=True)
    plan_path = project_root / DEG_TASK_PLAN
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        json.dumps(
            {
                "schema_version": "bioinformatics_deg_task_plan.v1",
                "task_type": "differential_expression_recompute",
                "status": "configured_not_run",
                "source_count_asset_id": "count_matrix_001",
                "source_group_design_path": "manifests/group_comparison_design.json",
                "comparisons": [{"comparison_name": "PFF_vs_PBS", "case_group": "PFF", "control_group": "PBS", "status": "selected"}],
                "method": {"name": "DESeq2", "status": "planned_placeholder"},
                "thresholds": {"padj": 0.05, "abs_log2fc": 1.0},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    context = build_deg_task_run_context(project_root)

    assert "default_count_matrix" in context["missing"]
    with pytest.raises(ValueError, match="默认 count matrix"):
        create_deg_task_run(project_root)


def test_deg_task_run_requires_confirmed_group_design(project_root: Path) -> None:
    _prepare_project(project_root)
    plan_path = project_root / DEG_TASK_PLAN
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        json.dumps(
            {
                "schema_version": "bioinformatics_deg_task_plan.v1",
                "task_type": "differential_expression_recompute",
                "status": "configured_not_run",
                "source_count_asset_id": "count_matrix_001",
                "source_group_design_path": "manifests/group_comparison_design.json",
                "comparisons": [{"comparison_name": "PFF_vs_PBS", "case_group": "PFF", "control_group": "PBS", "status": "selected"}],
                "method": {"name": "DESeq2", "status": "planned_placeholder"},
                "thresholds": {"padj": 0.05, "abs_log2fc": 1.0},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    context = build_deg_task_run_context(project_root)

    assert "confirmed_group_design" in context["missing"]
    with pytest.raises(ValueError, match="确认分组与比较设计"):
        create_deg_task_run(project_root)


def test_imported_deg_and_recompute_task_run_remain_separate(project_root: Path) -> None:
    _prepare_project(project_root)
    _save_confirmed_design(project_root)
    save_deg_task_plan(project_root)
    create_deg_task_run(project_root)

    center = load_analysis_task_center(project_root)
    capabilities = {str(item["task_id"]): item for item in center["capabilities"]}  # type: ignore[index]

    assert capabilities["differential_expression_recompute"]["source_asset_type"] == "count_matrix"
    assert capabilities["differential_expression_recompute"]["status"] == "skipped_dry_run"
    assert capabilities["deg_result_browse"]["source_asset_type"] == "deg_result_table"
    assert capabilities["deg_result_browse"]["status"] == "available"
