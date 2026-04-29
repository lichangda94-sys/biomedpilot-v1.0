from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

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


def quality_state_from_project(
    project_dir: Path,
    *,
    service: QualityAssessmentService | None = None,
    selected_tool: str = "",
    profile_type: str = "",
) -> QualityFormFlowState:
    service = service or QualityAssessmentService()
    project_dir = project_dir.expanduser().resolve()
    assessments = service.load_quality_assessments(project_dir)
    assessed_by_study = {assessment.study_id: assessment for assessment in assessments}
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
                assessment_status="assessed" if assessment else "needs_assessment",
                overall_judgement=assessment.overall_judgement if assessment else "",
            )
        )
    tool_name = selected_tool or (rows[0].recommended_tool if rows else "NOS")
    metadata = service.quality_form_metadata(tool_name)
    sample_domains = {domain: metadata["judgement_options"][0] for domain in metadata["domains"]} if metadata.get("judgement_options") else {}
    completeness = service.quality_completeness_summary(project_dir, expected_study_ids=[row.study_id for row in rows])
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
    )


def _included_studies(project_dir: Path) -> list[dict[str, object]]:
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
