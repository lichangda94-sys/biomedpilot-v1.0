from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.services.quality_service import QualityAssessmentService
from app.meta_analysis.services.quality_service import (
    GRADE_PLACEHOLDER_SCHEMA_VERSION,
    QUALITY_ASSESSMENT_RECORD_V1_SCHEMA_VERSION,
    QUALITY_ASSESSMENT_STATUSES,
    QUALITY_ASSESSMENT_SUMMARY_V1_SCHEMA_VERSION,
    QUALITY_TOOL_REGISTRY_V1_SCHEMA_VERSION,
    QUALITY_RATING_OPTIONS,
)
from app.meta_analysis.ui_text import (
    DEVELOPER_INFO_TITLE_ZH,
    INTERNAL_BETA_STATUS_ZH,
    QUALITY_DESCRIPTION_ZH,
    QUALITY_FIELD_ZH,
    QUALITY_TITLE_ZH,
)
from app.version import APP_VERSION


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
    title_zh: str = QUALITY_TITLE_ZH
    status_label_zh: str = "内部测试"
    description_zh: str = QUALITY_DESCRIPTION_ZH
    form_section_labels_zh: tuple[str, ...] = ()
    next_step_zh: str = "下一步：完成质量评价后进入统计分析或报告。"
    empty_state_zh: str = "没有纳入研究时显示空状态，不需要编辑 JSON。"
    developer_info_title_zh: str = DEVELOPER_INFO_TITLE_ZH


@dataclass(frozen=True)
class QualityStudyRow:
    study_id: str
    record_id: str
    title: str
    study_design: str
    recommended_tool: str
    assessment_status: str
    overall_judgement: str = ""


@dataclass(frozen=True)
class QualityFormFlowState:
    title: str
    status_label: str
    description: str
    project_dir: str
    study_rows: tuple[QualityStudyRow, ...]
    selected_tool: str
    tool_options: tuple[str, ...]
    tool_metadata: dict[str, object]
    domain_fields: tuple[str, ...]
    domain_note_fields: tuple[str, ...]
    judgement_options: tuple[str, ...]
    suggested_overall_judgement: str
    completeness_summary: dict[str, object]
    output_paths: dict[str, str]
    warnings: tuple[str, ...]
    testing_limitations: tuple[str, ...]
    record_schema_version: str = QUALITY_ASSESSMENT_RECORD_V1_SCHEMA_VERSION
    summary_schema_version: str = QUALITY_ASSESSMENT_SUMMARY_V1_SCHEMA_VERSION
    tool_registry_schema_version: str = QUALITY_TOOL_REGISTRY_V1_SCHEMA_VERSION
    assessment_status_options: tuple[str, ...] = QUALITY_ASSESSMENT_STATUSES
    rating_options: tuple[str, ...] = QUALITY_RATING_OPTIONS
    tool_recommendations: tuple[dict[str, object], ...] = ()
    grade_placeholder_schema_version: str = GRADE_PLACEHOLDER_SCHEMA_VERSION
    grade_placeholder_status: str = "placeholder_only_no_auto_grade"
    safety_flags: dict[str, bool] | None = None
    title_zh: str = QUALITY_TITLE_ZH
    status_label_zh: str = "内部测试"
    description_zh: str = QUALITY_DESCRIPTION_ZH
    input_summary_zh: str = "输入：最终纳入研究、研究设计和 reviewer 的 domain judgement。"
    output_summary_zh: str = "输出：quality_assessment、quality_table、quality_summary 和 report manifest source。"
    next_step_zh: str = "下一步：检查 analysis-ready dataset，并在报告中引用质量评价摘要。"
    empty_state_zh: str = "没有纳入研究时，请先完成全文筛选或数据提取。"
    tool_label_zh: str = "质量评价工具"
    domain_note_label_zh: str = "领域备注"
    overall_suggestion_label_zh: str = "总体判断建议"
    completeness_label_zh: str = "质量评价完整性"
    developer_info_title_zh: str = DEVELOPER_INFO_TITLE_ZH


