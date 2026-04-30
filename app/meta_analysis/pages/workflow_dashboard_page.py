from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.project_contract_service import CANONICAL_PROJECT_PATHS, MANIFEST_FILES
from app.meta_analysis.ui_text import (
    DEVELOPER_INFO_TITLE_ZH,
    WORKFLOW_DASHBOARD_DESCRIPTION_ZH,
    WORKFLOW_DASHBOARD_TITLE_ZH,
    WORKFLOW_EMPTY_STATE_ZH,
    release_status_zh,
    warning_summary_zh,
    workflow_status_zh,
    workflow_step_text,
)
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskStatus


WORKFLOW_STATUS_NOT_STARTED = "Not started"
WORKFLOW_STATUS_IN_PROGRESS = "In progress"
WORKFLOW_STATUS_NEEDS_REVIEW = "Needs review"
WORKFLOW_STATUS_READY = "Ready"
WORKFLOW_STATUS_COMPLETED = "Completed"
RELEASE_STATUS_DEVELOPER_PREVIEW = "Developer Preview"


@dataclass(frozen=True)
class WorkflowDashboardStep:
    step_id: str
    title: str
    workflow_status: str
    release_status: str
    input_summary: str
    output_summary: str
    next_step: str
    entrypoint_page: str
    required_artifacts: tuple[str, ...] = ()
    existing_artifacts: tuple[str, ...] = ()
    missing_artifacts: tuple[str, ...] = ()
    task_count: int = 0
    audit_event_count: int = 0
    data_asset_count: int = 0
    warnings: tuple[str, ...] = ()
    testing_limitations: tuple[str, ...] = ()
    display_title_zh: str = ""
    subtitle_en: str = ""
    workflow_status_zh: str = ""
    release_status_zh: str = ""
    input_summary_zh: str = ""
    output_summary_zh: str = ""
    next_step_zh: str = ""
    entrypoint_label_zh: str = ""
    warning_summary_zh: str = ""


@dataclass(frozen=True)
class WorkflowDashboardState:
    title: str
    description: str
    status_label: str
    project_dir: str
    empty_state: str
    overall_status: str
    completed_count: int
    needs_review_count: int
    in_progress_count: int
    not_started_count: int
    ready_count: int
    manifest_status: str
    manifest_warnings: tuple[str, ...]
    audit_log_path: str
    data_asset_count: int
    task_count: int
    steps: tuple[WorkflowDashboardStep, ...]
    display_title_zh: str = WORKFLOW_DASHBOARD_TITLE_ZH
    description_zh: str = WORKFLOW_DASHBOARD_DESCRIPTION_ZH
    status_label_zh: str = ""
    empty_state_zh: str = WORKFLOW_EMPTY_STATE_ZH
    overall_status_zh: str = ""
    manifest_status_zh: str = ""
    developer_info_title_zh: str = DEVELOPER_INFO_TITLE_ZH


def initial_workflow_dashboard_state(project_dir: Path | None = None) -> WorkflowDashboardState:
    return WorkflowDashboardState(
        title="Meta Project Workflow Dashboard",
        description="Developer Preview / testing 总控页，汇总 Meta 项目从 protocol 到 reproducibility package 的状态、入口、输出和 warning。",
        status_label=RELEASE_STATUS_DEVELOPER_PREVIEW,
        project_dir=str(project_dir.expanduser().resolve()) if project_dir is not None else "",
        empty_state="选择或创建 Meta 项目目录后，此处会显示每一步的 Not started / Ready / Needs review / Completed 状态。",
        overall_status=WORKFLOW_STATUS_NOT_STARTED,
        completed_count=0,
        needs_review_count=0,
        in_progress_count=0,
        not_started_count=0,
        ready_count=0,
        manifest_status="not_checked",
        manifest_warnings=(),
        audit_log_path="",
        data_asset_count=0,
        task_count=0,
        steps=(),
        status_label_zh=release_status_zh(RELEASE_STATUS_DEVELOPER_PREVIEW),
        overall_status_zh=workflow_status_zh(WORKFLOW_STATUS_NOT_STARTED),
        manifest_status_zh="未检查",
    )


