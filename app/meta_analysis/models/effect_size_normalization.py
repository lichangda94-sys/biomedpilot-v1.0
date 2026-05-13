from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


EFFECT_SIZE_INPUT_SCHEMA_VERSION = "meta_effect_size_input.m11"
EFFECT_SIZE_NORMALIZATION_SUMMARY_SCHEMA_VERSION = "meta_effect_size_normalization_summary.m11"

EFFECT_MEASURE_OR = "OR"
EFFECT_MEASURE_RR = "RR"
EFFECT_MEASURE_HR = "HR"
EFFECT_MEASURE_MD = "MD"
EFFECT_MEASURE_SMD = "SMD"
EFFECT_MEASURE_PROPORTION = "proportion"
EFFECT_MEASURE_CORRELATION = "correlation"
EFFECT_MEASURE_DIAGNOSTIC_ACCURACY = "diagnostic_accuracy"
EFFECT_MEASURE_OTHER = "other"

EFFECT_SIZE_SUPPORTED_MEASURES = (
    EFFECT_MEASURE_OR,
    EFFECT_MEASURE_RR,
    EFFECT_MEASURE_HR,
    EFFECT_MEASURE_MD,
    EFFECT_MEASURE_SMD,
    EFFECT_MEASURE_PROPORTION,
    EFFECT_MEASURE_CORRELATION,
    EFFECT_MEASURE_DIAGNOSTIC_ACCURACY,
    EFFECT_MEASURE_OTHER,
)

EFFECT_SIZE_RATIO_MEASURES = {EFFECT_MEASURE_OR, EFFECT_MEASURE_RR, EFFECT_MEASURE_HR}
EFFECT_SIZE_CONTINUOUS_MEASURES = {EFFECT_MEASURE_MD, EFFECT_MEASURE_SMD}

NORMALIZATION_STATUS_READY = "ready"
NORMALIZATION_STATUS_INCOMPLETE = "incomplete"
NORMALIZATION_STATUS_INVALID_NUMERIC = "invalid_numeric"
NORMALIZATION_STATUS_INVALID_CI = "invalid_ci"
NORMALIZATION_STATUS_UNSUPPORTED_EFFECT_TYPE = "unsupported_effect_type"
NORMALIZATION_STATUS_NEEDS_USER_REVIEW = "needs_user_review"

EFFECT_SIZE_NORMALIZATION_STATUSES = (
    NORMALIZATION_STATUS_READY,
    NORMALIZATION_STATUS_INCOMPLETE,
    NORMALIZATION_STATUS_INVALID_NUMERIC,
    NORMALIZATION_STATUS_INVALID_CI,
    NORMALIZATION_STATUS_UNSUPPORTED_EFFECT_TYPE,
    NORMALIZATION_STATUS_NEEDS_USER_REVIEW,
)


@dataclass(frozen=True)
class NormalizedEffectSizeInput:
    schema_version: str = EFFECT_SIZE_INPUT_SCHEMA_VERSION
    study_ref: str = ""
    study_label: str = ""
    effect_measure_type: str = ""
    estimate: float | None = None
    ci_lower: float | None = None
    ci_upper: float | None = None
    standard_error: float | None = None
    variance: float | None = None
    log_estimate: float | None = None
    log_ci_lower: float | None = None
    log_ci_upper: float | None = None
    events_case: float | None = None
    total_case: float | None = None
    events_control: float | None = None
    total_control: float | None = None
    mean_case: float | None = None
    sd_case: float | None = None
    n_case: float | None = None
    mean_control: float | None = None
    sd_control: float | None = None
    n_control: float | None = None
    correlation_coefficient: float | None = None
    diagnostic_tp: float | None = None
    diagnostic_fp: float | None = None
    diagnostic_fn: float | None = None
    diagnostic_tn: float | None = None
    source_state: str = ""
    normalization_status: str = NORMALIZATION_STATUS_INCOMPLETE
    warnings: list[str] = field(default_factory=list)
    source_field_completeness: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EffectSizeNormalizationSummary:
    schema_version: str = EFFECT_SIZE_NORMALIZATION_SUMMARY_SCHEMA_VERSION
    total_rows: int = 0
    confirmed_rows: int = 0
    normalized_ready: int = 0
    incomplete: int = 0
    invalid: int = 0
    needs_user_review: int = 0
    unsupported_effect_type: int = 0
    warnings: list[str] = field(default_factory=list)
    creates_computed_result: bool = False
    result_state: str = "configured_not_run"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
