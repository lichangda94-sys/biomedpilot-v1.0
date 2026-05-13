from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.attachment_page import attachment_state_from_project
from app.meta_analysis.pages.duplicate_review_page import duplicate_review_state_from_groups
from app.meta_analysis.pages.literature_import_page import import_diagnostics_visual_summary
from app.meta_analysis.services.attachment_service import AttachmentService
from app.meta_analysis.services.dedup_decision_service import DedupDecisionService
from app.meta_analysis.workspace import literature_import_quality_dashboard_state, recent_import_batch_summaries


def test_aa1_import_diagnostics_panel_summary_and_missing_file(tmp_path: Path) -> None:
    diagnostics_path = tmp_path / "batch-aa1_import_diagnostics.json"
    diagnostics_path.write_text(
        json.dumps(
            {
                "warning_count": 8,
                "failed_record_count": 1,
                "missing_title_count": 1,
                "missing_author_count": 2,
                "missing_year_count": 3,
                "missing_doi_count": 4,
                "missing_pmid_count": 5,
                "invalid_doi_count": 1,
                "invalid_year_count": 1,
                "failed_record_examples": ["row 2 missing title"],
            }
        ),
        encoding="utf-8",
    )

    state = import_diagnostics_visual_summary(str(diagnostics_path))
    missing = import_diagnostics_visual_summary(str(tmp_path / "missing_import_diagnostics.json"))
    cards = {card.key: card.value for card in state.summary_cards}
    warnings = {row.key: row.count for row in state.warning_rows}

    assert state.total_warning_count == 8
    assert cards["missing_title_count"] == 1
    assert cards["missing_author_count"] == 2
    assert cards["missing_year_count"] == 3
    assert cards["missing_doi_count"] == 4
    assert cards["missing_pmid_count"] == 5
    assert cards["invalid_doi_count"] == 1
    assert cards["invalid_year_count"] == 1
    assert warnings["failed_record_count"] == 1
    assert state.failed_record_examples == ("row 2 missing title",)
    assert state.diagnostics_path == str(diagnostics_path)
    assert missing.missing_diagnostics is True
    assert missing.summary_cards


def test_aa1_recent_import_batches_panel_empty_and_linked_record_count(tmp_path: Path) -> None:
    empty_state = literature_import_quality_dashboard_state(tmp_path)
    assert empty_state.batch_count == 0
    assert "暂无导入批次" in empty_state.empty_state

    literature_dir = tmp_path / "literature"
    diagnostics_dir = literature_dir / "import_diagnostics"
    diagnostics_dir.mkdir(parents=True)
    (literature_dir / "import_batches.json").write_text(
        json.dumps(
            [
                {
                    "batch_id": "batch-aa1",
                    "project_id": "meta-test",
                    "source_type": "PubMed",
                    "format_hint": "nbib",
                    "status": "completed",
                    "raw_record_count": 3,
                    "parsed_record_count": 3,
                    "normalized_record_count": 2,
                    "failed_record_count": 1,
                    "warning_count": 4,
                    "duplicate_candidate_count": 1,
                    "created_at": "2026-04-29T00:00:00+08:00",
                }
            ]
        ),
        encoding="utf-8",
    )
    (diagnostics_dir / "batch-aa1_import_diagnostics.json").write_text(
        json.dumps({"missing_doi_count": 1, "warning_count": 4}),
        encoding="utf-8",
    )

    state = literature_import_quality_dashboard_state(tmp_path)
    recent = recent_import_batch_summaries(tmp_path)

    assert state.batch_count == 1
    assert state.batches[0].batch_id == "batch-aa1"
    assert state.batches[0].linked_literature_record_count == 2
    assert state.batches[0].duplicate_candidate_count == 1
    assert recent[0]["batch_id"] == "batch-aa1"
    assert recent[0]["linked_literature_record_count"] == 2


