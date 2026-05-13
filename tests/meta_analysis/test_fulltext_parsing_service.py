from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.fulltext_eligibility_page import fulltext_eligibility_state_from_project
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.formal_report_service import PRISMAService
from app.meta_analysis.services.fulltext_management_service import FullTextManagementService
from app.meta_analysis.services.fulltext_parsing_service import (
    FULLTEXT_PARSE_MANIFEST_SCHEMA_VERSION,
    FULLTEXT_PARSE_RESULT_SCHEMA_VERSION,
    FullTextParsingService,
)
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


def test_fulltext_parsing_extracts_text_sections_identifiers_and_manifest(tmp_path: Path) -> None:
    pdf = _write_text_pdf(tmp_path / "study.pdf")
    management = FullTextManagementService()
    management.attach_pdf(tmp_path, record_id="rec-1", source_file_path=str(pdf), actor="reviewer", notes="Local PDF")
    service = FullTextParsingService(fulltext_management=management)

    result = service.parse_record(tmp_path, record_id="rec-1")
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))
    extracted_text = Path(result.extracted_text_path).read_text(encoding="utf-8")

    assert result.success
    assert result.parse_status == "parsed"
    assert payload["schema_version"] == FULLTEXT_PARSE_RESULT_SCHEMA_VERSION
    assert payload["parser_level"] == "testing"
    assert "10.1000/fulltext.123" in payload["doi_candidates"]
    assert "12345678" in payload["pmid_candidates"]
    assert "abstract" in payload["section_paths"]
    assert "Methods text" in Path(result.section_paths["methods"]).read_text(encoding="utf-8")
    assert "Full text title" in extracted_text
    assert manifest["schema_version"] == FULLTEXT_PARSE_MANIFEST_SCHEMA_VERSION
    assert manifest["parsed_count"] == 1
    assert not (tmp_path / "extraction" / "extraction_records.json").exists()
    assert not (tmp_path / "quality" / "quality_assessments.json").exists()


def test_fulltext_parsing_missing_pdf_records_failure_without_crashing(tmp_path: Path) -> None:
    result = FullTextParsingService().parse_record(tmp_path, record_id="missing-rec")
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))

    assert not result.success
    assert result.parse_status == "parse_failed"
    assert result.diagnostics["error_code"] == "missing_pdf_path"
    assert payload["parse_status"] == "parse_failed"
    assert manifest["parse_failed_count"] == 1
    assert Path(result.extracted_text_path).exists()


def test_fulltext_parsing_writes_audit_and_governance_draft_not_final_decision(tmp_path: Path) -> None:
    pdf = _write_text_pdf(tmp_path / "study.pdf")
    management = FullTextManagementService()
    management.attach_pdf(tmp_path, record_id="rec-1", source_file_path=str(pdf), actor="reviewer")

    FullTextParsingService(fulltext_management=management).parse_record(tmp_path, record_id="rec-1")
    audit = MetaAuditLogService().list_events(tmp_path)
    governance = MetaResearchGovernanceService().list_events(tmp_path)
    prisma = PRISMAService().collect_prisma_numbers(tmp_path)

    assert any(event.event_type == "record_parsed" and event.target_type == "fulltext_parse_result" for event in audit)
    assert any(event.action == "draft_created" and event.target_type == "fulltext_parsing" for event in governance)
    assert not any(event.target_type == "data_extraction_final" for event in governance)
    assert prisma.full_text_reports_excluded == 0
    assert prisma.studies_included == 0


def test_fulltext_parsing_page_state_exposes_parse_counts(tmp_path: Path) -> None:
    pdf = _write_text_pdf(tmp_path / "study.pdf")
    management = FullTextManagementService()
    management.attach_pdf(tmp_path, record_id="rec-1", source_file_path=str(pdf), actor="reviewer")
    parser = FullTextParsingService(fulltext_management=management)
    parser.parse_record(tmp_path, record_id="rec-1")

    state = fulltext_eligibility_state_from_project(
        tmp_path,
        fulltext_management_service=management,
        fulltext_parsing_service=parser,
    )

    assert state.fulltext_parse_schema_version == FULLTEXT_PARSE_MANIFEST_SCHEMA_VERSION
    assert state.fulltext_parse_counts == {"total": 1, "parsed": 1, "parse_failed": 0}
    assert state.output_paths["fulltext_parse_manifest"].endswith("fulltext/fulltext_parse_manifest_v1.json")


def _write_text_pdf(path: Path) -> Path:
    path.write_text(
        "\n".join(
            [
                "%PDF-1.4",
                "Full text title for parsing",
                "PMID: 12345678",
                "DOI 10.1000/fulltext.123",
                "Abstract",
                "Abstract text for the study.",
                "Methods",
                "Methods text with eligibility details.",
                "Results",
                "Results text.",
                "Tables",
                "Table 1 baseline data.",
                "References",
                "Reference list.",
                "/Type /Page",
                "%%EOF",
            ]
        ),
        encoding="utf-8",
    )
    return path