def initial_quality_state(service: QualityAssessmentService | None = None) -> QualityPageState:
    service = service or QualityAssessmentService()
    return QualityPageState(
        title="Quality Assessment / 质量评价",
        description="ROB2 / ROBINS-I / NOS / QUADAS-2 / JBI / AHRQ / Cochrane RoB / GRADE placeholder 处于 testing 状态；工具推荐和 overall judgement 都只作为 suggestion，最终评分必须人工完成。",
        status_label="测试中",
        tool_options=tuple(service.list_quality_tools()),
        form_sections=("study_selector", "tool_selector", "domain_judgements", "domain_notes", "overall_judgement", "reviewer_notes"),
        domain_note_support=True,
        overall_judgement_suggestion="根据 domain judgements 生成建议，但不强制覆盖人工判断，也不写最终 risk-of-bias 结论。",
        completeness_summary_fields=("expected_study_count", "assessed_study_count", "missing_study_ids", "completeness_score"),
        output_summary="输出：quality_assessment_records_v1、quality_assessment_summary_v1、quality table 和 report draft input；不创建 analysis-ready dataset。",
        next_step="下一步：Analysis 或 Reporting。",
        empty_state="没有 included studies 时显示空状态，不要求编辑 JSON。",
        title_zh=QUALITY_TITLE_ZH,
        status_label_zh=f"{APP_VERSION} · {INTERNAL_BETA_STATUS_ZH}",
        description_zh=QUALITY_DESCRIPTION_ZH,
        form_section_labels_zh=tuple(QUALITY_FIELD_ZH.get(item, item) for item in ("study_selector", "tool_selector", "domain_judgements", "domain_notes", "overall_judgement", "reviewer_notes")),
    )


def quality_state_from_project(
    project_dir: Path,
    *,
    service: QualityAssessmentService | None = None,
    selected_tool: str = "",
    profile_type: str = "",
) -> QualityFormFlowState:
    service = service or QualityAssessmentService()
    project_dir = project_dir.expanduser().resolve()
    assessments = service.load_quality_assessment_records_v1(project_dir)
    assessed_by_study = {str(assessment.get("study_id", "")): assessment for assessment in assessments}
    for assessment in service.load_quality_assessments(project_dir):
        assessed_by_study.setdefault(
            assessment.study_id,
            {
                "study_id": assessment.study_id,
                "record_id": assessment.record_id,
                "status": "assessed",
                "overall_judgement": assessment.overall_judgement,
            },
        )
    included = _included_studies(project_dir)
    rows = []
    for item in included:
        study_id = str(item.get("study_id") or item.get("record_id") or "")
        study_design = str(item.get("study_design") or "")
        assessment = assessed_by_study.get(study_id)
        rows.append(
            QualityStudyRow(
                study_id=study_id,
                record_id=str(item.get("record_id", "")),
                title=str(item.get("title", "")),
                study_design=study_design,
                recommended_tool=service.recommended_tool_for_study(study_design=study_design, profile_type=profile_type),
                assessment_status=str(assessment.get("status", "assessed")) if assessment else "needs_assessment",
                overall_judgement=str(assessment.get("overall_rating") or assessment.get("overall_judgement") or "") if assessment else "",
            )
        )
    tool_name = selected_tool or (rows[0].recommended_tool if rows else "NOS")
    metadata = service.quality_form_metadata(tool_name)
    sample_domains = {domain: metadata["judgement_options"][0] for domain in metadata["domains"]} if metadata.get("judgement_options") else {}
    completeness = service.quality_completeness_summary(project_dir, expected_study_ids=[row.study_id for row in rows])
    tool_recommendations = tuple(service.recommend_quality_tools(meta_type=profile_type, study_design=rows[0].study_design if rows else ""))
    warnings: list[str] = []
    if not rows:
        warnings.append("no_included_studies_for_quality_assessment")
    if completeness.get("missing_study_ids"):
        warnings.append(f"quality_assessment_missing:{len(completeness['missing_study_ids'])}")
    return QualityFormFlowState(
        title="Quality Assessment Workspace",
        status_label="Testing / Developer Preview",
        description="按 included studies 逐篇填写 quality assessment；根据 study design 或 method profile 推荐 NOS / QUADAS-2 / RoB2 simplified，并显示 overall judgement suggestion，但不强制覆盖 reviewer 判断。",
        project_dir=str(project_dir),
        study_rows=tuple(rows),
        selected_tool=tool_name,
        tool_options=tuple(service.list_quality_tools()),
        tool_metadata=metadata,
        domain_fields=tuple(metadata.get("domains", [])),
        domain_note_fields=tuple(metadata.get("domain_note_fields", [])),
        judgement_options=tuple(metadata.get("judgement_options", [])),
        suggested_overall_judgement=service.suggest_overall_judgement(tool_name, sample_domains),
        completeness_summary=completeness,
        output_paths={
            "quality_assessment_records_v1": str(project_dir / "quality" / "quality_assessment_records_v1.json"),
            "quality_assessment_summary_v1": str(project_dir / "quality" / "quality_assessment_summary_v1.json"),
            "quality_assessments": str(project_dir / "quality" / "quality_assessments.json"),
            "quality_assessment": str(project_dir / "quality" / "quality_assessment.json"),
            "quality_assessment_table": str(project_dir / "exports" / "quality_assessment_table.csv"),
            "quality_table": str(project_dir / "quality" / "quality_table.csv"),
            "quality_summary": str(project_dir / "quality" / "quality_summary.md"),
        },
        warnings=tuple(warnings),
        testing_limitations=(
            "Developer Preview：quality tools 是 testing 表单模板，不替代 reviewer 判断。",
            "overall judgement suggestion 只作为建议，用户必须人工确认。",
            "GRADE placeholder 不是正式 GRADE evidence profile。",
        ),
        record_schema_version=QUALITY_ASSESSMENT_RECORD_V1_SCHEMA_VERSION,
        summary_schema_version=QUALITY_ASSESSMENT_SUMMARY_V1_SCHEMA_VERSION,
        tool_registry_schema_version=QUALITY_TOOL_REGISTRY_V1_SCHEMA_VERSION,
        assessment_status_options=QUALITY_ASSESSMENT_STATUSES,
        rating_options=QUALITY_RATING_OPTIONS,
        tool_recommendations=tool_recommendations,
        grade_placeholder_schema_version=GRADE_PLACEHOLDER_SCHEMA_VERSION,
        grade_placeholder_status="placeholder_only_no_auto_grade",
        safety_flags={
            "auto_quality_scoring": False,
            "auto_grade_conclusion": False,
            "creates_analysis_ready_dataset": False,
            "runs_statistics": False,
            "advances_prisma": False,
        },
        title_zh=QUALITY_TITLE_ZH,
        status_label_zh=f"{APP_VERSION} · {INTERNAL_BETA_STATUS_ZH}",
        description_zh=QUALITY_DESCRIPTION_ZH,
    )


