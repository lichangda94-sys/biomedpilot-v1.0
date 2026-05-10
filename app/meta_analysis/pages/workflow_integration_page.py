from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.meta_analysis.search.search_strategy_builder_service import SearchStrategyBuilderService
from app.meta_analysis.services.analysis_plan_service import AnalysisPlanService
from app.meta_analysis.services.literature_library_service import LiteratureLibraryService
from app.meta_analysis.services.manual_extraction_effect_row_service import ManualExtractionEffectRowService
from app.meta_analysis.services.pico_workspace_service import PICOWorkspaceService
from app.meta_analysis.services.quality_service import QualityAssessmentService
from app.version import APP_VERSION


WORKFLOW_INTEGRATION_SCHEMA_VERSION = "meta_workflow_ui_integration.v1"


@dataclass(frozen=True)
class MetaWorkflowStepState:
    step_id: str
    order: int
    title_zh: str
    route_key: str
    status: str
    artifact_count: int
    artifact_summary: str
    artifact_paths: tuple[str, ...]
    updated_at: str
    warning_count: int
    warnings: tuple[str, ...]
    primary_action_zh: str
    next_action_zh: str
    next_step_id: str
    placeholder: bool = False
    testing_level: bool = True
    safety_flags: dict[str, bool] | None = None


@dataclass(frozen=True)
class MetaWorkflowIntegrationState:
    schema_version: str
    title_zh: str
    status_label_zh: str
    project_dir: str
    step_count: int
    steps: tuple[MetaWorkflowStepState, ...]
    next_recommended_step_id: str
    safety_flags: dict[str, bool]


