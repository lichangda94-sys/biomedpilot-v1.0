from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from extraction.models import OutcomeType
from literature.models import utc_now


class AnalysisMetric(StrEnum):
    OR = "OR"
    RR = "RR"
    MD = "MD"
    SMD = "SMD"
    HR = "HR"


class AnalysisModelType(StrEnum):
    FIXED_EFFECT = "fixed_effect"
    RANDOM_EFFECT = "random_effect"


@dataclass(slots=True)
class AnalysisInput:
    analysis_id: str
    project_id: str
    outcome_record_ids: list[str]
    outcome_type: OutcomeType
    metric: AnalysisMetric
    model_type: AnalysisModelType
    analysis_profile_id: str | None = None
    created_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, object]:
        return {
            "analysis_id": self.analysis_id,
            "project_id": self.project_id,
            "outcome_record_ids": list(self.outcome_record_ids),
            "outcome_type": self.outcome_type.value,
            "metric": self.metric.value,
            "model_type": self.model_type.value,
            "analysis_profile_id": self.analysis_profile_id,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "AnalysisInput":
        return cls(
            analysis_id=str(payload["analysis_id"]),
            project_id=str(payload["project_id"]),
            outcome_record_ids=list(payload.get("outcome_record_ids", [])),
            outcome_type=OutcomeType(str(payload["outcome_type"])),
            metric=AnalysisMetric(str(payload["metric"])),
            model_type=AnalysisModelType(str(payload["model_type"])),
            analysis_profile_id=(
                str(payload["analysis_profile_id"])
                if payload.get("analysis_profile_id") is not None
                else None
            ),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
        )


@dataclass(slots=True)
class StudyEffectResult:
    study_effect_id: str
    analysis_id: str
    outcome_record_id: str
    metric: AnalysisMetric
    effect_value: float
    standard_error: float
    variance: float
    ci_lower: float
    ci_upper: float
    weight_fixed: float
    weight_random: float | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "study_effect_id": self.study_effect_id,
            "analysis_id": self.analysis_id,
            "outcome_record_id": self.outcome_record_id,
            "metric": self.metric.value,
            "effect_value": self.effect_value,
            "standard_error": self.standard_error,
            "variance": self.variance,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "weight_fixed": self.weight_fixed,
            "weight_random": self.weight_random,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "StudyEffectResult":
        return cls(
            study_effect_id=str(payload["study_effect_id"]),
            analysis_id=str(payload["analysis_id"]),
            outcome_record_id=str(payload["outcome_record_id"]),
            metric=AnalysisMetric(str(payload["metric"])),
            effect_value=float(payload["effect_value"]),
            standard_error=float(payload["standard_error"]),
            variance=float(payload["variance"]),
            ci_lower=float(payload["ci_lower"]),
            ci_upper=float(payload["ci_upper"]),
            weight_fixed=float(payload["weight_fixed"]),
            weight_random=(
                float(payload["weight_random"])
                if payload.get("weight_random") is not None
                else None
            ),
        )


@dataclass(slots=True)
class MetaResult:
    meta_result_id: str
    analysis_id: str
    metric: AnalysisMetric
    model_type: AnalysisModelType
    pooled_effect: float
    ci_lower: float
    ci_upper: float
    p_value: float
    tau2: float
    q_statistic: float
    i2: float
    study_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "meta_result_id": self.meta_result_id,
            "analysis_id": self.analysis_id,
            "metric": self.metric.value,
            "model_type": self.model_type.value,
            "pooled_effect": self.pooled_effect,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "p_value": self.p_value,
            "tau2": self.tau2,
            "q_statistic": self.q_statistic,
            "i2": self.i2,
            "study_count": self.study_count,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "MetaResult":
        return cls(
            meta_result_id=str(payload["meta_result_id"]),
            analysis_id=str(payload["analysis_id"]),
            metric=AnalysisMetric(str(payload["metric"])),
            model_type=AnalysisModelType(str(payload["model_type"])),
            pooled_effect=float(payload["pooled_effect"]),
            ci_lower=float(payload["ci_lower"]),
            ci_upper=float(payload["ci_upper"]),
            p_value=float(payload["p_value"]),
            tau2=float(payload["tau2"]),
            q_statistic=float(payload["q_statistic"]),
            i2=float(payload["i2"]),
            study_count=int(payload["study_count"]),
        )