def workflow_dashboard_state_from_project(
    project_dir: Path,
    *,
    data_center: DataCenter | None = None,
    task_center: TaskCenter | None = None,
    audit_log: MetaAuditLogService | None = None,
) -> WorkflowDashboardState:
    project_dir = project_dir.expanduser().resolve()
    data_assets = data_center.list_assets(project_dir.name) if data_center is not None else []
    tasks = [task for task in task_center.list_tasks(limit=None) if task.project_id == project_dir.name] if task_center is not None else []
    audit_log = audit_log or MetaAuditLogService()
    audit_events = audit_log.list_events(project_dir)
    manifest_warnings = _manifest_warnings(project_dir)
    steps = tuple(_build_step(definition, project_dir, data_assets, tasks, audit_events) for definition in WORKFLOW_STEP_DEFINITIONS)
    counts = _status_counts(steps)
    overall = _overall_status(steps)
    return WorkflowDashboardState(
        title="Meta Project Workflow Dashboard",
        description="Developer Preview / testing 总控页，读取项目目录、canonical artifacts、Task Center、Data Center、audit log 和 manifests，帮助测试人员知道下一步该做什么。",
        status_label=RELEASE_STATUS_DEVELOPER_PREVIEW,
        project_dir=str(project_dir),
        empty_state="该项目尚未生成 Meta workflow artifacts；请从 Project Setup 或 Literature Import 开始。",
        overall_status=overall,
        completed_count=counts[WORKFLOW_STATUS_COMPLETED],
        needs_review_count=counts[WORKFLOW_STATUS_NEEDS_REVIEW],
        in_progress_count=counts[WORKFLOW_STATUS_IN_PROGRESS],
        not_started_count=counts[WORKFLOW_STATUS_NOT_STARTED],
        ready_count=counts[WORKFLOW_STATUS_READY],
        manifest_status=WORKFLOW_STATUS_COMPLETED if not manifest_warnings else WORKFLOW_STATUS_NEEDS_REVIEW,
        manifest_warnings=tuple(manifest_warnings),
        audit_log_path=str(audit_log.audit_path(project_dir)),
        data_asset_count=len(data_assets),
        task_count=len(tasks),
        steps=steps,
        status_label_zh=release_status_zh(RELEASE_STATUS_DEVELOPER_PREVIEW),
        overall_status_zh=workflow_status_zh(overall),
        manifest_status_zh=workflow_status_zh(WORKFLOW_STATUS_COMPLETED if not manifest_warnings else WORKFLOW_STATUS_NEEDS_REVIEW),
    )