WORKFLOW_STEP_DEFINITIONS: tuple[dict[str, str], ...] = (
    {
        "step_id": "project_home",
        "title_zh": "Meta 项目首页",
        "route_key": "workflow_home",
        "primary_action_zh": "查看流程状态",
        "next_action_zh": "进入研究问题",
        "next_step_id": "pico_workspace",
    },
    {
        "step_id": "pico_workspace",
        "title_zh": "中文研究问题 / PICO",
        "route_key": "pico_workspace",
        "primary_action_zh": "生成 PICO 草稿",
        "next_action_zh": "确认后生成检索策略",
        "next_step_id": "search_strategy",
    },
    {
        "step_id": "search_strategy",
        "title_zh": "检索策略",
        "route_key": "search_strategy",
        "primary_action_zh": "生成检索策略",
        "next_action_zh": "进入文献获取",
        "next_step_id": "literature_acquisition",
    },
    {
        "step_id": "literature_acquisition",
        "title_zh": "文献获取",
        "route_key": "literature_acquisition",
        "primary_action_zh": "导入选中文献",
        "next_action_zh": "查看文献库",
        "next_step_id": "literature_library",
    },
    {
        "step_id": "literature_library",
        "title_zh": "文献库",
        "route_key": "literature_library",
        "primary_action_zh": "查看文献记录",
        "next_action_zh": "进入去重复核",
        "next_step_id": "dedup_review",
    },
    {
        "step_id": "dedup_review",
        "title_zh": "去重复核",
        "route_key": "dedup_review",
        "primary_action_zh": "查看重复组",
        "next_action_zh": "配置排除标准",
        "next_step_id": "exclusion_criteria",
    },
    {
        "step_id": "exclusion_criteria",
        "title_zh": "排除标准",
        "route_key": "exclusion_criteria",
        "primary_action_zh": "查看排除理由",
        "next_action_zh": "进入标题摘要筛选",
        "next_step_id": "title_abstract_screening",
    },
    {
        "step_id": "title_abstract_screening",
        "title_zh": "标题摘要筛选",
        "route_key": "title_abstract_screening",
        "primary_action_zh": "查看筛选占位",
        "next_action_zh": "进入全文管理",
        "next_step_id": "fulltext_management",
    },
    {
        "step_id": "fulltext_management",
        "title_zh": "全文管理与全文筛选",
        "route_key": "fulltext_management",
        "primary_action_zh": "查看全文状态",
        "next_action_zh": "进入数据提取",
        "next_step_id": "manual_extraction",
    },
    {
        "step_id": "manual_extraction",
        "title_zh": "数据提取",
        "route_key": "manual_extraction",
        "primary_action_zh": "新建提取行",
        "next_action_zh": "进入 AI 辅助提取",
        "next_step_id": "ai_extraction",
    },
    {
        "step_id": "ai_extraction",
        "title_zh": "AI 辅助提取",
        "route_key": "ai_extraction",
        "primary_action_zh": "查看建议队列",
        "next_action_zh": "进入质量评价",
        "next_step_id": "quality_assessment",
    },
    {
        "step_id": "quality_assessment",
        "title_zh": "质量评价",
        "route_key": "quality_assessment",
        "primary_action_zh": "保存人工评分",
        "next_action_zh": "进入分析计划",
        "next_step_id": "analysis_plan",
    },
    {
        "step_id": "analysis_plan",
        "title_zh": "分析计划",
        "route_key": "analysis_plan",
        "primary_action_zh": "生成分析计划草稿",
        "next_action_zh": "确认后进入统计分析",
        "next_step_id": "statistics_analysis",
    },
    {
        "step_id": "statistics_analysis",
        "title_zh": "统计分析",
        "route_key": "statistics_analysis",
        "primary_action_zh": "查看分析计划",
        "next_action_zh": "等待统计引擎接入",
        "next_step_id": "figure_results",
    },
    {
        "step_id": "figure_results",
        "title_zh": "图表结果",
        "route_key": "figure_results",
        "primary_action_zh": "查看图表占位",
        "next_action_zh": "进入 PRISMA",
        "next_step_id": "prisma",
    },
    {
        "step_id": "prisma",
        "title_zh": "PRISMA",
        "route_key": "prisma",
        "primary_action_zh": "查看 PRISMA 占位",
        "next_action_zh": "进入报告导出",
        "next_step_id": "report_export",
    },
    {
        "step_id": "report_export",
        "title_zh": "报告导出",
        "route_key": "report_export",
        "primary_action_zh": "查看报告占位",
        "next_action_zh": "进入可复现项目包",
        "next_step_id": "reproducibility_package",
    },
    {
        "step_id": "reproducibility_package",
        "title_zh": "可复现项目包",
        "route_key": "reproducibility_package",
        "primary_action_zh": "查看导出占位",
        "next_action_zh": "等待可复现包接入",
        "next_step_id": "",
    },
)


def meta_workflow_integration_state_from_project(project_dir: Path) -> MetaWorkflowIntegrationState:
    project_dir = project_dir.expanduser().resolve()
    steps = tuple(_step_state(project_dir, index + 1, definition) for index, definition in enumerate(WORKFLOW_STEP_DEFINITIONS))
    next_step = next((step.step_id for step in steps if step.status not in {"已确认", "已生成", "已有记录", "testing-level"}), steps[-1].step_id)
    return MetaWorkflowIntegrationState(
        schema_version=WORKFLOW_INTEGRATION_SCHEMA_VERSION,
        title_zh="Meta 分析工作流",
        status_label_zh=f"{APP_VERSION} · Developer Preview / testing",
        project_dir=str(project_dir),
        step_count=len(steps),
        steps=steps,
        next_recommended_step_id=next_step,
        safety_flags={
            "auto_runs_statistics": False,
            "auto_generates_figures": False,
            "auto_generates_final_report": False,
            "advances_prisma": False,
            "calls_dataset_module": False,
        },
    )


def workflow_navigation_items() -> tuple[dict[str, str], ...]:
    return WORKFLOW_STEP_DEFINITIONS


