from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.models.dedup import DuplicateGroup
from app.meta_analysis.pages.attachment_page import attachment_state_from_project, initial_attachment_state
from app.meta_analysis.pages.audit_log_page import audit_log_state_from_project, initial_audit_log_state
from app.meta_analysis.pages.duplicate_review_page import duplicate_review_state_from_groups
from app.meta_analysis.pages.literature_import_page import literature_import_state_from_result
from app.meta_analysis.services.attachment_service import AttachmentService
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.dedup_decision_service import DedupDecisionService
from app.meta_analysis.services.literature_import_service import LiteratureImportService
from app.meta_analysis.workspace import recent_import_batch_summaries
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter


def test_import_page_state_exposes_diagnostics_warnings_failed_preview_and_recent_batches(tmp_path: Path) -> None:
    source = tmp_path / "records.csv"
    source.write_text(
        "title,authors,year,doi,pmid,abstract\n"
        "Trial A,Smith J,2024,10.1000/a,111,Abstract\n"
        ",No Title,2024,,222,\n",
        encoding="utf-8",
    )
    service = LiteratureImportService(
        task_center=TaskCenter(tmp_path / "tasks" / "tasks.json"),
        data_center=DataCenter(tmp_path / "data" / "data_assets.json"),
        storage_root=tmp_path,
    )
    result = service.import_file(project_id="meta-test", source_path=str(source))
    recent = recent_import_batch_summaries(tmp_path)
    state = literature_import_state_from_result(result, recent_import_batches=recent)

    assert state.status_label == "测试中"
    assert state.diagnostics_summary is not None
    assert state.diagnostics_summary["missing_title_count"] == 1
    assert state.diagnostics_export_path.endswith("_import_diagnostics.json")
    assert state.warnings_export_path.endswith("_import_warnings.csv")
    assert state.failed_records_preview
    assert state.recent_import_batches[0]["parsed_count"] == 2


def test_attachment_page_state_exposes_registry_missing_report_and_modes(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    source_pdf = tmp_path / "paper.pdf"
    source_pdf.write_bytes(b"%PDF-1.4")
    service = AttachmentService(
        task_center=TaskCenter(tmp_path / "tasks" / "tasks.json"),
        data_center=DataCenter(tmp_path / "data" / "data_assets.json"),
    )
    service.add_attachment(project_dir, record_id="rec-1", source_file_path=str(source_pdf), attachment_type="pdf", mode="link_existing_files")
    service.export_missing_fulltext_report(project_dir, record_ids=["rec-1", "rec-2"])

    initial = initial_attachment_state()
    state = attachment_state_from_project(project_dir, service=service)

    assert initial.status_label == "测试中"
    assert "link_existing_files" in state.mode_options
    assert "copy_to_project_library" in state.mode_options
    assert "ignore_attachments" in state.mode_options
    assert state.attachment_registry_path.endswith("attachment_registry.json")
    assert state.missing_fulltext_report_path.endswith("missing_fulltext_report.csv")
    assert state.attachment_count == 1
    assert state.missing_fulltext_count == 1
    assert state.file_status_summary[0].startswith("rec-1:pdf:available")


def test_duplicate_review_page_state_exposes_merge_preview_canonical_candidate_and_conflicts(tmp_path: Path) -> None:
    source_path = tmp_path / "screening_ready.json"
    review_path = tmp_path / "batch_duplicate_groups.json"
    source_path.write_text(
        json.dumps(
            {
                "records": [
                    {"record_id": "rec-1", "source": "nbib", "title": "Short", "abstract": "", "authors": ["Smith J"], "journal": "J", "pmid": "123"},
                    {"record_id": "rec-2", "source": "ris", "title": "Longer complete title", "abstract": "Long abstract", "authors": ["Smith J", "Wang M"], "journal": "Journal", "doi": "10.1000/a"},
                ]
            }
        ),
        encoding="utf-8",
    )
    review_path.write_text(
        json.dumps(
            {
                "project_id": "meta-test",
                "source_path": str(source_path),
                "duplicate_groups": [{"group_id": "dup-1", "record_ids": ["rec-1", "rec-2"], "reason": "pmid_exact,title_author_year_journal_suspected", "confidence": 0.98}],
            }
        ),
        encoding="utf-8",
    )
    service = DedupDecisionService(storage_root=tmp_path)
    group = service.load_groups(duplicate_review_path=str(review_path))[0]
    preview = service.preview_merge(duplicate_review_path=str(review_path), group_id=group.group_id)
    state = duplicate_review_state_from_groups(groups=[group], original_record_count=2, merge_preview=preview)

    assert state.merge_preview is not None
    assert "pmid_exact" in state.match_reasons
    assert "title" in state.field_conflicts
    assert "authors" in state.field_conflicts
    assert state.canonical_candidate_id
    assert "merge" in state.decision_options
    assert "set_master_record" in state.decision_options


def test_audit_log_page_state_exposes_readonly_event_summary(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    service = MetaAuditLogService()
    service.record_event(project_dir, event_type="import_batch_created", target_type="import_batch", target_id="batch-1", summary="created")
    service.record_event(project_dir, event_type="diagnostics_generated", target_type="diagnostics", target_id="batch-1", summary="diagnostics")
    service.record_event(project_dir, event_type="report_exported", target_type="report", target_id="report-1", summary="report")

    initial = initial_audit_log_state()
    state = audit_log_state_from_project(project_dir, service=service)

    assert initial.status_label == "测试中"
    assert state.audit_log_path.endswith("audit_log.jsonl")
    assert state.event_count == 3
    assert state.event_type_counts == {"import_batch_created": 1, "diagnostics_generated": 1, "report_exported": 1}
    assert any("report_exported" in item for item in state.recent_events)


def test_audit_log_page_state_handles_missing_log_without_crashing(tmp_path: Path) -> None:
    state = audit_log_state_from_project(tmp_path / "empty-project")

    assert state.event_count == 0
    assert state.event_type_counts == {}
    assert state.recent_events == ()
    assert "warning" in state.warning_summary.lower()

