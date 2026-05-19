from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.analysis_task_runs import create_deg_task_run, load_analysis_task_run
from app.bioinformatics.deg_executor_preflight import run_deg_executor_preflight
from app.bioinformatics.deg_task_plan import save_deg_task_plan
from app.bioinformatics.group_comparison_design import load_group_design_context, save_group_comparison_design
from app.bioinformatics.project_recognition import run_project_recognition
from app.bioinformatics.project_standardization import generate_standardized_assets
from app.bioinformatics.project_workspace import create_bioinformatics_project


def _write_integrated_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "gene_id,A1_count,A2_count,B1_count,B2_count,A1_fpkm,A2_fpkm,B1_fpkm,B2_fpkm,PFFvsPBS_log2FoldChange,PFFvsPBS_pvalue,PFFvsPBS_padj,gene_name",
                "ENSMUSG00000026193,10,11,20,21,1.1,1.2,2.1,2.2,1.5,0.01,0.04,Sox17",
                "ENSMUSG00000064351,30,31,18,17,3.1,3.2,1.8,1.7,-1.6,0.02,0.03,mt-Nd1",
            ]
        ),
        encoding="utf-8",
    )


def _prepare_project(tmp_path: Path) -> Path:
    project = create_bioinformatics_project("DEG Preflight Project", tmp_path).project_root
    _write_integrated_csv(project / "raw_data" / "local_import" / "integrated.csv")
    run_project_recognition(project)
    generate_standardized_assets(project)
    context = load_group_design_context(project)
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
        project,
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
    save_deg_task_plan(project)
    return project


def test_deg_executor_preflight_materializes_inputs_without_results(tmp_path: Path) -> None:
    project = _prepare_project(tmp_path)
    run = create_deg_task_run(project)

    payload = run_deg_executor_preflight(project, task_run_id=str(run["run_id"]))

    assert payload["status"] == "passed_with_warnings"
    assert payload["not_run"] is True
    count_matrix = Path(str(payload["count_matrix_path"]))
    sample_design = Path(str(payload["sample_design_path"]))
    comparisons = Path(str(payload["comparison_design_path"]))
    assert count_matrix.exists()
    assert sample_design.exists()
    assert comparisons.exists()
    assert "gene_id\tA1\tA2\tB1\tB2" in count_matrix.read_text(encoding="utf-8")
    assert "PFF_vs_PBS\tPFF\tPBS" in comparisons.read_text(encoding="utf-8")
    assert not (project / "results" / "summaries" / "result_index.json").exists()

    loaded = load_analysis_task_run(project, "deg", str(run["run_id"]))
    assert loaded is not None
    assert loaded["status"] == "skipped_dry_run"
    assert loaded["deg_preflight_manifest"]["status"] == "passed_with_warnings"  # type: ignore[index]
    assert "executor_preflight.json" in loaded["deg_preflight_manifest"]["path"]  # type: ignore[index]


def test_deg_executor_preflight_fails_without_task_run(tmp_path: Path) -> None:
    project = create_bioinformatics_project("No Run", tmp_path).project_root

    payload = run_deg_executor_preflight(project)

    assert payload["status"] == "failed"
    assert "未找到 DEG 任务记录" in json.dumps(payload, ensure_ascii=False)