def _step_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    step_id = definition["step_id"]
    if step_id == "project_home":
        return _project_home_state(project_dir, order, definition)
    if step_id == "pico_workspace":
        return _pico_state(project_dir, order, definition)
    if step_id == "search_strategy":
        return _search_strategy_state(project_dir, order, definition)
    if step_id == "literature_acquisition":
        return _pubmed_handoff_state(project_dir, order, definition)
    if step_id == "literature_library":
        return _literature_library_state(project_dir, order, definition)
    if step_id == "dedup_review":
        return _dedup_state(project_dir, order, definition)
    if step_id == "exclusion_criteria":
        return _placeholder_state(project_dir, order, definition, "排除标准页面将在 UI-07 接入；本轮不执行筛选")
    if step_id == "title_abstract_screening":
        return _placeholder_state(project_dir, order, definition, "标题摘要筛选将在 UI-08 接入；本轮不创建筛选决定")
    if step_id == "fulltext_management":
        return _fulltext_state(project_dir, order, definition)
    if step_id == "manual_extraction":
        return _manual_extraction_state(project_dir, order, definition)
    if step_id == "ai_extraction":
        return _ai_extraction_state(project_dir, order, definition)
    if step_id == "quality_assessment":
        return _quality_state(project_dir, order, definition)
    if step_id == "analysis_plan":
        return _analysis_plan_state(project_dir, order, definition)
    if step_id == "statistics_analysis":
        return _statistics_placeholder_state(project_dir, order, definition)
    if step_id == "figure_results":
        return _placeholder_state(project_dir, order, definition, "图表输出将在 M18 接入")
    if step_id == "prisma":
        return _placeholder_state(project_dir, order, definition, "PRISMA 引擎将在 UI-16 接入；数字必须来自真实流程记录")
    if step_id == "report_export":
        return _placeholder_state(project_dir, order, definition, "正式报告将在 M20 接入")
    if step_id == "reproducibility_package":
        return _placeholder_state(project_dir, order, definition, "可复现项目包将在 UI-18 接入")
    return _base_state(project_dir, order, definition, status="待开发", artifact_summary="暂不可用")


def _project_home_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    artifact_paths = _existing_paths(
        project_dir,
        (
            "protocol/pico_workspace_confirmed.json",
            "protocol/search_strategy_v2/search_strategy_confirmed.json",
            "literature/library_manifest.json",
            "analysis/analysis_plan_confirmed_v1.json",
        ),
    )
    status = "已有项目" if artifact_paths else "未开始"
    warnings = () if artifact_paths else ("尚未生成项目 artifact",)
    return _base_state(
        project_dir,
        order,
        definition,
        status=status,
        artifact_count=len(artifact_paths),
        artifact_summary=_summary_or_empty(artifact_paths, "项目 artifact"),
        artifact_paths=artifact_paths,
        warnings=warnings,
    )


def _pico_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    service = PICOWorkspaceService()
    draft = service.load_draft(project_dir)
    confirmed = service.load_confirmed(project_dir)
    paths = _existing_paths(project_dir, ("protocol/pico_workspace_draft.json", "protocol/pico_workspace_confirmed.json"))
    status = "已确认" if confirmed is not None else "草稿待确认" if draft is not None else "未开始"
    warnings: tuple[str, ...] = tuple(draft.warnings) if draft is not None else ("需要输入中文研究问题",)
    summary = f"draft={bool(draft)} confirmed={bool(confirmed)}"
    return _base_state(project_dir, order, definition, status=status, artifact_count=len(paths), artifact_summary=summary, artifact_paths=paths, warnings=warnings)


def _search_strategy_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    service = SearchStrategyBuilderService()
    drafts = service.load_drafts(project_dir)
    confirmed = service.load_confirmed(project_dir)
    paths = _existing_paths(
        project_dir,
        (
            "protocol/search_strategy_v2/search_strategy_drafts.json",
            "protocol/search_strategy_v2/search_strategy_confirmed.json",
            "protocol/search_strategy_v2/search_strategy_draft.md",
            "protocol/search_strategy_v2/search_strategy_draft.txt",
        ),
    )
    status = "已确认" if confirmed else "草稿待确认" if drafts else "未开始"
    warnings = tuple(_dedupe([*(warning for draft in drafts for warning in draft.warnings), *("没有已确认研究问题" if not (project_dir / "protocol" / "pico_workspace_confirmed.json").exists() else "",)]))
    summary = f"drafts={len(drafts)} confirmed={len(confirmed)}"
    return _base_state(project_dir, order, definition, status=status, artifact_count=len(paths), artifact_summary=summary, artifact_paths=paths, warnings=warnings)


