from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.meta_analysis.pages.duplicate_review_page import duplicate_review_state_from_groups
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.dedup_decision_service import DedupDecisionService
from app.meta_analysis.services.formal_report_service import PRISMAService


def _write_duplicate_review_fixture(tmp_path: Path, *, empty_group: bool = False) -> Path:
    source_path = tmp_path / "screening_ready.json"
    source_path.write_text(
        json.dumps(
            {
                "project_id": "meta-test",
                "records": [
                    {
                        "record_id": "rec-1",
                        "source": "nbib",
                        "title": "Short duplicate title",
                        "abstract": "A",
                        "authors": ["Smith J"],
                        "journal": "Journal A",
                        "year": 2024,
                        "doi": "10.1000/a",
                        "pmid": "123",
                    },
                    {
                        "record_id": "rec-2",
                        "source": "ris",
                        "title": "Longer duplicate title with details",
                        "abstract": "A longer abstract",
                        "authors": ["Smith J", "Wang M"],
                        "journal": "Journal A",
                        "year": 2024,
                        "doi": "10.1000/a",
                        "pmid": "123",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    review_path = tmp_path / "batch_duplicate_groups.json"
    review_path.write_text(
        json.dumps(
            {
                "project_id": "meta-test",
                "batch_id": "batch",
                "source_path": str(source_path),
                "duplicate_groups": [
                    {
                        "group_id": "dup-1",
                        "record_ids": [] if empty_group else ["rec-1", "rec-2"],
                        "reason": "pmid_exact,doi_exact,title_author_year_journal_suspected",
                        "confidence": 0.99,
                        "status": "pending",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return review_path


def test_duplicate_review_state_exposes_group_records_field_differences_and_merge_preview(tmp_path: Path) -> None:
    service = DedupDecisionService(storage_root=tmp_path)
    review_path = _write_duplicate_review_fixture(tmp_path)
    groups = service.load_groups(duplicate_review_path=str(review_path))
    preview = service.preview_merge(duplicate_review_path=str(review_path), group_id="dup-1")

    state = duplicate_review_state_from_groups(groups=groups, original_record_count=2, merge_preview=preview)
    differences = {item.field_name: item.values_by_record_id for item in state.field_differences}

    assert state.status_label == "测试中"
    assert state.current_group_records[0].record_id == "rec-1"
    assert state.current_group_records[1].record_id == "rec-2"
    assert "title" in differences
    assert "abstract" in differences
    assert "authors" in differences
    assert state.merge_preview_summary.available is True
    assert state.merge_preview_summary.group_id == "dup-1"
    assert state.merge_preview_summary.merged_from_record_ids == ("rec-1", "rec-2")
    assert ("title", "rec-2") in state.merge_preview_summary.field_sources
    assert {"keep_both", "mark_not_duplicate", "exclude_duplicate", "merge"} <= set(state.interactive_decision_options)
    assert "不会执行批量合并" in state.interaction_warning


def test_interactive_duplicate_decisions_write_audit_log_without_bulk_merge(tmp_path: Path) -> None:
    audit = MetaAuditLogService()
    service = DedupDecisionService(storage_root=tmp_path, audit_log=audit)
    review_path = _write_duplicate_review_fixture(tmp_path)

    decisions = [
        service.save_interactive_decision(duplicate_review_path=str(review_path), group_id="dup-1", decision="keep_both"),
        service.save_interactive_decision(duplicate_review_path=str(review_path), group_id="dup-1", decision="mark_not_duplicate"),
        service.save_interactive_decision(duplicate_review_path=str(review_path), group_id="dup-1", decision="exclude_duplicate"),
        service.save_interactive_decision(duplicate_review_path=str(review_path), group_id="dup-1", decision="merge"),
    ]
    events = audit.list_events(tmp_path)

    assert [decision.decision for decision in decisions] == ["keep_both", "mark_not_duplicate", "exclude_duplicate", "merge"]
    assert decisions[-1].merged_record["record_id"] == "merged-dup-1"
    assert len([event for event in events if event.event_type == "duplicate_decision"]) == 4
    assert all(event.target_id == "dup-1" for event in events if event.event_type == "duplicate_decision")
    assert review_path.with_name("batch_dedup_decisions.json").exists()
    assert not list(tmp_path.rglob("*deduplicated_literature.json"))


def test_interactive_merge_requires_available_preview(tmp_path: Path) -> None:
    service = DedupDecisionService(storage_root=tmp_path)
    review_path = _write_duplicate_review_fixture(tmp_path, empty_group=True)

    with pytest.raises(ValueError, match="merge 决策需要先生成可读 merge preview"):
        service.save_interactive_decision(duplicate_review_path=str(review_path), group_id="dup-1", decision="merge")


def test_prisma_collects_duplicates_removed_from_duplicate_review_decisions(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    (project_dir / "literature").mkdir(parents=True)
    (project_dir / "deduplication").mkdir(parents=True)
    (project_dir / "screening").mkdir(parents=True)
    (project_dir / "literature" / "literature_records.json").write_text(
        json.dumps({"records": [{"record_id": "rec-1"}, {"record_id": "rec-2"}, {"record_id": "rec-3"}]}),
        encoding="utf-8",
    )
    (project_dir / "deduplication" / "duplicate_candidate_groups.json").write_text(
        json.dumps({"duplicate_groups": [{"group_id": "dup-1", "record_ids": ["rec-1", "rec-2"]}]}),
        encoding="utf-8",
    )
    (project_dir / "deduplication" / "dedup_decisions.json").write_text(
        json.dumps({"decisions": [{"group_id": "dup-1", "decision": "keep_first", "selected_record_id": "rec-1"}]}),
        encoding="utf-8",
    )
    (project_dir / "screening" / "screening_decisions.json").write_text(
        json.dumps({"screening_records": [{"record_id": "rec-1", "decision": "included"}, {"record_id": "rec-3", "decision": "excluded"}]}),
        encoding="utf-8",
    )

    summary = PRISMAService().collect_prisma_numbers(project_dir)
    markdown_path = PRISMAService().export_prisma_flow_markdown(project_dir, summary)

    assert summary.records_identified == 3
    assert summary.duplicates_removed == 1
    assert summary.records_after_deduplication == 2
    assert "Duplicates removed: 1" in markdown_path.read_text(encoding="utf-8")
