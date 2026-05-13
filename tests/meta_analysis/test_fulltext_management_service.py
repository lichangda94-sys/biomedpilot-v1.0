from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.fulltext_eligibility_page import fulltext_eligibility_state_from_project
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.formal_report_service import PRISMAService
from app.meta_analysis.services.fulltext_management_service import (
    FULLTEXT_EXCLUSION_REASON_FULL_TEXT_UNAVAILABLE,
    FULLTEXT_EXCLUSION_REASON_WRONG_POPULATION,
    FULLTEXT_EXCLUSION_REASONS_M4C,
    FULLTEXT_MANAGEMENT_REGISTRY_SCHEMA_VERSION,
    FULLTEXT_STATUS_FULL_TEXT_CONFIRMED,
    FULLTEXT_STATUS_FULL_TEXT_NEEDED,
    FULLTEXT_STATUS_FULL_TEXT_UPLOADED,
    FULLTEXT_STATUS_FULL_TEXT_UNAVAILABLE,
    FULLTEXT_STATUS_LINK_AVAILABLE,
    FULLTEXT_STATUS_NEEDS_MANUAL_RETRIEVAL,
    FULLTEXT_STATUS_PDF_ATTACHED,
    FullTextManagementService,
)
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


def test_fulltext_management_builds_registry_from_screening_without_prisma_or_screening_decision(tmp_path: Path) -> None:
    _seed_screening_decisions(tmp_path)

    result = FullTextManagementService().build_registry_from_screening(tmp_path, project_id="meta-fulltext")
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    records = {record["record_id"]: record for record in payload["records"]}
    prisma = PRISMAService().collect_prisma_numbers(tmp_path)

    assert result.success
    assert payload["schema_version"] == FULLTEXT_MANAGEMENT_REGISTRY_SCHEMA_VERSION
    assert payload["auto_pdf_fetch"] is False
    assert payload["auto_fulltext_screening"] is False
    assert records["rec-1"]["fulltext_status"] == FULLTEXT_STATUS_FULL_TEXT_NEEDED
    assert records["rec-1"]["authors"] == "Zhang Wei, Li Ming"
    assert records["rec-1"]["journal"] == "Journal A"
    assert records["rec-1"]["year"] == "2025"
    assert records["rec-1"]["links"][0]["link_type"] == "doi"
    assert "rec-3" not in records
    assert not (tmp_path / "fulltext" / "fulltext_screening_decisions.json").exists()
    assert prisma.records_screened == 3
    assert prisma.full_text_reports_assessed == 2
    assert prisma.full_text_reports_excluded == 0


def test_fulltext_management_adds_link_and_marks_unavailable_with_audit_governance(tmp_path: Path) -> None:
    _seed_screening_decisions(tmp_path)
    service = FullTextManagementService()
    service.build_registry_from_screening(tmp_path, project_id="meta-fulltext")

    link_result = service.add_link(
        tmp_path,
        record_id="rec-1",
        link_type="publisher",
        url="https://example.org/article",
        actor="reviewer",
        notes="Publisher page found.",
    )
    unavailable = service.mark_unavailable(
        tmp_path,
        record_id="rec-2",
        reason=FULLTEXT_EXCLUSION_REASON_FULL_TEXT_UNAVAILABLE,
        actor="reviewer",
    )
    audit_events = MetaAuditLogService().list_events(tmp_path)
    governance_events = MetaResearchGovernanceService().list_events(tmp_path)

    assert link_result.success
    assert link_result.record.fulltext_status == FULLTEXT_STATUS_LINK_AVAILABLE
    assert any(link["link_type"] == "publisher" for link in link_result.record.links)
    assert unavailable.record.fulltext_status == FULLTEXT_STATUS_FULL_TEXT_UNAVAILABLE
    assert unavailable.record.unavailable_reason == FULLTEXT_EXCLUSION_REASON_FULL_TEXT_UNAVAILABLE
    assert unavailable.record.fulltext_exclusion_reason == FULLTEXT_EXCLUSION_REASON_FULL_TEXT_UNAVAILABLE
    assert any(event.event_type == "fulltext_status_changed" and event.target_type == "fulltext_management_record" for event in audit_events)
    assert any(event.target_type == "fulltext_management" and event.status == "confirmed" for event in governance_events)
    assert not (tmp_path / "fulltext" / "fulltext_screening_decisions.json").exists()


def test_fulltext_management_attach_pdf_copies_to_project_and_does_not_parse(tmp_path: Path) -> None:
    _seed_screening_decisions(tmp_path)
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%test\n")
    service = FullTextManagementService()
    service.build_registry_from_screening(tmp_path, project_id="meta-fulltext")

    result = service.attach_pdf(tmp_path, record_id="rec-1", source_file_path=str(pdf), actor="reviewer", notes="Local PDF")
    record = service.get_record(tmp_path, "rec-1")

    assert result.success
    assert record is not None
    assert record.fulltext_status == FULLTEXT_STATUS_PDF_ATTACHED
    assert Path(record.pdf_path).exists()
    assert "rec-1_source.pdf" in record.pdf_path
    assert not (tmp_path / "fulltext" / "parsed_fulltext").exists()
    assert not (tmp_path / "fulltext" / "fulltext_screening_decisions.json").exists()