def _pubmed_handoff_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    candidate_dir = project_dir / "protocol" / "pubmed_candidates"
    previews = sorted(candidate_dir.glob("*_candidates_preview.json"))
    selections = sorted(candidate_dir.glob("*_candidate_selection.json"))
    handoff_audits = sorted((project_dir / "audit").glob("*_pubmed_handoff_audit.json"))
    selected = sum(_count_decisions(path, "selected") for path in selections)
    rejected = sum(_count_decisions(path, "rejected") for path in selections)
    imported = _imported_count_from_batches(project_dir, "pubmed_confirmed_candidates")
    status = "已导入选中项" if imported else "等待用户选择" if previews else "未开始"
    warnings = () if previews else ("暂无 PubMed candidates preview",)
    paths = tuple(str(path) for path in [*previews, *selections, *handoff_audits])
    summary = f"previews={len(previews)} selected={selected} rejected={rejected} imported={imported}"
    return _base_state(project_dir, order, definition, status=status, artifact_count=len(paths), artifact_summary=summary, artifact_paths=paths, warnings=warnings)


def _literature_library_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    service = LiteratureLibraryService()
    records = service.list_records(project_dir)
    manifest = service.read_manifest(project_dir)
    total_batches = int(manifest.get("total_batches", 0) or 0)
    source_counts = dict(manifest.get("source_counts", {})) if isinstance(manifest.get("source_counts"), dict) else {}
    paths = _existing_paths(project_dir, ("literature/literature_records.json", "literature/import_batches.json", "literature/library_manifest.json"))
    status = "已有记录" if records else "未开始"
    warnings = () if records else ("文献库为空",)
    summary = f"records={len(records)} batches={total_batches} sources={source_counts}"
    return _base_state(project_dir, order, definition, status=status, artifact_count=len(paths), artifact_summary=summary, artifact_paths=paths, warnings=warnings)


def _dedup_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    paths = _existing_paths(
        project_dir,
        (
            "deduplication/duplicate_groups_v2.json",
            "deduplication/dedup_decisions_v2.json",
            "deduplication/deduplicated_literature_v2.json",
            "deduplication/pubmed_candidate_duplicate_groups.json",
        ),
    )
    group_count = 0
    risk_counts: dict[str, int] = {}
    for rel in ("deduplication/duplicate_groups_v2.json", "deduplication/pubmed_candidate_duplicate_groups.json"):
        payload = _load_json(project_dir / rel)
        groups = _items(payload, "duplicate_groups", "groups")
        group_count += len(groups)
        for group in groups:
            risk = str(group.get("risk_level") or group.get("risk") or group.get("duplicate_type") or "unknown")
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
    status = "待人工复核" if group_count else "未发现重复组" if paths else "未开始"
    warnings = ("需要人工确认去重决定",) if group_count else ()
    summary = f"duplicate_groups={group_count} risk_counts={risk_counts}"
    return _base_state(project_dir, order, definition, status=status, artifact_count=len(paths), artifact_summary=summary, artifact_paths=paths, warnings=warnings)


def _fulltext_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    paths = _existing_paths(
        project_dir,
        (
            "fulltext/fulltext_management_registry_v1.json",
            "fulltext/fulltext_parse_manifest_v1.json",
            "fulltext/fulltext_registry.json",
            "reports/missing_fulltext_report.csv",
        ),
    )
    registry = _load_json(project_dir / "fulltext" / "fulltext_management_registry_v1.json")
    records = _items(registry, "records")
    parse_manifest = _load_json(project_dir / "fulltext" / "fulltext_parse_manifest_v1.json")
    parse_total = int(parse_manifest.get("total_count", parse_manifest.get("total", 0)) or 0) if parse_manifest else 0
    status = "已有全文状态" if records or parse_total else "未开始"
    warnings = () if records or parse_total else ("暂无全文管理记录",)
    summary = f"fulltext_records={len(records)} parse_total={parse_total}"
    return _base_state(project_dir, order, definition, status=status, artifact_count=len(paths), artifact_summary=summary, artifact_paths=paths, warnings=warnings)