WORKFLOW_STEP_DEFINITIONS: tuple[dict[str, object], ...] = (
    {
        "step_id": "project_setup",
        "title": "Project Setup",
        "required_artifacts": ("project.json",),
        "prerequisites": (),
        "task_types": (),
        "audit_events": (),
        "entrypoint_page": "Project Center / Meta workspace",
        "input_summary": "项目目录和 Meta project manifests。",
        "output_summary": "project.json、data_manifest.json、artifact_manifest.json、task_manifest.json、lineage_manifest.json。",
        "next_step": "Protocol / Research Question。",
    },
    {
        "step_id": "protocol",
        "title": "Protocol / Research Question",
        "required_artifacts": ("protocol/review_protocol.json",),
        "prerequisites": ("project.json",),
        "task_types": (),
        "audit_events": ("record_saved",),
        "data_types": ("review_protocol", "search_terms_draft", "search_strategy_preview", "protocol_summary"),
        "entrypoint_page": "Protocol / Research Question page",
        "input_summary": "研究标题、PICO/PICOS、目标分析类型和数据库计划。",
        "output_summary": "review_protocol.json、search_terms_draft.json、search_strategy_preview.md。",
        "next_step": "Literature Import。",
    },
    {
        "step_id": "literature_import",
        "title": "Literature Import",
        "required_artifacts": ("literature/literature_records.json",),
        "fallback_globs": ("literature_import/*_records.json",),
        "prerequisites": (),
        "task_types": ("literature_import",),
        "audit_events": ("import_batch_created", "record_saved"),
        "data_types": ("literature_records",),
        "entrypoint_page": "Literature Import page",
        "input_summary": "RIS / NBIB / CSV 文献导出文件。",
        "output_summary": "literature_records、import batch、Data Center literature_records。",
        "next_step": "Import Diagnostics。",
    },
    {
        "step_id": "import_diagnostics",
        "title": "Import Diagnostics",
        "required_artifacts": ("literature/import_diagnostics/",),
        "fallback_globs": ("literature/import_diagnostics/*_import_diagnostics.json",),
        "prerequisites": ("literature/literature_records.json",),
        "task_types": ("literature_import",),
        "audit_events": ("diagnostics_generated",),
        "entrypoint_page": "Literature Import diagnostics panel",
        "input_summary": "ImportBatch diagnostics JSON 和 warnings CSV。",
        "output_summary": "missing field counts、failed examples、warning severity。",
        "next_step": "Duplicate Review。",
    },
    {
        "step_id": "duplicate_review",
        "title": "Duplicate Review",
        "required_artifacts": ("deduplication/duplicate_candidate_groups.json",),
        "fallback_globs": ("deduplication/*duplicate_groups.json", "*duplicate_groups.json"),
        "prerequisites": ("literature/literature_records.json",),
        "task_types": ("duplicate_review", "dedup_decision"),
        "audit_events": ("duplicate_detected", "duplicate_decision"),
        "data_types": ("duplicate_candidate_groups", "deduplicated_literature"),
        "entrypoint_page": "Duplicate Review page",
        "input_summary": "screening_ready_records 或 imported literature records。",
        "output_summary": "duplicate groups、merge preview、dedup decisions、deduplicated_literature。",
        "next_step": "Criteria Builder / Screening。",
    },
    {
        "step_id": "criteria_builder",
        "title": "Criteria Builder",
        "required_artifacts": ("criteria/criteria_summary.md",),
        "prerequisites": ("protocol/review_protocol.json",),
        "task_types": (),
        "audit_events": ("record_saved",),
        "data_types": ("inclusion_criteria", "exclusion_criteria", "criteria_summary"),
        "entrypoint_page": "Criteria page (planned AB5)",
        "input_summary": "Protocol / PICO-PICOS。",
        "output_summary": "inclusion_criteria.json、exclusion_criteria.json、criteria_summary.md。",
        "next_step": "Title / Abstract Screening。",
    },
    {
        "step_id": "title_abstract_screening",
        "title": "Title / Abstract Screening",
        "required_artifacts": ("screening/screening_decisions.json", "screening/title_abstract_decisions.json"),
        "prerequisites": ("deduplication/deduplicated_literature.json", "literature/literature_records.json"),
        "task_types": ("screening", "screening_decision"),
        "audit_events": ("screening_decision",),
        "data_types": ("screening_queue", "screening_decisions"),
        "entrypoint_page": "Screening page",
        "input_summary": "deduplicated_literature 或 screening queue。",
        "output_summary": "title_abstract_decisions、screening_summary、screening_decisions。",
        "next_step": "Full-text / Attachment。",
    },
    {
        "step_id": "fulltext_attachment",
        "title": "Full-text / Attachment",
        "required_artifacts": ("fulltext/fulltext_eligibility_decisions.json", "fulltext/final_included_studies.json"),
        "fallback_globs": ("fulltext/fulltext_registry.json", "attachments/attachment_registry.json"),
        "prerequisites": ("screening/screening_decisions.json", "screening/title_abstract_decisions.json"),
        "task_types": ("fulltext_attach", "fulltext_screening_decision", "fulltext_exclusion_export", "attachment_link", "attachment_copy", "missing_fulltext_report_export"),
        "audit_events": ("fulltext_status_changed",),
        "data_types": ("fulltext_registry", "attachment_registry", "missing_fulltext_report", "fulltext_eligibility_decisions", "final_included_studies"),
        "entrypoint_page": "Full-text / Attachment / Eligibility page",
        "input_summary": "included / maybe records 和本地 PDF 路径。",
        "output_summary": "fulltext_eligibility_decisions、fulltext_exclusion_report、final_included_studies，并保留 fulltext_registry / attachment_registry。",
        "next_step": "Extraction。",
    },
    {
        "step_id": "extraction",
        "title": "Extraction",
        "required_artifacts": ("extraction/extraction_records.json",),
        "prerequisites": ("screening/screening_decisions.json", "fulltext/final_included_studies.json"),
        "task_types": ("extraction", "extraction_record_save", "extraction_export"),
        "audit_events": ("extraction_updated",),
        "data_types": ("extraction_pool", "extraction_records"),
        "entrypoint_page": "Extraction page",
        "input_summary": "included studies 和 extraction schema。",
        "output_summary": "extraction_records、drafts、validation report、CSV export。",
        "next_step": "Quality Assessment。",
    },
    {
        "step_id": "quality_assessment",
        "title": "Quality Assessment",
        "required_artifacts": ("quality/quality_assessments.json", "exports/quality_assessment_table.csv"),
        "prerequisites": ("extraction/extraction_records.json",),
        "task_types": ("quality_assessment_save", "quality_assessment_export"),
        "audit_events": (),
        "data_types": ("quality_assessments", "quality_assessment_table"),
        "entrypoint_page": "Quality page",
        "input_summary": "included studies 和 quality tool registry。",
        "output_summary": "quality_assessments、quality_assessment_table、quality summary。",
        "next_step": "Analysis-ready Dataset。",
    },
    {
        "step_id": "analysis_ready_dataset",
        "title": "Analysis-ready Dataset",
        "required_artifacts": ("analysis/analysis_ready_datasets.json",),
        "prerequisites": ("extraction/extraction_records.json",),
        "task_types": ("analysis_dataset_build", "analysis"),
        "audit_events": (),
        "data_types": ("analysis_ready_dataset",),
        "entrypoint_page": "Analysis page",
        "input_summary": "extraction_records 和 selected outcome/effect measure。",
        "output_summary": "analysis_ready_datasets 和 validation summary。",
        "next_step": "Meta-analysis Run。",
    },
    {
        "step_id": "meta_analysis_run",
        "title": "Meta-analysis Run",
        "required_artifacts": ("analysis/analysis_results.json",),
        "prerequisites": ("analysis/analysis_ready_datasets.json",),
        "task_types": ("meta_analysis_run",),
        "audit_events": ("analysis_run_completed",),
        "data_types": ("analysis_result",),
        "entrypoint_page": "Analysis page",
        "input_summary": "analysis-ready dataset 和 fixed/random model 参数。",
        "output_summary": "analysis_results、study-level effects、heterogeneity、applicability warnings。",
        "next_step": "Figures / Tables。",
    },
    {
        "step_id": "figures_tables",
        "title": "Figures / Tables",
        "required_artifacts": ("figures/figure_artifacts.json", "exports/"),
        "fallback_globs": ("figures/forest_plot_*", "figures/funnel_plot_*", "exports/analysis_result_table_*.csv"),
        "prerequisites": ("analysis/analysis_results.json",),
        "task_types": ("forest_plot_export", "funnel_plot_export", "analysis_result_table_export"),
        "audit_events": (),
        "data_types": ("forest_plot", "funnel_plot", "analysis_result_table"),
        "entrypoint_page": "Analysis / Figures panel",
        "input_summary": "analysis_result。",
        "output_summary": "forest/funnel plot PNG/SVG and analysis result table CSV。",
        "next_step": "PRISMA / Report。",
    },
    {
        "step_id": "prisma_report",
        "title": "PRISMA / Report",
        "required_artifacts": ("reports/prisma_flow_summary.json", "reports/formal_meta_report.md"),
        "prerequisites": ("analysis/analysis_results.json",),
        "task_types": ("prisma_collect", "formal_report_export", "html_report_export", "word_report_export"),
        "audit_events": ("report_exported",),
        "data_types": ("prisma_flow_summary", "formal_meta_report", "formal_html_report", "formal_word_report"),
        "entrypoint_page": "Reporting page",
        "input_summary": "import/dedup/screening/full-text/extraction/analysis/figure artifacts。",
        "output_summary": "PRISMA summary、formal Markdown/HTML/DOCX testing report、report_manifest。",
        "next_step": "Reproducibility Package。",
    },
    {
        "step_id": "reproducibility_package",
        "title": "Reproducibility Package",
        "required_artifacts": ("exports/",),
        "fallback_globs": ("exports/reproducibility_package_*.zip",),
        "prerequisites": ("reports/formal_meta_report.md",),
        "task_types": ("reproducibility_package_export", "project_snapshot_create", "supplementary_export", "figure_package_export"),
        "audit_events": (),
        "data_types": ("reproducibility_package", "project_snapshot", "supplementary_exports", "figure_package"),
        "entrypoint_page": "Reporting / Export panel",
        "input_summary": "complete project artifacts and manifests。",
        "output_summary": "reproducibility package ZIP、supplementary exports、figure package、snapshot。",
        "next_step": "Internal beta review。",
    },
)


