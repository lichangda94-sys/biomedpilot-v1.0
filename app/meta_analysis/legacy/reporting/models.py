from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from analysis.models import AnalysisMetric, AnalysisModelType


@dataclass(slots=True)
class ForestPlotRow:
    study_label: str
    effect_value: float
    ci_lower: float
    ci_upper: float
    weight: float
    outcome_record_id: str

    def to_dict(self) -> dict[str, object]:
        return {
            "study_label": self.study_label,
            "effect_value": self.effect_value,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "weight": self.weight,
            "outcome_record_id": self.outcome_record_id,
        }


@dataclass(slots=True)
class ForestPlotData:
    analysis_id: str
    metric: AnalysisMetric
    model_type: AnalysisModelType
    rows: list[ForestPlotRow] = field(default_factory=list)
    pooled_effect: float = 0.0
    pooled_ci_lower: float = 0.0
    pooled_ci_upper: float = 0.0
    study_count: int = 0


@dataclass(slots=True)
class FunnelPlotPoint:
    study_label: str
    effect_value: float
    standard_error: float
    outcome_record_id: str

    def to_dict(self) -> dict[str, object]:
        return {
            "study_label": self.study_label,
            "effect_value": self.effect_value,
            "standard_error": self.standard_error,
            "outcome_record_id": self.outcome_record_id,
        }


@dataclass(slots=True)
class FunnelPlotData:
    analysis_id: str
    metric: AnalysisMetric
    points: list[FunnelPlotPoint] = field(default_factory=list)


@dataclass(slots=True)
class StudyCharacteristicsRow:
    extraction_record_id: str
    study_title: str
    study_design: str
    population: str
    condition: str
    intervention: str
    comparator: str
    sample_size_total: int | None
    follow_up: str
    country: str
    notes: str

    def to_dict(self) -> dict[str, object]:
        return {
            "extraction_record_id": self.extraction_record_id,
            "study_title": self.study_title,
            "study_design": self.study_design,
            "population": self.population,
            "condition": self.condition,
            "intervention": self.intervention,
            "comparator": self.comparator,
            "sample_size_total": self.sample_size_total,
            "follow_up": self.follow_up,
            "country": self.country,
            "notes": self.notes,
        }


@dataclass(slots=True)
class StudyCharacteristicsTable:
    project_id: str
    rows: list[StudyCharacteristicsRow] = field(default_factory=list)


@dataclass(slots=True)
class AnalysisSummaryRow:
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
    analysis_profile_id: str | None = None
    analysis_profile_name: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "analysis_id": self.analysis_id,
            "analysis_profile_id": self.analysis_profile_id,
            "analysis_profile_name": self.analysis_profile_name,
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


@dataclass(slots=True)
class AnalysisSummaryTable:
    project_id: str
    rows: list[AnalysisSummaryRow] = field(default_factory=list)


@dataclass(slots=True)
class ChineseAnalysisSummary:
    analysis_id: str
    metric: AnalysisMetric
    model_type: AnalysisModelType
    pooled_effect: float
    ci_lower: float
    ci_upper: float
    study_count: int
    i2: float
    short_cn_summary: str
    analysis_profile_id: str | None = None
    analysis_profile_name: str = ""


@dataclass(slots=True)
class ExportArtifact:
    name: str
    path: Path