def _manual_extraction_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    service = ManualExtractionEffectRowService()
    study_units = service.load_study_units(project_dir)
    effect_rows = service.load_effect_rows(project_dir)
    validation = _load_json(service.validation_report_path(project_dir))
    missing_count = int(validation.get("missing_required_fields_count", 0) or 0)
    paths = _existing_paths(
        project_dir,
        (
            "extraction/extraction_manifest.json",
            "extraction/extraction_study_units.json",
            "extraction/extraction_effect_rows.json",
            "extraction/extraction_validation_report.json",
        ),
    )
    status = "已有草稿" if effect_rows else "未开始"
    warnings = (f"缺失关键字段：{missing_count}",) if missing_count else ()
    summary = f"study_units={len(study_units)} effect_rows={len(effect_rows)} missing_required_fields={missing_count}"
    return _base_state(project_dir, order, definition, status=status, artifact_count=len(paths), artifact_summary=summary, artifact_paths=paths, warnings=warnings)


def _ai_extraction_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    queue_path = project_dir / "extraction" / "extraction_ai_suggestion_queue.json"
    application_path = project_dir / "extraction" / "extraction_ai_suggestion_applications.json"
    queue = _load_json(queue_path)
    suggestions = _items(queue, "suggestions")
    pending = len([item for item in suggestions if str(item.get("status", "pending")) == "pending"])
    paths = tuple(str(path) for path in (queue_path, application_path) if path.exists())
    status = "有待审核建议" if pending else "已有建议" if suggestions else "未开始"
    warnings = ("AI 建议必须人工审核",) if suggestions else ()
    summary = f"suggestions={len(suggestions)} pending={pending}"
    return _base_state(project_dir, order, definition, status=status, artifact_count=len(paths), artifact_summary=summary, artifact_paths=paths, warnings=warnings)


def _quality_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    service = QualityAssessmentService()
    assessments = service.load_quality_assessments(project_dir)
    records_v1 = service.load_quality_assessment_records_v1(project_dir)
    completed = len([record for record in records_v1 if str(record.get("status", "")) == "completed_by_user"])
    paths = _existing_paths(
        project_dir,
        (
            "quality/quality_assessment_records_v1.json",
            "quality/quality_assessment_summary_v1.json",
            "quality/quality_table.csv",
        ),
    )
    status = "已有人工评分" if completed or assessments else "未开始"
    warnings = ("质量评价未完成",) if not completed else ()
    artifact_summary = f"assessments={len(assessments) + len(records_v1)} completed={completed}"
    return _base_state(project_dir, order, definition, status=status, artifact_count=len(paths), artifact_summary=artifact_summary, artifact_paths=paths, warnings=warnings)


def _analysis_plan_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    service = AnalysisPlanService()
    draft = service.load_draft(project_dir)
    confirmed = service.load_confirmed(project_dir)
    paths = _existing_paths(
        project_dir,
        (
            "analysis/analysis_plan_draft_v1.json",
            "analysis/analysis_plan_confirmed_v1.json",
            "analysis/analysis_plan_manifest_v1.json",
        ),
    )
    status = "已确认" if confirmed else "草稿待确认" if draft else "未开始"
    warnings = tuple(str(item) for item in draft.get("warnings", []) if item) if draft else ("尚未生成分析计划草稿",)
    summary = f"draft={bool(draft)} confirmed={bool(confirmed)}"
    return _base_state(project_dir, order, definition, status=status, artifact_count=len(paths), artifact_summary=summary, artifact_paths=paths, warnings=warnings)


