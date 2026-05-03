from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.bioinformatics.project_analysis_tasks import create_analysis_task, load_analysis_task_center
from app.bioinformatics.project_readiness import load_readiness_artifacts, run_project_readiness
from app.bioinformatics.project_recognition import TYPE_LABELS, load_recognition_report, run_project_recognition
from app.bioinformatics.project_standardization import generate_standardized_assets, load_standardization_artifacts
from app.bioinformatics.project_workflow_orchestrator import load_workflow_state, run_project_stage, run_project_workflow
from app.bioinformatics.project_workspace import create_bioinformatics_project
from app.bioinformatics.project_workspace_binding import (
    generate_gse_acquisition_plan,
    load_latest_acquisition_summary,
    read_acquisition_artifacts,
    register_acquisition,
)
from app.bioinformatics.reports.project_report_builder import generate_project_report, load_project_report
from app.bioinformatics.results.project_results import load_result_index, write_result_index


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    return create_bioinformatics_project("Workflow Adapter Project", tmp_path).project_root


def test_acquisition_binding_generates_plan_record_handoff(project_root: Path, tmp_path: Path) -> None:
    source = tmp_path / "expression_matrix.tsv"
    source.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")

    summary = register_acquisition(
        project_root,
        source_type="local_import",
        source_label="本地表达矩阵",
        strategy="reference",
        selected_paths=[source],
    )

    assert summary.strategy == "reference"
    assert summary.record_path.exists()
    assert summary.handoff_path.exists()
    assert summary.referenced_paths == (str(source.resolve()),)
    artifacts = read_acquisition_artifacts(project_root)
    assert artifacts["record"]["strategy"] == "reference"  # type: ignore[index]


def test_gse_acquisition_plan_is_plan_only(project_root: Path) -> None:
    summary = generate_gse_acquisition_plan(project_root, "GSE33630")

    assert summary.strategy == "plan_only"
    assert summary.source_type == "geo_gse"
    assert load_latest_acquisition_summary(project_root).source_label == "GSE33630"  # type: ignore[union-attr]
    assert read_acquisition_artifacts(project_root)["record"]["strategy"] == "plan_only"  # type: ignore[index]


def test_plan_only_project_is_not_ready(project_root: Path) -> None:
    generate_gse_acquisition_plan(project_root, "GSE33630")
    run_project_recognition(project_root)

    readiness = run_project_readiness(project_root)
    report = readiness["readiness_report"]  # type: ignore[index]
    matrix_rows = readiness["capability_matrix"]["rows"]  # type: ignore[index]

    assert report["overall_status"] == "not_ready"
    assert report["has_core_input"] is False
    assert not any(row["analysis_type"] == "reporting" and row["can_run"] for row in matrix_rows)


def test_recognition_readiness_standardization_chain(project_root: Path) -> None:
    raw_file = project_root / "raw_data" / "local_import" / "expression_matrix.tsv"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")

    recognition = run_project_recognition(project_root)
    assert load_recognition_report(project_root) is not None
    assert recognition["files"][0]["recognized_type"] == "expression_matrix"  # type: ignore[index]
    assert TYPE_LABELS["unknown"] == "未知文件"

    readiness = run_project_readiness(project_root)
    matrix_rows = readiness["capability_matrix"]["rows"]  # type: ignore[index]
    assert any(row["label"] == "差异表达分析" for row in matrix_rows)
    assert load_readiness_artifacts(project_root)["readiness_report"] is not None

    standardization = generate_standardized_assets(project_root)
    assert "不等于正式 biological normalization" in standardization["registry"]["warnings"][0]  # type: ignore[index]
    assert load_standardization_artifacts(project_root)["registry"] is not None


def test_workflow_and_task_center_do_not_run_analysis(project_root: Path) -> None:
    raw_file = project_root / "raw_data" / "local_import" / "expression_matrix.tsv"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")
    run_project_recognition(project_root)
    run_project_readiness(project_root)

    stage = run_project_stage(project_root, "task_center")
    assert stage["status"] in {"completed", "completed_with_warnings"}

    center = load_analysis_task_center(project_root)
    assert center["tasks"]
    with pytest.raises(ValueError, match="缺失输入"):
        create_analysis_task(project_root, "differential_expression")

    state = run_project_workflow(project_root)
    assert load_workflow_state(project_root) is not None
    assert state["steps"]


def test_result_and_report_adapters(project_root: Path) -> None:
    missing_result = project_root / "results" / "tables" / "missing.tsv"
    write_result_index(
        project_root,
        [
            {
                "result_name": "Missing table",
                "analysis_type": "preview",
                "file_type": "tsv",
                "path": str(missing_result),
                "status": "created",
            }
        ],
    )
    results = load_result_index(project_root)
    assert "结果文件缺失" in results["warnings"][0]  # type: ignore[index]

    payload = generate_project_report(project_root)
    assert Path(str(payload["markdown_path"])).exists()
    report = load_project_report(project_root)
    assert "PDF" in json.dumps(report["manifest"], ensure_ascii=False)
