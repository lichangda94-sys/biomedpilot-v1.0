from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.adapters.legacy_geo import LegacyGeoAdapter
from app.bioinformatics.pages.geo_import_page import initial_geo_import_state
from app.bioinformatics.services.geo_import_service import GeoImportService
from app.shared.data_center.service import DataCenter
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature
from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType


def make_service(tmp_path) -> tuple[GeoImportService, TaskCenter, DataCenter]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = GeoImportService(
        task_center=task_center,
        data_center=data_center,
        storage_root=tmp_path,
    )
    return service, task_center, data_center


def test_legacy_geo_adapter_builds_query_and_accessions() -> None:
    plan = LegacyGeoAdapter().build_query_plan(
        query_text="papillary thyroid carcinoma",
        accession_text="GSE33630, gse27155",
        max_results=10,
    )
    assert "GSE[ETYP]" in plan.full_geo_query
    assert plan.accessions == ["GSE33630", "GSE27155"]
    assert plan.max_results == 10


def test_geo_import_rejects_empty_input(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    result = service.create_geo_import_plan(project_id="bio-test", query_text="", accession_text="")
    assert not result.success
    assert "请输入" in result.message
    assert task_center.list_tasks()[0].status is TaskStatus.FAILED
    assert data_center.list_assets() == []


def test_geo_import_rejects_invalid_max_results(tmp_path) -> None:
    service, _task_center, _data_center = make_service(tmp_path)
    result = service.create_geo_import_plan(project_id="bio-test", query_text="cancer", max_results=0)
    assert not result.success
    assert "max_results" in result.message


def test_geo_import_creates_query_plan(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    result = service.create_geo_import_plan(
        project_id="bio-test",
        query_text="papillary thyroid carcinoma",
        accession_text="GSE33630",
        max_results=5,
    )
    assert result.success
    assert result.accessions == ["GSE33630"]
    assert "GSE[ETYP]" in result.full_geo_query
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert payload["online_search_executed"] is False
    assert payload["plan"]["accessions"] == ["GSE33630"]
    task = task_center.list_tasks()[0]
    assert task.status is TaskStatus.COMPLETED
    assert task.task_type is TaskType.IMPORT
    assert any(asset.data_type == "geo_query_plan" for asset in data_center.list_assets("bio-test"))


def test_geo_import_feature_status_and_page_state() -> None:
    feature = get_feature("bio-data-import")
    assert feature is not None
    assert feature.status is FeatureAvailabilityStatus.TESTING
    assert "GEO 查询计划" in feature.description
    state = initial_geo_import_state()
    assert state.title == "数据检索 / 导入"
    assert state.status_label == "测试中"
