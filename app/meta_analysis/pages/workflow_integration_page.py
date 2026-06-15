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
        "title_zh": "项目首页",
        "route_key": "workflow_home",
        "primary_action_zh": "查看流程状态",
        "next_action_zh": "继续：研究问题 / PICO",
        "next_step_id": "pico_workspace",
    },
    {
        "step_id": "page_button_audit",
        "title_zh": "页面能力审计",
        "route_key": "page_button_audit",
        "primary_action_zh": "查看按钮接入表",
        "next_action_zh": "继续：研究问题 / PICO",
        "next_step_id": "pico_workspace",
    },
    {
        "step_id": "pico_workspace",
        "title_zh": "研究问题与 PICO",
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
        "next_action_zh": "确认检索策略后导入文献",
        "next_step_id": "literature_import",
    },
    {
        "step_id": "literature_import",
        "title_zh": "文献库与导入",
        "route_key": "literature_import",
        "primary_action_zh": "导入文献",
        "next_action_zh": "导入文献后进入去重与筛选",
        "next_step_id": "screening",
    },
    {
        "step_id": "screening",
        "title_zh": "去重与筛选",
        "route_key": "screening_review",
        "primary_action_zh": "生成重复组 / 保存筛选决定",
        "next_action_zh": "完成去重后配置排除标准",
        "next_step_id": "exclusion_criteria",
    },
    {
        "step_id": "exclusion_criteria",
        "title_zh": "排除标准",
        "route_key": "exclusion_criteria",
        "primary_action_zh": "保存 / 确认排除标准",
        "next_action_zh": "进入标题摘要筛选",
        "next_step_id": "title_abstract_screening",
    },
    {
        "step_id": "title_abstract_screening",
        "title_zh": "标题摘要筛选",
        "route_key": "title_abstract_screening",
        "primary_action_zh": "生成筛选队列 / 保存人工决定",
        "next_action_zh": "完成筛选后进入全文管理",
        "next_step_id": "fulltext_management",
    },
    {
        "step_id": "fulltext_management",
        "title_zh": "全文管理",
        "route_key": "fulltext_management",
        "primary_action_zh": "建立全文队列 / 上传全文 / OCR",
        "next_action_zh": "全文确认后进入数据提取",
        "next_step_id": "manual_extraction",
    },
    {
        "step_id": "manual_extraction",
        "title_zh": "数据提取",
        "route_key": "manual_extraction",
        "primary_action_zh": "新建提取行",
        "next_action_zh": "完成提取后进入 AI 建议审核",
        "next_step_id": "ai_extraction",
    },
    {
        "step_id": "ai_extraction",
        "title_zh": "AI 辅助提取",
        "route_key": "ai_extraction",
        "primary_action_zh": "审核 AI 提取建议",
        "next_action_zh": "人工应用建议后进入质量评价",
        "next_step_id": "quality_assessment",
    },
    {
        "step_id": "quality_assessment",
        "title_zh": "质量评价",
        "route_key": "quality_assessment",
        "primary_action_zh": "保存 / 确认质量评价",
        "next_action_zh": "完成质量评价后进入分析计划",
        "next_step_id": "analysis_plan",
    },
    {
        "step_id": "analysis_plan",
        "title_zh": "分析计划",
        "route_key": "analysis_plan",
        "primary_action_zh": "生成并确认分析计划",
        "next_action_zh": "确认后运行统计分析",
        "next_step_id": "statistics_analysis",
    },
    {
        "step_id": "statistics_analysis",
        "title_zh": "统计分析",
        "route_key": "statistics_analysis",
        "primary_action_zh": "运行统计分析",
        "next_action_zh": "生成 / 查看图表结果",
        "next_step_id": "figure_results",
    },
    {
        "step_id": "figure_results",
        "title_zh": "图表结果",
        "route_key": "figure_results",
        "primary_action_zh": "查看 forest / funnel 等图表 artifact",
        "next_action_zh": "生成 PRISMA summary",
        "next_step_id": "prisma",
    },
    {
        "step_id": "prisma",
        "title_zh": "PRISMA",
        "route_key": "prisma",
        "primary_action_zh": "生成 PRISMA summary",
        "next_action_zh": "进入报告导出",
        "next_step_id": "report_export",
    },
    {
        "step_id": "report_export",
        "title_zh": "报告导出",
        "route_key": "report_export",
        "primary_action_zh": "生成 / 导出报告草稿",
        "next_action_zh": "导出可复现项目包",
        "next_step_id": "reproducibility_package",
    },
    {
        "step_id": "reproducibility_package",
        "title_zh": "复现包",
        "route_key": "reproducibility_package",
        "primary_action_zh": "导出可复现项目包",
        "next_action_zh": "返回项目首页",
        "next_step_id": "",
    },
)


