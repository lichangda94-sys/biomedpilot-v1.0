from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.pages.survival_page import initial_survival_state
from app.bioinformatics.services.survival_service import SurvivalService
from app.shared.data_center.service import DataCenter
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature
from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType


def make_service(tmp_path) -> tuple[SurvivalService, TaskCenter, DataCenter]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = SurvivalService(
        task_center=task_center,
        data_center=data_center,
        storage_root=tmp_path,
    )
    return service, task_center, data_center


def write_cleaning_plan(tmp_path: Path, *, metadata_files: list[str], survival_fields: list[str] | None = None) -> Path:
    path = tmp_path / "geo_cleaning_plan.json"
    payload = {
        "project_id": "bio-test",
        "cleaning_executed": False,
        "cleaning_items": [
            {
                "accession": "GSE1001",
                "expression_files": ["counts.tsv"],
                "metadata_files": metadata_files,
                "survival_fields": survival_fields or [],
                "status": "ready_for_cleaning",
                "next_action": "Run controlled normalization after confirming matrix format.",
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_survival_rejects_empty_path(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    result = service.create_preflight(project_id="bio-test", cleaning_plan_path="")
    assert not result.success
    assert "请选择" in result.message
    assert task_center.list_tasks()[0].status is TaskStatus.FAILED
    assert data_center.list_assets() == []


def test_survival_rejects_missing_file(tmp_path) -> None:
    service, task_center, _data_center = make_service(tmp_path)
    result = service.create_preflight(project_id="bio-test", cleaning_plan_path=str(tmp_path / "missing.json"))
    assert not result.success
    assert "不存在" in result.message
    assert task_center.list_tasks()[0].task_type is TaskType.ANALYSIS


def test_survival_rejects_non_json(tmp_path) -> None:
    source = tmp_path / "cleaning.txt"
    source.write_text("not json", encoding="utf-8")
    service, _task_center, _data_center = make_service(tmp_path)
    result = service.create_preflight(project_id="bio-test", cleaning_plan_path=str(source))
    assert not result.success
    assert "JSON" in result.message


def test_survival_blocks_without_survival_fields(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    source = write_cleaning_plan(tmp_path, metadata_files=["clinical.tsv"])
    result = service.create_preflight(project_id="bio-test", cleaning_plan_path=str(source))
    assert result.success
    assert result.ready_for_survival_count == 0
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert payload["survival_analysis_executed"] is False
    assert payload["preflight_items"][0]["status"] == "blocked_no_survival_fields"
    task = task_center.list_tasks()[0]
    assert task.status is TaskStatus.COMPLETED
    assert task.task_type is TaskType.ANALYSIS
    assert any(asset.data_type == "geo_survival_preflight" for asset in data_center.list_assets("bio-test"))


def test_survival_marks_ready_with_time_and_event_fields(tmp_path) -> None:
    service, _task_center, _data_center = make_service(tmp_path)
    source = write_cleaning_plan(tmp_path, metadata_files=["clinical.tsv"], survival_fields=["os_time_days", "vital_status"])
    result = service.create_preflight(project_id="bio-test", cleaning_plan_path=str(source))
    assert result.success
    assert result.ready_for_survival_count == 1
    assert result.details["survival_analysis_executed"] is False
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert payload["network_used"] is False
    assert payload["preflight_items"][0]["status"] == "ready_for_survival_setup"


def test_survival_feature_status_and_page_state() -> None:
    feature = get_feature("bio-survival")
    assert feature is not None
    assert feature.status is FeatureAvailabilityStatus.TESTING
    assert "不计算 Kaplan-Meier" in feature.description
    state = initial_survival_state()
    assert state.title == "生存分析"
    assert state.status_label == "测试中"