def _included_studies(project_dir: Path) -> list[dict[str, object]]:
    extraction_effect_rows = project_dir / "extraction" / "extraction_effect_rows.json"
    if extraction_effect_rows.exists():
        try:
            payload = json.loads(extraction_effect_rows.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        rows = []
        for item in payload.get("effect_rows", []):
            if not isinstance(item, dict):
                continue
            if str(item.get("evidence_state", "")) != "confirmed" and str(item.get("extraction_status", "")) != "completed_by_user":
                continue
            structured = dict(item.get("m5_structured_fields", {}) if isinstance(item.get("m5_structured_fields"), dict) else {})
            rows.append(
                {
                    "study_id": structured.get("study_id") or item.get("study_unit_label") or item.get("study_unit_id") or "",
                    "record_id": item.get("record_id", ""),
                    "title": structured.get("title", ""),
                    "study_design": structured.get("study_design", ""),
                }
            )
        if rows:
            return rows
    final_path = project_dir / "fulltext" / "final_included_studies.json"
    if final_path.exists():
        try:
            payload = json.loads(final_path.read_text(encoding="utf-8"))
            rows = payload.get("included_studies", [])
            return [dict(item) for item in rows if isinstance(item, dict)] if isinstance(rows, list) else []
        except Exception:
            return []
    extraction_path = project_dir / "extraction" / "extraction_records.json"
    if not extraction_path.exists():
        return []
    try:
        payload = json.loads(extraction_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    rows = []
    for item in payload.get("records", []):
        if not isinstance(item, dict):
            continue
        study = dict(item.get("study_characteristics", {})) if isinstance(item.get("study_characteristics"), dict) else {}
        rows.append(
            {
                "study_id": item.get("study_id", ""),
                "record_id": item.get("record_id", ""),
                "title": "",
                "study_design": study.get("study_design", ""),
            }
        )
    return rows
