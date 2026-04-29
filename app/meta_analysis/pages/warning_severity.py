from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


WarningSeverity = Literal["blocker", "major", "minor", "info"]
SEVERITY_LEVELS: tuple[WarningSeverity, ...] = ("blocker", "major", "minor", "info")


@dataclass(frozen=True)
class WarningSeverityItem:
    key: str
    severity: WarningSeverity
    message: str


def classify_warning_severity(*, context: str, key: str, count: int = 1, message: str = "") -> WarningSeverity:
    if count <= 0:
        return "info"
    normalized_context = context.strip().lower()
    normalized_key = key.strip().lower()
    text = f"{normalized_key} {message.strip().lower()}"

    if normalized_context == "import_diagnostics":
        if normalized_key in {"failed_record_count", "missing_title_count"}:
            return "blocker"
        if normalized_key in {"missing_author_count", "missing_year_count", "invalid_doi_count", "invalid_year_count", "duplicate_identifier_count", "diagnostics_file_missing"}:
            return "major"
        if normalized_key in {"missing_doi_count", "missing_pmid_count", "empty_abstract_count"}:
            return "minor"
        return "info"

    if normalized_context == "attachment":
        if normalized_key in {"attachment_source_file_missing"}:
            return "blocker"
        if normalized_key in {"attachment_registry_missing", "broken_path_count", "missing_attachment_count"}:
            return "major"
        if normalized_key in {"missing_fulltext_count", "missing_fulltext_report_missing"}:
            return "minor"
        if "automatic_pdf_download" in text or "ocr" in text:
            return "info"
        return "info"

    if normalized_context == "merge_preview":
        if normalized_key in {"merge_preview_no_records", "merge_preview_missing"}:
            return "blocker"
        if normalized_key in {"field_conflict", "field_conflicts", "canonical_candidate_missing"}:
            return "major"
        if normalized_key in {"low_confidence", "suspected_duplicate"}:
            return "minor"
        return "info"

    if normalized_context == "prisma_trace":
        if normalized_key in {"missing_source_reference", "missing_prisma_summary"}:
            return "major"
        if normalized_key in {"missing_audit_events", "missing_audit_log"}:
            return "minor"
        if normalized_key in {"full_text_workflow_incomplete", "formal_prisma_diagram_not_implemented"}:
            return "info"
        return "info"

    return "info"


def warning_severity_counts(items: list[WarningSeverityItem] | tuple[WarningSeverityItem, ...]) -> dict[str, int]:
    counts = {level: 0 for level in SEVERITY_LEVELS}
    for item in items:
        counts[item.severity] = counts.get(item.severity, 0) + 1
    return counts
