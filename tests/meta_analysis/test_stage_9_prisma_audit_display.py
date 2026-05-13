from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.audit_log_page import audit_log_state_from_project
from app.meta_analysis.pages.reporting_page import reporting_prisma_trace_state_from_project
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.formal_report_service import PRISMAService


def test_reporting_prisma_trace_state_shows_summary_source_and_audit_warnings(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    (project_dir / "literature").mkdir(parents=True)
    (project_dir / "screening").mkdir(parents=True)
    (project_dir / "literature" / "records.json").write_text(
        json.dumps({"records": [{"record_id": "rec-1"}, {"record_id": "rec-2"}]}),
        encoding="utf-8",
    )
    (project_dir / "screening" / "screening_decisions.json").write_text(
        json.dumps({"screening_records": [{"record_id": "rec-1", "decision": "included"}]}),
        encoding="utf-8",
    )
    audit = MetaAuditLogService()
    audit.record_event(project_dir, event_type="import_batch_created", target_type="import_batch", target_id="batch-1", summary="import")
    audit.record_event(project_dir, event_type="screening_decision", target_type="screening", target_id="rec-1", summary="screening")

    state = reporting_prisma_trace_state_from_project(project_dir, audit_log=audit)

    assert state.summary is not None
    assert state.summary.records_identified == 2
    assert state.summary.records_screened == 1
    assert any(row.source_type == "ImportBatch" and row.status == "available" for row in state.source_references)
    assert any("DuplicateReviewDecision" in warning for warning in state.source_reference_warnings)
    assert state.workflow_event_counts["import"] == 1
    assert state.workflow_event_counts["screening"] == 1
    assert any("dedup" in warning for warning in state.audit_reference_warnings)
    assert state.review_log_jsonl_path.endswith("review_log.jsonl")
    assert state.review_log_csv_path.endswith("review_log.csv")


def test_reporting_prisma_trace_state_handles_missing_sources_and_missing_audit(tmp_path: Path) -> None:
    project_dir = tmp_path / "empty-project"

    state = reporting_prisma_trace_state_from_project(project_dir)

    assert state.summary is not None
    assert state.summary.records_identified == 0
    assert state.source_reference_warnings
    assert state.audit_reference_warnings
    assert all(count == 0 for count in state.workflow_event_counts.values())


def test_audit_page_state_exposes_workflow_counts_and_review_log_paths(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    audit = MetaAuditLogService()
    audit.record_event(project_dir, event_type="import_batch_created", target_type="import_batch", target_id="batch-1", summary="import")
    audit.record_event(project_dir, event_type="duplicate_decision", target_type="duplicate_group", target_id="dup-1", summary="dedup")
    audit.record_event(project_dir, event_type="fulltext_status_changed", target_type="fulltext", target_id="ft-1", summary="fulltext")
    audit.record_event(project_dir, event_type="extraction_updated", target_type="extraction", target_id="ext-1", summary="extraction")
    audit.record_event(project_dir, event_type="analysis_run_completed", target_type="analysis", target_id="res-1", summary="analysis")
    audit.record_event(project_dir, event_type="report_exported", target_type="report", target_id="report-1", summary="report")

    state = audit_log_state_from_project(project_dir, service=audit)

    assert state.event_count == 6
    assert state.workflow_event_counts == {
        "import": 1,
        "dedup": 1,
        "screening": 0,
        "fulltext": 1,
        "extraction": 1,
        "analysis": 1,
        "report": 1,
    }
    assert state.review_log_jsonl_path.endswith("review_log.jsonl")
    assert state.review_log_csv_path.endswith("review_log.csv")


def test_audit_service_exports_review_log_jsonl_and_csv_even_when_audit_missing(tmp_path: Path) -> None:
    project_dir = tmp_path / "empty-project"
    audit = MetaAuditLogService()

    jsonl_path = audit.export_review_log_jsonl(project_dir)
    csv_path = audit.export_review_log_csv(project_dir)

    assert jsonl_path.exists()
    assert jsonl_path.read_text(encoding="utf-8") == ""
    assert csv_path.exists()
    assert "event_id,event_type,project_id" in csv_path.read_text(encoding="utf-8")


def test_prisma_markdown_includes_source_references(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    (project_dir / "literature").mkdir(parents=True)
    (project_dir / "literature" / "records.json").write_text(json.dumps({"records": [{"record_id": "rec-1"}]}), encoding="utf-8")
    service = PRISMAService()

    summary = service.collect_prisma_numbers(project_dir)
    markdown_path = service.export_prisma_flow_markdown(project_dir, summary)
    text = markdown_path.read_text(encoding="utf-8")

    assert "## Source References" in text
    assert "ImportBatch" in text
    assert "ScreeningRecord" in text
