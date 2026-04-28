from __future__ import annotations

from pathlib import Path

from app.meta_analysis.pages.literature_import_page import initial_literature_import_state
from app.meta_analysis.services.literature_import_service import LiteratureImportService
from app.shared.data_center.service import DataCenter
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature
from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "literature"


def make_service(tmp_path) -> tuple[LiteratureImportService, TaskCenter, DataCenter]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = LiteratureImportService(
        task_center=task_center,
        data_center=data_center,
        storage_root=tmp_path,
    )
    return service, task_center, data_center


def test_literature_import_rejects_empty_path(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    result = service.import_file(project_id="meta-test", source_path="")
    assert not result.success
    assert "请选择" in result.message
    assert task_center.list_tasks()[0].status is TaskStatus.FAILED
    assert data_center.list_assets() == []


def test_literature_import_rejects_missing_file(tmp_path) -> None:
    service, task_center, _data_center = make_service(tmp_path)
    result = service.import_file(project_id="meta-test", source_path=str(tmp_path / "missing.nbib"))
    assert not result.success
    assert "文件不存在" in result.message
    assert task_center.list_tasks()[0].task_type is TaskType.LITERATURE_IMPORT


def test_literature_import_rejects_unsupported_extension(tmp_path) -> None:
    source = tmp_path / "records.txt"
    source.write_text("not supported", encoding="utf-8")
    service, _task_center, data_center = make_service(tmp_path)
    result = service.import_file(project_id="meta-test", source_path=str(source))
    assert not result.success
    assert ".nbib" in result.message
    assert data_center.list_assets() == []


def test_literature_import_nbib_smoke(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    result = service.import_file(project_id="meta-test", source_path=str(FIXTURES / "sample.nbib"))
    assert result.success
    assert result.source_type == "nbib"
    assert result.imported_records == 2
    assert Path(result.output_path).exists()
    task = task_center.list_tasks()[0]
    assert task.status is TaskStatus.COMPLETED
    assert task.project_id == "meta-test"
    assert task.task_type is TaskType.LITERATURE_IMPORT
    asset = data_center.list_assets()[0]
    assert asset.data_type == "literature_records"
    assert asset.output_path == result.output_path


def test_literature_import_ris_smoke(tmp_path) -> None:
    service, _task_center, data_center = make_service(tmp_path)
    result = service.import_file(project_id="meta-test", source_path=str(FIXTURES / "sample.ris"))
    assert result.success
    assert result.source_type == "ris"
    assert result.imported_records == 2
    assert data_center.list_assets("meta-test")


def test_literature_import_csv_smoke(tmp_path) -> None:
    service, _task_center, data_center = make_service(tmp_path)
    result = service.import_file(project_id="meta-test", source_path=str(FIXTURES / "sample.csv"))
    assert result.success
    assert result.source_type == "csv"
    assert result.imported_records == 2
    assert data_center.list_assets("meta-test")[0].module == "meta_analysis"


def test_literature_import_feature_availability_status() -> None:
    feature = get_feature("meta-literature-import")
    assert feature is not None
    assert feature.status is FeatureAvailabilityStatus.TESTING
    assert "NBIB" in feature.description


def test_literature_import_page_state() -> None:
    state = initial_literature_import_state()
    assert state.title == "文献导入"
    assert state.supported_formats == ("NBIB", "RIS", "CSV")
    assert state.status_label in {"测试中", "已开放"}