def meta_workflow_integration_state_from_project(project_dir: Path) -> MetaWorkflowIntegrationState:
    project_dir = project_dir.expanduser().resolve()
    steps = tuple(_step_state(project_dir, index + 1, definition) for index, definition in enumerate(WORKFLOW_STEP_DEFINITIONS))
    next_step = next((step.step_id for step in steps if step.status != "已完成"), steps[-1].step_id)
    return MetaWorkflowIntegrationState(
        schema_version=WORKFLOW_INTEGRATION_SCHEMA_VERSION,
        title_zh="Meta 分析工作流",
        status_label_zh=f"{APP_VERSION} · 内部测试",
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
    if step_id == "page_button_audit":
        return _page_button_audit_state(project_dir, order, definition)
    if step_id == "pico_workspace":
        return _pico_state(project_dir, order, definition)
    if step_id == "search_strategy":
        return _search_strategy_state(project_dir, order, definition)
    if step_id == "literature_import":
        return _aggregate_stage_state(
            project_dir,
            order,
            definition,
            (
                _pubmed_handoff_state(project_dir, order, {**definition, "step_id": "literature_acquisition"}),
                _literature_library_state(project_dir, order, {**definition, "step_id": "literature_library"}),
            ),
        )
    if step_id == "screening":
        return _dedup_state(project_dir, order, definition)
    if step_id == "exclusion_criteria":
        return _exclusion_criteria_state(project_dir, order, definition)
    if step_id == "title_abstract_screening":
        return _title_abstract_screening_state(project_dir, order, definition)
    if step_id == "fulltext_management":
        return _fulltext_state(project_dir, order, definition)
    if step_id in {"manual_extraction", "extraction_quality"}:
        return _manual_extraction_state(project_dir, order, definition)
    if step_id == "ai_extraction":
        return _ai_extraction_state(project_dir, order, definition)
    if step_id == "quality_assessment":
        return _quality_state(project_dir, order, definition)
    if step_id == "analysis_plan":
        return _analysis_plan_state(project_dir, order, definition)
    if step_id == "statistics_analysis":
        return _statistics_state(project_dir, order, definition)
    if step_id == "figure_results":
        return _figure_state(project_dir, order, definition)
    if step_id == "prisma":
        return _prisma_state(project_dir, order, definition)
    if step_id == "report_export":
        return _report_state(project_dir, order, definition)
    if step_id == "reproducibility_package":
        return _reproducibility_state(project_dir, order, definition)
    if step_id == "analysis_results":
        return _aggregate_stage_state(
            project_dir,
            order,
            definition,
            (
                _analysis_plan_state(project_dir, order, {**definition, "step_id": "analysis_plan"}),
                _statistics_placeholder_state(project_dir, order, {**definition, "step_id": "statistics_analysis"}),
            ),
        )
    if step_id == "prisma_reporting":
        return _aggregate_stage_state(
            project_dir,
            order,
            definition,
            (
                _placeholder_state(project_dir, order, {**definition, "step_id": "prisma"}, "PRISMA 数字来自真实流程记录"),
                _placeholder_state(project_dir, order, {**definition, "step_id": "report_export"}, "报告导出仍为测试版"),
            ),
        )
    return _base_state(project_dir, order, definition, status="阻塞", artifact_summary="暂不可用")


def _project_home_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    artifact_paths = _existing_paths(
        project_dir,
        (
            "meta_project_manifest.json",
            "protocol/pico_workspace_confirmed.json",
            "protocol/search_strategy_v2/search_strategy_confirmed.json",
            "literature/library_manifest.json",
            "analysis/analysis_plan_confirmed_v1.json",
        ),
    )
    status = "已完成" if artifact_paths else "未开始"
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


def _page_button_audit_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    audit_doc = Path(__file__).resolve().parents[3] / "docs" / "meta_preview_page_button_audit_2026-06-11.md"
    runtime_audit = project_dir / "audit" / "meta_page_button_audit_runtime.json"
    runtime_audit_csv = project_dir / "audit" / "meta_page_button_audit_runtime.csv"
    capability_manifest = project_dir / "audit" / "meta_workflow_capability_manifest.json"
    audit_package = project_dir / "audit" / "meta_page_button_audit_package.zip"
    delivery_package = project_dir / "audit" / "meta_preview_delivery_package.zip"
    integrity_manifest = project_dir / "audit" / "meta_preview_integrity_manifest.json"
    paths = tuple(str(path) for path in (audit_doc, runtime_audit, runtime_audit_csv, capability_manifest, audit_package, delivery_package, integrity_manifest) if path.exists())
    return _base_state(
        project_dir,
        order,
        definition,
        status="已完成",
        artifact_count=len(paths),
        artifact_summary="active runtime button/function mapping is available in the app and docs",
        artifact_paths=paths,
        warnings=("审计表说明的是当前 preview 可见按钮接入与 testing 边界，不等同于已完成生产级统计/投稿验证。",),
    )


def _pico_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    service = PICOWorkspaceService()
    draft = service.load_draft(project_dir)
    confirmed = service.load_confirmed(project_dir)
    paths = _existing_paths(project_dir, ("protocol/pico_workspace_draft.json", "protocol/pico_workspace_confirmed.json"))
    status = "已完成" if confirmed is not None else "草稿" if draft is not None else "未开始"
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
            "protocol/search_strategy_v2/search_execution_manifest.json",
            "exports/search_strategy_package.zip",
        ),
    )
    if confirmed:
        status = "已完成"
    elif drafts:
        status = "草稿"
    elif not (project_dir / "protocol" / "pico_workspace_confirmed.json").exists():
        status = "阻塞"
    else:
        status = "未开始"
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
    status = "已完成" if imported else "待确认" if previews else "未开始"
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
    paths = _existing_paths(
        project_dir,
        (
            "literature/literature_records.json",
            "literature/import_batches.json",
            "literature/library_manifest.json",
            "literature/literature_acquisition_organization_manifest.json",
            "literature/literature_citation_manifest.json",
            "literature/literature_library_export.ris",
            "literature/literature_library_export.bib",
            "literature/literature_library_export.csl.json",
            "literature/literature_register.csv",
            "literature/literature_capability_artifact_index.json",
            "exports/literature_organization_package.zip",
        ),
    )
    status = "已完成" if records else "未开始"
    warnings = () if records else ("文献库为空",)
    summary = f"records={len(records)} batches={total_batches} sources={source_counts}"
    return _base_state(project_dir, order, definition, status=status, artifact_count=len(paths), artifact_summary=summary, artifact_paths=paths, warnings=warnings)


