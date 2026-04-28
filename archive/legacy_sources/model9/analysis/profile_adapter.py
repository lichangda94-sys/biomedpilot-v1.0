from __future__ import annotations

from dataclasses import dataclass

from analysis.models import AnalysisMetric, AnalysisModelType
from analysis_profiles.models import EngineReadyAnalysisConfig
from extraction.models import OutcomeType


@dataclass(frozen=True, slots=True)
class ProfileAnalysisInput:
    analysis_profile_id: str
    project_id: str
    outcome_record_ids: list[str]
    outcome_type: OutcomeType
    metric: AnalysisMetric
    model_type: AnalysisModelType


def build_profile_analysis_input(
    config: EngineReadyAnalysisConfig,
    outcome_record_ids: list[str],
) -> ProfileAnalysisInput:
    return ProfileAnalysisInput(
        analysis_profile_id=config.analysis_profile_id,
        project_id=config.project_id,
        outcome_record_ids=list(outcome_record_ids),
        outcome_type=config.outcome_type,
        metric=config.metric,
        model_type=config.model_type,
    )
