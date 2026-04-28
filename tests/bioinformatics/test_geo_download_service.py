from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.pages.geo_download_page import initial_geo_download_state
from app.bioinformatics.services.geo_download_service import GeoDownloadService
from app.shared.data_center.service import DataCenter
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature
from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType


def make_service(tmp_path) -> tuple[GeoDownloadService, TaskCenter, DataCenter]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = GeoDownloadService(
        task_center=task_center,
        data_center=data_center,
        storage_root=tmp_path,
    )
    return service, task_center, data_center


def write_query_plan(tmp_path: Path, *, accessions: list[str]) -> Path:
    path = tmp_path / "geo_query_plan.json"
    payload = {
        "project_id": "bio-test",
        "online_search_executed": False,
        "plan": {
            "query_text": "papillary thyroid carcinoma",
            "full_geo_query": "(papillary thyroid carcinoma) AND GSE[ETYP]",
            "accessions": accessions,
            "max_results": 20,
            "legacy_source": "legacy",
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_geo_download_rejects_empty_path(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    result = service.create_download_plan(project_id="bio-test", geo_query_plan_path="")
    assert not result.success
    assert "请选择" in result.message
    assert task_center.list_tasks()[0].status is TaskStatus.FAILED
    assert data_center.list_assets() == []


def test_geo_download_rejects_missing_file(tmp_path) -> None:
    service, task_center, _data_center = make_service(tmp_path)
    result = service.create_download_plan(project_id="bio-test", geo_query_plan_path=str(tmp_path / "missing.json"))
    assert not result.success
    assert "不存在" in result.message
    assert task_center.list_tasks()[0].task_type is TaskType.DOWNLOAD


def test_geo_download_rejects_non_json(tmp_path) -> None:
    source = tmp_path / "plan.txt"
    source.write_text("not json", encoding="utf-8")
    service, _task_center, _data_center = make_service(tmp_path)
    result = service.create_download_plan(project_id="bio-test", geo_query_plan_path=str(source))
    assert not result.success
    assert "JSON" in result.message


def test_geo_download_creates_plan_without_downloading(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    source = write_query_plan(tmp_path, accessions=["GSE33630", "GSE27155"])
    result = service.create_download_plan(project_id="bio-test", geo_query_plan_path=str(source))
    assert result.success
    assert result.planned_accessions == 2
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert payload["download_executed"] is False
    assert payload["requires_user_confirmation"] is True
    assert payload["download_items"][0]["status"] == "planned"
    task = task_center.list_tasks()[0]
    assert task.status is TaskStatus.COMPLETED
    assert task.task_type is TaskType.DOWNLOAD
    assert any(asset.data_type == "geo_download_plan" for asset in data_center.list_assets("bio-test"))


def test_geo_download_handles_query_plan_without_accessions(tmp_path) -> None:
    service, _task_center, _data_center = make_service(tmp_path)
    source = write_query_plan(tmp_path, accessions=[])
    result = service.create_download_plan(project_id="bio-test", geo_query_plan_path=str(source))
    assert result.success
    assert result.planned_accessions == 0
    assert "没有明确 accession" in result.message


def test_geo_download_feature_status_and_page_state() -> None:
    feature = get_feature("bio-download")
    assert feature is not None
    assert feature.status is FeatureAvailabilityStatus.TESTING
    assert "下载计划" in feature.description
    state = initial_geo_download_state()
    assert state.title == "数据下载"
    assert state.status_label == "测试中"