def _dedup_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    library_count = len(LiteratureLibraryService().list_records(project_dir))
    paths = _existing_paths(
        project_dir,
        (
            "deduplication/duplicate_groups_v2.json",
            "deduplication/dedup_decisions_v2.json",
            "deduplication/deduplicated_literature_v2.json",
            "deduplication/pubmed_candidate_duplicate_groups.json",
            "screening/title_abstract_queue_v2.json",
            "screening/screening_organization_manifest.json",
            "screening/title_abstract_screening_decisions.csv",
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
    dedup_payload = _load_json(project_dir / "deduplication" / "deduplicated_literature_v2.json")
    queue_payload = _load_json(project_dir / "screening" / "title_abstract_queue_v2.json")
    queue_count = int(queue_payload.get("record_count", 0) or 0) if queue_payload else 0
    unresolved = len(dedup_payload.get("unresolved_group_ids", [])) if dedup_payload else 0
    if queue_count:
        status = "待筛选"
        warnings = ()
    elif dedup_payload and unresolved:
        status = "有警告"
        warnings = ("仍有重复组待处理",)
    elif dedup_payload:
        status = "已完成"
        warnings = ()
    elif group_count:
        status = "待确认"
        warnings = ("需要人工确认去重决定",)
    elif library_count:
        status = "草稿"
        warnings = ("文献库已有记录，下一步需要生成重复组",)
    else:
        status = "已完成" if paths else "未开始"
        warnings = ()
    active_count = int(dedup_payload.get("active_record_count", dedup_payload.get("deduplicated_count", 0)) or 0) if dedup_payload else library_count
    summary = f"records={library_count} active_records={active_count} duplicate_groups={group_count} screening_queue={queue_count} risk_counts={risk_counts}"
    return _base_state(project_dir, order, definition, status=status, artifact_count=len(paths), artifact_summary=summary, artifact_paths=paths, warnings=warnings)


def _fulltext_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    paths = _existing_paths(
        project_dir,
        (
            "fulltext/fulltext_management_registry_v1.json",
            "fulltext/fulltext_parse_manifest_v1.json",
            "fulltext/fulltext_retrieval_manifest.json",
            "fulltext/fulltext_retrieval_register.csv",
            "exports/fulltext_retrieval_package.zip",
            "fulltext/fulltext_registry.json",
            "reports/missing_fulltext_report.csv",
        ),
    )
    registry = _load_json(project_dir / "fulltext" / "fulltext_management_registry_v1.json")
    records = _items(registry, "records")
    parse_manifest = _load_json(project_dir / "fulltext" / "fulltext_parse_manifest_v1.json")
    parse_total = int(parse_manifest.get("total_count", parse_manifest.get("total", 0)) or 0) if parse_manifest else 0
    status = "已完成" if records or parse_total else "未开始"
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
            "extraction/extraction_organization_manifest.json",
            "extraction/manual_extraction_template.csv",
            "extraction/manual_extraction_current.csv",
            "exports/extraction_organization_package.zip",
        ),
    )
    status = "有警告" if missing_count else "草稿" if effect_rows else "未开始"
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
    status = "待确认" if pending else "草稿" if suggestions else "未开始"
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
            "quality/quality_assessment_v1_export.json",
            "quality/quality_organization_manifest.json",
            "exports/quality_assessment_v1.csv",
            "exports/quality_assessment_package.zip",
        ),
    )
    status = "已完成" if completed else "有警告" if assessments else "未开始"
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
    status = "已完成" if confirmed else "草稿" if draft else "未开始"
    warnings = tuple(str(item) for item in draft.get("warnings", []) if item) if draft else ("尚未生成分析计划草稿",)
    summary = f"draft={bool(draft)} confirmed={bool(confirmed)}"
    return _base_state(project_dir, order, definition, status=status, artifact_count=len(paths), artifact_summary=summary, artifact_paths=paths, warnings=warnings)