def _build_step(
    definition: dict[str, object],
    project_dir: Path,
    data_assets: list[object],
    tasks: list[object],
    audit_events: list[object],
) -> WorkflowDashboardStep:
    required = tuple(str(item) for item in definition.get("required_artifacts", ()))
    fallback_globs = tuple(str(item) for item in definition.get("fallback_globs", ()))
    prerequisites = tuple(str(item) for item in definition.get("prerequisites", ()))
    task_types = tuple(str(item) for item in definition.get("task_types", ()))
    audit_event_types = tuple(str(item) for item in definition.get("audit_events", ()))
    data_types = tuple(str(item) for item in definition.get("data_types", ()))
    existing = _existing_artifacts(project_dir, required, fallback_globs)
    missing = tuple(item for item in required if not _artifact_exists(project_dir, item))
    task_matches = [task for task in tasks if getattr(getattr(task, "task_type", ""), "value", str(getattr(task, "task_type", ""))) in task_types]
    running_tasks = [
        task
        for task in task_matches
        if getattr(task, "status", "") in {TaskStatus.PENDING, TaskStatus.RUNNING}
        or getattr(getattr(task, "status", ""), "value", "") in {"pending", "running"}
    ]
    audit_count = len([event for event in audit_events if getattr(event, "event_type", "") in audit_event_types])
    data_count = len([asset for asset in data_assets if getattr(asset, "data_type", "") in data_types])
    warnings = _step_warnings(str(definition["step_id"]), project_dir, existing, missing)
    status = _infer_step_status(
        project_dir=project_dir,
        required=required,
        existing=existing,
        prerequisites=prerequisites,
        running_tasks=running_tasks,
        warnings=warnings,
        step_id=str(definition["step_id"]),
    )
    step_text = workflow_step_text(str(definition["step_id"]))
    return WorkflowDashboardStep(
        step_id=str(definition["step_id"]),
        title=str(definition["title"]),
        workflow_status=status,
        release_status=RELEASE_STATUS_DEVELOPER_PREVIEW,
        input_summary=str(definition["input_summary"]),
        output_summary=str(definition["output_summary"]),
        next_step=str(definition["next_step"]),
        entrypoint_page=str(definition["entrypoint_page"]),
        required_artifacts=required,
        existing_artifacts=existing,
        missing_artifacts=missing,
        task_count=len(task_matches),
        audit_event_count=audit_count,
        data_asset_count=data_count,
        warnings=tuple(warnings),
        testing_limitations=(
            "Developer Preview / testing：状态来自本地 artifacts、tasks、data assets 和 audit log。",
            "缺失 artifact 会显示 warning，不会阻塞其他页面打开。",
        ),
        display_title_zh=step_text.title_zh,
        subtitle_en=step_text.subtitle_en,
        workflow_status_zh=workflow_status_zh(status),
        release_status_zh=release_status_zh(RELEASE_STATUS_DEVELOPER_PREVIEW),
        input_summary_zh=step_text.input_summary_zh,
        output_summary_zh=step_text.output_summary_zh,
        next_step_zh=step_text.next_step_zh,
        entrypoint_label_zh=step_text.entrypoint_zh,
        warning_summary_zh=warning_summary_zh(warnings),
    )


