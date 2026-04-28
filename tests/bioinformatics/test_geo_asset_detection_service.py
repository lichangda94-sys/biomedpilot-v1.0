from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.pages.geo_asset_detection_page import initial_geo_asset_detection_state
from app.bioinformatics.services.geo_asset_detection_service import GeoAssetDetectionService
from app.shared.data_center.service import DataCenter
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature
from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType


def make_service(tmp_path) -> tuple[GeoAssetDetectionService, TaskCenter, DataCenter]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = GeoAssetDetectionService(
        task_center=task_center,
        data_center=data_center,
        storage_root=tmp_path,
    )
    return service, task_center, data_center


def write_download_plan(tmp_path: Path, *, target_dir: Path) -> Path:
    path = tmp_path / "geo_download_plan.json"
    payload = {
        "project_id": "bio-test",
        "download_executed": False,
        "download_items": [
            {
                "accession": "GSE1001",
                "target_dir": str(target_dir),
                "status": "planned",
                "note": "Download not executed.",
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_geo_asset_detection_rejects_empty_path(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    result = service.detect_assets(project_id="bio-test", geo_download_plan_path="")
    assert not result.success
    assert "请选择" in result.message
    assert task_center.list_tasks()[0].status is TaskStatus.FAILED
    assert data_center.list_assets() == []


def test_geo_asset_detection_rejects_missing_file(tmp_path) -> None:
    service, task_center, _data_center = make_service(tmp_path)
    result = service.detect_assets(project_id="bio-test", geo_download_plan_path=str(tmp_path / "missing.json"))
    assert not result.success
    assert "不存在" in result.message
    assert task_center.list_tasks()[0].task_type is TaskType.PREPROCESS


def test_geo_asset_detection_rejects_non_json(tmp_path) -> None:
    source = tmp_path / "download.txt"
    source.write_text("not json", encoding="utf-8")
    service, _task_center, _data_center = make_service(tmp_path)
    result = service.detect_assets(project_id="bio-test", geo_download_plan_path=str(source))
    assert not result.success
    assert "JSON" in result.message


def test_geo_asset_detection_handles_missing_local_target_without_network(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    source = write_download_plan(tmp_path, target_dir=tmp_path / "does-not-exist")
    result = service.detect_assets(project_id="bio-test", geo_download_plan_path=str(source))
    assert result.success
    assert result.dataset_count == 1
    assert result.ready_dataset_count == 0
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert payload["network_used"] is False
    detection = payload["detections"][0]
    assert detection["accession"] == "GSE1001"
    assert detection["has_expression_payload"] is False
    task = task_center.list_tasks()[0]
    assert task.status is TaskStatus.COMPLETED
    assert task.task_type is TaskType.PREPROCESS
    assert any(asset.data_type == "geo_asset_detection" for asset in data_center.list_assets("bio-test"))


def test_geo_asset_detection_scans_local_expression_file(tmp_path) -> None:
    dataset_dir = tmp_path / "GSE1001"
    dataset_dir.mkdir()
    (dataset_dir / "counts.tsv").write_text(
        "gene_id\tGSM1\tGSM2\nENSG1\t10\t20\nENSG2\t30\t40\n",
        encoding="utf-8",
    )
    source = write_download_plan(tmp_path, target_dir=dataset_dir)
    service, _task_center, _data_center = make_service(tmp_path)
    result = service.detect_assets(project_id="bio-test", geo_download_plan_path=str(source))
    assert result.success
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    detection = payload["detections"][0]
    assert detection["scan_root"] == str(dataset_dir.resolve())
    assert detection["candidate_expression_files"]
    assert detection["has_expression_payload"] is True


def test_geo_asset_detection_feature_status_and_page_state() -> None:
    feature = get_feature("bio-asset-detection")
    assert feature is not None
    assert feature.status is FeatureAvailabilityStatus.TESTING
    assert "不联网" in feature.description
    state = initial_geo_asset_detection_state()
    assert state.title == "数据资产识别"
    assert state.status_label == "测试中"