def test_fulltext_management_page_state_exposes_registry_counts(tmp_path: Path) -> None:
    _seed_screening_decisions(tmp_path)
    service = FullTextManagementService()
    service.build_registry_from_screening(tmp_path, project_id="meta-fulltext")
    service.add_link(tmp_path, record_id="rec-1", link_type="pubmed", url="https://pubmed.ncbi.nlm.nih.gov/111/", actor="reviewer")

    state = fulltext_eligibility_state_from_project(tmp_path, fulltext_management_service=service)

    assert state.fulltext_management_schema_version == FULLTEXT_MANAGEMENT_REGISTRY_SCHEMA_VERSION
    assert state.fulltext_management_record_count == 2
    assert state.fulltext_management_status_counts[FULLTEXT_STATUS_LINK_AVAILABLE] == 1
    assert state.output_paths["fulltext_management_registry"].endswith("fulltext/fulltext_management_registry_v1.json")


def test_fulltext_management_validates_actor_link_type_and_unavailable_reason(tmp_path: Path) -> None:
    service = FullTextManagementService()

    missing_actor = service.add_link(tmp_path, record_id="rec-1", link_type="pubmed", url="https://pubmed.ncbi.nlm.nih.gov/111/", actor="")
    bad_link = service.add_link(tmp_path, record_id="rec-1", link_type="unknown", url="https://example.org", actor="reviewer")
    no_reason = service.mark_unavailable(tmp_path, record_id="rec-1", reason="", actor="reviewer")
    bad_reason = service.mark_unavailable(tmp_path, record_id="rec-1", reason="free text reason", actor="reviewer")
    suggested_status = service.update_status(tmp_path, record_id="rec-1", status="suggested_include", actor="reviewer")

    assert not missing_actor.success
    assert "actor" in missing_actor.message
    assert not bad_link.success
    assert "unsupported" in bad_link.message
    assert not no_reason.success
    assert "reason" in no_reason.message
    assert not bad_reason.success
    assert "reason" in bad_reason.message
    assert not suggested_status.success
    assert "unsupported" in suggested_status.message


def test_fulltext_management_status_transition_rules_and_summary(tmp_path: Path) -> None:
    _seed_screening_decisions(tmp_path)
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%test\n")
    service = FullTextManagementService()
    service.build_registry_from_screening(tmp_path, project_id="meta-fulltext")

    blocked = service.update_status(tmp_path, record_id="rec-1", status=FULLTEXT_STATUS_FULL_TEXT_CONFIRMED, actor="reviewer")
    uploaded = service.attach_pdf(tmp_path, record_id="rec-1", source_file_path=str(pdf), actor="reviewer")
    confirmed = service.update_status(tmp_path, record_id="rec-1", status=FULLTEXT_STATUS_FULL_TEXT_CONFIRMED, actor="reviewer")
    excluded = service.mark_excluded(tmp_path, record_id="rec-2", reason=FULLTEXT_EXCLUSION_REASON_WRONG_POPULATION, actor="reviewer")
    summary = service.summary_counts(tmp_path)

    assert not blocked.success
    assert "transition" in blocked.message
    assert uploaded.success
    assert uploaded.record.fulltext_status == FULLTEXT_STATUS_FULL_TEXT_UPLOADED
    assert confirmed.success
    assert confirmed.record.fulltext_status == FULLTEXT_STATUS_FULL_TEXT_CONFIRMED
    assert excluded.success
    assert excluded.record.fulltext_exclusion_reason == FULLTEXT_EXCLUSION_REASON_WRONG_POPULATION
    assert summary[FULLTEXT_STATUS_FULL_TEXT_NEEDED] == 0
    assert summary[FULLTEXT_STATUS_FULL_TEXT_CONFIRMED] == 1
    assert summary["ready_for_extraction"] == 1
    assert summary["full_text_excluded"] == 1


def test_fulltext_management_safe_file_label_hides_raw_paths(tmp_path: Path) -> None:
    _seed_screening_decisions(tmp_path)
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%test\n")
    service = FullTextManagementService()
    service.build_registry_from_screening(tmp_path, project_id="meta-fulltext")
    service.attach_pdf(tmp_path, record_id="rec-1", source_file_path=str(pdf), actor="reviewer")
    record = service.get_record(tmp_path, "rec-1")

    assert record is not None
    label = service.safe_file_label(record)

    assert "已登记全文文件" in label
    assert "source.pdf" in label
    assert str(tmp_path) not in label
    assert set(FULLTEXT_EXCLUSION_REASONS_M4C) >= {
        "full_text_unavailable",
        "wrong_population",
        "wrong_intervention_or_exposure",
        "wrong_comparator",
        "wrong_outcome",
        "wrong_study_type",
        "duplicate_after_full_text",
        "insufficient_data",
        "other",
    }


def _seed_screening_decisions(project_dir: Path) -> None:
    path = project_dir / "screening" / "screening_decisions.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "screening_records": [
                    {
                        "record_id": "rec-1",
                        "screening_record_id": "screen-1",
                        "decision": "included",
                        "title": "Included trial",
                        "authors": ["Zhang Wei", "Li Ming"],
                        "journal": "Journal A",
                        "year": "2025",
                        "doi": "10.1000/fulltext.001",
                        "pmid": "111",
                    },
                    {
                        "record_id": "rec-2",
                        "screening_record_id": "screen-2",
                        "decision": "maybe",
                        "title": "Maybe trial",
                        "pmcid": "PMC222",
                    },
                    {
                        "record_id": "rec-3",
                        "screening_record_id": "screen-3",
                        "decision": "excluded",
                        "title": "Excluded trial",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