def _infer_step_status(
    *,
    project_dir: Path,
    required: tuple[str, ...],
    existing: tuple[str, ...],
    prerequisites: tuple[str, ...],
    running_tasks: list[object],
    warnings: list[str],
    step_id: str,
) -> str:
    if running_tasks:
        return WORKFLOW_STATUS_IN_PROGRESS
    if step_id == "protocol":
        return _protocol_status(project_dir)
    if _step_complete(step_id, required, existing):
        return WORKFLOW_STATUS_NEEDS_REVIEW if warnings else WORKFLOW_STATUS_COMPLETED
    if any(_artifact_exists(project_dir, item) for item in prerequisites):
        return WORKFLOW_STATUS_READY
    return WORKFLOW_STATUS_NOT_STARTED


def _step_complete(step_id: str, required: tuple[str, ...], existing: tuple[str, ...]) -> bool:
    if not required:
        return bool(existing)
    return bool(existing)


def _existing_artifacts(project_dir: Path, required: tuple[str, ...], fallback_globs: tuple[str, ...]) -> tuple[str, ...]:
    existing: list[str] = []
    for relative in required:
        if _artifact_exists(project_dir, relative):
            existing.append(relative)
    for pattern in fallback_globs:
        for path in project_dir.glob(pattern):
            if path.exists():
                existing.append(str(path.relative_to(project_dir)))
    return tuple(dict.fromkeys(existing))


