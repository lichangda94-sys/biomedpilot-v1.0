from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.literature_library_page import literature_library_state_from_project
from app.meta_analysis.pages.protocol_page import write_pubmed_search_execution_artifacts
from app.meta_analysis.search.pubmed_candidates_handoff_service import PubMedCandidatesHandoffService
from app.meta_analysis.search.pubmed_search_service import PubMedSearchExecution, PubMedSearchResult
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.formal_report_service import PRISMAService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


def test_pubmed_candidates_preview_does_not_enter_literature_library(tmp_path: Path) -> None:
    paths = write_pubmed_search_execution_artifacts(tmp_path, '"Obesity"[Mesh]', _execution())

    preview = json.loads(Path(paths["pubmed_candidates_preview"]).read_text(encoding="utf-8"))
    governance_events = MetaResearchGovernanceService().list_events(tmp_path)

    assert preview["schema_version"] == "meta_pubmed_candidate_preview.v1"
    assert preview["candidate_count"] == 2
    assert preview["candidates"][0]["user_decision"] == "pending"
    assert preview["auto_imported"] is False
    assert preview["auto_screened"] is False
    assert not (tmp_path / "literature" / "literature_records.json").exists()
    assert not (tmp_path / "screening").exists()
    assert any(event.action == "draft_created" and event.target_type == "literature_inclusion" for event in governance_events)


def test_only_selected_pubmed_candidates_import_to_normalized_library(tmp_path: Path) -> None:
    paths = write_pubmed_search_execution_artifacts(tmp_path, '"Obesity"[Mesh]', _execution())
    preview_id = _preview_id(paths["pubmed_candidates_preview"])

    result = PubMedCandidatesHandoffService().import_selected_candidates(
        tmp_path,
        preview_id=preview_id,
        selected_candidate_ids=("pcand-111",),
        rejected_candidate_ids=("pcand-222",),
        actor="reviewer",
    )
    library = json.loads(Path(result.literature_records_path).read_text(encoding="utf-8"))
    records = library["records"]
    record = records[0]

    assert result.success
    assert result.selected_count == 1
    assert result.rejected_count == 1
    assert result.imported_count == 1
    assert len(records) == 1
    assert record["pmid"] == "111"
    assert record["doi"] == "10.1000/demo111"
    assert record["title"] == "Obesity and thyroid cancer risk"
    assert record["database_source"] == "PubMed"
    assert record["source"] == "pubmed_confirmed_candidates"
    assert record["record_status"] == "imported_pending_dedup"
    assert record["screening_status"] == "not_started"
    assert record["dedup_status"] == "pending_review"
    assert record["provenance"]["candidate_preview_id"] == preview_id
    assert record["provenance"]["pubmed_execution_report_path"] == "protocol/search_execution_report.json"
    assert "222" not in json.dumps(records)


def test_pubmed_candidate_handoff_writes_batch_audit_governance_and_dedup_queue(tmp_path: Path) -> None:
    paths = write_pubmed_search_execution_artifacts(tmp_path, '"Obesity"[Mesh]', _execution())
    preview_id = _preview_id(paths["pubmed_candidates_preview"])

    result = PubMedCandidatesHandoffService().import_selected_candidates(
        tmp_path,
        preview_id=preview_id,
        selected_candidate_ids=("111", "222"),
        actor="reviewer",
    )
    batch_payload = json.loads(Path(result.import_batch_path).read_text(encoding="utf-8"))
    dedup_payload = json.loads(Path(result.dedup_queue_path).read_text(encoding="utf-8"))
    handoff_audit = json.loads(Path(result.handoff_audit_path).read_text(encoding="utf-8"))
    audit_events = MetaAuditLogService().list_events(tmp_path)
    governance_events = MetaResearchGovernanceService().list_events(tmp_path)

    assert batch_payload["import_batches"][-1]["source_type"] == "pubmed_confirmed_candidates"
    assert batch_payload["import_batches"][-1]["selected_count"] == 2
    assert batch_payload["import_batches"][-1]["imported_count"] == 2
    assert dedup_payload["status"] == "pending_reviewer_decision"
    assert dedup_payload["auto_merged"] is False
    assert dedup_payload["screening_status"] == "not_started"
    assert handoff_audit["schema_version"] == "meta_pubmed_candidate_handoff.v1"
    assert handoff_audit["prisma_status"] == "not_updated"
    assert any(event.event_type == "pubmed_candidate_handoff" for event in audit_events)
    assert any(event.action == "accept" and event.status == "user_accepted" for event in governance_events)
    assert any(event.action == "confirm" and event.target_id == result.import_batch_id for event in governance_events)


