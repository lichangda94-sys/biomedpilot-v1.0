from __future__ import annotations

from dataclasses import dataclass

from app.meta_analysis.services.quality_service import QualityAssessmentService


@dataclass(frozen=True)
class QualityPageState:
    title: str
    description: str
    status_label: str
    tool_options: tuple[str, ...]
    form_sections: tuple[str, ...]
    domain_note_support: bool
    overall_judgement_suggestion: str
    completeness_summary_fields: tuple[str, ...]
    output_summary: str
    next_step: str
    empty_state: str


def initial_quality_state(service: QualityAssessmentService | None = None) -> QualityPageState:
    service = service or QualityAssessmentService()
    return QualityPageState(
        title="Quality Assessment / 质量评价",
        description="NOS / QUADAS-2 / RoB2 simplified 质量评价表单处于 testing 状态，支持 domain-level notes 和非强制 overall judgement 建议。",
        status_label="测试中",
        tool_options=tuple(service.list_quality_tools()),
        form_sections=("study_selector", "tool_selector", "domain_judgements", "domain_notes", "overall_judgement", "reviewer_notes"),
        domain_note_support=True,
        overall_judgement_suggestion="根据 domain judgements 自动建议，但不强制覆盖人工判断。",
        completeness_summary_fields=("expected_study_count", "assessed_study_count", "missing_study_ids", "completeness_score"),
        output_summary="输出：quality_assessments、quality_assessment_table，并进入 report manifest。",
        next_step="下一步：Analysis 或 Reporting。",
        empty_state="没有 included studies 时显示空状态，不要求编辑 JSON。",
    )