def test_aa1_attachment_registry_panel_summary_and_missing_registry(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    missing_state = attachment_state_from_project(project_dir, service=AttachmentService())

    assert missing_state.attachment_registry_missing is True
    assert "attachment_registry.json 尚未生成" in missing_state.attachment_registry_warning
    assert missing_state.missing_fulltext_report_path.endswith("missing_fulltext_report.csv")

    registry_path = project_dir / "attachments" / "attachment_registry.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps(
            {
                "project_id": "meta-project",
                "ignored_attachments": [{"record_id": "rec-ignore"}],
                "attachments": [
                    {
                        "attachment_id": "att-linked",
                        "record_id": "rec-1",
                        "attachment_type": "pdf",
                        "file_path": str(tmp_path / "linked.pdf"),
                        "file_name": "linked.pdf",
                        "file_exists": False,
                        "file_size": 0,
                        "checksum": "",
                        "added_at": "2026-04-29T00:00:00+08:00",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (project_dir / "reports").mkdir()
    (project_dir / "reports" / "missing_fulltext_report.csv").write_text(
        "record_id,missing_fulltext\nrec-1,true\n",
        encoding="utf-8",
    )

    state = attachment_state_from_project(project_dir, service=AttachmentService())

    assert state.attachment_registry_missing is False
    assert state.attachment_count == 1
    assert state.pdf_attachment_count == 1
    assert state.link_attachment_count == 1
    assert state.copy_attachment_count == 0
    assert state.ignore_attachment_count == 1
    assert state.missing_attachment_count == 1
    assert state.broken_path_count == 1
    assert state.missing_fulltext_report_status == "available"
    assert state.missing_fulltext_count == 1


def test_aa1_duplicate_merge_preview_field_conflicts_and_old_decisions(tmp_path: Path) -> None:
    source_path = tmp_path / "screening_ready.json"
    source_path.write_text(
        json.dumps(
            {
                "project_id": "meta-test",
                "records": [
                    {
                        "record_id": "rec-1",
                        "source": "nbib",
                        "title": "Short title",
                        "authors": ["Smith J"],
                        "year": 2023,
                        "journal": "J Clin",
                        "doi": "10.1000/a",
                        "pmid": "111",
                        "clinical_trials_ids": ["NCT0001"],
                    },
                    {
                        "record_id": "rec-2",
                        "source": "ris",
                        "title": "Longer title for the same trial",
                        "creators": [{"full_name": "Smith John", "creator_type": "author", "order": 1}],
                        "date": "2024-01-01",
                        "publication_title": "Journal of Clinical Trials",
                        "doi": "10.1000/b",
                        "pmid": "222",
                        "clinical_trials_ids": ["NCT0002"],
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
                        "duplicate_group_id": "dup-aa1",
                        "candidate_record_ids": ["rec-1", "rec-2"],
                        "match_reason": "doi_exact,title_author_year_journal_suspected",
                        "confidence": 0.9,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    review_path.with_name("batch_dedup_decisions.json").write_text(
        json.dumps(
            {
                "decisions": [
                    {
                        "decision_id": "legacy-decision",
                        "group_id": "dup-aa1",
                        "decision": "keep_first",
                        "selected_record_id": "rec-1",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    service = DedupDecisionService(storage_root=tmp_path)
    groups = service.load_groups(duplicate_review_path=str(review_path))
    preview = service.preview_merge(duplicate_review_path=str(review_path), group_id="dup-aa1")
    state = duplicate_review_state_from_groups(groups=groups, original_record_count=2, merge_preview=preview)
    conflict_names = {item.field_name for item in state.field_conflict_summary}

    assert groups[0].status == "resolved"
    assert state.decision_options[:3] == ("keep_first", "keep_second", "merge")
    assert state.canonical_candidate_id
    assert "doi_exact" in state.match_reasons
    assert "title" in conflict_names
    assert "creators/authors" in conflict_names
    assert "year/date" in conflict_names
    assert "journal/publication_title" in conflict_names
    assert "doi" in conflict_names
    assert "pmid" in conflict_names
    assert "clinical_trials_ids" in conflict_names
    assert "authors" in state.field_conflicts
    assert state.merge_preview_summary.available is True
