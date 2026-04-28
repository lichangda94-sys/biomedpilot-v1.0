from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.prepare_screening_page import initial_prepare_screening_state
from app.meta_analysis.services.literature_import_service import LiteratureImportService
from app.meta_analysis.services.prepare_screening_service import PrepareScreeningService
from app.shared.data_center.service import DataCenter
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature
from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "literature"


def make_services(tmp_path) -> tuple[LiteratureImportService, PrepareScreeningService, TaskCenter, DataCenter]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    import_service = LiteratureImportService(
        task_center=task_center,
        data_center=data_center,
        storage_root=tmp_path,
    )
    prepare_service = PrepareScreeningService(
        task_center=task_center,
        data_center=data_center,
        storage_root=tmp_path,
    )
    return import_service, prepare_service, task_center, data_center


def test_prepare_screening_rejects_empty_path(tmp_path) -> None:
    _import_service, prepare_service, task_center, data_center = make_services(tmp_path)
    result = prepare_service.prepare(project_id="meta-test", import_output_path="")
    assert not result.success
    assert "请选择" in result.message
    assert task_center.list_tasks()[0].status is TaskStatus.FAILED
    assert data_center.list_assets() == []


def test_prepare_screening_rejects_missing_file(tmp_path) -> None:
    _import_service, prepare_service, task_center, _data_center = make_services(tmp_path)
    result = prepare_service.prepare(project_id="meta-test", import_output_path=str(tmp_path / "missing.json"))
    assert not result.success
    assert "不存在" in result.message
    assert task_center.list_tasks()[0].task_type is TaskType.PREPARE_SCREENING


def test_prepare_screening_rejects_non_json(tmp_path) -> None:
    source = tmp_path / "records.txt"
    source.write_text("not json", encoding="utf-8")
    _import_service, prepare_service, _task_center, _data_center = make_services(tmp_path)
    result = prepare_service.prepare(project_id="meta-test", import_output_path=str(source))
    assert not result.success
    assert "JSON" in result.message


def test_prepare_screening_from_literature_import_output(tmp_path) -> None:
    import_service, prepare_service, task_center, data_center = make_services(tmp_path)
    import_result = import_service.import_file(project_id="meta-test", source_path=str(FIXTURES / "sample.nbib"))
    assert import_result.success
    result = prepare_service.prepare(project_id="meta-test", import_output_path=import_result.output_path)
    assert result.success
    assert result.total_records == 2
    assert result.prepared_records == 2
    assert Path(result.output_path).exists()
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert payload["records"][0]["title_normalized"]
    task = task_center.list_tasks()[0]
    assert task.status is TaskStatus.COMPLETED
    assert task.task_type is TaskType.PREPARE_SCREENING
    assets = data_center.list_assets("meta-test")
    assert any(asset.data_type == "screening_ready_records" for asset in assets)


def test_prepare_screening_feature_status_and_page_state() -> None:
    feature = get_feature("meta-dedup-prep")
    assert feature is not None
    assert feature.status is FeatureAvailabilityStatus.TESTING
    assert "标准化" in feature.description
    state = initial_prepare_screening_state()
    assert state.title == "去重准备 / Prepare for Screening"
    assert state.status_label == "测试中"