def _exclusion_criteria_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    paths = _existing_paths(
        project_dir,
        (
            "screening/exclusion_criteria_library_v1.json",
            "screening/exclusion_criteria_selection_v1.json",
            "screening/exclusion_criteria_confirmed_v1.json",
        ),
    )
    status = "已完成" if any(path.endswith("confirmed_v1.json") for path in paths) else "草稿" if paths else "未开始"
    warnings = () if paths else ("尚未保存排除标准",)
    return _base_state(project_dir, order, definition, status=status, artifact_count=len(paths), artifact_summary=f"criteria_artifacts={len(paths)}", artifact_paths=paths, warnings=warnings)


def _title_abstract_screening_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    queue_path = project_dir / "screening" / "title_abstract_queue_v2.json"
    decisions_path = project_dir / "screening" / "title_abstract_decisions_v2.json"
    paths = tuple(str(path) for path in (queue_path, decisions_path) if path.exists())
    queue = _load_json(queue_path)
    decisions = _load_json(decisions_path)
    queue_records = _items(queue, "records", "screening_records")
    decision_records = _items(decisions, "decisions", "screening_records")
    status = "已完成" if decision_records else "待确认" if queue_records else "未开始"
    warnings = () if queue_records else ("尚未生成标题摘要筛选队列",)
    summary = f"queue_records={len(queue_records)} decisions={len(decision_records)}"
    return _base_state(project_dir, order, definition, status=status, artifact_count=len(paths), artifact_summary=summary, artifact_paths=paths, warnings=warnings)


def _statistics_placeholder_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    confirmed_plan = (project_dir / "analysis" / "analysis_plan_confirmed_v1.json").exists()
    if confirmed_plan:
        status = "有警告"
        summary = "统计引擎将在 M17 接入；本流程页不自动运行统计"
        warnings: tuple[str, ...] = ()
    else:
        status = "阻塞"
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


def _statistics_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    confirmed_plan = (project_dir / "analysis" / "analysis_plan_confirmed_v1.json").exists()
    manifest = project_dir / "analysis" / "analysis_manifest.json"
    result_files = tuple(sorted((project_dir / "analysis" / "results").glob("*_result.json"))) if (project_dir / "analysis" / "results").exists() else ()
    paths = tuple(str(path) for path in (manifest, *result_files) if path.exists())
    paths = (*paths, *_existing_paths(project_dir, ("analysis/statistics_results_manifest.json", "exports/statistics_results_package.zip")))
    if result_files:
        status = "已完成"
        warnings: tuple[str, ...] = ("统计结果仍为 testing-level，需人工审核",)
    elif confirmed_plan:
        status = "待确认"
        warnings = ("已有 confirmed analysis plan，尚未运行统计分析",)
    else:
        status = "阻塞"
        warnings = ("缺少 confirmed analysis plan",)
    summary = f"confirmed_plan={confirmed_plan} result_files={len(result_files)}"
    return _base_state(project_dir, order, definition, status=status, artifact_count=len(paths), artifact_summary=summary, artifact_paths=paths, warnings=warnings)


