from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app_meta.core import demo_data

APP_VERSION = "0.1.0"


@dataclass(frozen=True)
class MetaDashboardMetrics:
    retrieved_literature_count: str
    retrieved_literature_trend: str
    included_studies_count: str
    included_studies_trend: str
    current_outcome_subtitle: str
    heterogeneity_i2: str
    heterogeneity_subtitle: str


@dataclass(frozen=True)
class PrismaFlowState:
    search_count: str
    deduplicated_count: str
    screened_count: str
    full_text_count: str
    included_count: str
    updated_at: str


@dataclass(frozen=True)
class ForestPlotStudyRow:
    study_name: str
    experimental_events: int
    experimental_total: int
    control_events: int
    control_total: int
    effect_size: float
    ci_low: float
    ci_high: float
    weight_percent: float


@dataclass(frozen=True)
class ForestPlotSummary:
    pooled_effect_size: float
    ci_low: float
    ci_high: float
    total_experimental_n: int
    total_control_n: int
    total_experimental_events: int
    total_control_events: int
    model_label: str
    outcome_type: str
    heterogeneity_text: str
    overall_effect_text: str
    x_axis_labels: tuple[float, ...]


@dataclass(frozen=True)
class RiskOfBiasRow:
    study_name: str
    randomization: str
    deviations: str
    missing_outcome: str
    outcome_measurement: str
    selective_reporting: str
    overall: str


@dataclass(frozen=True)
class GradeSummary:
    outcome: str
    evidence_quality: str
    rating_levels: tuple[str, ...]
    rows: tuple[tuple[str, str], ...]
    conclusion: str


@dataclass(frozen=True)
class RecentOutputItem:
    filename: str
    file_type: str
    timestamp: str


@dataclass(frozen=True)
class AnalysisSettings:
    effect_model: str
    outcome_type: str
    subgroup_analysis: str
    sensitivity_analysis: str
    publication_bias_test: str
    continuity_correction: str


@dataclass(frozen=True)
class MetaProjectState:
    project_id: str
    project_name: str
    created_at: str
    updated_at: str
    progress_percent: int
    review_type: str
    current_outcome: str
    current_effect_size: str
    project_dir: Path
    project_status: str
    app_version: str
    metrics: MetaDashboardMetrics
    prisma_flow: PrismaFlowState
    forest_plot: tuple[tuple[ForestPlotStudyRow, ...], ForestPlotSummary]
    risk_of_bias: tuple[RiskOfBiasRow, ...]
    grade: GradeSummary
    recent_outputs: tuple[RecentOutputItem, ...]
    analysis_settings: AnalysisSettings


def create_demo_project_state() -> MetaProjectState:
    project = demo_data.DEMO_PROJECT
    return MetaProjectState(
        project_id=project["project_id"],
        project_name=project["project_name"],
        created_at=project["created_at"],
        updated_at=project["updated_at"],
        progress_percent=project["progress_percent"],
        review_type=project["review_type"],
        current_outcome=project["current_outcome"],
        current_effect_size=project["current_effect_size"],
        project_dir=Path(project["project_dir"]),
        project_status=project.get("project_status", "Demo"),
        app_version=project.get("app_version", APP_VERSION),
        metrics=MetaDashboardMetrics(**demo_data.DEMO_METRICS),
        prisma_flow=PrismaFlowState(**demo_data.DEMO_PRISMA_FLOW),
        forest_plot=(
            tuple(ForestPlotStudyRow(**row) for row in demo_data.DEMO_FOREST_STUDIES),
            ForestPlotSummary(**demo_data.DEMO_FOREST_SUMMARY),
        ),
        risk_of_bias=tuple(RiskOfBiasRow(**row) for row in demo_data.DEMO_RISK_OF_BIAS),
        grade=GradeSummary(
            outcome=demo_data.DEMO_GRADE["outcome"],
            evidence_quality=demo_data.DEMO_GRADE["evidence_quality"],
            rating_levels=tuple(demo_data.DEMO_GRADE["rating_levels"]),
            rows=tuple(tuple(row) for row in demo_data.DEMO_GRADE["rows"]),
            conclusion=demo_data.DEMO_GRADE["conclusion"],
        ),
        recent_outputs=tuple(RecentOutputItem(**row) for row in demo_data.DEMO_RECENT_OUTPUTS),
        analysis_settings=AnalysisSettings(**demo_data.DEMO_ANALYSIS_SETTINGS),
    )