def test_pubmed_candidate_handoff_does_not_create_screening_or_advance_prisma_review_counts(tmp_path: Path) -> None:
    paths = write_pubmed_search_execution_artifacts(tmp_path, '"Obesity"[Mesh]', _execution())
    preview_id = _preview_id(paths["pubmed_candidates_preview"])

    PubMedCandidatesHandoffService().import_selected_candidates(
        tmp_path,
        preview_id=preview_id,
        selected_candidate_ids=("pcand-111",),
        actor="reviewer",
    )
    prisma = PRISMAService().collect_prisma_numbers(tmp_path)

    assert not (tmp_path / "screening").exists()
    assert not (tmp_path / "reports" / "prisma_flow_summary.json").exists()
    assert prisma.records_screened == 0
    assert prisma.records_excluded_title_abstract == 0
    assert prisma.full_text_reports_sought == 0
    assert prisma.full_text_reports_assessed == 0
    assert prisma.studies_included == 0
    assert prisma.reports_included == 0


def test_literature_library_can_read_imported_pubmed_candidates(tmp_path: Path) -> None:
    paths = write_pubmed_search_execution_artifacts(tmp_path, '"Obesity"[Mesh]', _execution())
    preview_id = _preview_id(paths["pubmed_candidates_preview"])
    PubMedCandidatesHandoffService().import_selected_candidates(
        tmp_path,
        preview_id=preview_id,
        selected_candidate_ids=("pcand-111",),
        actor="reviewer",
    )

    state = literature_library_state_from_project(tmp_path)

    assert state.total_records == 1
    assert state.rows[0].pmid == "111"
    assert state.rows[0].source_database == "PubMed"
    assert state.rows[0].screening_status == "not_started"


def _execution() -> PubMedSearchExecution:
    return PubMedSearchExecution(
        success=True,
        query_used='"Obesity"[Mesh]',
        executed_at="2026-05-06T00:00:00+00:00",
        result_count=2,
        returned_count=2,
        search_execution_id="pubmedexec-test",
        records=(
            PubMedSearchResult(
                pmid="111",
                doi="10.1000/demo111",
                title="Obesity and thyroid cancer risk",
                journal="Meta Trial Journal",
                year="2024",
                publication_date="2024-01-02",
                authors=("Alice Adams",),
                abstract="Candidate abstract for thyroid cancer risk.",
                snippet="Candidate abstract for thyroid cancer risk.",
                url="https://pubmed.ncbi.nlm.nih.gov/111/",
                query_used='"Obesity"[Mesh]',
            ),
            PubMedSearchResult(
                pmid="222",
                doi="10.1000/demo222",
                title="BMI and thyroid neoplasms",
                journal="Meta Review Journal",
                year="2025",
                publication_date="2025",
                authors=("Ben Baker",),
                abstract="Second candidate abstract.",
                snippet="Second candidate abstract.",
                url="https://pubmed.ncbi.nlm.nih.gov/222/",
                query_used='"Obesity"[Mesh]',
            ),
        ),
    )


def _preview_id(path: str) -> str:
    return Path(path).name.replace("_candidates_preview.json", "")
