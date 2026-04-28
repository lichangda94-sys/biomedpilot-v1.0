from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class OutcomeDataType(StrEnum):
    BINARY = "binary"
    CONTINUOUS = "continuous"
    GENERIC_EFFECT = "generic_effect"
    DIAGNOSTIC_ACCURACY = "diagnostic_accuracy"
    PROPORTION = "proportion"
    CORRELATION = "correlation"


class ExtractionValidationStatus(StrEnum):
    VALID = "valid"
    VALID_WITH_WARNINGS = "valid_with_warnings"
    INVALID = "invalid"


@dataclass(frozen=True)
class StudyCharacteristics:
    first_author: str = ""
    year: int | None = None
    country: str = ""
    study_design: str = ""
    population: str = ""
    sample_size: int | None = None
    intervention_or_exposure: str = ""
    comparator: str = ""
    follow_up: str = ""
    notes: str = ""


@dataclass(frozen=True)
class BinaryOutcomeData:
    outcome_name: str
    effect_measure: str
    experimental_events: int
    experimental_total: int
    control_events: int
    control_total: int
    timepoint: str = ""
    subgroup: str = ""
    notes: str = ""


@dataclass(frozen=True)
class ContinuousOutcomeData:
    outcome_name: str
    effect_measure: str
    experimental_mean: float
    experimental_sd: float
    experimental_total: int
    control_mean: float
    control_sd: float
    control_total: int
    unit: str = ""
    timepoint: str = ""
    subgroup: str = ""
    notes: str = ""


@dataclass(frozen=True)
class GenericEffectOutcomeData:
    outcome_name: str
    effect_measure: str
    effect: float
    ci_lower: float | None = None
    ci_upper: float | None = None
    standard_error: float | None = None
    p_value: float | None = None
    adjusted: bool = False
    covariates: list[str] = field(default_factory=list)
    timepoint: str = ""
    subgroup: str = ""
    notes: str = ""


@dataclass(frozen=True)
class DiagnosticAccuracyOutcomeData:
    outcome_name: str
    tp: int
    fp: int
    fn: int
    tn: int
    effect_measure: str = "DOR"
    sensitivity: float | None = None
    specificity: float | None = None
    cutoff: str = ""
    index_test: str = ""
    reference_standard: str = ""
    notes: str = ""


@dataclass(frozen=True)
class ProportionOutcomeData:
    outcome_name: str
    events: int
    total: int
    effect_measure: str = "PREVALENCE"
    population_source: str = ""
    diagnostic_criteria: str = ""
    timepoint: str = ""
    subgroup: str = ""
    notes: str = ""


@dataclass(frozen=True)
class CorrelationOutcomeData:
    outcome_name: str
    r: float
    sample_size: int
    effect_measure: str = "CORRELATION"
    correlation_type: str = ""
    p_value: float | None = None
    variable_x: str = ""
    variable_y: str = ""
    notes: str = ""


ExtractionOutcomeData = (
    BinaryOutcomeData
    | ContinuousOutcomeData
    | GenericEffectOutcomeData
    | DiagnosticAccuracyOutcomeData
    | ProportionOutcomeData
    | CorrelationOutcomeData
)


@dataclass(frozen=True)
class ExtractedOutcome:
    outcome_id: str
    outcome_data_type: str
    data: ExtractionOutcomeData


@dataclass(frozen=True)
class ExtractionValidationResult:
    status: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class ExtractionRecord:
    extraction_id: str
    project_id: str
    record_id: str
    study_id: str
    reviewer_id: str
    profile_type: str
    study_characteristics: StudyCharacteristics
    outcomes: list[ExtractedOutcome]
    notes: str = ""
    source_location: str = ""
    validation_status: str = ExtractionValidationStatus.INVALID.value
    created_at: str = ""
    updated_at: str = ""


def new_extraction_id() -> str:
    return f"extr-{uuid4().hex[:12]}"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def extraction_record_to_dict(record: ExtractionRecord) -> dict[str, Any]:
    payload = asdict(record)
    serialized_outcomes: list[dict[str, Any]] = []
    for outcome in record.outcomes:
        item = asdict(outcome)
        item["data"] = asdict(outcome.data)
        serialized_outcomes.append(item)
    payload["outcomes"] = serialized_outcomes
    return payload


def extraction_record_from_dict(payload: dict[str, Any]) -> ExtractionRecord:
    outcomes = [
        ExtractedOutcome(
            outcome_id=str(item["outcome_id"]),
            outcome_data_type=str(item["outcome_data_type"]),
            data=_outcome_data_from_dict(str(item["outcome_data_type"]), dict(item["data"])),
        )
        for item in payload.get("outcomes", [])
    ]
    return ExtractionRecord(
        extraction_id=str(payload["extraction_id"]),
        project_id=str(payload["project_id"]),
        record_id=str(payload["record_id"]),
        study_id=str(payload["study_id"]),
        reviewer_id=str(payload["reviewer_id"]),
        profile_type=str(payload["profile_type"]),
        study_characteristics=StudyCharacteristics(**dict(payload.get("study_characteristics", {}))),
        outcomes=outcomes,
        notes=str(payload.get("notes", "")),
        source_location=str(payload.get("source_location", "")),
        validation_status=str(payload.get("validation_status", ExtractionValidationStatus.INVALID.value)),
        created_at=str(payload.get("created_at", "")),
        updated_at=str(payload.get("updated_at", "")),
    )


def _outcome_data_from_dict(outcome_data_type: str, payload: dict[str, Any]) -> ExtractionOutcomeData:
    if outcome_data_type == OutcomeDataType.BINARY.value:
        return BinaryOutcomeData(**payload)
    if outcome_data_type == OutcomeDataType.CONTINUOUS.value:
        return ContinuousOutcomeData(**payload)
    if outcome_data_type == OutcomeDataType.GENERIC_EFFECT.value:
        return GenericEffectOutcomeData(**payload)
    if outcome_data_type == OutcomeDataType.DIAGNOSTIC_ACCURACY.value:
        return DiagnosticAccuracyOutcomeData(**payload)
    if outcome_data_type == OutcomeDataType.PROPORTION.value:
        return ProportionOutcomeData(**payload)
    if outcome_data_type == OutcomeDataType.CORRELATION.value:
        return CorrelationOutcomeData(**payload)
    raise ValueError(f"Unsupported outcome data type: {outcome_data_type}")
