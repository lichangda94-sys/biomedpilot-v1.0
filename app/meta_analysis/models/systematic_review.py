from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


FULLTEXT_AVAILABILITY_STATUSES = ("not_checked", "available", "unavailable", "requested", "not_required")

FULLTEXT_EXCLUSION_REASONS = (
    "wrong population",
    "wrong intervention or exposure",
    "wrong comparator",
    "wrong outcome",
    "wrong study design",
    "duplicate cohort",
    "insufficient data",
    "no full text",
    "review or editorial",
    "animal or in vitro study",
    "conference abstract only",
    "language restriction",
    "other",
)


@dataclass(frozen=True)
class FullTextFile:
    fulltext_id: str
    project_id: str
    record_id: str
    pdf_path: str
    supplementary_paths: list[str]
    availability_status: str
    uploaded_at: str
    notes: str = ""


@dataclass(frozen=True)
class FullTextScreeningDecision:
    decision_id: str
    project_id: str
    record_id: str
    reviewer_id: str
    decision: str
    exclusion_reason: str = ""
    notes: str = ""
    created_at: str = ""


@dataclass(frozen=True)
class QualityAssessment:
    assessment_id: str
    project_id: str
    study_id: str
    record_id: str
    tool_name: str
    domains: dict[str, str]
    overall_judgement: str
    reviewer_id: str
    notes: str
    created_at: str


@dataclass(frozen=True)
class QualityToolDefinition:
    tool_name: str
    domains: tuple[str, ...]
    judgement_options: tuple[str, ...]
    recommended_profiles: tuple[str, ...]
    output_summary_fields: tuple[str, ...]


def new_fulltext_id() -> str:
    return f"fulltext-{uuid4().hex[:12]}"


def new_fulltext_decision_id() -> str:
    return f"ftdec-{uuid4().hex[:12]}"


def new_quality_assessment_id() -> str:
    return f"qa-{uuid4().hex[:12]}"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def fulltext_file_to_dict(record: FullTextFile) -> dict[str, Any]:
    return asdict(record)


def fulltext_file_from_dict(payload: dict[str, Any]) -> FullTextFile:
    return FullTextFile(
        fulltext_id=str(payload["fulltext_id"]),
        project_id=str(payload["project_id"]),
        record_id=str(payload["record_id"]),
        pdf_path=str(payload.get("pdf_path", "")),
        supplementary_paths=[str(item) for item in payload.get("supplementary_paths", [])],
        availability_status=str(payload.get("availability_status", "not_checked")),
        uploaded_at=str(payload.get("uploaded_at", "")),
        notes=str(payload.get("notes", "")),
    )


def fulltext_decision_to_dict(decision: FullTextScreeningDecision) -> dict[str, Any]:
    return asdict(decision)


def fulltext_decision_from_dict(payload: dict[str, Any]) -> FullTextScreeningDecision:
    return FullTextScreeningDecision(
        decision_id=str(payload["decision_id"]),
        project_id=str(payload["project_id"]),
        record_id=str(payload["record_id"]),
        reviewer_id=str(payload.get("reviewer_id", "")),
        decision=str(payload.get("decision", "")),
        exclusion_reason=str(payload.get("exclusion_reason", "")),
        notes=str(payload.get("notes", "")),
        created_at=str(payload.get("created_at", "")),
    )


def quality_assessment_to_dict(assessment: QualityAssessment) -> dict[str, Any]:
    return asdict(assessment)


def quality_assessment_from_dict(payload: dict[str, Any]) -> QualityAssessment:
    return QualityAssessment(
        assessment_id=str(payload["assessment_id"]),
        project_id=str(payload["project_id"]),
        study_id=str(payload["study_id"]),
        record_id=str(payload["record_id"]),
        tool_name=str(payload["tool_name"]),
        domains={str(key): str(value) for key, value in dict(payload.get("domains", {})).items()},
        overall_judgement=str(payload.get("overall_judgement", "")),
        reviewer_id=str(payload.get("reviewer_id", "")),
        notes=str(payload.get("notes", "")),
        created_at=str(payload.get("created_at", "")),
    )