def _figure_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    manifest = project_dir / "figures" / "figure_artifacts.json"
    payload = _load_json(manifest)
    figures = _items(payload, "figures", "artifacts")
    result_files = tuple(sorted((project_dir / "analysis" / "results").glob("*_result.json"))) if (project_dir / "analysis" / "results").exists() else ()
    paths = tuple(str(path) for path in (manifest, *result_files) if path.exists())
    paths = (*paths, *_existing_paths(project_dir, ("figures/figure_results_manifest.json", "exports/figure_results_package.zip")))
    status = "已完成" if figures else "草稿" if result_files else "阻塞"
    warnings = () if figures else ("暂无图表 artifact；请先运行统计或导出图表",)
    summary = f"figure_artifacts={len(figures)} statistics_results={len(result_files)}"
    return _base_state(project_dir, order, definition, status=status, artifact_count=len(paths), artifact_summary=summary, artifact_paths=paths, warnings=warnings)


def _prisma_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    paths = _existing_paths(project_dir, ("reports/prisma_flow_summary.json", "reports/prisma_flow_summary.md", "reports/prisma_summary.json", "reports/prisma_flow.md", "reports/prisma_flow.svg", "reports/prisma_reporting_manifest.json", "exports/prisma_reporting_package.zip"))
    status = "已完成" if paths else "未开始"
    warnings = () if paths else ("尚未生成 PRISMA summary",)
    return _base_state(project_dir, order, definition, status=status, artifact_count=len(paths), artifact_summary=f"prisma_artifacts={len(paths)}", artifact_paths=paths, warnings=warnings)


def _report_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    paths = _existing_paths(
        project_dir,
        (
            "reports/formal_meta_report.md",
            "reports/formal_meta_report.html",
            "reports/formal_meta_report.docx",
            "reports/report_manifest.json",
            "reports/formal_report_delivery_manifest.json",
            "exports/formal_report_package.zip",
        ),
    )
    status = "已完成" if paths else "未开始"
    warnings = () if paths else ("尚未生成报告草稿",)
    return _base_state(project_dir, order, definition, status=status, artifact_count=len(paths), artifact_summary=f"report_artifacts={len(paths)}", artifact_paths=paths, warnings=warnings)


def _reproducibility_state(project_dir: Path, order: int, definition: dict[str, str]) -> MetaWorkflowStepState:
    packages = tuple(sorted((project_dir / "exports").glob("reproducibility_package_*.zip"))) if (project_dir / "exports").exists() else ()
    paths = tuple(str(path) for path in packages)
    status = "已完成" if packages else "未开始"
    warnings = () if packages else ("尚未导出复现包",)
    return _base_state(project_dir, order, definition, status=status, artifact_count=len(paths), artifact_summary=f"reproducibility_packages={len(paths)}", artifact_paths=paths, warnings=warnings)


def _aggregate_stage_state(
    project_dir: Path,
    order: int,
    definition: dict[str, str],
    children: tuple[MetaWorkflowStepState, ...],
) -> MetaWorkflowStepState:
    statuses = [child.status for child in children]
    if statuses and all(status == "已完成" for status in statuses):
        status = "已完成"
    elif any(status == "待筛选" for status in statuses):
        status = "待筛选"
    elif any(status == "待确认" for status in statuses):
        status = "待确认"
    elif any(status == "有警告" for status in statuses):
        status = "有警告"
    elif any(status == "草稿" for status in statuses):
        status = "草稿"
    elif any(status == "阻塞" for status in statuses):
        status = "阻塞"
    elif any(status == "已完成" for status in statuses):
        status = "草稿"
    else:
        status = "未开始"
    artifact_paths = tuple(path for child in children for path in child.artifact_paths)
    warnings = tuple(warning for child in children for warning in child.warnings)
    summary = "；".join(f"{child.title_zh}：{child.artifact_summary}" for child in children)
    return _base_state(
        project_dir,
        order,
        definition,
        status=status,
        artifact_count=sum(child.artifact_count for child in children),
        artifact_summary=summary,
        artifact_paths=artifact_paths,
        warnings=warnings,
        placeholder=all(child.placeholder for child in children),
        safety_flags={"auto_confirms_research_judgement": False, "runs_statistics": False, "advances_prisma": False},
    )


def _placeholder_state(project_dir: Path, order: int, definition: dict[str, str], message: str) -> MetaWorkflowStepState:
    return _base_state(
        project_dir,
        order,
        definition,
        status="阻塞",
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
