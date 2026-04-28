from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.pages.differential_expression_page import initial_differential_expression_state
from app.bioinformatics.services.differential_expression_service import DifferentialExpressionService
from app.shared.data_center.service import DataCenter
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature
from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType


def make_service(tmp_path) -> tuple[DifferentialExpressionService, TaskCenter, DataCenter]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = DifferentialExpressionService(
        task_center=task_center,
        data_center=data_center,
        storage_root=tmp_path,
    )
    return service, task_center, data_center


def write_grouping_plan(
    tmp_path: Path,
    *,
    metadata_files: list[str],
    group_assignments: dict[str, str] | None = None,
    expression_files: list[str] | None = None,
) -> Path:
    path = tmp_path / "geo_sample_grouping_plan.json"
    payload = {
        "project_id": "bio-test",
        "grouping_executed": False,
        "group_inference_executed": False,
        "grouping_items": [
            {
                "accession": "GSE1001",
                "expression_files": expression_files if expression_files is not None else ["counts.tsv"],
                "metadata_files": metadata_files,
                "group_assignments": group_assignments or {},
                "status": "ready_for_manual_grouping",
                "next_action": "Review sample annotation columns and assign case/control groups.",
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_differential_expression_rejects_empty_path(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    result = service.create_preflight(project_id="bio-test", sample_grouping_path="")
    assert not result.success
    assert "请选择" in result.message
    assert task_center.list_tasks()[0].status is TaskStatus.FAILED
    assert data_center.list_assets() == []


def test_differential_expression_rejects_missing_file(tmp_path) -> None:
    service, task_center, _data_center = make_service(tmp_path)
    result = service.create_preflight(project_id="bio-test", sample_grouping_path=str(tmp_path / "missing.json"))
    assert not result.success
    assert "不存在" in result.message
    assert task_center.list_tasks()[0].task_type is TaskType.ANALYSIS


def test_differential_expression_rejects_non_json(tmp_path) -> None:
    source = tmp_path / "grouping.txt"
    source.write_text("not json", encoding="utf-8")
    service, _task_center, _data_center = make_service(tmp_path)
    result = service.create_preflight(project_id="bio-test", sample_grouping_path=str(source))
    assert not result.success
    assert "JSON" in result.message


def test_differential_expression_blocks_without_group_assignments(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    source = write_grouping_plan(tmp_path, metadata_files=["sample_annotation.tsv"])
    result = service.create_preflight(project_id="bio-test", sample_grouping_path=str(source))
    assert result.success
    assert result.ready_for_analysis_count == 0
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert payload["formal_deg_executed"] is False
    assert payload["network_used"] is False
    assert payload["preflight_items"][0]["status"] == "blocked_no_group_assignment"
    task = task_center.list_tasks()[0]
    assert task.status is TaskStatus.COMPLETED
    assert task.task_type is TaskType.ANALYSIS
    assert any(asset.data_type == "geo_differential_expression_preflight" for asset in data_center.list_assets("bio-test"))


def test_differential_expression_marks_ready_with_case_control_groups(tmp_path) -> None:
    service, _task_center, _data_center = make_service(tmp_path)
    source = write_grouping_plan(
        tmp_path,
        metadata_files=["sample_annotation.tsv"],
        group_assignments={"GSM1": "case", "GSM2": "control"},
    )
    result = service.create_preflight(project_id="bio-test", sample_grouping_path=str(source))
    assert result.success
    assert result.ready_for_analysis_count == 1
    assert result.details["formal_deg_executed"] is False
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert payload["statistical_engine"] == "not_configured"
    assert payload["preflight_items"][0]["status"] == "ready_for_deg_runner"


def test_differential_expression_feature_status_and_page_state() -> None:
    feature = get_feature("bio-deg")
    assert feature is not None
    assert feature.status is FeatureAvailabilityStatus.TESTING
    assert "不运行正式差异统计" in feature.description
    state = initial_differential_expression_state()
    assert state.title == "差异表达分析"
    assert state.status_label == "测试中"