def _statistics_placeholder_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    confirmed_plan = (project_dir / "analysis" / "analysis_plan_confirmed_v1.json").exists()
    if confirmed_plan:
        status = "testing-level"
        summary = "统计引擎将在 M17 接入；本流程页不自动运行统计"
        warnings: tuple[str, ...] = ()
    else:
        status = "暂不可用"
        summary = "请先确认分析计划"
        warnings = ("缺少 confirmed analysis plan",)
    return _base_state(
        project_dir,
        order,
        definition,
        status=status,
        artifact_summary=summary,
        artifact_paths=(),
        warnings=warnings,
        placeholder=True,
        safety_flags={"runs_statistics": False, "creates_final_result": False, "advances_prisma": False},
    )


def _placeholder_state(project_dir: Path, order: int, definition: dict[str, str], message: str) -> MetaWorkflowStepState:
    return _base_state(
        project_dir,
        order,
        definition,
        status="待开发",
        artifact_summary=message,
        artifact_paths=(),
        warnings=(message,),
        placeholder=True,
        safety_flags={"creates_artifact": False, "advances_prisma": False},
    )


def _base_state(
    project_dir: Path,
    order: int,
    definition: dict[str, str],
    *,
    status: str,
    artifact_count: int = 0,
    artifact_summary: str,
    artifact_paths: tuple[str, ...] = (),
    warnings: tuple[str, ...] = (),
    placeholder: bool = False,
    safety_flags: dict[str, bool] | None = None,
) -> MetaWorkflowStepState:
    updated_at = _latest_updated_at([Path(path) for path in artifact_paths])
    return MetaWorkflowStepState(
        step_id=definition["step_id"],
        order=order,
        title_zh=definition["title_zh"],
        route_key=definition["route_key"],
        status=status,
        artifact_count=artifact_count,
        artifact_summary=artifact_summary,
        artifact_paths=artifact_paths,
        updated_at=updated_at,
        warning_count=len(warnings),
        warnings=warnings,
        primary_action_zh=definition["primary_action_zh"],
        next_action_zh=definition["next_action_zh"],
        next_step_id=definition["next_step_id"],
        placeholder=placeholder,
        testing_level=True,
        safety_flags=safety_flags or {
            "auto_confirms_research_judgement": False,
            "runs_statistics": False,
            "advances_prisma": False,
        },
    )


def _existing_paths(project_dir: Path, relative_paths: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(project_dir / rel) for rel in relative_paths if (project_dir / rel).exists())


def _summary_or_empty(paths: tuple[str, ...], label: str) -> str:
    return f"{label}={len(paths)}" if paths else f"{label}=0"


def _items(payload: Any, *keys: str) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return [dict(item) for item in value if isinstance(item, dict)]
    for value in payload.values():
        if isinstance(value, list):
            return [dict(item) for item in value if isinstance(item, dict)]
    return []


def _count_decisions(path: Path, status: str) -> int:
    payload = _load_json(path)
    rows = _items(payload, "candidates", "selections", "decisions")
    count = 0
    for row in rows:
        decision = str(row.get("selected") or row.get("decision") or row.get("user_decision") or "")
        if decision == status or (status == "selected" and decision == "True"):
            count += 1
    return count


def _imported_count_from_batches(project_dir: Path, source_type: str) -> int:
    payload = _load_json(project_dir / "literature" / "import_batches.json")
    batches = _items(payload, "import_batches")
    return sum(int(batch.get("imported_count", 0) or 0) for batch in batches if str(batch.get("source_type", "")) == source_type)


def _latest_updated_at(paths: list[Path]) -> str:
    latest = ""
    for path in paths:
        payload = _load_json(path)
        for key in ("updated_at", "created_at", "confirmed_at"):
            value = str(payload.get(key, "")).strip() if isinstance(payload, dict) else ""
            if value and value > latest:
                latest = value
    return latest


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        text = str(item).strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _load_json(path: Path) -> Any:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload
