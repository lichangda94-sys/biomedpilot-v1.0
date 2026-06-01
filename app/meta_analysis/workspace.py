from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Callable

from app.shared.feature_availability import FeatureAvailability, FeatureAvailabilityStatus, list_features
from app.shared.feature_status import FeatureItem, feature_item_from_availability
from app.shared.result_report_export_shell import make_result_report_export_adoption_panel
from app.shared.semantic_keys import FeatureStatusKey, ModuleKey, PageKey
from app.shared.storage import default_storage_root
from app.shared.ui_components.common import WorkflowStep, make_workflow_stepper
from app.shared.ui_components.dense_workbench import (
    ExtractionField,
    ReferenceItem,
    make_extraction_form_table,
    make_preview_card,
    make_reference_queue_panel,
)
from app.shared.ui_components.primitives import make_card, make_status_chip
from app.shared.ui_components.specialized import ExportFormatAction, ExportGateCheck, make_export_gate_panel, make_plot_placeholder
from app.shared.ui_components.workbench import make_workbench_shell
from app.version import APP_VERSION

from app.meta_analysis.project_workspace import MetaProjectSummary, create_meta_analysis_project, open_meta_analysis_project
from app.meta_analysis.services.extraction_schema_registry_v1_service import ExtractionSchemaRegistryV1Service
from app.meta_analysis.services.pico_workspace_service import PICOWorkspaceService
from app.meta_analysis.search.search_strategy_builder_service import SearchStrategyBuilderService
from app.meta_analysis.services.title_abstract_screening_v2_service import TitleAbstractScreeningV2Service
from app.meta_analysis.version import META_INTERNAL_BETA_VERSION, META_SOFTWARE_STATUS

META_ANALYSIS_MAINLINE_CONTRACT_VERSION = META_INTERNAL_BETA_VERSION

try:
    from PySide6.QtCore import QSize, Qt
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QApplication,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QStackedWidget,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    from app.app_identity import META_PAGE_ICON_PATHS, load_meta_page_icon
except Exception:  # pragma: no cover
    QSize = None  # type: ignore[assignment]
    QWidget = None  # type: ignore[assignment]
    META_PAGE_ICON_PATHS = {}
    load_meta_page_icon = None  # type: ignore[assignment]


def meta_analysis_features() -> list[FeatureItem]:
    return [feature_item_from_availability(feature) for feature in meta_analysis_step_features()]


def meta_analysis_step_features() -> list[FeatureAvailability]:
    step_ids = {
        "meta-literature-import",
        "meta-dedup-prep",
        "meta-duplicate-review",
        "meta-screening",
        "meta-extraction",
        "meta-analysis",
        "meta-reporting",
    }
    features = [feature for feature in list_features("meta_analysis") if feature.feature_id in step_ids]
    if features:
        return features
    return [
        FeatureAvailability(
            "meta_analysis",
            "meta-mainline-shell",
            "Meta 分析入口",
            FeatureAvailabilityStatus.TESTING,
            "mainline 保留 Meta 模块入口、项目绑定和占位工作台；完整流程在 dev/meta-analysis 开发。",
            "在 dev/meta-analysis 完成验收后再合入具体功能。",
            "app/meta_analysis/workspace.py",
        )
    ]


@dataclass(frozen=True)
class MetaWorkspaceNavigationItem:
    step_id: str
    label: str
    description: str
    page_key: str
    status_label: str = "Mainline shell"
    status_label_zh: str = "主线壳"


@dataclass(frozen=True)
class MetaWorkspaceLayoutState:
    title: str
    status_label: str
    description: str
    navigation_items: tuple[MetaWorkspaceNavigationItem, ...]
    default_page_key: str
    testing_notice: str
    version_status_label: str = ""
    entry_title: str = "Meta 分析模块"
    developer_info_label: str = "开发者信息"


@dataclass(frozen=True)
class ImportBatchQualitySummary:
    batch_id: str
    project_id: str
    source_database: str
    source_format: str
    status: str
    created_at: str
    raw_record_count: int
    parsed_record_count: int
    normalized_record_count: int
    failed_record_count: int
    warning_count: int
    duplicate_candidate_count: int
    linked_literature_record_count: int
    diagnostics_path: str
    diagnostics_summary: str = ""


@dataclass(frozen=True)
class LiteratureImportQualityDashboardState:
    title: str
    status_label: str
    description: str
    empty_state: str
    batch_count: int
    batches: tuple[ImportBatchQualitySummary, ...]


@dataclass(frozen=True)
class MetaTargetIAPage:
    key: str
    label: str
    status_key: str
    boundary: str
    page_group: str
    flow_index: int


@dataclass(frozen=True)
class MetaActiveType:
    type_id: str
    label_zh: str
    effect_size: str
    group: str
    status_key: str = "testing"
    interaction_mode: str = "schema_shell"


def meta_target_ia_pages() -> tuple[MetaTargetIAPage, ...]:
    return (
        MetaTargetIAPage("project_home", "Project Home / 项目首页", "shell_only", "项目状态总览；不声明生产级系统综述能力。", "main_flow", 1),
        MetaTargetIAPage("question_meta_type", "Question & Meta Type / 研究问题与 Meta 类型", "testing", "选择 active Meta 类型，控制后续 extraction schema、质量评价和统计任务。", "main_flow", 2),
        MetaTargetIAPage("search_strategy", "Search Strategy / 检索策略", "testing", "检索策略和检索计划；不是自动系统综述结论。", "main_flow", 3),
        MetaTargetIAPage("import_dedup", "Import & Deduplication / 文献导入与去重", "testing", "导入、文献库和去重壳层；保留人工审核。", "main_flow", 4),
        MetaTargetIAPage("screening", "Screening / 文献筛选", "testing", "标题摘要、全文筛选和排除理由；AI 仅辅助建议。", "main_flow", 5),
        MetaTargetIAPage("fulltext_extraction", "Full-text & Extraction / 全文与数据提取", "testing", "按 Meta 类型加载不同数据提取结构；需要人工复核。", "main_flow", 6),
        MetaTargetIAPage("quality_assessment", "Quality Assessment / 质量评价", "planned", "按 Meta 类型选择评价工具；当前仅目标 IA 壳层。", "main_flow", 7),
        MetaTargetIAPage("analysis_tasks", "Meta Analysis Tasks / 统计分析", "planned", "显示类型专属统计任务边界；不启用 Network Meta。", "main_flow", 8),
        MetaTargetIAPage("result_report", "Result & Report / 结果与报告", "shell_only", "仅展示测试边界，不生成生产级结果或投稿级系统综述。", "main_flow", 9),
        MetaTargetIAPage("report_export", "Report Export / 报告导出", "shell_only", "报告草稿边界；不声明投稿级输出。", "main_flow", 10),
        MetaTargetIAPage("meta_settings", "Meta Settings / Meta 设置", "shell_only", "Meta 偏好、日志和外部资源检测入口。", "auxiliary", 1),
    )


def meta_active_types_v1() -> tuple[MetaActiveType, ...]:
    return (
        MetaActiveType("binary_outcome_meta", "二分类结局 Meta", "OR / RR / RD", "结局型 Meta"),
        MetaActiveType("continuous_outcome_meta", "连续结局 Meta", "MD / SMD / WMD", "结局型 Meta"),
        MetaActiveType("survival_outcome_meta", "生存结局 Meta", "HR", "结局型 Meta"),
        MetaActiveType("prevalence_incidence_meta", "患病率 / 发生率 Meta", "event / total / rate", "流行病学 Meta"),
        MetaActiveType("diagnostic_accuracy_meta", "诊断准确性 Meta", "TP / FP / FN / TN", "诊断与关联 Meta"),
        MetaActiveType("exposure_disease_risk_meta", "暴露-疾病风险 Meta", "OR / RR / HR", "诊断与关联 Meta"),
        MetaActiveType("biomarker_expression_difference_meta", "生物标志物表达差异 Meta", "表达差异 / 组间比较", "诊断与关联 Meta"),
        MetaActiveType("correlation_meta", "相关性 Meta", "r / Fisher z", "关联与预后 Meta"),
        MetaActiveType("prognostic_factor_meta", "预后因素 Meta", "HR / OR", "关联与预后 Meta"),
        MetaActiveType("dose_response_meta", "剂量反应 Meta", "testing schema only", "Testing schema"),
    )


_META_PAGE_SEMANTIC_KEYS = {
    "project_home": PageKey.META_PROJECT_HOME.value,
    "question_meta_type": PageKey.META_QUESTION_TYPE.value,
    "search_strategy": PageKey.META_SEARCH_STRATEGY.value,
    "import_dedup": PageKey.META_IMPORT_DEDUP.value,
    "screening": PageKey.META_SCREENING.value,
    "fulltext_extraction": PageKey.META_FULLTEXT_EXTRACTION.value,
    "quality_assessment": PageKey.META_QUALITY_ASSESSMENT.value,
    "analysis_tasks": PageKey.META_ANALYSIS_TASKS.value,
    "result_report": PageKey.META_RESULT_REPORT.value,
    "report_export": PageKey.META_REPORT_EXPORT.value,
    "meta_settings": PageKey.META_SETTINGS.value,
}

_META_STATUS_SEMANTIC_KEYS = {
    "shell_only": FeatureStatusKey.SHELL_ONLY.value,
    "testing": FeatureStatusKey.TESTING.value,
    "planned": FeatureStatusKey.PLANNED.value,
}


def meta_workspace_layout_state() -> MetaWorkspaceLayoutState:
    version_status = f"{APP_VERSION} · 内部测试版 / {META_SOFTWARE_STATUS} · {META_ANALYSIS_MAINLINE_CONTRACT_VERSION}"
    return MetaWorkspaceLayoutState(
        title="Meta 分析模块",
        status_label=version_status,
        description="使用 UIShell 成熟 target IA：项目、问题类型、检索、导入去重、筛选、全文提取、质量评价、统计、结果报告和导出门控。",
        navigation_items=(
            MetaWorkspaceNavigationItem("target_ia", "Meta UIShell target IA", "UIShell high-fidelity gated runtime baseline.", "target_ia"),
        ),
        default_page_key="target_ia",
        testing_notice="当前 Meta 分析模块为 Developer Preview；旧页面仅作为后端能力来源，最终视觉页面以 UIShell target IA 为准。",
        version_status_label=version_status,
    )


def recent_import_batch_summaries(root_dir: Path | None = None, *, limit: int = 5) -> list[dict[str, object]]:
    return [
        {
            "project_id": summary.project_id,
            "batch_id": summary.batch_id,
            "source_database": summary.source_database,
            "format": summary.source_format,
            "source_format": summary.source_format,
            "status": summary.status,
            "raw_record_count": summary.raw_record_count,
            "parsed_count": summary.parsed_record_count,
            "parsed_record_count": summary.parsed_record_count,
            "normalized_record_count": summary.normalized_record_count,
            "failed_record_count": summary.failed_record_count,
            "warning_count": summary.warning_count,
            "duplicate_candidate_count": summary.duplicate_candidate_count,
            "linked_literature_record_count": summary.linked_literature_record_count,
            "diagnostics_path": summary.diagnostics_path,
            "diagnostics_summary": summary.diagnostics_summary,
            "created_at": summary.created_at,
        }
        for summary in recent_import_batch_quality_summaries(root_dir, limit=limit)
    ]


def recent_import_batch_quality_summaries(root_dir: Path | None = None, *, limit: int = 5) -> list[ImportBatchQualitySummary]:
    root = root_dir or default_storage_root()
    summaries: list[ImportBatchQualitySummary] = []
    for path in (root / "projects").glob("*/meta_analysis/literature_import/*_records.json"):
        payload = _load_json_object(path)
        if payload:
            summaries.append(_summary_from_unified_import(path, payload))
    for item in _load_json_list(root / "literature" / "import_batches.json"):
        metadata = dict(item.get("metadata", {})) if isinstance(item.get("metadata"), dict) else {}
        batch_id = str(item.get("batch_id", ""))
        diagnostics_path = root / "literature" / "import_diagnostics" / f"{batch_id}_import_diagnostics.json"
        diagnostics = _load_json_object(diagnostics_path)
        summaries.append(
            ImportBatchQualitySummary(
                batch_id=batch_id,
                project_id=str(item.get("project_id", "")),
                source_database=str(metadata.get("source_database") or item.get("source_type", "")),
                source_format=str(item.get("format_hint", "")),
                status=str(item.get("status", "")),
                created_at=str(item.get("created_at", "")),
                raw_record_count=_int_from(item, "raw_record_count", _int_from(item, "total_records", 0)),
                parsed_record_count=_int_from(item, "parsed_record_count", _int_from(item, "imported_records", 0)),
                normalized_record_count=_int_from(item, "normalized_record_count", _int_from(item, "imported_records", 0)),
                failed_record_count=_int_from(item, "failed_records", _int_from(item, "failed_record_count", 0)),
                warning_count=_int_from(item, "warning_count", _int_from(diagnostics, "warning_count", 0)),
                duplicate_candidate_count=_int_from(item, "duplicate_candidate_count", _int_from(diagnostics, "duplicate_candidate_count", 0)),
                linked_literature_record_count=_int_from(item, "normalized_record_count", _int_from(item, "imported_records", 0)),
                diagnostics_path=str(diagnostics_path) if diagnostics_path.exists() else "",
                diagnostics_summary=_diagnostics_summary_text(diagnostics),
            )
        )
    deduped = {f"{item.project_id}:{item.batch_id}:{item.created_at}": item for item in summaries}
    return sorted(deduped.values(), key=lambda item: item.created_at, reverse=True)[:limit]


def literature_import_quality_dashboard_state(root_dir: Path | None = None, *, limit: int = 5) -> LiteratureImportQualityDashboardState:
    batches = tuple(recent_import_batch_quality_summaries(root_dir, limit=limit))
    return LiteratureImportQualityDashboardState(
        title="Meta Literature Import Quality Dashboard",
        status_label="Testing / Developer Preview",
        description="只读显示最近文献导入批次的解析质量、warning 数量、failed 数量、duplicate candidate 数量和 diagnostics 路径。",
        empty_state="暂无导入批次。请先在 UIShell Meta Import & Deduplication 页面接入导入 adapter。",
        batch_count=len(batches),
        batches=batches,
    )


def _summary_from_unified_import(path: Path, payload: dict[str, object]) -> ImportBatchQualitySummary:
    records = list(payload.get("records", []))
    diagnostics_path = str(payload.get("diagnostics_path", ""))
    diagnostics = _load_json_object(Path(diagnostics_path)) if diagnostics_path else {}
    source_type = str(payload.get("source_type", ""))
    return ImportBatchQualitySummary(
        batch_id=str(payload.get("batch_id", path.stem.replace("_records", ""))),
        project_id=str(payload.get("project_id", path.parents[2].name)),
        source_database=str(payload.get("source_database") or source_type or "local_file"),
        source_format=str(payload.get("source_format") or source_type),
        status=str(payload.get("status") or "completed"),
        created_at=str(payload.get("created_at", "")),
        raw_record_count=_int_from(diagnostics, "raw_record_count", len(records)),
        parsed_record_count=_int_from(diagnostics, "parsed_record_count", len(records)),
        normalized_record_count=_int_from(diagnostics, "normalized_record_count", len(records)),
        failed_record_count=_int_from(diagnostics, "failed_record_count", 0),
        warning_count=_int_from(diagnostics, "warning_count", _int_from(payload, "warning_count", 0)),
        duplicate_candidate_count=_int_from(diagnostics, "duplicate_candidate_count", _int_from(payload, "duplicate_candidate_count", 0)),
        linked_literature_record_count=len(records),
        diagnostics_path=diagnostics_path,
        diagnostics_summary=_diagnostics_summary_text(diagnostics),
    )


def _load_json_object(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_json_list(path: Path) -> list[dict[str, object]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def _int_from(payload: dict[str, object], key: str, default: int = 0) -> int:
    try:
        return int(payload.get(key, default))
    except (TypeError, ValueError):
        return default


def _diagnostics_summary_text(diagnostics: dict[str, object]) -> str:
    if not diagnostics:
        return ""
    core = {
        "raw": _int_from(diagnostics, "raw_record_count"),
        "parsed": _int_from(diagnostics, "parsed_record_count"),
        "warnings": _int_from(diagnostics, "warning_count"),
        "failed": _int_from(diagnostics, "failed_record_count"),
    }
    extra = {
        key: value
        for key, value in sorted(diagnostics.items())
        if key.endswith("_count") and key not in {"raw_record_count", "parsed_record_count", "warning_count", "failed_record_count"}
    }
    parts = [f"{key}={value}" for key, value in core.items()]
    parts.extend(f"{key}={value}" for key, value in extra.items())
    return "; ".join(parts)


if QWidget is not None:
    _META_FLOW_BUTTON_STYLESHEET = """
    QPushButton#metaTargetIANavItem {
        border: 1px solid #C9D6E6;
        border-radius: 8px;
        background: #FFFFFF;
        color: #42526B;
        font-size: 12px;
        font-weight: 650;
        padding: 8px 10px;
        text-align: left;
    }
    QPushButton#metaTargetIANavItem:checked,
    QPushButton#metaTargetIANavItem[currentStep="true"] {
        border: 2px solid #2F80ED;
        background: #EAF3FF;
        color: #123E73;
        font-weight: 800;
    }
    QPushButton#metaTargetIANavItem[statusKey="planned"] {
        border-color: #E8C56D;
        background: #FFF8E6;
    }
    QPushButton#metaTargetIANavItem[currentStep="true"][statusKey="planned"] {
        border-color: #B7791F;
        background: #FFF3C4;
    }
    """

    _META_PROJECT_HOME_STYLESHEET = """
    QWidget#metaAnalysisWorkspace {
        background: #F5F7FB;
    }
    QFrame#metaMainlineHeader {
        background: #FFFFFF;
        border: 0;
        border-bottom: 1px solid #E5E7EB;
    }
    QFrame#metaProjectHomeRuntimePanel {
        background: #F5F7FB;
        border: 0;
    }
    QFrame#metaProjectHomeCard,
    QFrame#metaProjectHomeSideCard,
    QFrame#metaProjectQuestionCard,
    QFrame#metaProjectGateNotice {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
    }
    QLabel#metaProjectHomeSectionTitle {
        color: #0F172A;
        font-size: 13px;
        font-weight: 850;
    }
    QLabel#metaProjectHomeSectionSubtitle,
    QLabel#metaProjectHomeMuted,
    QLabel#metaProjectHomeFooter {
        color: #64748B;
        font-size: 11px;
    }
    QLabel#metaProjectHomeStepDone,
    QLabel#metaProjectHomeStepTodo,
    QLabel#metaProjectHomeStepCurrent {
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 8px 10px;
        color: #475569;
        font-size: 10px;
        font-weight: 750;
    }
    QLabel#metaProjectHomeStepCurrent {
        background: #EAF3FF;
        border-color: #93C5FD;
        color: #2563EB;
    }
    QLabel#metaProjectHomeStepTodo {
        background: #FFFFFF;
        color: #64748B;
    }
    QLabel#metaProjectHomeStepDone {
        background: #F0FDF4;
        border-color: #BBF7D0;
        color: #059669;
    }
    QLabel#metaProjectHomeSummaryBadge {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        color: #334155;
        font-size: 11px;
        font-weight: 800;
        padding: 4px 8px;
    }
    QLabel#metaProjectHomeSummaryBlocked {
        background: #FFF7ED;
        border: 1px solid #FED7AA;
        border-radius: 10px;
        color: #C2410C;
        font-size: 11px;
        font-weight: 850;
        padding: 4px 8px;
    }
    QLabel#metaProjectHomeSummaryTesting {
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 10px;
        color: #2563EB;
        font-size: 11px;
        font-weight: 850;
        padding: 4px 8px;
    }
    QLabel#metaProjectHomeActionIndex {
        background: #EAF3FF;
        border: 1px solid #BFDBFE;
        border-radius: 10px;
        color: #2563EB;
        font-size: 11px;
        font-weight: 900;
    }
    QPushButton#metaProjectHomeBoundaryButton {
        background: #FFFFFF;
        border: 1px solid #D8E1EC;
        border-radius: 9px;
        color: #334155;
        font-size: 12px;
        font-weight: 800;
        padding: 7px 11px;
    }
    QFrame#metaQuestionTypeDraftPanel,
    QFrame#metaTypeSelectionPanel,
    QFrame#metaQuestionQuickAccessPanel {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
    }
    QLabel#metaQuestionStepBadge {
        background: #EAF3FF;
        border: 0;
        border-radius: 4px;
        color: #2563EB;
        font-size: 12px;
        font-weight: 900;
    }
    QLabel#metaQuestionStepBadge[semantic="green"] {
        background: #E9FBEF;
        color: #059669;
    }
    QLabel#metaQuestionSectionTitle {
        background: transparent;
        border: 0;
        color: #0F172A;
        font-size: 13px;
        font-weight: 850;
    }
    QLabel#metaQuestionMuted,
    QLabel#metaQuestionTypeDescription {
        background: transparent;
        border: 0;
        color: #64748B;
        font-size: 11px;
    }
    QLabel#metaQuestionTextarea {
        background: #F8FAFC;
        border: 1px solid #D8E1EC;
        border-radius: 8px;
        color: #7B8494;
        font-size: 12px;
        padding: 10px;
    }
    QFrame#metaQuestionAISuggestionCard {
        background: #EFF8FF;
        border: 1px solid #BAE6FD;
        border-radius: 8px;
    }
    QFrame#metaQuestionTipsCard {
        background: #FFFBEB;
        border: 1px solid #FDE68A;
        border-radius: 8px;
    }
    QLabel#metaQuestionTipsText {
        background: transparent;
        border: 0;
        color: #92400E;
        font-size: 11px;
    }
    QFrame#metaActiveTypeCard {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 10px;
    }
    QFrame#metaActiveTypeCard[selected="true"] {
        border: 2px solid #60A5FA;
        background: #EFF6FF;
    }
    QFrame#metaActiveTypeCard[planned="true"] {
        border: 1px dashed #CBD5E1;
        background: #F8FAFC;
    }
    QLabel#metaMetaTypeCategoryLabel {
        background: #F1F5F9;
        border-radius: 4px;
        color: #334155;
        font-size: 11px;
        font-weight: 850;
        padding: 4px 8px;
    }
    QLabel#metaActiveTypeId {
        background: transparent;
        border: 0;
        padding: 0;
        color: #94A3B8;
        font-size: 9px;
        font-family: Menlo;
    }
    QLabel#metaActiveTypeLabel {
        background: transparent;
        border: 0;
        padding: 0;
        color: #0F172A;
        font-size: 12px;
        font-weight: 850;
    }
    QLabel#metaActiveTypeEffect {
        background: transparent;
        border: 0;
        padding: 0;
        color: #64748B;
        font-size: 11px;
    }
    QPushButton#metaActiveTypeSelectButton {
        background: #FFFFFF;
        border: 2px solid #D1D5DB;
        border-radius: 10px;
        color: transparent;
        max-width: 20px;
        min-width: 20px;
        max-height: 20px;
        min-height: 20px;
    }
    QPushButton#metaActiveTypeSelectButton:checked {
        background: #2563EB;
        border-color: #2563EB;
    }
    QPushButton#metaQuestionNextSearchStrategyButton {
        background: #2563EB;
        border: 1px solid #2563EB;
        border-radius: 9px;
        color: #FFFFFF;
        font-size: 12px;
        font-weight: 850;
        padding: 7px 11px;
    }
    """

    def _compact_flow_label(label: str) -> str:
        parts = [part.strip() for part in label.split("/", 1)]
        compact = "\n".join(parts) if len(parts) == 2 else label
        return compact.replace("&", "&&")

    def _meta_flow_button_text(page: MetaTargetIAPage) -> str:
        status = page.status_key.replace("_", " ")
        return f"{page.flow_index:02d}\n{_compact_flow_label(page.label)}\n{status}"

    def _refresh_dynamic_style(widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def _apply_meta_page_icon(button: QPushButton, semantic_key: str, *, size: int) -> None:
        icon = load_meta_page_icon(semantic_key)
        if not icon.isNull():
            button.setIcon(icon)
            button.setIconSize(QSize(size, size))
        button.setProperty("iconSource", str(META_PAGE_ICON_PATHS.get(semantic_key, "")))
        button.setProperty("iconFallback", icon.isNull())

    def _readonly_table(object_name: str, headers: tuple[str, ...], rows: tuple[tuple[str, ...], ...]) -> QTableWidget:
        table = QTableWidget(len(rows), len(headers))
        table.setObjectName(object_name)
        table.setProperty("uiPrimitive", "meta_runtime_table")
        table.setProperty("readOnly", True)
        table.setProperty("horizontalOverflow", True)
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.horizontalHeader().setMinimumSectionSize(96)
        table.setAlternatingRowColors(True)
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                item = QTableWidgetItem(value)
                table.setItem(row_index, column_index, item)
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        return table

    class MetaAnalysisWorkspaceWidget(QWidget):
        def __init__(self, on_back: Callable[[], None] | None = None) -> None:
            super().__init__()
            self.setObjectName("metaAnalysisWorkspace")
            self.setStyleSheet(_META_PROJECT_HOME_STYLESHEET)
            self._on_back = on_back
            self._current_project_dir: Path | None = None
            self._current_meta_project: MetaProjectSummary | None = None
            self._layout_state = meta_workspace_layout_state()
            self._current_target_page_key = "project_home"
            self._selected_active_meta_type_id = meta_active_types_v1()[0].type_id
            self._target_ia_buttons: dict[str, QPushButton] = {}
            self._active_type_buttons: dict[str, QPushButton] = {}
            self._page_keys: list[str] = []
            self._build_ui()

        def page_keys(self) -> tuple[str, ...]:
            return tuple(self._page_keys)

        def current_page_key(self) -> str:
            row = self._navigation_list.currentRow()
            if row < 0 or row >= len(self._page_keys):
                return ""
            return self._page_keys[row]

        def current_target_page_key(self) -> str:
            return self._current_target_page_key

        def selected_active_meta_type_id(self) -> str:
            return self._selected_active_meta_type_id

        def network_meta_enabled(self) -> bool:
            return False

        def current_project_dir(self) -> Path | None:
            return self._current_project_dir

        def set_project_record(self, record) -> None:
            self.set_project_dir(Path(record.project_dir))

        def set_project_dir(self, path: str | Path | None) -> None:
            self._current_project_dir = Path(path).expanduser().resolve() if path else None
            self._current_meta_project = None
            if self._current_project_dir is not None:
                validation = open_meta_analysis_project(self._current_project_dir)
                if validation.is_valid and validation.summary is not None:
                    self._current_meta_project = validation.summary
            self._refresh_summary()

        def open_meta_project_folder(self, path: str | Path) -> bool:
            validation = open_meta_analysis_project(path)
            if not validation.is_valid or validation.summary is None:
                self._status_label.setText("；".join(validation.errors) or "该文件夹不是有效 Meta 项目。")
                return False
            self._current_project_dir = validation.summary.project_root
            self._current_meta_project = validation.summary
            self._refresh_summary()
            return True

        def set_new_project_form(self, *, project_name: str = "", research_topic: str = "", save_location: str | Path | None = None) -> None:
            self._pending_project_name = project_name
            self._pending_research_topic = research_topic
            self._pending_save_location = str(save_location or "")

        def create_meta_project_from_form(self, *, allow_existing_nonempty: bool = False) -> MetaProjectSummary | None:
            project_name = getattr(self, "_pending_project_name", "").strip()
            save_location = getattr(self, "_pending_save_location", "").strip()
            research_topic = getattr(self, "_pending_research_topic", "").strip()
            if not project_name or not save_location:
                self._set_status("请先填写项目名称和保存位置。")
                return None
            try:
                summary = create_meta_analysis_project(
                    project_name,
                    save_location,
                    research_topic=research_topic,
                    allow_existing_nonempty=allow_existing_nonempty,
                )
            except Exception as exc:
                self._set_status(f"创建 Meta 项目失败：{exc}")
                return None
            self._current_project_dir = summary.project_root
            self._current_meta_project = summary
            self._refresh_summary()
            self._set_status(f"Meta 项目已创建：{summary.project_root}")
            return summary

        def show_step(self, page_key: str) -> None:
            if page_key in self._page_keys:
                self._navigation_list.setCurrentRow(self._page_keys.index(page_key))

        def show_target_ia_page(self, page_key: str) -> None:
            if page_key not in {page.key for page in meta_target_ia_pages()}:
                raise KeyError(f"Unknown Meta Analysis target IA page: {page_key}")
            self._current_target_page_key = page_key
            self._sync_target_interaction_state()

        def select_active_meta_type(self, type_id: str) -> None:
            if type_id not in {meta_type.type_id for meta_type in meta_active_types_v1()}:
                return
            self._selected_active_meta_type_id = type_id
            self._sync_type_interaction_state()

        def _set_status(self, text: str) -> None:
            if hasattr(self, "_status_label"):
                self._status_label.setText(text)

        def _write_gate_artifact(self, relative_path: str, payload: dict[str, object]) -> Path | None:
            if self._current_project_dir is None:
                self._set_status("未绑定 Meta 项目；该动作保持 gated。")
                return None
            path = self._current_project_dir / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self._set_status(f"已生成 gate artifact：{path.relative_to(self._current_project_dir)}")
            return path

        def _ensure_protocol_draft(self) -> Path | None:
            if self._current_project_dir is None:
                self._set_status("未绑定 Meta 项目；不能写入研究问题草稿。")
                return None
            question = "甲状腺癌患者中 adiponectin 表达或水平是否与预后或临床病理特征相关？"
            draft = PICOWorkspaceService().generate_draft(
                self._current_project_dir,
                question,
                pico_mode="auto",
                project_id=self._current_project_dir.name,
            )
            self._write_gate_artifact(
                "ui_runtime/meta_question_type_gate.json",
                {
                    "page_key": "question_meta_type",
                    "service": "PICOWorkspaceService.generate_draft",
                    "artifact": str(PICOWorkspaceService().draft_path(self._current_project_dir).relative_to(self._current_project_dir)),
                    "selected_meta_type": self._selected_active_meta_type_id,
                    "draft_id": getattr(draft, "draft_id", getattr(draft, "protocol_id", "pico_workspace_draft")),
                    "formal_action_enabled": False,
                },
            )
            return PICOWorkspaceService().draft_path(self._current_project_dir)

        def _save_search_draft_or_reason(self) -> Path | None:
            if self._current_project_dir is None:
                self._set_status("未绑定 Meta 项目；检索草稿保存保持 gated。")
                return None
            confirmed = PICOWorkspaceService().load_confirmed(self._current_project_dir)
            if confirmed is None:
                return self._write_gate_artifact(
                    "ui_runtime/meta_search_strategy_disabled_reason.json",
                    {
                        "page_key": "search_strategy",
                        "disabled_reason": "需要先确认 protocol；当前只允许复制 mock query。",
                        "service_checked": "PICOWorkspaceService.load_confirmed",
                        "formal_action_enabled": False,
                    },
                )
            SearchStrategyBuilderService().generate_from_confirmed_protocol(self._current_project_dir, actor="uishell_runtime")
            return self._write_gate_artifact(
                "ui_runtime/meta_search_strategy_gate.json",
                {
                    "page_key": "search_strategy",
                    "service": "SearchStrategyBuilderService.generate_from_confirmed_protocol",
                    "artifact": str(SearchStrategyBuilderService().draft_set_path(self._current_project_dir).relative_to(self._current_project_dir)),
                    "formal_action_enabled": False,
                },
            )

        def _copy_search_query(self) -> None:
            query = (
                '("thyroid cancer"[Title/Abstract] OR "thyroid carcinoma"[Title/Abstract]) '
                'AND ("adiponectin"[Title/Abstract] OR "ADIPOQ"[Title/Abstract])'
            )
            clipboard = QApplication.clipboard() if QApplication is not None else None
            if clipboard is not None:
                clipboard.setText(query)
            self._write_gate_artifact(
                "ui_runtime/meta_search_query_copy_manifest.json",
                {
                    "page_key": "search_strategy",
                    "service": "QApplication.clipboard",
                    "copied_query": query,
                    "formal_action_enabled": False,
                },
            )

        def _save_screening_draft_artifact(self) -> Path | None:
            service_state = "no_project_bound"
            if self._current_project_dir is not None:
                try:
                    TitleAbstractScreeningV2Service().build_queue(self._current_project_dir, project_id=self._current_project_dir.name)
                    service_state = "called_TitleAbstractScreeningV2Service.build_queue"
                except Exception as exc:
                    service_state = f"screening_queue_gate_blocked:{exc}"
            return self._write_gate_artifact(
                "ui_runtime/meta_screening_draft_decision_gate.json",
                {
                    "page_key": "screening",
                    "service_state": service_state,
                    "decision_state": "draft_only",
                    "formal_action_enabled": False,
                },
            )

        def _save_extraction_design_gate(self) -> Path | None:
            schemas = ExtractionSchemaRegistryV1Service().default_schemas()
            return self._write_gate_artifact(
                "ui_runtime/meta_extraction_design_gate.json",
                {
                    "page_key": "fulltext_extraction",
                    "service": "ExtractionSchemaRegistryV1Service.default_schemas",
                    "schema_count": len(schemas),
                    "selected_meta_type": self._selected_active_meta_type_id,
                    "formal_action_enabled": False,
                },
            )

        def _write_rob_disabled_reason(self) -> Path | None:
            return self._write_gate_artifact(
                "ui_runtime/meta_risk_of_bias_disabled_reason.json",
                {
                    "page_key": "quality_assessment",
                    "disabled_reason": "质量评价保存需要 reviewer-confirmed RoB store；当前仅预览 draft domains。",
                    "formal_action_enabled": False,
                },
            )

        def _write_report_gate_reason(self) -> Path | None:
            return self._write_gate_artifact(
                "ui_runtime/meta_report_export_disabled_reason.json",
                {
                    "page_key": self._current_target_page_key,
                    "disabled_reason": "缺少 formal pooled result、reviewer acceptance 和 report-ready package；导出保持关闭。",
                    "formal_action_enabled": False,
                    "file_write_allowed": False,
                },
            )

        def _wire_runtime_button_contracts(self) -> None:
            for button in self.findChildren(QPushButton):
                if button.property("formalActionEnabled") is None:
                    button.setProperty("formalActionEnabled", False)
                if not button.isEnabled() and button.property("disabledReason") is None:
                    button.setProperty("disabledReason", "功能门控未通过；当前仅显示 UIShell gated runtime。")
                if button.property("buttonBehavior") is None:
                    button.setProperty("buttonBehavior", "meta_uishell_gated_runtime_button")

            self._set_button_contract("metaProjectHomeBoundaryButton", "disabled_boundary_explanation", disabled_reason="边界说明仅作为 gate 文案，不执行功能。")
            self._set_button_contract("metaQuestionNextSearchStrategyButton", "navigates_to_search_strategy")
            self._set_button_contract("metaCopyQueryButton", "copies_search_query_draft_to_clipboard", on_click=self._copy_search_query)
            self._set_button_contract(
                "metaSaveSearchDraftButton",
                "calls_search_strategy_builder_or_writes_disabled_reason",
                on_click=self._save_search_draft_or_reason,
                enable=True,
            )
            self._set_button_contract(
                "metaSaveDraftScreeningDecisionButton",
                "calls_screening_store_or_writes_draft_gate_artifact",
                on_click=self._save_screening_draft_artifact,
            )
            self._set_button_contract(
                "metaScreeningSaveNextButton",
                "calls_screening_store_or_writes_draft_gate_artifact",
                on_click=self._save_screening_draft_artifact,
            )
            self._set_button_contract(
                "metaSaveExtractionDesignButton",
                "calls_extraction_schema_registry_and_writes_gate_artifact",
                on_click=self._save_extraction_design_gate,
                enable=True,
            )
            self._set_button_contract(
                "metaConfirmExtractionButton",
                "calls_extraction_schema_registry_and_writes_gate_artifact",
                on_click=self._save_extraction_design_gate,
                enable=True,
            )
            self._set_button_contract(
                "metaTargetBoundaryDisabledAction",
                "writes_disabled_reason_if_project_bound",
                on_click=self._write_report_gate_reason,
                disabled_reason="正式执行仍被 gate 阻断。",
            )
            self._set_button_contract(
                "metaGenerateReportDisabledButton",
                "writes_report_ready_disabled_reason",
                on_click=self._write_report_gate_reason,
                disabled_reason="缺少正式统计结果与 report-ready package。",
            )
            self._set_button_contract(
                "metaSaveRiskOfBiasDraftButton",
                "writes_risk_of_bias_disabled_reason",
                on_click=self._write_rob_disabled_reason,
                enable=True,
            )

            for button in self.findChildren(QPushButton, "metaActiveTypeSelectButton"):
                button.setProperty("buttonBehavior", "selects_active_meta_type_and_updates_schema_shell_state")
                button.setProperty("artifactSemantic", "in_memory_schema_shell_state")
                button.clicked.connect(lambda _checked=False: self._ensure_protocol_draft())
            for button in self.findChildren(QPushButton, "metaDatabaseDraftScopeButton"):
                button.setProperty("buttonBehavior", "sets_database_draft_scope_without_execution")
                button.setProperty("artifactSemantic", "draft_scope_only")
            for button in self.findChildren(QPushButton):
                if button.text().startswith("Import - adapter needed"):
                    button.setProperty("buttonBehavior", "disabled_import_adapter_needed")
                    button.setProperty("disabledReason", "导入 adapter 接线未完成；不能伪装真实导入。")
                elif button.text() in {"Auto merge disabled", "Auto delete disabled", "Send to screening disabled"}:
                    button.setProperty("buttonBehavior", "disabled_dedup_mutation_gate")
                    button.setProperty("disabledReason", "去重写入需要 reviewer-confirmed store；当前只显示 preview。")
                elif button.text().startswith("DOCX") or button.text().startswith("HTML") or button.text().startswith("PDF"):
                    button.setProperty("buttonBehavior", "disabled_export_gate")
                    button.setProperty("disabledReason", "报告导出需要 report-ready gate 通过。")
                elif button.text().startswith("CSV") or button.text().startswith("XLSX") or button.text().startswith("ZIP"):
                    button.setProperty("buttonBehavior", "disabled_export_gate")
                    button.setProperty("disabledReason", "报告导出需要 report-ready gate 通过。")

        def _set_button_contract(
            self,
            object_name: str,
            behavior: str,
            *,
            on_click: Callable[[], object] | None = None,
            enable: bool | None = None,
            disabled_reason: str | None = None,
        ) -> None:
            for button in self.findChildren(QPushButton, object_name):
                button.setProperty("buttonBehavior", behavior)
                button.setProperty("formalActionEnabled", False)
                if disabled_reason is not None:
                    button.setProperty("disabledReason", disabled_reason)
                if enable is not None:
                    button.setEnabled(enable)
                    if enable:
                        button.setProperty("disabledReason", None)
                if on_click is not None:
                    button.clicked.connect(lambda _checked=False, callback=on_click: callback())

        def meta_workspace_layout_state(self) -> dict[str, object]:
            return {
                "workflow_nav": self._navigation_list.objectName(),
                "current_step_workspace": self._page_stack.objectName(),
                "page_keys": self.page_keys(),
                "current_page_key": self.current_page_key(),
                "current_target_page_key": self.current_target_page_key(),
                "selected_active_meta_type_id": self.selected_active_meta_type_id(),
                "network_meta_enabled": self.network_meta_enabled(),
                "project_dir": str(self._current_project_dir or ""),
                "contract_version": META_ANALYSIS_MAINLINE_CONTRACT_VERSION,
            }

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(18, 18, 18, 18)
            root.setSpacing(12)

            header = QFrame()
            header.setObjectName("metaMainlineHeader")
            header_layout = QHBoxLayout(header)
            title_col = QVBoxLayout()
            title = QLabel("Meta 分析 / Meta Analysis")
            title.setObjectName("metaWorkspaceTitle")
            title.setStyleSheet("font-size: 22px; font-weight: 700;")
            subtitle = QLabel("系统综述与 Meta 分析流程管理，当前为 Developer Preview（本地测试版）。")
            subtitle.setObjectName("metaWorkspaceSubtitle")
            self._workspace_title_label = title
            self._workspace_subtitle_label = subtitle
            title_col.addWidget(title)
            title_col.addWidget(subtitle)
            header_layout.addLayout(title_col, 1)
            if self._on_back is not None:
                back = QPushButton("返回模块首页")
                back.setObjectName("metaBackButton")
                back.clicked.connect(self._on_back)
                header_layout.addWidget(back)
            root.addWidget(header)
            root.addWidget(self._build_target_ia_shell(), 1)

            self._status_label = QLabel("")
            self._status_label.setObjectName("metaProjectStatus")
            self._status_label.setVisible(False)
            root.addWidget(self._status_label)

            body = QHBoxLayout()
            self._navigation_list = QListWidget()
            self._navigation_list.setObjectName("metaWorkflowStepList")
            self._navigation_list.setMaximumWidth(260)
            self._page_stack = QStackedWidget()
            self._page_stack.setObjectName("metaCurrentStepWorkspace")
            self._navigation_list.setMaximumHeight(150)
            self._page_stack.setMaximumHeight(150)
            self._navigation_list.setVisible(False)
            self._page_stack.setVisible(False)
            body.addWidget(self._navigation_list)
            body.addWidget(self._page_stack, 1)
            root.addLayout(body, 0)

            self._navigation_list.currentRowChanged.connect(self._page_stack.setCurrentIndex)
            self._build_pages()
            self._refresh_summary()
            self._wire_runtime_button_contracts()

        def target_ia_page_keys(self) -> tuple[str, ...]:
            return tuple(page.key for page in meta_target_ia_pages())

        def active_meta_type_ids(self) -> tuple[str, ...]:
            return tuple(meta_type.type_id for meta_type in meta_active_types_v1())

        def _build_target_ia_shell(self) -> QFrame:
            preview = make_status_chip("Developer Preview / 本地测试版", status_key="developer_preview")
            preview.setObjectName("metaDeveloperPreviewChip")

            nav_frame = make_workflow_stepper(
                [
                    WorkflowStep(
                        key=page.key,
                        label=_compact_flow_label(page.label),
                        status_key=page.status_key,
                        semantic_state=page.status_key,
                        enabled=True,
                        current=page.key == self._current_target_page_key,
                        description=page.boundary,
                    )
                    for page in meta_target_ia_pages()
                ],
                object_name="metaWorkflowNavigationPanel",
                title="Workflow / 流程导航",
                on_step_requested=self.show_target_ia_page,
            )
            nav_frame.setProperty("uiPrimitive", "workflow_stepper")
            nav_frame.setProperty("orientation", "vertical")
            nav_frame.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
            nav_frame.setProperty("layoutPolishNoOverlap", True)
            nav_frame.setMinimumWidth(280)
            nav_frame.setMaximumWidth(320)
            nav_title = nav_frame.findChild(QLabel, "workbenchSecondaryNavTitle")
            if nav_title is None:
                nav_title = nav_frame.findChild(QLabel, "uiSectionTitle")
            if nav_title is not None:
                nav_title.setObjectName("metaWorkflowNavigationTitle")
            nav_buttons = nav_frame.findChildren(QPushButton, "workflowStepperButton")
            for page, item in zip(meta_target_ia_pages(), nav_buttons, strict=False):
                item.setObjectName("metaTargetIANavItem")
                item.setText(_meta_flow_button_text(page))
                item.setCheckable(True)
                item.setMinimumHeight(74)
                item.setMinimumSize(0, 74)
                item.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                item.setProperty("pageKey", page.key)
                item.setProperty("semanticKey", _META_PAGE_SEMANTIC_KEYS[page.key])
                item.setProperty("pageGroup", page.page_group)
                item.setProperty("flowIndex", page.flow_index)
                item.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
                item.setProperty("statusSemanticKey", _META_STATUS_SEMANTIC_KEYS[page.status_key])
                item.setProperty("interactionMode", "select_only")
                item.setProperty("buttonBehavior", f"navigates_to_meta_target_ia_page_{page.key}")
                item.setProperty("formalActionEnabled", False)
                item.setProperty("fileWriteAllowed", False)
                item.setStyleSheet(_META_FLOW_BUTTON_STYLESHEET)
                _apply_meta_page_icon(item, _META_PAGE_SEMANTIC_KEYS[page.key], size=22)
                self._target_ia_buttons[page.key] = item
            nav_frame.setVisible(False)

            runtime_main = make_card(object_name="metaRuntimeContentPanel")
            runtime_main.setObjectName("metaRuntimeContentPanel")
            runtime_main.setProperty("uiPrimitive", "workbench_content_panel")
            runtime_main.setProperty("layoutPolishNoOverlap", True)
            runtime_main_layout = QVBoxLayout(runtime_main)
            runtime_main_layout.setContentsMargins(12, 12, 12, 12)
            runtime_main_layout.setSpacing(10)

            self._target_interaction_status = QLabel("")
            self._target_interaction_status.setObjectName("metaTargetInteractionStatus")
            self._target_interaction_status.setWordWrap(True)
            self._target_interaction_status.setStyleSheet("font-weight: 650; color: #334155;")
            runtime_main_layout.addWidget(self._target_interaction_status)

            self._target_runtime_stack = QStackedWidget()
            self._target_runtime_stack.setObjectName("metaTargetRuntimeStack")
            self._target_runtime_stack.setProperty("layoutPolishNoOverlap", True)
            self._target_runtime_page_indices: dict[str, int] = {}
            runtime_main_layout.addWidget(self._target_runtime_stack, 1)

            self._result_export_panel = make_result_report_export_adoption_panel(module="meta_analysis")
            self._result_export_panel.setObjectName("resultReportExportAdoptionPanel")
            self._result_export_panel.setMinimumWidth(300)
            self._result_export_panel.setMaximumWidth(360)
            self._result_export_panel.setProperty("uiPrimitive", "workbench_right_gate_panel")

            frame = make_workbench_shell(
                title="Meta Analysis / Meta 分析目标 IA shell",
                subtitle="定义研究问题，选择适合的 Meta 分析类型，并按流程进入检索、筛选、全文管理、质量评价与报告草稿。",
                object_name="metaTargetIAShell",
                module_key=ModuleKey.META_ANALYSIS.value,
                page_key="meta_target_ia",
                status_widgets=[preview],
                secondary_nav=nav_frame,
                main_content=runtime_main,
                right_panel=self._result_export_panel,
            )
            title = frame.findChild(QLabel, "workbenchPageTitle")
            if title is not None:
                title.setObjectName("metaTargetIATitle")
            boundary = frame.findChild(QLabel, "workbenchPageSubtitle")
            if boundary is not None:
                boundary.setObjectName("metaTargetIABoundary")
            shell_header = frame.findChild(QFrame, "workbenchHeader")
            if shell_header is not None:
                shell_header.setVisible(False)

            self._project_home_panel = self._build_project_home_runtime_panel()
            self._add_target_runtime_page("project_home", self._project_home_panel)

            self._fulltext_extraction_panel = self._build_fulltext_extraction_panel()
            self._add_target_runtime_page("fulltext_extraction", self._fulltext_extraction_panel)

            self._risk_of_bias_panel = self._build_risk_of_bias_panel()
            self._add_target_runtime_page("quality_assessment", self._risk_of_bias_panel)

            self._active_type_section = QFrame()
            self._active_type_section.setObjectName("metaActiveTypeSection")
            self._active_type_section.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
            self._active_type_section.setProperty("pageKey", "question_meta_type")
            self._active_type_section.setProperty("runtimeStatus", "testing")
            self._active_type_section.setProperty("processingMode", "english_first")
            self._active_type_section.setProperty("aiBoundary", "advisory_only")
            self._active_type_section.setProperty("networkMetaState", "planned_disabled")
            self._active_type_section.setProperty("resultSemanticKey", "no_formal_result")
            self._active_type_section.setProperty("reportStatusKey", "report.status.draft")
            self._active_type_section.setProperty("exportGate", "disabled_empty_result")
            self._active_type_section.setProperty("formalActionEnabled", False)
            self._active_type_section.setStyleSheet(
                """
                QFrame#metaActiveTypeSection QLabel {
                    background: transparent;
                    border: 0;
                    padding: 0;
                }
                QFrame#metaActiveTypeSection QLabel#metaQuestionStepBadge {
                    background: #EAF3FF;
                    border-radius: 4px;
                    color: #2563EB;
                    font-weight: 900;
                }
                QFrame#metaActiveTypeSection QLabel#metaQuestionStepBadge[semantic="green"] {
                    background: #E9FBEF;
                    color: #059669;
                }
                QFrame#metaActiveTypeSection QLabel#metaQuestionTextarea {
                    background: #F8FAFC;
                    border: 1px solid #D8E1EC;
                    border-radius: 8px;
                    color: #7B8494;
                    padding: 10px;
                }
                QFrame#metaActiveTypeSection QLabel#metaMetaTypeCategoryLabel,
                QFrame#metaActiveTypeSection QLabel#metaProjectHomeSummaryTesting,
                QFrame#metaActiveTypeSection QLabel#metaProjectHomeSummaryBadge {
                    background: #F1F5F9;
                    border: 1px solid #E2E8F0;
                    border-radius: 8px;
                    padding: 4px 8px;
                }
                """
            )
            active_type_layout = QVBoxLayout(self._active_type_section)
            active_type_layout.setContentsMargins(0, 0, 0, 0)
            active_type_layout.setSpacing(12)

            self._active_type_status = QLabel("")
            self._active_type_status.setObjectName("metaActiveTypeInteractionStatus")
            self._active_type_status.setWordWrap(True)
            self._active_type_status.setObjectName("metaActiveTypeInteractionStatus")

            visual_row = QHBoxLayout()
            visual_row.setContentsMargins(0, 0, 0, 0)
            visual_row.setSpacing(14)
            visual_row.addWidget(self._build_question_type_draft_panel(), 0, Qt.AlignTop)
            visual_row.addWidget(self._build_meta_type_selection_panel(), 1)
            active_type_layout.addLayout(visual_row, 1)
            active_type_layout.addWidget(self._build_question_type_quick_access_panel())
            self._add_target_runtime_page("question_meta_type", self._active_type_section)

            self._search_strategy_panel = self._build_search_strategy_panel()
            self._add_target_runtime_page("search_strategy", self._search_strategy_panel)

            self._reference_dedup_panel = self._build_reference_dedup_panel()
            self._add_target_runtime_page("import_dedup", self._reference_dedup_panel)

            self._screening_panel = self._build_screening_panel()
            self._add_target_runtime_page("screening", self._screening_panel)

            self._result_review_panel = self._build_result_review_panel()
            self._add_target_runtime_page("result_report", self._result_review_panel)

            self._report_export_gate_panel = self._build_report_export_gate_panel()
            self._add_target_runtime_page("report_export", self._report_export_gate_panel)

            self._analysis_tasks_panel = self._build_target_boundary_panel(
                page_key="analysis_tasks",
                title="Meta Analysis Tasks / 统计分析",
                status_key="planned",
                rows=(
                    "Pairwise Meta executor is not enabled in this runtime shell.",
                    "Network Meta remains planned / disabled.",
                    "No formal statistical output, figure output, report, or export is generated.",
                ),
            )
            self._add_target_runtime_page("analysis_tasks", self._analysis_tasks_panel)

            self._meta_settings_panel = self._build_target_boundary_panel(
                page_key="meta_settings",
                title="Meta Settings / Meta 设置",
                status_key="shell_only",
                rows=(
                    "Meta preferences, logs, and external resource checks remain shell-only.",
                    "No executor, retrieval adapter, report adapter, or export adapter is enabled from this page.",
                ),
            )
            self._add_target_runtime_page("meta_settings", self._meta_settings_panel)

            self._sync_target_interaction_state()
            self._sync_type_interaction_state()
            return frame

        def _add_target_runtime_page(self, page_key: str, widget: QWidget) -> None:
            scroll = QScrollArea()
            scroll.setObjectName(f"metaRuntimeScrollArea_{page_key}")
            scroll.setWidgetResizable(True)
            scroll.setProperty("pageKey", page_key)
            scroll.setProperty("layoutPolishNoOverlap", True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            scroll.setWidget(widget)
            self._target_runtime_page_indices[page_key] = self._target_runtime_stack.addWidget(scroll)

        def _build_target_boundary_panel(self, *, page_key: str, title: str, rows: tuple[str, ...], status_key: str) -> QFrame:
            frame = QFrame()
            frame.setObjectName("metaTargetBoundaryRuntimePanel")
            frame.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
            frame.setProperty("pageKey", page_key)
            frame.setProperty("runtimeStatus", status_key)
            frame.setProperty("resultSemanticKey", "no_formal_result")
            frame.setProperty("reportStatusKey", "report.status.draft")
            frame.setProperty("exportGate", "disabled_empty_result")
            frame.setProperty("formalActionEnabled", False)
            frame.setStyleSheet("QFrame#metaTargetBoundaryRuntimePanel { border: 1px solid #D6E0EA; border-radius: 8px; background: #FFFFFF; }")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(10)
            heading = QLabel(title)
            heading.setObjectName("metaTargetBoundaryRuntimeTitle")
            heading.setStyleSheet("font-weight: 750;")
            layout.addWidget(heading)
            layout.addWidget(make_status_chip(status_key=status_key))
            for row in rows:
                label = QLabel(row)
                label.setObjectName("metaTargetBoundaryRuntimeRow")
                label.setWordWrap(True)
                layout.addWidget(label)
            disabled = QPushButton("Formal action disabled")
            disabled.setObjectName("metaTargetBoundaryDisabledAction")
            disabled.setProperty("formalActionEnabled", False)
            disabled.setProperty("actionSemantic", "disabled_boundary")
            disabled.setEnabled(False)
            layout.addWidget(disabled)
            layout.addStretch(1)
            return frame

        def _build_project_home_runtime_panel(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("metaProjectHomeRuntimePanel")
            frame.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
            frame.setProperty("pageKey", "project_home")
            frame.setProperty("runtimeStatus", "shell_only")
            frame.setProperty("processingMode", "english_first")
            frame.setProperty("aiBoundary", "advisory_only")
            frame.setProperty("resultSemanticKey", "no_formal_result")
            frame.setProperty("reportStatusKey", "report.status.draft")
            frame.setProperty("exportGate", "disabled_empty_result")
            frame.setProperty("formalActionEnabled", False)
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(12)

            body = QHBoxLayout()
            body.setContentsMargins(0, 0, 0, 0)
            body.setSpacing(12)
            main_col = QVBoxLayout()
            main_col.setSpacing(12)
            main_col.addWidget(self._build_project_home_status_chips())
            main_col.addWidget(self._build_project_home_workflow_card())
            main_col.addWidget(self._build_project_home_question_card())
            body.addLayout(main_col, 1)

            side_col = QVBoxLayout()
            side_col.setSpacing(12)
            side_col.addWidget(self._build_project_home_summary_card())
            side_col.addWidget(self._build_project_home_next_actions_card())
            side_col.addStretch(1)
            side_wrap = QWidget()
            side_wrap.setMinimumWidth(268)
            side_wrap.setMaximumWidth(300)
            side_wrap.setLayout(side_col)
            body.addWidget(side_wrap)
            layout.addLayout(body)
            layout.addWidget(self._build_project_home_gate_notice())

            hidden_contract = QWidget()
            hidden_contract.setVisible(False)
            hidden_layout = QVBoxLayout(hidden_contract)
            hidden_layout.setContentsMargins(0, 0, 0, 0)
            workflow_rows = tuple(
                (
                    f"{page.flow_index:02d}" if page.page_group == "main_flow" else "AUX",
                    page.label,
                    page.status_key,
                    page.boundary,
                )
                for page in meta_target_ia_pages()
            )
            workflow = _readonly_table(
                "metaProjectHomeWorkflowOverview",
                ("Step", "Page", "Status", "Gate / boundary"),
                workflow_rows,
            )
            workflow.setMinimumHeight(190)
            hidden_layout.addWidget(workflow)

            summary = _readonly_table(
                "metaProjectHomeSummaryTable",
                ("Area", "Current state", "Gate"),
                (
                    ("References", "0 imported", "import required"),
                    ("Screening", "not started", "draft only"),
                    ("Extraction", "not started", "manual review required"),
                    ("Risk of bias", "incomplete", "reviewer controlled"),
                    ("Formal pooled result", "none", "executor not enabled"),
                    ("Report-ready", "blocked", "draft workflow only"),
                    ("Export", "disabled", "formal result missing"),
                ),
            )
            summary.setMinimumHeight(170)
            hidden_layout.addWidget(summary)
            layout.addWidget(hidden_contract)
            return frame

        def _build_project_home_status_chips(self) -> QWidget:
            wrap = QWidget()
            wrap.setFixedHeight(30)
            chip_row = QHBoxLayout(wrap)
            chip_row.setContentsMargins(0, 0, 0, 0)
            chip_row.setSpacing(8)
            for object_name, text, semantic in (
                ("metaProjectHomeDeveloperPreviewChip", "Developer Preview / 本地测试版", "testing"),
                ("metaProjectHomeEnglishFirstChip", "English-first processing", "testing"),
                ("metaProjectHomeAISuggestionChip", "AI suggestion only", "testing"),
                ("metaProjectHomeReportNotReadyChip", "Report not ready", "blocked"),
            ):
                chip = QLabel(text)
                chip.setObjectName(object_name)
                chip.setProperty("statusKey", semantic)
                chip.setStyleSheet(
                    "background: #FFF7ED; border: 1px solid #FED7AA; border-radius: 10px; color: #9A3412; "
                    "font-size: 11px; font-weight: 850; padding: 4px 8px;"
                    if semantic == "blocked"
                    else "background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 10px; color: #2563EB; "
                    "font-size: 11px; font-weight: 850; padding: 4px 8px;"
                )
                chip.setFixedHeight(24)
                chip.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
                chip_row.addWidget(chip)
            chip_row.addStretch(1)
            return wrap

        def _build_project_home_workflow_card(self) -> QFrame:
            card = QFrame()
            card.setObjectName("metaProjectHomeCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(16, 14, 16, 16)
            layout.setSpacing(12)
            header = QHBoxLayout()
            title_col = QVBoxLayout()
            title_col.setSpacing(2)
            title = QLabel("Meta 工作流程总览")
            title.setObjectName("metaProjectHomeSectionTitle")
            subtitle = QLabel("Workflow Overview · 12 步流程")
            subtitle.setObjectName("metaProjectHomeSectionSubtitle")
            title_col.addWidget(title)
            title_col.addWidget(subtitle)
            header.addLayout(title_col, 1)
            legend_current = QLabel("● 当前步骤")
            legend_current.setObjectName("metaProjectHomeMuted")
            legend_todo = QLabel("○ 待完成")
            legend_todo.setObjectName("metaProjectHomeMuted")
            header.addWidget(legend_current)
            header.addWidget(legend_todo)
            layout.addLayout(header)

            rows = (
                (
                    ("1", "项目首页", "Project Home", "current"),
                    ("2", "问题与类型", "Question & Meta Type", "todo"),
                    ("3", "检索策略", "Search Strategy", "todo"),
                    ("4", "文献导入", "Reference Management", "todo"),
                    ("5", "去重", "Deduplication", "todo"),
                    ("6", "筛选", "Screening", "todo"),
                ),
                (
                    ("7", "全文与提取", "Full-text & Extraction", "todo"),
                    ("8", "数据提取", "Extraction", "todo"),
                    ("9", "质量评价", "Risk of Bias", "todo"),
                    ("10", "统计分析", "Analysis Tasks", "todo"),
                    ("11", "结果报告", "Result & Report", "todo"),
                    ("12", "报告导出", "Report Export", "todo"),
                ),
            )
            for row_index, step_row in enumerate(rows):
                row = QHBoxLayout()
                row.setSpacing(8)
                for number, zh, en, state in step_row:
                    row.addWidget(self._project_home_step_label(number, zh, en, state), 1)
                layout.addLayout(row)
                if row_index == 0:
                    divider = QHBoxLayout()
                    left = QFrame()
                    left.setFrameShape(QFrame.HLine)
                    left.setStyleSheet("color: #E5E7EB;")
                    center = QLabel("Steps 7 - 12")
                    center.setObjectName("metaProjectHomeMuted")
                    right = QFrame()
                    right.setFrameShape(QFrame.HLine)
                    right.setStyleSheet("color: #E5E7EB;")
                    divider.addWidget(left, 1)
                    divider.addWidget(center)
                    divider.addWidget(right, 1)
                    layout.addLayout(divider)
            return card

        def _project_home_step_label(self, number: str, zh: str, en: str, state: str) -> QLabel:
            label = QLabel(f"{number}    {zh}\n{en}")
            label.setObjectName(
                "metaProjectHomeStepCurrent"
                if state == "current"
                else ("metaProjectHomeStepDone" if state == "done" else "metaProjectHomeStepTodo")
            )
            label.setWordWrap(True)
            label.setMinimumHeight(70)
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            return label

        def _build_project_home_question_card(self) -> QFrame:
            card = QFrame()
            card.setObjectName("metaProjectQuestionCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(16, 14, 16, 16)
            layout.setSpacing(12)
            title = QLabel("研究问题草稿 / Research Question Draft")
            title.setObjectName("metaProjectHomeSectionTitle")
            layout.addWidget(title)
            question_row = QHBoxLayout()
            question_row.setSpacing(10)
            for heading, body in (
                ("中文问题", "甲状腺癌患者中 adiponectin 表达或水平是否与预后或临床病理特征相关？"),
                (
                    "English Question",
                    "Is adiponectin expression or circulating adiponectin associated with prognosis or clinicopathological features in thyroid cancer patients?",
                ),
            ):
                block = QFrame()
                block.setObjectName("metaProjectHomeCard")
                block_layout = QVBoxLayout(block)
                block_layout.setContentsMargins(12, 10, 12, 10)
                heading_label = QLabel(heading)
                heading_label.setObjectName("metaProjectHomeMuted")
                body_label = QLabel(body)
                body_label.setObjectName("metaProjectHomeSectionSubtitle")
                body_label.setWordWrap(True)
                block_layout.addWidget(heading_label)
                block_layout.addWidget(body_label)
                question_row.addWidget(block, 1)
            layout.addLayout(question_row)
            suggested = QHBoxLayout()
            suggested.addWidget(QLabel("Suggested type"))
            for text in ("prognostic_factor_meta", "biomarker_expression_difference_meta"):
                badge = QLabel(text)
                badge.setObjectName("metaProjectHomeSummaryTesting")
                suggested.addWidget(badge)
            suggested.addStretch(1)
            layout.addLayout(suggested)
            notice = QLabel("本界面为非生产环境示例数据（Mockup only），不代表真实证据或分析结果。reviewer manual confirmation is required.")
            notice.setObjectName("metaProjectHomeMuted")
            notice.setWordWrap(True)
            layout.addWidget(notice)
            return card

        def _build_project_home_summary_card(self) -> QFrame:
            card = QFrame()
            card.setObjectName("metaProjectHomeSideCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(14, 14, 14, 14)
            layout.setSpacing(9)
            title = QLabel("项目摘要")
            title.setObjectName("metaProjectHomeSectionTitle")
            subtitle = QLabel("Project Summary")
            subtitle.setObjectName("metaProjectHomeSectionSubtitle")
            layout.addWidget(title)
            layout.addWidget(subtitle)
            for label, value, state in (
                ("References", "0 imported", "neutral"),
                ("Screening", "not started", "neutral"),
                ("Extraction", "not started", "neutral"),
                ("Risk of bias", "incomplete", "blocked"),
                ("Formal result", "none", "blocked"),
                ("Report-ready", "blocked", "blocked"),
                ("Export", "disabled", "blocked"),
            ):
                row = QHBoxLayout()
                name = QLabel(label)
                name.setObjectName("metaProjectHomeMuted")
                badge = QLabel(value)
                badge.setObjectName("metaProjectHomeSummaryBlocked" if state == "blocked" else "metaProjectHomeSummaryBadge")
                row.addWidget(name, 1)
                row.addWidget(badge)
                layout.addLayout(row)
            return card

        def _build_project_home_next_actions_card(self) -> QFrame:
            card = QFrame()
            card.setObjectName("metaProjectHomeSideCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(14, 14, 14, 14)
            layout.setSpacing(10)
            title = QLabel("下一步建议")
            title.setObjectName("metaProjectHomeSectionTitle")
            subtitle = QLabel("Next Actions")
            subtitle.setObjectName("metaProjectHomeSectionSubtitle")
            layout.addWidget(title)
            layout.addWidget(subtitle)
            for index, (title_text, body) in enumerate(
                (
                    ("确认研究问题与 Meta 类型", "Confirm research question and Meta type"),
                    ("生成英文检索式草稿", "Generate English search query draft"),
                    ("导入参考文献", "Import references"),
                    ("人工确认筛选规则", "Manually confirm screening criteria"),
                ),
                start=1,
            ):
                row = QHBoxLayout()
                number = QLabel(str(index))
                number.setObjectName("metaProjectHomeActionIndex")
                number.setFixedSize(22, 22)
                number.setAlignment(Qt.AlignCenter)
                text_col = QVBoxLayout()
                text_col.setSpacing(1)
                title_label = QLabel(title_text)
                title_label.setObjectName("metaProjectHomeSectionSubtitle")
                body_label = QLabel(body)
                body_label.setObjectName("metaProjectHomeMuted")
                body_label.setWordWrap(True)
                text_col.addWidget(title_label)
                text_col.addWidget(body_label)
                row.addWidget(number)
                row.addLayout(text_col, 1)
                layout.addLayout(row)
            return card

        def _build_project_home_gate_notice(self) -> QFrame:
            card = QFrame()
            card.setObjectName("metaProjectGateNotice")
            layout = QHBoxLayout(card)
            layout.setContentsMargins(16, 14, 16, 14)
            layout.setSpacing(12)
            text_col = QVBoxLayout()
            text_col.setSpacing(6)
            title = QLabel("重要提示 / Gate Notice")
            title.setObjectName("metaProjectHomeSectionTitle")
            text_col.addWidget(title)
            for text in (
                "中文输入可辅助生成英文检索式，但当前仅保留英文优先的本地草稿流程。",
                "AI suggestion 仅供参考，不能替代人工筛选、提取、偏倚风险判断或结论。",
                "当前没有正式统计结果、正式图表、report-ready package 或文件导出。",
                "网络 Meta（Network Meta）暂不启用。",
                "本界面为 Developer Preview，仅供流程设计与演示。",
            ):
                item = QLabel(f"• {text}")
                item.setObjectName("metaProjectHomeMuted")
                item.setWordWrap(True)
                text_col.addWidget(item)
            layout.addLayout(text_col, 1)
            button = QPushButton("了解边界 / View Boundaries")
            button.setObjectName("metaProjectHomeBoundaryButton")
            button.setProperty("formalActionEnabled", False)
            button.setEnabled(False)
            layout.addWidget(button, 0, Qt.AlignTop)
            return card

        def _build_question_type_draft_panel(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("metaQuestionTypeDraftPanel")
            frame.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
            frame.setProperty("pageKey", "question_meta_type")
            frame.setProperty("runtimeStatus", "testing")
            frame.setProperty("processingMode", "english_first")
            frame.setProperty("aiBoundary", "advisory_only")
            frame.setProperty("networkMetaState", "planned_disabled")
            frame.setProperty("resultSemanticKey", "no_formal_result")
            frame.setProperty("reportStatusKey", "report.status.draft")
            frame.setProperty("exportGate", "disabled_empty_result")
            frame.setProperty("formalActionEnabled", False)
            frame.setMinimumWidth(340)
            frame.setMaximumWidth(370)
            frame.setMaximumHeight(500)
            frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(16, 12, 16, 16)
            layout.setSpacing(12)

            header_wrap = QWidget()
            header_wrap.setFixedHeight(24)
            header = QHBoxLayout(header_wrap)
            header.setContentsMargins(0, 0, 0, 0)
            badge = QLabel("1")
            badge.setObjectName("metaQuestionStepBadge")
            badge.setFixedSize(20, 20)
            badge.setAlignment(Qt.AlignCenter)
            title = QLabel("研究问题 / Research Question")
            title.setObjectName("metaQuestionSectionTitle")
            header.addWidget(badge)
            header.addWidget(title)
            header.addStretch(1)
            layout.addWidget(header_wrap)

            question_label = QLabel("研究问题（中文）")
            question_label.setObjectName("metaQuestionSectionTitle")
            layout.addWidget(question_label)
            textarea = QLabel("请用中文简要描述您的研究问题，例如：\n某药物对癌症患者生存率的影响。\n\n\n\n0/500")
            textarea.setObjectName("metaQuestionTextarea")
            textarea.setMinimumHeight(128)
            textarea.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            layout.addWidget(textarea)

            ai_card = QFrame()
            ai_card.setObjectName("metaQuestionAISuggestionCard")
            ai_layout = QVBoxLayout(ai_card)
            ai_layout.setContentsMargins(12, 10, 12, 10)
            ai_layout.setSpacing(8)
            ai_header = QHBoxLayout()
            ai_title = QLabel("研究问题建议（英文）")
            ai_title.setObjectName("metaQuestionSectionTitle")
            ai_badge = QLabel("AI 建议，仅供参考")
            ai_badge.setObjectName("metaProjectHomeSummaryTesting")
            shuffle = QLabel("换一换")
            shuffle.setObjectName("metaQuestionMuted")
            ai_header.addWidget(ai_title)
            ai_header.addWidget(ai_badge)
            ai_header.addStretch(1)
            ai_header.addWidget(shuffle)
            ai_layout.addLayout(ai_header)
            ai_body = QLabel("What is the effect of [intervention/exposure] on\n[outcome] in [population]?")
            ai_body.setObjectName("metaQuestionSectionSubtitle")
            ai_body.setStyleSheet("color: #0369A1; font-size: 12px; font-style: italic;")
            ai_body.setWordWrap(True)
            ai_layout.addWidget(ai_body)
            layout.addWidget(ai_card)

            tips = QFrame()
            tips.setObjectName("metaQuestionTipsCard")
            tips_layout = QVBoxLayout(tips)
            tips_layout.setContentsMargins(12, 10, 12, 10)
            tips_layout.setSpacing(8)
            tips_title = QLabel("提示 / Tips")
            tips_title.setObjectName("metaQuestionSectionTitle")
            tips_layout.addWidget(tips_title)
            for text in (
                "请确保问题包含：研究对象、干预/暴露、结局指标。",
                "选择最符合您研究目的的 Meta 分析类型。",
                "不同类型将启用不同的统计方法与结果展示。",
            ):
                item = QLabel(f"• {text}")
                item.setObjectName("metaQuestionTipsText")
                item.setWordWrap(True)
                tips_layout.addWidget(item)
            layout.addWidget(tips)

            legacy_contract = QWidget()
            legacy_contract.setVisible(False)
            legacy_layout = QVBoxLayout(legacy_contract)
            legacy_layout.setContentsMargins(0, 0, 0, 0)

            chinese = QLabel("中文工作问题：脂联素表达与甲状腺癌预后或诊断价值之间的关系。")
            chinese.setObjectName("metaChineseWorkingQuestionDraft")
            chinese.setWordWrap(True)
            english = QLabel("English question draft: Is adiponectin associated with thyroid cancer diagnosis or prognosis in human studies?")
            english.setObjectName("metaEnglishQuestionDraft")
            english.setWordWrap(True)
            legacy_layout.addWidget(chinese)
            legacy_layout.addWidget(english)

            pico = _readonly_table(
                "metaPicoPecoDraftTable",
                ("Field", "Draft value", "State"),
                (
                    ("Population", "Adults with thyroid cancer or thyroid nodules", "draft"),
                    ("Exposure / Index", "Adiponectin expression or circulating adiponectin", "draft"),
                    ("Comparator", "Benign tissue, healthy control, low-expression group", "draft"),
                    ("Outcome", "Diagnostic accuracy, expression difference, prognosis", "draft"),
                    ("Study type", "Human observational studies", "draft"),
                ),
            )
            pico.setMinimumHeight(146)
            legacy_layout.addWidget(pico)

            suggested = QLabel("Suggested Meta type draft: Prognostic factor meta or Biomarker expression difference meta. AI suggestion is advisory only.")
            suggested.setObjectName("metaSuggestedMetaTypeDraft")
            suggested.setWordWrap(True)
            suggested.setStyleSheet("border: 1px solid #BFD7FF; border-radius: 6px; padding: 6px 8px; background: #EFF6FF;")
            legacy_layout.addWidget(suggested)

            card_grid = QGridLayout()
            card_grid.setHorizontalSpacing(8)
            card_grid.setVerticalSpacing(8)
            candidate_cards = (
                ("prognostic_factor_meta", "Prognostic factor meta", "draft choice"),
                ("biomarker_expression_difference_meta", "Biomarker expression difference meta", "draft choice"),
                ("diagnostic_accuracy_meta", "Diagnostic accuracy meta", "draft choice"),
                ("intervention_effect_meta", "Intervention effect meta", "draft choice"),
                ("adverse_event_meta", "Adverse event meta", "draft choice"),
                ("other_meta_type", "Other meta type", "draft choice"),
            )
            for index, (type_id, label, state) in enumerate(candidate_cards):
                card = QFrame()
                card.setObjectName("metaQuestionTypeCandidateCard")
                card.setProperty("typeId", type_id)
                card.setProperty("state", state)
                card.setProperty("formalActionEnabled", False)
                card.setMinimumHeight(78)
                card.setStyleSheet("QFrame#metaQuestionTypeCandidateCard { border: 1px solid #CBD5E1; border-radius: 8px; background: #F8FAFC; }")
                card_layout = QVBoxLayout(card)
                card_layout.setContentsMargins(10, 8, 10, 8)
                candidate_label = QLabel(label)
                candidate_label.setObjectName("metaQuestionTypeCandidateLabel")
                candidate_label.setWordWrap(True)
                state_label = QLabel(state)
                state_label.setObjectName("metaQuestionTypeCandidateState")
                state_label.setStyleSheet("color: #64748B;")
                card_layout.addWidget(candidate_label)
                card_layout.addWidget(state_label)
                card_grid.addWidget(card, index // 3, index % 3)
            legacy_layout.addLayout(card_grid)
            layout.addWidget(legacy_contract)
            layout.addStretch(1)
            return frame

        def _build_meta_type_selection_panel(self) -> QFrame:
            panel = QFrame()
            panel.setObjectName("metaTypeSelectionPanel")
            layout = QVBoxLayout(panel)
            layout.setContentsMargins(20, 12, 20, 16)
            layout.setSpacing(12)

            header = QHBoxLayout()
            badge = QLabel("2")
            badge.setObjectName("metaQuestionStepBadge")
            badge.setProperty("semantic", "green")
            badge.setFixedSize(20, 20)
            badge.setAlignment(Qt.AlignCenter)
            title = QLabel("Meta 类型选择 / Select Meta Type")
            title.setObjectName("metaQuestionSectionTitle")
            header.addWidget(badge)
            header.addWidget(title)
            header.addStretch(1)
            layout.addLayout(header)
            description = QLabel("请选择最符合您研究问题的 Meta 分析类型。")
            description.setObjectName("metaQuestionMuted")
            layout.addWidget(description)

            hidden_groups = QWidget()
            hidden_groups.setVisible(False)
            hidden_group_layout = QVBoxLayout(hidden_groups)
            hidden_group_layout.setContentsMargins(0, 0, 0, 0)
            for text in ("结局型 Meta", "流行病学 Meta", "诊断与关联 Meta", "关联与预后 Meta", "Testing schema"):
                label = QLabel(text)
                label.setObjectName("metaTypeGroupTitle")
                hidden_group_layout.addWidget(label)
            layout.addWidget(hidden_groups)

            self._active_type_cards: dict[str, QFrame] = {}
            active_types = {item.type_id: item for item in meta_active_types_v1()}
            groups = (
                ("疗效 / 效果类", ("binary_outcome_meta", "continuous_outcome_meta", "survival_outcome_meta")),
                ("发生率 / 诊断类", ("prevalence_incidence_meta", "diagnostic_accuracy_meta", "exposure_disease_risk_meta")),
                ("生物标志物 / 相关性类", ("biomarker_expression_difference_meta", "correlation_meta", "prognostic_factor_meta")),
                ("剂量反应类", ("dose_response_meta",)),
            )
            for label, type_ids in groups:
                section = QVBoxLayout()
                section.setSpacing(8)
                title_row = QHBoxLayout()
                group_label = QLabel(label)
                group_label.setObjectName("metaMetaTypeCategoryLabel")
                divider = QFrame()
                divider.setFrameShape(QFrame.HLine)
                divider.setStyleSheet("color: #E5E7EB;")
                title_row.addWidget(group_label)
                title_row.addWidget(divider, 1)
                section.addLayout(title_row)
                cards = QHBoxLayout()
                cards.setSpacing(10)
                for type_id in type_ids:
                    cards.addWidget(self._build_meta_type_card(active_types[type_id]), 1)
                if label == "剂量反应类":
                    cards.addWidget(self._build_network_meta_planned_card(), 1)
                    cards.addStretch(1)
                section.addLayout(cards)
                layout.addLayout(section)

            footer = QHBoxLayout()
            footer.addWidget(self._active_type_status, 1)
            next_search = QPushButton("下一步：检索策略 / Next: Search Strategy")
            next_search.setObjectName("metaQuestionNextSearchStrategyButton")
            next_search.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
            next_search.setProperty("pageKey", "question_meta_type")
            next_search.setProperty("targetPageKey", "search_strategy")
            next_search.setProperty("actionSemantic", "navigation_only")
            next_search.setProperty("formalActionEnabled", False)
            next_search.setMinimumHeight(34)
            next_search.clicked.connect(lambda _checked=False: self.show_target_ia_page("search_strategy"))
            footer.addWidget(next_search)
            layout.addLayout(footer)
            return panel

        def _build_meta_type_card(self, meta_type: MetaActiveType) -> QFrame:
            descriptions = {
                "binary_outcome_meta": "如缓解率、有效率、死亡率等",
                "continuous_outcome_meta": "如均值差、标准化均值差等",
                "survival_outcome_meta": "如 OS、PFS、HR 等",
                "prevalence_incidence_meta": "如疾病患病率、发病率等",
                "diagnostic_accuracy_meta": "如灵敏度、特异度、AUC 等",
                "exposure_disease_risk_meta": "如 OR、RR、HR 等",
                "biomarker_expression_difference_meta": "如基因、蛋白表达差异等",
                "correlation_meta": "如相关系数合并等",
                "prognostic_factor_meta": "如预后因子与结局的关联等",
                "dose_response_meta": "如剂量-反应关系、趋势分析等",
            }
            card = QFrame()
            card.setObjectName("metaActiveTypeCard")
            card.setProperty("typeId", meta_type.type_id)
            card.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
            card.setProperty("statusKey", meta_type.status_key)
            card.setProperty("semanticKey", FeatureStatusKey.TESTING.value)
            card.setMinimumHeight(154)
            card.setMinimumWidth(170)
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            layout = QVBoxLayout(card)
            layout.setContentsMargins(12, 10, 12, 10)
            layout.setSpacing(7)
            top = QHBoxLayout()
            icon = QLabel("⌁")
            icon.setObjectName("metaProjectHomeSummaryTesting")
            icon.setFixedSize(32, 32)
            icon.setAlignment(Qt.AlignCenter)
            select = QPushButton("")
            select.setObjectName("metaActiveTypeSelectButton")
            select.setCheckable(True)
            select.setProperty("typeId", meta_type.type_id)
            select.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
            select.setProperty("statusKey", meta_type.status_key)
            select.setProperty("semanticKey", FeatureStatusKey.TESTING.value)
            select.setProperty("interactionMode", meta_type.interaction_mode)
            select.setProperty("formalActionEnabled", False)
            select.clicked.connect(lambda _checked=False, type_id=meta_type.type_id: self.select_active_meta_type(type_id))
            self._active_type_buttons[meta_type.type_id] = select
            self._active_type_cards[meta_type.type_id] = card
            top.addWidget(icon)
            top.addStretch(1)
            top.addWidget(select)
            layout.addLayout(top)
            type_id = QLabel(meta_type.type_id)
            type_id.setObjectName("metaActiveTypeId")
            type_id.setWordWrap(True)
            label = QLabel(meta_type.label_zh)
            label.setObjectName("metaActiveTypeLabel")
            label.setWordWrap(True)
            effect = QLabel(descriptions.get(meta_type.type_id, meta_type.effect_size))
            effect.setObjectName("metaActiveTypeEffect")
            effect.setWordWrap(True)
            layout.addWidget(type_id)
            layout.addWidget(label)
            layout.addWidget(effect)
            layout.addStretch(1)
            return card

        def _build_network_meta_planned_card(self) -> QFrame:
            card = QFrame()
            card.setObjectName("metaActiveTypeCardPlanned")
            card.setProperty("typeId", "network_meta_analysis")
            card.setProperty("planned", True)
            card.setMinimumHeight(154)
            card.setMinimumWidth(170)
            card.setStyleSheet("QFrame#metaActiveTypeCardPlanned { border: 1px dashed #CBD5E1; border-radius: 10px; background: #F8FAFC; }")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(12, 10, 12, 10)
            top = QHBoxLayout()
            icon = QLabel("⌘")
            icon.setObjectName("metaProjectHomeSummaryBadge")
            icon.setFixedSize(32, 32)
            icon.setAlignment(Qt.AlignCenter)
            planned_button = QPushButton("计划中")
            planned_button.setObjectName("metaNetworkMetaPlannedButton")
            planned_button.setProperty("typeId", "network_meta_analysis")
            planned_button.setProperty("statusKey", "planned")
            planned_button.setProperty("interactionMode", "planned_disabled")
            planned_button.setProperty("formalActionEnabled", False)
            planned_button.setEnabled(False)
            top.addWidget(icon)
            top.addStretch(1)
            top.addWidget(planned_button)
            layout.addLayout(top)
            type_id = QLabel("network_meta")
            type_id.setObjectName("metaActiveTypeId")
            title = QLabel("网络 Meta 分析")
            title.setObjectName("metaActiveTypeLabel")
            desc = QLabel("探索干预比较的网络证据合成\n计划中 / Planned")
            desc.setObjectName("metaActiveTypeEffect")
            desc.setWordWrap(True)
            boundary = QLabel("Network Meta：planned only / not enabled，不属于当前 active Meta 类型。")
            boundary.setObjectName("metaNetworkMetaBoundary")
            boundary.setProperty("typeId", "network_meta_analysis")
            boundary.setProperty("statusKey", "planned")
            boundary.setProperty("formalActionEnabled", False)
            boundary.setVisible(False)
            layout.addWidget(type_id)
            layout.addWidget(title)
            layout.addWidget(desc)
            layout.addWidget(boundary)
            layout.addStretch(1)
            return card

        def _build_question_type_quick_access_panel(self) -> QFrame:
            panel = QFrame()
            panel.setObjectName("metaQuestionQuickAccessPanel")
            layout = QHBoxLayout(panel)
            layout.setContentsMargins(20, 13, 20, 13)
            layout.setSpacing(8)
            title = QLabel("快速入口")
            title.setObjectName("metaQuestionSectionTitle")
            layout.addWidget(title)
            layout.addStretch(1)
            for text in ("最近使用", "使用指南", "常见问题", "意见反馈"):
                button = QPushButton(text)
                button.setObjectName("metaProjectHomeBoundaryButton")
                button.setProperty("formalActionEnabled", False)
                button.setEnabled(False)
                layout.addWidget(button)
            return panel

        def _build_search_strategy_panel(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("metaSearchStrategyRuntimePanel")
            frame.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
            frame.setProperty("pageKey", "search_strategy")
            frame.setProperty("runtimeStatus", "testing")
            frame.setProperty("processingMode", "english_first")
            frame.setProperty("aiBoundary", "advisory_only")
            frame.setProperty("resultSemanticKey", "no_formal_result")
            frame.setProperty("reportStatusKey", "report.status.draft")
            frame.setProperty("exportGate", "disabled_empty_result")
            frame.setProperty("formalActionEnabled", False)
            frame.setStyleSheet(
                """
                QFrame#metaSearchStrategyRuntimePanel {
                    background: #F5F7FB;
                    border: 0;
                }
                QFrame#metaSearchCard,
                QFrame#metaSearchSideCard,
                QFrame#metaSearchStepper {
                    background: #FFFFFF;
                    border: 1px solid #E5E7EB;
                    border-radius: 12px;
                }
                QLabel#metaSearchTitle {
                    color: #0F172A;
                    font-size: 13px;
                    font-weight: 850;
                }
                QLabel#metaSearchMuted {
                    color: #64748B;
                    font-size: 11px;
                }
                QLabel#metaSearchStepDone {
                    background: transparent;
                    color: #2563EB;
                    font-size: 10px;
                    font-weight: 850;
                }
                QLabel#metaSearchStepCurrent {
                    color: #2563EB;
                    font-size: 10px;
                    font-weight: 900;
                }
                QLabel#metaSearchTermGroup {
                    border-radius: 8px;
                    font-size: 11px;
                    font-weight: 850;
                    padding: 7px 12px;
                }
                QLabel#metaSearchTermGroup[semantic="population"] {
                    background: #EAF3FF;
                    color: #1D4ED8;
                    border-left: 3px solid #3B82F6;
                }
                QLabel#metaSearchTermGroup[semantic="exposure"] {
                    background: #E9FBF3;
                    color: #047857;
                    border-left: 3px solid #10B981;
                }
                QLabel#metaSearchTermGroup[semantic="outcome"] {
                    background: #FFF7ED;
                    color: #C2410C;
                    border-left: 3px solid #FB923C;
                }
                QLabel#metaSearchTermGroup[semantic="study"] {
                    background: #F5F3FF;
                    color: #7C3AED;
                    border-left: 3px solid #A855F7;
                }
                QLabel#metaSearchQueryEditor {
                    background: #FFFFFF;
                    border: 1px solid #D8E1EC;
                    border-radius: 8px;
                    color: #64748B;
                    font-family: Menlo;
                    font-size: 11px;
                    padding: 8px;
                }
                QLabel#metaSearchDbRow {
                    background: #FFFFFF;
                    border: 1px solid #D8E1EC;
                    border-radius: 8px;
                    color: #334155;
                    font-size: 11px;
                    padding: 9px 12px;
                }
                QLabel#metaSearchDbRow[selected="true"] {
                    background: #EFF6FF;
                    border-color: #93C5FD;
                }
                QLabel#metaSearchChecklistPassed {
                    color: #059669;
                    font-size: 11px;
                    font-weight: 850;
                }
                QLabel#metaSearchChecklistWarning {
                    color: #D97706;
                    font-size: 11px;
                    font-weight: 850;
                }
                QLabel#metaSearchChecklistTodo {
                    color: #64748B;
                    font-size: 11px;
                    font-weight: 850;
                }
                QPushButton#metaDatabaseDraftScopeButton {
                    background: #EFF6FF;
                    border: 1px solid #93C5FD;
                    border-radius: 8px;
                    color: #1D4ED8;
                    font-size: 11px;
                    font-weight: 850;
                    text-align: left;
                    padding: 8px 10px;
                }
                QPushButton#metaCopyQueryButton,
                QPushButton#metaSaveSearchDraftButton,
                QPushButton#metaSearchTokenButton {
                    background: #FFFFFF;
                    border: 1px solid #D8E1EC;
                    border-radius: 7px;
                    color: #334155;
                    font-size: 11px;
                    font-weight: 750;
                    padding: 6px 10px;
                }
                QPushButton#metaSearchTokenButton[token="operator"] {
                    background: #EFF6FF;
                    border-color: #93C5FD;
                    color: #1D4ED8;
                }
                QPushButton#metaSearchNextReferenceButton {
                    background: #2563EB;
                    border: 1px solid #2563EB;
                    border-radius: 9px;
                    color: #FFFFFF;
                    font-size: 12px;
                    font-weight: 850;
                    padding: 10px 12px;
                }
                """
            )
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(14)
            layout.addWidget(self._build_meta_search_stepper())

            term_table = _readonly_table(
                "metaSearchTermGroupTable",
                ("Term group", "English terms", "State"),
                (
                    ("Disease", "thyroid cancer OR thyroid carcinoma OR thyroid neoplasm", "draft"),
                    ("Biomarker", "adiponectin OR ADIPOQ", "draft"),
                    ("Outcome", "prognosis OR survival OR recurrence OR clinicopathological", "draft"),
                ),
            )
            term_table.setMinimumHeight(118)
            term_table.setVisible(False)

            query = QLabel(
                'PubMed-style query draft: ("thyroid cancer"[Title/Abstract] OR "thyroid carcinoma"[Title/Abstract] OR '
                '"thyroid neoplasm"[Title/Abstract]) AND ("adiponectin"[Title/Abstract] OR "ADIPOQ"[Title/Abstract]) '
                'AND ("prognosis"[Title/Abstract] OR "survival"[Title/Abstract] OR "recurrence"[Title/Abstract] OR '
                '"clinicopathological"[Title/Abstract])'
            )
            query.setObjectName("metaSearchPubMedStyleQueryDraft")
            query.setProperty("queryState", "draft_only")
            query.setWordWrap(True)
            query.setStyleSheet("background: transparent; border: 0; color: #64748B;")
            query.setVisible(False)

            logic = QLabel("Boolean logic preview: Disease AND Biomarker AND Outcome")
            logic.setObjectName("metaSearchBooleanLogicPreview")
            logic.setWordWrap(True)
            logic.setVisible(False)

            database_scope = QFrame()
            database_scope.setObjectName("metaDatabaseDraftScope")
            database_scope.setProperty("selectionState", "draft_scope_only")
            database_layout = QVBoxLayout(database_scope)
            database_layout.setContentsMargins(0, 0, 0, 0)
            database_layout.setSpacing(8)
            for database in ("PubMed", "Embase", "Web of Science"):
                item = QPushButton(database)
                item.setObjectName("metaDatabaseDraftScopeButton")
                item.setCheckable(True)
                item.setChecked(True)
                item.setProperty("databaseName", database)
                item.setProperty("selectionState", "draft_scope_only")
                item.setProperty("executedSearch", False)
                item.setProperty("formalActionEnabled", False)
                item.setMinimumHeight(42)
                database_layout.addWidget(item)

            action_row = QHBoxLayout()
            copy_query = QPushButton("Copy Query")
            copy_query.setObjectName("metaCopyQueryButton")
            copy_query.setProperty("actionSemantic", "copy_only")
            copy_query.setProperty("formalActionEnabled", False)
            copy_query.setMinimumHeight(34)
            save_draft = QPushButton("Save Draft - adapter needed")
            save_draft.setObjectName("metaSaveSearchDraftButton")
            save_draft.setProperty("actionSemantic", "adapter_needed")
            save_draft.setProperty("formalActionEnabled", False)
            save_draft.setEnabled(False)
            save_draft.setMinimumHeight(34)
            action_row.addWidget(copy_query)
            action_row.addWidget(save_draft)
            action_row.addStretch(1)

            main = QHBoxLayout()
            main.setSpacing(14)
            left = QVBoxLayout()
            left.setSpacing(14)
            left.addWidget(self._build_query_builder_card(term_table, query, action_row))
            left.addWidget(self._build_search_fields_card())
            main.addLayout(left, 1)
            right = QVBoxLayout()
            right.setSpacing(14)
            right.addWidget(self._build_database_selection_card(database_scope))
            right.addWidget(self._build_strategy_checklist_card())
            right.addStretch(1)
            right_wrap = QWidget()
            right_wrap.setMinimumWidth(360)
            right_wrap.setMaximumWidth(400)
            right_wrap.setLayout(right)
            main.addWidget(right_wrap)
            layout.addLayout(main)

            next_ref = QPushButton("下一步：文献导入 / Next: Reference Management")
            next_ref.setObjectName("metaSearchNextReferenceButton")
            next_ref.setProperty("targetPageKey", "import_dedup")
            next_ref.setProperty("formalActionEnabled", False)
            next_ref.clicked.connect(lambda _checked=False: self.show_target_ia_page("import_dedup"))
            layout.addWidget(next_ref)
            layout.addWidget(logic)
            return frame

        def _build_meta_search_stepper(self) -> QFrame:
            stepper = QFrame()
            stepper.setObjectName("metaSearchStepper")
            layout = QHBoxLayout(stepper)
            layout.setContentsMargins(16, 10, 16, 10)
            layout.setSpacing(8)
            steps = (
                ("✓", "项目首页\nProject Home", "done"),
                ("✓", "问题与类型\nQuestion", "done"),
                ("3", "检索策略\nSearch Strategy", "current"),
                ("4", "文献导入\nReferences", "todo"),
                ("5", "去重\nDeduplication", "todo"),
                ("6", "筛选\nScreening", "todo"),
                ("7", "全文提取\nFull-text", "todo"),
                ("8", "偏倚风险\nRisk of Bias", "todo"),
                ("9", "成对Meta\nPairwise", "todo"),
                ("10", "结果复核\nReview", "todo"),
                ("11", "报告门控\nGate", "todo"),
                ("12", "导出\nExport", "todo"),
            )
            for marker, text, state in steps:
                item = QLabel(f"{marker}\n{text}")
                item.setObjectName("metaSearchStepCurrent" if state == "current" else "metaSearchStepDone")
                item.setAlignment(Qt.AlignCenter)
                item.setMinimumWidth(64)
                layout.addWidget(item, 1)
            return stepper

        def _build_query_builder_card(self, term_table: QTableWidget, query: QLabel, action_row: QHBoxLayout) -> QFrame:
            card = QFrame()
            card.setObjectName("metaSearchCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(14, 10, 14, 12)
            layout.setSpacing(9)
            title = QLabel("1. 检索式构建 / Query Builder")
            title.setObjectName("metaSearchTitle")
            layout.addWidget(title)
            header = QHBoxLayout()
            label = QLabel("关键词组 / TERM GROUPS")
            label.setObjectName("metaSearchTitle")
            count = QLabel("4 groups")
            count.setObjectName("metaSearchMuted")
            header.addWidget(label)
            header.addStretch(1)
            header.addWidget(count)
            layout.addLayout(header)
            for semantic, heading, value, terms in (
                ("population", "POPULATION / 人群", "甲状腺癌", "3 terms"),
                ("exposure", "EXPOSURE / INDEX MARKER / 暴露/指标", "Adiponectin", "4 terms"),
                ("outcome", "OUTCOME / 结局", "预后 / 生存等", "6 terms"),
                ("study", "STUDY DESIGN / 研究设计", "观察性研究", "4 terms"),
            ):
                layout.addWidget(self._search_term_group_label(semantic, heading, value, terms))
            add = QLabel("+  新建关键词组 / New Group")
            add.setObjectName("metaSearchMuted")
            add.setAlignment(Qt.AlignCenter)
            add.setStyleSheet("border: 1px dashed #CBD5E1; border-radius: 8px; padding: 8px; color: #64748B;")
            layout.addWidget(add)
            editor_header = QHBoxLayout()
            editor_title = QLabel("检索式编辑 / QUERY EDITOR")
            editor_title.setObjectName("metaSearchTitle")
            editor_count = QLabel("5 lines · 313 chars")
            editor_count.setObjectName("metaSearchMuted")
            editor_header.addWidget(editor_title)
            editor_header.addStretch(1)
            editor_header.addWidget(editor_count)
            layout.addLayout(editor_header)
            editor = QLabel(
                "1  (thyroid cancer OR thyroid carcinoma OR thyroid neoplasm)\n"
                "2  AND (adiponectin OR ADIPOQ)\n"
                "3  AND (prognosis OR survival OR recurrence)\n"
                "4  AND (clinicopathological OR overall survival)\n"
                "5  NOT animal studies"
            )
            editor.setObjectName("metaSearchQueryEditor")
            editor.setMinimumHeight(118)
            editor.setMaximumHeight(118)
            editor.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            layout.addWidget(editor)
            token_row = QHBoxLayout()
            token_row.setSpacing(6)
            for text, semantic in (("清空", ""), ("格式化", ""), ("添加组", ""), ("AND", "operator"), ("OR", "operator"), ("NOT", "operator"), ("(", "operator"), (")", "operator"), ("预览", "")):
                button = QPushButton(text)
                button.setObjectName("metaSearchTokenButton")
                button.setProperty("token", semantic)
                button.setProperty("formalActionEnabled", False)
                button.setEnabled(text not in {"添加组"})
                button.setMinimumHeight(28)
                token_row.addWidget(button)
            token_row.addStretch(1)
            layout.addLayout(token_row)
            layout.addLayout(action_row)
            layout.addWidget(query)
            layout.addWidget(term_table)
            return card

        def _search_term_group_label(self, semantic: str, heading: str, value: str, terms: str) -> QLabel:
            label = QLabel(f"{heading}\n{value}                                      {terms}   edit  delete")
            label.setObjectName("metaSearchTermGroup")
            label.setProperty("semantic", semantic)
            label.setMinimumHeight(46)
            label.setMaximumHeight(46)
            return label

        def _build_search_fields_card(self) -> QFrame:
            card = QFrame()
            card.setObjectName("metaSearchCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(16, 12, 16, 16)
            layout.setSpacing(10)
            title = QLabel("2. 检索字段与限制 / Fields & Filters")
            title.setObjectName("metaSearchTitle")
            layout.addWidget(title)
            for text in (
                "FIELD / 字段：Title/Abstract, MeSH Terms, Keywords",
                "LANGUAGE / 语言：English-first draft; Chinese database search disabled",
                "YEAR / 年份：No limit by default",
            ):
                label = QLabel(text)
                label.setObjectName("metaSearchDbRow")
                layout.addWidget(label)
            return card

        def _build_database_selection_card(self, database_scope: QFrame) -> QFrame:
            card = QFrame()
            card.setObjectName("metaSearchSideCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(16, 12, 16, 16)
            layout.setSpacing(10)
            title = QLabel("4. 选择数据库 / Select Databases (Draft)")
            title.setObjectName("metaSearchTitle")
            layout.addWidget(title)
            tabs = QHBoxLayout()
            for text, active in (("全部 / All", False), ("常用 / Common", True), ("自定义 / Custom", False)):
                tab = QLabel(text)
                tab.setAlignment(Qt.AlignCenter)
                tab.setObjectName("metaSearchDbRow")
                tab.setProperty("selected", active)
                if active:
                    tab.setStyleSheet("background: #2563EB; color: #FFFFFF; border: 0; border-radius: 0; padding: 8px; font-weight: 850;")
                tabs.addWidget(tab, 1)
            layout.addLayout(tabs)
            layout.addWidget(database_scope)
            for name, code, selected in (
                ("Scopus", "SCP", False),
                ("Cochrane Library", "COC", False),
                ("Other（手动导入 / Manual import）", "", False),
            ):
                row = QLabel(f"{'☑' if selected else '☐'}   {name}\n无数量限制 / No limit                         {code}")
                row.setObjectName("metaSearchDbRow")
                row.setProperty("selected", selected)
                layout.addWidget(row)
            footer = QHBoxLayout()
            selected = QLabel("2 个已选 / selected")
            selected.setObjectName("metaSearchMuted")
            draft = QLabel("Draft — 不执行真实检索")
            draft.setStyleSheet("background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 8px; color: #D97706; padding: 4px 8px;")
            footer.addWidget(selected)
            footer.addStretch(1)
            footer.addWidget(draft)
            layout.addLayout(footer)
            return card

        def _build_strategy_checklist_card(self) -> QFrame:
            card = QFrame()
            card.setObjectName("metaSearchSideCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(16, 12, 16, 16)
            layout.setSpacing(10)
            title = QLabel("5. 检索策略清单 / Strategy Checklist")
            title.setObjectName("metaSearchTitle")
            layout.addWidget(title)
            rows = (
                ("研究问题已确定", "Research question defined", "passed"),
                ("关键词组已覆盖核心要素", "Key elements covered", "passed"),
                ("布尔逻辑结构完整", "Boolean logic structure complete", "passed"),
                ("字段与限制需优化", "Fields & limits need optimization", "warning"),
                ("数据库组合待确认", "Database combination to confirm", "todo"),
                ("检索执行与结果数量待记录", "Execution & results to be recorded", "todo"),
            )
            for zh, en, state in rows:
                label = QLabel(f"{'✓' if state == 'passed' else ('!' if state == 'warning' else '○')}  {zh}\n   {en}        { {'passed': '通过', 'warning': '警告', 'todo': '未完成'}[state] }")
                label.setObjectName(
                    "metaSearchChecklistPassed" if state == "passed" else ("metaSearchChecklistWarning" if state == "warning" else "metaSearchChecklistTodo")
                )
                layout.addWidget(label)
            progress = QLabel("3 / 6 完成")
            progress.setObjectName("metaSearchMuted")
            progress.setAlignment(Qt.AlignRight)
            layout.addWidget(progress)
            return card

        def _build_reference_dedup_panel(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("metaReferenceDedupRuntimePanel")
            frame.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
            frame.setProperty("pageKey", "import_dedup")
            frame.setProperty("runtimeStatus", "testing")
            frame.setProperty("processingMode", "english_first")
            frame.setProperty("aiBoundary", "advisory_only")
            frame.setProperty("resultSemanticKey", "no_formal_result")
            frame.setProperty("reportStatusKey", "report.status.draft")
            frame.setProperty("exportGate", "disabled_empty_result")
            frame.setProperty("formalActionEnabled", False)
            frame.setStyleSheet("QFrame#metaReferenceDedupRuntimePanel { border: 1px solid #D6E0EA; border-radius: 8px; background: #FFFFFF; }")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(10)

            title = QLabel("Import / Reference Management / Deduplication")
            title.setObjectName("metaReferenceDedupRuntimeTitle")
            title.setStyleSheet("font-weight: 750;")
            layout.addWidget(title)

            import_row = QHBoxLayout()
            for source_id, label in (
                ("ris_bibtex_endnote", "RIS / BibTeX / EndNote XML"),
                ("csv_excel", "CSV / Excel"),
                ("pubmed_result_file", "PubMed result file"),
                ("manual_entry", "Manual entry"),
            ):
                card = QFrame()
                card.setObjectName("metaImportSourceCard")
                card.setProperty("sourceId", source_id)
                card.setProperty("importState", "adapter_needed")
                card.setStyleSheet("QFrame#metaImportSourceCard { border: 1px solid #CBD5E1; border-radius: 8px; background: #F8FAFC; }")
                card_layout = QVBoxLayout(card)
                card_layout.setContentsMargins(10, 8, 10, 8)
                label_widget = QLabel(label)
                label_widget.setObjectName("metaImportSourceLabel")
                label_widget.setWordWrap(True)
                button = QPushButton("Import - adapter needed")
                button.setObjectName("metaImportSourceButton")
                button.setProperty("sourceId", source_id)
                button.setProperty("actionSemantic", "adapter_needed")
                button.setProperty("formalActionEnabled", False)
                button.setEnabled(False)
                card_layout.addWidget(label_widget)
                card_layout.addWidget(button)
                import_row.addWidget(card)
            layout.addLayout(import_row)

            reference_label = QLabel("Reference table preview (mockup-only / local draft)")
            reference_label.setObjectName("metaReferenceTablePreviewLabel")
            reference_label.setStyleSheet("font-weight: 700;")
            layout.addWidget(reference_label)
            reference_table = _readonly_table(
                "metaReferencePreviewTable",
                ("ref_id", "title", "year", "source", "DOI/PMID", "screening_status", "dedup_status"),
                (
                    ("REF-001", "Serum adiponectin and clinicopathological features in thyroid carcinoma", "2018", "PubMed mock", "PMID-MOCK-001", "not_started", "unique"),
                    ("REF-002", "ADIPOQ expression and survival outcomes in differentiated thyroid cancer", "2020", "RIS mock", "DOI-MOCK-002", "not_started", "possible_duplicate"),
                    ("REF-003", "Adiponectin signaling in thyroid neoplasm progression", "2021", "CSV mock", "DOI-MOCK-003", "not_started", "possible_duplicate"),
                    ("REF-004", "Circulating adipokines and thyroid cancer risk", "2017", "PubMed mock", "PMID-MOCK-004", "not_started", "unique"),
                ),
            )
            reference_table.setMinimumHeight(150)
            layout.addWidget(reference_table)

            dedup_label = QLabel("Deduplication risk preview")
            dedup_label.setObjectName("metaDedupRiskPreviewTitle")
            dedup_label.setStyleSheet("font-weight: 700;")
            layout.addWidget(dedup_label)
            dedup_table = _readonly_table(
                "metaDedupRiskGroupTable",
                ("group_id", "risk", "records", "reviewer compare draft", "boundary"),
                (
                    ("DUP-001", "possible duplicate", "REF-002, REF-003", "compare title / DOI / year", "reviewer review required"),
                ),
            )
            dedup_table.setMinimumHeight(86)
            layout.addWidget(dedup_table)

            chip = make_status_chip("no automatic merge / reviewer review required", status_key="blocked")
            chip.setObjectName("metaDedupReviewerRequiredChip")
            layout.addWidget(chip)

            action_row = QHBoxLayout()
            for object_name, text in (
                ("metaAutoMergeDisabledButton", "Auto merge disabled"),
                ("metaAutoDeleteDisabledButton", "Auto delete disabled"),
                ("metaSendToScreeningDisabledButton", "Send to screening disabled"),
            ):
                button = QPushButton(text)
                button.setObjectName(object_name)
                button.setProperty("actionSemantic", "disabled_boundary")
                button.setProperty("formalActionEnabled", False)
                button.setEnabled(False)
                button.setMinimumHeight(34)
                action_row.addWidget(button)
            action_row.addStretch(1)
            layout.addLayout(action_row)
            return frame

        def _build_screening_panel(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("metaScreeningRuntimePanel")
            frame.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
            frame.setProperty("pageKey", "screening")
            frame.setProperty("runtimeStatus", "testing")
            frame.setProperty("processingMode", "english_first")
            frame.setProperty("aiBoundary", "advisory_only")
            frame.setProperty("screeningState", "draft_decisions_only")
            frame.setProperty("resultSemanticKey", "no_formal_result")
            frame.setProperty("reportStatusKey", "report.status.draft")
            frame.setProperty("exportGate", "disabled_empty_result")
            frame.setProperty("formalActionEnabled", False)
            frame.setStyleSheet(
                """
                QFrame#metaScreeningRuntimePanel {
                    background: #F5F7FB;
                    border: 0;
                }
                QFrame#metaScreeningCard,
                QFrame#metaScreeningStepper,
                QFrame#metaScreeningProgressCard,
                QFrame#metaScreeningDecisionCard,
                QFrame#metaScreeningDecisionLog {
                    background: #FFFFFF;
                    border: 1px solid #E5E7EB;
                    border-radius: 12px;
                }
                QLabel#metaScreeningTitle {
                    color: #0F172A;
                    font-size: 13px;
                    font-weight: 850;
                }
                QLabel#metaScreeningMuted,
                QLabel#metaScreeningSmall {
                    color: #64748B;
                    font-size: 11px;
                }
                QLabel#metaScreeningStepDone,
                QLabel#metaScreeningStepCurrent,
                QLabel#metaScreeningStepTodo {
                    color: #94A3B8;
                    font-size: 10px;
                    font-weight: 750;
                }
                QLabel#metaScreeningStepDone,
                QLabel#metaScreeningStepCurrent {
                    color: #2563EB;
                    font-weight: 900;
                }
                QLabel#metaScreeningRefItem {
                    background: #FFFFFF;
                    border: 1px solid transparent;
                    border-radius: 8px;
                    color: #334155;
                    font-size: 11px;
                    padding: 8px 10px;
                }
                QLabel#metaScreeningRefItem[selected="true"] {
                    background: #EAF3FF;
                    border-left: 3px solid #2563EB;
                    border-color: #BFDBFE;
                }
                QLabel#metaScreeningStatusInclude {
                    background: #DCFCE7;
                    border-radius: 8px;
                    color: #059669;
                    font-size: 10px;
                    font-weight: 850;
                    padding: 3px 6px;
                }
                QLabel#metaScreeningStatusExclude {
                    background: #FEE2E2;
                    border-radius: 8px;
                    color: #DC2626;
                    font-size: 10px;
                    font-weight: 850;
                    padding: 3px 6px;
                }
                QLabel#metaScreeningStatusUncertain {
                    background: #FEF3C7;
                    border-radius: 8px;
                    color: #D97706;
                    font-size: 10px;
                    font-weight: 850;
                    padding: 3px 6px;
                }
                QLabel#metaScreeningStatusFulltext {
                    background: #DBEAFE;
                    border-radius: 8px;
                    color: #2563EB;
                    font-size: 10px;
                    font-weight: 850;
                    padding: 3px 6px;
                }
                QLabel#metaScreeningMetric {
                    color: #2563EB;
                    font-size: 16px;
                    font-weight: 900;
                }
                QLabel#metaScreeningAbstract {
                    background: transparent;
                    border: 0;
                    color: #475569;
                    font-size: 12px;
                    line-height: 1.35;
                }
                QLabel#metaScreeningMetaBox,
                QLabel#metaScreeningNoteBox {
                    background: #F8FAFC;
                    border: 1px solid #EEF2F7;
                    border-radius: 10px;
                    color: #475569;
                    font-size: 11px;
                    padding: 8px 10px;
                }
                QLabel#metaScreeningKeyword {
                    background: #EFF6FF;
                    border: 1px solid #BFDBFE;
                    border-radius: 10px;
                    color: #2563EB;
                    font-size: 10px;
                    font-weight: 800;
                    padding: 4px 8px;
                }
                QLabel#metaScreeningAISuggestionCard {
                    background: #FFFBEB;
                    border: 1px solid #FDE68A;
                    border-radius: 10px;
                    color: #B45309;
                    font-size: 11px;
                    padding: 8px 10px;
                }
                QLabel#metaScreeningExclusionReason,
                QLabel#metaScreeningNotesBox {
                    background: #F8FAFC;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                    color: #94A3B8;
                    font-size: 11px;
                    padding: 9px 10px;
                }
                QPushButton#metaScreeningDecisionDraftButton {
                    border-radius: 10px;
                    font-size: 12px;
                    font-weight: 850;
                    padding: 10px 12px;
                }
                QPushButton#metaScreeningDecisionDraftButton[decisionId="include_draft"] {
                    background: #E9FBF3;
                    border: 1px solid #86EFAC;
                    color: #059669;
                }
                QPushButton#metaScreeningDecisionDraftButton[decisionId="exclude_draft"] {
                    background: #FF3045;
                    border: 1px solid #FF3045;
                    color: #FFFFFF;
                }
                QPushButton#metaScreeningDecisionDraftButton[decisionId="uncertain"] {
                    background: #FFFBEB;
                    border: 1px solid #FACC15;
                    color: #B45309;
                }
                QPushButton#metaScreeningDecisionDraftButton[decisionId="need_full_text"] {
                    background: #EFF6FF;
                    border: 1px solid #93C5FD;
                    color: #2563EB;
                }
                QPushButton#metaSaveDraftScreeningDecisionButton {
                    background: #2563EB;
                    border: 1px solid #2563EB;
                    border-radius: 10px;
                    color: #FFFFFF;
                    font-size: 12px;
                    font-weight: 900;
                    padding: 10px 12px;
                }
                QPushButton#metaScreeningSaveNextButton {
                    background: #FFFFFF;
                    border: 1px solid #E5E7EB;
                    border-radius: 10px;
                    color: #475569;
                    font-size: 11px;
                    font-weight: 750;
                    padding: 8px 10px;
                }
                QPushButton#metaScreeningNextFulltextButton {
                    background: #2563EB;
                    border: 1px solid #2563EB;
                    border-radius: 10px;
                    color: #FFFFFF;
                    font-size: 12px;
                    font-weight: 900;
                    padding: 10px 14px;
                }
                """
            )
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(12)
            layout.addWidget(self._build_meta_screening_stepper())

            counts = _readonly_table(
                "metaScreeningDraftCountsTable",
                ("Bucket", "Count", "State"),
                (
                    ("Queue", "4", "draft counts"),
                    ("Include draft", "1", "not final"),
                    ("Exclude draft", "1", "not final"),
                    ("Uncertain", "1", "draft"),
                    ("Need full text", "1", "draft"),
                ),
            )
            counts.setMinimumHeight(118)
            counts.setVisible(False)

            queue = _readonly_table(
                "metaScreeningReferenceQueue",
                ("ref_id", "title", "screening_status"),
                (
                    ("REF-001", "Serum adiponectin and clinicopathological features in thyroid carcinoma", "include_draft"),
                    ("REF-002", "ADIPOQ expression and survival outcomes in differentiated thyroid cancer", "uncertain"),
                    ("REF-004", "Circulating adipokines and thyroid cancer risk", "exclude_draft"),
                ),
            )
            queue.setMinimumHeight(138)
            queue.setVisible(False)

            reference_queue = make_reference_queue_panel(
                references=(
                    ReferenceItem("REF-001", "Serum adiponectin and clinicopathological features", "include_draft", "testing", "testing"),
                    ReferenceItem("REF-002", "ADIPOQ expression and survival outcomes", "uncertain", "testing", "testing"),
                    ReferenceItem("REF-004", "Circulating adipokines and thyroid cancer risk", "exclude_draft", "testing", "testing"),
                ),
                object_name="metaSharedReferenceQueuePanel",
            )
            reference_queue.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
            reference_queue.setProperty("pageKey", "screening")
            reference_queue.setProperty("screeningState", "draft_decisions_only")
            reference_queue.setProperty("formalActionEnabled", False)
            reference_queue.setVisible(False)

            main = QHBoxLayout()
            main.setSpacing(12)
            main.addWidget(self._build_screening_queue_column(counts, queue, reference_queue))
            main.addWidget(self._build_screening_reference_detail_card(), 1)
            main.addWidget(self._build_screening_decision_column())
            layout.addLayout(main)

            footer = QHBoxLayout()
            note = QLabel("AI 建议仅供参考，不能替代人工筛选。最终纳排决策须由研究者确认后方可进入下一流程。")
            note.setObjectName("metaScreeningMuted")
            note.setStyleSheet("color: #2563EB;")
            footer.addWidget(note, 1)
            next_fulltext = QPushButton("下一步：全文与提取 / Next: Full-text & Extraction  ->")
            next_fulltext.setObjectName("metaScreeningNextFulltextButton")
            next_fulltext.setProperty("targetPageKey", "fulltext_extraction")
            next_fulltext.setProperty("formalActionEnabled", False)
            next_fulltext.clicked.connect(lambda _checked=False: self.show_target_ia_page("fulltext_extraction"))
            footer.addWidget(next_fulltext)
            layout.addLayout(footer)

            layout.addWidget(counts)
            layout.addWidget(queue)
            layout.addWidget(reference_queue)
            return frame

        def _build_meta_screening_stepper(self) -> QFrame:
            stepper = QFrame()
            stepper.setObjectName("metaScreeningStepper")
            layout = QHBoxLayout(stepper)
            layout.setContentsMargins(12, 9, 12, 9)
            layout.setSpacing(6)
            steps = (
                ("1", "选题\nTopic", "done"),
                ("2", "协议\nProtocol", "done"),
                ("3", "检索\nSearch", "done"),
                ("4", "去重\nDedup", "done"),
                ("5", "筛选\nScreening", "current"),
                ("6", "全文\nFull-text", "todo"),
                ("7", "提取\nExtraction", "todo"),
                ("8", "质量\nQuality", "todo"),
                ("9", "合并\nSynthesis", "todo"),
                ("10", "分析\nAnalysis", "todo"),
                ("11", "报告\nReport", "todo"),
                ("12", "发布\nPublish", "todo"),
            )
            for marker, text, state in steps:
                item = QLabel(f"{marker}\n{text}")
                item.setObjectName(
                    "metaScreeningStepCurrent" if state == "current" else ("metaScreeningStepDone" if state == "done" else "metaScreeningStepTodo")
                )
                item.setAlignment(Qt.AlignCenter)
                item.setMinimumWidth(48)
                layout.addWidget(item, 1)
            return stepper

        def _build_screening_queue_column(self, counts: QTableWidget, queue: QTableWidget, reference_queue: QFrame) -> QFrame:
            column = QFrame()
            column.setObjectName("metaScreeningCard")
            column.setFixedWidth(280)
            column.setFixedHeight(575)
            layout = QVBoxLayout(column)
            layout.setContentsMargins(12, 10, 12, 10)
            layout.setSpacing(8)
            header = QHBoxLayout()
            title = QLabel("参考文献队列 / Queue")
            title.setObjectName("metaScreeningTitle")
            title.setWordWrap(True)
            badge = QLabel("8 条")
            badge.setObjectName("metaScreeningSmall")
            badge.setStyleSheet("border: 1px solid #E5E7EB; border-radius: 10px; padding: 3px 8px;")
            header.addWidget(title)
            header.addStretch(1)
            header.addWidget(badge)
            layout.addLayout(header)

            tabs = QHBoxLayout()
            for text, active in (("全部 (8)", True), ("待筛选 (6)", False), ("已处理 (2)", False)):
                tab = QLabel(text)
                tab.setObjectName("metaScreeningSmall")
                tab.setAlignment(Qt.AlignCenter)
                if active:
                    tab.setStyleSheet("color: #2563EB; font-weight: 900; border-bottom: 2px solid #2563EB; padding: 6px;")
                else:
                    tab.setStyleSheet("color: #64748B; padding: 6px;")
                tabs.addWidget(tab, 1)
            layout.addLayout(tabs)

            refs = (
                ("#004", "建议纳入", "include", "待筛选", "CAR-T relapsed B-cell lymphoma review", "2022  Blood Cancer"),
                ("#005", "建议排除", "exclude", "已排除", "PD-L1 gastric cancer meta-analysis", "2017  Oncotarget"),
                ("#006", "不确定", "uncertain", "待筛选", "Dupilumab safety in adult dermatitis", "2019  JAMA"),
            )
            for index, (ref_no, badge_text, semantic, state, title_text, meta) in enumerate(refs):
                layout.addWidget(self._build_screening_reference_item(ref_no, badge_text, semantic, state, title_text, meta, selected=index == 0))

            footer = QHBoxLayout()
            footer_label = QLabel("第 1-8 条，共 22 条")
            footer_label.setObjectName("metaScreeningMuted")
            page = QLabel("<   1   >")
            page.setObjectName("metaScreeningMuted")
            page.setAlignment(Qt.AlignRight)
            footer.addWidget(footer_label)
            footer.addStretch(1)
            footer.addWidget(page)
            layout.addLayout(footer)

            progress = QFrame()
            progress.setObjectName("metaScreeningProgressCard")
            progress_layout = QVBoxLayout(progress)
            progress_layout.setContentsMargins(12, 10, 12, 10)
            progress_layout.setSpacing(8)
            progress_title = QLabel("筛选进度 / Screening Progress")
            progress_title.setObjectName("metaScreeningTitle")
            progress_layout.addWidget(progress_title)
            metrics = QHBoxLayout()
            for value, label, color in (("6", "待筛选", "#2563EB"), ("1", "已纳入", "#059669"), ("1", "已排除", "#DC2626"), ("0", "不确定", "#D97706")):
                box = QVBoxLayout()
                metric = QLabel(value)
                metric.setObjectName("metaScreeningMetric")
                metric.setAlignment(Qt.AlignCenter)
                metric.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 900;")
                caption = QLabel(label)
                caption.setObjectName("metaScreeningMuted")
                caption.setAlignment(Qt.AlignCenter)
                box.addWidget(metric)
                box.addWidget(caption)
                metrics.addLayout(box)
            progress_layout.addLayout(metrics)
            bar = QLabel("")
            bar.setFixedHeight(6)
            bar.setStyleSheet("background: #2563EB; border-radius: 3px;")
            progress_layout.addWidget(bar)
            percent = QLabel("25% 完成")
            percent.setObjectName("metaScreeningMuted")
            percent.setAlignment(Qt.AlignRight)
            progress_layout.addWidget(percent)
            layout.addWidget(progress)
            return column

        def _build_screening_reference_item(self, ref_no: str, badge_text: str, semantic: str, state: str, title_text: str, meta: str, *, selected: bool) -> QLabel:
            label = QLabel(f"{ref_no}    {badge_text}                                      {state}\n{title_text} · {meta}")
            label.setObjectName("metaScreeningRefItem")
            label.setProperty("selected", selected)
            label.setWordWrap(True)
            label.setMinimumHeight(72 if selected else 68)
            label.setMaximumHeight(82 if selected else 76)
            return label

        def _build_screening_reference_detail_card(self) -> QFrame:
            detail = QFrame()
            detail.setObjectName("metaScreeningReferenceDetail")
            detail.setProperty("screeningState", "draft_decisions_only")
            detail.setFixedWidth(390)
            detail.setFixedHeight(575)
            layout = QVBoxLayout(detail)
            layout.setContentsMargins(14, 10, 14, 10)
            layout.setSpacing(8)
            header = QHBoxLayout()
            title = QLabel("文献详情 / Reference Detail")
            title.setObjectName("metaScreeningTitle")
            pager = QLabel("<    4 / 8    >")
            pager.setObjectName("metaScreeningMuted")
            header.addWidget(title)
            header.addStretch(1)
            header.addWidget(pager)
            layout.addLayout(header)

            paper_title = QLabel("CAR-T cell therapy for relapsed or refractory B-cell non-Hodgkin lymphoma: systematic review and meta-analysis")
            paper_title.setObjectName("metaScreeningTitle")
            paper_title.setStyleSheet("font-size: 14px; font-weight: 900; color: #0F172A;")
            paper_title.setWordWrap(True)
            layout.addWidget(paper_title)
            author = QLabel("Schuster SJ, Bishop MR, Tam CS, et al.")
            author.setObjectName("metaScreeningMuted")
            layout.addWidget(author)

            meta_box = QLabel("期刊 / JOURNAL                         年份 / YEAR\nBlood Cancer Journal                    2022\n\nPMID                                     DOI\n35773265                                10.1038/s41408-022-00700-z")
            meta_box.setObjectName("metaScreeningMetaBox")
            meta_box.setWordWrap(True)
            layout.addWidget(meta_box)

            abstract_title = QLabel("摘要 / ABSTRACT")
            abstract_title.setObjectName("metaScreeningMuted")
            abstract_title.setStyleSheet("font-weight: 850; color: #94A3B8;")
            layout.addWidget(abstract_title)
            abstract = QLabel(
                "Chimeric antigen receptor T-cell (CAR-T) therapy has emerged as a transformative treatment for relapsed or refractory B-cell non-Hodgkin lymphoma. "
                "This systematic review and meta-analysis evaluates efficacy and safety across multiple clinical trials. Pooled response rate and safety outcomes are summarized for reviewer triage."
            )
            abstract.setObjectName("metaScreeningAbstract")
            abstract.setWordWrap(True)
            layout.addWidget(abstract)

            keyword_title = QLabel("关键词 / KEYWORDS")
            keyword_title.setObjectName("metaScreeningMuted")
            keyword_title.setStyleSheet("font-weight: 850; color: #94A3B8;")
            layout.addWidget(keyword_title)
            keyword_row = QHBoxLayout()
            for keyword in ("CAR-T", "B-cell", "CD19", "immuno", "meta"):
                chip = QLabel(keyword)
                chip.setObjectName("metaScreeningKeyword")
                chip.setAlignment(Qt.AlignCenter)
                keyword_row.addWidget(chip)
            keyword_row.addStretch(1)
            layout.addLayout(keyword_row)

            ai_card = QLabel("AI suggestion: likely_include, confidence 0.72. Advisory only; reviewer remains the authority.")
            ai_card.setObjectName("metaScreeningAISuggestionCard")
            ai_card.setProperty("aiBoundary", "advisory_only")
            ai_card.setWordWrap(True)
            layout.addWidget(ai_card)
            layout.addStretch(1)
            return detail

        def _build_screening_decision_column(self) -> QFrame:
            column = QFrame()
            column.setObjectName("metaScreeningDecisionCard")
            column.setFixedWidth(260)
            column.setFixedHeight(575)
            layout = QVBoxLayout(column)
            layout.setContentsMargins(12, 10, 12, 10)
            layout.setSpacing(8)
            title = QLabel("筛选决策 / Screening Decision")
            title.setObjectName("metaScreeningTitle")
            title.setWordWrap(True)
            layout.addWidget(title)
            decision_label = QLabel("选择决策 / SELECT DECISION")
            decision_label.setObjectName("metaScreeningMuted")
            decision_label.setStyleSheet("font-weight: 850; color: #94A3B8;")
            layout.addWidget(decision_label)

            decision_grid = QGridLayout()
            decision_grid.setHorizontalSpacing(8)
            decision_grid.setVerticalSpacing(8)
            for decision_id, text in (
                ("include_draft", "纳入草稿"),
                ("exclude_draft", "排除草稿"),
                ("uncertain", "不确定"),
                ("need_full_text", "需全文"),
            ):
                button = QPushButton(text)
                button.setObjectName("metaScreeningDecisionDraftButton")
                button.setProperty("decisionId", decision_id)
                button.setProperty("decisionState", "draft_only")
                button.setProperty("formalActionEnabled", False)
                button.setMinimumHeight(40)
                index = {"include_draft": 0, "exclude_draft": 1, "uncertain": 2, "need_full_text": 3}[decision_id]
                decision_grid.addWidget(button, index // 2, index % 2)
            layout.addLayout(decision_grid)

            reason_label = QLabel("排除原因 / EXCLUSION REASON")
            reason_label.setObjectName("metaScreeningMuted")
            reason_label.setStyleSheet("font-weight: 850; color: #94A3B8;")
            layout.addWidget(reason_label)
            reason = QLabel("请选择排除原因                         v")
            reason.setObjectName("metaScreeningExclusionReason")
            layout.addWidget(reason)
            notes_label = QLabel("补充说明 / ADDITIONAL NOTES")
            notes_label.setObjectName("metaScreeningMuted")
            notes_label.setStyleSheet("font-weight: 850; color: #94A3B8;")
            layout.addWidget(notes_label)
            notes = QLabel("添加决策说明（可选）...\n\n")
            notes.setObjectName("metaScreeningNotesBox")
            notes.setMaximumHeight(70)
            layout.addWidget(notes)

            save_draft = QPushButton("Save Draft Decision")
            save_draft.setObjectName("metaSaveDraftScreeningDecisionButton")
            save_draft.setProperty("actionSemantic", "draft_only")
            save_draft.setProperty("formalActionEnabled", False)
            save_draft.setMinimumHeight(40)
            layout.addWidget(save_draft)
            save_next = QPushButton("保存并下一条 / Save Next")
            save_next.setObjectName("metaScreeningSaveNextButton")
            save_next.setProperty("actionSemantic", "draft_only")
            save_next.setProperty("formalActionEnabled", False)
            save_next.setMinimumHeight(32)
            layout.addWidget(save_next)
            layout.addSpacing(20)

            log = QFrame()
            log.setObjectName("metaScreeningDecisionLog")
            log_layout = QVBoxLayout(log)
            log_layout.setContentsMargins(12, 10, 12, 10)
            log_layout.setSpacing(8)
            log_header = QHBoxLayout()
            log_title = QLabel("决策记录 / Log")
            log_title.setObjectName("metaScreeningTitle")
            log_title.setWordWrap(True)
            log_count = QLabel("3 条记录")
            log_count.setObjectName("metaScreeningMuted")
            log_header.addWidget(log_title)
            log_header.addStretch(1)
            log_header.addWidget(log_count)
            log_layout.addLayout(log_header)
            for badge, semantic, text in (
                ("纳入草稿", "include", "RCT设计，符合纳入标准\n09:15 · Developer"),
                ("排除草稿", "exclude", "结局指标与检索方案不符\n09:32 · Developer"),
                ("需全文", "fulltext", "摘要信息不足，需全文核查\n10:05 · Developer"),
            ):
                row = QLabel(f"{badge}    {text}")
                row.setObjectName(
                    "metaScreeningStatusInclude" if semantic == "include" else ("metaScreeningStatusExclude" if semantic == "exclude" else "metaScreeningStatusFulltext")
                )
                row.setWordWrap(True)
                log_layout.addWidget(row)
            layout.addWidget(log, 1)
            return column

        def _build_fulltext_extraction_panel(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("metaFulltextExtractionPanel")
            frame.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
            frame.setProperty("pageKey", "fulltext_extraction")
            frame.setProperty("semanticKey", PageKey.META_FULLTEXT_EXTRACTION.value)
            frame.setProperty("statusKey", "testing")
            frame.setProperty("extractionState", "draft_extraction")
            frame.setProperty("resultSemanticKey", "no_formal_result")
            frame.setProperty("reportStatusKey", "report.status.draft")
            frame.setProperty("exportGate", "disabled_empty_result")
            frame.setProperty("formalActionEnabled", False)
            frame.setStyleSheet(
                """
                QFrame#metaFulltextExtractionPanel {
                    background: #F5F7FB;
                    border: 0;
                }
                QFrame#metaFulltextStepper,
                QFrame#metaFulltextCard,
                QFrame#metaFulltextSideCard,
                QFrame#metaFulltextTableCard,
                QFrame#metaExtractionDesignBody,
                QFrame#metaFulltextManagementBody {
                    background: #FFFFFF;
                    border: 1px solid #E5E7EB;
                    border-radius: 12px;
                }
                QLabel#metaFulltextTitle,
                QLabel#metaExtractionSectionTitle {
                    color: #0F172A;
                    font-size: 13px;
                    font-weight: 850;
                }
                QLabel#metaFulltextMuted,
                QLabel#metaFulltextSmall,
                QLabel#metaExtractionMuted {
                    color: #64748B;
                    font-size: 11px;
                }
                QLabel#metaFulltextStepDone,
                QLabel#metaFulltextStepCurrent,
                QLabel#metaFulltextStepTodo {
                    color: #94A3B8;
                    font-size: 10px;
                    font-weight: 750;
                }
                QLabel#metaFulltextStepDone,
                QLabel#metaFulltextStepCurrent {
                    color: #2563EB;
                    font-weight: 900;
                }
                QPushButton#metaFulltextExtractionTab {
                    background: transparent;
                    border: 0;
                    border-radius: 0;
                    color: #475569;
                    font-size: 12px;
                    font-weight: 750;
                    padding: 7px 10px;
                }
                QPushButton#metaFulltextExtractionTab:checked {
                    color: #2563EB;
                    border-bottom: 2px solid #2563EB;
                    font-weight: 900;
                }
                QLabel#metaFulltextStatusRow,
                QLabel#metaFulltextSourceRow,
                QLabel#metaExtractionStructureItem,
                QLabel#metaExtractionInfoBox {
                    background: #F8FAFC;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                    color: #334155;
                    font-size: 11px;
                    padding: 8px 10px;
                }
                QLabel#metaFulltextStatusRow[status="ready"],
                QLabel#metaExtractionMatchBadge {
                    background: #ECFDF5;
                    border-color: #BBF7D0;
                    color: #059669;
                    font-weight: 850;
                }
                QLabel#metaFulltextStatusRow[status="pending"] {
                    background: #FFFBEB;
                    border-color: #FDE68A;
                    color: #B45309;
                }
                QLabel#metaFulltextStatusRow[status="missing"] {
                    background: #FEF2F2;
                    border-color: #FECACA;
                    color: #DC2626;
                }
                QLabel#metaExtractionFieldHeader {
                    background: #F8FAFC;
                    border: 0;
                    color: #64748B;
                    font-size: 10px;
                    font-weight: 850;
                    padding: 6px;
                }
                QLabel#metaExtractionFieldCell {
                    background: #FFFFFF;
                    border: 0;
                    border-bottom: 1px solid #F1F5F9;
                    color: #334155;
                    font-size: 10px;
                    padding: 6px;
                }
                QLabel#metaExtractionFieldCell[semantic="section"] {
                    background: #F8FAFC;
                    color: #2563EB;
                    font-weight: 900;
                }
                QLabel#metaExtractionRequiredDot {
                    background: #2563EB;
                    border-radius: 7px;
                    color: #FFFFFF;
                    font-size: 9px;
                    font-weight: 900;
                }
                QLabel#metaExtractionAnalysisDot {
                    background: #22C55E;
                    border-radius: 7px;
                    color: #FFFFFF;
                    font-size: 9px;
                    font-weight: 900;
                }
                QPushButton#metaSaveExtractionDesignButton,
                QPushButton#metaBackToFulltextButton {
                    background: #FFFFFF;
                    border: 1px solid #E5E7EB;
                    border-radius: 9px;
                    color: #334155;
                    font-size: 12px;
                    font-weight: 800;
                    padding: 9px 12px;
                }
                QPushButton#metaConfirmExtractionButton {
                    background: #2563EB;
                    border: 1px solid #2563EB;
                    border-radius: 10px;
                    color: #FFFFFF;
                    font-size: 12px;
                    font-weight: 900;
                    padding: 10px 14px;
                }
                """
            )
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)

            layout.addWidget(self._build_fulltext_stepper())

            tab_row = QHBoxLayout()
            tab_row.setSpacing(14)
            self._fulltext_extraction_tabs: dict[str, QPushButton] = {}
            for index, tab in enumerate(("全文管理", "提取表设计", "提取完成核查", "历史记录")):
                button = QPushButton(tab)
                button.setObjectName("metaFulltextExtractionTab")
                button.setCheckable(True)
                button.setChecked(index == 0)
                button.setMinimumHeight(34)
                button.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
                button.setProperty("pageKey", "fulltext_extraction")
                button.setProperty("tabKey", tab)
                button.clicked.connect(lambda _checked=False, tab_key=tab: self._select_fulltext_extraction_tab(tab_key))
                self._fulltext_extraction_tabs[tab] = button
                tab_row.addWidget(button)
            tab_row.addStretch(1)
            layout.addLayout(tab_row)

            fulltext_status = _readonly_table(
                "metaFulltextStatusPreviewTable",
                ("ref_id", "full_text_state", "extraction_state"),
                (
                    ("REF-001", "file pending", "not_started"),
                    ("REF-002", "needs retrieval", "not_started"),
                    ("REF-004", "not requested", "not_started"),
                ),
            )
            fulltext_status.setProperty("horizontalOverflow", True)
            fulltext_status.setMinimumHeight(92)
            fulltext_status.setVisible(False)

            self._fulltext_management_body = self._build_fulltext_management_body(fulltext_status)
            layout.addWidget(self._fulltext_management_body)

            self._extraction_design_body = self._build_extraction_design_body()
            layout.addWidget(self._extraction_design_body)

            shared_extraction_table = make_extraction_form_table(
                (
                    ExtractionField("first_author", "first_author", "Zhang", "testing", "draft", "manual extraction draft"),
                    ExtractionField("year", "year", "2020", "testing", "draft", "manual extraction draft"),
                    ExtractionField("cancer_type", "cancer_type", "thyroid carcinoma", "testing", "draft", "manual review required"),
                    ExtractionField("effect_measure", "effect_measure", "HR", "testing", "draft", "not a formal pooled input"),
                    ExtractionField("effect_value", "effect_value", "1.48 draft", "testing", "draft", "not a formal effect estimate"),
                    ExtractionField("ci_lower", "ci_lower", "1.05 draft", "testing", "draft", "not a formal effect estimate"),
                    ExtractionField("ci_upper", "ci_upper", "2.10 draft", "testing", "draft", "not a formal effect estimate"),
                ),
                object_name="metaSharedExtractionFormTable",
            )
            shared_extraction_table.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
            shared_extraction_table.setProperty("pageKey", "fulltext_extraction")
            shared_extraction_table.setProperty("extractionState", "draft_extraction")
            shared_extraction_table.setProperty("formalActionEnabled", False)
            shared_extraction_table.setProperty("draftOnly", True)
            shared_extraction_table.setProperty("formalAnalysisInput", False)
            shared_extraction_table.setVisible(False)
            layout.addWidget(shared_extraction_table)

            self._extraction_action_bar = QFrame()
            self._extraction_action_bar.setObjectName("metaExtractionActionBar")
            action_row = QHBoxLayout(self._extraction_action_bar)
            action_row.setContentsMargins(0, 0, 0, 0)
            save = QPushButton("保存提取表设计")
            save.setObjectName("metaSaveExtractionDesignButton")
            save.setMinimumHeight(34)
            save.setEnabled(False)
            mark_draft = QPushButton("Mark as Draft Extracted - adapter needed")
            mark_draft.setObjectName("metaConfirmExtractionButton")
            mark_draft.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
            mark_draft.setProperty("pageKey", "fulltext_extraction")
            mark_draft.setProperty("actionSemantic", "advance_to_extraction_stage")
            mark_draft.setProperty("draftActionSemantic", "draft_extraction_adapter_needed")
            mark_draft.setProperty("formalActionEnabled", False)
            mark_draft.setMinimumHeight(34)
            mark_draft.setEnabled(False)
            back = QPushButton("返回全文管理")
            back.setObjectName("metaBackToFulltextButton")
            back.setMinimumHeight(34)
            back.clicked.connect(lambda _checked=False: self._select_fulltext_extraction_tab("全文管理"))
            action_row.addWidget(save)
            action_row.addStretch(1)
            action_row.addWidget(mark_draft)
            action_row.addWidget(back)
            layout.addWidget(self._extraction_action_bar)
            self._select_fulltext_extraction_tab("全文管理")
            return frame

        def _build_fulltext_stepper(self) -> QFrame:
            stepper = QFrame()
            stepper.setObjectName("metaFulltextStepper")
            layout = QHBoxLayout(stepper)
            layout.setContentsMargins(14, 9, 14, 9)
            layout.setSpacing(8)
            steps = (
                ("✓", "项目首页", "done"),
                ("✓", "研究问题与\nMeta类型", "done"),
                ("✓", "检索策略", "done"),
                ("✓", "文献导入与\n去重", "done"),
                ("✓", "文献筛选", "done"),
                ("6", "全文与数据\n提取", "current"),
                ("7", "质量评价", "todo"),
                ("8", "统计分析", "todo"),
                ("9", "结果与报告", "todo"),
                ("10", "报告导出", "todo"),
            )
            for marker, text, state in steps:
                item = QLabel(f"{marker}\n{text}")
                item.setObjectName(
                    "metaFulltextStepCurrent" if state == "current" else ("metaFulltextStepDone" if state == "done" else "metaFulltextStepTodo")
                )
                item.setAlignment(Qt.AlignCenter)
                item.setMinimumWidth(70)
                layout.addWidget(item, 1)
            return stepper

        def _build_fulltext_management_body(self, fulltext_status: QTableWidget) -> QFrame:
            body = QFrame()
            body.setObjectName("metaFulltextManagementBody")
            body.setFixedHeight(560)
            layout = QHBoxLayout(body)
            layout.setContentsMargins(12, 12, 12, 12)
            layout.setSpacing(12)

            queue = QFrame()
            queue.setObjectName("metaFulltextCard")
            queue.setFixedWidth(280)
            queue_layout = QVBoxLayout(queue)
            queue_layout.setContentsMargins(14, 12, 14, 12)
            queue_layout.setSpacing(9)
            title = QLabel("全文管理 / Full-text Management")
            title.setObjectName("metaFulltextTitle")
            queue_layout.addWidget(title)
            for text, status in (
                ("REF-001  file pending\nCAR-T B-cell lymphoma review", "pending"),
                ("REF-002  needs retrieval\nPD-L1 gastric cancer meta-analysis", "missing"),
                ("REF-004  ready for extraction\nCirculating adipokines and cancer risk", "ready"),
            ):
                row = QLabel(text)
                row.setObjectName("metaFulltextStatusRow")
                row.setProperty("status", status)
                row.setWordWrap(True)
                row.setMinimumHeight(62)
                queue_layout.addWidget(row)
            upload = QLabel("+ 绑定 PDF / HTML 文件")
            upload.setObjectName("metaFulltextSourceRow")
            upload.setStyleSheet("border-style: dashed; color: #2563EB;")
            upload.setAlignment(Qt.AlignCenter)
            upload.setMinimumHeight(44)
            queue_layout.addWidget(upload)
            queue_layout.addWidget(fulltext_status)
            queue_layout.addStretch(1)
            layout.addWidget(queue)

            preview = QFrame()
            preview.setObjectName("metaFulltextTableCard")
            preview_layout = QVBoxLayout(preview)
            preview_layout.setContentsMargins(14, 12, 14, 12)
            preview_layout.setSpacing(10)
            preview_header = QHBoxLayout()
            preview_title = QLabel("全文预览 / Full-text Preview")
            preview_title.setObjectName("metaFulltextTitle")
            state = QLabel("mockup-only / draft extraction")
            state.setObjectName("metaExtractionMatchBadge")
            preview_header.addWidget(preview_title)
            preview_header.addStretch(1)
            preview_header.addWidget(state)
            preview_layout.addLayout(preview_header)
            meta = QLabel("REF-001 · Blood Cancer Journal · 2022 · PMID 35773265")
            meta.setObjectName("metaFulltextMuted")
            preview_layout.addWidget(meta)
            for heading, content in (
                ("Abstract", "CAR-T therapy has emerged as a transformative treatment for relapsed or refractory B-cell non-Hodgkin lymphoma. This article is queued for manual evidence extraction."),
                ("Methods", "Eligible studies were summarized by response and safety endpoints. Extraction remains reviewer-controlled."),
                ("Extraction readiness", "PDF/HTML binding is pending for one record; no production data extraction is generated from this preview."),
            ):
                section = QLabel(f"{heading}\n{content}")
                section.setObjectName("metaFulltextSourceRow")
                section.setWordWrap(True)
                section.setMinimumHeight(78)
                preview_layout.addWidget(section)
            preview_layout.addStretch(1)
            layout.addWidget(preview, 1)

            side = QFrame()
            side.setObjectName("metaFulltextSideCard")
            side.setFixedWidth(210)
            side_layout = QVBoxLayout(side)
            side_layout.setContentsMargins(14, 12, 14, 12)
            side_layout.setSpacing(10)
            side_title = QLabel("全文状态 / Readiness")
            side_title.setObjectName("metaFulltextTitle")
            side_layout.addWidget(side_title)
            for text, status in (
                ("全文文件齐备度\n1 / 3 ready", "pending"),
                ("数据提取准备\nmanual extraction draft", "ready"),
                ("质量追踪\nmanual review required", "pending"),
                ("边界\nadapter disabled; reviewer controlled", "missing"),
            ):
                row = QLabel(text)
                row.setObjectName("metaFulltextStatusRow")
                row.setProperty("status", status)
                row.setWordWrap(True)
                side_layout.addWidget(row)
            next_design = QPushButton("进入提取表设计")
            next_design.setObjectName("metaSaveExtractionDesignButton")
            next_design.setProperty("formalActionEnabled", False)
            next_design.clicked.connect(lambda _checked=False: self._select_fulltext_extraction_tab("提取表设计"))
            side_layout.addStretch(1)
            side_layout.addWidget(next_design)
            layout.addWidget(side)
            return body

        def _build_extraction_design_body(self) -> QFrame:
            body = QFrame()
            body.setObjectName("metaExtractionDesignBody")
            body.setFixedHeight(560)
            layout = QHBoxLayout(body)
            layout.setContentsMargins(12, 12, 12, 12)
            layout.setSpacing(12)

            structure = QFrame()
            structure.setObjectName("metaFulltextCard")
            structure.setFixedWidth(180)
            structure_layout = QVBoxLayout(structure)
            structure_layout.setContentsMargins(12, 10, 12, 10)
            structure_layout.setSpacing(8)
            structure_title = QLabel("提取表结构")
            structure_title.setObjectName("metaExtractionSectionTitle")
            structure_layout.addWidget(structure_title)
            structure_hint = QLabel("点击切换查看或编辑各部分字段")
            structure_hint.setObjectName("metaExtractionMuted")
            structure_hint.setWordWrap(True)
            structure_layout.addWidget(structure_hint)
            for section, count, active in (
                ("研究基本信息", "6", True),
                ("研究对象与分组", "4", False),
                ("干预 / 暴露", "3", False),
                ("对照措施", "2", False),
                ("结局指标", "5", False),
                ("效应量数据（二分类）", "8", False),
                ("备注与来源", "3", False),
                ("复核字段", "2", False),
            ):
                label = QLabel(f"{section}                                      {count}")
                label.setObjectName("metaExtractionStructureItem")
                label.setProperty("sectionKey", section)
                if active:
                    label.setStyleSheet("background: #EAF3FF; border-color: #BFDBFE; color: #2563EB; font-weight: 900;")
                structure_layout.addWidget(label)
            add = QLabel("+  新增自定义字段")
            add.setObjectName("metaExtractionStructureItem")
            add.setStyleSheet("border-style: dashed; color: #2563EB;")
            add.setAlignment(Qt.AlignCenter)
            structure_layout.addWidget(add)
            layout.addWidget(structure)

            fields = QFrame()
            fields.setObjectName("metaFulltextTableCard")
            fields.setFixedWidth(560)
            fields_layout = QVBoxLayout(fields)
            fields_layout.setContentsMargins(14, 12, 14, 12)
            fields_layout.setSpacing(8)
            title_row = QHBoxLayout()
            fields_title = QLabel("当前提取表字段（Binary Outcome Meta 专用）")
            fields_title.setObjectName("metaExtractionSectionTitle")
            match = QLabel("与当前 Meta 类型匹配")
            match.setObjectName("metaExtractionMatchBadge")
            title_row.addWidget(fields_title)
            title_row.addWidget(match)
            title_row.addStretch(1)
            for text in ("导入", "保存", "预览"):
                action = QLabel(text)
                action.setObjectName("metaFulltextSourceRow")
                action.setStyleSheet("background: #FFFFFF; color: #2563EB;")
                title_row.addWidget(action)
            fields_layout.addLayout(title_row)
            legacy_contract = QLabel("当前提取表字段（Binary Outcome Meta 专用）")
            legacy_contract.setObjectName("metaExtractionLegacyContractLabel")
            legacy_contract.setProperty("legacyCompatibilityOnly", True)
            legacy_contract.setVisible(False)
            fields_layout.addWidget(legacy_contract)
            field_grid = QGridLayout()
            field_grid.setHorizontalSpacing(0)
            field_grid.setVerticalSpacing(0)
            for column, header in enumerate(("序号", "字段名称", "字段含义 / 说明", "必填", "数据类型", "来源提示", "用于分析", "操作")):
                header_label = QLabel(header)
                header_label.setObjectName("metaExtractionFieldHeader")
                field_grid.addWidget(header_label, 0, column)
            rows = (
                ("一、研究基本信息", "", "", "", "", "", "", ""),
                ("1", "研究 ID", "本研究在本项目中的唯一编号", "✓", "文本 Text", "-", "", "edit"),
                ("2", "first_author", "论文第一作者", "✓", "文本 Text", "来源首页", "", "edit"),
                ("3", "year", "论文发表年份", "✓", "数字 Number", "来源首页", "", "edit"),
                ("4", "cancer_type", "研究所处国家或地区", "✓", "下拉选择 Select", "方法部分", "✓", "edit"),
                ("5", "研究设计", "研究类型（RCT、队列研究等）", "✓", "下拉选择 Select", "-", "✓", "edit"),
                ("6", "样本量（总样本）", "研究纳入的总样本量", "", "数字 Number", "-", "✓", "edit"),
                ("二、研究对象与分组", "", "", "", "", "", "", ""),
                ("7", "marker_name", "adiponectin / ADIPOQ", "✓", "文本 Text", "结果部分", "✓", "edit"),
                ("8", "effect_measure", "HR / OR / RR", "✓", "Select", "表格", "✓", "edit"),
                ("9", "effect_value", "1.48 mockup-only / draft extraction", "✓", "Number", "表格", "✓", "edit"),
                ("10", "ci_lower", "1.05 mockup-only / draft extraction", "✓", "Number", "表格", "✓", "edit"),
                ("11", "ci_upper", "2.10 mockup-only / draft extraction", "✓", "Number", "表格", "✓", "edit"),
                ("12", "adjusted_model", "multivariable", "", "Text", "方法", "✓", "edit"),
                ("13", "outcome_name", "overall survival", "✓", "Text", "结果", "✓", "edit"),
            )
            for row, values in enumerate(rows, start=1):
                section_row = values[1] == ""
                for column, value in enumerate(values):
                    label = QLabel(value)
                    label.setObjectName("metaExtractionFieldCell")
                    if section_row:
                        label.setProperty("semantic", "section")
                    label.setWordWrap(False)
                    label.setMinimumHeight(28)
                    field_grid.addWidget(label, row, column)
            fields_layout.addLayout(field_grid)
            legend = QLabel("必填字段    非必填字段    用于统计分析                         共 8 个部分，33 个字段，必填字段 25 个")
            legend.setObjectName("metaExtractionMuted")
            fields_layout.addWidget(legend)
            layout.addWidget(fields, 1)

            side = QFrame()
            side.setObjectName("metaFulltextSideCard")
            side.setFixedWidth(172)
            side_layout = QVBoxLayout(side)
            side_layout.setContentsMargins(12, 10, 12, 10)
            side_layout.setSpacing(10)
            info_title = QLabel("提取表信息")
            info_title.setObjectName("metaExtractionSectionTitle")
            side_layout.addWidget(info_title)
            for text in (
                "提取表名称\n二分类结局（RCT）提取表 v2.1",
                "适用研究类型\n随机对照试验（RCT）",
                "创建时间\n2024-05-20 14:25",
                "更新时间\n2024-05-20 14:25",
                "创建者\nResearcher（她）",
                "备注\n-",
            ):
                box = QLabel(text)
                box.setObjectName("metaExtractionInfoBox")
                box.setWordWrap(True)
                side_layout.addWidget(box)
            completeness = QLabel("完整性检查\n100%\n配置完整\n必填字段已配置 25/25\n建议字段已配置 8/8\n与 Meta 类型匹配")
            completeness.setObjectName("metaExtractionMatchBadge")
            completeness.setWordWrap(True)
            side_layout.addWidget(completeness)
            side_layout.addStretch(1)
            layout.addWidget(side)
            return body

        def _build_risk_of_bias_panel(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("metaRiskOfBiasRuntimePanel")
            frame.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
            frame.setProperty("pageKey", "quality_assessment")
            frame.setProperty("runtimeStatus", "planned")
            frame.setProperty("processingMode", "english_first")
            frame.setProperty("aiBoundary", "advisory_only")
            frame.setProperty("riskOfBiasState", "preview_in_progress")
            frame.setProperty("resultSemanticKey", "no_formal_result")
            frame.setProperty("reportStatusKey", "report.status.draft")
            frame.setProperty("exportGate", "disabled_empty_result")
            frame.setProperty("formalActionEnabled", False)
            frame.setStyleSheet("QFrame#metaRiskOfBiasRuntimePanel { border: 1px solid #D6E0EA; border-radius: 8px; background: #FFFFFF; }")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(10)

            title = QLabel("Risk of Bias / 质量评价预览")
            title.setObjectName("metaRiskOfBiasRuntimeTitle")
            title.setStyleSheet("font-weight: 750;")
            layout.addWidget(title)

            rob = _readonly_table(
                "metaRiskOfBiasDomainTable",
                ("tool / domain", "draft state", "preview note"),
                (
                    ("NOS Selection", "Draft", "preview score requires final confirmation"),
                    ("NOS Comparability", "In progress", "preview score requires final confirmation"),
                    ("NOS Outcome", "Draft", "preview score requires final confirmation"),
                    ("ROBINS-I Confounding", "not_started", "tool suggestion only"),
                    ("QUADAS-2", "not_applicable_for_current_type", "depends on diagnostic type"),
                ),
            )
            rob.setMinimumHeight(150)
            layout.addWidget(rob)

            score = QLabel("Preview / draft only: no automatic RoB final judgement and no formal quality score.")
            score.setObjectName("metaRiskOfBiasPreviewScoreNotice")
            score.setProperty("riskOfBiasState", "preview_only")
            score.setWordWrap(True)
            score.setStyleSheet("border: 1px solid #F5D899; border-radius: 6px; padding: 8px; background: #FFF7E6;")
            layout.addWidget(score)

            save = QPushButton("Save RoB Draft - adapter needed")
            save.setObjectName("metaSaveRiskOfBiasDraftButton")
            save.setProperty("actionSemantic", "adapter_needed")
            save.setProperty("formalActionEnabled", False)
            save.setEnabled(False)
            save.setMinimumHeight(34)
            layout.addWidget(save)
            return frame

        def _build_result_review_panel(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("metaResultReviewRuntimePanel")
            frame.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
            frame.setProperty("pageKey", "result_report")
            frame.setProperty("runtimeStatus", "shell_only")
            frame.setProperty("resultSemanticKey", "testing_summary_only")
            frame.setProperty("formalResultSemanticKey", "no_formal_result")
            frame.setProperty("reportStatusKey", "report.status.draft")
            frame.setProperty("reportReadyState", "blocked")
            frame.setProperty("exportGate", "disabled_empty_result")
            frame.setProperty("fileWriteAllowed", False)
            frame.setProperty("formalActionEnabled", False)
            frame.setStyleSheet(
                """
                QFrame#metaResultReviewRuntimePanel {
                    background: #F5F7FB;
                    border: 0;
                }
                QFrame#metaExportReportStepper,
                QFrame#metaExportReportCard,
                QFrame#metaExportReportGateCard,
                QFrame#metaExportReportBottomCard {
                    background: #FFFFFF;
                    border: 1px solid #E5E7EB;
                    border-radius: 12px;
                }
                QLabel#metaExportReportTitle {
                    color: #0F172A;
                    font-size: 13px;
                    font-weight: 850;
                }
                QLabel#metaExportReportMuted {
                    color: #64748B;
                    font-size: 11px;
                }
                QLabel#metaExportReportStepDone,
                QLabel#metaExportReportStepCurrent,
                QLabel#metaExportReportStepBlocked {
                    color: #16A34A;
                    font-size: 10px;
                    font-weight: 900;
                }
                QLabel#metaExportReportStepBlocked {
                    color: #EF4444;
                }
                QLabel#metaExportReportStepCurrent {
                    color: #2563EB;
                }
                QLabel#metaReportTypeItem {
                    background: #FFFFFF;
                    border: 1px solid transparent;
                    border-radius: 9px;
                    color: #334155;
                    font-size: 11px;
                    padding: 9px 10px;
                }
                QLabel#metaReportTypeItem[selected="true"] {
                    background: #EAF3FF;
                    border-color: #BFDBFE;
                }
                QLabel#metaExportFormatBadge {
                    background: #EFF6FF;
                    border-radius: 7px;
                    color: #2563EB;
                    font-size: 10px;
                    font-weight: 850;
                    padding: 3px 6px;
                }
                QLabel#metaExportPreviewRow {
                    background: #FFFFFF;
                    border: 0;
                    border-bottom: 1px solid #F1F5F9;
                    color: #334155;
                    font-size: 11px;
                    padding: 7px 8px;
                }
                QLabel#metaExportStatusDone {
                    background: #DCFCE7;
                    border: 1px solid #86EFAC;
                    border-radius: 7px;
                    color: #059669;
                    font-size: 10px;
                    font-weight: 850;
                    padding: 4px 7px;
                }
                QLabel#metaExportStatusDraft {
                    background: #FEF3C7;
                    border: 1px solid #FACC15;
                    border-radius: 7px;
                    color: #B45309;
                    font-size: 10px;
                    font-weight: 850;
                    padding: 4px 7px;
                }
                QLabel#metaExportStatusDisabled {
                    background: #F3F4F6;
                    border: 1px solid #E5E7EB;
                    border-radius: 7px;
                    color: #9CA3AF;
                    font-size: 10px;
                    font-weight: 850;
                    padding: 4px 7px;
                }
                QLabel#metaExportGateRow {
                    background: #FFFFFF;
                    border: 0;
                    border-bottom: 1px solid #FEE2E2;
                    color: #334155;
                    font-size: 11px;
                    padding: 7px 8px;
                }
                QLabel#metaExportGateHeader,
                QLabel#metaExportFinalBlocked {
                    background: #FEF2F2;
                    border: 1px solid #FECACA;
                    border-radius: 9px;
                    color: #DC2626;
                    font-size: 12px;
                    font-weight: 900;
                    padding: 9px 10px;
                }
                QLabel#metaExportSettingBox {
                    background: #F8FAFC;
                    border: 1px solid #E5E7EB;
                    border-radius: 9px;
                    color: #64748B;
                    font-size: 11px;
                    padding: 8px 10px;
                }
                QLabel#metaResultReviewHumanReviewNotice {
                    background: #FFFBEB;
                    border: 1px solid #FDE68A;
                    border-radius: 10px;
                    color: #B45309;
                    font-size: 11px;
                    padding: 9px 10px;
                }
                QPushButton#metaGenerateReportDisabledButton {
                    background: #F3F4F6;
                    border: 1px solid #E5E7EB;
                    border-radius: 10px;
                    color: #9CA3AF;
                    font-size: 12px;
                    font-weight: 850;
                    padding: 10px 12px;
                }
                """
            )
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(12)
            layout.addWidget(self._build_export_report_stepper())

            review_notice = QLabel("人工复核集中在此页面：前置草稿、提取和 RoB 预览不能升级为正式结果。")
            review_notice.setObjectName("metaResultReviewHumanReviewNotice")
            review_notice.setProperty("reviewBoundary", "human_review_required")
            review_notice.setWordWrap(True)

            readiness = _readonly_table(
                "metaResultReadinessSummaryTable",
                ("gate", "state", "reason"),
                (
                    ("result_semantic", "testing_summary_only / no_formal_result", "no formal pairwise result"),
                    ("formal_pooled_effect", "none", "Pairwise Meta executor not enabled"),
                    ("forest_plot", "disabled_boundary", "no formal result artifact"),
                    ("heterogeneity", "none", "no computed model"),
                    ("publication_bias", "none", "no computed model"),
                    ("ai_suggestion", "advisory_only", "reviewer remains authority"),
                ),
            )
            readiness.setMinimumHeight(150)
            readiness.setVisible(False)

            forest_placeholder = make_plot_placeholder(
                title="Forest plot placeholder / 森林图占位",
                plot_type="forest_plot",
                message="Formal synthesis estimates and figure previews are disabled in UI-D5.",
                status_key="blocked",
                semantic_state="blocked",
                object_name="metaForestPlotPlaceholder",
            )
            forest_placeholder.setVisible(False)

            pairwise = _readonly_table(
                "metaPairwiseInputPreviewTable",
                ("study_id", "effect_type", "effect_value", "ci_lower", "ci_upper", "readiness"),
                (
                    ("STUDY-001", "HR", "1.48 draft", "1.05 draft", "2.10 draft", "preflight_only"),
                    ("STUDY-002", "HR", "1.21 draft", "0.88 draft", "1.67 draft", "warning_missing_adjustment"),
                    ("STUDY-003", "OR", "1.76 draft", "1.10 draft", "2.82 draft", "incompatible_effect_type"),
                ),
            )
            pairwise.setObjectName("metaPairwiseInputPreviewTable")
            pairwise.setProperty("previewOnly", True)
            pairwise.setMinimumHeight(120)
            pairwise_card = make_preview_card(
                title="Pairwise input preview / 配对输入预览",
                preview_widget=pairwise,
                status_key="preflight_only",
                semantic_state="preflight_only",
                caption="Draft extraction values are shown for review only; no summary estimate is computed.",
                object_name="metaPairwiseInputPreviewCard",
            )
            pairwise_card.setVisible(False)

            blockers = _readonly_table(
                "metaReportReadyBlockerChecklist",
                ("blocker", "state"),
                (
                    ("research question/type confirmation", "missing_or_draft"),
                    ("search strategy", "draft"),
                    ("references", "not_finalized"),
                    ("screening", "not_final"),
                    ("extraction", "not_final"),
                    ("risk of bias", "not_final"),
                    ("pairwise input", "not_formal"),
                    ("formal result", "missing"),
                ),
            )
            blockers.setMinimumHeight(162)
            blockers.setVisible(False)

            generate = QPushButton("Generate Report disabled")
            generate.setObjectName("metaGenerateReportDisabledButton")
            generate.setProperty("actionSemantic", "disabled_report_gate")
            generate.setProperty("formalActionEnabled", False)
            generate.setProperty("fileWriteAllowed", False)
            generate.setEnabled(False)
            generate.setMinimumHeight(34)

            main = QHBoxLayout()
            main.setSpacing(12)
            main.addWidget(self._build_export_report_type_card())
            main.addWidget(self._build_export_content_preview_card(), 1)
            main.addWidget(self._build_export_gate_status_card(generate))
            layout.addLayout(main)

            bottom = QHBoxLayout()
            bottom.setSpacing(12)
            bottom.addWidget(self._build_export_settings_card(), 1)
            bottom.addWidget(self._build_export_history_card(), 1)
            layout.addLayout(bottom)
            layout.addWidget(review_notice)

            layout.addWidget(readiness)
            layout.addWidget(forest_placeholder)
            layout.addWidget(pairwise_card)
            layout.addWidget(blockers)
            return frame

        def _build_export_report_stepper(self) -> QFrame:
            stepper = QFrame()
            stepper.setObjectName("metaExportReportStepper")
            layout = QHBoxLayout(stepper)
            layout.setContentsMargins(14, 9, 14, 9)
            layout.setSpacing(7)
            steps = (
                ("✓", "项目首页", "done"),
                ("✓", "问题与类型", "done"),
                ("✓", "检索策略", "done"),
                ("✓", "文献导入", "done"),
                ("✓", "去重", "done"),
                ("✓", "筛选", "done"),
                ("✓", "全文与提取", "done"),
                ("✓", "偏倚风险", "done"),
                ("✓", "成对Meta输入", "done"),
                ("✓", "结果复核", "done"),
                ("✕", "报告门控", "blocked"),
                ("12", "导出", "current"),
            )
            for marker, text, state in steps:
                item = QLabel(f"{marker}\n{text}")
                item.setObjectName(
                    "metaExportReportStepCurrent" if state == "current" else ("metaExportReportStepBlocked" if state == "blocked" else "metaExportReportStepDone")
                )
                item.setAlignment(Qt.AlignCenter)
                item.setMinimumWidth(58)
                layout.addWidget(item, 1)
            return stepper

        def _build_export_report_type_card(self) -> QFrame:
            card = QFrame()
            card.setObjectName("metaExportReportCard")
            card.setFixedWidth(260)
            card.setFixedHeight(455)
            layout = QVBoxLayout(card)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(9)
            title = QLabel("报告类型 / Report Type")
            title.setObjectName("metaExportReportTitle")
            layout.addWidget(title)
            tabs = QHBoxLayout()
            for text, active in (("系统模板", True), ("自定义模板", False), ("输出片段", False)):
                tab = QLabel(text)
                tab.setObjectName("metaExportReportMuted")
                tab.setAlignment(Qt.AlignCenter)
                if active:
                    tab.setStyleSheet("color: #2563EB; border-bottom: 2px solid #2563EB; padding: 6px; font-weight: 900;")
                tabs.addWidget(tab, 1)
            layout.addLayout(tabs)
            for title_text, subtitle, fmt, selected in (
                ("Meta 分析完整报告", "Full Meta-Analysis Report", "DOCX", False),
                ("方法学与流程报告", "Methods & Process Report", "DOCX", False),
                ("数据提取表", "Data Extraction Table", "XLSX", False),
                ("成对比较结果表", "Paired Comparison Results", "XLSX", False),
                ("PRISMA 流程图", "PRISMA Flowchart", "PNG/SVG", False),
                ("汇总包", "Summary Package", "ZIP", True),
            ):
                item = QLabel(f"{title_text}                                      {fmt}\n{subtitle}")
                item.setObjectName("metaReportTypeItem")
                item.setProperty("selected", selected)
                item.setWordWrap(True)
                layout.addWidget(item)
            footer = QLabel("导出已禁用，通过 Gate 后解锁")
            footer.setObjectName("metaExportReportMuted")
            footer.setStyleSheet("color: #9CA3AF;")
            layout.addStretch(1)
            layout.addWidget(footer)
            return card

        def _build_export_content_preview_card(self) -> QFrame:
            card = QFrame()
            card.setObjectName("metaExportReportCard")
            card.setFixedWidth(410)
            card.setFixedHeight(455)
            layout = QVBoxLayout(card)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(8)
            header = QHBoxLayout()
            title = QLabel("导出内容预览 / Export Content Preview")
            title.setObjectName("metaExportReportTitle")
            draft = QLabel("仅显示草稿状态")
            draft.setObjectName("metaExportReportMuted")
            header.addWidget(title)
            header.addStretch(1)
            header.addWidget(draft)
            layout.addLayout(header)
            column_header = QLabel("内容项 / CONTENT                                      状态 / STATUS                         说明")
            column_header.setObjectName("metaExportReportMuted")
            column_header.setStyleSheet("font-weight: 850; color: #64748B;")
            layout.addWidget(column_header)
            rows = (
                ("方法与流程 / Methods", "已完成草稿", "done", "可纳入报告"),
                ("检索策略 / Search", "已完成草稿", "done", "可纳入报告"),
                ("文献信息 / Literature", "已导入草稿", "info", "待人工确认"),
                ("筛选结果 / Screening", "草稿", "draft", "需完善"),
                ("数据提取表 / Extraction", "草稿", "draft", "需完善"),
                ("偏倚风险 / Risk of Bias", "已完成草稿", "done", "可纳入报告"),
                ("成对输入 / Paired Input", "草稿", "draft", "需完善"),
                ("Meta 分析结果 / Results", "不可用", "disabled", "Gate 未过"),
                ("图表与森林图 / Plots", "不可用", "disabled", "Gate 未过"),
                ("发表偏倚 / Bias", "不可用", "disabled", "Gate 未过"),
            )
            for name, status, semantic, note in rows:
                row = QHBoxLayout()
                name_label = QLabel(name)
                name_label.setObjectName("metaExportPreviewRow")
                name_label.setMaximumHeight(31)
                name_label.setMinimumWidth(175)
                status_label = QLabel(status)
                status_label.setObjectName(
                    "metaExportStatusDone" if semantic in {"done", "info"} else ("metaExportStatusDraft" if semantic == "draft" else "metaExportStatusDisabled")
                )
                status_label.setAlignment(Qt.AlignCenter)
                status_label.setFixedWidth(95)
                status_label.setMaximumHeight(31)
                note_label = QLabel(note)
                note_label.setObjectName("metaExportPreviewRow")
                note_label.setMaximumHeight(31)
                row.addWidget(name_label)
                row.addWidget(status_label)
                row.addWidget(note_label, 1)
                layout.addLayout(row)
            warning = QLabel("⚠ 3 项内容不可用，需先通过 Report-ready Gate")
            warning.setObjectName("metaExportReportMuted")
            warning.setStyleSheet("background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 8px; color: #B45309; padding: 7px;")
            layout.addWidget(warning)
            return card

        def _build_export_gate_status_card(self, generate: QPushButton) -> QFrame:
            card = QFrame()
            card.setObjectName("metaExportReportGateCard")
            card.setFixedWidth(250)
            card.setFixedHeight(455)
            layout = QVBoxLayout(card)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(8)
            header = QLabel("报告门控未通过")
            header.setObjectName("metaExportGateHeader")
            header.setMinimumHeight(46)
            header.setMaximumHeight(52)
            header.setAlignment(Qt.AlignCenter)
            layout.addWidget(header)
            column_header = QLabel("检查项                                      状态")
            column_header.setObjectName("metaExportReportMuted")
            column_header.setStyleSheet("font-weight: 850;")
            layout.addWidget(column_header)
            checks = (
                ("研究问题确认", False),
                ("检索策略确认", False),
                ("去重完成确认", True),
                ("筛选完成确认", False),
                ("提取完成确认", False),
                ("偏倚风险确认", False),
                ("成对输入确认", False),
                ("分析一致性", False),
                ("结果可报告性", False),
            )
            for text, passed in checks:
                row = QLabel(f"{text}                                      {'✓' if passed else '✕'}")
                row.setObjectName("metaExportGateRow")
                row.setWordWrap(False)
                row.setMaximumHeight(34)
                layout.addWidget(row)
            final = QLabel("最终结果 / Final Result                                      ✕")
            final.setObjectName("metaExportFinalBlocked")
            final.setMinimumHeight(34)
            final.setAlignment(Qt.AlignCenter)
            layout.addWidget(final)
            generate.setText("Export Disabled")
            layout.addWidget(generate)
            footer = QLabel("8/9 checks failed · 需完成所有检查项")
            footer.setObjectName("metaExportReportMuted")
            footer.setAlignment(Qt.AlignCenter)
            layout.addWidget(footer)
            return card

        def _build_export_settings_card(self) -> QFrame:
            card = QFrame()
            card.setObjectName("metaExportReportBottomCard")
            card.setFixedHeight(126)
            layout = QVBoxLayout(card)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(8)
            header = QHBoxLayout()
            title = QLabel("导出设置 / Export Settings")
            title.setObjectName("metaExportReportTitle")
            disabled = QLabel("已禁用")
            disabled.setObjectName("metaExportReportMuted")
            disabled.setStyleSheet("background: #F3F4F6; border-radius: 7px; padding: 4px 8px;")
            header.addWidget(title)
            header.addStretch(1)
            header.addWidget(disabled)
            layout.addLayout(header)
            grid = QGridLayout()
            grid.setHorizontalSpacing(10)
            grid.setVerticalSpacing(8)
            for index, text in enumerate(
                (
                    "文件格式 / File Format\nDOCX (.docx)",
                    "包含级别 / Include Level\n完整报告 Full Report",
                    "报告语言 / Language\n中英双语 Bilingual",
                    "引用格式 / Citation Format\nVancouver Style",
                )
            ):
                box = QLabel(text)
                box.setObjectName("metaExportSettingBox")
                grid.addWidget(box, index // 2, index % 2)
            layout.addLayout(grid)
            return card

        def _build_export_history_card(self) -> QFrame:
            card = QFrame()
            card.setObjectName("metaExportReportBottomCard")
            card.setFixedHeight(126)
            layout = QVBoxLayout(card)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(8)
            title = QLabel("导出历史 / Export History")
            title.setObjectName("metaExportReportTitle")
            layout.addWidget(title)
            empty = QLabel("暂无导出记录\n通过 Report-ready Gate 后才记录正式导出历史\nFormal export history logged after gate passes")
            empty.setObjectName("metaExportReportMuted")
            empty.setAlignment(Qt.AlignCenter)
            empty.setWordWrap(True)
            layout.addWidget(empty, 1)
            return card

        def _build_report_export_gate_panel(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("metaReportExportGateRuntimePanel")
            frame.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
            frame.setProperty("pageKey", "report_export")
            frame.setProperty("runtimeStatus", "shell_only")
            frame.setProperty("resultSemanticKey", "no_formal_result")
            frame.setProperty("reportStatusKey", "report.status.draft")
            frame.setProperty("reportReadyState", "blocked")
            frame.setProperty("exportGate", "disabled_empty_result")
            frame.setProperty("fileWriteAllowed", False)
            frame.setProperty("formalActionEnabled", False)
            frame.setStyleSheet("QFrame#metaReportExportGateRuntimePanel { border: 1px solid #D6E0EA; border-radius: 8px; background: #FFFFFF; }")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(10)

            title = QLabel("Report Export / 报告导出门控")
            title.setObjectName("metaReportExportGateRuntimeTitle")
            title.setStyleSheet("font-weight: 750;")
            layout.addWidget(title)

            shared_gate = make_export_gate_panel(
                title="Shared export gate / 共享导出门控",
                checks=(
                    ExportGateCheck("formal_result", "Formal pooled result", False, "No formal pairwise pooled result exists.", "blocked"),
                    ExportGateCheck("report_ready", "Report-ready package", False, "Report-ready systematic review package is not enabled.", "report_disabled"),
                    ExportGateCheck("export_adapter", "Export adapter", False, "Export adapter is not connected in the runtime shell.", "adapter_needed"),
                ),
                formats=(
                    ExportFormatAction("export.format.docx", "DOCX disabled", "Report-ready gate is not satisfied.", "export_disabled"),
                    ExportFormatAction("export.format.html", "HTML disabled", "Report-ready gate is not satisfied.", "export_disabled"),
                    ExportFormatAction("export.format.pdf", "PDF disabled", "Report-ready gate is not satisfied.", "export_disabled"),
                ),
                artifact_exists=False,
                object_name="metaSharedExportGatePanel",
            )
            shared_gate.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
            shared_gate.setProperty("pageKey", "report_export")
            layout.addWidget(shared_gate)

            gate = _readonly_table(
                "metaReportExportGateReasonTable",
                ("gate", "state", "reason"),
                (
                    ("result", "disabled", "no formal result"),
                    ("report", "disabled", "report not ready"),
                    ("adapter", "disabled", "export adapter missing"),
                    ("file_write", "false", "no file write in gated shell"),
                ),
            )
            gate.setMinimumHeight(112)
            layout.addWidget(gate)

            format_row = QHBoxLayout()
            for export_format in ("DOCX", "HTML", "PDF", "CSV", "XLSX", "ZIP"):
                button = QPushButton(f"{export_format} disabled")
                button.setObjectName("metaExportFormatDisabledButton")
                button.setProperty("exportFormat", export_format)
                button.setProperty("actionSemantic", "disabled_export_gate")
                button.setProperty("formalActionEnabled", False)
                button.setProperty("fileWriteAllowed", False)
                button.setEnabled(False)
                button.setMinimumHeight(34)
                format_row.addWidget(button)
            layout.addLayout(format_row)

            future = QLabel("Export will be enabled after gate.")
            future.setObjectName("metaExportAfterGateNotice")
            future.setProperty("exportGate", "disabled_empty_result")
            future.setWordWrap(True)
            layout.addWidget(future)
            return frame

        def _select_fulltext_extraction_tab(self, tab_key: str) -> None:
            for key, button in getattr(self, "_fulltext_extraction_tabs", {}).items():
                button.setChecked(key == tab_key)
            show_extraction_design = tab_key == "提取表设计"
            if hasattr(self, "_fulltext_management_body"):
                self._fulltext_management_body.setVisible(tab_key == "全文管理")
            if hasattr(self, "_extraction_design_body"):
                self._extraction_design_body.setVisible(show_extraction_design)
            if hasattr(self, "_extraction_action_bar"):
                self._extraction_action_bar.setVisible(show_extraction_design)

        def _sync_target_interaction_state(self) -> None:
            pages = {page.key: page for page in meta_target_ia_pages()}
            current = pages[self._current_target_page_key]
            if hasattr(self, "_workspace_title_label"):
                if self._current_target_page_key == "question_meta_type":
                    self._workspace_title_label.setText("Meta Analysis / 研究问题与 Meta 类型")
                    self._workspace_subtitle_label.setText("定义研究问题，选择适合的 Meta 分析类型，系统将为您推荐后续流程与方法。")
                elif self._current_target_page_key == "search_strategy":
                    self._workspace_title_label.setText("检索策略 / Search Strategy Builder")
                    self._workspace_subtitle_label.setText("构建英文检索式，管理检索数据库与字段，当前为 Developer Preview。")
                elif self._current_target_page_key == "screening":
                    self._workspace_title_label.setText("筛选 / Screening Workspace")
                    self._workspace_subtitle_label.setText("标题与摘要筛选、人工决策、AI 建议仅供参考。")
                elif self._current_target_page_key == "fulltext_extraction":
                    self._workspace_title_label.setText("全文与数据提取 / Full-text & Extraction")
                    self._workspace_subtitle_label.setText("管理全文获取状态、进行数据提取与质控追踪，确保数据提取逻辑和可追溯。")
                elif self._current_target_page_key == "result_report":
                    self._workspace_title_label.setText("导出与报告 / Export & Report")
                    self._workspace_subtitle_label.setText("当前结果未通过 Report-ready Gate，正式报告生成与导出功能已禁用。")
                elif self._current_target_page_key == "project_home":
                    self._workspace_title_label.setText("Meta 分析 / Meta Analysis")
                    self._workspace_subtitle_label.setText("系统综述与 Meta 分析流程管理，当前为 Developer Preview（本地测试版）。")
            for key, button in self._target_ia_buttons.items():
                is_current = key == self._current_target_page_key
                button.setChecked(is_current)
                button.setProperty("currentStep", is_current)
                _refresh_dynamic_style(button)
                button.setMinimumHeight(74)
                button.setMinimumSize(0, 74)
            if hasattr(self, "_target_interaction_status"):
                self._target_interaction_status.setText(
                    f"当前页面：{current.label} · {current.status_key}"
                )
            if hasattr(self, "_target_runtime_stack"):
                target_index = self._target_runtime_page_indices.get(self._current_target_page_key)
                if target_index is not None:
                    self._target_runtime_stack.setCurrentIndex(target_index)
            if hasattr(self, "_result_export_panel"):
                self._result_export_panel.setVisible(self._current_target_page_key == "report_export")

        def _sync_type_interaction_state(self) -> None:
            types = {meta_type.type_id: meta_type for meta_type in meta_active_types_v1()}
            current = types[self._selected_active_meta_type_id]
            for type_id, button in self._active_type_buttons.items():
                button.setChecked(type_id == self._selected_active_meta_type_id)
            for type_id, card in getattr(self, "_active_type_cards", {}).items():
                card.setProperty("selected", type_id == self._selected_active_meta_type_id)
                _refresh_dynamic_style(card)
            if hasattr(self, "_active_type_status"):
                self._active_type_status.setText(
                    f"Selected active Meta type: {current.type_id} · {current.status_key} · {current.interaction_mode}; AI suggestion remains review-only."
                )

        def _build_pages(self) -> None:
            for item in self._layout_state.navigation_items:
                self._navigation_list.addItem(QListWidgetItem(f"{item.label}\n{item.status_label_zh}"))
                self._page_stack.addWidget(self._page(item))
                self._page_keys.append(item.page_key)
            self._navigation_list.setCurrentRow(0)

        def _page(self, item: MetaWorkspaceNavigationItem) -> QFrame:
            frame = QFrame()
            frame.setObjectName(f"metaMainlinePage_{item.page_key}")
            layout = QVBoxLayout(frame)
            heading = QLabel(item.label)
            heading.setStyleSheet("font-size: 18px; font-weight: 700;")
            body = QLabel(item.description)
            body.setWordWrap(True)
            note = QLabel(self._layout_state.testing_notice)
            note.setObjectName("metaMainlineBoundaryNotice")
            note.setWordWrap(True)
            layout.addWidget(heading)
            layout.addWidget(body)
            layout.addWidget(note)
            layout.addStretch(1)
            return frame

        def _refresh_summary(self) -> None:
            if self._current_meta_project is not None:
                summary = self._current_meta_project
                self._status_label.setText(
                    f"当前 Meta 项目：{summary.project_name} · {summary.status} · {summary.project_root}"
                )
            elif self._current_project_dir is not None:
                self._status_label.setText(f"当前目录：{self._current_project_dir}；尚未读取到有效 Meta 项目 manifest。")
            else:
                self._status_label.setText("当前未绑定 Meta 项目。")

else:  # pragma: no cover

    class MetaAnalysisWorkspaceWidget:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs) -> None:
            self._current_project_dir = None

        def page_keys(self) -> tuple[str, ...]:
            return tuple(item.page_key for item in meta_workspace_layout_state().navigation_items)

        def current_project_dir(self) -> Path | None:
            return self._current_project_dir

        def set_project_record(self, record) -> None:
            self._current_project_dir = Path(record.project_dir).expanduser().resolve()
