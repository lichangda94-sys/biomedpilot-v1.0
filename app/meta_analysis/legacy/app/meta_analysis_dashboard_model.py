from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ForestPlotRow:
    study: str
    effect: float
    ci_low: float
    ci_high: float
    weight: float


@dataclass(frozen=True)
class PrismaStage:
    label: str
    count: int
    note: str


@dataclass(frozen=True)
class GradeDomain:
    label: str
    rating: str
    note: str


@dataclass(frozen=True)
class RiskOfBiasDomain:
    label: str
    low: int
    some_concerns: int
    high: int


@dataclass(frozen=True)
class OutputFile:
    name: str
    kind: str
    updated_at: str


@dataclass(frozen=True)
class MetaAnalysisDashboardModel:
    project_title: str
    project_subtitle: str
    progress_label: str
    progress_percent: int
    included_studies: int
    pooled_effect_label: str
    heterogeneity_label: str
    last_sync_label: str
    forest_rows: tuple[ForestPlotRow, ...]
    prisma_stages: tuple[PrismaStage, ...]
    grade_domains: tuple[GradeDomain, ...]
    rob_domains: tuple[RiskOfBiasDomain, ...]
    output_files: tuple[OutputFile, ...]


def demo_meta_dashboard_model() -> MetaAnalysisDashboardModel:
    return MetaAnalysisDashboardModel(
        project_title="Meta 分析项目总览",
        project_subtitle="Cardiovascular prevention review · Intervention vs Control",
        progress_label="Screening complete · Extraction in review",
        progress_percent=72,
        included_studies=18,
        pooled_effect_label="RR 0.82 [0.71, 0.95]",
        heterogeneity_label="I2 34% · Random effects",
        last_sync_label="Demo data · Ready for service adapter",
        forest_rows=(
            ForestPlotRow("Anderson 2019", 0.76, 0.58, 0.99, 14.2),
            ForestPlotRow("Bennett 2020", 0.91, 0.73, 1.13, 12.8),
            ForestPlotRow("Chen 2021", 0.69, 0.51, 0.92, 16.5),
            ForestPlotRow("Diaz 2022", 0.88, 0.66, 1.18, 10.4),
            ForestPlotRow("Evans 2024", 0.79, 0.64, 0.98, 18.1),
        ),
        prisma_stages=(
            PrismaStage("检索记录", 1248, "PubMed / Embase / CENTRAL"),
            PrismaStage("去重后", 936, "312 duplicates removed"),
            PrismaStage("标题摘要筛选", 184, "752 excluded"),
            PrismaStage("全文评估", 42, "142 excluded"),
            PrismaStage("纳入研究", 18, "Quantitative synthesis"),
        ),
        grade_domains=(
            GradeDomain("Risk of bias", "Some concerns", "Two studies need adjudication"),
            GradeDomain("Inconsistency", "Low concern", "I2 remains moderate"),
            GradeDomain("Indirectness", "Low concern", "Population aligned with PICO"),
            GradeDomain("Imprecision", "Moderate", "CI crosses minimal important effect"),
        ),
        rob_domains=(
            RiskOfBiasDomain("Randomization", 13, 4, 1),
            RiskOfBiasDomain("Deviations", 12, 5, 1),
            RiskOfBiasDomain("Missing data", 15, 2, 1),
            RiskOfBiasDomain("Outcome measurement", 14, 3, 1),
        ),
        output_files=(
            OutputFile("forest_plot_primary.svg", "Figure", "Today 10:24"),
            OutputFile("screening_decisions.csv", "Data", "Yesterday 18:12"),
            OutputFile("grade_summary.docx", "Report draft", "Apr 26 16:40"),
        ),
    )
