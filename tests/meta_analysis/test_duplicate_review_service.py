from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.duplicate_review_page import initial_duplicate_review_state
from app.meta_analysis.services.duplicate_review_service import DuplicateReviewService
from app.shared.data_center.service import DataCenter
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature
from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType


def make_service(tmp_path) -> tuple[DuplicateReviewService, TaskCenter, DataCenter]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = DuplicateReviewService(
        task_center=task_center,
        data_center=data_center,
        storage_root=tmp_path,
    )
    return service, task_center, data_center


def write_screening_ready(tmp_path: Path) -> Path:
    path = tmp_path / "screening_ready.json"
    payload = {
        "project_id": "meta-test",
        "batch_id": "batch-test",
        "records": [
            {
                "record_id": "rec-1",
                "batch_id": "batch-test",
                "source": "nbib",
                "title": "Same Trial Title",
                "abstract": "A",
                "authors": ["Doe, Jane"],
                "journal": "Journal",
                "year": 2024,
                "doi": "10.1000/same",
                "pmid": "111",
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
                "batch_id": "batch-test",
                "source": "ris",
                "title": "Same Trial Title",
                "abstract": "B",
                "authors": ["Doe, Jane"],
                "journal": "Journal",
                "year": 2024,
                "doi": "10.1000/same",
                "pmid": "222",
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
                "batch_id": "batch-test",
                "source": "csv",
                "title": "Different Study",
                "abstract": "",
                "authors": ["Smith, John"],
                "journal": "",
                "year": 2020,
                "doi": "",
                "pmid": "",
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


def test_duplicate_review_rejects_empty_path(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    result = service.review(project_id="meta-test", screening_ready_path="")
    assert not result.success
    assert "请选择" in result.message
    assert task_center.list_tasks()[0].status is TaskStatus.FAILED
    assert data_center.list_assets() == []


def test_duplicate_review_rejects_missing_file(tmp_path) -> None:
    service, task_center, _data_center = make_service(tmp_path)
    result = service.review(project_id="meta-test", screening_ready_path=str(tmp_path / "missing.json"))
    assert not result.success
    assert "不存在" in result.message
    assert task_center.list_tasks()[0].task_type is TaskType.DUPLICATE_REVIEW


def test_duplicate_review_rejects_non_json(tmp_path) -> None:
    source = tmp_path / "records.txt"
    source.write_text("not json", encoding="utf-8")
    service, _task_center, _data_center = make_service(tmp_path)
    result = service.review(project_id="meta-test", screening_ready_path=str(source))
    assert not result.success
    assert "JSON" in result.message


def test_duplicate_review_generates_candidate_groups(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    source = write_screening_ready(tmp_path)
    result = service.review(project_id="meta-test", screening_ready_path=str(source))
    assert result.success
    assert result.total_records == 3
    assert result.duplicate_group_count >= 1
    assert result.candidate_record_count >= 2
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert payload["duplicate_groups"]
    assert payload["duplicate_groups"][0]["candidate_record_ids"]
    task = task_center.list_tasks()[0]
    assert task.status is TaskStatus.COMPLETED
    assert task.task_type is TaskType.DUPLICATE_REVIEW
    assets = data_center.list_assets("meta-test")
    assert any(asset.data_type == "duplicate_candidate_groups" for asset in assets)


def test_duplicate_review_feature_status_and_page_state() -> None:
    feature = get_feature("meta-duplicate-review")
    assert feature is not None
    assert feature.status is FeatureAvailabilityStatus.TESTING
    assert "最小人工决策" in feature.description
    state = initial_duplicate_review_state()
    assert state.title == "文献去重"
    assert state.status_label == "测试中"
