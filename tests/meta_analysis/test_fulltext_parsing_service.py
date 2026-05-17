from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.fulltext_eligibility_page import fulltext_eligibility_state_from_project
from app.meta_analysis.fulltext import (
    MetaOcrRuntimeService,
    OcrBlock,
    OcrDocumentResult,
    OcrEngineInfo,
    OcrPageResult,
    OcrSource,
)
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


def test_fulltext_parsing_can_use_ocr_worker_outputs_as_auxiliary_text(tmp_path: Path) -> None:
    pdf = _write_text_pdf(tmp_path / "scanned.pdf")
    management = FullTextManagementService()
    management.attach_pdf(tmp_path, record_id="rec-ocr", source_file_path=str(pdf), actor="reviewer")
    service = FullTextParsingService(fulltext_management=management, ocr_runner=_FakeOcrRunner())

    result = service.parse_record(tmp_path, record_id="rec-ocr", use_ocr=True)
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    extracted_text = Path(result.extracted_text_path).read_text(encoding="utf-8")

    assert result.success
    assert result.parse_status == "parsed"
    assert payload["parser_level"] == "ocr_testing"
    assert payload["diagnostics"]["parser"] == "paddleocr_local"
    assert payload["diagnostics"]["runtime_status"] == "injected_runner"
    assert payload["diagnostics"]["ocr_text_path"] == "fulltext/ocr/rec-ocr.txt"
    assert payload["diagnostics"]["ocr_json_path"] == "fulltext/ocr/rec-ocr.ocr.json"
    assert "OCR full text 中文 English 繁體" in extracted_text
    assert Path(result.output_path).exists()
    assert (tmp_path / "fulltext" / "ocr" / "rec-ocr.ocr.json").exists()
    assert not (tmp_path / "extraction" / "extraction_records.json").exists()
    assert not (tmp_path / "quality" / "quality_assessments.json").exists()


def test_fulltext_parsing_records_missing_ocr_runtime_without_final_outputs(tmp_path: Path) -> None:
    pdf = _write_text_pdf(tmp_path / "scanned.pdf")
    management = FullTextManagementService()
    management.attach_pdf(tmp_path, record_id="rec-missing-runtime", source_file_path=str(pdf), actor="reviewer")
    service = FullTextParsingService(
        fulltext_management=management,
        ocr_runtime_service=MetaOcrRuntimeService(runtime_root=tmp_path / "missing-runtime"),
    )

    result = service.parse_record(tmp_path, record_id="rec-missing-runtime", use_ocr=True)
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))

    assert not result.success
    assert result.parse_status == "parse_failed"
    assert result.diagnostics["error_code"] == "ocr_runtime_unavailable:not_configured"
    assert result.diagnostics["runtime_status"] == "not_configured"
    assert payload["diagnostics"]["parser"] == "paddleocr_local"
    assert not (tmp_path / "extraction" / "extraction_records.json").exists()
    assert not (tmp_path / "quality" / "quality_assessments.json").exists()


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


class _FakeOcrRunner:
    def run_pdf_ocr(self, pdf_path: Path, *, record_id: str, attachment_id: str = "", lang: str = "auto") -> OcrDocumentResult:
        return OcrDocumentResult(
            source=OcrSource(path=str(pdf_path), media_type="application/pdf", attachment_id=attachment_id, record_id=record_id),
            engine=OcrEngineInfo(engine_version="test-runtime", runtime_manifest_id="runtime-test"),
            pages=(
                OcrPageResult(
                    page_index=0,
                    page_label="1",
                    text="OCR full text 中文 English 繁體",
                    blocks=(OcrBlock(block_id="b1", text="OCR full text 中文 English 繁體", confidence=0.99, order=1),),
                ),
            ),
        )
