from __future__ import annotations

import csv
import json
from pathlib import Path

from app.meta_analysis.pages.duplicate_review_page import duplicate_review_state_from_groups
from app.meta_analysis.services.dedup_decision_service import DedupDecisionService


def _write_review_fixture(tmp_path: Path) -> Path:
    source_path = tmp_path / "screening_ready.json"
    source_path.write_text(
        json.dumps(
            {
                "project_id": "meta-test",
                "records": [
                    {
                        "record_id": "rec-1",
                        "source": "nbib",
                        "title": "Complete trial title",
                        "abstract": "Short abstract",
                        "authors": ["Smith J"],
                        "journal": "Journal A",
                        "year": 2024,
                        "doi": "10.1000/a",
                        "pmid": "123",
                    },
                    {
                        "record_id": "rec-2",
                        "source": "ris",
                        "title": "Complete trial title with subtitle",
                        "abstract": "Longer abstract for the same trial",
                        "authors": ["Smith J", "Wang M"],
                        "journal": "Journal A",
                        "year": 2024,
                        "doi": "10.1000/a",
                        "pmid": "123",
                    },
                    {
                        "record_id": "rec-3",
                        "source": "csv",
                        "title": "Similar oncology trial",
                        "abstract": "A",
                        "authors": ["Lee K"],
                        "journal": "Journal B",
                        "year": 2020,
                        "doi": "",
                        "pmid": "",
                    },
                    {
                        "record_id": "rec-4",
                        "source": "csv",
                        "title": "Similar oncology trial update",
                        "abstract": "B",
                        "authors": ["Lee K"],
                        "journal": "Journal B",
                        "year": 2021,
                        "doi": "",
                        "pmid": "",
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
                "source_path": str(source_path),
                "duplicate_groups": [
                    {
                        "group_id": "dup-exact",
                        "record_ids": ["rec-1", "rec-2"],
                        "reason": "pmid_exact,doi_exact",
                        "confidence": 1.0,
                        "status": "pending",
                    },
                    {
                        "duplicate_group_id": "dup-suspected",
                        "candidate_record_ids": ["rec-3", "rec-4"],
                        "match_reason": "title_author_year_journal_suspected",
                        "confidence": 0.82,
                        "status": "pending",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return review_path


def test_duplicate_review_page_state_summarizes_exact_and_suspected_groups(tmp_path: Path) -> None:
    service = DedupDecisionService(storage_root=tmp_path)
    review_path = _write_review_fixture(tmp_path)
    groups = service.load_groups(duplicate_review_path=str(review_path))
    preview = service.preview_merge(duplicate_review_path=str(review_path), group_id="dup-exact")
    queue_path = service.export_duplicate_review_queue(duplicate_review_path=str(review_path))

    state = duplicate_review_state_from_groups(
        groups=groups,
        original_record_count=4,
        merge_preview=preview,
        duplicate_review_queue_export_path=queue_path,
    )

    assert state.status_label == "测试中"
    assert state.duplicate_group_count == 2
    assert state.exact_duplicate_group_count == 1
    assert state.suspected_duplicate_group_count == 1
    assert state.duplicate_review_queue_export_path.endswith("_duplicate_review_queue.csv")
    exact = state.group_summaries[0]
    suspected = state.group_summaries[1]
    assert exact.group_id == "dup-exact"
    assert exact.record_ids == ("rec-1", "rec-2")
    assert exact.duplicate_type == "exact"
    assert exact.reason == "pmid_exact,doi_exact"
    assert exact.confidence == 1.0
    assert exact.master_candidate_id == "rec-1"
    assert exact.merge_preview_available is True
    assert suspected.group_id == "dup-suspected"
    assert suspected.record_ids == ("rec-3", "rec-4")
    assert suspected.duplicate_type == "suspected"


def test_duplicate_review_queue_csv_exports_readonly_summary_without_decisions(tmp_path: Path) -> None:
    service = DedupDecisionService(storage_root=tmp_path)
    review_path = _write_review_fixture(tmp_path)

    queue_path = Path(service.export_duplicate_review_queue(duplicate_review_path=str(review_path)))
    rows = list(csv.DictReader(queue_path.open(encoding="utf-8")))

    assert queue_path.exists()
    assert rows[0]["group_id"] == "dup-exact"
    assert rows[0]["duplicate_type"] == "exact"
    assert rows[0]["record_ids"] == "rec-1|rec-2"
    assert rows[0]["reason"] == "pmid_exact,doi_exact"
    assert rows[0]["master_candidate_id"] == "rec-1"
    assert rows[0]["merge_preview_available"] == "yes"
    assert rows[1]["group_id"] == "dup-suspected"
    assert rows[1]["duplicate_type"] == "suspected"
    assert not review_path.with_name("batch_dedup_decisions.json").exists()


def test_merge_preview_is_readable_and_does_not_auto_merge_records(tmp_path: Path) -> None:
    service = DedupDecisionService(storage_root=tmp_path)
    review_path = _write_review_fixture(tmp_path)

    preview = service.preview_merge(duplicate_review_path=str(review_path), group_id="dup-exact")
    source_payload_before = json.loads(Path(json.loads(review_path.read_text(encoding="utf-8"))["source_path"]).read_text(encoding="utf-8"))

    assert preview.group_id == "dup-exact"
    assert preview.merged_from_record_ids == ["rec-1", "rec-2"]
    assert preview.merged_record["record_id"] == "merged-dup-exact"
    assert preview.merged_record["title"] == "Complete trial title with subtitle"
    assert preview.field_sources["title"] == "rec-2"
    assert preview.field_sources["pmid"] == "rec-1"
    assert preview.warnings == []
    assert not review_path.with_name("batch_dedup_decisions.json").exists()
    source_payload_after = json.loads(Path(json.loads(review_path.read_text(encoding="utf-8"))["source_path"]).read_text(encoding="utf-8"))
    assert source_payload_after == source_payload_before


def test_duplicate_review_summary_handles_empty_groups() -> None:
    state = duplicate_review_state_from_groups(groups=[], original_record_count=0)

    assert state.duplicate_group_count == 0
    assert state.exact_duplicate_group_count == 0
    assert state.suspected_duplicate_group_count == 0
    assert state.group_summaries == ()
    assert state.current_group is None
