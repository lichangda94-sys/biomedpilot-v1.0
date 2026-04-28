from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.pages.sample_grouping_page import initial_sample_grouping_state
from app.bioinformatics.services.sample_grouping_service import SampleGroupingService
from app.shared.data_center.service import DataCenter
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature
from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType


def make_service(tmp_path) -> tuple[SampleGroupingService, TaskCenter, DataCenter]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = SampleGroupingService(
        task_center=task_center,
        data_center=data_center,
        storage_root=tmp_path,
    )
    return service, task_center, data_center


def write_cleaning_plan(tmp_path: Path, *, metadata_files: list[str], expression_files: list[str] | None = None) -> Path:
    path = tmp_path / "geo_cleaning_plan.json"
    payload = {
        "project_id": "bio-test",
        "cleaning_executed": False,
        "cleaning_items": [
            {
                "accession": "GSE1001",
                "expression_files": expression_files if expression_files is not None else ["counts.tsv"],
                "metadata_files": metadata_files,
                "status": "ready_for_cleaning",
                "next_action": "Run controlled normalization after confirming matrix format.",
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_sample_grouping_rejects_empty_path(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    result = service.create_grouping_plan(project_id="bio-test", cleaning_plan_path="")
    assert not result.success
    assert "请选择" in result.message
    assert task_center.list_tasks()[0].status is TaskStatus.FAILED
    assert data_center.list_assets() == []


def test_sample_grouping_rejects_missing_file(tmp_path) -> None:
    service, task_center, _data_center = make_service(tmp_path)
    result = service.create_grouping_plan(project_id="bio-test", cleaning_plan_path=str(tmp_path / "missing.json"))
    assert not result.success
    assert "不存在" in result.message
    assert task_center.list_tasks()[0].task_type is TaskType.PREPROCESS


def test_sample_grouping_rejects_non_json(tmp_path) -> None:
    source = tmp_path / "cleaning.txt"
    source.write_text("not json", encoding="utf-8")
    service, _task_center, _data_center = make_service(tmp_path)
    result = service.create_grouping_plan(project_id="bio-test", cleaning_plan_path=str(source))
    assert not result.success
    assert "JSON" in result.message


def test_sample_grouping_creates_ready_plan(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    source = write_cleaning_plan(tmp_path, metadata_files=["sample_annotation.tsv"])
    result = service.create_grouping_plan(project_id="bio-test", cleaning_plan_path=str(source))
    assert result.success
    assert result.ready_for_grouping_count == 1
    assert result.details["grouping_executed"] is False
    assert result.details["group_inference_executed"] is False
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert payload["grouping_executed"] is False
    assert payload["group_inference_executed"] is False
    assert payload["grouping_items"][0]["status"] == "ready_for_manual_grouping"
    assert payload["grouping_items"][0]["expression_files"] == ["counts.tsv"]
    task = task_center.list_tasks()[0]
    assert task.status is TaskStatus.COMPLETED
    assert task.task_type is TaskType.PREPROCESS
    assert any(asset.data_type == "geo_sample_grouping_plan" for asset in data_center.list_assets("bio-test"))


def test_sample_grouping_blocks_without_sample_annotation(tmp_path) -> None:
    service, _task_center, _data_center = make_service(tmp_path)
    source = write_cleaning_plan(tmp_path, metadata_files=[])
    result = service.create_grouping_plan(project_id="bio-test", cleaning_plan_path=str(source))
    assert result.success
    assert result.ready_for_grouping_count == 0
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert payload["grouping_items"][0]["status"] == "blocked_no_sample_annotation"


def test_sample_grouping_feature_status_and_page_state() -> None:
    feature = get_feature("bio-sample-groups")
    assert feature is not None
    assert feature.status is FeatureAvailabilityStatus.TESTING
    assert "样本分组预检" in feature.description
    state = initial_sample_grouping_state()
    assert state.title == "样本分组"
    assert state.status_label == "测试中"
