from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class StudyAnalysisRow:
    study_id: str
    record_id: str
    first_author: str
    year: int | None
    outcome_name: str
    effect_measure: str
    outcome_data_type: str
    raw_data: dict[str, Any]
    normalized_data: dict[str, Any]
    analysis_status: str
    exclusion_reason: str = ""
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AnalysisReadyDataset:
    dataset_id: str
    project_id: str
    profile_type: str
    outcome_name: str
    effect_measure: str
    outcome_data_type: str
    included_extraction_ids: list[str]
    excluded_extraction_ids: list[str]
    study_rows: list[StudyAnalysisRow]
    validation_errors: list[str]
    validation_warnings: list[str]
    created_at: str


@dataclass(frozen=True)
class AnalysisDatasetValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def new_analysis_ready_dataset_id() -> str:
    return f"ards-{uuid4().hex[:12]}"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def analysis_ready_dataset_to_dict(dataset: AnalysisReadyDataset) -> dict[str, Any]:
    payload = asdict(dataset)
    payload["study_rows"] = [asdict(row) for row in dataset.study_rows]
    return payload


def analysis_ready_dataset_from_dict(payload: dict[str, Any]) -> AnalysisReadyDataset:
    return AnalysisReadyDataset(
        dataset_id=str(payload["dataset_id"]),
        project_id=str(payload["project_id"]),
        profile_type=str(payload["profile_type"]),
        outcome_name=str(payload["outcome_name"]),
        effect_measure=str(payload["effect_measure"]),
        outcome_data_type=str(payload.get("outcome_data_type", "")),
        included_extraction_ids=[str(item) for item in payload.get("included_extraction_ids", [])],
        excluded_extraction_ids=[str(item) for item in payload.get("excluded_extraction_ids", [])],
        study_rows=[StudyAnalysisRow(**dict(item)) for item in payload.get("study_rows", [])],
        validation_errors=[str(item) for item in payload.get("validation_errors", [])],
        validation_warnings=[str(item) for item in payload.get("validation_warnings", [])],
        created_at=str(payload.get("created_at", "")),
    )
