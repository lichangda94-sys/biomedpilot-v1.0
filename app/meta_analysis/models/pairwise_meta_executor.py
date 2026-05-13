from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.meta_analysis.models.statistical_result_state import STATISTICAL_RESULT_STATE_CONFIGURED_NOT_RUN


PAIRWISE_META_EXECUTOR_SCHEMA_VERSION = "meta_pairwise_executor_result.m12"
PAIRWISE_META_EXECUTOR_NAME = "PairwiseMetaExecutor"
PAIRWISE_META_EXECUTOR_VERSION = "m12.fixed_effect_iv.1"

PAIRWISE_MODEL_FIXED_EFFECT = "fixed_effect"
PAIRWISE_MODEL_RANDOM_EFFECT = "random_effect"
PAIRWISE_SUPPORTED_MODELS = (PAIRWISE_MODEL_FIXED_EFFECT,)


@dataclass(frozen=True)
class PairwiseMetaExecutorConfig:
    model: str = PAIRWISE_MODEL_FIXED_EFFECT
    confidence_level: float = 0.95
    allow_developer_preview_computed: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PairwiseStudyResult:
    study_label: str
    effect_measure_type: str
    estimate: float
    standard_error: float
    variance: float
    weight: float
    effect_scale: str
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PairwiseMetaExecutorResult:
    result_state: str = STATISTICAL_RESULT_STATE_CONFIGURED_NOT_RUN
    executor_schema_version: str = PAIRWISE_META_EXECUTOR_SCHEMA_VERSION
    executor_name: str = PAIRWISE_META_EXECUTOR_NAME
    executor_version: str = PAIRWISE_META_EXECUTOR_VERSION
    result_id: str = ""
    analysis_run_id: str = ""
    model_used: str = PAIRWISE_MODEL_FIXED_EFFECT
    effect_measure_type: str = ""
    effect_scale: str = ""
    included_studies: list[dict[str, Any]] = field(default_factory=list)
    excluded_studies: list[dict[str, Any]] = field(default_factory=list)
    pooled_effect: float | None = None
    pooled_ci_lower: float | None = None
    pooled_ci_upper: float | None = None
    pooled_standard_error: float | None = None
    z_value: float | None = None
    p_value: float | None = None
    back_transformed_effect: float | None = None
    back_transformed_ci_lower: float | None = None
    back_transformed_ci_upper: float | None = None
    heterogeneity_summary: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    validation_errors: list[str] = field(default_factory=list)
    reproducibility_metadata: dict[str, Any] = field(default_factory=dict)
    result_manifest: dict[str, Any] = field(default_factory=dict)
    formal_computed: bool = False
    testing_level: bool = False
    developer_preview_testing: bool = True
    user_reviewed: bool = False
    report_ready: bool = False
    medical_conclusion_status: str = "not_generated"
    testing_level_notice: str = "Developer Preview / testing MVP; not production, clinical, regulatory, or publication-ready."

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