def _artifact_exists(project_dir: Path, relative: str) -> bool:
    path = project_dir / relative
    if relative.endswith("/"):
        return path.exists() and path.is_dir() and any(path.iterdir())
    return path.exists()


def _step_warnings(step_id: str, project_dir: Path, existing: tuple[str, ...], missing: tuple[str, ...]) -> list[str]:
    warnings: list[str] = []
    if step_id == "project_setup":
        warnings.extend(_manifest_warnings(project_dir))
    if step_id == "protocol":
        warnings.extend(_protocol_warnings(project_dir))
    if step_id == "import_diagnostics":
        warnings.extend(_diagnostics_warnings(project_dir))
    if step_id == "duplicate_review":
        warnings.extend(_duplicate_review_warnings(project_dir))
    if step_id == "fulltext_attachment":
        warnings.extend(_fulltext_warnings(project_dir))
    if step_id == "extraction":
        warnings.extend(_extraction_warnings(project_dir))
    if step_id == "meta_analysis_run":
        warnings.extend(_analysis_warnings(project_dir))
    if step_id == "prisma_report":
        warnings.extend(_report_warnings(project_dir))
    if not existing and missing:
        warnings.append(f"missing_required_artifacts:{','.join(missing)}")
    return warnings


def _protocol_status(project_dir: Path) -> str:
    protocol_path = project_dir / "protocol" / "review_protocol.json"
    if not protocol_path.exists():
        return WORKFLOW_STATUS_NOT_STARTED
    payload = _load_json(protocol_path)
    readiness = str(payload.get("readiness_status", ""))
    confirmed = bool(payload.get("confirmed", False))
    strategy_path = project_dir / "protocol" / "search_strategy_preview.md"
    warnings = payload.get("warnings", [])
    has_warnings = bool(warnings) if isinstance(warnings, list) else False
    if confirmed or readiness == "completed":
        return WORKFLOW_STATUS_COMPLETED
    if strategy_path.exists() and has_warnings:
        return WORKFLOW_STATUS_NEEDS_REVIEW
    if strategy_path.exists() and readiness in {"ready", "completed"}:
        return WORKFLOW_STATUS_READY
    return WORKFLOW_STATUS_IN_PROGRESS


