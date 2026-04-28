from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.pages.geo_cleaning_page import initial_geo_cleaning_state
from app.bioinformatics.services.geo_cleaning_service import GeoCleaningService
from app.shared.data_center.service import DataCenter
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature
from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType


def make_service(tmp_path) -> tuple[GeoCleaningService, TaskCenter, DataCenter]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = GeoCleaningService(
        task_center=task_center,
        data_center=data_center,
        storage_root=tmp_path,
    )
    return service, task_center, data_center


def write_asset_detection(tmp_path: Path, *, expression_files: list[str]) -> Path:
    path = tmp_path / "asset_detection.json"
    payload = {
        "project_id": "bio-test",
        "network_used": False,
        "detections": [
            {
                "accession": "GSE1001",
                "scan_root": str(tmp_path / "GSE1001"),
                "validation_status": "EXPRESSION_ONLY" if expression_files else "EMPTY_OR_BROKEN",
                "recommended_strategy": "SERIES_MATRIX_FIRST",
                "has_expression_payload": bool(expression_files),
                "has_sample_annotation": False,
                "candidate_expression_files": expression_files,
                "candidate_metadata_files": [],
                "warnings": [],
                "errors": [],
                "next_action": "",
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_geo_cleaning_rejects_empty_path(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    result = service.create_cleaning_plan(project_id="bio-test", asset_detection_path="")
    assert not result.success
    assert "请选择" in result.message
    assert task_center.list_tasks()[0].status is TaskStatus.FAILED
    assert data_center.list_assets() == []


def test_geo_cleaning_rejects_missing_file(tmp_path) -> None:
    service, task_center, _data_center = make_service(tmp_path)
    result = service.create_cleaning_plan(project_id="bio-test", asset_detection_path=str(tmp_path / "missing.json"))
    assert not result.success
    assert "不存在" in result.message
    assert task_center.list_tasks()[0].task_type is TaskType.PREPROCESS


def test_geo_cleaning_rejects_non_json(tmp_path) -> None:
    source = tmp_path / "asset.txt"
    source.write_text("not json", encoding="utf-8")
    service, _task_center, _data_center = make_service(tmp_path)
    result = service.create_cleaning_plan(project_id="bio-test", asset_detection_path=str(source))
    assert not result.success
    assert "JSON" in result.message


def test_geo_cleaning_creates_ready_plan(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    source = write_asset_detection(tmp_path, expression_files=["counts.tsv"])
    result = service.create_cleaning_plan(project_id="bio-test", asset_detection_path=str(source))
    assert result.success
    assert result.ready_for_cleaning_count == 1
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert payload["cleaning_executed"] is False
    assert payload["cleaning_items"][0]["status"] == "ready_for_cleaning"
    task = task_center.list_tasks()[0]
    assert task.status is TaskStatus.COMPLETED
    assert task.task_type is TaskType.PREPROCESS
    assert any(asset.data_type == "geo_cleaning_plan" for asset in data_center.list_assets("bio-test"))


def test_geo_cleaning_blocks_without_expression_payload(tmp_path) -> None:
    service, _task_center, _data_center = make_service(tmp_path)
    source = write_asset_detection(tmp_path, expression_files=[])
    result = service.create_cleaning_plan(project_id="bio-test", asset_detection_path=str(source))
    assert result.success
    assert result.ready_for_cleaning_count == 0
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert payload["cleaning_items"][0]["status"] == "blocked_no_expression_payload"


def test_geo_cleaning_feature_status_and_page_state() -> None:
    feature = get_feature("bio-cleaning")
    assert feature is not None
    assert feature.status is FeatureAvailabilityStatus.TESTING
    assert "清洗预检计划" in feature.description
    state = initial_geo_cleaning_state()
    assert state.title == "数据清洗"
    assert state.status_label == "测试中"
