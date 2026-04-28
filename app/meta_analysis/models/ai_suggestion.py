from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class AISuggestionStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EDITED = "edited"


@dataclass(frozen=True)
class AISuggestion:
    suggestion_id: str
    project_id: str
    target_type: str
    target_id: str
    suggestion_type: str
    suggested_value: Any
    rationale: str
    confidence: float
    status: str = AISuggestionStatus.PENDING.value
    reviewer_action: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass(frozen=True)
class AISuggestionActionResult:
    success: bool
    suggestion_id: str
    status: str
    message: str
    output_path: str = ""
    details: dict[str, Any] = field(default_factory=dict)


TARGET_TYPES = (
    "search_strategy",
    "screening_decision",
    "exclusion_reason",
    "extraction_candidate",
    "report_text",
    "data_warning",
)


SUGGESTION_TYPES = (
    "keyword_expansion",
    "relevance_screening",
    "exclusion_reason_suggestion",
    "extraction_candidate",
    "data_consistency_warning",
    "report_draft_suggestion",
)


def new_ai_suggestion_id() -> str:
    return f"aisug-{uuid4().hex[:12]}"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def ai_suggestion_to_dict(suggestion: AISuggestion) -> dict[str, Any]:
    return asdict(suggestion)


def ai_suggestion_from_dict(payload: dict[str, Any]) -> AISuggestion:
    return AISuggestion(
        suggestion_id=str(payload["suggestion_id"]),
        project_id=str(payload["project_id"]),
        target_type=str(payload["target_type"]),
        target_id=str(payload["target_id"]),
        suggestion_type=str(payload["suggestion_type"]),
        suggested_value=payload.get("suggested_value"),
        rationale=str(payload.get("rationale", "")),
        confidence=float(payload.get("confidence", 0.0)),
        status=str(payload.get("status", AISuggestionStatus.PENDING.value)),
        reviewer_action=str(payload.get("reviewer_action", "")),
        created_at=str(payload.get("created_at", "")),
        updated_at=str(payload.get("updated_at", "")),
    )