def _protocol_warnings(project_dir: Path) -> list[str]:
    protocol_path = project_dir / "protocol" / "review_protocol.json"
    if not protocol_path.exists():
        return []
    payload = _load_json(protocol_path)
    warnings = payload.get("warnings", [])
    output = [str(item) for item in warnings if str(item).strip()] if isinstance(warnings, list) else []
    if not (project_dir / "protocol" / "search_terms_draft.json").exists():
        output.append("missing_search_terms_draft")
    if not (project_dir / "protocol" / "search_strategy_preview.md").exists():
        output.append("missing_search_strategy_preview")
    return output


def _manifest_warnings(project_dir: Path) -> list[str]:
    return [f"manifest_missing:{filename}" for filename in MANIFEST_FILES if not (project_dir / filename).exists()]


def _diagnostics_warnings(project_dir: Path) -> list[str]:
    warnings: list[str] = []
    for path in sorted((project_dir / "literature" / "import_diagnostics").glob("*_import_diagnostics.json")):
        payload = _load_json(path)
        for key in ("failed_record_count", "warning_count", "missing_title_count", "invalid_doi_count", "invalid_year_count"):
            value = _int_value(payload.get(key, 0))
            if value:
                warnings.append(f"{path.name}:{key}:{value}")
    return warnings


def _duplicate_review_warnings(project_dir: Path) -> list[str]:
    warnings: list[str] = []
    for path in sorted((project_dir / "deduplication").glob("*duplicate_groups.json")):
        payload = _load_json(path)
        groups = payload.get("duplicate_groups", [])
        if isinstance(groups, list) and groups:
            decisions_path = path.with_name(path.name.replace("_duplicate_groups.json", "_dedup_decisions.json"))
            if not decisions_path.exists():
                warnings.append(f"duplicate_groups_need_review:{len(groups)}")
    return warnings


def _fulltext_warnings(project_dir: Path) -> list[str]:
    warnings: list[str] = []
    missing_report = project_dir / "reports" / "missing_fulltext_report.csv"
    if missing_report.exists():
        with missing_report.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        missing_count = len([row for row in rows if str(row.get("missing_fulltext", "")).lower() == "true"])
        if missing_count:
            warnings.append(f"missing_fulltext_count:{missing_count}")
    attachment_registry = _load_json(project_dir / "attachments" / "attachment_registry.json")
    attachments = attachment_registry.get("attachments", [])
    if isinstance(attachments, list):
        broken = len([item for item in attachments if isinstance(item, dict) and not Path(str(item.get("file_path", ""))).exists()])
        if broken:
            warnings.append(f"broken_attachment_paths:{broken}")
    eligibility = _load_json(project_dir / "fulltext" / "fulltext_eligibility_decisions.json")
    decisions = eligibility.get("decisions", [])
    if isinstance(decisions, list):
        blocked = len(
            [
                item
                for item in decisions
                if isinstance(item, dict) and item.get("eligibility_status") in {"missing_full_text", "failed_to_access", "excluded_after_full_text_review"}
            ]
        )
        if blocked:
            warnings.append(f"fulltext_excluded_or_missing:{blocked}")
    if (project_dir / "fulltext" / "fulltext_eligibility_decisions.json").exists() and not (project_dir / "fulltext" / "final_included_studies.json").exists():
        warnings.append("missing_final_included_studies")
    return warnings


def _extraction_warnings(project_dir: Path) -> list[str]:
    payload = _load_json(project_dir / "extraction" / "extraction_validation_report.json")
    warnings = payload.get("warnings", [])
    errors = payload.get("errors", [])
    output: list[str] = []
    if isinstance(errors, list) and errors:
        output.append(f"extraction_validation_errors:{len(errors)}")
    if isinstance(warnings, list) and warnings:
        output.append(f"extraction_validation_warnings:{len(warnings)}")
    return output


def _analysis_warnings(project_dir: Path) -> list[str]:
    warnings_path = project_dir / "analysis" / "applicability_warnings.json"
    payload = _load_json(warnings_path)
    warnings = payload.get("warnings", [])
    if isinstance(warnings, list) and warnings:
        return [f"applicability_warnings:{len(warnings)}"]
    return []


