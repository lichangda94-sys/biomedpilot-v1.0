from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.screening_page import initial_screening_state
from app.meta_analysis.services.screening_service import ScreeningService
from app.shared.data_center.service import DataCenter
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature
from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType


def make_service(tmp_path) -> tuple[ScreeningService, TaskCenter, DataCenter]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = ScreeningService(
        task_center=task_center,
        data_center=data_center,
        storage_root=tmp_path,
    )
    return service, task_center, data_center


def write_prepare_output(tmp_path: Path) -> Path:
    path = tmp_path / "screening_ready.json"
    payload = {
        "project_id": "meta-test",
        "batch_id": "batch-screening",
        "records": [
            {
                "record_id": "rec-1",
                "batch_id": "batch-screening",
                "source_record_id": "src-1",
                "source": "nbib",
                "title": "Same Trial Title",
                "abstract": "Abstract A",
                "title_normalized": "same trial title",
                "doi_normalized": "10.1000/same",
                "pmid_normalized": "111",
                "authors_normalized": ["doe jane"],
                "journal_normalized": "journal",
                "year_normalized": 2024,
                "source_trace": ["rec-1"],
            },
            {
                "record_id": "rec-2",
                "batch_id": "batch-screening",
                "source_record_id": "src-2",
                "source": "ris",
                "title": "Same Trial Title",
                "abstract": "Abstract B",
                "title_normalized": "same trial title",
                "doi_normalized": "10.1000/same",
                "pmid_normalized": "222",
                "authors_normalized": ["doe jane"],
                "journal_normalized": "journal",
                "year_normalized": 2024,
                "source_trace": ["rec-2"],
            },
            {
                "record_id": "rec-3",
                "batch_id": "batch-screening",
                "source_record_id": "src-3",
                "source": "csv",
                "title": "Different Study",
                "abstract": "",
                "title_normalized": "different study",
                "doi_normalized": "",
                "pmid_normalized": "",
                "authors_normalized": ["smith john"],
                "journal_normalized": "",
                "year_normalized": 2020,
                "source_trace": ["rec-3"],
            },
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def write_duplicate_output(tmp_path: Path, prepare_path: Path) -> Path:
    path = tmp_path / "duplicate_groups.json"
    payload = {
        "project_id": "meta-test",
        "batch_id": "batch-screening",
        "source_path": str(prepare_path),
        "duplicate_groups": [
            {
                "duplicate_group_id": "dup-1",
                "candidate_record_ids": ["rec-1", "rec-2"],
                "match_reason": "doi",
                "confidence": 1.0,
                "suggested_primary_record_id": "rec-1",
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_screening_rejects_empty_path(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    result = service.create_queue(project_id="meta-test", source_path="")
    assert not result.success
    assert "请选择" in result.message
    assert task_center.list_tasks()[0].status is TaskStatus.FAILED
    assert data_center.list_assets() == []


def test_screening_rejects_missing_file(tmp_path) -> None:
    service, task_center, _data_center = make_service(tmp_path)
    result = service.create_queue(project_id="meta-test", source_path=str(tmp_path / "missing.json"))
    assert not result.success
    assert "不存在" in result.message
    assert task_center.list_tasks()[0].task_type is TaskType.SCREENING


def test_screening_rejects_non_json(tmp_path) -> None:
    source = tmp_path / "records.txt"
    source.write_text("not json", encoding="utf-8")
    service, _task_center, _data_center = make_service(tmp_path)
    result = service.create_queue(project_id="meta-test", source_path=str(source))
    assert not result.success
    assert "JSON" in result.message


def test_screening_queue_from_prepare_output(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    source = write_prepare_output(tmp_path)
    result = service.create_queue(project_id="meta-test", source_path=str(source))
    assert result.success
    assert result.total_records == 3
    assert result.queued_records == 3
    assert result.decision_counts["pending"] == 3
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert payload["stage"] == "title_abstract_screening"
    assert payload["screening_records"][0]["decision"] == "pending"
    task = task_center.list_tasks()[0]
    assert task.status is TaskStatus.COMPLETED
    assert task.task_type is TaskType.SCREENING
    assert any(asset.data_type == "screening_queue" for asset in data_center.list_assets("meta-test"))


def test_screening_decision_update_marks_record_included(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    source = write_prepare_output(tmp_path)
    queue_result = service.create_queue(project_id="meta-test", source_path=str(source))
    payload = json.loads(Path(queue_result.output_path).read_text(encoding="utf-8"))
    record_id = payload["screening_records"][0]["screening_record_id"]
    result = service.update_decision(
        project_id="meta-test",
        queue_path=queue_result.output_path,
        screening_record_id=record_id,
        decision="included",
        notes="Eligible for extraction",
    )
    assert result.success
    assert result.decision_counts["included"] == 1
    updated_payload = json.loads(Path(queue_result.output_path).read_text(encoding="utf-8"))
    updated_record = updated_payload["screening_records"][0]
    assert updated_record["decision"] == "included"
    assert updated_record["decided_at"]
    assert updated_record["notes"] == "Eligible for extraction"
    task = task_center.list_tasks()[0]
    assert task.task_type is TaskType.SCREENING_DECISION
    assert task.status is TaskStatus.COMPLETED
    assert any(asset.data_type == "screening_decisions" for asset in data_center.list_assets("meta-test"))


def test_screening_decision_update_requires_valid_decision(tmp_path) -> None:
    service, task_center, _data_center = make_service(tmp_path)
    source = write_prepare_output(tmp_path)
    queue_result = service.create_queue(project_id="meta-test", source_path=str(source))
    result = service.update_decision(
        project_id="meta-test",
        queue_path=queue_result.output_path,
        screening_record_id="screen-unknown",
        decision="yes",
    )
    assert not result.success
    assert "pending、included、excluded" in result.message
    assert task_center.list_tasks()[0].status is TaskStatus.FAILED


def test_screening_decision_update_requires_exclusion_reason(tmp_path) -> None:
    service, _task_center, _data_center = make_service(tmp_path)
    source = write_prepare_output(tmp_path)
    queue_result = service.create_queue(project_id="meta-test", source_path=str(source))
    payload = json.loads(Path(queue_result.output_path).read_text(encoding="utf-8"))
    result = service.update_decision(
        project_id="meta-test",
        queue_path=queue_result.output_path,
        screening_record_id=payload["screening_records"][0]["screening_record_id"],
        decision="excluded",
    )
    assert not result.success
    assert "排除原因" in result.message


def test_screening_queue_from_duplicate_output_filters_non_primary_duplicates(tmp_path) -> None:
    service, _task_center, _data_center = make_service(tmp_path)
    prepare_path = write_prepare_output(tmp_path)
    duplicate_path = write_duplicate_output(tmp_path, prepare_path)
    result = service.create_queue(project_id="meta-test", source_path=str(duplicate_path))
    assert result.success
    assert result.total_records == 3
    assert result.queued_records == 2
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    queued_ids = {record["normalized_record_id"] for record in payload["screening_records"]}
    assert queued_ids == {"rec-1", "rec-3"}
    assert result.details["duplicate_groups_used"] == 1


def test_screening_feature_status_and_page_state() -> None:
    feature = get_feature("meta-screening")
    assert feature is not None
    assert feature.status is FeatureAvailabilityStatus.TESTING
    assert "include/exclude/maybe" in feature.description
    state = initial_screening_state()
    assert state.title == "Screening / 标题摘要筛选"
    assert state.status_label == "测试中"
