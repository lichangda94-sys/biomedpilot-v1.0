from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


DEFAULT_INCLUSION_CRITERIA = (
    "human studies",
    "target population",
    "target disease",
    "target exposure or intervention",
    "eligible comparator",
    "eligible outcome",
    "eligible study design",
    "sufficient extractable data",
    "full text available",
)

DEFAULT_EXCLUSION_CRITERIA = (
    "review",
    "meta-analysis",
    "conference abstract",
    "letter / comment / correspondence / editorial",
    "case report",
    "animal study",
    "cell experiment",
    "duplicate population",
    "wrong population",
    "wrong intervention or exposure",
    "wrong comparator",
    "wrong outcome",
    "insufficient data",
    "full text unavailable",
)


@dataclass(frozen=True)
class Criterion:
    criterion_id: str
    label: str
    category: str
    applies_to_stage: tuple[str, ...] = ("title_abstract", "full_text")
    required: bool = False
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CriteriaSet:
    project_id: str
    criteria_id: str
    inclusion_criteria: tuple[Criterion, ...] = ()
    exclusion_criteria: tuple[Criterion, ...] = ()
    source_protocol_path: str = ""
    developer_preview: bool = True
    readiness_status: str = "needs_review"
    warnings: tuple[str, ...] = ()
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def criterion_from_label(label: str, *, category: str, index: int, required: bool = False) -> Criterion:
    slug = "_".join(label.lower().replace("/", " ").replace("-", " ").split())
    return Criterion(
        criterion_id=f"{category}-{index + 1:02d}-{slug[:48]}",
        label=label,
        category=category,
        required=required,
    )


def criteria_set_from_dict(payload: dict[str, Any]) -> CriteriaSet:
    return CriteriaSet(
        project_id=str(payload.get("project_id", "")),
        criteria_id=str(payload.get("criteria_id") or f"criteria-{uuid4().hex[:12]}"),
        inclusion_criteria=tuple(_criterion_from_payload(item) for item in payload.get("inclusion_criteria", []) if isinstance(item, dict)),
        exclusion_criteria=tuple(_criterion_from_payload(item) for item in payload.get("exclusion_criteria", []) if isinstance(item, dict)),
        source_protocol_path=str(payload.get("source_protocol_path", "")),
        developer_preview=bool(payload.get("developer_preview", True)),
        readiness_status=str(payload.get("readiness_status", "needs_review")),
        warnings=tuple(str(item) for item in payload.get("warnings", []) if str(item).strip()) if isinstance(payload.get("warnings", []), list) else (),
        created_at=str(payload.get("created_at", "")),
        updated_at=str(payload.get("updated_at", "")),
    )


def new_criteria_id() -> str:
    return f"criteria-{uuid4().hex[:12]}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _criterion_from_payload(payload: dict[str, Any]) -> Criterion:
    return Criterion(
        criterion_id=str(payload.get("criterion_id", "")),
        label=str(payload.get("label", "")),
        category=str(payload.get("category", "")),
        applies_to_stage=tuple(str(item) for item in payload.get("applies_to_stage", []) if str(item).strip()) if isinstance(payload.get("applies_to_stage", []), list) else (),
        required=bool(payload.get("required", False)),
        notes=str(payload.get("notes", "")),
    )
