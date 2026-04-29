from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class PRISMAFlowSummary:
    records_identified: int
    records_after_deduplication: int
    records_screened: int
    records_excluded_title_abstract: int
    full_text_reports_sought: int
    full_text_reports_assessed: int
    full_text_reports_excluded: int
    full_text_exclusion_reasons: dict[str, int]
    studies_included: int
    reports_included: int
    data_sources: list[str]
    notes: list[str]
    created_at: str
    source_references: list[dict[str, str]] = field(default_factory=list)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def prisma_flow_summary_to_dict(summary: PRISMAFlowSummary) -> dict[str, Any]:
    return asdict(summary)


def prisma_flow_summary_from_dict(payload: dict[str, Any]) -> PRISMAFlowSummary:
    return PRISMAFlowSummary(
        records_identified=int(payload.get("records_identified", 0)),
        records_after_deduplication=int(payload.get("records_after_deduplication", 0)),
        records_screened=int(payload.get("records_screened", 0)),
        records_excluded_title_abstract=int(payload.get("records_excluded_title_abstract", 0)),
        full_text_reports_sought=int(payload.get("full_text_reports_sought", 0)),
        full_text_reports_assessed=int(payload.get("full_text_reports_assessed", 0)),
        full_text_reports_excluded=int(payload.get("full_text_reports_excluded", 0)),
        full_text_exclusion_reasons={str(key): int(value) for key, value in dict(payload.get("full_text_exclusion_reasons", {})).items()},
        studies_included=int(payload.get("studies_included", 0)),
        reports_included=int(payload.get("reports_included", 0)),
        data_sources=[str(item) for item in payload.get("data_sources", [])],
        notes=[str(item) for item in payload.get("notes", [])],
        created_at=str(payload.get("created_at", "")),
        source_references=[{str(key): str(value) for key, value in dict(item).items()} for item in payload.get("source_references", []) if isinstance(item, dict)],
    )
