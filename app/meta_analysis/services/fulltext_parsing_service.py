from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.fulltext_management_service import FullTextManagementService
from app.meta_analysis.services.fulltext_service import FullTextService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


FULLTEXT_PARSE_RESULT_SCHEMA_VERSION = "meta_fulltext_parse_result.v1"
FULLTEXT_PARSE_MANIFEST_SCHEMA_VERSION = "meta_fulltext_parse_manifest.v1"

SECTION_NAMES = ("abstract", "methods", "results", "tables", "references")


@dataclass(frozen=True)
class FullTextParseResult:
    success: bool
    project_id: str
    record_id: str
    pdf_path: str
    output_path: str
    extracted_text_path: str
    manifest_path: str
    parse_status: str
    page_count: int = 0
    title_guess: str = ""
    doi_candidates: tuple[str, ...] = ()
    pmid_candidates: tuple[str, ...] = ()
    section_paths: dict[str, str] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    message: str = ""


class FullTextParsingService:
    def __init__(
        self,
        *,
        fulltext_management: FullTextManagementService | None = None,
        fulltext_service: FullTextService | None = None,
        audit_log: MetaAuditLogService | None = None,
        research_governance: MetaResearchGovernanceService | None = None,
    ) -> None:
        self._audit_log = audit_log or MetaAuditLogService()
        self._governance = research_governance or MetaResearchGovernanceService(audit_log=self._audit_log)
        self._management = fulltext_management or FullTextManagementService(audit_log=self._audit_log, research_governance=self._governance)
        self._fulltext = fulltext_service or FullTextService(audit_log=self._audit_log)

    def parsed_dir(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "fulltext" / "parsed_fulltext"

    def extracted_text_dir(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "fulltext" / "extracted_text"

    def section_dir(self, project_dir: Path, record_id: str) -> Path:
        return self.parsed_dir(project_dir) / _safe_id(record_id) / "sections"

    def result_path(self, project_dir: Path, record_id: str) -> Path:
        return self.parsed_dir(project_dir) / f"{_safe_id(record_id)}_fulltext_parse_v1.json"

    def manifest_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "fulltext" / "fulltext_parse_manifest_v1.json"

    def parse_record(self, project_dir: Path, *, record_id: str) -> FullTextParseResult:
        project_dir = project_dir.expanduser().resolve()
        pdf_path = self._pdf_path_for_record(project_dir, record_id)
        if not pdf_path:
            return self._write_failure(project_dir, record_id=record_id, pdf_path="", error_code="missing_pdf_path")
        return self.parse_pdf_file(project_dir, record_id=record_id, pdf_path=pdf_path)

    def parse_pdf_file(self, project_dir: Path, *, record_id: str, pdf_path: str) -> FullTextParseResult:
        project_dir = project_dir.expanduser().resolve()
        source = Path(pdf_path).expanduser().resolve()
        if not source.exists() or not source.is_file():
            return self._write_failure(project_dir, record_id=record_id, pdf_path=str(source), error_code="pdf_file_missing")
        extracted = _extract_text(source)
        text = extracted["text"]
        diagnostics = dict(extracted["diagnostics"])
        if not text.strip():
            diagnostics["warnings"] = [*diagnostics.get("warnings", []), "no_extractable_text"]
        parsed = {
            "schema_version": FULLTEXT_PARSE_RESULT_SCHEMA_VERSION,
            "project_id": project_dir.name,
            "parse_id": f"ftparse-{uuid4().hex[:12]}",
            "record_id": record_id,
            "pdf_path": str(source),
            "parse_status": "parsed" if text.strip() else "parse_failed",
            "parser_level": "testing",
            "created_at": _now(),
            "page_count": int(diagnostics.get("page_count", 0) or 0),
            "title_guess": _title_guess(text),
            "doi_candidates": _doi_candidates(text),
            "pmid_candidates": _pmid_candidates(text),
            "sections": _section_summary(text),
            "diagnostics": diagnostics,
            "safety_note": "Parsed text is auxiliary only and does not write final extraction, screening, quality, or analysis artifacts.",
        }
        output_path = self.result_path(project_dir, record_id)
        text_path = self.extracted_text_dir(project_dir) / f"{_safe_id(record_id)}.txt"
        section_paths = _write_sections(self.section_dir(project_dir, record_id), parsed["sections"])
        _write_text(text_path, text)
        _write_json(output_path, {**parsed, "extracted_text_path": str(text_path.relative_to(project_dir)), "section_paths": {key: str(Path(value).relative_to(project_dir)) for key, value in section_paths.items()}})
        manifest_path = self._update_manifest(project_dir, output_payload=_load_json(output_path))
        self._audit_log.record_event(
            project_dir,
            event_type="record_parsed",
            project_id=project_dir.name,
            target_type="fulltext_parse_result",
            target_id=record_id,
            source_path=str(source),
            output_path=str(output_path.relative_to(project_dir)),
            summary=f"Full-text PDF parsed with status {parsed['parse_status']}.",
            details={"parse_status": parsed["parse_status"], "parser_level": "testing", "page_count": parsed["page_count"]},
        )
        self._governance.record_draft_created(
            project_dir,
            project_id=project_dir.name,
            target_type="fulltext_parsing",
            target_id=record_id,
            after={"parse_status": parsed["parse_status"], "output_path": str(output_path.relative_to(project_dir))},
            metadata={"writes_final_extraction": False, "parser_level": "testing"},
        )
        return FullTextParseResult(
            success=parsed["parse_status"] == "parsed",
            project_id=project_dir.name,
            record_id=record_id,
            pdf_path=str(source),
            output_path=str(output_path),
            extracted_text_path=str(text_path),
            manifest_path=str(manifest_path),
            parse_status=str(parsed["parse_status"]),
            page_count=int(parsed["page_count"]),
            title_guess=str(parsed["title_guess"]),
            doi_candidates=tuple(parsed["doi_candidates"]),
            pmid_candidates=tuple(parsed["pmid_candidates"]),
            section_paths={key: str(value) for key, value in section_paths.items()},
            diagnostics=diagnostics,
            message=f"Full-text parsing completed with status {parsed['parse_status']}.",
        )

    def _write_failure(self, project_dir: Path, *, record_id: str, pdf_path: str, error_code: str) -> FullTextParseResult:
        project_dir = project_dir.expanduser().resolve()
        output_path = self.result_path(project_dir, record_id)
        text_path = self.extracted_text_dir(project_dir) / f"{_safe_id(record_id)}.txt"
        diagnostics = {"error_code": error_code, "warnings": [error_code], "page_count": 0, "parser": "none"}
        payload = {
            "schema_version": FULLTEXT_PARSE_RESULT_SCHEMA_VERSION,
            "project_id": project_dir.name,
            "parse_id": f"ftparse-{uuid4().hex[:12]}",
            "record_id": record_id,
            "pdf_path": pdf_path,
            "parse_status": "parse_failed",
            "parser_level": "testing",
            "created_at": _now(),
            "page_count": 0,
            "title_guess": "",
            "doi_candidates": [],
            "pmid_candidates": [],
            "sections": {},
            "section_paths": {},
            "extracted_text_path": str(text_path.relative_to(project_dir)),
            "diagnostics": diagnostics,
            "safety_note": "Parse failure is recorded for manual fallback; no final extraction artifact is written.",
        }
        _write_text(text_path, "")
        _write_json(output_path, payload)
        manifest_path = self._update_manifest(project_dir, output_payload=payload)
        self._audit_log.record_event(
            project_dir,
            event_type="record_parsed",
            project_id=project_dir.name,
            target_type="fulltext_parse_result",
            target_id=record_id,
            source_path=pdf_path,
            output_path=str(output_path.relative_to(project_dir)),
            summary=f"Full-text PDF parsing failed: {error_code}.",
            details=diagnostics,
        )
        return FullTextParseResult(
            success=False,
            project_id=project_dir.name,
            record_id=record_id,
            pdf_path=pdf_path,
            output_path=str(output_path),
            extracted_text_path=str(text_path),
            manifest_path=str(manifest_path),
            parse_status="parse_failed",
            diagnostics=diagnostics,
            message=f"Full-text parsing failed: {error_code}.",
        )

    def _pdf_path_for_record(self, project_dir: Path, record_id: str) -> str:
        management_record = self._management.get_record(project_dir, record_id)
        if management_record and management_record.pdf_path:
            return management_record.pdf_path
        fulltext_record = self._fulltext.get_fulltext_by_record_id(project_dir, record_id)
        if fulltext_record and fulltext_record.pdf_path:
            return fulltext_record.pdf_path
        return ""

    def _update_manifest(self, project_dir: Path, *, output_payload: dict[str, Any]) -> Path:
        path = self.manifest_path(project_dir)
        payload = _load_json(path)
        records = [dict(item) for item in payload.get("records", []) if isinstance(item, dict)]
        records = [item for item in records if str(item.get("record_id", "")) != str(output_payload.get("record_id", ""))]
        records.append(
            {
                "record_id": output_payload.get("record_id", ""),
                "parse_status": output_payload.get("parse_status", ""),
                "result_path": str(self.result_path(project_dir, str(output_payload.get("record_id", ""))).relative_to(project_dir)),
                "extracted_text_path": output_payload.get("extracted_text_path", ""),
                "page_count": output_payload.get("page_count", 0),
                "updated_at": _now(),
            }
        )
        _write_json(
            path,
            {
                "schema_version": FULLTEXT_PARSE_MANIFEST_SCHEMA_VERSION,
                "project_id": project_dir.name,
                "updated_at": _now(),
                "record_count": len(records),
                "parsed_count": len([item for item in records if item.get("parse_status") == "parsed"]),
                "parse_failed_count": len([item for item in records if item.get("parse_status") == "parse_failed"]),
                "records": records,
                "safety_note": "Full-text parse artifacts are auxiliary and do not create final extraction values.",
            },
        )
        return path


def _extract_text(path: Path) -> dict[str, Any]:
    warnings: list[str] = []
    page_count = 0
    parser = "fallback_bytes"
    for module_name in ("pypdf", "PyPDF2"):
        try:
            module = __import__(module_name)
            reader = module.PdfReader(str(path))
            page_count = len(reader.pages)
            parts = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(parts).strip()
            if text:
                return {"text": text, "diagnostics": {"parser": module_name, "page_count": page_count, "warnings": warnings}}
            warnings.append(f"{module_name}_returned_empty_text")
        except Exception as exc:
            warnings.append(f"{module_name}_unavailable_or_failed:{type(exc).__name__}")
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="ignore")
    if not text.strip():
        text = raw.decode("latin-1", errors="ignore")
    if raw.startswith(b"%PDF"):
        page_count = max(1, len(re.findall(rb"/Type\s*/Page\b", raw)))
    return {"text": _clean_fallback_text(text), "diagnostics": {"parser": parser, "page_count": page_count, "warnings": warnings}}


def _clean_fallback_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[^\S\r\n]+", " ", text)
    return text.strip()


def _title_guess(text: str) -> str:
    for line in text.splitlines():
        candidate = line.strip()
        if 8 <= len(candidate) <= 220 and not candidate.lower().startswith(("abstract", "methods", "results", "references")):
            return candidate
    return ""


def _doi_candidates(text: str) -> tuple[str, ...]:
    pattern = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
    return tuple(dict.fromkeys(match.group(0).rstrip(".;,") for match in pattern.finditer(text)))


def _pmid_candidates(text: str) -> tuple[str, ...]:
    pattern = re.compile(r"\bPMID\s*[:#]?\s*(\d{5,10})\b", re.IGNORECASE)
    return tuple(dict.fromkeys(match.group(1) for match in pattern.finditer(text)))


def _section_summary(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    lines = text.splitlines()
    current = ""
    collected: dict[str, list[str]] = {name: [] for name in SECTION_NAMES}
    for line in lines:
        normalized = re.sub(r"[^a-z]+", "", line.strip().lower())
        if normalized in SECTION_NAMES:
            current = normalized
            continue
        if normalized in {"method", "methodology", "materialsandmethods"}:
            current = "methods"
            continue
        if normalized in {"result"}:
            current = "results"
            continue
        if normalized in {"table", "tablesfigures"}:
            current = "tables"
            continue
        if current:
            collected[current].append(line)
    for key, values in collected.items():
        text_value = "\n".join(item for item in values if item.strip()).strip()
        if text_value:
            sections[key] = text_value
    return sections


def _write_sections(section_dir: Path, sections: dict[str, str]) -> dict[str, Path]:
    output: dict[str, Path] = {}
    for key, text in sections.items():
        path = section_dir / f"{key}.txt"
        _write_text(path, text)
        output[key] = path
    return output


def _safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", value.strip()).strip("-") or "record"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
