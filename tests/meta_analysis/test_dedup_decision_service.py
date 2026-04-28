from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.models.dedup import DuplicateGroup
from app.meta_analysis.pages.duplicate_review_page import duplicate_review_state_from_groups, initial_duplicate_review_state
from app.meta_analysis.services.dedup_decision_service import DedupDecisionService
from app.meta_analysis.services.duplicate_review_service import DuplicateReviewService
from app.shared.data_center.service import DataCenter
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature
from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType


def make_services(tmp_path: Path) -> tuple[DuplicateReviewService, DedupDecisionService, TaskCenter, DataCenter]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    review_service = DuplicateReviewService(
        task_center=task_center,
        data_center=data_center,
        storage_root=tmp_path,
    )
    dedup_service = DedupDecisionService(
        task_center=task_center,
        data_center=data_center,
        storage_root=tmp_path,
    )
    return review_service, dedup_service, task_center, data_center


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
                "source_record_id": "nbib-1",
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
                "source_record_id": "ris-2",
                "title": "Same Trial Title",
                "abstract": "B",
                "authors": ["Doe, Jane", "Roe, Ray"],
                "journal": "Journal",
                "year": 2024,
                "doi": "10.1000/same",
                "pmid": "222",
                "title_normalized": "same trial title",
                "doi_normalized": "10.1000/same",
                "pmid_normalized": "222",
                "authors_normalized": ["doe jane", "roe ray"],
                "journal_normalized": "journal",
                "year_normalized": 2024,
                "source_trace": ["rec-2"],
            },
            {
                "record_id": "rec-3",
                "batch_id": "batch-test",
                "source": "csv",
                "source_record_id": "csv-3",
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


def write_duplicate_review(tmp_path: Path) -> tuple[Path, DedupDecisionService, TaskCenter, DataCenter]:
    review_service, dedup_service, task_center, data_center = make_services(tmp_path)
    source = write_screening_ready(tmp_path)
    result = review_service.review(project_id="meta-test", screening_ready_path=str(source))
    assert result.success
    return Path(result.output_path), dedup_service, task_center, data_center


def output_record_ids(output_path: str) -> set[str]:
    payload = json.loads(Path(output_path).read_text(encoding="utf-8"))
    return {str(record.get("record_id", "")) for record in payload["records"]}


def test_duplicate_group_data_structure(tmp_path) -> None:
    review_path, service, _task_center, _data_center = write_duplicate_review(tmp_path)
    groups = service.load_groups(duplicate_review_path=str(review_path))
    assert groups
    group = groups[0]
    assert isinstance(group, DuplicateGroup)
    assert group.group_id
    assert len(group.records) >= 2
    assert group.match_reason
    assert group.status == "pending"


def test_keep_first_generates_deduplicated_literature(tmp_path) -> None:
    review_path, service, _task_center, _data_center = write_duplicate_review(tmp_path)
    group = service.load_groups(duplicate_review_path=str(review_path))[0]
    decision = service.save_decision(duplicate_review_path=str(review_path), group_id=group.group_id, decision="keep_first")
    result = service.generate_deduplicated_literature(project_id="meta-test", duplicate_review_path=str(review_path))
    assert decision.selected_record_id == "rec-1"
    assert result.success
    assert result.original_count == 3
    assert result.unique_count == 2
    assert output_record_ids(result.output_path) == {"rec-1", "rec-3"}


def test_keep_second_keeps_second_candidate(tmp_path) -> None:
    review_path, service, _task_center, _data_center = write_duplicate_review(tmp_path)
    group = service.load_groups(duplicate_review_path=str(review_path))[0]
    decision = service.save_decision(duplicate_review_path=str(review_path), group_id=group.group_id, decision="keep_second")
    result = service.generate_deduplicated_literature(project_id="meta-test", duplicate_review_path=str(review_path))
    assert decision.selected_record_id == "rec-2"
    assert output_record_ids(result.output_path) == {"rec-2", "rec-3"}


def test_merge_creates_merged_record(tmp_path) -> None:
    review_path, service, _task_center, _data_center = write_duplicate_review(tmp_path)
    group = service.load_groups(duplicate_review_path=str(review_path))[0]
    decision = service.save_decision(duplicate_review_path=str(review_path), group_id=group.group_id, decision="merge")
    result = service.generate_deduplicated_literature(project_id="meta-test", duplicate_review_path=str(review_path))
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert decision.merged_record["record_id"] == f"merged-{group.group_id}"
    assert output_record_ids(result.output_path) == {f"merged-{group.group_id}", "rec-3"}
    merged = [record for record in payload["records"] if record["record_id"] == f"merged-{group.group_id}"][0]
    assert merged["authors"] == ["Doe, Jane", "Roe, Ray"]
    assert merged["merged_from_record_ids"] == ["rec-1", "rec-2"]


def test_mark_not_duplicate_keeps_all_candidates(tmp_path) -> None:
    review_path, service, _task_center, _data_center = write_duplicate_review(tmp_path)
    group = service.load_groups(duplicate_review_path=str(review_path))[0]
    service.save_decision(duplicate_review_path=str(review_path), group_id=group.group_id, decision="mark_not_duplicate")
    result = service.generate_deduplicated_literature(project_id="meta-test", duplicate_review_path=str(review_path))
    assert result.resolved_group_count == 1
    assert result.unique_count == 3
    assert output_record_ids(result.output_path) == {"rec-1", "rec-2", "rec-3"}


def test_skip_leaves_group_unresolved_without_excluding_records(tmp_path) -> None:
    review_path, service, _task_center, _data_center = write_duplicate_review(tmp_path)
    group = service.load_groups(duplicate_review_path=str(review_path))[0]
    service.save_decision(duplicate_review_path=str(review_path), group_id=group.group_id, decision="skip")
    result = service.generate_deduplicated_literature(project_id="meta-test", duplicate_review_path=str(review_path))
    assert result.resolved_group_count == 0
    assert result.unique_count == 3
    assert result.details["unresolved_group_ids"] == [group.group_id]


def test_dedup_result_registers_data_center_and_task_center(tmp_path) -> None:
    review_path, service, task_center, data_center = write_duplicate_review(tmp_path)
    group = service.load_groups(duplicate_review_path=str(review_path))[0]
    service.save_decision(duplicate_review_path=str(review_path), group_id=group.group_id, decision="keep_first")
    result = service.generate_deduplicated_literature(project_id="meta-test", duplicate_review_path=str(review_path))
    assets = data_center.list_assets("meta-test")
    tasks = task_center.list_tasks()
    assert any(asset.data_type == "deduplicated_literature" and asset.output_path == result.output_path for asset in assets)
    assert tasks[0].task_type is TaskType.DEDUP_DECISION
    assert tasks[0].status is TaskStatus.COMPLETED
    assert tasks[0].module == "meta_analysis"


def test_feature_availability_status_and_description() -> None:
    feature = get_feature("meta-duplicate-review")
    assert feature is not None
    assert feature.status is FeatureAvailabilityStatus.TESTING
    assert "最小人工决策" in feature.description
    assert "高级 fuzzy matching" in feature.description


def test_duplicate_review_page_state_contains_manual_decision_fields() -> None:
    group = DuplicateGroup(
        group_id="dup-1",
        records=[{"record_id": "rec-1", "title": "A"}, {"record_id": "rec-2", "title": "A"}],
        match_reason="doi",
        confidence=1.0,
        status="resolved",
    )
    initial = initial_duplicate_review_state()
    state = duplicate_review_state_from_groups(groups=[group], original_record_count=2)
    assert initial.title == "文献去重"
    assert initial.status_label == "测试中"
    assert state.original_record_count == 2
    assert state.duplicate_group_count == 1
    assert state.resolved_group_count == 1
    assert state.current_group == group
    assert "keep_first" in state.decision_options
    assert "doi" in state.current_group_fields
