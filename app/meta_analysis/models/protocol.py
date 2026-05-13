from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


PROTOCOL_STATUS_IN_PROGRESS = "in_progress"
PROTOCOL_STATUS_NEEDS_REVIEW = "needs_review"
PROTOCOL_STATUS_READY = "ready"
PROTOCOL_STATUS_COMPLETED = "completed"


DEFAULT_PLANNED_DATABASES = ("PubMed", "Web of Science", "CNKI", "WanFang")


@dataclass(frozen=True)
class PICOFramework:
    population: str = ""
    intervention_or_exposure: str = ""
    comparator: str = ""
    outcomes: tuple[str, ...] = ()
    study_design: str = ""


@dataclass(frozen=True)
class ProjectProtocol:
    project_id: str
    protocol_id: str
    project_title: str = ""
    review_question: str = ""
    background: str = ""
    rationale: str = ""
    objective: str = ""
    meta_analysis_type: str = ""
    method_profile_id: str = ""
    pico: PICOFramework = field(default_factory=PICOFramework)
    primary_outcome: str = ""
    secondary_outcomes: tuple[str, ...] = ()
    eligible_study_designs: tuple[str, ...] = ()
    planned_databases: tuple[str, ...] = DEFAULT_PLANNED_DATABASES
    custom_databases: tuple[str, ...] = ()
    search_date: str = ""
    language_restriction: str = ""
    date_range_restriction: str = ""
    notes: str = ""
    developer_preview: bool = True
    readiness_status: str = PROTOCOL_STATUS_IN_PROGRESS
    confirmed: bool = False
    warnings: tuple[str, ...] = ()
    created_at: str = ""
    updated_at: str = ""
    confirmed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProtocolArtifactPaths:
    review_protocol: str
    search_terms_draft: str
    search_strategy_preview: str
    protocol_summary: str


@dataclass(frozen=True)
class ProtocolSaveResult:
    success: bool
    protocol: ProjectProtocol
    artifact_paths: ProtocolArtifactPaths
    warnings: tuple[str, ...]
    message: str


def protocol_from_dict(payload: dict[str, Any]) -> ProjectProtocol:
    pico_payload = payload.get("pico", {})
    pico = PICOFramework(
        population=str(pico_payload.get("population", "")) if isinstance(pico_payload, dict) else "",
        intervention_or_exposure=str(pico_payload.get("intervention_or_exposure", "")) if isinstance(pico_payload, dict) else "",
        comparator=str(pico_payload.get("comparator", "")) if isinstance(pico_payload, dict) else "",
        outcomes=tuple(str(item) for item in _as_list(pico_payload.get("outcomes", ())) if str(item).strip()) if isinstance(pico_payload, dict) else (),
        study_design=str(pico_payload.get("study_design", "")) if isinstance(pico_payload, dict) else "",
    )
    return ProjectProtocol(
        project_id=str(payload.get("project_id", "")),
        protocol_id=str(payload.get("protocol_id") or f"protocol-{uuid4().hex[:12]}"),
        project_title=str(payload.get("project_title", "")),
        review_question=str(payload.get("review_question", "")),
        background=str(payload.get("background", "")),
        rationale=str(payload.get("rationale", "")),
        objective=str(payload.get("objective", "")),
        meta_analysis_type=str(payload.get("meta_analysis_type", "")),
        method_profile_id=str(payload.get("method_profile_id", "")),
        pico=pico,
        primary_outcome=str(payload.get("primary_outcome", "")),
        secondary_outcomes=tuple(str(item) for item in _as_list(payload.get("secondary_outcomes", ())) if str(item).strip()),
        eligible_study_designs=tuple(str(item) for item in _as_list(payload.get("eligible_study_designs", ())) if str(item).strip()),
        planned_databases=tuple(str(item) for item in _as_list(payload.get("planned_databases", DEFAULT_PLANNED_DATABASES)) if str(item).strip()),
        custom_databases=tuple(str(item) for item in _as_list(payload.get("custom_databases", ())) if str(item).strip()),
        search_date=str(payload.get("search_date", "")),
        language_restriction=str(payload.get("language_restriction", "")),
        date_range_restriction=str(payload.get("date_range_restriction", "")),
        notes=str(payload.get("notes", "")),
        developer_preview=bool(payload.get("developer_preview", True)),
        readiness_status=str(payload.get("readiness_status", PROTOCOL_STATUS_IN_PROGRESS)),
        confirmed=bool(payload.get("confirmed", False)),
        warnings=tuple(str(item) for item in _as_list(payload.get("warnings", ())) if str(item).strip()),
        created_at=str(payload.get("created_at", "")),
        updated_at=str(payload.get("updated_at", "")),
        confirmed_at=str(payload.get("confirmed_at", "")),
    )


def new_protocol_id() -> str:
    return f"protocol-{uuid4().hex[:12]}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    if isinstance(value, str):
        return [item.strip() for item in value.replace(";", ",").split(",") if item.strip()]
    return [value]