def _report_warnings(project_dir: Path) -> list[str]:
    report_manifest = _load_json(project_dir / "reports" / "report_manifest.json")
    sections = report_manifest.get("sections", [])
    if not isinstance(sections, list):
        return []
    missing = [section for section in sections if isinstance(section, dict) and section.get("status") in {"missing", "placeholder"}]
    return [f"report_sections_need_review:{len(missing)}"] if missing else []


def _status_counts(steps: tuple[WorkflowDashboardStep, ...]) -> dict[str, int]:
    counts = {
        WORKFLOW_STATUS_NOT_STARTED: 0,
        WORKFLOW_STATUS_IN_PROGRESS: 0,
        WORKFLOW_STATUS_NEEDS_REVIEW: 0,
        WORKFLOW_STATUS_READY: 0,
        WORKFLOW_STATUS_COMPLETED: 0,
    }
    for step in steps:
        counts[step.workflow_status] = counts.get(step.workflow_status, 0) + 1
    return counts


def _overall_status(steps: tuple[WorkflowDashboardStep, ...]) -> str:
    if any(step.workflow_status == WORKFLOW_STATUS_IN_PROGRESS for step in steps):
        return WORKFLOW_STATUS_IN_PROGRESS
    if any(step.workflow_status == WORKFLOW_STATUS_NEEDS_REVIEW for step in steps):
        return WORKFLOW_STATUS_NEEDS_REVIEW
    if all(step.workflow_status == WORKFLOW_STATUS_COMPLETED for step in steps):
        return WORKFLOW_STATUS_COMPLETED
    if any(step.workflow_status in {WORKFLOW_STATUS_READY, WORKFLOW_STATUS_COMPLETED} for step in steps):
        return WORKFLOW_STATUS_READY
    return WORKFLOW_STATUS_NOT_STARTED


def _load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _int_value(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


try:
    from PySide6.QtWidgets import QFrame, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFrame = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class WorkflowDashboardPage(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self._state = initial_workflow_dashboard_state()
            root = QVBoxLayout(self)
            title = QLabel(self._state.display_title_zh)
            title.setStyleSheet("font-size: 20px; font-weight: 700;")
            root.addWidget(title)
            description = QLabel(self._state.description_zh)
            description.setWordWrap(True)
            root.addWidget(description)
            root.addWidget(QLabel(f"功能状态：{self._state.status_label_zh} / {self._state.status_label}"))
            self._project_dir_input = QLineEdit()
            self._project_dir_input.setPlaceholderText("选择或粘贴 Meta 项目目录路径")
            root.addWidget(self._project_dir_input)
            refresh = QPushButton("刷新流程状态")
            refresh.clicked.connect(self._refresh)
            root.addWidget(refresh)
            card = QFrame()
            card.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            layout = QVBoxLayout(card)
            self._summary_label = QLabel(self._state.empty_state)
            self._summary_label.setWordWrap(True)
            layout.addWidget(self._summary_label)
            root.addWidget(card)
            root.addStretch(1)

        def _refresh(self) -> None:
            state = workflow_dashboard_state_from_project(Path(self._project_dir_input.text()).expanduser())
            step_lines = [
                f"- {step.display_title_zh} {step.subtitle_en}: {step.workflow_status_zh} / {step.release_status_zh}; "
                f"下一步：{step.next_step_zh}; 问题：{len(step.warnings)}；进入：{step.entrypoint_label_zh}"
                for step in state.steps
            ]
            self._summary_label.setText(
                f"项目目录：{state.project_dir}\n"
                f"总体状态：{state.overall_status_zh} / {state.overall_status}\n"
                f"已完成 / 已就绪 / 需要复核 / 进行中 / 未开始："
                f"{state.completed_count} / {state.ready_count} / {state.needs_review_count} / {state.in_progress_count} / {state.not_started_count}\n"
                f"项目文件状态：{state.manifest_status_zh}\n"
                f"{state.developer_info_title_zh}：audit_log={state.audit_log_path}; data_assets={state.data_asset_count}; tasks={state.task_count}\n"
                + "\n".join(step_lines)
            )

else:

    class WorkflowDashboardPage:  # type: ignore[no-redef]
        pass
