from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.extraction_page import initial_extraction_state
from app.meta_analysis.services.extraction_service import ExtractionService
from app.shared.data_center.service import DataCenter
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature
from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType


def make_service(tmp_path) -> tuple[ExtractionService, TaskCenter, DataCenter]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = ExtractionService(
        task_center=task_center,
        data_center=data_center,
        storage_root=tmp_path,
    )
    return service, task_center, data_center


def write_screening_queue(tmp_path: Path, *, decisions: list[str]) -> Path:
    path = tmp_path / "screening_queue.json"
    records = []
    for index, decision in enumerate(decisions, start=1):
        records.append(
            {
                "screening_record_id": f"screen-{index}",
                "project_id": "meta-test",
                "source_record_id": f"src-{index}",
                "normalized_record_id": f"rec-{index}",
                "title": f"Study {index}",
                "abstract": "",
                "stage": "title_abstract_screening",
                "decision": decision,
                "exclusion_reason_code": "",
                "exclusion_reason_text": "",
                "reviewer_id": None,
                "notes": "",
            }
        )
    payload = {
        "project_id": "meta-test",
        "batch_id": "batch-extraction",
        "stage": "title_abstract_screening",
        "screening_records": records,
        "decision_counts": {"total": len(records)},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_extraction_rejects_empty_path(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    result = service.create_pool(project_id="meta-test", screening_queue_path="")
    assert not result.success
    assert "请选择" in result.message
    assert task_center.list_tasks()[0].status is TaskStatus.FAILED
    assert data_center.list_assets() == []


def test_extraction_rejects_missing_file(tmp_path) -> None:
    service, task_center, _data_center = make_service(tmp_path)
    result = service.create_pool(project_id="meta-test", screening_queue_path=str(tmp_path / "missing.json"))
    assert not result.success
    assert "不存在" in result.message
    assert task_center.list_tasks()[0].task_type is TaskType.EXTRACTION


def test_extraction_rejects_non_json(tmp_path) -> None:
    source = tmp_path / "screening.txt"
    source.write_text("not json", encoding="utf-8")
    service, _task_center, _data_center = make_service(tmp_path)
    result = service.create_pool(project_id="meta-test", screening_queue_path=str(source))
    assert not result.success
    assert "JSON" in result.message


def test_extraction_pool_from_included_screening_records(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    source = write_screening_queue(tmp_path, decisions=["included", "pending", "excluded"])
    result = service.create_pool(project_id="meta-test", screening_queue_path=str(source))
    assert result.success
    assert result.total_screening_records == 3
    assert result.included_records == 1
    assert result.extraction_records == 1
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert payload["manual_data_entry_enabled"] is False
    assert payload["extraction_records"][0]["study_title"] == "Study 1"
    task = task_center.list_tasks()[0]
    assert task.status is TaskStatus.COMPLETED
    assert task.task_type is TaskType.EXTRACTION
    assert any(asset.data_type == "extraction_pool" for asset in data_center.list_assets("meta-test"))


def test_extraction_pool_with_only_pending_records_is_explicit(tmp_path) -> None:
    service, _task_center, _data_center = make_service(tmp_path)
    source = write_screening_queue(tmp_path, decisions=["pending", "pending"])
    result = service.create_pool(project_id="meta-test", screening_queue_path=str(source))
    assert result.success
    assert result.extraction_records == 0
    assert "没有 included 记录" in result.message
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert payload["extraction_records"] == []


def test_extraction_feature_status_and_page_state() -> None:
    feature = get_feature("meta-extraction")
    assert feature is not None
    assert feature.status is FeatureAvailabilityStatus.TESTING
    assert "提取池" in feature.description
    state = initial_extraction_state()
    assert state.title == "Extraction / 数据提取"
    assert state.status_label == "测试中"
