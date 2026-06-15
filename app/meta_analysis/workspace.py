from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import json
from pathlib import Path

from app.shared.feature_availability import FeatureAvailability, list_features
from app.shared.feature_status import FeatureItem, feature_item_from_availability
from app.shared.storage import default_storage_root
from app.version import APP_VERSION
from app.ui_style_tokens import meta_workspace_stylesheet

from app.meta_analysis.project_workspace import (
    MetaProjectSummary,
    create_meta_analysis_project,
    open_meta_analysis_project,
)
from app.meta_analysis.ui_text import INTERNAL_BETA_STATUS_ZH
from app.meta_analysis.pages.workflow_integration_page import (
    MetaWorkflowStepState,
    meta_workflow_integration_state_from_project,
    workflow_navigation_items,
)


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
    return [feature for feature in list_features("meta_analysis") if feature.feature_id in step_ids]


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
class MetaWorkspaceNavigationItem:
    step_id: str
    label: str
    description: str
    page_key: str
    status_label: str = "Testing / Developer Preview"
    status_label_zh: str = "内部测试"


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


def meta_workspace_layout_state() -> MetaWorkspaceLayoutState:
    version_status = f"{APP_VERSION} · {INTERNAL_BETA_STATUS_ZH}"
    workflow_items = tuple(
        MetaWorkspaceNavigationItem(
            str(item["step_id"]),
            str(item["title_zh"]),
            "Meta Analysis 中文工作流步骤；显示状态、artifact 摘要、warning 和下一步。",
            str(item["route_key"]),
            status_label="Testing / Developer Preview",
            status_label_zh="内部测试",
        )
        for item in workflow_navigation_items()
    )
    return MetaWorkspaceLayoutState(
        title="Meta 分析模块",
        status_label=version_status,
        description="用中文串联 Meta 分析主流程：状态可见、按钮清楚、下一步明确。",
        navigation_items=workflow_items,
        default_page_key="workflow_home",
        testing_notice="当前 Meta 分析模块仍为内部测试版；所有结果需要人工复核，不能作为正式临床、投稿或 production 结论。",
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
    projects_root = root / "projects"
    summaries: list[ImportBatchQualitySummary] = []
    if projects_root.exists():
        for path in projects_root.glob("*/meta_analysis/literature_import/*_records.json"):
            payload = _load_json_object(path)
            if payload:
                summaries.append(_summary_from_unified_import(path, payload))
    summaries.extend(_batch_manifest_summaries(root))
    deduped = {f"{item.project_id}:{item.batch_id}:{item.created_at}": item for item in summaries}
    return sorted(deduped.values(), key=lambda item: item.created_at, reverse=True)[:limit]


def literature_import_quality_dashboard_state(root_dir: Path | None = None, *, limit: int = 5) -> LiteratureImportQualityDashboardState:
    batches = tuple(recent_import_batch_quality_summaries(root_dir, limit=limit))
    return LiteratureImportQualityDashboardState(
        title="Meta Literature Import Quality Dashboard",
        status_label="Testing / Developer Preview",
        description="只读显示最近文献导入批次的解析质量、warning 数量、failed 数量、duplicate candidate 数量和 diagnostics 路径。",
        empty_state="暂无导入批次。请先在 Literature Import 页面导入 NBIB / RIS / CSV 文件。",
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


def _batch_manifest_summaries(root: Path) -> list[ImportBatchQualitySummary]:
    batches_path = root / "literature" / "import_batches.json"
    if not batches_path.exists():
        return []
    summaries: list[ImportBatchQualitySummary] = []
    for item in _load_json_list(batches_path):
        batch_id = str(item.get("batch_id", ""))
        diagnostics_path = root / "literature" / "import_diagnostics" / f"{batch_id}_import_diagnostics.json"
        diagnostics = _load_json_object(diagnostics_path)
        metadata = dict(item.get("metadata", {})) if isinstance(item.get("metadata"), dict) else {}
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
    return summaries


def _load_json_object(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
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
    return [dict(item) for item in payload if isinstance(item, dict)] if isinstance(payload, list) else []


def _int_from(payload: dict[str, object], key: str, fallback: int = 0) -> int:
    try:
        return int(payload.get(key, fallback))
    except (TypeError, ValueError):
        return fallback


def _diagnostics_summary_text(diagnostics: dict[str, object]) -> str:
    if not diagnostics:
        return ""
    fields = (
        "missing_title_count",
        "missing_author_count",
        "missing_year_count",
        "missing_doi_count",
        "missing_pmid_count",
        "invalid_year_count",
        "invalid_doi_count",
    )
    return "; ".join(f"{field}={_int_from(diagnostics, field)}" for field in fields if _int_from(diagnostics, field))


def _meta_project_folder_name(project_name: str) -> str:
    cleaned = "".join(char if char.isalnum() else "_" for char in project_name.strip())
    return "_".join(part for part in cleaned.split("_") if part) or "Meta_Project"


def _compact_path(path: Path | None) -> str:
    if path is None:
        return "未选择"
    home = Path.home()
    try:
        relative = path.expanduser().resolve().relative_to(home)
        parts = (home.name, *relative.parts)
    except ValueError:
        parts = path.parts
    if len(parts) <= 4:
        return " / ".join(parts)
    return " / ".join((parts[0], "...", *parts[-3:]))


def _workflow_stage_zh(stage: str) -> str:
    return {
        "project_home": "项目首页",
        "pico_workspace": "研究问题与 PICO",
        "search_strategy": "检索策略",
        "literature_import": "文献库与导入",
        "screening": "去重与筛选",
        "fulltext_management": "全文管理",
        "manual_extraction": "数据提取",
        "extraction_quality": "数据提取",
        "ai_extraction": "AI 辅助提取",
        "quality_assessment": "质量评价",
        "analysis_plan": "分析计划",
        "statistics_analysis": "统计分析",
        "figure_results": "图表结果",
        "prisma": "PRISMA",
        "report_export": "报告导出",
        "reproducibility_package": "复现包",
        "analysis_results": "统计分析",
        "prisma_reporting": "报告导出",
    }.get(stage, "项目首页")


def _main_stage_status_label(status: str) -> str:
    if status in {"已确认", "已生成", "已有记录", "已有项目", "已有草稿", "已有人工评分", "已创建", "已完成"}:
        return "已完成"
    if status in {"草稿待确认", "已有建议"}:
        return "草稿"
    if status in {"待人工复核", "等待用户选择", "有待审核建议", "需要确认"}:
        return "待确认"
    if status in {"testing-level", "待开发", "暂不可用"}:
        return "阻塞"
    return status or "未开始"


def _nav_stage_label(title: str) -> str:
    return {
        "Meta 项目首页": "项目首页",
        "项目首页": "项目首页",
        "研究问题 / PICO": "研究问题与 PICO",
        "研究问题与 PICO": "研究问题与 PICO",
        "检索与导入": "检索策略",
        "检索策略": "检索策略",
        "文献库与导入": "文献库与导入",
        "文献筛选": "去重与筛选",
        "去重与筛选": "去重与筛选",
        "提取与质量评价": "数据提取",
        "数据提取与质量评价": "数据提取",
        "数据提取": "数据提取",
        "统计分析": "统计分析",
        "报告导出": "报告导出",
    }.get(title, title)


try:
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QFileDialog,
        QFrame,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPlainTextEdit,
        QPushButton,
        QScrollArea,
        QStackedWidget,
        QTableWidget,
        QTableWidgetItem,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
    from PySide6.QtCore import Qt
except Exception:  # pragma: no cover
    QApplication = QCheckBox = QComboBox = QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QListWidget = QListWidgetItem = QMessageBox = QPlainTextEdit = QPushButton = QScrollArea = QStackedWidget = QTableWidget = QTableWidgetItem = QTextEdit = QVBoxLayout = QWidget = None
    Qt = None


if QWidget is not None:
    from app.meta_analysis.search.pubmed_candidates_handoff_service import PubMedCandidatesHandoffService
    from app.meta_analysis.search.pubmed_search_service import PubMedSearchService
    from app.meta_analysis.search.search_strategy_builder_service import SearchStrategyBuilderService
    from app.meta_analysis.services.dedup_review_v2_service import (
        DECISION_KEEP_BOTH,
        DECISION_MARK_NOT_DUPLICATE,
        DECISION_MERGE,
        DECISION_SET_MASTER_RECORD,
        DECISION_SKIP,
        DedupReviewV2Service,
    )
    from app.meta_analysis.services.ai_assisted_extraction_queue_service import AIAssistedExtractionQueueService
    from app.meta_analysis.services.analysis_plan_service import (
        ANALYSIS_PLAN_EFFECT_MEASURE_TYPES,
        ANALYSIS_PLAN_MODEL_PREFERENCES,
        ANALYSIS_PLAN_READINESS_WARNING_LABELS_ZH,
        AnalysisPlanService,
    )
    from app.meta_analysis.models.result_review import result_review_label_zh
    from app.meta_analysis.models.statistical_result_state import (
        STATISTICAL_RESULT_STATE_NOT_RUN,
        statistical_result_state_label_zh,
    )
    from app.meta_analysis.services.effect_size_normalization_service import EffectSizeNormalizationService
    from app.meta_analysis.services.exclusion_criteria_library_service import (
        FULL_TEXT_STAGE,
        TITLE_ABSTRACT_STAGE,
        ExclusionCriteriaLibraryService,
    )
    from app.meta_analysis.services.figure_result_service import FigureResultService
    from app.meta_analysis.services.formal_report_service import FormalMarkdownReportBuilder, PRISMAService
    from app.meta_analysis.services.fulltext_eligibility_service import FullTextEligibilityService
    from app.meta_analysis.services.fulltext_management_service import (
        FULLTEXT_EXCLUSION_REASON_LABELS_ZH,
        FULLTEXT_EXCLUSION_REASONS_M4C,
        FULLTEXT_MANAGEMENT_STATUSES,
        FULLTEXT_STATUS_FULL_TEXT_CONFIRMED,
        FULLTEXT_STATUS_FULL_TEXT_UNAVAILABLE,
        FULLTEXT_STATUS_LABELS_ZH,
        FullTextManagementService,
    )
    from app.meta_analysis.services.fulltext_parsing_service import FullTextParsingService
    from app.meta_analysis.services.literature_library_service import LiteratureLibraryService
    from app.meta_analysis.services.manual_extraction_effect_row_service import ManualExtractionEffectRowService
    from app.meta_analysis.services.manual_extraction_effect_row_service import (
        STRUCTURED_EXTRACTION_EFFECT_MEASURES,
        STRUCTURED_EXTRACTION_EVIDENCE_STATES,
        STRUCTURED_EXTRACTION_FIELD_LABELS_ZH,
    )
    from app.meta_analysis.services.meta_statistics_engine_service import MetaStatisticsEngineService
    from app.meta_analysis.services.multisource_literature_import_service import MultiSourceLiteratureImportService
    from app.meta_analysis.services.pairwise_meta_executor_service import PairwiseMetaExecutorService
    from app.meta_analysis.services.pico_workspace_service import PICOWorkspaceService
    from app.meta_analysis.services.publication_export_service import PublicationExportService
    from app.meta_analysis.services.quality_service import QualityAssessmentService
    from app.meta_analysis.services.quality_service import (
        NOS_DOMAIN_LABELS_ZH,
        NOS_DOMAINS,
        QUALITY_M6_STATE_LABELS_ZH,
        QUALITY_RATING_LABELS_ZH,
    )
    from app.meta_analysis.services.result_review_service import StatisticalResultReviewService
    from app.meta_analysis.services.title_abstract_screening_v2_service import (
        DECISION_EXCLUDE,
        DECISION_INCLUDE,
        DECISION_NEED_FULL_TEXT,
        DECISION_NOT_SCREENED,
        DECISION_UNCERTAIN,
        EXCLUSION_REASON_LABELS_ZH,
        TitleAbstractScreeningV2Service,
    )

    class MetaAnalysisWorkspaceWidget(QWidget):
        def __init__(self, on_back: Callable[[], None] | None = None) -> None:
            super().__init__()
            self.setObjectName("metaWorkspace")
            self.setStyleSheet(meta_workspace_stylesheet())
            self._layout_state = meta_workspace_layout_state()
            self._on_back = on_back
            self._current_project_record = None
            self._current_project_dir: Path | None = None
            self._current_meta_project: MetaProjectSummary | None = None
            self._page_keys: list[str] = []

            root = QHBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)
            self._global_nav = QFrame()
            self._global_nav.setObjectName("metaGlobalNav")
            self._global_nav.setFixedWidth(230)
            global_layout = QVBoxLayout(self._global_nav)
            global_layout.setContentsMargins(16, 18, 16, 18)
            global_layout.setSpacing(12)
            title = QLabel("Meta 分析")
            title.setObjectName("metaSideTitle")
            global_layout.addWidget(title)
            self._project_summary_label = QLabel("当前项目：未选择")
            self._project_summary_label.setObjectName("metaMutedText")
            self._project_summary_label.setWordWrap(True)
            global_layout.addWidget(self._project_summary_label)
            status = QLabel("")
            status.setObjectName("metaStatusBadge")
            global_layout.addWidget(status)
            notice = QLabel("")
            notice.setObjectName("metaMutedText")
            notice.setWordWrap(True)
            global_layout.addWidget(notice)
            back = QPushButton("返回首页")
            back.setObjectName("metaSecondaryButton")
            if on_back:
                back.clicked.connect(on_back)
            global_layout.addWidget(back)
            global_layout.addStretch(1)

            self._workflow_nav = QFrame()
            self._workflow_nav.setObjectName("metaWorkflowNav")
            self._workflow_nav.setFixedWidth(310)
            workflow_layout = QVBoxLayout(self._workflow_nav)
            workflow_layout.setContentsMargins(14, 18, 14, 18)
            workflow_layout.setSpacing(10)
            workflow_title = QLabel("Meta 项目侧栏")
            workflow_title.setObjectName("metaPanelTitle")
            workflow_layout.addWidget(workflow_title)
            self._sidebar_project_label = QLabel("当前项目：未创建\n项目位置：未选择")
            self._sidebar_project_label.setObjectName("metaMutedText")
            self._sidebar_project_label.setWordWrap(True)
            workflow_layout.addWidget(self._sidebar_project_label)
            sidebar_actions = QHBoxLayout()
            self._new_project_nav_button = QPushButton("新建 Meta 项目")
            self._new_project_nav_button.setObjectName("metaSecondaryButton")
            self._new_project_nav_button.clicked.connect(lambda: self.show_step("workflow_home"))
            self._open_project_nav_button = QPushButton("打开已有项目")
            self._open_project_nav_button.setObjectName("metaSecondaryButton")
            self._open_project_nav_button.clicked.connect(self._choose_existing_project_folder)
            sidebar_actions.addWidget(self._new_project_nav_button)
            sidebar_actions.addWidget(self._open_project_nav_button)
            workflow_layout.addLayout(sidebar_actions)
            self._navigation_list = QListWidget()
            self._navigation_list.setObjectName("metaWorkflowStepList")
            workflow_layout.addWidget(self._navigation_list, 1)
            back = QPushButton("返回模块首页")
            back.setObjectName("metaSecondaryButton")
            if on_back:
                back.clicked.connect(on_back)
            workflow_layout.addWidget(back)

            self._workspace = QFrame()
            self._workspace.setObjectName("metaCurrentStepWorkspace")
            workspace_layout = QVBoxLayout(self._workspace)
            workspace_layout.setContentsMargins(18, 18, 18, 18)
            workspace_layout.setSpacing(0)
            self._page_stack = QStackedWidget()
            self._page_stack.setObjectName("metaCurrentStepStack")
            workspace_layout.addWidget(self._page_stack, 1)

            self._navigation_list.currentRowChanged.connect(self._page_stack.setCurrentIndex)
            root.addWidget(self._workflow_nav)
            root.addWidget(self._workspace, 1)
            self._rebuild_pages()

        def page_keys(self) -> tuple[str, ...]:
            return tuple(self._page_keys)

        def current_page_key(self) -> str:
            row = self._navigation_list.currentRow()
            if row < 0 or row >= len(self._page_keys):
                return ""
            return self._page_keys[row]

        def current_project_dir(self) -> Path | None:
            return self._current_project_dir

        def set_project_record(self, record) -> None:
            self._current_project_record = record
            self.set_project_dir(Path(record.project_dir))

        def set_project_dir(self, path: str | Path | None) -> None:
            self._current_project_dir = Path(path).expanduser().resolve() if path else None
            self._current_meta_project = None
            if self._current_project_dir is not None:
                validation = open_meta_analysis_project(self._current_project_dir)
                if validation.is_valid and validation.summary is not None:
                    self._current_meta_project = validation.summary
            self._rebuild_pages()

        def set_new_project_form(self, *, project_name: str = "", research_topic: str = "", save_location: str | Path | None = None) -> None:
            if hasattr(self, "_new_project_name_input"):
                self._new_project_name_input.setText(project_name)
                self._research_topic_input.setText(research_topic)
                self._save_location_input.setText(str(save_location or ""))
                self._refresh_final_project_path()

        def create_meta_project_from_form(self, *, allow_existing_nonempty: bool = False) -> MetaProjectSummary | None:
            project_name = self._new_project_name_input.text().strip() if hasattr(self, "_new_project_name_input") else ""
            save_location = self._save_location_input.text().strip() if hasattr(self, "_save_location_input") else ""
            research_topic = self._research_topic_input.text().strip() if hasattr(self, "_research_topic_input") else ""
            if not project_name:
                self._set_project_status("请先填写项目名称。")
                return None
            if not save_location:
                self._set_project_status("请先选择保存位置。")
                return None
            target = Path(save_location).expanduser().resolve() / _meta_project_folder_name(project_name)
            if target.exists() and any(target.iterdir()) and not allow_existing_nonempty:
                answer = QMessageBox.question(
                    self,
                    "确认使用已有文件夹",
                    "目标项目文件夹已存在且不是空文件夹。是否继续在该文件夹中创建 Meta 项目？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if answer != QMessageBox.Yes:
                    self._set_project_status("已取消创建 Meta 项目。")
                    return None
                allow_existing_nonempty = True
            try:
                summary = create_meta_analysis_project(project_name, save_location, research_topic=research_topic, allow_existing_nonempty=allow_existing_nonempty)
            except Exception as exc:
                self._set_project_status(f"创建 Meta 项目失败：{exc}")
                return None
            self._current_project_dir = summary.project_root
            self._current_meta_project = summary
            self._set_project_status("Meta 项目已创建，可以继续研究问题 / PICO。")
            self._rebuild_pages()
            return summary

        def open_meta_project_folder(self, path: str | Path) -> bool:
            validation = open_meta_analysis_project(path)
            if not validation.is_valid or validation.summary is None:
                self._set_project_status("；".join(validation.errors) or "该文件夹不是有效 Meta 项目。")
                return False
            self._current_project_dir = validation.summary.project_root
            self._current_meta_project = validation.summary
            self._set_project_status("已打开 Meta 项目。")
            self._rebuild_pages()
            return True

        def _choose_save_location(self) -> None:
            path = QFileDialog.getExistingDirectory(self, "选择保存位置")
            if path:
                self._save_location_input.setText(path)
                self._refresh_final_project_path()

        def _choose_existing_project_folder(self) -> None:
            path = QFileDialog.getExistingDirectory(self, "选择已有项目文件夹")
            if path:
                self.open_meta_project_folder(path)

        def _refresh_final_project_path(self, *_args) -> None:
            project_name = self._new_project_name_input.text().strip() if hasattr(self, "_new_project_name_input") else ""
            save_location = self._save_location_input.text().strip() if hasattr(self, "_save_location_input") else ""
            final = str(Path(save_location).expanduser() / _meta_project_folder_name(project_name)) if project_name and save_location else "请填写项目名称并选择保存位置"
            self._final_project_path_label.setText(f"最终项目路径：{final}")

        def _set_project_status(self, text: str) -> None:
            if hasattr(self, "_project_action_status_label"):
                self._project_action_status_label.setText(text)

        def show_step(self, page_key: str) -> None:
            if page_key in self._page_keys:
                self._navigation_list.setCurrentRow(self._page_keys.index(page_key))

        def meta_workspace_layout_state(self) -> dict[str, object]:
            return {
                "global_nav": self._global_nav.objectName(),
                "workflow_nav": self._workflow_nav.objectName(),
                "current_step_workspace": self._workspace.objectName(),
                "page_keys": self.page_keys(),
                "current_page_key": self.current_page_key(),
                "project_dir": str(self._current_project_dir or ""),
            }

        def _rebuild_pages(self) -> None:
            current_page_key = self.current_page_key() or self._layout_state.default_page_key
            while self._page_stack.count():
                widget = self._page_stack.widget(0)
                self._page_stack.removeWidget(widget)
                widget.deleteLater()
            self._navigation_list.clear()
            self._page_keys = []
            self._update_project_summary()
            state = meta_workflow_integration_state_from_project(self._project_dir_for_state())
            for step in state.steps:
                status = _main_stage_status_label(step.status)
                item = QListWidgetItem(f"{step.order}. {_nav_stage_label(step.title_zh)} · {status}")
                item.setToolTip(f"{step.primary_action_zh}\n{step.next_action_zh}")
                self._navigation_list.addItem(item)
                self._page_stack.addWidget(_scroll_page(self._page_for_step(step, state)))
                self._page_keys.append(step.route_key)
            if current_page_key in self._page_keys:
                self._navigation_list.setCurrentRow(self._page_keys.index(current_page_key))
            else:
                self._navigation_list.setCurrentRow(0)

        def _project_dir_for_state(self) -> Path:
            return self._current_project_dir or (default_storage_root() / "projects" / "__meta_empty_state__" / "meta_analysis")

        def _update_project_summary(self) -> None:
            if self._current_project_dir is None:
                self._project_summary_label.setText("当前项目：未创建\n进入项目后显示真实 Meta 工作区。")
                self._sidebar_project_label.setText("当前项目：未创建\n项目位置：未选择")
                return
            name = self._current_meta_project.project_name if self._current_meta_project is not None else getattr(self._current_project_record, "name", "") or self._current_project_dir.name
            compact = _compact_path(self._current_project_dir)
            self._project_summary_label.setText(f"当前项目：{name}\n{compact}")
            self._sidebar_project_label.setText(f"当前项目：{name}\n项目位置：{compact}")

        def _page_for_step(self, step: MetaWorkflowStepState, state) -> QWidget:
            if self._current_project_dir is None:
                if step.route_key == "workflow_home":
                    return self._meta_project_home_page(state)
                if step.route_key == "page_button_audit":
                    return _page_button_audit_page(None, on_next=lambda: self.show_step("pico_workspace"), on_route=self.show_step)
                return _no_project_page(step)
            project_dir = self._current_project_dir
            if step.route_key == "workflow_home":
                return _project_home_page(state, project_dir, self._current_meta_project, on_go_pico=lambda: self.show_step("pico_workspace"))
            if step.route_key == "page_button_audit":
                return _page_button_audit_page(project_dir, on_next=lambda: self.show_step("pico_workspace"), on_route=self.show_step)
            if step.route_key == "pico_workspace":
                return _pico_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("search_strategy"))
            if step.route_key == "search_strategy":
                return _search_strategy_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("literature_import"))
            if step.route_key == "literature_import":
                return _literature_acquisition_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("screening_review"))
            if step.route_key == "screening_review":
                return _dedup_review_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("exclusion_criteria"))
            if step.route_key == "exclusion_criteria":
                return _exclusion_criteria_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("title_abstract_screening"))
            if step.route_key == "title_abstract_screening":
                return _title_abstract_screening_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("fulltext_management"))
            if step.route_key == "fulltext_management":
                return _fulltext_management_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("manual_extraction"))
            if step.route_key == "manual_extraction":
                return _manual_extraction_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("ai_extraction"))
            if step.route_key == "ai_extraction":
                return _ai_extraction_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("quality_assessment"))
            if step.route_key == "quality_assessment":
                return _quality_assessment_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("analysis_plan"))
            if step.route_key == "analysis_plan":
                return _analysis_plan_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("statistics_analysis"))
            if step.route_key == "statistics_analysis":
                return _statistics_analysis_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("figure_results"))
            if step.route_key == "figure_results":
                return _figure_results_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("prisma"))
            if step.route_key == "prisma":
                return _prisma_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("report_export"))
            if step.route_key == "report_export":
                return _report_export_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("reproducibility_package"))
            if step.route_key == "reproducibility_package":
                return _reproducibility_package_page(project_dir, on_refresh=self._rebuild_pages)
            return _placeholder_step_page(step)

        def _meta_project_home_page(self, state) -> QFrame:
            frame = QFrame()
            frame.setObjectName("metaProjectHomePage")
            layout = QVBoxLayout(frame)
            layout.setSpacing(12)
            layout.addWidget(_meta_home_header(None, "项目首页", "管理 Meta 项目，并继续研究问题、检索、筛选、提取、分析与报告流程。"))
            layout.addWidget(self._meta_project_management_card(compact=True))
            action_card = _card("下一步")
            action_layout = action_card.layout()
            action_layout.addWidget(QLabel("请先新建或打开 Meta 项目。"))
            continue_button = QPushButton("继续：研究问题 / PICO")
            continue_button.setObjectName("metaPrimaryButton")
            continue_button.setEnabled(False)
            action_layout.addWidget(continue_button)
            layout.addWidget(action_card)
            layout.addWidget(_developer_details(_developer_diagnostics_text(state), button_text="开发者诊断"))
            layout.addStretch(1)
            return frame

        def _meta_project_management_card(self, *, compact: bool = False) -> QFrame:
            card = _card("新建 Meta 项目" if compact else "Meta 项目管理")
            card.setObjectName("metaProjectManagementCard")
            layout = card.layout()
            self._new_project_name_input = QLineEdit()
            self._new_project_name_input.setObjectName("metaProjectNameInput")
            self._new_project_name_input.setPlaceholderText("项目名称")
            self._research_topic_input = QLineEdit()
            self._research_topic_input.setObjectName("metaResearchTopicInput")
            self._research_topic_input.setPlaceholderText("研究主题（可选）")
            self._save_location_input = QLineEdit()
            self._save_location_input.setObjectName("metaSaveLocationInput")
            self._save_location_input.setPlaceholderText("请选择保存位置")
            browse_button = QPushButton("选择保存位置")
            browse_button.setObjectName("metaSecondaryButton")
            browse_button.clicked.connect(self._choose_save_location)
            self._final_project_path_label = QLabel("最终项目路径：请填写项目名称并选择保存位置")
            self._final_project_path_label.setObjectName("metaMutedText")
            self._final_project_path_label.setWordWrap(True)
            self._new_project_name_input.textChanged.connect(self._refresh_final_project_path)
            self._save_location_input.textChanged.connect(self._refresh_final_project_path)
            create_button = QPushButton("创建项目")
            create_button.setObjectName("metaPrimaryButton")
            create_button.clicked.connect(lambda: self.create_meta_project_from_form())
            layout.addWidget(self._new_project_name_input)
            layout.addWidget(self._research_topic_input)
            location_row = QHBoxLayout()
            location_row.addWidget(self._save_location_input, 1)
            location_row.addWidget(browse_button)
            layout.addLayout(location_row)
            layout.addWidget(self._final_project_path_label)
            layout.addWidget(create_button)
            layout.addWidget(QLabel("打开已有 Meta 项目"))
            open_button = QPushButton("选择已有项目文件夹")
            open_button.setObjectName("metaSecondaryButton")
            open_button.clicked.connect(self._choose_existing_project_folder)
            layout.addWidget(open_button)
            self._project_action_status_label = QLabel("请先新建或打开 Meta 项目。" if self._current_project_dir is None else "Meta 项目已打开。")
            self._project_action_status_label.setObjectName("metaMutedText")
            self._project_action_status_label.setWordWrap(True)
            layout.addWidget(self._project_action_status_label)
            return card

    def _feature_row(feature: FeatureAvailability) -> QFrame:
        frame = QFrame()
        frame.setObjectName("metaCard")
        layout = QVBoxLayout(frame)
        title = QLabel(feature.display_label())
        title.setObjectName("metaCardTitle")
        detail = QLabel(feature.description)
        detail.setWordWrap(True)
        source = QLabel(f"来源：{feature.legacy_source or '统一壳子占位'}")
        source.setWordWrap(True)
        next_step = QLabel(f"下一步：{feature.next_step}")
        next_step.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(detail)
        layout.addWidget(source)
        layout.addWidget(next_step)
        return frame


    def _scroll_page(widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setObjectName("metaCurrentStepScroll")
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        return scroll


    def _project_home_page(state, project_dir: Path, summary: MetaProjectSummary | None, *, on_go_pico: Callable[[], None]) -> QFrame:
        frame = QFrame()
        frame.setObjectName("metaProjectHomePage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(_meta_home_header(summary, "项目首页", "管理 Meta 项目，并继续研究问题、检索、筛选、提取、分析与报告流程。"))
        action_card = _card("当前项目已打开")
        action_layout = action_card.layout()
        action_layout.addWidget(QLabel("下一步：填写研究问题 / PICO"))
        next_button = QPushButton("继续：研究问题 / PICO")
        next_button.setObjectName("metaPrimaryButton")
        next_button.clicked.connect(on_go_pico)
        action_layout.addWidget(next_button)
        layout.addWidget(action_card)
        layout.addWidget(_project_business_summary(project_dir))
        layout.addWidget(_progress_summary(state))
        layout.addWidget(_developer_details(_developer_diagnostics_text(state, summary), button_text="开发者诊断"))
        layout.addStretch(1)
        return frame


    def _no_project_page(step: MetaWorkflowStepState) -> QFrame:
        frame = QFrame()
        frame.setObjectName("metaNoProjectPage")
        layout = QVBoxLayout(frame)
        layout.addWidget(_page_header(step.title_zh, "请先新建或打开 Meta 项目。", "空状态"))
        layout.addWidget(_info_card("尚未开始", ["请先新建或打开 Meta 项目。", "项目创建前不会写入研究问题、检索策略或文献库。"]))
        button = QPushButton("继续：研究问题 / PICO")
        button.setObjectName("metaSecondaryButton")
        button.setEnabled(False)
        layout.addWidget(button)
        layout.addStretch(1)
        return frame


    def _page_button_audit_page(project_dir: Path | None, *, on_next: Callable[[], None], on_route: Callable[[str], None]) -> QFrame:
        rows = _button_audit_rows()
        frame = QFrame()
        frame.setObjectName("metaPageButtonAuditPage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(
            _page_header(
                "页面能力审计",
                "逐页列出 preview Meta 模块当前可见按钮、模块、接入服务、跳转目标和边界。",
                "只读审计",
            )
        )
        layout.addWidget(
            _info_card(
                "审计范围",
                [
                    f"已记录页面/按钮/模块项：{len(rows)}",
                    "范围限定为 active runtime，不包含 legacy 快照。",
                    "本页不运行检索、统计、OCR、报告导出或任何项目写入。",
                    "生产级能力仍需样例 walkthrough、统一测试、统计专家复核和打包验证后才能声明完成。",
                ],
                object_name="metaButtonAuditSummary",
            )
        )
        table = QTableWidget()
        table.setObjectName("metaPageButtonAuditTable")
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["页面", "按钮 / 模块", "接入功能或指向", "边界"])
        table.setRowCount(len(rows))
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        for row, values in enumerate(rows):
            for col, value in enumerate(values):
                table.setItem(row, col, QTableWidgetItem(value))
        layout.addWidget(table, 1)
        actions = QHBoxLayout()
        export_button = QPushButton("导出审计记录 JSON")
        export_button.setObjectName("metaSecondaryButton")
        export_csv_button = QPushButton("导出审计表 CSV")
        export_csv_button.setObjectName("metaSecondaryButton")
        export_capability_manifest_button = QPushButton("导出能力总清单")
        export_capability_manifest_button.setObjectName("metaSecondaryButton")
        export_package_button = QPushButton("导出页面审计包")
        export_package_button.setObjectName("metaSecondaryButton")
        export_delivery_package_button = QPushButton("导出完整交付包")
        export_delivery_package_button.setObjectName("metaPrimaryButton")
        export_integrity_manifest_button = QPushButton("导出交付校验清单")
        export_integrity_manifest_button.setObjectName("metaSecondaryButton")
        go_selected_button = QPushButton("跳转到选中页面")
        go_selected_button.setObjectName("metaSecondaryButton")
        next_button = QPushButton("继续：研究问题 / PICO")
        next_button.setObjectName("metaPrimaryButton")
        next_button.setEnabled(project_dir is not None)
        actions.addWidget(export_button)
        actions.addWidget(export_csv_button)
        actions.addWidget(export_capability_manifest_button)
        actions.addWidget(export_package_button)
        actions.addWidget(export_delivery_package_button)
        actions.addWidget(export_integrity_manifest_button)
        actions.addWidget(go_selected_button)
        next_button.clicked.connect(on_next)
        actions.addWidget(next_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        docs_path = Path(__file__).resolve().parents[2] / "docs" / "meta_preview_page_button_audit_2026-06-11.md"
        scope = str(project_dir) if project_dir is not None else "未选择项目；显示全局 preview 页面能力审计"
        layout.addWidget(_developer_details(f"project_dir={scope}\naudit_doc={docs_path}"))

        def do_export_audit() -> None:
            export_root = (project_dir / "audit") if project_dir is not None else (default_storage_root() / "meta_analysis" / "audit")
            export_root.mkdir(parents=True, exist_ok=True)
            export_path = export_root / "meta_page_button_audit_runtime.json"
            payload = _page_button_audit_payload(project_dir, rows, docs_path)
            export_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            _show_message(f"已导出页面能力审计：{export_path}")

        def do_export_audit_csv() -> None:
            path = _write_page_button_audit_csv(project_dir, rows)
            _show_message(f"已导出页面能力审计 CSV：{path.name}")

        def do_export_capability_manifest() -> None:
            path = _write_meta_workflow_capability_manifest(project_dir, rows)
            _show_message(f"已导出工作流能力总清单：{path.name}")

        def do_export_audit_package() -> None:
            path = _write_page_button_audit_package(project_dir, rows, docs_path)
            _show_message(f"已导出页面审计包：{path.name}")

        def do_export_delivery_package() -> None:
            path = _write_meta_preview_delivery_package(project_dir, rows, docs_path)
            _show_message(f"已导出完整交付包：{path.name}")

        def do_export_integrity_manifest() -> None:
            path = _write_meta_preview_integrity_manifest(project_dir, rows, docs_path)
            _show_message(f"已导出交付校验清单：{path.name}")

        def do_go_selected_page() -> None:
            selected_row = table.currentRow()
            if selected_row < 0:
                _show_message("请先选择一行审计记录。")
                return
            page_item = table.item(selected_row, 0)
            page_name = page_item.text() if page_item is not None else ""
            route = _audit_page_route(page_name)
            if not route:
                _show_message(f"暂无可跳转页面：{page_name}")
                return
            on_route(route)

        export_button.clicked.connect(do_export_audit)
        export_csv_button.clicked.connect(do_export_audit_csv)
        export_capability_manifest_button.clicked.connect(do_export_capability_manifest)
        export_package_button.clicked.connect(do_export_audit_package)
        export_delivery_package_button.clicked.connect(do_export_delivery_package)
        export_integrity_manifest_button.clicked.connect(do_export_integrity_manifest)
        go_selected_button.clicked.connect(do_go_selected_page)
        return frame


    def _page_button_audit_payload(project_dir: Path | None, rows: list[tuple[str, str, str, str]], docs_path: Path) -> dict[str, object]:
        return {
            "schema_version": "meta_page_button_audit.runtime.v1",
            "scope": "active_runtime_preview",
            "audit_scope": "page_button_and_module",
            "project_dir": str(project_dir or ""),
            "source_doc": str(docs_path),
            "row_count": len(rows),
            "rows": [
                {
                    "page": page,
                    "button_or_module": button,
                    "function_or_route": target,
                    "boundary": boundary,
                }
                for page, button, target, boundary in rows
            ],
        }


    def _write_page_button_audit_csv(project_dir: Path | None, rows: list[tuple[str, str, str, str]]) -> Path:
        import csv

        export_root = (project_dir / "audit") if project_dir is not None else (default_storage_root() / "meta_analysis" / "audit")
        export_root.mkdir(parents=True, exist_ok=True)
        output_path = export_root / "meta_page_button_audit_runtime.csv"
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["page", "button_or_module", "function_or_route", "boundary", "route_key"])
            for page, button, target, boundary in rows:
                writer.writerow([page, button, target, boundary, _audit_page_route(page)])
        return output_path


    def _write_meta_workflow_capability_manifest(project_dir: Path | None, rows: list[tuple[str, str, str, str]]) -> Path:
        export_root = (project_dir / "audit") if project_dir is not None else (default_storage_root() / "meta_analysis" / "audit")
        export_root.mkdir(parents=True, exist_ok=True)
        output_path = export_root / "meta_workflow_capability_manifest.json"
        route_counts: dict[str, int] = {}
        page_counts: dict[str, int] = {}
        for page, _button, _target, _boundary in rows:
            route = _audit_page_route(page)
            page_counts[page] = page_counts.get(page, 0) + 1
            if route:
                route_counts[route] = route_counts.get(route, 0) + 1
        workflow_artifacts = (
            "protocol/search_strategy_v2/search_execution_manifest.json",
            "literature/literature_acquisition_organization_manifest.json",
            "literature/literature_citation_manifest.json",
            "literature/literature_library_export.ris",
            "literature/literature_library_export.bib",
            "literature/literature_library_export.csl.json",
            "literature/literature_register.csv",
            "exports/literature_organization_package.zip",
            "screening/screening_organization_manifest.json",
            "screening/title_abstract_screening_decisions.csv",
            "fulltext/fulltext_retrieval_manifest.json",
            "fulltext/fulltext_retrieval_register.csv",
            "exports/fulltext_retrieval_package.zip",
            "extraction/extraction_organization_manifest.json",
            "exports/extraction_organization_package.zip",
            "quality/quality_organization_manifest.json",
            "exports/quality_assessment_package.zip",
            "analysis/statistics_results_manifest.json",
            "exports/statistics_results_package.zip",
            "figures/figure_results_manifest.json",
            "exports/figure_results_package.zip",
            "reports/prisma_reporting_manifest.json",
            "exports/prisma_reporting_package.zip",
            "reports/formal_report_delivery_manifest.json",
            "exports/formal_report_package.zip",
        )
        audit_artifacts = (
            "audit/meta_page_button_audit_runtime.json",
            "audit/meta_page_button_audit_runtime.csv",
            "audit/meta_page_button_audit_package.zip",
            "audit/meta_workflow_capability_manifest.json",
        )
        def artifact_rows(relative_paths: tuple[str, ...]) -> list[dict[str, object]]:
            rows_out: list[dict[str, object]] = []
            for rel in relative_paths:
                exists = bool(project_dir and (project_dir / rel).exists())
                rows_out.append({"path": rel, "exists": exists})
            return rows_out

        payload = {
            "schema_version": "meta_workflow_capability_manifest.v1",
            "project_dir": str(project_dir or ""),
            "page_count": len(page_counts),
            "button_or_module_count": len(rows),
            "route_count": len(route_counts),
            "route_counts": route_counts,
            "page_counts": page_counts,
            "workflow_capability_artifacts": artifact_rows(workflow_artifacts),
            "literature_capability_artifacts": artifact_rows(workflow_artifacts),
            "audit_artifacts": artifact_rows(audit_artifacts),
            "boundaries": [
                "This manifest summarizes UI route/button/module coverage and local artifact presence only.",
                "It does not execute retrieval, import, deduplication, screening, full-text parsing, statistics, or reporting.",
                "A runtime walkthrough is still required before claiming complete production readiness.",
            ],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path


    def _write_page_button_audit_package(project_dir: Path | None, rows: list[tuple[str, str, str, str]], docs_path: Path) -> Path:
        import zipfile

        export_root = (project_dir / "audit") if project_dir is not None else (default_storage_root() / "meta_analysis" / "audit")
        export_root.mkdir(parents=True, exist_ok=True)
        runtime_json = export_root / "meta_page_button_audit_runtime.json"
        runtime_json.write_text(json.dumps(_page_button_audit_payload(project_dir, rows, docs_path), ensure_ascii=False, indent=2), encoding="utf-8")
        runtime_csv = _write_page_button_audit_csv(project_dir, rows)
        capability_manifest = _write_meta_workflow_capability_manifest(project_dir, rows)
        output_path = export_root / "meta_page_button_audit_package.zip"
        candidate_paths = [runtime_json, runtime_csv, capability_manifest, docs_path]
        if project_dir is not None:
            candidate_paths.extend(
                [
                    project_dir / "protocol" / "search_strategy_v2" / "search_execution_manifest.json",
                    project_dir / "literature" / "literature_acquisition_organization_manifest.json",
                    project_dir / "literature" / "literature_citation_manifest.json",
                    project_dir / "literature" / "literature_library_export.ris",
                    project_dir / "literature" / "literature_library_export.bib",
                    project_dir / "literature" / "literature_library_export.csl.json",
                    project_dir / "literature" / "literature_register.csv",
                    project_dir / "screening" / "screening_organization_manifest.json",
                    project_dir / "screening" / "title_abstract_screening_decisions.csv",
                    project_dir / "fulltext" / "fulltext_retrieval_manifest.json",
                    project_dir / "fulltext" / "fulltext_retrieval_register.csv",
                    project_dir / "exports" / "fulltext_retrieval_package.zip",
                    project_dir / "extraction" / "extraction_organization_manifest.json",
                    project_dir / "exports" / "extraction_organization_package.zip",
                    project_dir / "quality" / "quality_organization_manifest.json",
                    project_dir / "exports" / "quality_assessment_package.zip",
                    project_dir / "analysis" / "statistics_results_manifest.json",
                    project_dir / "exports" / "statistics_results_package.zip",
                    project_dir / "figures" / "figure_results_manifest.json",
                    project_dir / "exports" / "figure_results_package.zip",
                    project_dir / "reports" / "prisma_reporting_manifest.json",
                    project_dir / "exports" / "prisma_reporting_package.zip",
                    project_dir / "reports" / "formal_report_delivery_manifest.json",
                    project_dir / "exports" / "formal_report_package.zip",
                    project_dir / "exports" / "literature_organization_package.zip",
                ]
            )
        included: list[str] = []
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as package:
            for path in candidate_paths:
                if not path.exists() or not path.is_file():
                    continue
                if project_dir is not None:
                    try:
                        archive_name = str(path.relative_to(project_dir))
                    except ValueError:
                        archive_name = f"docs/{path.name}" if path == docs_path else path.name
                else:
                    archive_name = f"docs/{path.name}" if path == docs_path else path.name
                if archive_name in included:
                    continue
                package.write(path, archive_name)
                included.append(archive_name)
            package.writestr(
                "meta_page_button_audit_package_manifest.json",
                json.dumps(
                    {
                        "schema_version": "meta_page_button_audit_package.v1",
                        "project_dir": str(project_dir or ""),
                        "included_count": len(included),
                        "included_paths": included,
                        "boundaries": [
                            "This package contains UI button/module audit and existing local workflow organization artifacts only.",
                            "It does not run retrieval, screening, full-text parsing, statistics, or report generation.",
                            "Runtime validation and desktop walkthrough are still required before completion can be claimed.",
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
        return output_path


    def _write_meta_preview_delivery_package(project_dir: Path | None, rows: list[tuple[str, str, str, str]], docs_path: Path) -> Path:
        import zipfile

        export_root = (project_dir / "audit") if project_dir is not None else (default_storage_root() / "meta_analysis" / "audit")
        export_root.mkdir(parents=True, exist_ok=True)
        generated_paths = [
            _write_page_button_audit_csv(project_dir, rows),
            _write_meta_workflow_capability_manifest(project_dir, rows),
            _write_page_button_audit_package(project_dir, rows, docs_path),
        ]
        if project_dir is not None:
            generated_paths.extend(
                [
                    _write_search_execution_manifest(project_dir),
                    _write_search_strategy_package(project_dir),
                    _write_literature_capability_artifact_index(project_dir),
                    _write_literature_organization_package(project_dir),
                    _write_fulltext_retrieval_package(project_dir),
                    _write_extraction_organization_package(project_dir),
                    _write_quality_assessment_package(project_dir),
                    _write_statistics_results_package(project_dir),
                    _write_figure_results_package(project_dir),
                    _write_prisma_reporting_package(project_dir),
                    _write_formal_report_package(project_dir),
                ]
            )
        generated_paths.append(_write_meta_preview_integrity_manifest(project_dir, rows, docs_path))
        candidate_paths = [docs_path, *generated_paths]
        if project_dir is not None:
            candidate_paths.extend(
                [
                    project_dir / "protocol" / "search_strategy_v2" / "search_strategy_drafts.json",
                    project_dir / "protocol" / "search_strategy_v2" / "search_strategy_confirmed.json",
                    project_dir / "protocol" / "search_strategy_v2" / "search_strategy_draft.md",
                    project_dir / "protocol" / "search_strategy_v2" / "search_strategy_draft.txt",
                    project_dir / "literature" / "literature_records.json",
                    project_dir / "literature" / "import_batches.json",
                    project_dir / "literature" / "library_manifest.json",
                    project_dir / "screening" / "screening_organization_manifest.json",
                    project_dir / "screening" / "title_abstract_screening_decisions.csv",
                    project_dir / "fulltext" / "fulltext_retrieval_manifest.json",
                    project_dir / "fulltext" / "fulltext_retrieval_register.csv",
                    project_dir / "exports" / "fulltext_retrieval_package.zip",
                    project_dir / "extraction" / "extraction_organization_manifest.json",
                    project_dir / "exports" / "extraction_organization_package.zip",
                    project_dir / "quality" / "quality_organization_manifest.json",
                    project_dir / "exports" / "quality_assessment_package.zip",
                    project_dir / "analysis" / "statistics_results_manifest.json",
                    project_dir / "exports" / "statistics_results_package.zip",
                    project_dir / "figures" / "figure_results_manifest.json",
                    project_dir / "exports" / "figure_results_package.zip",
                    project_dir / "reports" / "prisma_reporting_manifest.json",
                    project_dir / "exports" / "prisma_reporting_package.zip",
                    project_dir / "reports" / "formal_report_delivery_manifest.json",
                    project_dir / "exports" / "formal_report_package.zip",
                ]
            )
        output_path = export_root / "meta_preview_delivery_package.zip"
        included: list[str] = []
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as package:
            for path in candidate_paths:
                if not path.exists() or not path.is_file():
                    continue
                if project_dir is not None:
                    try:
                        archive_name = str(path.relative_to(project_dir))
                    except ValueError:
                        archive_name = f"docs/{path.name}" if path == docs_path else path.name
                else:
                    archive_name = f"docs/{path.name}" if path == docs_path else path.name
                if archive_name in included or archive_name == "audit/meta_preview_delivery_package.zip":
                    continue
                package.write(path, archive_name)
                included.append(archive_name)
            package.writestr(
                "meta_preview_delivery_package_manifest.json",
                json.dumps(
                    {
                        "schema_version": "meta_preview_delivery_package.v1",
                        "project_dir": str(project_dir or ""),
                        "included_count": len(included),
                        "included_paths": included,
                        "boundaries": [
                            "This package is a local audit and literature/search organization handoff.",
                            "It does not execute external database retrieval, import new literature, make reviewer decisions, parse full text, run statistics, or generate final reports.",
                            "Desktop walkthrough, syntax checks, tests, and real project validation remain required before completion can be claimed.",
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
        return output_path


    def _write_meta_preview_integrity_manifest(project_dir: Path | None, rows: list[tuple[str, str, str, str]], docs_path: Path) -> Path:
        import hashlib

        export_root = (project_dir / "audit") if project_dir is not None else (default_storage_root() / "meta_analysis" / "audit")
        export_root.mkdir(parents=True, exist_ok=True)
        expected_paths = [docs_path]
        if project_dir is not None:
            expected_paths.extend(
                [
                    project_dir / "audit" / "meta_page_button_audit_runtime.json",
                    project_dir / "audit" / "meta_page_button_audit_runtime.csv",
                    project_dir / "audit" / "meta_workflow_capability_manifest.json",
                    project_dir / "audit" / "meta_page_button_audit_package.zip",
                    project_dir / "audit" / "meta_preview_delivery_package.zip",
                    project_dir / "protocol" / "search_strategy_v2" / "search_execution_manifest.json",
                    project_dir / "exports" / "search_strategy_package.zip",
                    project_dir / "literature" / "literature_acquisition_organization_manifest.json",
                    project_dir / "literature" / "literature_citation_manifest.json",
                    project_dir / "literature" / "literature_library_export.ris",
                    project_dir / "literature" / "literature_library_export.bib",
                    project_dir / "literature" / "literature_library_export.csl.json",
                    project_dir / "literature" / "literature_register.csv",
                    project_dir / "literature" / "literature_capability_artifact_index.json",
                    project_dir / "exports" / "literature_organization_package.zip",
                    project_dir / "screening" / "screening_organization_manifest.json",
                    project_dir / "screening" / "title_abstract_screening_decisions.csv",
                    project_dir / "fulltext" / "fulltext_retrieval_manifest.json",
                    project_dir / "fulltext" / "fulltext_retrieval_register.csv",
                    project_dir / "exports" / "fulltext_retrieval_package.zip",
                    project_dir / "extraction" / "extraction_organization_manifest.json",
                    project_dir / "exports" / "extraction_organization_package.zip",
                    project_dir / "quality" / "quality_organization_manifest.json",
                    project_dir / "exports" / "quality_assessment_package.zip",
                    project_dir / "analysis" / "statistics_results_manifest.json",
                    project_dir / "exports" / "statistics_results_package.zip",
                    project_dir / "figures" / "figure_results_manifest.json",
                    project_dir / "exports" / "figure_results_package.zip",
                    project_dir / "reports" / "prisma_reporting_manifest.json",
                    project_dir / "exports" / "prisma_reporting_package.zip",
                    project_dir / "reports" / "formal_report_delivery_manifest.json",
                    project_dir / "exports" / "formal_report_package.zip",
                ]
            )
        entries: list[dict[str, object]] = []
        for path in expected_paths:
            exists = path.exists() and path.is_file()
            digest = ""
            size = 0
            if exists:
                data = path.read_bytes()
                digest = hashlib.sha256(data).hexdigest()
                size = len(data)
            if project_dir is not None:
                try:
                    label = str(path.relative_to(project_dir))
                except ValueError:
                    label = f"docs/{path.name}" if path == docs_path else str(path)
            else:
                label = f"docs/{path.name}" if path == docs_path else path.name
            entries.append({"path": label, "exists": exists, "size_bytes": size, "sha256": digest})
        output_path = export_root / "meta_preview_integrity_manifest.json"
        payload = {
            "schema_version": "meta_preview_integrity_manifest.v1",
            "project_dir": str(project_dir or ""),
            "button_or_module_count": len(rows),
            "checked_count": len(entries),
            "present_count": len([item for item in entries if item["exists"]]),
            "missing_count": len([item for item in entries if not item["exists"]]),
            "artifacts": entries,
            "boundaries": [
                "This manifest provides local file presence and SHA-256 hashes only.",
                "It does not validate runtime behavior, scientific correctness, database access, or production readiness.",
                "Missing artifacts can be generated from their corresponding UI buttons when project prerequisites exist.",
            ],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path


    def _audit_page_route(page_name: str) -> str:
        return {
            "项目首页": "workflow_home",
            "页面能力审计": "page_button_audit",
            "研究问题与 PICO": "pico_workspace",
            "检索策略": "search_strategy",
            "文献库与导入": "literature_import",
            "去重与筛选": "screening_review",
            "排除标准": "exclusion_criteria",
            "标题摘要筛选": "title_abstract_screening",
            "全文管理": "fulltext_management",
            "数据提取": "manual_extraction",
            "AI 辅助提取": "ai_extraction",
            "质量评价": "quality_assessment",
            "分析计划": "analysis_plan",
            "统计分析": "statistics_analysis",
            "图表结果": "figure_results",
            "PRISMA": "prisma",
            "报告导出": "report_export",
            "复现包": "reproducibility_package",
        }.get(page_name, "")


    def _button_audit_rows() -> list[tuple[str, str, str, str]]:
        return [
            ("项目首页", "新建 / 打开项目", "创建或校验 Meta 项目 manifest、config、目录结构", "本地项目管理，不联网"),
            ("项目首页", "新建 Meta 项目", "切换到 workflow_home，显示项目创建表单", "仅导航到本地项目管理界面"),
            ("项目首页", "打开已有项目", "打开本地目录选择器并校验 Meta 项目 manifest/config", "只读取本地项目目录"),
            ("项目首页", "选择保存位置", "打开本地目录选择器，填充项目保存位置", "不创建项目"),
            ("项目首页", "创建项目", "调用 create_meta_analysis_project 创建项目目录、manifest、config 和基础结构", "本地写入，不联网"),
            ("项目首页", "选择已有项目文件夹", "打开本地目录选择器并调用 open_meta_analysis_project 校验项目", "只打开本地已有项目"),
            ("项目首页", "返回首页 / 返回模块首页", "返回 Meta 模块首页或上一级入口", "仅导航"),
            ("项目首页", "继续：研究问题 / PICO", "跳转 pico_workspace", "仅导航"),
            ("项目首页", "模块：项目管理表单", "接入项目名称、研究主题、保存位置、最终项目路径预览和本地项目打开/创建流程", "只管理本地项目目录"),
            ("项目首页", "模块：流程进度摘要", "读取 workflow integration state，展示各页面 artifact 数量、状态和下一步", "只读展示，不推进流程"),
            ("无项目空状态", "继续：研究问题 / PICO（禁用）", "项目未创建/打开前保持 disabled，引导用户先完成项目管理", "禁用按钮不执行业务动作"),
            ("页面能力审计", "导出审计表 CSV", "写入 audit/meta_page_button_audit_runtime.csv，包含页面、按钮或模块、接入功能、边界和 route_key", "只导出审计表，不运行流程"),
            ("页面能力审计", "导出审计记录 JSON", "写入 audit/meta_page_button_audit_runtime.json，包含页面、按钮/模块、接入功能和边界", "只导出审计 JSON，不运行流程"),
            ("页面能力审计", "导出能力总清单", "写入 audit/meta_workflow_capability_manifest.json，汇总 route/page/button-or-module 覆盖和全流程 artifact 存在状态", "只检查本地 artifact 是否存在"),
            ("页面能力审计", "导出页面审计包", "写入 audit/meta_page_button_audit_package.zip，打包按钮/模块审计 JSON、Markdown 审计表和现有全流程整理 manifest/package", "只打包本地 artifact，不运行流程"),
            ("页面能力审计", "导出完整交付包", "写入 audit/meta_preview_delivery_package.zip，一键生成并打包页面审计、能力总清单、检索、文献、筛选、全文、提取、质量、统计、图表、PRISMA 和报告交付包", "本地交付包，不运行外部检索或声明正式结论"),
            ("页面能力审计", "导出交付校验清单", "写入 audit/meta_preview_integrity_manifest.json，记录关键交付 artifact 是否存在、大小和 SHA-256", "只做本地文件校验，不验证运行时行为"),
            ("页面能力审计", "跳转到选中页面", "根据审计表选中行的页面名称跳转到对应 Meta route", "只导航，不执行业务动作"),
            ("页面能力审计", "模块：页面/按钮/模块审计表", "展示 runtime 审计 rows，包含页面、按钮或模块、接入功能、边界和 route_key", "只读展示，导出需用户点击按钮"),
            ("研究问题与 PICO", "生成 / 保存 / 确认 PICO", "PICOWorkspaceService 草稿、人工编辑和 confirmed protocol", "不自动执行检索"),
            ("研究问题与 PICO", "生成 PICO 草稿", "PICOWorkspaceService 根据研究问题生成 PICO/PICOS/PECO 草稿", "草稿不进入正式流程"),
            ("研究问题与 PICO", "保存草稿编辑", "保存人工编辑后的 PICO draft 和 UI draft 字段", "不自动确认 protocol"),
            ("研究问题与 PICO", "确认研究问题", "写入 protocol/pico_workspace_confirmed.json", "确认后仍需人工生成检索策略"),
            ("研究问题与 PICO", "下一步：检索策略", "跳转 search_strategy", "仅导航"),
            ("研究问题与 PICO", "模块：研究问题输入与 PICO/PICOS/PECO 草稿字段", "接入 protocol/pico_workspace_draft.json、confirmed protocol 和 UI draft 字段", "草稿必须人工确认后才进入正式流程"),
            ("研究问题与 PICO", "模块：已确认研究问题卡片", "读取 protocol/pico_workspace_confirmed.json，展示已确认研究问题、PICO、meta type 和备注", "只读展示 confirmed 状态"),
            ("检索策略", "生成检索策略", "SearchStrategyBuilderService 生成 PubMed/WOS/Embase/Cochrane/CNKI/WanFang/VIP 草稿", "非 PubMed 数据库只生成策略"),
            ("检索策略", "确认 / 导出 / 复制检索式", "保存 reviewer confirmation，导出 TXT/MD/JSON，复制当前查询", "不自动导入文献"),
            ("检索策略", "保存当前编辑", "保存当前数据库检索式编辑", "不自动确认检索式"),
            ("检索策略", "确认当前检索式", "确认当前数据库检索式", "不自动执行非 PubMed 数据库"),
            ("检索策略", "确认全部检索式", "确认全部数据库检索式", "不自动执行非 PubMed 数据库"),
            ("检索策略", "导出 TXT / MD / JSON", "导出检索策略 TXT、Markdown 和 JSON artifact", "只导出本地策略"),
            ("检索策略", "复制检索式", "复制当前编辑器中的检索式到剪贴板", "不联网"),
            ("检索策略", "复制数据库入口", "复制当前数据库的人工检索入口 URL，包括 PubMed/WOS/Embase/Cochrane/CNKI/WanFang/VIP", "不自动打开浏览器，不联网"),
            ("检索策略", "导出检索执行清单", "写入 protocol/search_strategy_v2/search_execution_manifest.json，记录 PubMed testing 执行路径和各外部数据库人工入口", "不证明数据库权限或检索完整性"),
            ("检索策略", "导出检索策略包", "写入 exports/search_strategy_package.zip，打包检索策略草稿、确认记录、TXT/MD/JSON 和执行清单", "只打包本地检索策略 artifact，不执行检索"),
            ("检索策略", "执行 PubMed testing-level 检索", "PubMedSearchService 执行 reviewer-confirmed PubMed 查询", "需要人工选择 candidates"),
            ("检索策略", "选择加入文献库 / 忽略本批次", "PubMedCandidatesHandoffService 写入或跳过候选文献", "不自动去重或筛选"),
            ("检索策略", "全选 / 取消全选", "选择或清空 PubMed candidate table 当前行选择", "只改变 UI selection"),
            ("检索策略", "选择加入文献库", "把选中的 PubMed candidates 写入文献库 handoff", "不自动去重或筛选"),
            ("检索策略", "忽略本批次", "将当前 PubMed candidate 批次标记为忽略/不导入", "不删除远端数据"),
            ("检索策略", "下一步：文献库与导入", "跳转 literature_import", "仅导航"),
            ("检索策略", "模块：数据库列表与检索式编辑器", "接入 search_strategy_drafts/confirmed，按数据库展示草稿、确认检索式和人工入口", "非 PubMed 数据库不在线执行"),
            ("检索策略", "模块：PubMed 候选文献表与详情", "读取 protocol/pubmed_candidates preview/report，展示 PMID、题名、摘要、期刊和处理状态", "候选文献需人工选择后才进入文献库"),
            ("文献库与导入", "导入选中文献", "将 PubMed candidates 写入 LiteratureLibraryService", "导入后仍需去重"),
            ("文献库与导入", "全选 / 取消全选", "选择或清空候选文献列表当前选择", "只改变 UI selection"),
            ("文献库与导入", "忽略本批次", "清空/忽略当前候选批次选择，不写入文献库", "不删除文献库记录"),
            ("文献库与导入", "选择文件导入", "MultiSourceLiteratureImportService 导入本地 PubMed XML/MEDLINE、WOS text/tab、RIS、Embase RIS、Cochrane RIS、CNKI 风格导出", "文件导入，不是在线抓取"),
            ("文献库与导入", "筛选 / 摘要 / 备注", "过滤文献表、导出摘要、保存备注", "不改变筛选结论"),
            ("文献库与导入", "导出文献库摘要", "导出当前文献库摘要", "只导出本地摘要"),
            ("文献库与导入", "保存备注", "保存页面备注 / 操作反馈", "不改变文献筛选结论"),
            ("文献库与导入", "复制 PubMed 链接 / 复制 DOI 链接", "根据当前文献 PMID/DOI 生成 https://pubmed.ncbi.nlm.nih.gov/{pmid}/ 或 https://doi.org/{doi} 并复制到剪贴板", "不自动打开浏览器，不联网"),
            ("文献库与导入", "复制引用信息", "基于当前 normalized literature record 复制标题、作者、年份、期刊、DOI、PMID 和来源", "不调用外部引用管理器"),
            ("文献库与导入", "导出引用整理清单", "写入 literature/literature_citation_manifest.json，汇总全部文献 citation text、DOI/PubMed 链接和缺失字段", "不调用 Crossref、PubMed、Zotero 或 EndNote"),
            ("文献库与导入", "导出 RIS", "写入 literature/literature_library_export.ris，供 EndNote/Zotero 等引用工具人工导入", "本地 RIS 生成，不调用外部引用管理器"),
            ("文献库与导入", "导出 BibTeX", "写入 literature/literature_library_export.bib，供 BibTeX/Zotero 等引用工具人工导入", "本地 BibTeX 生成，不调用外部引用管理器"),
            ("文献库与导入", "导出 CSL-JSON", "写入 literature/literature_library_export.csl.json，供 Zotero/Pandoc citeproc 等工作流人工导入", "本地 CSL-JSON 生成，不调用外部引用管理器"),
            ("文献库与导入", "导出文献台账 CSV", "写入 literature/literature_register.csv，包含题名、作者、年份、期刊、DOI/PMID、链接和筛选/去重状态", "本地 CSV 台账，不改变决策状态"),
            ("文献库与导入", "导出文献整理包", "写入 exports/literature_organization_package.zip，打包文献库、引用清单、RIS/BibTeX/CSL-JSON、检索/筛选/全文整理 manifest", "本地打包，不包含自动下载全文"),
            ("文献库与导入", "生成全部文献整理产物", "写入 literature/literature_capability_artifact_index.json，并生成检索、引用、筛选、全文和文献整理包 artifact", "只生成本地整理产物，不执行业务流程"),
            ("文献库与导入", "导出获取/整理清单", "写入 literature/literature_acquisition_organization_manifest.json，汇总 PubMed preview、本地导入、文献库、去重、筛选、全文组织状态", "只汇总 artifact，不推进流程"),
            ("文献库与导入", "下一步：去重与筛选", "跳转 screening_review", "仅导航"),
            ("文献库与导入", "模块：PubMed 候选列表", "读取 PubMed handoff preview，支持全选、取消、导入或忽略候选批次", "候选导入不等于去重或筛选"),
            ("文献库与导入", "模块：文献库表格与详情", "读取 literature/literature_records.json、import_batches.json 和 library_manifest.json，展示题名、作者、年份、来源和状态", "只展示/整理 normalized library"),
            ("文献库与导入", "模块：文献备注区", "写入本地 literature notes，记录页面备注和操作反馈", "备注不改变筛选决策"),
            ("去重与筛选", "生成重复组", "DedupReviewV2Service 建立重复候选组", "不删除原始文献"),
            ("去重与筛选", "保存人工决定", "保存 keep/merge/master/not-duplicate/skip 决策", "人工决定优先"),
            ("去重与筛选", "生成去重后文献库", "导出 deduplicated literature", "不破坏源 library"),
            ("去重与筛选", "创建标题摘要筛选队列", "TitleAbstractScreeningV2Service 创建 reviewer queue", "队列不等于筛选决定"),
            ("去重与筛选", "导出筛选整理清单", "写入 screening/screening_organization_manifest.json，汇总重复组、去重决定、去重后文献、筛选队列、筛选决定和全文需求", "不自动推进 PRISMA、全文或提取"),
            ("去重与筛选", "纳入 / 排除 / 不确定 / 需要全文", "快速写入当前标题摘要筛选记录的人工决策", "人工决定，不调用 AI 自动判定"),
            ("去重与筛选", "保存并下一篇", "保存当前筛选决定并推进到下一条未筛选记录", "只推进本地 UI 队列"),
            ("去重与筛选", "保存筛选决定", "保存当前记录的标题摘要筛选人工决定", "不自动推进全文或 PRISMA"),
            ("去重与筛选", "下一步：排除标准", "跳转 exclusion_criteria", "仅导航"),
            ("去重与筛选", "模块：重复组列表与候选详情", "读取 deduplication duplicate groups、review queue 和人工决策，展示 master/merge/not duplicate 信息", "不自动删除或合并源文献"),
            ("去重与筛选", "模块：标题摘要快速筛选区", "读取/写入 screening queue 和人工 decision，支持 include/exclude/uncertain/needs-full-text", "人工筛选决定优先"),
            ("排除标准", "保存草稿 / 确认 / 新增理由", "ExclusionCriteriaLibraryService 管理项目排除标准", "不自动排除文献"),
            ("排除标准", "保存排除标准草稿", "保存项目排除标准草稿", "不自动排除文献"),
            ("排除标准", "确认排除标准", "写入 confirmed exclusion criteria artifact", "确认标准不自动应用到既有文献"),
            ("排除标准", "新增理由", "增加自定义排除理由", "不自动排除文献"),
            ("排除标准", "下一步：标题摘要筛选", "跳转 title_abstract_screening", "仅导航"),
            ("排除标准", "模块：排除标准库与自定义理由", "接入 screening/exclusion_criteria_library_v1.json、selection 和 confirmed artifact", "标准确认后才作为筛选理由来源"),
            ("标题摘要筛选", "生成筛选队列 / 保存人工决定", "保存 include/exclude/uncertain/needs-full-text 决策", "AI/model 建议不写最终决定"),
            ("标题摘要筛选", "生成筛选队列", "TitleAbstractScreeningV2Service 创建 reviewer queue", "队列不等于筛选决定"),
            ("标题摘要筛选", "保存人工决定", "保存当前标题摘要筛选人工决定", "不自动推进全文"),
            ("标题摘要筛选", "导出筛选决定 CSV", "写入 screening/title_abstract_screening_decisions.csv，导出现有筛选队列、人工决定、排除理由和备注", "只导出现有状态，不生成新决定"),
            ("标题摘要筛选", "下一步：全文管理", "跳转 fulltext_management", "仅导航"),
            ("标题摘要筛选", "模块：筛选队列列表与决策表单", "接入 title_abstract_queue_v2.json 和 decisions_v2.json，展示题名摘要、排除理由和备注", "不由 AI 自动写最终决定"),
            ("全文管理", "建立全文队列", "FullTextManagementService 从筛选结果创建全文 registry", "不自动下载 PDF"),
            ("全文管理", "上传全文 / OCR 识别 PDF", "绑定本地 PDF，FullTextParsingService 生成 testing-level 解析 artifact", "OCR/解析不写最终提取值"),
            ("全文管理", "上传全文", "绑定本地 PDF 文件到全文 registry 记录", "不下载 PDF"),
            ("全文管理", "OCR 识别 PDF", "FullTextParsingService 对本地 PDF 执行 testing-level OCR/解析", "解析结果不写最终提取值"),
            ("全文管理", "全文确认 / 标记无法获取 / 保存全文筛选", "更新全文状态、排除原因和 eligibility 决定", "需人工复核"),
            ("全文管理", "标记无法获取", "将全文状态标记为 unavailable", "人工状态，不绕过全文获取"),
            ("全文管理", "全文确认", "确认当前记录全文已获取/可用", "需人工复核"),
            ("全文管理", "保存全文状态", "保存当前全文管理状态", "不自动筛选全文"),
            ("全文管理", "保存全文筛选", "保存全文 eligibility 状态和排除原因", "不自动推进数据提取"),
            ("全文管理", "复制获取链接", "根据选中文献 DOI/PMID/PMCID 复制 DOI、PubMed、PMC 获取链接集合", "不自动打开浏览器，不联网，不下载全文"),
            ("全文管理", "导出全文获取 CSV", "写入 fulltext/fulltext_retrieval_register.csv，导出 DOI/PubMed/PMC 链接、本地 PDF 路径和人工获取状态台账", "只导出现有全文候选，不下载全文"),
            ("全文管理", "导出全文获取清单", "写入 fulltext/fulltext_retrieval_manifest.json，汇总 DOI/PubMed/PMC 链接、本地 PDF 路径和人工获取状态", "不自动下载全文，不绕过访问权限"),
            ("全文管理", "导出全文获取包", "写入 exports/fulltext_retrieval_package.zip，打包全文获取清单、CSV、全文管理/解析 manifest 和缺失全文报告", "只打包本地全文获取 artifact，不下载全文"),
            ("全文管理", "下一步：数据提取", "跳转 manual_extraction", "仅导航"),
            ("全文管理", "模块：全文 registry 列表与状态编辑区", "接入 fulltext_management_registry_v1、fulltext_registry、parse manifest 和 eligibility records", "不自动下载全文或绕过权限"),
            ("全文管理", "模块：全文获取链接集合", "根据 DOI/PMID/PMCID 生成 DOI、PubMed、PMC 链接用于人工获取", "只复制链接，不打开外部站点"),
            ("数据提取", "新建 study unit / 新建提取行", "ManualExtractionEffectRowService 建立人工提取结构", "不生成 analysis-ready dataset"),
            ("数据提取", "新建 study unit", "创建人工提取 study unit", "不生成 analysis-ready dataset"),
            ("数据提取", "新建提取行", "创建人工 effect row draft", "不运行统计"),
            ("数据提取", "保存 / 完成 / 用户确认 / 标记缺失", "保存结构化提取行并记录人工确认", "不运行统计"),
            ("数据提取", "保存结构化草稿", "保存当前结构化提取字段为 draft", "不确认最终提取"),
            ("数据提取", "完成本行提取", "将当前 effect row 标记为完成", "不运行统计"),
            ("数据提取", "用户确认", "记录用户确认当前提取行", "不运行统计"),
            ("数据提取", "标记缺失数据", "将当前提取字段标记为缺失数据", "不做插补"),
            ("数据提取", "CSV 模板 / 当前导出 / 草稿导入", "导出模板和当前表，CSV 导入为 draft", "冲突不静默覆盖"),
            ("数据提取", "导出空模板 CSV", "导出 manual_extraction_template.csv", "只导出模板"),
            ("数据提取", "导出当前 CSV", "导出 manual_extraction_current.csv", "只导出现有提取行"),
            ("数据提取", "导入 CSV 草稿", "导入 CSV 为 extraction draft", "冲突不静默覆盖"),
            ("数据提取", "导出提取整理清单", "写入 extraction/extraction_organization_manifest.json，汇总 study unit、effect row、结构化提取、校验和 AI 建议状态", "只汇总提取 artifact，不生成分析数据集"),
            ("数据提取", "导出提取整理包", "写入 exports/extraction_organization_package.zip，打包提取 JSON、模板/当前 CSV、校验报告和 AI 建议记录", "只打包本地提取 artifact，不运行统计"),
            ("数据提取", "下一步：AI 辅助提取", "跳转 ai_extraction", "仅导航"),
            ("数据提取", "模块：文献、study unit、effect row 三列表", "读取可提取文献、study units 和 effect rows，支持选择后填充结构化表单", "选择不会自动确认数据"),
            ("数据提取", "模块：结构化提取表单", "接入研究基本信息、PICO/PECO、效应量和诊断字段，写入 manual extraction draft", "用户确认前不生成 analysis-ready dataset"),
            ("AI 辅助提取", "接受 / 拒绝 / 写入人工草稿", "AIAssistedExtractionQueueService 审核建议并写入 draft", "accepted 仍非最终值"),
            ("AI 辅助提取", "接受建议", "将选中 AI suggestion 标记为 accepted", "不直接写最终提取"),
            ("AI 辅助提取", "拒绝建议", "将选中 AI suggestion 标记为 rejected", "不删除人工草稿"),
            ("AI 辅助提取", "写入人工草稿", "将 accepted suggestion 应用为人工提取 draft", "仍需人工确认"),
            ("AI 辅助提取", "下一步：质量评价", "跳转 quality_assessment", "仅导航"),
            ("AI 辅助提取", "模块：AI suggestion 队列", "读取 extraction_ai_suggestion_queue/application，展示 confidence、状态和建议 ID", "建议必须人工审核"),
            ("质量评价", "保存评分草稿 / 已确认 / 导出 CSV", "QualityAssessmentService 保存、确认和导出质量评价", "不自动 GRADE"),
            ("质量评价", "保存评分草稿", "保存当前质量评价 domain rating、overall rating 和备注为草稿", "不自动确认"),
            ("质量评价", "已确认", "将当前质量评价记录标记为用户确认", "不自动 GRADE，不替代人工评分"),
            ("质量评价", "导出 CSV", "写入 exports/quality_assessment_v1.csv", "只导出质量评价表"),
            ("质量评价", "导出 JSON", "写入 quality/quality_assessment_v1_export.json，导出质量评价 v1 记录", "只导出本地质量评价记录"),
            ("质量评价", "导出质量评价包", "写入 exports/quality_assessment_package.zip，打包质量评价 JSON/CSV、summary、alias 和组织清单", "只打包质量评价 artifact，不改变评分状态"),
            ("质量评价", "下一步：分析计划", "跳转 analysis_plan", "仅导航"),
            ("质量评价", "模块：质量评价研究列表与评分表单", "接入 quality_assessment_records_v1、summary 和 tool registry，展示 domain rating、overall rating 和备注", "不自动 GRADE，不替代人工确认"),
            ("分析计划", "生成 / 保存 / 确认分析计划", "AnalysisPlanService 生成并锁定 confirmed plan", "确认不代表统计已运行"),
            ("分析计划", "生成分析计划草稿", "AnalysisPlanService 基于 protocol、提取、质量记录生成 draft", "不运行统计"),
            ("分析计划", "保存计划编辑", "保存人工编辑后的 analysis plan draft", "不确认计划"),
            ("分析计划", "确认分析计划", "写入 confirmed analysis plan", "不运行统计"),
            ("分析计划", "模块：分析计划编辑表单", "接入 draft/confirmed analysis plan，展示效应量类型、模型偏好、亚组/敏感性/发表偏倚计划", "确认计划不等于运行统计"),
            ("分析计划", "模块：统计前置审核区", "接入 effect normalization precheck、pairwise executor 和 statistical result review", "testing-level 结果需人工审核"),
            ("分析计划", "刷新效应量标准化预检查", "刷新并展示 effect normalization precheck 状态", "只刷新页面提示，不改写研究结论"),
            ("分析计划", "运行 pairwise executor", "PairwiseMetaExecutorService 基于 confirmed analysis plan 运行 testing-level pairwise 计算", "结果必须经人工审核，不能直接进入最终报告"),
            ("分析计划", "接受进入报告草稿 / 标记需要修订 / 不纳入报告 / 申请报告就绪", "StatisticalResultReviewService 记录统计结果审核状态和报告就绪申请", "只记录审核流转，不代表投稿级结论"),
            ("分析计划", "接受进入报告草稿", "StatisticalResultReviewService 将统计结果标记为可进入报告草稿", "不代表投稿级结论"),
            ("分析计划", "标记需要修订", "StatisticalResultReviewService 将统计结果标记为需要修订", "不改写统计结果"),
            ("分析计划", "不纳入报告", "StatisticalResultReviewService 将统计结果标记为不进入报告", "不删除统计结果"),
            ("分析计划", "申请报告就绪", "StatisticalResultReviewService 申请或授予报告就绪状态", "仍需满足审核 gate"),
            ("分析计划", "下一步：统计分析", "跳转 statistics_analysis", "仅导航"),
            ("统计分析", "运行统计分析", "MetaStatisticsEngineService 从 confirmed plan 运行 testing-level 统计", "不生成医学结论"),
            ("统计分析", "导出统计结果清单", "写入 analysis/statistics_results_manifest.json，汇总 confirmed plan、analysis manifest、run 和 result 文件", "只汇总本地统计 artifact，不运行统计"),
            ("统计分析", "导出统计结果包", "写入 exports/statistics_results_package.zip，打包分析计划、analysis manifest、统计 run/result 和审核记录", "只打包现有统计 artifact，不认证结果可发布"),
            ("统计分析", "下一步：图表结果", "跳转 figure_results", "仅导航"),
            ("统计分析", "模块：统计结果 JSON 预览", "读取 latest analysis result JSON 并展示 run_count、输入校验和 testing-level 结果", "不生成医学结论"),
            ("图表结果", "图表 artifact 表", "读取现有 figure/result artifact", "本页不重新计算统计"),
            ("图表结果", "导出图表结果清单", "写入 figures/figure_results_manifest.json，汇总 figure artifact 和统计 result 文件", "只汇总现有图表/结果，不生成新图"),
            ("图表结果", "导出图表结果包", "写入 exports/figure_results_package.zip，打包 figures 目录和统计 result 文件", "只打包现有图表/结果，不重跑统计"),
            ("图表结果", "下一步：PRISMA", "跳转 prisma", "仅导航"),
            ("图表结果", "模块：figure artifact 表", "读取 figures/figure_artifacts.json 和 analysis/results，展示 figure_id、type、format、path", "不重新计算统计或渲染新图"),
            ("PRISMA", "生成 summary / 导出 Markdown", "PRISMAService 从真实流程记录汇总数字", "不伪造 PRISMA 计数"),
            ("PRISMA", "生成 PRISMA summary", "PRISMAService 汇总并保存 reports/prisma_flow_summary.json", "数字来自本地流程记录"),
            ("PRISMA", "导出 Markdown", "导出 reports/prisma_flow_summary.md", "不伪造 PRISMA 计数"),
            ("PRISMA", "导出 PRISMA 报告包", "写入 exports/prisma_reporting_package.zip，生成并打包 PRISMA summary JSON/Markdown、简化 flow Markdown/SVG 和 manifest", "不改写源流程记录，不伪造计数"),
            ("PRISMA", "下一步：报告导出", "跳转 report_export", "仅导航"),
            ("PRISMA", "模块：PRISMA summary 卡片", "读取 reports/prisma_flow_summary.json，展示 identified、duplicates、screened、excluded、included", "数字来自本地流程记录"),
            ("报告导出", "生成草稿 / HTML / DOCX", "FormalMarkdownReportBuilder 和 PublicationExportService 输出 testing report", "非投稿级报告"),
            ("报告导出", "生成报告草稿", "FormalMarkdownReportBuilder 生成 Markdown 草稿", "testing 报告"),
            ("报告导出", "导出 HTML", "PublicationExportService 导出 HTML testing report", "非投稿级报告"),
            ("报告导出", "导出 DOCX", "PublicationExportService 导出 DOCX testing report", "非投稿级报告"),
            ("报告导出", "打开报告位置", "复制项目 reports 目录绝对路径到剪贴板并提示位置", "不自动打开 Finder 或外部应用"),
            ("报告导出", "导出报告交付包", "写入 exports/formal_report_package.zip，打包 Markdown、HTML、DOCX、report manifest、PRISMA artifact 和交付清单", "testing 报告包，不代表投稿级交付"),
            ("报告导出", "下一步：复现包", "跳转 reproducibility_package", "仅导航"),
            ("报告导出", "模块：报告预览", "读取 reports/formal_meta_report.md 并展示 Markdown 前 12000 字符", "预览不代表投稿级审稿完成"),
            ("复现包", "导出可复现项目包", "PublicationExportService 打包关键 artifact", "用于内部迁移和复核"),
            ("复现包", "模块：复现包列表", "读取 exports/reproducibility_package_*.zip 并展示已有 package", "只列出本地包"),
            ("所有页面", "开发者诊断", "展开 artifact、manifest、debug 路径", "只读显示"),
        ]


    def _write_literature_acquisition_manifest(project_dir: Path) -> Path:
        protocol_dir = project_dir / "protocol" / "pubmed_candidates"
        literature_dir = project_dir / "literature"
        dedup_dir = project_dir / "deduplication"
        screening_dir = project_dir / "screening"
        fulltext_dir = project_dir / "fulltext"
        preview_paths = tuple(sorted(protocol_dir.glob("*_candidates_preview.json"))) if protocol_dir.exists() else ()
        selection_paths = tuple(sorted(protocol_dir.glob("*_candidate_selection.json"))) if protocol_dir.exists() else ()
        records_payload = _load_json_object(literature_dir / "literature_records.json")
        batches_payload = _load_json_object(literature_dir / "import_batches.json")
        manifest_payload = _load_json_object(literature_dir / "library_manifest.json")
        dedup_payload = _load_json_object(dedup_dir / "deduplicated_literature_v2.json")
        duplicate_groups_payload = _load_json_object(dedup_dir / "duplicate_groups_v2.json")
        screening_queue_payload = _load_json_object(screening_dir / "title_abstract_queue_v2.json")
        screening_decisions_payload = _load_json_object(screening_dir / "title_abstract_decisions_v2.json")
        fulltext_registry_payload = _load_json_object(fulltext_dir / "fulltext_management_registry_v1.json")
        rows = _items_from_payload(records_payload, "records", "literature_records")
        batches = _items_from_payload(batches_payload, "batches", "import_batches")
        duplicate_groups = _items_from_payload(duplicate_groups_payload, "duplicate_groups", "groups")
        screening_queue = _items_from_payload(screening_queue_payload, "records", "screening_records")
        screening_decisions = _items_from_payload(screening_decisions_payload, "decisions", "screening_records")
        fulltext_records = _items_from_payload(fulltext_registry_payload, "records")
        output_path = literature_dir / "literature_acquisition_organization_manifest.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "meta_literature_acquisition_organization_manifest.v1",
            "project_dir": str(project_dir),
            "purpose": "Track literature acquisition, import, normalization, deduplication, screening preparation, and full-text organization artifacts for the preview Meta workflow.",
            "online_retrieval": {
                "pubmed_candidate_preview_count": len(preview_paths),
                "pubmed_selection_artifact_count": len(selection_paths),
                "pubmed_candidate_preview_paths": [str(path.relative_to(project_dir)) for path in preview_paths],
                "pubmed_selection_paths": [str(path.relative_to(project_dir)) for path in selection_paths],
                "non_pubmed_online_clients": "not_connected_in_preview; search strategy export only",
            },
            "local_import": {
                "import_batch_count": len(batches),
                "source_counts": manifest_payload.get("source_counts", {}),
                "library_manifest_path": "literature/library_manifest.json" if (literature_dir / "library_manifest.json").exists() else "",
                "import_batches_path": "literature/import_batches.json" if (literature_dir / "import_batches.json").exists() else "",
            },
            "library": {
                "record_count": len(rows),
                "records_path": "literature/literature_records.json" if (literature_dir / "literature_records.json").exists() else "",
                "missing_doi_count": len([row for row in rows if not str(row.get("doi", "")).strip()]),
                "missing_pmid_count": len([row for row in rows if not str(row.get("pmid", "")).strip()]),
                "missing_abstract_count": len([row for row in rows if not str(row.get("abstract", "")).strip()]),
                "pubmed_link_count": len([row for row in rows if str(row.get("pmid", "")).strip()]),
                "doi_link_count": len([row for row in rows if str(row.get("doi", "")).strip()]),
            },
            "organization": {
                "duplicate_group_count": len(duplicate_groups),
                "deduplicated_literature_exists": bool(dedup_payload),
                "screening_queue_count": len(screening_queue),
                "screening_decision_count": len(screening_decisions),
                "fulltext_record_count": len(fulltext_records),
            },
            "boundaries": [
                "PubMed retrieval requires reviewer-confirmed search strategy and reviewer-selected candidate handoff.",
                "WOS, Embase, Cochrane, CNKI, WanFang, and VIP remain search-strategy/export or local-file import paths in this preview.",
                "This manifest does not mark screening, PRISMA, extraction, analysis, or reporting as complete.",
            ],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path


    def _copy_text_to_clipboard(text: str) -> None:
        clipboard = QApplication.clipboard() if QApplication is not None else None
        if clipboard is not None:
            clipboard.setText(text)


    def _literature_citation_text(record: dict[str, object]) -> str:
        authors = record.get("authors", "")
        if isinstance(authors, list):
            author_text = "; ".join(str(author) for author in authors if str(author).strip())
        else:
            author_text = str(authors or record.get("first_author", "") or "").strip()
        rows = [
            f"Title: {record.get('title', '')}",
            f"Authors: {author_text}",
            f"Year: {record.get('year', '')}",
            f"Journal: {record.get('journal') or record.get('publication_title') or ''}",
            f"DOI: {record.get('doi', '')}",
            f"PMID: {record.get('pmid', '')}",
            f"Source: {record.get('source_type') or record.get('source') or ''}",
        ]
        return "\n".join(row for row in rows if row.split(": ", 1)[-1].strip())


    def _write_literature_citation_manifest(project_dir: Path) -> Path:
        library = LiteratureLibraryService()
        records = library.list_records(project_dir)
        rows: list[dict[str, object]] = []
        for record in records:
            doi = str(record.get("doi", "")).strip()
            pmid = str(record.get("pmid", "")).strip()
            rows.append(
                {
                    "record_id": str(record.get("record_id", "")),
                    "citation_text": _literature_citation_text(record),
                    "title": str(record.get("title", "")),
                    "authors": record.get("authors", record.get("first_author", "")),
                    "year": str(record.get("year", "")),
                    "journal": str(record.get("journal") or record.get("publication_title") or ""),
                    "doi": doi,
                    "pmid": pmid,
                    "source": str(record.get("source_type") or record.get("source") or ""),
                    "doi_url": f"https://doi.org/{doi}" if doi else "",
                    "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                    "missing_fields": [
                        field
                        for field, value in (
                            ("title", record.get("title", "")),
                            ("year", record.get("year", "")),
                            ("journal", record.get("journal") or record.get("publication_title") or ""),
                            ("doi", doi),
                            ("pmid", pmid),
                        )
                        if not str(value).strip()
                    ],
                }
            )
        output_path = project_dir / "literature" / "literature_citation_manifest.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "meta_literature_citation_manifest.v1",
            "project_dir": str(project_dir),
            "record_count": len(rows),
            "with_doi_count": len([row for row in rows if row["doi"]]),
            "with_pmid_count": len([row for row in rows if row["pmid"]]),
            "complete_core_citation_count": len([row for row in rows if not row["missing_fields"]]),
            "boundaries": [
                "This manifest organizes citation metadata from the normalized literature library.",
                "It does not contact Crossref, PubMed, Zotero, EndNote, or any external citation service.",
                "Reviewer should verify citation style and metadata before publication use.",
            ],
            "records": rows,
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path


    def _write_literature_ris_export(project_dir: Path) -> Path:
        library = LiteratureLibraryService()
        records = library.list_records(project_dir)
        lines: list[str] = []
        for record in records:
            lines.append("TY  - JOUR")
            title = str(record.get("title", "")).strip()
            if title:
                lines.append(f"TI  - {title}")
            authors = record.get("authors", "")
            if isinstance(authors, list):
                for author in authors:
                    text = str(author).strip()
                    if text:
                        lines.append(f"AU  - {text}")
            else:
                author_text = str(authors or record.get("first_author", "") or "").strip()
                if author_text:
                    lines.append(f"AU  - {author_text}")
            year = str(record.get("year", "")).strip()
            if year:
                lines.append(f"PY  - {year}")
            journal = str(record.get("journal") or record.get("publication_title") or "").strip()
            if journal:
                lines.append(f"JO  - {journal}")
            doi = str(record.get("doi", "")).strip()
            if doi:
                lines.append(f"DO  - {doi}")
            pmid = str(record.get("pmid", "")).strip()
            if pmid:
                lines.append(f"AN  - {pmid}")
                lines.append(f"UR  - https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
            abstract = str(record.get("abstract", "")).strip()
            if abstract:
                lines.append(f"AB  - {abstract}")
            source = str(record.get("source_type") or record.get("source") or "").strip()
            if source:
                lines.append(f"N1  - Source: {source}")
            lines.append("ER  -")
            lines.append("")
        output_path = project_dir / "literature" / "literature_library_export.ris"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path


    def _write_literature_bibtex_export(project_dir: Path) -> Path:
        library = LiteratureLibraryService()
        records = library.list_records(project_dir)
        entries: list[str] = []
        used_keys: set[str] = set()
        for index, record in enumerate(records, start=1):
            first_author = str(record.get("first_author", "") or "").strip()
            if not first_author:
                authors = record.get("authors", "")
                if isinstance(authors, list) and authors:
                    first_author = str(authors[0])
                else:
                    first_author = str(authors or "record")
            year = str(record.get("year", "") or "unknown").strip()
            key_base = "".join(char for char in f"{first_author}{year}" if char.isalnum()) or f"record{index}"
            key = key_base
            suffix = 2
            while key in used_keys:
                key = f"{key_base}{suffix}"
                suffix += 1
            used_keys.add(key)
            fields: list[tuple[str, str]] = []
            title = str(record.get("title", "") or "").strip()
            if title:
                fields.append(("title", title))
            authors = record.get("authors", "")
            if isinstance(authors, list):
                author_text = " and ".join(str(author) for author in authors if str(author).strip())
            else:
                author_text = str(authors or first_author).strip()
            if author_text:
                fields.append(("author", author_text))
            if year and year != "unknown":
                fields.append(("year", year))
            journal = str(record.get("journal") or record.get("publication_title") or "").strip()
            if journal:
                fields.append(("journal", journal))
            doi = str(record.get("doi", "") or "").strip()
            if doi:
                fields.append(("doi", doi))
            pmid = str(record.get("pmid", "") or "").strip()
            if pmid:
                fields.append(("pmid", pmid))
                fields.append(("url", f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"))
            abstract = str(record.get("abstract", "") or "").strip()
            if abstract:
                fields.append(("abstract", abstract))
            source = str(record.get("source_type") or record.get("source") or "").strip()
            if source:
                fields.append(("note", f"Source: {source}"))
            entry_lines = [f"@article{{{key},"]
            for field_name, value in fields:
                safe_value = value.replace("{", "\\{").replace("}", "\\}")
                entry_lines.append(f"  {field_name} = {{{safe_value}}},")
            if len(entry_lines) > 1:
                entry_lines[-1] = entry_lines[-1].rstrip(",")
            entry_lines.append("}")
            entries.append("\n".join(entry_lines))
        output_path = project_dir / "literature" / "literature_library_export.bib"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n\n".join(entries), encoding="utf-8")
        return output_path


    def _write_literature_csl_json_export(project_dir: Path) -> Path:
        library = LiteratureLibraryService()
        records = library.list_records(project_dir)
        items: list[dict[str, object]] = []
        for index, record in enumerate(records, start=1):
            authors = record.get("authors", "")
            if isinstance(authors, list):
                author_items = [_csl_author_item(str(author)) for author in authors if str(author).strip()]
            else:
                author_text = str(authors or record.get("first_author", "") or "").strip()
                author_items = [_csl_author_item(author_text)] if author_text else []
            year = str(record.get("year", "") or "").strip()
            item: dict[str, object] = {
                "id": str(record.get("record_id") or f"record-{index}"),
                "type": "article-journal",
                "title": str(record.get("title", "") or ""),
            }
            if author_items:
                item["author"] = author_items
            if year:
                item["issued"] = {"date-parts": [[int(year)]]} if year.isdigit() else {"literal": year}
            journal = str(record.get("journal") or record.get("publication_title") or "").strip()
            if journal:
                item["container-title"] = journal
            doi = str(record.get("doi", "") or "").strip()
            if doi:
                item["DOI"] = doi
                item["URL"] = f"https://doi.org/{doi}"
            pmid = str(record.get("pmid", "") or "").strip()
            if pmid:
                item["PMID"] = pmid
                item.setdefault("URL", f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
            abstract = str(record.get("abstract", "") or "").strip()
            if abstract:
                item["abstract"] = abstract
            source = str(record.get("source_type") or record.get("source") or "").strip()
            if source:
                item["note"] = f"Source: {source}"
            items.append(item)
        output_path = project_dir / "literature" / "literature_library_export.csl.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path


    def _write_literature_register_csv(project_dir: Path) -> Path:
        import csv

        library = LiteratureLibraryService()
        records = library.list_records(project_dir)
        output_path = project_dir / "literature" / "literature_register.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "record_id",
            "title",
            "first_author",
            "year",
            "journal",
            "doi",
            "pmid",
            "source",
            "doi_url",
            "pubmed_url",
            "has_abstract",
            "screening_status",
            "dedup_status",
        ]
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for record in records:
                doi = str(record.get("doi", "") or "").strip()
                pmid = str(record.get("pmid", "") or "").strip()
                writer.writerow(
                    {
                        "record_id": str(record.get("record_id", "")),
                        "title": str(record.get("title", "")),
                        "first_author": str(record.get("first_author", "")),
                        "year": str(record.get("year", "")),
                        "journal": str(record.get("journal") or record.get("publication_title") or ""),
                        "doi": doi,
                        "pmid": pmid,
                        "source": str(record.get("source_type") or record.get("source") or ""),
                        "doi_url": f"https://doi.org/{doi}" if doi else "",
                        "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                        "has_abstract": bool(str(record.get("abstract", "")).strip()),
                        "screening_status": str(record.get("screening_status", "")),
                        "dedup_status": str(record.get("dedup_status", "")),
                    }
                )
        return output_path


    def _write_literature_organization_package(project_dir: Path) -> Path:
        import zipfile

        generated_paths = [
            _write_literature_citation_manifest(project_dir),
            _write_literature_ris_export(project_dir),
            _write_literature_bibtex_export(project_dir),
            _write_literature_csl_json_export(project_dir),
            _write_literature_register_csv(project_dir),
            _write_literature_acquisition_manifest(project_dir),
        ]
        candidate_paths = [
            project_dir / "literature" / "literature_records.json",
            project_dir / "literature" / "import_batches.json",
            project_dir / "literature" / "library_manifest.json",
            project_dir / "protocol" / "search_strategy_v2" / "search_execution_manifest.json",
            project_dir / "screening" / "screening_organization_manifest.json",
            project_dir / "screening" / "title_abstract_screening_decisions.csv",
            project_dir / "fulltext" / "fulltext_retrieval_manifest.json",
            project_dir / "fulltext" / "fulltext_retrieval_register.csv",
            project_dir / "exports" / "fulltext_retrieval_package.zip",
            *generated_paths,
        ]
        output_dir = project_dir / "exports"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "literature_organization_package.zip"
        included: list[str] = []
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as package:
            for path in candidate_paths:
                if not path.exists() or not path.is_file():
                    continue
                archive_name = str(path.relative_to(project_dir))
                if archive_name in included:
                    continue
                package.write(path, archive_name)
                included.append(archive_name)
            package.writestr(
                "literature_organization_package_manifest.json",
                json.dumps(
                    {
                        "schema_version": "meta_literature_organization_package.v1",
                        "project_dir": str(project_dir),
                        "included_count": len(included),
                        "included_paths": included,
                        "boundaries": [
                            "This package contains local literature organization artifacts only.",
                            "It does not include downloaded full-text PDFs unless they are already represented by project manifests.",
                            "It does not prove external database access, final screening completion, or publication-ready citation formatting.",
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
        return output_path


    def _write_literature_capability_artifact_index(project_dir: Path) -> Path:
        requested = [
            _write_search_execution_manifest,
            _write_literature_acquisition_manifest,
            _write_literature_citation_manifest,
            _write_literature_ris_export,
            _write_literature_bibtex_export,
            _write_literature_csl_json_export,
            _write_literature_register_csv,
            _write_screening_organization_manifest,
            _write_title_abstract_screening_decisions_csv,
            _write_fulltext_retrieval_manifest,
            _write_fulltext_retrieval_csv,
            _write_fulltext_retrieval_package,
            _write_literature_organization_package,
        ]
        generated: list[dict[str, object]] = []
        for writer in requested:
            try:
                path = writer(project_dir)
                generated.append(
                    {
                        "artifact": str(path.relative_to(project_dir)),
                        "exists": path.exists(),
                        "writer": writer.__name__,
                    }
                )
            except Exception as exc:
                generated.append(
                    {
                        "artifact": "",
                        "exists": False,
                        "writer": writer.__name__,
                        "error": str(exc),
                    }
                )
        output_path = project_dir / "literature" / "literature_capability_artifact_index.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "meta_literature_capability_artifact_index.v1",
            "project_dir": str(project_dir),
            "generated_count": len([item for item in generated if item.get("exists")]),
            "requested_count": len(generated),
            "artifacts": generated,
            "boundaries": [
                "This action generates local literature organization artifacts only.",
                "It does not execute database retrieval, import new records, make screening decisions, download full text, run OCR, or perform statistics.",
                "Errors are recorded per artifact so reviewers can rerun or inspect missing prerequisites.",
            ],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path


    def _csl_author_item(author: str) -> dict[str, str]:
        parts = [part.strip() for part in author.replace(",", " ").split() if part.strip()]
        if len(parts) >= 2:
            return {"family": parts[-1], "given": " ".join(parts[:-1])}
        return {"literal": author}


    def _fulltext_retrieval_links_text(record, *, candidate=None) -> str:
        doi = str(getattr(record, "doi", "") or getattr(candidate, "doi", "") or "").strip()
        pmid = str(getattr(record, "pmid", "") or getattr(candidate, "pmid", "") or "").strip()
        pmcid = str(getattr(record, "pmcid", "") or getattr(candidate, "pmcid", "") or "").strip()
        lines = []
        if doi:
            lines.append(f"DOI: https://doi.org/{doi}")
        if pmid:
            lines.append(f"PubMed: https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
        if pmcid:
            lines.append(f"PMC: https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/")
        return "\n".join(lines)


    def _write_fulltext_retrieval_manifest(project_dir: Path) -> Path:
        management = FullTextManagementService()
        eligibility = FullTextEligibilityService()
        records = list(management.list_records(project_dir))
        candidates = list(eligibility.build_candidates_from_screening(project_dir))
        candidates_by_id = {str(getattr(candidate, "record_id", "")): candidate for candidate in candidates}
        source_records = records or candidates
        rows: list[dict[str, object]] = []
        for item in source_records:
            record_id = str(getattr(item, "record_id", ""))
            candidate = candidates_by_id.get(record_id)
            doi = str(getattr(item, "doi", "") or getattr(candidate, "doi", "") or "").strip()
            pmid = str(getattr(item, "pmid", "") or getattr(candidate, "pmid", "") or "").strip()
            pmcid = str(getattr(item, "pmcid", "") or getattr(candidate, "pmcid", "") or "").strip()
            pdf_path = str(getattr(item, "pdf_path", "") or "")
            rows.append(
                {
                    "record_id": record_id,
                    "title": str(getattr(item, "title", "") or getattr(candidate, "title", "") or ""),
                    "first_author": str(getattr(item, "first_author", "") or getattr(candidate, "first_author", "") or ""),
                    "year": str(getattr(item, "year", "") or getattr(candidate, "year", "") or ""),
                    "journal": str(getattr(item, "journal", "") or getattr(candidate, "journal", "") or ""),
                    "doi": doi,
                    "pmid": pmid,
                    "pmcid": pmcid,
                    "doi_url": f"https://doi.org/{doi}" if doi else "",
                    "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                    "pmc_url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/" if pmcid else "",
                    "pdf_path": pdf_path,
                    "fulltext_status": str(getattr(item, "fulltext_status", getattr(item, "eligibility_status", "")) or ""),
                    "source_screening_decision": str(getattr(item, "source_screening_decision", getattr(candidate, "screening_decision", "")) or ""),
                    "needs_manual_retrieval": not bool(pdf_path),
                }
            )
        output_path = project_dir / "fulltext" / "fulltext_retrieval_manifest.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "meta_fulltext_retrieval_manifest.v1",
            "project_dir": str(project_dir),
            "record_count": len(rows),
            "with_doi_count": len([row for row in rows if row["doi"]]),
            "with_pmid_count": len([row for row in rows if row["pmid"]]),
            "with_pmcid_count": len([row for row in rows if row["pmcid"]]),
            "with_local_pdf_count": len([row for row in rows if row["pdf_path"]]),
            "manual_retrieval_needed_count": len([row for row in rows if row["needs_manual_retrieval"]]),
            "boundaries": [
                "This manifest prepares manual full-text retrieval links only.",
                "The preview build does not download PDFs automatically, bypass paywalls, or use institutional login.",
                "PDF/OCR parsing artifacts remain auxiliary and do not write final extraction values.",
            ],
            "records": rows,
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path


    def _write_fulltext_retrieval_csv(project_dir: Path) -> Path:
        import csv

        management = FullTextManagementService()
        eligibility = FullTextEligibilityService()
        records = list(management.list_records(project_dir))
        candidates = list(eligibility.build_candidates_from_screening(project_dir))
        candidates_by_id = {str(getattr(candidate, "record_id", "")): candidate for candidate in candidates}
        source_records = records or candidates
        output_path = project_dir / "fulltext" / "fulltext_retrieval_register.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "record_id",
            "title",
            "first_author",
            "year",
            "journal",
            "doi",
            "pmid",
            "pmcid",
            "doi_url",
            "pubmed_url",
            "pmc_url",
            "pdf_path",
            "fulltext_status",
            "source_screening_decision",
            "needs_manual_retrieval",
        ]
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for item in source_records:
                record_id = str(getattr(item, "record_id", ""))
                candidate = candidates_by_id.get(record_id)
                doi = str(getattr(item, "doi", "") or getattr(candidate, "doi", "") or "").strip()
                pmid = str(getattr(item, "pmid", "") or getattr(candidate, "pmid", "") or "").strip()
                pmcid = str(getattr(item, "pmcid", "") or getattr(candidate, "pmcid", "") or "").strip()
                pdf_path = str(getattr(item, "pdf_path", "") or "")
                writer.writerow(
                    {
                        "record_id": record_id,
                        "title": str(getattr(item, "title", "") or getattr(candidate, "title", "") or ""),
                        "first_author": str(getattr(item, "first_author", "") or getattr(candidate, "first_author", "") or ""),
                        "year": str(getattr(item, "year", "") or getattr(candidate, "year", "") or ""),
                        "journal": str(getattr(item, "journal", "") or getattr(candidate, "journal", "") or ""),
                        "doi": doi,
                        "pmid": pmid,
                        "pmcid": pmcid,
                        "doi_url": f"https://doi.org/{doi}" if doi else "",
                        "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                        "pmc_url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/" if pmcid else "",
                        "pdf_path": pdf_path,
                        "fulltext_status": str(getattr(item, "fulltext_status", getattr(item, "eligibility_status", "")) or ""),
                        "source_screening_decision": str(getattr(item, "source_screening_decision", getattr(candidate, "screening_decision", "")) or ""),
                        "needs_manual_retrieval": not bool(pdf_path),
                    }
                )
        return output_path


    def _write_fulltext_retrieval_package(project_dir: Path) -> Path:
        import zipfile

        manifest = _write_fulltext_retrieval_manifest(project_dir)
        register = _write_fulltext_retrieval_csv(project_dir)
        candidate_paths = [
            manifest,
            register,
            project_dir / "fulltext" / "fulltext_management_registry_v1.json",
            project_dir / "fulltext" / "fulltext_parse_manifest_v1.json",
            project_dir / "fulltext" / "fulltext_registry.json",
            project_dir / "reports" / "missing_fulltext_report.csv",
        ]
        output_dir = project_dir / "exports"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "fulltext_retrieval_package.zip"
        included: list[str] = []
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as package:
            for path in candidate_paths:
                if not path.exists() or not path.is_file():
                    continue
                archive_name = str(path.relative_to(project_dir))
                if archive_name in included:
                    continue
                package.write(path, archive_name)
                included.append(archive_name)
            package.writestr(
                "fulltext_retrieval_package_manifest.json",
                json.dumps(
                    {
                        "schema_version": "meta_fulltext_retrieval_package.v1",
                        "project_dir": str(project_dir),
                        "included_count": len(included),
                        "included_paths": included,
                        "boundaries": [
                            "This package contains local full-text retrieval manifests and registers only.",
                            "It does not download PDFs, bypass access controls, or run OCR/full-text parsing.",
                            "Local PDF files are referenced by manifest paths but not copied into this package.",
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
        return output_path


    def _write_extraction_organization_manifest(project_dir: Path) -> Path:
        service = ManualExtractionEffectRowService()
        study_units = service.load_study_units(project_dir)
        effect_rows = service.load_effect_rows(project_dir)
        structured_rows = service.load_structured_extraction_table(project_dir)
        validation = _load_json_object(service.validation_report_path(project_dir))
        ai_queue = _load_json_object(project_dir / "extraction" / "extraction_ai_suggestion_queue.json")
        ai_applications = _load_json_object(project_dir / "extraction" / "extraction_ai_suggestion_applications.json")
        output_path = project_dir / "extraction" / "extraction_organization_manifest.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "meta_extraction_organization_manifest.v1",
            "project_dir": str(project_dir),
            "study_unit_count": len(study_units),
            "effect_row_count": len(effect_rows),
            "structured_row_count": len(structured_rows),
            "missing_required_fields_count": int(validation.get("missing_required_fields_count", 0) or 0),
            "ai_suggestion_count": len(ai_queue.get("suggestions", [])) if isinstance(ai_queue.get("suggestions", []), list) else 0,
            "ai_application_count": len(ai_applications.get("applications", [])) if isinstance(ai_applications.get("applications", []), list) else 0,
            "artifacts": [
                {"path": "extraction/extraction_manifest.json", "exists": (project_dir / "extraction" / "extraction_manifest.json").exists()},
                {"path": "extraction/extraction_study_units.json", "exists": service.study_units_path(project_dir).exists()},
                {"path": "extraction/extraction_effect_rows.json", "exists": service.effect_rows_path(project_dir).exists()},
                {"path": "extraction/manual_extraction_template.csv", "exists": (project_dir / "extraction" / "manual_extraction_template.csv").exists()},
                {"path": "extraction/manual_extraction_current.csv", "exists": (project_dir / "extraction" / "manual_extraction_current.csv").exists()},
                {"path": "extraction/extraction_validation_report.json", "exists": service.validation_report_path(project_dir).exists()},
                {"path": "extraction/extraction_ai_suggestion_queue.json", "exists": (project_dir / "extraction" / "extraction_ai_suggestion_queue.json").exists()},
                {"path": "extraction/extraction_ai_suggestion_applications.json", "exists": (project_dir / "extraction" / "extraction_ai_suggestion_applications.json").exists()},
            ],
            "boundaries": [
                "This manifest summarizes local manual extraction and AI suggestion artifacts only.",
                "It does not create an analysis-ready dataset, run meta-analysis, or infer missing data.",
                "AI suggestions remain draft inputs until explicitly reviewed by a human.",
            ],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path


    def _write_extraction_organization_package(project_dir: Path) -> Path:
        import zipfile

        service = ManualExtractionEffectRowService()
        template_result = service.export_empty_template_csv(project_dir, actor="reviewer")
        current_result = service.export_current_csv(project_dir, actor="reviewer")
        generated_paths = [
            _write_extraction_organization_manifest(project_dir),
            Path(template_result.output_path),
            Path(current_result.output_path),
        ]
        candidate_paths = [
            project_dir / "extraction" / "extraction_manifest.json",
            service.study_units_path(project_dir),
            service.effect_rows_path(project_dir),
            service.evidence_refs_path(project_dir),
            service.validation_report_path(project_dir),
            service.extraction_audit_path(project_dir),
            project_dir / "extraction" / "extraction_ai_suggestion_queue.json",
            project_dir / "extraction" / "extraction_ai_suggestion_applications.json",
            *generated_paths,
        ]
        output_dir = project_dir / "exports"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "extraction_organization_package.zip"
        included: list[str] = []
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as package:
            for path in candidate_paths:
                if not path.exists() or not path.is_file():
                    continue
                archive_name = str(path.relative_to(project_dir))
                if archive_name in included:
                    continue
                package.write(path, archive_name)
                included.append(archive_name)
            package.writestr(
                "extraction_organization_package_manifest.json",
                json.dumps(
                    {
                        "schema_version": "meta_extraction_organization_package.v1",
                        "project_dir": str(project_dir),
                        "included_count": len(included),
                        "included_paths": included,
                        "boundaries": [
                            "This package contains local extraction artifacts only.",
                            "It does not run statistics, impute missing values, or mark extraction complete.",
                            "Imported CSV rows remain draft data unless separately confirmed by a reviewer.",
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
        return output_path


    def _write_quality_organization_manifest(project_dir: Path) -> Path:
        service = QualityAssessmentService()
        records_v1 = service.load_quality_assessment_records_v1(project_dir)
        legacy_records = service.load_quality_assessments(project_dir)
        summary = _load_json_object(project_dir / "quality" / "quality_assessment_summary_v1.json")
        output_path = project_dir / "quality" / "quality_organization_manifest.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        completed = len([record for record in records_v1 if str(record.get("status", "")) == "completed_by_user"])
        payload = {
            "schema_version": "meta_quality_organization_manifest.v1",
            "project_dir": str(project_dir),
            "quality_record_v1_count": len(records_v1),
            "legacy_quality_record_count": len(legacy_records),
            "completed_by_user_count": completed,
            "summary": summary,
            "artifacts": [
                {"path": "quality/quality_assessment_records_v1.json", "exists": (project_dir / "quality" / "quality_assessment_records_v1.json").exists()},
                {"path": "quality/quality_assessment_summary_v1.json", "exists": (project_dir / "quality" / "quality_assessment_summary_v1.json").exists()},
                {"path": "quality/quality_assessment_v1_export.json", "exists": (project_dir / "quality" / "quality_assessment_v1_export.json").exists()},
                {"path": "exports/quality_assessment_v1.csv", "exists": (project_dir / "exports" / "quality_assessment_v1.csv").exists()},
                {"path": "quality/quality_table.csv", "exists": (project_dir / "quality" / "quality_table.csv").exists()},
                {"path": "exports/quality_assessment_table.csv", "exists": (project_dir / "exports" / "quality_assessment_table.csv").exists()},
            ],
            "boundaries": [
                "This manifest summarizes local quality assessment artifacts only.",
                "It does not change ratings, complete records, or override reviewer confirmation.",
                "Quality outputs remain dependent on human-reviewed study-level assessment records.",
            ],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path


    def _write_quality_assessment_package(project_dir: Path) -> Path:
        import zipfile

        service = QualityAssessmentService()
        beta_outputs = service.export_quality_beta_outputs(project_dir)
        generated_paths = [
            service.export_quality_assessments_v1_json(project_dir),
            service.export_quality_assessments_v1_csv(project_dir),
            _write_quality_organization_manifest(project_dir),
            *[Path(value) for value in beta_outputs.values()],
        ]
        candidate_paths = [
            project_dir / "quality" / "quality_assessment_records_v1.json",
            project_dir / "quality" / "quality_assessment_summary_v1.json",
            project_dir / "quality" / "quality_assessments.json",
            project_dir / "quality" / "quality_assessment.json",
            project_dir / "quality" / "quality_table.csv",
            project_dir / "exports" / "quality_assessment_table.csv",
            *generated_paths,
        ]
        output_dir = project_dir / "exports"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "quality_assessment_package.zip"
        included: list[str] = []
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as package:
            for path in candidate_paths:
                if not path.exists() or not path.is_file():
                    continue
                archive_name = str(path.relative_to(project_dir))
                if archive_name in included:
                    continue
                package.write(path, archive_name)
                included.append(archive_name)
            package.writestr(
                "quality_assessment_package_manifest.json",
                json.dumps(
                    {
                        "schema_version": "meta_quality_assessment_package.v1",
                        "project_dir": str(project_dir),
                        "included_count": len(included),
                        "included_paths": included,
                        "boundaries": [
                            "This package contains local quality assessment artifacts only.",
                            "It does not alter quality ratings or mark unconfirmed records complete.",
                            "Analysis readiness still depends on confirmed extraction and analysis plan artifacts.",
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
        return output_path


    def _write_statistics_results_manifest(project_dir: Path) -> Path:
        stats = MetaStatisticsEngineService(analysis_plan_service=AnalysisPlanService())
        manifest_path = stats.manifest_path(project_dir)
        results_dir = stats.results_dir(project_dir)
        runs_dir = stats.runs_dir(project_dir)
        result_files = tuple(sorted(results_dir.glob("*_result.json"))) if results_dir.exists() else ()
        run_files = tuple(sorted(runs_dir.glob("*.json"))) if runs_dir.exists() else ()
        output_path = project_dir / "analysis" / "statistics_results_manifest.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "meta_statistics_results_manifest.v1",
            "project_dir": str(project_dir),
            "confirmed_analysis_plan_exists": (project_dir / "analysis" / "analysis_plan_confirmed_v1.json").exists(),
            "analysis_manifest_exists": manifest_path.exists(),
            "result_count": len(result_files),
            "run_count": len(run_files),
            "result_paths": [str(path.relative_to(project_dir)) for path in result_files],
            "run_paths": [str(path.relative_to(project_dir)) for path in run_files],
            "latest_result_path": str(result_files[-1].relative_to(project_dir)) if result_files else "",
            "boundaries": [
                "This manifest summarizes local statistics artifacts only.",
                "It does not run statistics, approve results, generate clinical conclusions, or advance PRISMA.",
                "All statistics outputs remain testing-level until separately reviewed.",
            ],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path


    def _write_statistics_results_package(project_dir: Path) -> Path:
        import zipfile

        stats = MetaStatisticsEngineService(analysis_plan_service=AnalysisPlanService())
        manifest = _write_statistics_results_manifest(project_dir)
        result_paths = tuple(sorted(stats.results_dir(project_dir).glob("*_result.json"))) if stats.results_dir(project_dir).exists() else ()
        run_paths = tuple(sorted(stats.runs_dir(project_dir).glob("*.json"))) if stats.runs_dir(project_dir).exists() else ()
        candidate_paths = [
            manifest,
            stats.manifest_path(project_dir),
            project_dir / "analysis" / "analysis_plan_draft_v1.json",
            project_dir / "analysis" / "analysis_plan_confirmed_v1.json",
            project_dir / "analysis" / "analysis_plan_manifest_v1.json",
            project_dir / "analysis" / "pairwise_executor" / "latest_pairwise_meta_result_review.json",
            *result_paths,
            *run_paths,
        ]
        output_dir = project_dir / "exports"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "statistics_results_package.zip"
        included: list[str] = []
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as package:
            for path in candidate_paths:
                if not path.exists() or not path.is_file():
                    continue
                archive_name = str(path.relative_to(project_dir))
                if archive_name in included:
                    continue
                package.write(path, archive_name)
                included.append(archive_name)
            package.writestr(
                "statistics_results_package_manifest.json",
                json.dumps(
                    {
                        "schema_version": "meta_statistics_results_package.v1",
                        "project_dir": str(project_dir),
                        "included_count": len(included),
                        "included_paths": included,
                        "boundaries": [
                            "This package contains existing local statistics artifacts only.",
                            "It does not execute statistics or certify report readiness.",
                            "Human statistical result review remains required.",
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
        return output_path


    def _write_figure_results_manifest(project_dir: Path) -> Path:
        service = FigureResultService()
        artifacts = service.list_figure_artifacts(project_dir)
        results_dir = project_dir / "analysis" / "results"
        result_files = tuple(sorted(results_dir.glob("*_result.json"))) if results_dir.exists() else ()
        output_path = project_dir / "figures" / "figure_results_manifest.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "meta_figure_results_manifest.v1",
            "project_dir": str(project_dir),
            "figure_artifact_count": len(artifacts),
            "statistics_result_count": len(result_files),
            "figure_artifacts": [
                {
                    "figure_id": artifact.figure_id,
                    "analysis_result_id": artifact.analysis_result_id,
                    "figure_type": artifact.figure_type,
                    "format": artifact.format,
                    "path": artifact.file_path,
                }
                for artifact in artifacts
            ],
            "statistics_result_paths": [str(path.relative_to(project_dir)) for path in result_files],
            "boundaries": [
                "This manifest summarizes existing figure and result artifacts only.",
                "It does not generate figures, rerun statistics, or create medical conclusions.",
                "Figure artifacts remain tied to testing-level statistical results unless separately reviewed.",
            ],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path


    def _write_figure_results_package(project_dir: Path) -> Path:
        import zipfile

        manifest = _write_figure_results_manifest(project_dir)
        figure_dir = project_dir / "figures"
        results_dir = project_dir / "analysis" / "results"
        figure_paths = tuple(sorted(figure_dir.glob("*"))) if figure_dir.exists() else ()
        result_paths = tuple(sorted(results_dir.glob("*_result.json"))) if results_dir.exists() else ()
        candidate_paths = [
            manifest,
            figure_dir / "figure_artifacts.json",
            *figure_paths,
            *result_paths,
        ]
        output_dir = project_dir / "exports"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "figure_results_package.zip"
        included: list[str] = []
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as package:
            for path in candidate_paths:
                if not path.exists() or not path.is_file():
                    continue
                archive_name = str(path.relative_to(project_dir))
                if archive_name in included:
                    continue
                package.write(path, archive_name)
                included.append(archive_name)
            package.writestr(
                "figure_results_package_manifest.json",
                json.dumps(
                    {
                        "schema_version": "meta_figure_results_package.v1",
                        "project_dir": str(project_dir),
                        "included_count": len(included),
                        "included_paths": included,
                        "boundaries": [
                            "This package contains existing local figure/result artifacts only.",
                            "It does not generate new figures or rerun statistics.",
                            "Review of testing-level result status remains required before external use.",
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
        return output_path


    def _write_prisma_reporting_manifest(project_dir: Path) -> Path:
        reports_dir = project_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        output_path = reports_dir / "prisma_reporting_manifest.json"
        candidate_paths = [
            reports_dir / "prisma_flow_summary.json",
            reports_dir / "prisma_flow_summary.md",
            reports_dir / "prisma_summary.json",
            reports_dir / "prisma_flow.md",
            reports_dir / "prisma_flow.svg",
        ]
        payload = {
            "schema_version": "meta_prisma_reporting_manifest.v1",
            "project_dir": str(project_dir),
            "artifacts": [
                {
                    "path": str(path.relative_to(project_dir)),
                    "exists": path.exists(),
                    "size_bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
                }
                for path in candidate_paths
            ],
            "boundaries": [
                "PRISMA numbers are derived from local import, deduplication, screening, full-text, extraction, and analysis artifacts.",
                "This manifest does not invent counts or override reviewer decisions.",
                "Full-text PRISMA counts remain constrained by currently available full-text workflow records.",
            ],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path


    def _write_prisma_reporting_package(project_dir: Path) -> Path:
        import zipfile

        service = PRISMAService()
        summary = service.load_prisma_flow_summary(project_dir) or service.collect_prisma_numbers(project_dir)
        summary_json = service.save_prisma_flow_summary(project_dir, summary)
        summary_md = service.export_prisma_flow_markdown(project_dir, summary)
        simplified = service.export_simplified_prisma_flow(project_dir, summary)
        manifest = _write_prisma_reporting_manifest(project_dir)
        candidate_paths = [summary_json, summary_md, manifest, *simplified.values()]
        output_dir = project_dir / "exports"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "prisma_reporting_package.zip"
        included: list[str] = []
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as package:
            for path in candidate_paths:
                if not path.exists() or not path.is_file():
                    continue
                archive_name = str(path.relative_to(project_dir))
                if archive_name in included:
                    continue
                package.write(path, archive_name)
                included.append(archive_name)
            package.writestr(
                "prisma_reporting_package_manifest.json",
                json.dumps(
                    {
                        "schema_version": "meta_prisma_reporting_package.v1",
                        "project_dir": str(project_dir),
                        "included_count": len(included),
                        "included_paths": included,
                        "boundaries": [
                            "This package contains local PRISMA summary and diagram artifacts only.",
                            "It does not alter import, deduplication, screening, full-text, extraction, or analysis records.",
                            "Counts should be reviewed against source artifacts before external use.",
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
        return output_path


    def _write_formal_report_delivery_manifest(project_dir: Path) -> Path:
        reports_dir = project_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        output_path = reports_dir / "formal_report_delivery_manifest.json"
        candidate_paths = [
            reports_dir / "formal_meta_report.md",
            reports_dir / "formal_meta_report.html",
            reports_dir / "formal_meta_report.docx",
            reports_dir / "report_manifest.json",
            reports_dir / "prisma_flow_summary.json",
            reports_dir / "prisma_flow_summary.md",
            reports_dir / "prisma_flow.svg",
        ]
        payload = {
            "schema_version": "meta_formal_report_delivery_manifest.v1",
            "project_dir": str(project_dir),
            "artifacts": [
                {
                    "path": str(path.relative_to(project_dir)),
                    "exists": path.exists(),
                    "size_bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
                }
                for path in candidate_paths
            ],
            "boundaries": [
                "This manifest summarizes local draft/testing report artifacts only.",
                "It does not certify publication readiness or generate clinical conclusions.",
                "Missing content and testing-level caveats remain part of the generated report.",
            ],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path


    def _write_formal_report_package(project_dir: Path) -> Path:
        import zipfile

        report_md = FormalMarkdownReportBuilder().build_draft_markdown_report(project_dir)
        exporter = PublicationExportService()
        html = Path(exporter.export_html_report(project_dir).output_path)
        docx = Path(exporter.export_word_report(project_dir).output_path)
        manifest = _write_formal_report_delivery_manifest(project_dir)
        candidate_paths = [
            report_md,
            html,
            docx,
            manifest,
            project_dir / "reports" / "report_manifest.json",
            project_dir / "reports" / "prisma_flow_summary.json",
            project_dir / "reports" / "prisma_flow_summary.md",
            project_dir / "reports" / "prisma_flow.svg",
        ]
        output_dir = project_dir / "exports"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "formal_report_package.zip"
        included: list[str] = []
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as package:
            for path in candidate_paths:
                if not path.exists() or not path.is_file():
                    continue
                archive_name = str(path.relative_to(project_dir))
                if archive_name in included:
                    continue
                package.write(path, archive_name)
                included.append(archive_name)
            package.writestr(
                "formal_report_package_manifest.json",
                json.dumps(
                    {
                        "schema_version": "meta_formal_report_package.v1",
                        "project_dir": str(project_dir),
                        "included_count": len(included),
                        "included_paths": included,
                        "boundaries": [
                            "This package contains local draft/testing report artifacts only.",
                            "It is not a publication-ready submission package.",
                            "Clinical interpretation and final manuscript review remain manual gates.",
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
        return output_path


    def _write_screening_organization_manifest(project_dir: Path) -> Path:
        dedup_dir = project_dir / "deduplication"
        screening_dir = project_dir / "screening"
        duplicate_groups_payload = _load_json_object(dedup_dir / "duplicate_groups_v2.json")
        decisions_payload = _load_json_object(dedup_dir / "dedup_decisions_v2.json")
        deduplicated_payload = _load_json_object(dedup_dir / "deduplicated_literature_v2.json")
        queue_payload = _load_json_object(screening_dir / "title_abstract_queue_v2.json")
        screening_decisions_payload = _load_json_object(screening_dir / "title_abstract_decisions_v2.json")
        duplicate_groups = _items_from_payload(duplicate_groups_payload, "duplicate_groups", "groups")
        dedup_decisions = _items_from_payload(decisions_payload, "decisions")
        queue_records = _items_from_payload(queue_payload, "queue_records", "records", "screening_records")
        screening_decisions = _items_from_payload(screening_decisions_payload, "screening_records", "decisions")
        decision_counts: dict[str, int] = {}
        for item in screening_decisions:
            decision = str(item.get("decision") or item.get("screening_decision") or DECISION_NOT_SCREENED)
            decision_counts[decision] = decision_counts.get(decision, 0) + 1
        output_path = screening_dir / "screening_organization_manifest.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "meta_screening_organization_manifest.v1",
            "project_dir": str(project_dir),
            "deduplication": {
                "duplicate_group_count": len(duplicate_groups),
                "dedup_decision_count": len(dedup_decisions),
                "deduplicated_literature_exists": bool(deduplicated_payload),
                "active_record_count": deduplicated_payload.get("active_record_count", deduplicated_payload.get("deduplicated_count", 0)) if deduplicated_payload else 0,
                "unresolved_group_count": len(deduplicated_payload.get("unresolved_group_ids", [])) if isinstance(deduplicated_payload.get("unresolved_group_ids"), list) else 0,
            },
            "title_abstract_screening": {
                "queue_record_count": len(queue_records),
                "decision_count": len(screening_decisions),
                "decision_counts": decision_counts,
                "needs_full_text_count": decision_counts.get(DECISION_NEED_FULL_TEXT, 0),
                "included_count": decision_counts.get(DECISION_INCLUDE, 0),
                "excluded_count": decision_counts.get(DECISION_EXCLUDE, 0),
                "uncertain_count": decision_counts.get(DECISION_UNCERTAIN, 0),
            },
            "artifact_paths": {
                "duplicate_groups": "deduplication/duplicate_groups_v2.json" if (dedup_dir / "duplicate_groups_v2.json").exists() else "",
                "dedup_decisions": "deduplication/dedup_decisions_v2.json" if (dedup_dir / "dedup_decisions_v2.json").exists() else "",
                "deduplicated_literature": "deduplication/deduplicated_literature_v2.json" if (dedup_dir / "deduplicated_literature_v2.json").exists() else "",
                "screening_queue": "screening/title_abstract_queue_v2.json" if (screening_dir / "title_abstract_queue_v2.json").exists() else "",
                "screening_decisions": "screening/title_abstract_decisions_v2.json" if (screening_dir / "title_abstract_decisions_v2.json").exists() else "",
            },
            "boundaries": [
                "This manifest summarizes deduplication and title/abstract screening organization only.",
                "It does not automatically create full-text retrieval, PRISMA final counts, extraction rows, or analysis-ready datasets.",
                "Reviewer decisions remain the source of truth for inclusion and exclusion.",
            ],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path


    def _write_title_abstract_screening_decisions_csv(project_dir: Path) -> Path:
        import csv

        service = TitleAbstractScreeningV2Service()
        queue_payload = service.load_queue(project_dir)
        decisions_payload = _load_json_object(service.decisions_path(project_dir))
        queue_records = _items_from_payload(queue_payload, "queue_records", "records", "screening_records")
        decisions = _items_from_payload(decisions_payload, "screening_records", "decisions")
        decisions_by_id = {str(item.get("record_id", "")): item for item in decisions}
        output_path = project_dir / "screening" / "title_abstract_screening_decisions.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fields = ["record_id", "title", "year", "journal", "pmid", "doi", "decision", "exclusion_reason_code", "notes", "has_abstract"]
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for record in queue_records:
                record_id = str(record.get("record_id", ""))
                decision = decisions_by_id.get(record_id, {})
                writer.writerow(
                    {
                        "record_id": record_id,
                        "title": str(record.get("title", "")),
                        "year": str(record.get("year", "")),
                        "journal": str(record.get("journal", "")),
                        "pmid": str(record.get("pmid", "")),
                        "doi": str(record.get("doi", "")),
                        "decision": str(decision.get("decision", record.get("decision", ""))),
                        "exclusion_reason_code": str(decision.get("exclusion_reason_code", "")),
                        "notes": str(decision.get("notes", "")),
                        "has_abstract": bool(str(record.get("abstract", "")).strip()),
                    }
                )
        return output_path


    def _write_search_execution_manifest(project_dir: Path) -> Path:
        service = SearchStrategyBuilderService()
        drafts = list(service.load_drafts(project_dir))
        confirmed = list(service.load_confirmed(project_dir))
        draft_by_database = {str(getattr(item, "database_id", getattr(item, "database", ""))): item for item in drafts}
        confirmed_by_database = {str(getattr(item, "database_id", getattr(item, "database", ""))): item for item in confirmed}
        databases: list[dict[str, object]] = []
        for database in _search_database_order():
            draft = draft_by_database.get(database)
            confirmed_item = confirmed_by_database.get(database)
            draft_query = str(getattr(draft, "query", getattr(draft, "draft_query", "")) or "")
            confirmed_query = str(getattr(confirmed_item, "confirmed_query", getattr(confirmed_item, "query", "")) or "")
            databases.append(
                {
                    "database": database,
                    "label": _database_label(database),
                    "manual_entry_url": _manual_database_entry_url(database),
                    "has_draft": draft is not None,
                    "has_confirmed_query": bool(confirmed_query.strip()),
                    "query": confirmed_query or draft_query,
                    "execution_mode": "testing_pubmed_client" if database == "pubmed" else "manual_external_database_search",
                    "connected_action": "执行 PubMed testing-level 检索" if database == "pubmed" else "复制/导出检索式后到外部数据库人工执行",
                }
            )
        output_dir = project_dir / "protocol" / "search_strategy_v2"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "search_execution_manifest.json"
        payload = {
            "schema_version": "meta_search_execution_manifest.v1",
            "project_dir": str(project_dir),
            "database_count": len(databases),
            "confirmed_database_count": len([item for item in databases if item["has_confirmed_query"]]),
            "pubmed_testing_execution_available": any(item["database"] == "pubmed" and item["has_confirmed_query"] for item in databases),
            "databases": databases,
            "boundaries": [
                "PubMed has a reviewer-confirmed testing-level execution path in this preview.",
                "Web of Science, Embase, Cochrane, CNKI, WanFang, and VIP use query generation/export plus manual external execution.",
                "This manifest does not prove database access, subscription availability, or final search completeness.",
            ],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path


    def _write_search_strategy_package(project_dir: Path) -> Path:
        import zipfile

        execution_manifest = _write_search_execution_manifest(project_dir)
        strategy_dir = project_dir / "protocol" / "search_strategy_v2"
        candidate_paths = [
            strategy_dir / "search_strategy_drafts.json",
            strategy_dir / "search_strategy_confirmed.json",
            strategy_dir / "search_strategy_draft.md",
            strategy_dir / "search_strategy_draft.txt",
            execution_manifest,
            project_dir / "protocol" / "pico_workspace_confirmed.json",
        ]
        output_dir = project_dir / "exports"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "search_strategy_package.zip"
        included: list[str] = []
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as package:
            for path in candidate_paths:
                if not path.exists() or not path.is_file():
                    continue
                archive_name = str(path.relative_to(project_dir))
                if archive_name in included:
                    continue
                package.write(path, archive_name)
                included.append(archive_name)
            package.writestr(
                "search_strategy_package_manifest.json",
                json.dumps(
                    {
                        "schema_version": "meta_search_strategy_package.v1",
                        "project_dir": str(project_dir),
                        "included_count": len(included),
                        "included_paths": included,
                        "boundaries": [
                            "This package contains local search strategy artifacts only.",
                            "It does not execute PubMed or external database searches.",
                            "WOS, Embase, Cochrane, CNKI, WanFang, and VIP remain manual external execution paths in this preview.",
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
        return output_path


    def _manual_database_entry_url(database: str) -> str:
        return {
            "pubmed": "https://pubmed.ncbi.nlm.nih.gov/",
            "web_of_science": "https://www.webofscience.com/",
            "embase": "https://www.embase.com/",
            "cochrane": "https://www.cochranelibrary.com/",
            "cnki": "https://www.cnki.net/",
            "wanfang": "https://www.wanfangdata.com.cn/",
            "vip": "https://www.cqvip.com/",
        }.get(database, "")


    def _pico_page(project_dir: Path, *, on_refresh: Callable[[], None], on_next: Callable[[], None]) -> QFrame:
        service = PICOWorkspaceService()
        draft = service.load_draft(project_dir)
        confirmed = service.load_confirmed(project_dir)
        ui_draft = _load_json_object(_pico_ui_draft_path(project_dir))
        frame = QFrame()
        frame.setObjectName("metaPicoPage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(_page_header("研究问题与 PICO", "输入中文研究问题，选择 PICO/PICOS/PECO，生成草稿并由用户确认 Protocol。", "需要人工确认"))
        input_card = _card("输入研究问题")
        input_layout = input_card.layout()
        question = QPlainTextEdit()
        question.setObjectName("metaPicoQuestionInput")
        question.setPlaceholderText("例如：高血压患者降压药对卒中风险的影响")
        question.setMaximumHeight(96)
        if draft:
            question.setPlainText(draft.research_question_original)
        input_layout.addWidget(question)
        mode_selector = QComboBox()
        mode_selector.setObjectName("metaPicoModeSelector")
        for label, value in (("PICO", "pico"), ("PICOS", "picos"), ("PECO", "peco")):
            mode_selector.addItem(label, value)
        selected_mode = draft.pico_mode if draft else "pico"
        mode_selector.setCurrentIndex(max(0, mode_selector.findData(selected_mode)))
        input_layout.addWidget(mode_selector)
        generate = QPushButton("生成 PICO 草稿")
        generate.setObjectName("metaPrimaryButton")
        input_layout.addWidget(generate)
        layout.addWidget(input_card)

        draft_fields = {
            "population": QLineEdit(draft.population if draft else ""),
            "intervention": QLineEdit(draft.intervention if draft else ""),
            "exposure": QLineEdit(draft.exposure if draft else ""),
            "comparator": QLineEdit(draft.comparator if draft else ""),
            "outcome": QLineEdit(draft.outcome if draft else ""),
            "study_design": QLineEdit(draft.study_design if draft else ""),
            "inclusion_criteria": QLineEdit(str(ui_draft.get("inclusion_criteria") or (_default_inclusion_criteria(draft) if draft else ""))),
            "exclusion_criteria": QLineEdit(str(ui_draft.get("exclusion_criteria") or ("；".join(draft.exclusion_scope) if draft else ""))),
            "primary_outcomes": QLineEdit(str(ui_draft.get("primary_outcomes") or (draft.outcome if draft else ""))),
            "secondary_outcomes": QLineEdit(str(ui_draft.get("secondary_outcomes") or "")),
            "effect_measure": QLineEdit(str(ui_draft.get("effect_measure") or (_recommended_effect_measure(draft) if draft else ""))),
        }
        for key, field in draft_fields.items():
            field.setObjectName(f"metaPico{''.join(part.title() for part in key.split('_'))}Input")
        draft_card = _card("PICO / PICOS / PECO 草稿")
        draft_layout = draft_card.layout()
        if draft:
            draft_layout.addWidget(_kv_label("Draft ID", draft.protocol_id))
            for label, key in (
                ("P 研究对象", "population"),
                ("I 干预", "intervention"),
                ("E 暴露", "exposure"),
                ("C 对照", "comparator"),
                ("O 结局", "outcome"),
                ("S 研究类型", "study_design"),
                ("纳入标准草稿", "inclusion_criteria"),
                ("排除标准草稿", "exclusion_criteria"),
                ("主要结局", "primary_outcomes"),
                ("次要结局", "secondary_outcomes"),
                ("推荐效应量类型", "effect_measure"),
            ):
                draft_layout.addWidget(QLabel(label))
                draft_layout.addWidget(draft_fields[key])
            if draft.warnings:
                draft_layout.addWidget(_warning_label("；".join(draft.warnings)))
        else:
            draft_layout.addWidget(QLabel("尚未生成草稿。"))
        save = QPushButton("保存草稿编辑")
        save.setObjectName("metaSecondaryButton")
        confirm = QPushButton("确认研究问题")
        confirm.setObjectName("metaPrimaryButton")
        next_button = QPushButton("下一步：检索策略")
        next_button.setObjectName("metaSecondaryButton")
        row = QHBoxLayout()
        row.addWidget(save)
        row.addWidget(confirm)
        row.addWidget(next_button)
        row.addStretch(1)
        draft_layout.addLayout(row)
        layout.addWidget(draft_card)

        confirmed_lines = ["尚未确认。"]
        if confirmed:
            confirmed_lines = [
                f"Confirmed ID：{confirmed.confirmed_protocol_id}",
                f"模式：{confirmed.confirmed_pico_mode}",
                f"P：{confirmed.confirmed_population}",
                f"I/E：{confirmed.confirmed_intervention_or_exposure}",
                f"C：{confirmed.confirmed_comparator}",
                f"O：{'；'.join(confirmed.confirmed_outcomes)}",
                f"Meta 类型：{confirmed.confirmed_meta_type}",
                f"补充说明：{confirmed.user_notes or '无'}",
            ]
        layout.addWidget(_info_card("已确认研究问题", confirmed_lines, object_name="metaConfirmedProtocolCard"))
        layout.addWidget(_developer_details(f"project_dir={project_dir}\ndraft={bool(draft)} confirmed={bool(confirmed)}"))
        layout.addStretch(1)

        def do_generate() -> None:
            text = question.toPlainText().strip()
            if not text:
                _show_message("请输入研究问题")
                return
            service.generate_draft(project_dir, text, pico_mode=str(mode_selector.currentData()), actor="reviewer")
            on_refresh()

        def do_save() -> None:
            if not service.load_draft(project_dir):
                _show_message("请先生成草稿")
                return
            service.edit_draft(
                project_dir,
                actor="reviewer",
                updates={
                    "pico_mode": str(mode_selector.currentData()),
                    "population": draft_fields["population"].text().strip(),
                    "intervention": draft_fields["intervention"].text().strip(),
                    "exposure": draft_fields["exposure"].text().strip(),
                    "comparator": draft_fields["comparator"].text().strip(),
                    "outcome": draft_fields["primary_outcomes"].text().strip() or draft_fields["outcome"].text().strip(),
                    "study_design": draft_fields["study_design"].text().strip(),
                    "exclusion_scope": [item.strip() for item in draft_fields["exclusion_criteria"].text().split("；") if item.strip()],
                },
            )
            _save_pico_ui_draft(project_dir, draft_fields)
            on_refresh()

        def do_confirm() -> None:
            current = service.load_draft(project_dir)
            if current is None:
                _show_message("请先生成草稿")
                return
            meta_type = _default_meta_type(current.meta_type_candidates)
            service.confirm_protocol(
                project_dir,
                actor="reviewer",
                confirmed_meta_type=meta_type,
                user_notes="\n".join(
                    [
                        f"纳入标准草稿：{draft_fields['inclusion_criteria'].text().strip()}",
                        f"排除标准草稿：{draft_fields['exclusion_criteria'].text().strip()}",
                        f"主要结局：{draft_fields['primary_outcomes'].text().strip()}",
                        f"次要结局：{draft_fields['secondary_outcomes'].text().strip()}",
                        f"推荐效应量类型：{draft_fields['effect_measure'].text().strip()}",
                    ]
                ),
                overrides={
                    "confirmed_pico_mode": str(mode_selector.currentData()),
                    "confirmed_population": draft_fields["population"].text().strip(),
                    "confirmed_intervention_or_exposure": draft_fields["exposure"].text().strip() or draft_fields["intervention"].text().strip(),
                    "confirmed_comparator": draft_fields["comparator"].text().strip(),
                    "confirmed_outcomes": [
                        item.strip()
                        for item in (draft_fields["primary_outcomes"].text() + "；" + draft_fields["secondary_outcomes"].text()).split("；")
                        if item.strip()
                    ],
                    "confirmed_study_design": draft_fields["study_design"].text().strip(),
                },
            )
            on_refresh()

        generate.clicked.connect(do_generate)
        save.clicked.connect(do_save)
        confirm.clicked.connect(do_confirm)
        next_button.clicked.connect(on_next)
        return frame


    def _search_strategy_page(project_dir: Path, *, on_refresh: Callable[[], None], on_next: Callable[[], None]) -> QFrame:
        service = SearchStrategyBuilderService()
        drafts = list(service.load_drafts(project_dir))
        confirmed = list(service.load_confirmed(project_dir))
        draft_by_database = {draft.database: draft for draft in drafts}
        confirmed_by_database = {item.database: item for item in confirmed}
        frame = QFrame()
        frame.setObjectName("metaSearchStrategyPage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        confirmed_protocol = PICOWorkspaceService().load_confirmed(project_dir)
        layout.addWidget(_page_header("检索策略", "读取已确认 Protocol，生成可人工复核的多数据库检索草稿。", "草稿阶段"))
        if not (project_dir / "protocol" / "pico_workspace_confirmed.json").exists():
            layout.addWidget(_info_card("请先确认研究问题", ["没有 confirmed protocol 时不能生成正式检索策略草稿。"]))
            layout.addStretch(1)
            return frame
        if confirmed_protocol:
            layout.addWidget(
                _info_card(
                    "已确认 Protocol",
                    [
                        f"研究类型：{confirmed_protocol.confirmed_pico_mode.upper()}",
                        f"研究对象：{confirmed_protocol.confirmed_population or '待补充'}",
                        f"干预/暴露：{confirmed_protocol.confirmed_intervention_or_exposure or '待补充'}",
                        f"对照：{confirmed_protocol.confirmed_comparator or '待补充'}",
                        f"结局：{'；'.join(confirmed_protocol.confirmed_outcomes) or '待补充'}",
                        "下一阶段将基于该方案生成检索策略",
                    ],
                    object_name="metaSearchConfirmedProtocolCard",
                )
            )
        workbench = _card("检索策略工作台")
        workbench_layout = workbench.layout()
        split = QHBoxLayout()
        database_list = QListWidget()
        database_list.setObjectName("metaSearchDatabaseList")
        for database in _search_database_order():
            draft = draft_by_database.get(database)
            item = QListWidgetItem(f"{_database_label(database)} · {_search_strategy_status(draft, confirmed_by_database.get(database))}")
            item.setData(Qt.ItemDataRole.UserRole, database)
            database_list.addItem(item)
        split.addWidget(database_list, 1)

        editor_panel = QFrame()
        editor_layout = QVBoxLayout(editor_panel)
        selected_database_label = QLabel("请选择数据库")
        selected_database_label.setObjectName("metaSearchSelectedDatabaseLabel")
        editor = QPlainTextEdit()
        editor.setObjectName("metaSearchQueryEditor")
        editor.setPlaceholderText("生成检索策略后可编辑当前数据库检索式。")
        status_label = QLabel("状态：未生成")
        status_label.setObjectName("metaSearchStatusLabel")
        status_label.setWordWrap(True)
        database_notice = QLabel("")
        database_notice.setObjectName("metaMutedText")
        database_notice.setWordWrap(True)
        editor_layout.addWidget(selected_database_label)
        editor_layout.addWidget(editor)
        editor_layout.addWidget(status_label)
        editor_layout.addWidget(database_notice)
        split.addWidget(editor_panel, 3)
        workbench_layout.addLayout(split)

        actions = QHBoxLayout()
        generate = QPushButton("生成检索策略")
        generate.setObjectName("metaPrimaryButton")
        save_edit = QPushButton("保存当前编辑")
        save_edit.setObjectName("metaSecondaryButton")
        confirm_one = QPushButton("确认当前检索式")
        confirm_one.setObjectName("metaSecondaryButton")
        confirm_all = QPushButton("确认全部检索式")
        confirm_all.setObjectName("metaSecondaryButton")
        export = QPushButton("导出 TXT / MD / JSON")
        export.setObjectName("metaSecondaryButton")
        copy_query = QPushButton("复制检索式")
        copy_query.setObjectName("metaSecondaryButton")
        copy_database_entry = QPushButton("复制数据库入口")
        copy_database_entry.setObjectName("metaSecondaryButton")
        export_execution_manifest = QPushButton("导出检索执行清单")
        export_execution_manifest.setObjectName("metaSecondaryButton")
        export_search_package = QPushButton("导出检索策略包")
        export_search_package.setObjectName("metaSecondaryButton")
        pubmed_execute = QPushButton("执行 PubMed testing-level 检索")
        pubmed_execute.setObjectName("metaPubMedExecuteButton")
        next_button = QPushButton("下一步：文献库与导入")
        next_button.setObjectName("metaSecondaryButton")
        for button in (generate, save_edit, confirm_one, confirm_all, export, copy_query, copy_database_entry, export_execution_manifest, export_search_package, pubmed_execute, next_button):
            actions.addWidget(button)
        actions.addStretch(1)
        workbench_layout.addLayout(actions)
        layout.addWidget(workbench)

        preview = _latest_pubmed_preview_payload(project_dir)
        execution_report = _load_json_object(project_dir / "protocol" / "search_execution_report.json")
        candidate_card = _card("PubMed 候选文献")
        candidate_layout = candidate_card.layout()
        candidate_summary = QLabel(_pubmed_preview_summary(preview, execution_report=execution_report))
        candidate_summary.setObjectName("metaMutedText")
        candidate_summary.setWordWrap(True)
        candidate_layout.addWidget(candidate_summary)
        candidate_table = QTableWidget()
        candidate_table.setObjectName("metaPubMedCandidateTable")
        candidate_table.setColumnCount(8)
        candidate_table.setHorizontalHeaderLabels(["序号", "PMID", "年份", "第一作者", "标题", "期刊", "摘要", "处理状态"])
        candidate_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        candidate_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        candidate_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        candidate_table.setAlternatingRowColors(True)
        candidate_detail = QTextEdit()
        candidate_detail.setObjectName("metaPubMedCandidateDetail")
        candidate_detail.setReadOnly(True)
        candidate_detail.setPlainText("请选择一条候选文献以查看英文标题和摘要。")
        user_note = QPlainTextEdit()
        user_note.setObjectName("metaPubMedCandidateUserNote")
        user_note.setPlaceholderText("用户备注，仅显示在当前界面，不参与检索、识别或去重。")
        user_note.setMaximumHeight(70)
        candidate_page_info = QLabel(_pubmed_page_info_text(preview, execution_report=execution_report))
        candidate_page_info.setObjectName("metaMutedText")
        candidate_page_info.setWordWrap(True)
        candidate_layout.addWidget(candidate_page_info)
        candidate_actions = QHBoxLayout()
        select_all = QPushButton("全选")
        clear_selection = QPushButton("取消全选")
        import_selected = QPushButton("选择加入文献库")
        ignore_batch = QPushButton("忽略本批次")
        for button in (select_all, clear_selection, import_selected, ignore_batch):
            button.setObjectName("metaSecondaryButton")
            candidate_actions.addWidget(button)
        candidate_actions.addStretch(1)
        candidate_layout.addLayout(candidate_actions)
        candidate_layout.addWidget(candidate_table)
        candidate_layout.addWidget(candidate_detail)
        candidate_layout.addWidget(user_note)
        layout.addWidget(candidate_card)

        layout.addWidget(
            _info_card(
                "导出与限制",
                [
                    f"已生成草稿：{len(drafts)} 个数据库",
                    f"已确认检索式：{len(confirmed)} 个数据库",
                    "PubMed 仅为 testing-level 在线执行；其他数据库支持检索式生成、编辑、确认、复制和导出。",
                ],
                object_name="metaConfirmedSearchCard",
            )
        )
        layout.addWidget(_developer_details(f"drafts={len(drafts)} confirmed={len(confirmed)} project_dir={project_dir}"))
        layout.addStretch(1)

        def selected_database() -> str:
            item = database_list.currentItem()
            return str(item.data(Qt.ItemDataRole.UserRole)) if item else "pubmed"

        def update_editor(_index: int = 0) -> None:
            database = selected_database()
            draft = draft_by_database.get(database)
            confirmed_strategy = confirmed_by_database.get(database)
            selected_database_label.setText(_database_label(database))
            editor.setPlainText(draft.boolean_query if draft else "")
            status_label.setText(f"状态：{_search_strategy_status(draft, confirmed_strategy)}")
            database_notice.setText(_database_manual_notice(database))
            has_confirmed_pubmed = database == "pubmed" and confirmed_strategy is not None and bool(confirmed_strategy.confirmed_query)
            pubmed_execute.setVisible(database == "pubmed")
            pubmed_execute.setEnabled(has_confirmed_pubmed)
            save_edit.setEnabled(draft is not None)
            confirm_one.setEnabled(draft is not None)
            copy_query.setEnabled(bool(draft and draft.boolean_query))

        def do_generate() -> None:
            try:
                service.generate_from_confirmed_protocol(project_dir, actor="reviewer")
            except Exception as exc:
                _show_message(str(exc))
                return
            on_refresh()

        def do_save_edit() -> None:
            database = selected_database()
            draft = draft_by_database.get(database)
            if draft is None:
                _show_message("请先生成检索策略")
                return
            service.edit_draft(project_dir, search_strategy_id=draft.search_strategy_id, updates={"boolean_query": editor.toPlainText()}, actor="reviewer")
            on_refresh()

        def do_confirm_one() -> None:
            database = selected_database()
            try:
                service.confirm_strategies(project_dir, actor="reviewer", database_ids=(database,))
            except Exception as exc:
                _show_message(str(exc))
                return
            on_refresh()

        def do_confirm_all() -> None:
            try:
                service.confirm_strategies(project_dir, actor="reviewer")
            except Exception as exc:
                _show_message(str(exc))
                return
            on_refresh()

        def do_export() -> None:
            try:
                md_path, txt_path = service.export_drafts(project_dir)
                json_path = service.draft_set_path(project_dir)
            except Exception as exc:
                _show_message(str(exc))
                return
            _show_message(
                "已导出到项目目录："
                + "；".join(
                    str(path.relative_to(project_dir))
                    for path in (txt_path, md_path, json_path)
                )
            )

        def do_copy_query() -> None:
            clipboard = QApplication.clipboard() if QApplication is not None else None
            if clipboard is not None:
                clipboard.setText(editor.toPlainText())

        def do_copy_database_entry() -> None:
            database = current_database()
            url = _manual_database_entry_url(database)
            if not url:
                _show_message("当前数据库暂无入口 URL。")
                return
            _copy_text_to_clipboard(url)
            _show_message(f"{_database_label(database)} 入口已复制。")

        def do_export_execution_manifest() -> None:
            path = _write_search_execution_manifest(project_dir)
            _show_message(f"已导出检索执行清单：{path.name}")
            on_refresh()

        def do_export_search_package() -> None:
            path = _write_search_strategy_package(project_dir)
            _show_message(f"已导出检索策略包：{path.name}")
            on_refresh()

        def do_pubmed_execute() -> None:
            confirmed_strategy = confirmed_by_database.get("pubmed")
            if confirmed_strategy is None or not confirmed_strategy.confirmed_query.strip():
                _show_message("请先确认 PubMed 检索式。")
                return
            execution = PubMedSearchService().search_pubmed(confirmed_strategy.confirmed_query, max_results=20)
            report_path = _write_pubmed_execution_report(project_dir, execution)
            preview = PubMedCandidatesHandoffService().create_candidates_preview(
                project_dir,
                execution=execution,
                execution_report_path=str(report_path.relative_to(project_dir)),
                search_strategy_snapshot_path=str(service.confirmed_set_path(project_dir).relative_to(project_dir)),
                project_id=project_dir.name,
            )
            _show_message(f"PubMed testing-level 检索完成：候选 {len(preview.candidates)} 条。")
            on_refresh()

        preview_candidates = _items_from_payload(preview, "candidates")
        row_candidates: list[dict[str, object]] = []

        def populate_candidate_table() -> None:
            row_candidates.clear()
            row_candidates.extend(preview_candidates)
            candidate_table.setRowCount(len(row_candidates))
            for row, candidate in enumerate(row_candidates):
                values = [
                    str(row + 1),
                    str(candidate.get("pmid") or "-"),
                    str(candidate.get("year") or "-"),
                    _first_author(candidate) or "-",
                    str(candidate.get("title") or "Untitled"),
                    str(candidate.get("journal") or "-"),
                    "有摘要" if str(candidate.get("abstract") or "").strip() else "无摘要",
                    _pubmed_candidate_status_label(candidate),
                ]
                for col, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    if col == 0:
                        item.setData(Qt.ItemDataRole.UserRole, str(candidate.get("candidate_id", "")))
                    candidate_table.setItem(row, col, item)

        def update_candidate_detail(row: int = -1, _col: int = 0) -> None:
            if row < 0 or row >= len(row_candidates):
                candidate_detail.setPlainText("请选择一条候选文献以查看英文标题和摘要。")
                return
            candidate_detail.setPlainText(_candidate_detail_text(row_candidates[row]))

        def do_import_selected() -> None:
            preview_id = str(preview.get("preview_id", ""))
            selected_rows = _selected_table_rows(candidate_table)
            selected_ids = tuple(
                str(row_candidates[row].get("candidate_id", ""))
                for row in selected_rows
                if 0 <= row < len(row_candidates)
            )
            if not preview_id or not selected_ids:
                _show_message("请先选择候选文献。")
                return
            result = PubMedCandidatesHandoffService().import_selected_candidates(
                project_dir,
                preview_id=preview_id,
                selected_candidate_ids=selected_ids,
                actor="reviewer",
            )
            _show_message(result.message)
            on_refresh()

        def do_ignore_batch() -> None:
            candidate_table.clearSelection()
            candidate_detail.setPlainText("请选择一条候选文献以查看英文标题和摘要。")
            _show_message("已忽略当前候选批次；未写入文献库。")

        database_list.currentRowChanged.connect(update_editor)
        generate.clicked.connect(do_generate)
        save_edit.clicked.connect(do_save_edit)
        confirm_one.clicked.connect(do_confirm_one)
        confirm_all.clicked.connect(do_confirm_all)
        export.clicked.connect(do_export)
        copy_query.clicked.connect(do_copy_query)
        copy_database_entry.clicked.connect(do_copy_database_entry)
        export_execution_manifest.clicked.connect(do_export_execution_manifest)
        export_search_package.clicked.connect(do_export_search_package)
        pubmed_execute.clicked.connect(do_pubmed_execute)
        next_button.clicked.connect(on_next)
        select_all.clicked.connect(candidate_table.selectAll)
        clear_selection.clicked.connect(candidate_table.clearSelection)
        import_selected.clicked.connect(do_import_selected)
        ignore_batch.clicked.connect(do_ignore_batch)
        candidate_table.cellClicked.connect(update_candidate_detail)
        database_list.setCurrentRow(0)
        populate_candidate_table()
        return frame


    def _literature_acquisition_page(project_dir: Path, *, on_refresh: Callable[[], None], on_next: Callable[[], None]) -> QFrame:
        preview_paths = sorted((project_dir / "protocol" / "pubmed_candidates").glob("*_candidates_preview.json"))
        library = LiteratureLibraryService()
        records = library.list_records(project_dir)
        manifest = library.read_manifest(project_dir)
        library_diagnostics = _literature_library_diagnostics(project_dir, records=records)
        frame = QFrame()
        frame.setObjectName("metaLiteratureAcquisitionPage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(_page_header("文献库与导入", "PubMed candidates 和本地 NBIB/RIS/CSV 导入；不把数据库检索伪装为已执行。", "人工导入"))
        candidate_card = _card("PubMed candidates preview")
        candidate_layout = candidate_card.layout()
        preview_selector = QComboBox()
        preview_selector.setObjectName("metaPubMedPreviewSelector")
        candidate_list = QListWidget()
        candidate_list.setObjectName("metaPubMedCandidateList")
        candidate_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        candidate_detail = QTextEdit()
        candidate_detail.setObjectName("metaLiteraturePubMedCandidateDetail")
        candidate_detail.setReadOnly(True)
        previews = [_load_json_object(path) for path in preview_paths]
        for path, preview in zip(preview_paths, previews):
            preview_id = str(preview.get("preview_id") or path.name.replace("_candidates_preview.json", ""))
            preview_selector.addItem(f"{preview_id} · {len(_items_from_payload(preview, 'candidates'))} 条", preview_id)
        candidate_layout.addWidget(preview_selector)
        selection_row = QHBoxLayout()
        select_all = QPushButton("全选")
        clear_selection = QPushButton("取消全选")
        ignore_batch = QPushButton("忽略本批次")
        for button in (select_all, clear_selection, ignore_batch):
            button.setObjectName("metaSecondaryButton")
            selection_row.addWidget(button)
        selection_row.addStretch(1)
        candidate_layout.addLayout(selection_row)
        candidate_layout.addWidget(candidate_list)
        import_selected = QPushButton("导入选中文献")
        import_selected.setObjectName("metaPrimaryButton")
        candidate_layout.addWidget(import_selected)
        candidate_layout.addWidget(candidate_detail)
        layout.addWidget(candidate_card)
        local_card = _card("本地文献导入")
        local_layout = local_card.layout()
        local_layout.addWidget(QLabel("支持 NBIB / RIS / CSV / PubMed XML。其他格式仅按 testing-level preview 解析，不做过度承诺。"))
        import_file = QPushButton("选择文件导入")
        import_file.setObjectName("metaSecondaryButton")
        local_layout.addWidget(import_file)
        layout.addWidget(local_card)
        layout.addWidget(_info_card("文献库摘要", _literature_import_summary_lines(project_dir, manifest), object_name="metaImportBatchSummary"))
        layout.addWidget(_info_card("文献库诊断", _literature_diagnostics_lines(library_diagnostics), object_name="metaLiteratureDiagnosticsSummary"))
        layout.addWidget(_info_card("最近导入诊断", _latest_multisource_diagnostics_lines(project_dir), object_name="metaImportDiagnosticsSummary"))

        library_card = _card("文献列表")
        library_layout = library_card.layout()
        filter_row = QHBoxLayout()
        search_input = QLineEdit()
        search_input.setObjectName("metaLiteratureSearchInput")
        search_input.setPlaceholderText("搜索标题 / 作者 / DOI / PMID")
        source_filter = QComboBox()
        source_filter.setObjectName("metaLiteratureSourceFilter")
        source_filter.addItem("全部来源", "")
        for source in _literature_source_filter_values(records):
            source_filter.addItem(_source_label(source), source)
        missing_filter = QComboBox()
        missing_filter.setObjectName("metaLiteratureMissingFilter")
        for label, value in (
            ("全部字段", ""),
            ("缺 DOI", "doi"),
            ("缺 PMID", "pmid"),
            ("缺 Abstract", "abstract"),
            ("缺年份", "year"),
            ("缺期刊", "journal"),
        ):
            missing_filter.addItem(label, value)
        export_summary = QPushButton("导出文献库摘要")
        export_summary.setObjectName("metaSecondaryButton")
        export_acquisition_manifest = QPushButton("导出获取/整理清单")
        export_acquisition_manifest.setObjectName("metaSecondaryButton")
        filter_row.addWidget(search_input, 2)
        filter_row.addWidget(source_filter)
        filter_row.addWidget(missing_filter)
        filter_row.addWidget(export_summary)
        filter_row.addWidget(export_acquisition_manifest)
        library_layout.addLayout(filter_row)
        literature_table = QTableWidget()
        literature_table.setObjectName("metaLiteratureRecordsTable")
        literature_table.setColumnCount(8)
        literature_table.setHorizontalHeaderLabels(["标题", "年份", "期刊", "PMID", "DOI", "来源", "Abstract", "状态"])
        literature_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        literature_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        library_layout.addWidget(literature_table)
        detail = QTextEdit()
        detail.setObjectName("metaLiteratureDetailPanel")
        detail.setReadOnly(True)
        note_input = QPlainTextEdit()
        note_input.setObjectName("metaLiteratureUserNote")
        note_input.setPlaceholderText("用户备注，仅作为人工备注保存，不参与检索、去重、筛选、提取或统计。")
        note_input.setMaximumHeight(80)
        save_note = QPushButton("保存备注")
        save_note.setObjectName("metaSecondaryButton")
        copy_pubmed_link = QPushButton("复制 PubMed 链接")
        copy_pubmed_link.setObjectName("metaSecondaryButton")
        copy_doi_link = QPushButton("复制 DOI 链接")
        copy_doi_link.setObjectName("metaSecondaryButton")
        copy_citation = QPushButton("复制引用信息")
        copy_citation.setObjectName("metaSecondaryButton")
        export_citation_manifest = QPushButton("导出引用整理清单")
        export_citation_manifest.setObjectName("metaSecondaryButton")
        export_ris = QPushButton("导出 RIS")
        export_ris.setObjectName("metaSecondaryButton")
        export_bibtex = QPushButton("导出 BibTeX")
        export_bibtex.setObjectName("metaSecondaryButton")
        export_csl_json = QPushButton("导出 CSL-JSON")
        export_csl_json.setObjectName("metaSecondaryButton")
        export_register_csv = QPushButton("导出文献台账 CSV")
        export_register_csv.setObjectName("metaSecondaryButton")
        export_literature_package = QPushButton("导出文献整理包")
        export_literature_package.setObjectName("metaSecondaryButton")
        generate_all_literature_artifacts = QPushButton("生成全部文献整理产物")
        generate_all_literature_artifacts.setObjectName("metaPrimaryButton")
        link_row = QHBoxLayout()
        link_row.addWidget(save_note)
        link_row.addWidget(copy_pubmed_link)
        link_row.addWidget(copy_doi_link)
        link_row.addWidget(copy_citation)
        link_row.addWidget(export_citation_manifest)
        link_row.addWidget(export_ris)
        link_row.addWidget(export_bibtex)
        link_row.addWidget(export_csl_json)
        link_row.addWidget(export_register_csv)
        link_row.addWidget(export_literature_package)
        link_row.addWidget(generate_all_literature_artifacts)
        link_row.addStretch(1)
        library_layout.addWidget(detail)
        library_layout.addWidget(note_input)
        library_layout.addLayout(link_row)
        layout.addWidget(library_card)

        next_button = QPushButton("下一步：去重与筛选")
        next_button.setObjectName("metaSecondaryButton")
        layout.addWidget(next_button)
        layout.addWidget(_developer_details(f"previews={len(previews)} project_dir={project_dir}"))
        layout.addStretch(1)

        def load_preview(index: int = 0) -> None:
            candidate_list.clear()
            if index < 0 or index >= len(previews):
                return
            preview = previews[index]
            for candidate in _items_from_payload(preview, "candidates"):
                candidate_id = str(candidate.get("candidate_id", ""))
                text = f"{candidate.get('title') or 'Untitled'} · PMID {candidate.get('pmid') or '-'}"
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, candidate_id)
                item.setToolTip(_candidate_detail_text(candidate))
                candidate_list.addItem(item)
            update_detail()

        def update_detail() -> None:
            index = candidate_list.currentRow()
            if index < 0:
                candidate_detail.setPlainText("暂无候选文献。")
                return
            preview_index = preview_selector.currentIndex()
            if preview_index < 0 or preview_index >= len(previews):
                candidate_detail.setPlainText("暂无候选文献。")
                return
            candidates = _items_from_payload(previews[preview_index], "candidates")
            candidate_detail.setPlainText(_candidate_detail_text(candidates[index] if index < len(candidates) else {}))

        def do_import_selected() -> None:
            preview_id = preview_selector.currentData()
            selected_ids = []
            for item in candidate_list.selectedItems():
                selected_ids.append(str(item.data(Qt.ItemDataRole.UserRole)))
            if not preview_id or not selected_ids:
                _show_message("请选择 PubMed candidates")
                return
            result = PubMedCandidatesHandoffService().import_selected_candidates(
                project_dir,
                preview_id=str(preview_id),
                selected_candidate_ids=tuple(selected_ids),
                actor="reviewer",
            )
            _show_message(result.message)
            on_refresh()

        def do_import_file() -> None:
            filename, _ = QFileDialog.getOpenFileName(frame, "选择文献文件", str(project_dir), "Literature (*.nbib *.ris *.csv *.xml);;All files (*)")
            if not filename:
                return
            result = MultiSourceLiteratureImportService().import_file(project_dir, source_path=Path(filename), source_format="auto")
            _show_message(result.message)
            on_refresh()

        row_records: list[dict[str, object]] = []

        def populate_literature_table() -> None:
            row_records.clear()
            for record in records:
                if _record_matches_literature_filters(
                    record,
                    query=search_input.text(),
                    source_type=str(source_filter.currentData() or ""),
                    missing_field=str(missing_filter.currentData() or ""),
                ):
                    row_records.append(record)
            literature_table.setRowCount(len(row_records))
            for row, record in enumerate(row_records):
                values = [
                    str(record.get("title", "")),
                    str(record.get("year", "")),
                    str(record.get("journal") or record.get("publication_title") or ""),
                    str(record.get("pmid", "")),
                    str(record.get("doi", "")),
                    _source_label(str(record.get("source_type") or record.get("source") or "")),
                    "有" if str(record.get("abstract", "")).strip() else "无",
                    _record_status_label(record),
                ]
                for col, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    if col == 0:
                        item.setData(Qt.ItemDataRole.UserRole, str(record.get("record_id", "")))
                    literature_table.setItem(row, col, item)
            update_literature_detail(literature_table.currentRow())

        def update_literature_detail(row: int = 0, _col: int = 0) -> None:
            if 0 <= row < len(row_records):
                record = row_records[row]
                detail.setPlainText(_record_detail(record, user_note=_load_literature_note(project_dir, str(record.get("record_id", "")))))
                note_input.setPlainText(_load_literature_note(project_dir, str(record.get("record_id", ""))))
            else:
                detail.setPlainText("暂无文献。")
                note_input.setPlainText("")

        def do_save_note() -> None:
            row = literature_table.currentRow()
            if row < 0 or row >= len(row_records):
                _show_message("请先选择文献")
                return
            _save_literature_note(project_dir, str(row_records[row].get("record_id", "")), note_input.toPlainText())
            update_literature_detail(row)
            _show_message("备注已保存。")

        def selected_literature_record() -> dict[str, object]:
            row = literature_table.currentRow()
            if row < 0 or row >= len(row_records):
                return {}
            return row_records[row]

        def do_copy_pubmed_link() -> None:
            record = selected_literature_record()
            pmid = str(record.get("pmid", "")).strip()
            if not pmid:
                _show_message("当前文献没有 PMID，无法生成 PubMed 链接。")
                return
            _copy_text_to_clipboard(f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
            _show_message("PubMed 链接已复制。")

        def do_copy_doi_link() -> None:
            record = selected_literature_record()
            doi = str(record.get("doi", "")).strip()
            if not doi:
                _show_message("当前文献没有 DOI，无法生成 DOI 链接。")
                return
            _copy_text_to_clipboard(f"https://doi.org/{doi}")
            _show_message("DOI 链接已复制。")

        def do_copy_citation() -> None:
            record = selected_literature_record()
            if not record:
                _show_message("请先选择文献")
                return
            _copy_text_to_clipboard(_literature_citation_text(record))
            _show_message("引用信息已复制。")

        def do_export_citation_manifest() -> None:
            path = _write_literature_citation_manifest(project_dir)
            _show_message(f"已导出引用整理清单：{path.name}")
            on_refresh()

        def do_export_ris() -> None:
            path = _write_literature_ris_export(project_dir)
            _show_message(f"已导出 RIS：{path.name}")
            on_refresh()

        def do_export_bibtex() -> None:
            path = _write_literature_bibtex_export(project_dir)
            _show_message(f"已导出 BibTeX：{path.name}")
            on_refresh()

        def do_export_csl_json() -> None:
            path = _write_literature_csl_json_export(project_dir)
            _show_message(f"已导出 CSL-JSON：{path.name}")
            on_refresh()

        def do_export_register_csv() -> None:
            path = _write_literature_register_csv(project_dir)
            _show_message(f"已导出文献台账 CSV：{path.name}")
            on_refresh()

        def do_export_literature_package() -> None:
            path = _write_literature_organization_package(project_dir)
            _show_message(f"已导出文献整理包：{path.name}")
            on_refresh()

        def do_generate_all_literature_artifacts() -> None:
            path = _write_literature_capability_artifact_index(project_dir)
            _show_message(f"已生成全部文献整理产物索引：{path.name}")
            on_refresh()

        def do_export_summary() -> None:
            path = _export_literature_library_summary(project_dir, diagnostics=library_diagnostics, records=records)
            _show_message(f"已导出：{path}")

        def do_export_acquisition_manifest() -> None:
            path = _write_literature_acquisition_manifest(project_dir)
            _show_message(f"已导出文献获取/整理清单：{path}")
            on_refresh()

        preview_selector.currentIndexChanged.connect(load_preview)
        candidate_list.currentRowChanged.connect(lambda _row: update_detail())
        select_all.clicked.connect(lambda: _set_all_list_items_selected(candidate_list, True))
        clear_selection.clicked.connect(lambda: _set_all_list_items_selected(candidate_list, False))
        ignore_batch.clicked.connect(lambda: (_set_all_list_items_selected(candidate_list, False), _show_message("已忽略当前候选批次；未写入文献库。")))
        import_selected.clicked.connect(do_import_selected)
        import_file.clicked.connect(do_import_file)
        search_input.textChanged.connect(lambda _text: populate_literature_table())
        source_filter.currentIndexChanged.connect(lambda _index: populate_literature_table())
        missing_filter.currentIndexChanged.connect(lambda _index: populate_literature_table())
        literature_table.cellClicked.connect(update_literature_detail)
        save_note.clicked.connect(do_save_note)
        copy_pubmed_link.clicked.connect(do_copy_pubmed_link)
        copy_doi_link.clicked.connect(do_copy_doi_link)
        copy_citation.clicked.connect(do_copy_citation)
        export_citation_manifest.clicked.connect(do_export_citation_manifest)
        export_ris.clicked.connect(do_export_ris)
        export_bibtex.clicked.connect(do_export_bibtex)
        export_csl_json.clicked.connect(do_export_csl_json)
        export_register_csv.clicked.connect(do_export_register_csv)
        export_literature_package.clicked.connect(do_export_literature_package)
        generate_all_literature_artifacts.clicked.connect(do_generate_all_literature_artifacts)
        export_summary.clicked.connect(do_export_summary)
        export_acquisition_manifest.clicked.connect(do_export_acquisition_manifest)
        next_button.clicked.connect(on_next)
        load_preview(0)
        populate_literature_table()
        return frame


    def _literature_library_page(project_dir: Path) -> QFrame:
        service = LiteratureLibraryService()
        records = service.list_records(project_dir)
        manifest = service.read_manifest(project_dir)
        frame = QFrame()
        frame.setObjectName("metaLiteratureLibraryPage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(_page_header("文献库", "统一 normalized literature library。", "只读"))
        layout.addWidget(_info_card("文献库摘要", [f"总记录数：{manifest.get('total_records', len(records))}", f"batch 数：{manifest.get('total_batches', 0)}", f"来源分布：{manifest.get('source_counts', {})}"], object_name="metaLibrarySummary"))
        missing_doi = len([record for record in records if not str(record.get("doi", "")).strip()])
        missing_pmid = len([record for record in records if not str(record.get("pmid", "")).strip()])
        missing_abstract = len([record for record in records if not str(record.get("abstract", "")).strip()])
        layout.addWidget(_info_card("Diagnostics", [f"缺 DOI：{missing_doi}", f"缺 PMID：{missing_pmid}", f"缺摘要：{missing_abstract}"], object_name="metaLibraryDiagnostics"))
        table = QTableWidget()
        table.setObjectName("metaLiteratureTable")
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["题名", "年份", "DOI", "PMID", "来源"])
        table.setRowCount(len(records))
        for row, record in enumerate(records):
            values = [
                str(record.get("title", "")),
                str(record.get("year", "")),
                str(record.get("doi", "")),
                str(record.get("pmid", "")),
                str(record.get("source_type", "")),
            ]
            for col, value in enumerate(values):
                table.setItem(row, col, QTableWidgetItem(value))
        detail = QTextEdit()
        detail.setObjectName("metaLiteratureDetailPreview")
        detail.setReadOnly(True)
        if records:
            detail.setPlainText(_record_detail(records[0]))
        layout.addWidget(table)
        layout.addWidget(detail)
        layout.addWidget(_developer_details(f"records_path={service.records_path(project_dir)}\nmanifest={manifest}"))
        layout.addStretch(1)

        def update_detail(row: int, _col: int = 0) -> None:
            if 0 <= row < len(records):
                detail.setPlainText(_record_detail(records[row]))

        table.cellClicked.connect(update_detail)
        return frame


    def _dedup_review_page(project_dir: Path, *, on_refresh: Callable[[], None], on_next: Callable[[], None]) -> QFrame:
        service = DedupReviewV2Service()
        screening_service = TitleAbstractScreeningV2Service()
        queue = service.load_queue(project_dir)
        groups = list(queue.groups)
        decisions_payload = _load_json_object(service.decisions_path(project_dir))
        decisions = _items_from_payload(decisions_payload, "decisions")
        decisions_by_group = {str(item.get("group_id", "")): str(item.get("decision", "")) for item in decisions}
        deduplicated_payload = _load_json_object(service.deduplicated_set_path(project_dir))
        screening_queue = screening_service.load_queue(project_dir)
        screening_records = _items_from_payload(screening_queue, "queue_records")
        screening_decisions = _items_from_payload(_load_json_object(screening_service.decisions_path(project_dir)), "screening_records")
        screening_decisions_by_record = {str(item.get("record_id", "")): item for item in screening_decisions}
        screening_summary = screening_service.screening_summary(project_dir)
        prisma_summary = PRISMAService().collect_literature_acquisition_summary(project_dir)
        frame = QFrame()
        frame.setObjectName("metaTitleAbstractScreeningPage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(_page_header("文献筛选", "去重后逐篇完成标题摘要筛选；AI/规则只作为 suggestion。", "人工复核"))
        risk_counts: dict[str, int] = {}
        for group in groups:
            risk_counts[group.risk_level] = risk_counts.get(group.risk_level, 0) + 1
        layout.addWidget(
            _info_card(
                "去重摘要",
                [
                    f"重复组：{len(groups)}",
                    f"风险等级：{_risk_counts_text(risk_counts)}",
                    f"已保存决定：{len(decisions)}",
                    f"active record：{deduplicated_payload.get('active_record_count') or deduplicated_payload.get('deduplicated_count') or '未生成'}",
                    f"待筛选队列：{screening_queue.get('record_count', 0) if isinstance(screening_queue, dict) else 0}",
                    "不自动删除原始记录。",
                ],
                object_name="metaDedupSummary",
            )
        )
        layout.addWidget(_info_card("PRISMA 数字", _stage_m3_prisma_lines(prisma_summary), object_name="metaPrismaDedupSummary"))

        actions = _card("主操作")
        action_layout = actions.layout()
        build_queue = QPushButton("生成重复组")
        build_queue.setObjectName("metaPrimaryButton")
        save_decision = QPushButton("保存人工决定")
        save_decision.setObjectName("metaPrimaryButton")
        generate_deduped = QPushButton("生成去重后文献库")
        generate_deduped.setObjectName("metaPrimaryButton")
        build_screening_queue = QPushButton("创建标题摘要筛选队列")
        build_screening_queue.setObjectName("metaPrimaryButton")
        export_screening_manifest = QPushButton("导出筛选整理清单")
        export_screening_manifest.setObjectName("metaSecondaryButton")
        next_button = QPushButton("下一步：排除标准")
        next_button.setObjectName("metaSecondaryButton")
        action_row = QHBoxLayout()
        action_row.addWidget(build_queue)
        action_row.addWidget(save_decision)
        action_row.addWidget(generate_deduped)
        action_row.addWidget(build_screening_queue)
        action_row.addWidget(export_screening_manifest)
        action_row.addWidget(next_button)
        action_row.addStretch(1)
        action_layout.addLayout(action_row)
        layout.addWidget(actions)

        content_row = QHBoxLayout()
        group_list = QListWidget()
        group_list.setObjectName("metaDedupGroupList")
        group_list.setMinimumWidth(320)
        for group in groups:
            decision_text = _dedup_decision_label(decisions_by_group.get(group.group_id, ""))
            item = QListWidgetItem(f"{_risk_label(group.risk_level)} · {decision_text}\n{group.duplicate_rule} · {len(group.record_ids)} 篇")
            item.setData(Qt.ItemDataRole.UserRole, group.group_id)
            group_list.addItem(item)
        content_row.addWidget(group_list, 1)

        right_panel = QFrame()
        right_panel.setObjectName("metaCard")
        right_layout = QVBoxLayout(right_panel)
        detail = QTextEdit()
        detail.setObjectName("metaDedupGroupDetail")
        detail.setReadOnly(True)
        preview = QTextEdit()
        preview.setObjectName("metaDedupMergePreview")
        preview.setReadOnly(True)
        record_selector = QComboBox()
        record_selector.setObjectName("metaDedupRecordSelector")
        decision_selector = QComboBox()
        decision_selector.setObjectName("metaDedupDecisionSelector")
        for label, value in (
            ("确认为重复并合并", DECISION_MERGE),
            ("保留全部", DECISION_KEEP_BOTH),
            ("标记为不是重复", DECISION_MARK_NOT_DUPLICATE),
            ("选择主记录", DECISION_SET_MASTER_RECORD),
            ("跳过稍后处理", DECISION_SKIP),
        ):
            decision_selector.addItem(label, value)
        note = QPlainTextEdit()
        note.setObjectName("metaDedupDecisionNote")
        note.setPlaceholderText("人工决定备注")
        note.setMaximumHeight(80)
        right_layout.addWidget(QLabel("重复组详情"))
        right_layout.addWidget(detail)
        right_layout.addWidget(QLabel("Merge preview"))
        right_layout.addWidget(preview)
        right_layout.addWidget(QLabel("保留候选"))
        right_layout.addWidget(record_selector)
        right_layout.addWidget(QLabel("人工决定"))
        right_layout.addWidget(decision_selector)
        right_layout.addWidget(note)
        log_detail = QTextEdit()
        log_detail.setObjectName("metaDedupDecisionLog")
        log_detail.setReadOnly(True)
        log_detail.setPlainText(_dedup_log_text(decisions))
        right_layout.addWidget(QLabel("去重日志"))
        right_layout.addWidget(log_detail)
        content_row.addWidget(right_panel, 2)
        layout.addLayout(content_row)

        screening_card = _card("标题摘要筛选")
        screening_card.setObjectName("metaScreeningWorkspaceCard")
        screening_layout = screening_card.layout()
        screening_layout.addWidget(
            _info_card(
                "当前 PRISMA 计数",
                [
                    f"导入文献数：{screening_summary.imported_total}",
                    f"去重后文献数：{screening_summary.after_dedup_total}",
                    f"标题摘要筛选未筛选：{screening_summary.title_abstract_unscreened}",
                    f"标题摘要筛选纳入：{screening_summary.title_abstract_included}",
                    f"标题摘要筛选排除：{screening_summary.title_abstract_excluded}",
                    f"不确定：{screening_summary.title_abstract_uncertain}",
                    f"需要全文：{screening_summary.full_text_needed}",
                    f"全文筛选纳入：{screening_summary.full_text_included}",
                    f"全文筛选排除：{screening_summary.full_text_excluded}",
                ],
                object_name="metaScreeningPrismaCounts",
            )
        )
        screening_content = QHBoxLayout()
        screening_table = QTableWidget()
        screening_table.setObjectName("metaScreeningWorkspaceRecordTable")
        screening_table.setMinimumWidth(520)
        screening_table.setColumnCount(8)
        screening_table.setHorizontalHeaderLabels(["序号", "标题", "第一作者", "年份", "期刊", "摘要", "AI 建议", "人工状态"])
        screening_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        screening_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        screening_table.setAlternatingRowColors(True)
        screening_content.addWidget(screening_table, 2)
        screening_panel = _card("当前文献库")
        screening_panel_layout = screening_panel.layout()
        screening_detail = QTextEdit()
        screening_detail.setObjectName("metaScreeningWorkspaceRecordDetail")
        screening_detail.setReadOnly(True)
        screening_detail.setPlainText("请选择左侧文献以查看标题、摘要、AI 建议和人工决策区。")
        ai_suggestion = QTextEdit()
        ai_suggestion.setObjectName("metaScreeningWorkspaceAISuggestion")
        ai_suggestion.setReadOnly(True)
        ai_suggestion.setPlainText("暂无 AI 建议。")
        screening_decision = QComboBox()
        screening_decision.setObjectName("metaScreeningWorkspaceDecisionSelector")
        for label, value in (
            ("未筛选", DECISION_NOT_SCREENED),
            ("纳入", DECISION_INCLUDE),
            ("排除", DECISION_EXCLUDE),
            ("不确定", DECISION_UNCERTAIN),
            ("需要全文", DECISION_NEED_FULL_TEXT),
            ("重置为未筛选", "reset_to_unscreened"),
        ):
            screening_decision.addItem(label, value)
        screening_reason = QComboBox()
        screening_reason.setObjectName("metaScreeningWorkspaceReasonSelector")
        screening_reason.addItem("排除原因", "")
        for code, label in EXCLUSION_REASON_LABELS_ZH.items():
            screening_reason.addItem(label, code)
        screening_notes = QPlainTextEdit()
        screening_notes.setObjectName("metaScreeningWorkspaceNotes")
        screening_notes.setPlaceholderText("筛选备注；AI/规则建议需人工接受或编辑后才生效")
        screening_notes.setMaximumHeight(86)
        quick_actions = QHBoxLayout()
        include_button = QPushButton("纳入")
        exclude_button = QPushButton("排除")
        uncertain_button = QPushButton("不确定")
        fulltext_button = QPushButton("需要全文")
        next_unscreened_button = QPushButton("保存并下一篇")
        for button in (include_button, exclude_button, uncertain_button, fulltext_button, next_unscreened_button):
            button.setObjectName("metaSecondaryButton")
            quick_actions.addWidget(button)
        save_screening_decision = QPushButton("保存筛选决定")
        save_screening_decision.setObjectName("metaPrimaryButton")
        screening_panel_layout.addWidget(QLabel("文献信息"))
        screening_panel_layout.addWidget(screening_detail)
        screening_panel_layout.addWidget(QLabel("AI 建议"))
        screening_panel_layout.addWidget(ai_suggestion)
        screening_panel_layout.addWidget(QLabel("筛选决策"))
        screening_panel_layout.addWidget(screening_decision)
        screening_panel_layout.addWidget(QLabel("排除原因"))
        screening_panel_layout.addWidget(screening_reason)
        screening_panel_layout.addWidget(screening_notes)
        screening_panel_layout.addLayout(quick_actions)
        screening_panel_layout.addWidget(save_screening_decision)
        screening_content.addWidget(screening_panel, 2)
        screening_layout.addLayout(screening_content)
        screening_layout.addWidget(QLabel("下一步：全文管理"))
        layout.addWidget(screening_card)
        layout.addWidget(
            _info_card(
                "下一步页面",
                [
                    "全文管理已作为独立侧栏页面接入。",
                    "完成去重与标题摘要筛选后，点击“下一步：全文管理”进入全文队列、PDF 上传、OCR 和全文筛选。",
                ],
                object_name="metaNextPageHint",
            )
        )
        layout.addWidget(_developer_details(f"queue_path={service.review_queue_path(project_dir)}\ndecisions_path={service.decisions_path(project_dir)}"))
        layout.addStretch(1)

        def selected_group_id() -> str:
            item = group_list.currentItem()
            return str(item.data(Qt.ItemDataRole.UserRole)) if item is not None else ""

        def refresh_group_detail(index: int = 0) -> None:
            record_selector.clear()
            if index < 0 or index >= len(groups):
                detail.setPlainText("暂无重复组。")
                preview.setPlainText("请先生成重复组。")
                return
            group = groups[index]
            for record_id in group.record_ids:
                record_selector.addItem(record_id, record_id)
            detail.setPlainText(_dedup_group_detail(group.to_dict()))
            preview_payload = service.preview_merge(project_dir, group_id=group.group_id, selected_record_id=str(record_selector.currentData() or ""))
            preview.setPlainText(json.dumps(preview_payload, ensure_ascii=False, indent=2))

        def update_preview(_index: int = 0) -> None:
            group_id = selected_group_id()
            if not group_id:
                return
            preview_payload = service.preview_merge(project_dir, group_id=group_id, selected_record_id=str(record_selector.currentData() or ""))
            preview.setPlainText(json.dumps(preview_payload, ensure_ascii=False, indent=2))

        def do_build_queue() -> None:
            result = service.build_review_queue(project_dir, project_id=project_dir.name)
            _show_message(result.message)
            on_refresh()

        def do_save_decision() -> None:
            group_id = selected_group_id()
            if not group_id:
                _show_message("请选择重复组")
                return
            decision = str(decision_selector.currentData() or DECISION_KEEP_BOTH)
            merged_record = {}
            if decision in {DECISION_MERGE, DECISION_SET_MASTER_RECORD}:
                merged_record = service.preview_merge(project_dir, group_id=group_id, selected_record_id=str(record_selector.currentData() or ""))
            service.save_decision(
                project_dir,
                group_id=group_id,
                decision=decision,
                actor="reviewer",
                selected_record_id=str(record_selector.currentData() or ""),
                merged_record=merged_record,
                note=note.toPlainText(),
            )
            _show_message("已保存人工去重决定；原始记录已保留。")
            on_refresh()

        def do_generate_deduped() -> None:
            result = service.generate_deduplicated_set(project_dir, project_id=project_dir.name)
            unresolved = len(result.get("unresolved_group_ids", []))
            if unresolved:
                _show_message(f"已生成去重后文献库，仍有 {unresolved} 个重复组待处理。")
            else:
                _show_message("去重后文献库已生成。")
            on_refresh()

        def do_build_screening_queue() -> None:
            skipped_all = bool(groups) and all(decisions_by_group.get(group.group_id) == DECISION_SKIP for group in groups)
            if not service.deduplicated_set_path(project_dir).exists() and groups and not skipped_all:
                _show_message("请先生成去重后文献库，或将重复组标记为稍后处理。")
                return
            result = screening_service.build_queue(project_dir, project_id=project_dir.name)
            _show_message(f"筛选队列已创建：{result.record_count} 篇。")
            on_refresh()

        def do_export_screening_manifest() -> None:
            path = _write_screening_organization_manifest(project_dir)
            _show_message(f"已导出筛选整理清单：{path.name}")
            on_refresh()

        screening_rows: list[dict[str, object]] = []

        def populate_screening_table() -> None:
            screening_rows.clear()
            screening_rows.extend(screening_records)
            screening_table.setRowCount(len(screening_rows))
            for row, record in enumerate(screening_rows):
                decision_payload = screening_decisions_by_record.get(str(record.get("record_id", "")), {})
                ai_payload = _screening_ai_suggestion_payload(project_dir, str(record.get("record_id", "")))
                values = [
                    str(row + 1),
                    str(record.get("title") or "Untitled"),
                    _first_author(record) or "-",
                    str(record.get("year") or "-"),
                    str(record.get("journal") or "-"),
                    "有摘要" if str(record.get("abstract") or "").strip() else "无摘要",
                    _screening_ai_suggestion_label(ai_payload),
                    _screening_decision_label(str(decision_payload.get("decision") or record.get("decision") or DECISION_NOT_SCREENED)),
                ]
                for col, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    if col == 0:
                        item.setData(Qt.ItemDataRole.UserRole, str(record.get("record_id", "")))
                    screening_table.setItem(row, col, item)

        def selected_screening_row() -> int:
            rows = _selected_table_rows(screening_table)
            return rows[0] if rows else -1

        def selected_screening_record_id() -> str:
            row = selected_screening_row()
            return str(screening_rows[row].get("record_id", "")) if 0 <= row < len(screening_rows) else ""

        def refresh_screening_detail(index: int = -1, _col: int = 0) -> None:
            if index < 0 or index >= len(screening_rows):
                screening_detail.setPlainText("请选择左侧文献以查看标题、摘要、AI 建议和人工决策区。")
                ai_suggestion.setPlainText("暂无 AI 建议。")
                return
            record = screening_rows[index]
            decision_payload = screening_decisions_by_record.get(str(record.get("record_id", "")), {})
            screening_detail.setPlainText(_screening_record_user_detail(record, decision_payload))
            ai_suggestion.setPlainText(_screening_ai_suggestion_text(project_dir, str(record.get("record_id", ""))))

        def do_save_screening_decision(*, refresh: bool = True) -> bool:
            record_id = selected_screening_record_id()
            if not record_id:
                _show_message("请选择文献")
                return False
            selected_decision = str(screening_decision.currentData() or DECISION_NOT_SCREENED)
            selected_reason = str(screening_reason.currentData() or "")
            if selected_decision == DECISION_EXCLUDE and not selected_reason:
                _show_message("排除必须选择排除原因")
                return False
            result = screening_service.save_decision(
                project_dir,
                record_id=record_id,
                decision=selected_decision,
                actor="reviewer",
                exclusion_reason_code=selected_reason,
                notes=screening_notes.toPlainText(),
            )
            _show_message(result.message)
            if refresh:
                on_refresh()
            return result.success

        def do_quick_screening(decision: str, *, advance: bool = False) -> None:
            screening_decision.setCurrentIndex(max(0, screening_decision.findData(decision)))
            if not advance:
                do_save_screening_decision()
                return
            if not do_save_screening_decision(refresh=False):
                return
            next_row = _next_unscreened_screening_row(screening_rows, screening_decisions_by_record, after_row=selected_screening_row())
            on_refresh()
            if next_row < 0:
                return

        group_list.currentRowChanged.connect(refresh_group_detail)
        record_selector.currentIndexChanged.connect(update_preview)
        screening_table.cellClicked.connect(refresh_screening_detail)
        build_queue.clicked.connect(do_build_queue)
        save_decision.clicked.connect(do_save_decision)
        generate_deduped.clicked.connect(do_generate_deduped)
        build_screening_queue.clicked.connect(do_build_screening_queue)
        export_screening_manifest.clicked.connect(do_export_screening_manifest)
        save_screening_decision.clicked.connect(do_save_screening_decision)
        include_button.clicked.connect(lambda: do_quick_screening(DECISION_INCLUDE))
        exclude_button.clicked.connect(lambda: do_quick_screening(DECISION_EXCLUDE))
        uncertain_button.clicked.connect(lambda: do_quick_screening(DECISION_UNCERTAIN))
        fulltext_button.clicked.connect(lambda: do_quick_screening(DECISION_NEED_FULL_TEXT))
        next_unscreened_button.clicked.connect(lambda: do_quick_screening(str(screening_decision.currentData() or DECISION_NOT_SCREENED), advance=True))
        next_button.clicked.connect(on_next)
        group_list.setCurrentRow(0 if groups else -1)
        refresh_group_detail(group_list.currentRow())
        populate_screening_table()
        refresh_screening_detail()
        return frame


    def _exclusion_criteria_page(project_dir: Path, *, on_refresh: Callable[[], None], on_next: Callable[[], None]) -> QFrame:
        service = ExclusionCriteriaLibraryService()
        reasons = list(service.list_reasons(project_dir, enabled_only=False))
        enabled_codes = {reason.code for reason in reasons if reason.enabled} or {reason.code for reason in service.list_reasons(project_dir)}
        frame = QFrame()
        frame.setObjectName("metaExclusionCriteriaPage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(_page_header("排除标准", "项目级排除理由库；只作为人工筛选选项。", "人工配置"))
        layout.addWidget(
            _info_card(
                "当前状态",
                [
                    f"排除理由：{len(reasons)}",
                    f"已启用：{len(enabled_codes)}",
                    "不会自动筛选，不推进 PRISMA。",
                ],
                object_name="metaExclusionSummary",
            )
        )
        reason_list = QListWidget()
        reason_list.setObjectName("metaExclusionReasonList")
        reason_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for reason in reasons:
            item = QListWidgetItem(f"{reason.chinese_label} / {reason.english_label}\n{reason.code} · {','.join(reason.applies_to_stage)}")
            item.setData(Qt.ItemDataRole.UserRole, reason.code)
            reason_list.addItem(item)
            item.setSelected(reason.code in enabled_codes)
        layout.addWidget(reason_list)
        custom_card = _card("新增自定义理由")
        custom_layout = custom_card.layout()
        custom_cn = QLineEdit()
        custom_cn.setPlaceholderText("中文名称")
        custom_en = QLineEdit()
        custom_en.setPlaceholderText("English label")
        custom_prisma = QLineEdit()
        custom_prisma.setPlaceholderText("PRISMA reason mapping")
        custom_layout.addWidget(custom_cn)
        custom_layout.addWidget(custom_en)
        custom_layout.addWidget(custom_prisma)
        layout.addWidget(custom_card)
        button_row = QHBoxLayout()
        save_draft = QPushButton("保存排除标准草稿")
        confirm = QPushButton("确认排除标准")
        add_custom = QPushButton("新增理由")
        next_button = QPushButton("下一步：标题摘要筛选")
        for button in (save_draft, confirm, add_custom, next_button):
            button.setObjectName("metaSecondaryButton")
            button_row.addWidget(button)
        save_draft.setObjectName("metaPrimaryButton")
        button_row.addStretch(1)
        layout.addLayout(button_row)
        layout.addWidget(_developer_details(f"library_path={service.library_path(project_dir)}\nprisma_map={service.prisma_reason_map_path(project_dir)}"))
        layout.addStretch(1)

        def selected_codes() -> tuple[str, ...]:
            return tuple(str(item.data(Qt.ItemDataRole.UserRole)) for item in reason_list.selectedItems())

        def save(confirm_library: bool) -> None:
            service.save_library(project_dir, selected_reason_codes=selected_codes(), actor="reviewer", confirm=confirm_library)
            on_refresh()

        def do_add_custom() -> None:
            if not custom_cn.text().strip() or not custom_en.text().strip():
                _show_message("请填写自定义理由名称")
                return
            service.add_custom_reason(
                project_dir,
                english_label=custom_en.text().strip(),
                chinese_label=custom_cn.text().strip(),
                prisma_reason=custom_prisma.text().strip() or custom_en.text().strip(),
                actor="reviewer",
            )
            on_refresh()

        save_draft.clicked.connect(lambda: save(False))
        confirm.clicked.connect(lambda: save(True))
        add_custom.clicked.connect(do_add_custom)
        next_button.clicked.connect(on_next)
        return frame


    def _title_abstract_screening_page(project_dir: Path, *, on_refresh: Callable[[], None], on_next: Callable[[], None]) -> QFrame:
        service = TitleAbstractScreeningV2Service()
        exclusion = ExclusionCriteriaLibraryService()
        queue = service.load_queue(project_dir)
        records = _items_from_payload(queue, "queue_records")
        decisions = _items_from_payload(_load_json_object(service.decisions_path(project_dir)), "screening_records")
        reasons = list(exclusion.list_reasons(project_dir, stage=TITLE_ABSTRACT_STAGE, enabled_only=True))
        frame = QFrame()
        frame.setObjectName("metaTitleAbstractScreeningPage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(_page_header("标题摘要筛选", "从去重结果进入逐篇人工筛选；AI 只能作为 suggestion。", "人工决定"))
        layout.addWidget(_info_card("筛选摘要", [f"队列文献：{len(records)}", f"人工决定：{len(decisions)}", "PRISMA screened/excluded 只来自用户决定。"], object_name="metaScreeningSummary"))
        actions = QHBoxLayout()
        build_queue = QPushButton("生成筛选队列")
        save_decision = QPushButton("保存人工决定")
        export_decisions_csv = QPushButton("导出筛选决定 CSV")
        next_button = QPushButton("下一步：全文管理")
        for button in (build_queue, save_decision, export_decisions_csv, next_button):
            button.setObjectName("metaPrimaryButton" if button is build_queue else "metaSecondaryButton")
            actions.addWidget(button)
        actions.addStretch(1)
        layout.addLayout(actions)
        content = QHBoxLayout()
        record_list = QListWidget()
        record_list.setObjectName("metaScreeningRecordList")
        for record in records:
            item = QListWidgetItem(f"{record.get('title') or 'Untitled'}\n{record.get('year', '')} · PMID {record.get('pmid', '-') or '-'}")
            item.setData(Qt.ItemDataRole.UserRole, str(record.get("record_id", "")))
            record_list.addItem(item)
        content.addWidget(record_list, 1)
        panel = _card("当前文献")
        panel_layout = panel.layout()
        detail = QTextEdit()
        detail.setObjectName("metaScreeningRecordDetail")
        detail.setReadOnly(True)
        decision = QComboBox()
        decision.setObjectName("metaTitleAbstractScreeningDecisionSelector")
        for label, value in (("纳入", "include"), ("排除", "exclude"), ("不确定", "uncertain"), ("需复核", "needs_review")):
            decision.addItem(label, value)
        reason = QComboBox()
        reason.setObjectName("metaTitleAbstractScreeningReasonSelector")
        reason.addItem("选择排除理由", "")
        for item in reasons:
            reason.addItem(f"{item.chinese_label} / {item.english_label}", item.code)
        notes = QPlainTextEdit()
        notes.setPlaceholderText("筛选备注")
        notes.setMaximumHeight(80)
        panel_layout.addWidget(detail)
        panel_layout.addWidget(decision)
        panel_layout.addWidget(reason)
        panel_layout.addWidget(notes)
        content.addWidget(panel, 2)
        layout.addLayout(content)
        layout.addWidget(_developer_details(f"queue={service.queue_path(project_dir)}\ndecisions={service.decisions_path(project_dir)}"))
        layout.addStretch(1)

        def update_detail(index: int = 0) -> None:
            if 0 <= index < len(records):
                record = records[index]
                detail.setPlainText("\n".join([f"题名：{record.get('title', '')}", f"摘要：{record.get('abstract', '')}", f"来源：{record.get('source_type', '')}"]))
            else:
                detail.setPlainText("暂无待筛选文献。")

        def do_build_queue() -> None:
            result = service.build_queue(project_dir, project_id=project_dir.name)
            _show_message(result.message)
            on_refresh()

        def do_save_decision() -> None:
            item = record_list.currentItem()
            if item is None:
                _show_message("请选择文献")
                return
            record_id = str(item.data(Qt.ItemDataRole.UserRole))
            selected_decision = str(decision.currentData() or "")
            selected_reason = str(reason.currentData() or "")
            if selected_decision == "exclude" and not selected_reason:
                _show_message("排除必须选择排除理由")
                return
            result = service.save_decision(
                project_dir,
                record_id=record_id,
                decision=selected_decision,
                actor="reviewer",
                exclusion_reason_code=selected_reason,
                notes=notes.toPlainText(),
            )
            _show_message(result.message)
            on_refresh()

        def do_export_decisions_csv() -> None:
            path = _write_title_abstract_screening_decisions_csv(project_dir)
            _show_message(f"已导出筛选决定 CSV：{path.name}")
            on_refresh()

        record_list.currentRowChanged.connect(update_detail)
        build_queue.clicked.connect(do_build_queue)
        save_decision.clicked.connect(do_save_decision)
        export_decisions_csv.clicked.connect(do_export_decisions_csv)
        next_button.clicked.connect(on_next)
        record_list.setCurrentRow(0 if records else -1)
        update_detail(record_list.currentRow())
        return frame


    def _fulltext_management_page(project_dir: Path, *, on_refresh: Callable[[], None], on_next: Callable[[], None]) -> QFrame:
        management = FullTextManagementService()
        eligibility = FullTextEligibilityService()
        parser = FullTextParsingService(fulltext_management=management)
        records = list(management.list_records(project_dir))
        candidates = list(eligibility.build_candidates_from_screening(project_dir))
        decisions = list(eligibility.load_eligibility_decisions(project_dir))
        candidates_by_id = {candidate.record_id: candidate for candidate in candidates}
        summary = management.summary_counts(project_dir)
        frame = QFrame()
        frame.setObjectName("metaFulltextManagementPage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(_page_header("全文管理", "全文筛选、全文状态、上传全文和用户确认。", "Developer Preview / testing"))
        layout.addWidget(
            _info_card(
                "全文状态",
                [
                    f"当前全文候选：{len(candidates)}",
                    f"全文管理记录：{len(records)}",
                    f"全文筛选决定：{len(decisions)}",
                    f"需要全文：{summary['full_text_needed']}",
                    f"已上传全文：{summary['full_text_uploaded']}",
                    f"全文待检查：{summary['full_text_pending_review']}",
                    f"全文已确认：{summary['full_text_confirmed']}",
                    f"全文不可获取：{summary['full_text_unavailable']}",
                    f"全文已排除：{summary['full_text_excluded']}",
                    f"可进入提取：{summary['ready_for_extraction']}",
                    "全文解析或模型提示只作为 suggested，不会自动成为确认提取证据。",
                ],
                object_name="metaFulltextSummary",
            )
        )
        buttons = QHBoxLayout()
        build_registry = QPushButton("建立全文队列")
        attach_pdf = QPushButton("上传全文")
        ocr_pdf = QPushButton("OCR 识别 PDF")
        mark_unavailable = QPushButton("标记无法获取")
        confirm_fulltext = QPushButton("全文确认")
        save_status = QPushButton("保存全文状态")
        save_eligibility = QPushButton("保存全文筛选")
        copy_retrieval_links = QPushButton("复制获取链接")
        export_retrieval_csv = QPushButton("导出全文获取 CSV")
        export_retrieval_manifest = QPushButton("导出全文获取清单")
        export_retrieval_package = QPushButton("导出全文获取包")
        next_button = QPushButton("下一步：数据提取")
        for button in (build_registry, attach_pdf, ocr_pdf, mark_unavailable, confirm_fulltext, save_status, save_eligibility, copy_retrieval_links, export_retrieval_csv, export_retrieval_manifest, export_retrieval_package, next_button):
            button.setObjectName("metaSecondaryButton")
            buttons.addWidget(button)
        build_registry.setObjectName("metaPrimaryButton")
        buttons.addStretch(1)
        layout.addLayout(buttons)
        record_table = QTableWidget()
        record_table.setObjectName("metaFulltextRecordTable")
        record_table.setColumnCount(7)
        record_table.setHorizontalHeaderLabels(["标题", "第一作者", "年份", "期刊", "初筛状态", "全文状态", "PDF 文件"])
        record_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        record_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        record_table.setAlternatingRowColors(True)
        source_records = records or candidates
        layout.addWidget(record_table)
        form = _card("人工全文状态")
        form_layout = form.layout()
        fulltext_detail = QTextEdit()
        fulltext_detail.setObjectName("metaFulltextRecordDetail")
        fulltext_detail.setReadOnly(True)
        fulltext_detail.setPlainText("请选择一篇文献后再上传 PDF 或修改全文状态。")
        fulltext_status = QComboBox()
        fulltext_status.setObjectName("metaFulltextStatusSelector")
        for status in FULLTEXT_MANAGEMENT_STATUSES:
            fulltext_status.addItem(FULLTEXT_STATUS_LABELS_ZH.get(status, status), status)
        eligibility_status = QComboBox()
        eligibility_status.setObjectName("metaFulltextEligibilitySelector")
        for status in ("available_online", "local_pdf_linked", "local_pdf_copied", "missing_full_text", "manual_review_required", "excluded_after_full_text_review", "included_for_extraction"):
            eligibility_status.addItem(status, status)
        fulltext_reason = QComboBox()
        fulltext_reason.setObjectName("metaFulltextReasonSelector")
        for reason in FULLTEXT_EXCLUSION_REASONS_M4C:
            fulltext_reason.addItem(FULLTEXT_EXCLUSION_REASON_LABELS_ZH.get(reason, reason), reason)
        notes = QLineEdit()
        notes.setPlaceholderText("备注（可选，不作为确认提取证据）")
        form_layout.addWidget(QLabel("当前文献"))
        form_layout.addWidget(fulltext_detail)
        form_layout.addWidget(QLabel("全文状态"))
        form_layout.addWidget(fulltext_status)
        form_layout.addWidget(QLabel("全文筛选"))
        form_layout.addWidget(eligibility_status)
        form_layout.addWidget(QLabel("排除原因"))
        form_layout.addWidget(fulltext_reason)
        form_layout.addWidget(notes)
        layout.addWidget(form)
        layout.addWidget(_developer_details(f"management={management.registry_path(project_dir)}\nrecords={len(records)}\ncandidates={len(candidates)}"))
        layout.addStretch(1)

        fulltext_rows = list(source_records)

        def populate_fulltext_table() -> None:
            record_table.setRowCount(len(fulltext_rows))
            for row, record in enumerate(fulltext_rows):
                record_id = getattr(record, "record_id", "")
                candidate = candidates_by_id.get(record_id)
                values = [
                    getattr(record, "title", "") or "未命名文献",
                    _first_author({"first_author": getattr(record, "first_author", ""), "authors": getattr(record, "authors", "") or getattr(candidate, "authors", "")}) or "-",
                    str(getattr(record, "year", "") or getattr(candidate, "year", "") or "-"),
                    getattr(record, "journal", "") or getattr(candidate, "journal", "") or "期刊未记录",
                    _screening_decision_label(getattr(record, "source_screening_decision", "") or getattr(candidate, "screening_decision", "") or "未记录"),
                    FULLTEXT_STATUS_LABELS_ZH.get(getattr(record, "fulltext_status", getattr(record, "eligibility_status", "")), getattr(record, "fulltext_status", getattr(record, "eligibility_status", "")) or "未记录"),
                    management.safe_file_label(record) if hasattr(record, "pdf_path") else "未登记全文文件",
                ]
                for col, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    if col == 0:
                        item.setData(Qt.ItemDataRole.UserRole, record_id)
                    record_table.setItem(row, col, item)

        def selected_record_id() -> str:
            rows = _selected_table_rows(record_table)
            if not rows:
                return ""
            row = rows[0]
            if row < 0 or row >= len(fulltext_rows):
                return ""
            return str(getattr(fulltext_rows[row], "record_id", ""))

        def selected_fulltext_record():
            rows = _selected_table_rows(record_table)
            if not rows:
                return None
            row = rows[0]
            if row < 0 or row >= len(fulltext_rows):
                return None
            return fulltext_rows[row]

        def update_fulltext_detail(row: int = -1, _col: int = 0) -> None:
            if row < 0 or row >= len(fulltext_rows):
                fulltext_detail.setPlainText("请选择一篇文献后再上传 PDF 或修改全文状态。")
                return
            record = fulltext_rows[row]
            candidate = candidates_by_id.get(getattr(record, "record_id", ""))
            fulltext_detail.setPlainText(_fulltext_record_detail_text(record, candidate=candidate, management=management))

        def do_build_registry() -> None:
            result = management.build_registry_from_screening(project_dir, project_id=project_dir.name)
            _show_message(result.message)
            on_refresh()

        def do_attach_pdf() -> None:
            record_id = selected_record_id()
            if not record_id:
                _show_message("请选择文献")
                return
            filename, _ = QFileDialog.getOpenFileName(frame, "选择 PDF", str(project_dir), "PDF (*.pdf);;All files (*)")
            if filename:
                result = management.attach_pdf(project_dir, record_id=record_id, source_file_path=filename, actor="reviewer", notes=notes.text())
                _show_message(result.message)
                on_refresh()

        def do_ocr_pdf() -> None:
            record_id = selected_record_id()
            if not record_id:
                _show_message("请选择文献")
                return
            record = management.get_record(project_dir, record_id)
            if record is None or not record.pdf_path:
                _show_message("请先上传或登记本地 PDF")
                return
            result = parser.parse_record(project_dir, record_id=record_id, use_ocr=True)
            if result.success:
                _show_message(f"OCR 已完成：{Path(result.extracted_text_path).name}；原始 JSON 已写入 fulltext/ocr。")
            else:
                _show_message(f"OCR 未完成：{result.diagnostics.get('error_code', result.parse_status)}")
            on_refresh()

        def do_mark_unavailable() -> None:
            record_id = selected_record_id()
            if not record_id:
                _show_message("请选择文献")
                return
            result = management.mark_unavailable(project_dir, record_id=record_id, reason=str(fulltext_reason.currentData()), actor="reviewer", notes=notes.text())
            _show_message(result.message)
            on_refresh()

        def do_confirm_fulltext() -> None:
            record_id = selected_record_id()
            if not record_id:
                _show_message("请选择文献")
                return
            result = management.update_status(project_dir, record_id=record_id, status=FULLTEXT_STATUS_FULL_TEXT_CONFIRMED, actor="reviewer", notes=notes.text())
            _show_message(result.message)
            on_refresh()

        def do_save_status() -> None:
            record_id = selected_record_id()
            if not record_id:
                _show_message("请选择文献")
                return
            status = str(fulltext_status.currentData())
            if status == FULLTEXT_STATUS_FULL_TEXT_UNAVAILABLE:
                result = management.mark_unavailable(project_dir, record_id=record_id, reason=str(fulltext_reason.currentData()), actor="reviewer", notes=notes.text())
            else:
                result = management.update_status(project_dir, record_id=record_id, status=status, actor="reviewer", notes=notes.text())
            _show_message(result.message)
            on_refresh()

        def do_save_eligibility() -> None:
            record_id = selected_record_id()
            if not record_id:
                _show_message("请选择文献")
                return
            result = eligibility.save_eligibility_decision(
                project_dir,
                record_id=record_id,
                eligibility_status=str(eligibility_status.currentData()),
                reviewer_id="reviewer",
                exclusion_reason=str(fulltext_reason.currentData()),
            )
            _show_message(result.message)
            on_refresh()

        def do_copy_retrieval_links() -> None:
            record = selected_fulltext_record()
            if record is None:
                _show_message("请选择文献")
                return
            candidate = candidates_by_id.get(str(getattr(record, "record_id", "")))
            link_text = _fulltext_retrieval_links_text(record, candidate=candidate)
            if not link_text:
                _show_message("当前文献缺少 DOI / PMID / PMCID，暂无可复制获取链接。")
                return
            _copy_text_to_clipboard(link_text)
            _show_message("全文获取链接已复制。")

        def do_export_retrieval_csv() -> None:
            path = _write_fulltext_retrieval_csv(project_dir)
            _show_message(f"已导出全文获取 CSV：{path.name}")
            on_refresh()

        def do_export_retrieval_manifest() -> None:
            path = _write_fulltext_retrieval_manifest(project_dir)
            _show_message(f"已导出全文获取清单：{path.name}")
            on_refresh()

        def do_export_retrieval_package() -> None:
            path = _write_fulltext_retrieval_package(project_dir)
            _show_message(f"已导出全文获取包：{path.name}")
            on_refresh()

        build_registry.clicked.connect(do_build_registry)
        attach_pdf.clicked.connect(do_attach_pdf)
        ocr_pdf.clicked.connect(do_ocr_pdf)
        mark_unavailable.clicked.connect(do_mark_unavailable)
        confirm_fulltext.clicked.connect(do_confirm_fulltext)
        save_status.clicked.connect(do_save_status)
        save_eligibility.clicked.connect(do_save_eligibility)
        copy_retrieval_links.clicked.connect(do_copy_retrieval_links)
        export_retrieval_csv.clicked.connect(do_export_retrieval_csv)
        export_retrieval_manifest.clicked.connect(do_export_retrieval_manifest)
        export_retrieval_package.clicked.connect(do_export_retrieval_package)
        next_button.clicked.connect(on_next)
        record_table.cellClicked.connect(update_fulltext_detail)
        populate_fulltext_table()
        return frame


    def _manual_extraction_page(project_dir: Path, *, on_refresh: Callable[[], None], on_next: Callable[[], None]) -> QFrame:
        service = ManualExtractionEffectRowService()
        records = service.literature_records_for_extraction(project_dir)
        units = service.load_study_units(project_dir)
        rows = service.load_effect_rows(project_dir)
        structured_rows = service.load_structured_extraction_table(project_dir)
        validation = _load_json_object(service.validation_report_path(project_dir))
        frame = QFrame()
        frame.setObjectName("metaManualExtractionPage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(_page_header("数据提取", "结构化录入研究基本信息、PICO/PECO、效应量数据和统计字段。", "人工确认"))
        layout.addWidget(
            _info_card(
                "提取状态",
                [
                    f"可提取文献：{len(records)}",
                    f"study unit：{len(units)}",
                    f"effect row：{len(rows)}",
                    f"结构化提取行：{len(structured_rows)}",
                    f"缺失关键字段：{validation.get('missing_required_fields_count', 0)}",
                    "用户确认不会运行正式统计分析。",
                ],
                object_name="metaExtractionSummary",
            )
        )
        action_row = QHBoxLayout()
        create_unit = QPushButton("新建 study unit")
        create_row = QPushButton("新建提取行")
        save_structured = QPushButton("保存结构化草稿")
        complete_row = QPushButton("完成本行提取")
        confirm_structured = QPushButton("用户确认")
        mark_missing = QPushButton("标记缺失数据")
        export_template = QPushButton("导出空模板 CSV")
        export_current = QPushButton("导出当前 CSV")
        import_csv = QPushButton("导入 CSV 草稿")
        export_extraction_manifest = QPushButton("导出提取整理清单")
        export_extraction_package = QPushButton("导出提取整理包")
        next_button = QPushButton("下一步：AI 辅助提取")
        for button in (create_unit, create_row, save_structured, complete_row, confirm_structured, mark_missing, export_template, export_current, import_csv, export_extraction_manifest, export_extraction_package, next_button):
            button.setObjectName("metaSecondaryButton")
            action_row.addWidget(button)
        create_unit.setObjectName("metaPrimaryButton")
        action_row.addStretch(1)
        layout.addLayout(action_row)
        lists = QHBoxLayout()
        record_list = QListWidget()
        record_list.setObjectName("metaExtractionRecordList")
        for record in records:
            item = QListWidgetItem(
                "\n".join(
                    [
                        str(record.get("title") or "未命名文献"),
                        " · ".join(part for part in (str(record.get("first_author") or ""), str(record.get("year") or ""), _extraction_source_label(str(record.get("extraction_source") or ""))) if part),
                    ]
                )
            )
            item.setData(Qt.ItemDataRole.UserRole, str(record.get("record_id", "")))
            record_list.addItem(item)
        unit_list = QListWidget()
        unit_list.setObjectName("metaStudyUnitList")
        for unit in units:
            item = QListWidgetItem(
                "\n".join(
                    [
                        str(unit.get("study_unit_label") or "未命名 study unit"),
                        " · ".join(part for part in (str(unit.get("study_design") or ""), str(unit.get("country_or_region") or "")) if part),
                    ]
                )
            )
            item.setData(Qt.ItemDataRole.UserRole, str(unit.get("study_unit_id", "")))
            unit_list.addItem(item)
        row_list = QListWidget()
        row_list.setObjectName("metaEffectRowList")
        for row in rows:
            structured = dict(row.get("m5_structured_fields", {}) if isinstance(row.get("m5_structured_fields"), dict) else {})
            item = QListWidgetItem(
                "\n".join(
                    [
                        str(structured.get("outcome") or row.get("outcome_name") or "待填写结局"),
                        f"{structured.get('effect_measure_type') or row.get('data_input_mode', '')} · {_evidence_state_label(str(row.get('evidence_state') or row.get('extraction_status') or 'draft'))}",
                    ]
                )
            )
            item.setData(Qt.ItemDataRole.UserRole, str(row.get("effect_row_id", "")))
            row_list.addItem(item)
        lists.addWidget(record_list)
        lists.addWidget(unit_list)
        lists.addWidget(row_list)
        layout.addLayout(lists)

        structured_card = _card("结构化提取表")
        structured_layout = structured_card.layout()
        structured_layout.addWidget(QLabel("研究基本信息"))
        study_id_input = QLineEdit()
        title_input = QLineEdit()
        first_author_input = QLineEdit()
        year_input = QLineEdit()
        country_input = QLineEdit()
        design_input = QLineEdit()
        population_input = QLineEdit()
        sample_total_input = QLineEdit()
        for field_name, widget in (
            ("study_id", study_id_input),
            ("title", title_input),
            ("first_author", first_author_input),
            ("year", year_input),
            ("country_or_region", country_input),
            ("study_design", design_input),
            ("population", population_input),
            ("sample_size_total", sample_total_input),
        ):
            widget.setObjectName(f"metaExtraction_{field_name}")
            widget.setPlaceholderText(STRUCTURED_EXTRACTION_FIELD_LABELS_ZH[field_name])
            structured_layout.addWidget(widget)
        structured_layout.addWidget(QLabel("PICO/PECO"))
        intervention_input = QLineEdit()
        comparator_input = QLineEdit()
        outcome_input = QLineEdit()
        follow_up_input = QLineEdit()
        for field_name, widget in (
            ("intervention_or_exposure", intervention_input),
            ("comparator", comparator_input),
            ("outcome", outcome_input),
            ("follow_up_duration", follow_up_input),
        ):
            widget.setObjectName(f"metaExtraction_{field_name}")
            widget.setPlaceholderText(STRUCTURED_EXTRACTION_FIELD_LABELS_ZH[field_name])
            structured_layout.addWidget(widget)
        structured_layout.addWidget(QLabel("效应量数据"))
        effect_type = QComboBox()
        effect_type.setObjectName("metaExtractionEffectMeasureSelector")
        for measure in STRUCTURED_EXTRACTION_EFFECT_MEASURES:
            effect_type.addItem(measure, measure)
        structured_layout.addWidget(effect_type)
        effect_estimate_input = QLineEdit()
        ci_lower_input = QLineEdit()
        ci_upper_input = QLineEdit()
        for field_name, widget in (
            ("effect_estimate", effect_estimate_input),
            ("ci_lower", ci_lower_input),
            ("ci_upper", ci_upper_input),
        ):
            widget.setObjectName(f"metaExtraction_{field_name}")
            widget.setPlaceholderText(STRUCTURED_EXTRACTION_FIELD_LABELS_ZH[field_name])
            structured_layout.addWidget(widget)
        structured_layout.addWidget(QLabel("统计字段"))
        events_case_input = QLineEdit()
        total_case_input = QLineEdit()
        events_control_input = QLineEdit()
        total_control_input = QLineEdit()
        notes_input = QLineEdit()
        for field_name, widget in (
            ("events_case", events_case_input),
            ("total_case", total_case_input),
            ("events_control", events_control_input),
            ("total_control", total_control_input),
            ("notes", notes_input),
        ):
            widget.setObjectName(f"metaExtraction_{field_name}")
            widget.setPlaceholderText(STRUCTURED_EXTRACTION_FIELD_LABELS_ZH[field_name])
            structured_layout.addWidget(widget)
        evidence_state = QComboBox()
        evidence_state.setObjectName("metaExtractionEvidenceStateSelector")
        for state in STRUCTURED_EXTRACTION_EVIDENCE_STATES:
            evidence_state.addItem(_evidence_state_label(state), state)
        structured_layout.addWidget(QLabel("提取状态"))
        structured_layout.addWidget(evidence_state)
        layout.addWidget(structured_card)
        layout.addWidget(
            _info_card(
                "下一步页面",
                [
                    "质量评价已作为独立侧栏页面接入。",
                    "完成结构化提取和 AI 建议审核后，点击“下一步：质量评价”进入人工质量评分。",
                ],
                object_name="metaNextPageHint",
            )
        )
        layout.addWidget(_developer_details(f"manifest={service.manifest_path(project_dir)}\nvalidation={service.validation_report_path(project_dir)}"))
        layout.addStretch(1)

        def selected_record_id() -> str:
            item = record_list.currentItem()
            return str(item.data(Qt.ItemDataRole.UserRole)) if item is not None else (str(records[0].get("record_id", "")) if records else "")

        def selected_unit_id() -> str:
            item = unit_list.currentItem()
            return str(item.data(Qt.ItemDataRole.UserRole)) if item is not None else (str(units[0].get("study_unit_id", "")) if units else "")

        def selected_row_id() -> str:
            item = row_list.currentItem()
            return str(item.data(Qt.ItemDataRole.UserRole)) if item is not None else ""

        def do_create_unit() -> None:
            record_id = selected_record_id()
            if not record_id:
                _show_message("请先在文献库中导入文献")
                return
            result = service.create_study_unit(project_dir, record_id=record_id, study_unit_label=f"Study unit {len(units) + 1}", actor="reviewer")
            _show_message(result.message)
            on_refresh()

        def do_create_row() -> None:
            unit_id = selected_unit_id()
            if not unit_id:
                _show_message("请先新建 study unit")
                return
            result = service.create_effect_row(
                project_dir,
                study_unit_id=unit_id,
                actor="reviewer",
                data_input_mode="manual_note_only",
                outcome_name="待填写结局",
                evidence_note="UI draft; requires reviewer completion.",
            )
            _show_message(result.message)
            on_refresh()

        def structured_fields() -> dict[str, object]:
            return {
                "study_id": study_id_input.text(),
                "title": title_input.text(),
                "first_author": first_author_input.text(),
                "year": year_input.text(),
                "country_or_region": country_input.text(),
                "study_design": design_input.text(),
                "population": population_input.text(),
                "sample_size_total": sample_total_input.text(),
                "intervention_or_exposure": intervention_input.text(),
                "comparator": comparator_input.text(),
                "outcome": outcome_input.text(),
                "follow_up_duration": follow_up_input.text(),
                "effect_measure_type": str(effect_type.currentData()),
                "effect_estimate": effect_estimate_input.text(),
                "ci_lower": ci_lower_input.text(),
                "ci_upper": ci_upper_input.text(),
                "events_case": events_case_input.text(),
                "total_case": total_case_input.text(),
                "events_control": events_control_input.text(),
                "total_control": total_control_input.text(),
                "notes": notes_input.text(),
            }

        def do_save_structured() -> None:
            record_id = selected_record_id()
            result = service.create_structured_extraction_row(
                project_dir,
                fields=structured_fields(),
                actor="reviewer",
                evidence_state=str(evidence_state.currentData()),
                record_id=record_id,
            )
            _show_message(result.message)
            on_refresh()

        def do_complete_row() -> None:
            row_id = selected_row_id()
            if not row_id:
                _show_message("请选择 effect row")
                return
            result = service.complete_effect_row(project_dir, effect_row_id=row_id, actor="reviewer")
            _show_message(result.message)
            on_refresh()

        def do_confirm_structured() -> None:
            row_id = selected_row_id()
            if not row_id:
                _show_message("请选择提取行")
                return
            result = service.confirm_structured_extraction_row(project_dir, effect_row_id=row_id, actor="reviewer")
            _show_message(result.message)
            on_refresh()

        def do_mark_missing() -> None:
            row_id = selected_row_id()
            if not row_id:
                _show_message("请选择 effect row")
                return
            result = service.mark_missing_data(project_dir, effect_row_id=row_id, actor="reviewer", missing_reason="用户标记缺失数据")
            _show_message(result.message)
            on_refresh()

        def do_import_csv() -> None:
            filename, _ = QFileDialog.getOpenFileName(frame, "选择 CSV", str(project_dir), "CSV (*.csv);;All files (*)")
            if filename:
                result = service.import_csv_as_draft(project_dir, csv_path=Path(filename), actor="reviewer")
                _show_message(result.message)
                on_refresh()

        def do_export_extraction_manifest() -> None:
            path = _write_extraction_organization_manifest(project_dir)
            _show_message(f"已导出提取整理清单：{path.name}")
            on_refresh()

        def do_export_extraction_package() -> None:
            path = _write_extraction_organization_package(project_dir)
            _show_message(f"已导出提取整理包：{path.name}")
            on_refresh()

        create_unit.clicked.connect(do_create_unit)
        create_row.clicked.connect(do_create_row)
        save_structured.clicked.connect(do_save_structured)
        complete_row.clicked.connect(do_complete_row)
        confirm_structured.clicked.connect(do_confirm_structured)
        mark_missing.clicked.connect(do_mark_missing)
        export_template.clicked.connect(lambda: _show_message(service.export_empty_template_csv(project_dir, actor="reviewer").message))
        export_current.clicked.connect(lambda: _show_message(service.export_current_csv(project_dir, actor="reviewer").message))
        import_csv.clicked.connect(do_import_csv)
        export_extraction_manifest.clicked.connect(do_export_extraction_manifest)
        export_extraction_package.clicked.connect(do_export_extraction_package)
        next_button.clicked.connect(on_next)
        return frame


    def _ai_extraction_page(project_dir: Path, *, on_refresh: Callable[[], None], on_next: Callable[[], None]) -> QFrame:
        service = AIAssistedExtractionQueueService()
        suggestions = service.list_extraction_suggestions(project_dir)
        counts: dict[str, int] = {}
        for suggestion in suggestions:
            counts[suggestion.status] = counts.get(suggestion.status, 0) + 1
        frame = QFrame()
        frame.setObjectName("metaAIExtractionPage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(_page_header("AI 辅助提取", "suggestion 队列；accepted 后也只写人工提取草稿。", "建议待审"))
        layout.addWidget(_info_card("建议队列", [f"总数：{len(suggestions)}", f"状态：{counts}", "不会写 final extraction，不生成 analysis-ready dataset。"], object_name="metaAIExtractionSummary"))
        suggestion_list = QListWidget()
        suggestion_list.setObjectName("metaAIExtractionSuggestionList")
        for suggestion in suggestions:
            item = QListWidgetItem(f"{suggestion.status} · {suggestion.suggestion_id}\nconfidence={suggestion.confidence}")
            item.setData(Qt.ItemDataRole.UserRole, suggestion.suggestion_id)
            suggestion_list.addItem(item)
        layout.addWidget(suggestion_list)
        actions = QHBoxLayout()
        accept = QPushButton("接受建议")
        reject = QPushButton("拒绝建议")
        apply_draft = QPushButton("写入人工草稿")
        next_button = QPushButton("下一步：质量评价")
        for button in (accept, reject, apply_draft, next_button):
            button.setObjectName("metaSecondaryButton")
            actions.addWidget(button)
        actions.addStretch(1)
        layout.addLayout(actions)
        layout.addWidget(_developer_details(f"queue={service.queue_path(project_dir)}\napplication={service.application_path(project_dir)}"))
        layout.addStretch(1)

        def selected_suggestion_id() -> str:
            item = suggestion_list.currentItem()
            return str(item.data(Qt.ItemDataRole.UserRole)) if item is not None else ""

        def do_accept() -> None:
            suggestion_id = selected_suggestion_id()
            if suggestion_id:
                service.accept_suggestion(project_dir, suggestion_id, actor="reviewer")
                on_refresh()

        def do_reject() -> None:
            suggestion_id = selected_suggestion_id()
            if suggestion_id:
                service.reject_suggestion(project_dir, suggestion_id, actor="reviewer")
                on_refresh()

        def do_apply() -> None:
            suggestion_id = selected_suggestion_id()
            if not suggestion_id:
                return
            result = service.apply_accepted_suggestion_as_draft(project_dir, suggestion_id=suggestion_id, actor="reviewer")
            _show_message(result.message)
            on_refresh()

        accept.clicked.connect(do_accept)
        reject.clicked.connect(do_reject)
        apply_draft.clicked.connect(do_apply)
        next_button.clicked.connect(on_next)
        return frame


    def _quality_assessment_page(project_dir: Path, *, on_refresh: Callable[[], None], on_next: Callable[[], None]) -> QFrame:
        service = QualityAssessmentService()
        registry = service.tool_registry_v1()
        records = service.load_quality_assessment_records_v1(project_dir)
        study_rows = _quality_study_rows_for_workspace(project_dir)
        summary = service.quality_m6_summary(project_dir, expected_study_ids=[row["study_id"] for row in study_rows])
        frame = QFrame()
        frame.setObjectName("metaQualityAssessmentPage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(_page_header("质量评价", "NOS 优先的人工偏倚风险评价；其他工具保持 staged/testing。", "人工确认"))
        layout.addWidget(
            _info_card(
                "质量评价摘要",
                [
                    f"工具数：{registry.get('tool_count', 0)}",
                    f"待评价研究：{summary['studies_pending_quality']}",
                    f"草稿质量评价：{summary['studies_with_draft_quality']}",
                    f"已确认质量评价：{summary['studies_with_confirmed_quality']}",
                    f"低风险/较好：{summary['low_risk_or_good']}",
                    f"不明确：{summary['unclear']}",
                    f"高风险/较差：{summary['high_risk_or_poor']}",
                    "不自动评分，不自动 GRADE，不运行统计。",
                ],
                object_name="metaQualitySummary",
            )
        )
        study_list = QListWidget()
        study_list.setObjectName("metaQualityStudyList")
        if study_rows:
            for row in study_rows:
                item = QListWidgetItem(
                    "\n".join(
                        [
                            str(row.get("title") or row.get("study_id") or "未命名研究"),
                            " · ".join(part for part in (str(row.get("first_author") or ""), str(row.get("year") or ""), str(row.get("study_design") or "")) if part),
                        ]
                    )
                )
                item.setData(Qt.ItemDataRole.UserRole, dict(row))
                study_list.addItem(item)
        else:
            study_list.addItem(QListWidgetItem("暂无可评价研究；请先完成数据提取确认。"))
        layout.addWidget(study_list)
        layout.addWidget(QLabel("评价工具"))
        tool_selector = QComboBox()
        tool_selector.setObjectName("metaQualityToolSelector")
        for tool_name in service.list_quality_tools():
            suffix = " · staged/testing" if tool_name != "NOS" else " · NOS"
            tool_selector.addItem(f"{tool_name}{suffix}", tool_name)
        tool_selector.setCurrentText("NOS · NOS")
        layout.addWidget(tool_selector)
        assessment_list = QListWidget()
        assessment_list.setObjectName("metaQualityAssessmentList")
        for record in records:
            item = QListWidgetItem(
                "\n".join(
                    [
                        f"{record.get('tool_name')} · {_quality_state_label(str(record.get('status') or 'draft'))}",
                        f"总体判断：{_quality_rating_label(str(record.get('overall_rating') or record.get('overall_judgement') or ''))}",
                    ]
                )
            )
            item.setData(Qt.ItemDataRole.UserRole, str(record.get("assessment_id", "")))
            assessment_list.addItem(item)
        layout.addWidget(assessment_list)
        form = _card("偏倚风险")
        form_layout = form.layout()
        domain_selectors: dict[str, QComboBox] = {}
        domain_notes: dict[str, QLineEdit] = {}
        for domain in NOS_DOMAINS:
            form_layout.addWidget(QLabel(f"评价维度：{NOS_DOMAIN_LABELS_ZH.get(domain, domain)}"))
            selector = QComboBox()
            selector.setObjectName(f"metaQualityDomain_{domain}")
            for rating in ("not_assessed", "low_risk_or_good", "unclear", "high_risk_or_poor"):
                selector.addItem(QUALITY_RATING_LABELS_ZH.get(rating, rating), rating)
            domain_selectors[domain] = selector
            form_layout.addWidget(selector)
            note = QLineEdit()
            note.setObjectName(f"metaQualityDomainNote_{domain}")
            note.setPlaceholderText("评价理由")
            domain_notes[domain] = note
            form_layout.addWidget(QLabel("评价理由"))
            form_layout.addWidget(note)
        overall = QComboBox()
        overall.setObjectName("metaQualityOverallSelector")
        for rating in ("not_assessed", "low_risk_or_good", "unclear", "high_risk_or_poor"):
            overall.addItem(QUALITY_RATING_LABELS_ZH.get(rating, rating), rating)
        state_selector = QComboBox()
        state_selector.setObjectName("metaQualityStateSelector")
        for state in ("draft", "suggested", "user_accepted", "user_edited", "confirmed", "rejected"):
            state_selector.addItem(QUALITY_M6_STATE_LABELS_ZH.get(state, state), state)
        notes = QPlainTextEdit()
        notes.setObjectName("metaQualityNotes")
        notes.setPlaceholderText("评价理由 / 备注；AI 或规则建议必须由用户确认后才生效")
        notes.setMaximumHeight(90)
        form_layout.addWidget(QLabel("总体判断"))
        form_layout.addWidget(overall)
        form_layout.addWidget(QLabel("已确认"))
        form_layout.addWidget(state_selector)
        form_layout.addWidget(notes)
        layout.addWidget(form)
        actions = QHBoxLayout()
        save_draft = QPushButton("保存评分草稿")
        complete = QPushButton("已确认")
        export_csv = QPushButton("导出 CSV")
        export_json = QPushButton("导出 JSON")
        export_quality_package = QPushButton("导出质量评价包")
        next_button = QPushButton("下一步：分析计划")
        for button in (save_draft, complete, export_csv, export_json, export_quality_package, next_button):
            button.setObjectName("metaSecondaryButton")
            actions.addWidget(button)
        save_draft.setObjectName("metaPrimaryButton")
        actions.addStretch(1)
        layout.addLayout(actions)
        layout.addWidget(_developer_details(f"records={project_dir / 'quality' / 'quality_assessment_records_v1.json'}"))
        layout.addStretch(1)

        def selected_assessment_id() -> str:
            item = assessment_list.currentItem()
            return str(item.data(Qt.ItemDataRole.UserRole)) if item is not None else ""

        def do_save_draft() -> None:
            tool_name = str(tool_selector.currentData() or "")
            if not tool_name:
                _show_message("暂无推荐工具")
                return
            selected = _selected_quality_study()
            state = str(state_selector.currentData() or "draft")
            result = service.create_quality_assessment_draft(
                project_dir,
                study_id=str(selected.get("study_id") or "study-ui-draft"),
                record_id=str(selected.get("record_id") or "record-ui-draft"),
                tool_name=tool_name,
                domains={domain: str(selector.currentData()) for domain, selector in domain_selectors.items()},
                domain_notes={domain: note.text() for domain, note in domain_notes.items()},
                overall_rating=str(overall.currentData()),
                notes=notes.toPlainText(),
                reviewer_id="reviewer",
                actor="reviewer",
                assessment_state=state,
            )
            _show_message(result.message)
            on_refresh()

        def do_complete() -> None:
            assessment_id = selected_assessment_id()
            if not assessment_id:
                _show_message("请选择质量评价记录")
                return
            result = service.confirm_quality_assessment_by_user(project_dir, assessment_id=assessment_id, actor="reviewer")
            _show_message(result.message)
            on_refresh()

        def _selected_quality_study() -> dict[str, object]:
            item = study_list.currentItem()
            data = item.data(Qt.ItemDataRole.UserRole) if item is not None else {}
            return dict(data) if isinstance(data, dict) else {}

        save_draft.clicked.connect(do_save_draft)
        complete.clicked.connect(do_complete)
        export_csv.clicked.connect(lambda: _show_message(f"已导出：{service.export_quality_assessments_v1_csv(project_dir).name}"))
        export_json.clicked.connect(lambda: _show_message(f"已导出：{service.export_quality_assessments_v1_json(project_dir).name}"))
        export_quality_package.clicked.connect(lambda: (_show_message(f"已导出质量评价包：{_write_quality_assessment_package(project_dir).name}"), on_refresh()))
        next_button.clicked.connect(on_next)
        return frame


    def _analysis_plan_page(project_dir: Path, *, on_refresh: Callable[[], None], on_next: Callable[[], None]) -> QFrame:
        service = AnalysisPlanService()
        draft = service.load_draft(project_dir)
        confirmed = service.load_confirmed(project_dir)
        active_plan = confirmed or draft
        readiness = service.analysis_plan_readiness(project_dir)
        warning_labels = dict(active_plan.get("m7_warning_labels_zh", {})) if isinstance(active_plan.get("m7_warning_labels_zh"), dict) else dict(readiness.get("warning_labels_zh", {}))
        frame = QFrame()
        frame.setObjectName("metaAnalysisPlanPage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(_page_header("分析计划", "确认研究类型、效应量、模型、异质性、亚组/敏感性/发表偏倚计划。", "Developer Preview / testing"))
        layout.addWidget(
            _info_card(
                "当前状态",
                [
                    f"计划状态：{_analysis_plan_state_label(str(active_plan.get('plan_state') or active_plan.get('status') or '未生成'))}",
                    f"纳入研究数量：{int(active_plan.get('included_study_count', readiness.get('included_study_count', 0)) or 0)}",
                    "确认分析计划不会运行正式统计分析。",
                    "该计划仅用于测试阶段，不代表正式统计结论。",
                ],
                object_name="metaAnalysisPlanSummary",
            )
        )
        form = _card("分析计划")
        form_layout = form.layout()
        form_layout.addWidget(_kv_label("研究类型", str(active_plan.get("meta_profile") or active_plan.get("meta_type") or "待生成")))
        form_layout.addWidget(_kv_label("纳入研究数量", str(active_plan.get("included_study_count", readiness.get("included_study_count", 0)))))
        research_question = QLineEdit()
        research_question.setObjectName("metaAnalysisPlanResearchQuestionInput")
        research_question.setPlaceholderText("研究问题")
        research_question.setText(str(active_plan.get("research_question", "")))
        form_layout.addWidget(research_question)
        population = QLineEdit()
        population.setObjectName("metaAnalysisPlanPopulationInput")
        population.setPlaceholderText("Population / 研究对象")
        population.setText(str(active_plan.get("population", "")))
        form_layout.addWidget(population)
        intervention = QLineEdit()
        intervention.setObjectName("metaAnalysisPlanInterventionInput")
        intervention.setPlaceholderText("Intervention / Exposure / 干预或暴露")
        intervention.setText(str(active_plan.get("intervention_or_exposure", "")))
        form_layout.addWidget(intervention)
        comparator = QLineEdit()
        comparator.setObjectName("metaAnalysisPlanComparatorInput")
        comparator.setPlaceholderText("Comparator / 对照")
        comparator.setText(str(active_plan.get("comparator", "")))
        form_layout.addWidget(comparator)
        outcome = QLineEdit()
        outcome.setObjectName("metaAnalysisPlanOutcomeInput")
        outcome.setPlaceholderText("Outcome / 结局")
        outcome.setText(str(active_plan.get("outcome", "")))
        form_layout.addWidget(outcome)
        effect_type = QComboBox()
        effect_type.setObjectName("metaAnalysisPlanEffectMeasureSelector")
        for item in ANALYSIS_PLAN_EFFECT_MEASURE_TYPES:
            effect_type.addItem(item, item)
        selected_effect = str(active_plan.get("effect_measure_type") or active_plan.get("effect_measure") or "OR")
        effect_index = effect_type.findData(selected_effect)
        if effect_index >= 0:
            effect_type.setCurrentIndex(effect_index)
        form_layout.addWidget(_kv_label("效应量类型", "OR / RR / HR / MD / SMD / proportion / correlation / diagnostic_accuracy / other"))
        form_layout.addWidget(effect_type)
        model_preference = QComboBox()
        model_preference.setObjectName("metaAnalysisPlanModelPreferenceSelector")
        model_labels = {
            "fixed_effect": "固定效应",
            "random_effect": "随机效应",
            "both": "固定效应 + 随机效应",
            "undecided": "暂不决定",
        }
        for item in ANALYSIS_PLAN_MODEL_PREFERENCES:
            model_preference.addItem(model_labels[item], item)
        selected_model = str(active_plan.get("model_preference") or "random_effect")
        model_index = model_preference.findData(selected_model)
        if model_index >= 0:
            model_preference.setCurrentIndex(model_index)
        form_layout.addWidget(_kv_label("固定效应", "可在模型偏好中选择"))
        form_layout.addWidget(_kv_label("随机效应", "可在模型偏好中选择"))
        form_layout.addWidget(model_preference)
        form_layout.addWidget(_kv_label("异质性", "I2 / tau2 / Q"))
        subgroup_plan = QPlainTextEdit()
        subgroup_plan.setObjectName("metaAnalysisPlanSubgroupInput")
        subgroup_plan.setPlaceholderText("亚组分析")
        subgroup_plan.setPlainText(_plan_text(active_plan.get("subgroup_plan", "")))
        form_layout.addWidget(_kv_label("亚组分析", "按研究问题人工填写或确认"))
        form_layout.addWidget(subgroup_plan)
        sensitivity_plan = QPlainTextEdit()
        sensitivity_plan.setObjectName("metaAnalysisPlanSensitivityInput")
        sensitivity_plan.setPlaceholderText("敏感性分析")
        sensitivity_plan.setPlainText(_plan_text(active_plan.get("sensitivity_plan", "")))
        form_layout.addWidget(_kv_label("敏感性分析", "按研究问题人工填写或确认"))
        form_layout.addWidget(sensitivity_plan)
        publication_bias_plan = QPlainTextEdit()
        publication_bias_plan.setObjectName("metaAnalysisPlanPublicationBiasInput")
        publication_bias_plan.setPlaceholderText("发表偏倚")
        publication_bias_plan.setPlainText(_plan_text(active_plan.get("publication_bias_plan", "")))
        form_layout.addWidget(_kv_label("发表偏倚", "研究数量充足时再考虑；当前只记录计划"))
        form_layout.addWidget(publication_bias_plan)
        layout.addWidget(form)
        layout.addWidget(
            _info_card(
                "准备度提示",
                list(warning_labels.values())
                or [ANALYSIS_PLAN_READINESS_WARNING_LABELS_ZH["developer_preview_testing_only"]],
                object_name="metaAnalysisPlanWarnings",
            )
        )
        buttons = QHBoxLayout()
        generate = QPushButton("生成分析计划草稿")
        save_draft = QPushButton("保存计划编辑")
        confirm = QPushButton("确认分析计划")
        next_button = QPushButton("下一步：统计分析")
        for button in (generate, save_draft, confirm, next_button):
            button.setObjectName("metaSecondaryButton")
            buttons.addWidget(button)
        generate.setObjectName("metaPrimaryButton")
        buttons.addStretch(1)
        layout.addLayout(buttons)
        layout.addWidget(_m10_m13_statistics_controls(project_dir, on_refresh=on_refresh))
        layout.addWidget(_developer_details(f"draft={service.draft_path(project_dir)}\nconfirmed={service.confirmed_path(project_dir)}\nmanifest={service.manifest_path(project_dir)}"))
        layout.addStretch(1)

        def _ui_updates(plan_state: str = "user_edited") -> dict[str, object]:
            return {
                "research_question": research_question.text().strip(),
                "population": population.text().strip(),
                "intervention_or_exposure": intervention.text().strip(),
                "comparator": comparator.text().strip(),
                "outcome": outcome.text().strip(),
                "effect_measure": str(effect_type.currentData()),
                "effect_measure_type": str(effect_type.currentData()),
                "model_default": str(model_preference.currentData()),
                "model_preference": str(model_preference.currentData()),
                "heterogeneity_metrics": ["I2", "tau2", "Q"],
                "subgroup_plan": {"user_plan": subgroup_plan.toPlainText().strip(), "status": "user_edited"},
                "sensitivity_plan": {"user_plan": sensitivity_plan.toPlainText().strip(), "status": "user_edited"},
                "publication_bias_plan": {"user_plan": publication_bias_plan.toPlainText().strip(), "status": "user_edited"},
                "plan_state": plan_state,
            }

        def do_generate() -> None:
            try:
                result = service.generate_draft(project_dir, actor="reviewer")
                _show_message(result.message)
            except Exception as exc:
                _show_message(str(exc))
            on_refresh()

        def do_save_draft() -> None:
            try:
                if not service.load_draft(project_dir):
                    service.generate_draft(project_dir, actor="reviewer")
                result = service.edit_draft(project_dir, actor="reviewer", updates=_ui_updates())
                _show_message(result.message)
            except Exception as exc:
                _show_message(str(exc))
            on_refresh()

        def do_confirm() -> None:
            try:
                if not service.load_draft(project_dir):
                    service.generate_draft(project_dir, actor="reviewer")
                service.edit_draft(project_dir, actor="reviewer", updates=_ui_updates())
                result = service.confirm_plan(project_dir, actor="reviewer")
                _show_message(result.message)
            except Exception as exc:
                _show_message(str(exc))
            on_refresh()

        generate.clicked.connect(do_generate)
        save_draft.clicked.connect(do_save_draft)
        confirm.clicked.connect(do_confirm)
        next_button.clicked.connect(on_next)
        return frame


    def _m10_m13_statistics_controls(project_dir: Path, *, on_refresh: Callable[[], None]) -> QFrame:
        plan_service = AnalysisPlanService()
        normalization_service = EffectSizeNormalizationService()
        pairwise_service = PairwiseMetaExecutorService(analysis_plan_service=plan_service, normalization_service=normalization_service)
        review_service = StatisticalResultReviewService(pairwise_executor=pairwise_service)
        normalized_effects = normalization_service.normalize_extraction_rows(project_dir)
        normalization_summary = normalization_service.summarize_normalization(normalized_effects)
        latest_result = pairwise_service.load_latest_result(project_dir)
        review = review_service.load_review(project_dir)
        panel = _card("M10-M13 统计结果路径")
        panel.setObjectName("metaM10M13StatisticsPanel")
        layout = panel.layout()
        layout.addWidget(
            _info_card(
                "效应量标准化预检查",
                [
                    f"总提取行：{normalization_summary.total_rows}",
                    f"confirmed 行：{normalization_summary.confirmed_rows}",
                    f"可用于后续统计的研究数：{normalization_summary.normalized_ready}",
                    f"需要用户检查：{normalization_summary.needs_user_review}",
                    f"字段不完整：{normalization_summary.incomplete}",
                    f"无效或不支持：{normalization_summary.invalid + normalization_summary.unsupported_effect_type}",
                    "标准化输入只用于 executor 预检查，不生成 computed 或 report_ready 结果。",
                ],
                object_name="metaEffectSizeNormalizationPreview",
            )
        )
        layout.addWidget(
            _info_card(
                "Pairwise executor",
                _pairwise_workspace_result_lines(latest_result),
                object_name="metaPairwiseExecutorPreview",
            )
        )
        layout.addWidget(
            _info_card(
                "统计结果审核",
                [
                    f"审核状态：{result_review_label_zh(review.review_state)}",
                    f"当前统计状态：{statistical_result_state_label_zh(review.result_state or (latest_result.result_state if latest_result else STATISTICAL_RESULT_STATE_NOT_RUN))}",
                    f"已确认查看警告：{'是' if review.review_warnings_acknowledged else '否'}",
                    f"申请报告就绪：{'是' if review.report_ready_requested else '否'}",
                    f"报告就绪：{'是' if review.report_ready_granted else '否'}",
                    f"阻止进入报告的原因：{'；'.join(review.report_ready_blockers) if review.report_ready_blockers else '无'}",
                    "report_ready 只代表可进入当前草稿报告流程，不代表正式发表、临床、监管或 production 结论。",
                ],
                object_name="metaResultReviewPreview",
            )
        )
        feedback = QLabel("")
        feedback.setObjectName("metaStatisticsFeedback")
        feedback.setWordWrap(True)
        layout.addWidget(feedback)
        review_notes = QLineEdit()
        review_notes.setObjectName("metaResultReviewNotesInput")
        review_notes.setPlaceholderText("审核备注（可选）")
        warning_ack = QCheckBox("已确认查看警告")
        warning_ack.setObjectName("metaResultWarningAcknowledgement")
        warning_ack.setChecked(bool(review.review_warnings_acknowledged))
        layout.addWidget(review_notes)
        layout.addWidget(warning_ack)
        buttons = QHBoxLayout()
        refresh_normalization = QPushButton("刷新效应量标准化预检查")
        run = QPushButton("运行 pairwise executor")
        accept = QPushButton("接受进入报告草稿")
        needs_revision = QPushButton("标记需要修订")
        reject = QPushButton("不纳入报告")
        report_ready = QPushButton("申请报告就绪")
        for button in (refresh_normalization, accept, needs_revision, reject, report_ready):
            button.setObjectName("metaSecondaryButton")
            buttons.addWidget(button)
        run.setObjectName("metaPrimaryButton")
        buttons.insertWidget(1, run)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        layout.addWidget(_developer_details(f"pairwise_result={pairwise_service.latest_result_path(project_dir)}\nreview={review_service.review_path(project_dir)}"))

        def latest_for_review():
            result = pairwise_service.load_latest_result(project_dir)
            if result is None:
                raise ValueError("请先运行 pairwise executor。")
            return result

        def set_transition_feedback(prefix: str, transition) -> None:
            blockers = "；".join(transition.blockers) if transition.blockers else "无"
            feedback.setText(f"{prefix}：{'已完成' if transition.success else '未完成'}；阻止进入报告的原因：{blockers}")

        def do_refresh_normalization() -> None:
            _show_message("已刷新效应量标准化预检查。")
            on_refresh()

        def do_run_pairwise() -> None:
            try:
                result = pairwise_service.execute(project_dir, actor="reviewer")
                if result.validation_errors:
                    feedback.setText("输入校验失败：" + "；".join(result.validation_errors))
                else:
                    feedback.setText("pairwise executor 已完成计算；结果仍为 Developer Preview / testing，需用户审核。")
            except Exception as exc:
                feedback.setText(f"pairwise executor 运行失败：{exc}")
            on_refresh()

        def do_accept() -> None:
            try:
                transition = review_service.accept_for_report(
                    project_dir,
                    latest_for_review(),
                    reviewer_role="reviewer",
                    review_notes=review_notes.text(),
                    warnings_acknowledged=warning_ack.isChecked(),
                )
                set_transition_feedback("接受进入报告草稿", transition)
            except Exception as exc:
                feedback.setText(f"统计结果审核失败：{exc}")
            on_refresh()

        def do_needs_revision() -> None:
            try:
                transition = review_service.mark_needs_revision(project_dir, latest_for_review(), reviewer_role="reviewer", review_notes=review_notes.text())
                set_transition_feedback("标记需要修订", transition)
            except Exception as exc:
                feedback.setText(f"统计结果审核失败：{exc}")
            on_refresh()

        def do_reject() -> None:
            try:
                transition = review_service.reject_for_report(project_dir, latest_for_review(), reviewer_role="reviewer", review_notes=review_notes.text())
                set_transition_feedback("不纳入报告", transition)
            except Exception as exc:
                feedback.setText(f"统计结果审核失败：{exc}")
            on_refresh()

        def do_report_ready() -> None:
            try:
                requested = review_service.request_report_ready(project_dir, latest_for_review(), reviewer_role="reviewer")
                latest = pairwise_service.load_latest_result(project_dir)
                granted = review_service.grant_report_ready(project_dir, latest, reviewer_role="reviewer") if requested.success else requested
                set_transition_feedback("申请报告就绪", granted)
            except Exception as exc:
                feedback.setText(f"申请报告就绪失败：{exc}")
            on_refresh()

        refresh_normalization.clicked.connect(do_refresh_normalization)
        run.clicked.connect(do_run_pairwise)
        accept.clicked.connect(do_accept)
        needs_revision.clicked.connect(do_needs_revision)
        reject.clicked.connect(do_reject)
        report_ready.clicked.connect(do_report_ready)
        return panel


    def _pairwise_workspace_result_lines(result) -> list[str]:
        if result is None:
            return [
                "当前统计状态：尚未运行正式统计分析",
                "模型：未运行",
                "纳入研究数：0",
                "合并效应量：缺失",
                "95% CI：缺失",
                "异质性 I²：缺失",
                "测试阶段提示：尚未运行 M12 pairwise executor。",
                "需要用户审核后才能进入报告。",
            ]
        payload = result.to_dict()
        heterogeneity = payload.get("heterogeneity_summary", {})
        i2 = heterogeneity.get("i_squared") if isinstance(heterogeneity, dict) else None
        ci = "缺失"
        if payload.get("pooled_ci_lower") is not None and payload.get("pooled_ci_upper") is not None:
            ci = f"{_format_number(payload.get('pooled_ci_lower'))} - {_format_number(payload.get('pooled_ci_upper'))}"
        errors = "；".join(str(item) for item in payload.get("validation_errors", []) if str(item)) if isinstance(payload.get("validation_errors"), list) else ""
        warnings = "；".join(str(item) for item in payload.get("warnings", []) if str(item)) if isinstance(payload.get("warnings"), list) else ""
        return [
            f"当前统计状态：{statistical_result_state_label_zh(str(payload.get('result_state', 'not_run')))}",
            f"模型：{payload.get('model_used') or '未运行'}",
            f"纳入研究数：{len(payload.get('included_studies', [])) if isinstance(payload.get('included_studies'), list) else 0}",
            f"合并效应量：{_format_number(payload.get('pooled_effect'))}",
            f"95% CI：{ci}",
            f"异质性 I²：{_format_number(i2)}",
            f"校验错误：{errors or '无'}",
            f"警告：{warnings or '无'}",
            "测试阶段提示：M12 为 Developer Preview / testing MVP，不生成正式医学结论。",
            "需要用户审核后才能进入报告。",
        ]


    def _format_number(value: object) -> str:
        if value is None:
            return "缺失"
        try:
            return f"{float(value):.6g}"
        except (TypeError, ValueError):
            return "缺失"


    def _statistics_analysis_page(project_dir: Path, *, on_refresh: Callable[[], None], on_next: Callable[[], None]) -> QFrame:
        plan_service = AnalysisPlanService()
        stats = MetaStatisticsEngineService(analysis_plan_service=plan_service)
        confirmed = plan_service.load_confirmed(project_dir)
        manifest = _load_json_object(stats.manifest_path(project_dir))
        result_files = sorted(stats.results_dir(project_dir).glob("*_result.json")) if stats.results_dir(project_dir).exists() else []
        latest_result = _load_json_object(result_files[-1]) if result_files else {}
        frame = QFrame()
        frame.setObjectName("metaStatisticsAnalysisPage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(_page_header("统计分析", "只能从 confirmed analysis plan 运行；结果 testing-level。", "M17 / testing"))
        layout.addWidget(_info_card("输入校验", ["请先确认分析计划" if not confirmed else "已有 confirmed analysis plan", f"run_count={manifest.get('run_count', len(result_files))}", "不生成医学 conclusion，不推进 PRISMA。"], object_name="metaStatisticsSummary"))
        result_view = QTextEdit()
        result_view.setObjectName("metaStatisticsResultPreview")
        result_view.setReadOnly(True)
        result_view.setPlainText(json.dumps(latest_result or {"message": "暂无统计结果"}, ensure_ascii=False, indent=2)[:12000])
        layout.addWidget(result_view)
        buttons = QHBoxLayout()
        run = QPushButton("运行统计分析")
        run.setObjectName("metaPrimaryButton")
        run.setEnabled(bool(confirmed))
        export_stats_manifest = QPushButton("导出统计结果清单")
        export_stats_manifest.setObjectName("metaSecondaryButton")
        export_stats_package = QPushButton("导出统计结果包")
        export_stats_package.setObjectName("metaSecondaryButton")
        next_button = QPushButton("下一步：图表结果")
        next_button.setObjectName("metaSecondaryButton")
        buttons.addWidget(run)
        buttons.addWidget(export_stats_manifest)
        buttons.addWidget(export_stats_package)
        buttons.addWidget(next_button)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        layout.addWidget(_developer_details(f"manifest={stats.manifest_path(project_dir)}\nresults={stats.results_dir(project_dir)}"))
        layout.addStretch(1)

        def do_run() -> None:
            try:
                result = stats.run_statistics(project_dir, actor="reviewer")
                _show_message(result.message)
            except Exception as exc:
                _show_message(str(exc))
            on_refresh()

        def do_export_stats_manifest() -> None:
            path = _write_statistics_results_manifest(project_dir)
            _show_message(f"已导出统计结果清单：{path.name}")
            on_refresh()

        def do_export_stats_package() -> None:
            path = _write_statistics_results_package(project_dir)
            _show_message(f"已导出统计结果包：{path.name}")
            on_refresh()

        run.clicked.connect(do_run)
        export_stats_manifest.clicked.connect(do_export_stats_manifest)
        export_stats_package.clicked.connect(do_export_stats_package)
        next_button.clicked.connect(on_next)
        return frame


    def _figure_results_page(project_dir: Path, *, on_refresh: Callable[[], None], on_next: Callable[[], None]) -> QFrame:
        service = FigureResultService()
        artifacts = service.list_figure_artifacts(project_dir)
        results_dir = project_dir / "analysis" / "results"
        result_files = sorted(results_dir.glob("*_result.json")) if results_dir.exists() else []
        frame = QFrame()
        frame.setObjectName("metaFigureResultsPage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(_page_header("图表结果", "读取已存在图表/统计结果；不重新计算统计。", "M18 逐步接入"))
        layout.addWidget(_info_card("图表摘要", [f"figure artifacts：{len(artifacts)}", f"standardized results：{len(result_files)}", "本页不会重新计算统计，不生成 conclusion。"], object_name="metaFigureSummary"))
        table = QTableWidget()
        table.setObjectName("metaFigureArtifactTable")
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["figure_id", "type", "format", "path"])
        table.setRowCount(len(artifacts))
        for row, artifact in enumerate(artifacts):
            values = [artifact.figure_id, artifact.figure_type, artifact.format, artifact.file_path]
            for col, value in enumerate(values):
                table.setItem(row, col, QTableWidgetItem(str(value)))
        layout.addWidget(table)
        actions = QHBoxLayout()
        export_figure_manifest = QPushButton("导出图表结果清单")
        export_figure_manifest.setObjectName("metaSecondaryButton")
        export_figure_package = QPushButton("导出图表结果包")
        export_figure_package.setObjectName("metaSecondaryButton")
        next_button = QPushButton("下一步：PRISMA")
        next_button.setObjectName("metaSecondaryButton")
        actions.addWidget(export_figure_manifest)
        actions.addWidget(export_figure_package)
        actions.addWidget(next_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        def do_export_figure_manifest() -> None:
            path = _write_figure_results_manifest(project_dir)
            _show_message(f"已导出图表结果清单：{path.name}")
            on_refresh()

        def do_export_figure_package() -> None:
            path = _write_figure_results_package(project_dir)
            _show_message(f"已导出图表结果包：{path.name}")
            on_refresh()

        export_figure_manifest.clicked.connect(do_export_figure_manifest)
        export_figure_package.clicked.connect(do_export_figure_package)
        next_button.clicked.connect(on_next)
        layout.addWidget(_developer_details(f"figure_manifest={project_dir / 'figures' / 'figure_artifacts.json'}\nresults_dir={results_dir}"))
        layout.addStretch(1)
        return frame


    def _prisma_page(project_dir: Path, *, on_refresh: Callable[[], None], on_next: Callable[[], None]) -> QFrame:
        service = PRISMAService()
        summary = service.load_prisma_flow_summary(project_dir)
        frame = QFrame()
        frame.setObjectName("metaPrismaPage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(_page_header("PRISMA", "数字必须来自真实导入、去重、筛选、全文记录。", "可追溯"))
        lines = ["尚未生成 PRISMA summary。"]
        if summary is not None:
            payload = _prisma_payload(summary)
            lines = [
                f"identified={payload.get('records_identified', 0)}",
                f"duplicates_removed={payload.get('duplicates_removed', 0)}",
                f"screened={payload.get('records_screened', 0)}",
                f"title/abstract excluded={payload.get('records_excluded_title_abstract', 0)}",
                f"studies included={payload.get('studies_included', 0)}",
            ]
        layout.addWidget(_info_card("PRISMA summary", lines, object_name="metaPrismaSummary"))
        buttons = QHBoxLayout()
        collect = QPushButton("生成 PRISMA summary")
        export_md = QPushButton("导出 Markdown")
        export_prisma_package = QPushButton("导出 PRISMA 报告包")
        next_button = QPushButton("下一步：报告导出")
        for button in (collect, export_md, export_prisma_package, next_button):
            button.setObjectName("metaSecondaryButton")
            buttons.addWidget(button)
        collect.setObjectName("metaPrimaryButton")
        buttons.addStretch(1)
        layout.addLayout(buttons)
        layout.addWidget(_developer_details(f"summary={project_dir / 'reports' / 'prisma_flow_summary.json'}"))
        layout.addStretch(1)

        def do_collect() -> None:
            result = service.collect_prisma_numbers(project_dir)
            path = service.save_prisma_flow_summary(project_dir, result)
            _show_message(f"已生成：{path.name}")
            on_refresh()

        def do_export_md() -> None:
            result = service.load_prisma_flow_summary(project_dir) or service.collect_prisma_numbers(project_dir)
            path = service.export_prisma_flow_markdown(project_dir, result)
            _show_message(f"已导出：{path.name}")
            on_refresh()

        def do_export_prisma_package() -> None:
            path = _write_prisma_reporting_package(project_dir)
            _show_message(f"已导出 PRISMA 报告包：{path.name}")
            on_refresh()

        collect.clicked.connect(do_collect)
        export_md.clicked.connect(do_export_md)
        export_prisma_package.clicked.connect(do_export_prisma_package)
        next_button.clicked.connect(on_next)
        return frame


    def _report_export_page(project_dir: Path, *, on_refresh: Callable[[], None], on_next: Callable[[], None]) -> QFrame:
        report_path = project_dir / "reports" / "formal_meta_report.md"
        frame = QFrame()
        frame.setObjectName("metaReportExportPage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(_page_header("报告导出", "生成中文 draft/testing 报告；明确区分确认、草稿、建议、缺失和未来统计占位。", "draft"))
        missing_hint = "缺失内容提示：生成报告后会在 Markdown 末尾列出。"
        layout.addWidget(
            _info_card(
                "报告状态",
                [
                    f"Markdown 草稿：{'已存在' if report_path.exists() else '暂无'}",
                    "不会自动生成 pooled effect、p value、forest plot、funnel plot 或医学结论。",
                    "统计分析结果尚未作为正式可发表结论生成。",
                    missing_hint,
                ],
                object_name="metaReportSummary",
            )
        )
        preview = QTextEdit()
        preview.setObjectName("metaReportPreview")
        preview.setReadOnly(True)
        preview.setPlainText(report_path.read_text(encoding="utf-8")[:12000] if report_path.exists() else "暂无报告草稿。")
        layout.addWidget(preview)
        buttons = QHBoxLayout()
        build_md = QPushButton("生成报告草稿")
        show_location = QPushButton("打开报告位置")
        export_html = QPushButton("导出 HTML")
        export_docx = QPushButton("导出 DOCX")
        export_report_package = QPushButton("导出报告交付包")
        next_button = QPushButton("下一步：复现包")
        for button in (build_md, show_location, export_html, export_docx, export_report_package, next_button):
            button.setObjectName("metaSecondaryButton")
            buttons.addWidget(button)
        build_md.setObjectName("metaPrimaryButton")
        buttons.addStretch(1)
        layout.addLayout(buttons)
        layout.addWidget(_developer_details(f"report={report_path}"))
        layout.addStretch(1)

        def do_build_md() -> None:
            path = FormalMarkdownReportBuilder().build_draft_markdown_report(project_dir)
            _show_message(f"已生成：{path.name}")
            on_refresh()

        def do_show_location() -> None:
            reports_dir = project_dir / "reports"
            _copy_text_to_clipboard(str(reports_dir))
            _show_message(f"报告目录路径已复制：{reports_dir}")

        def do_export_html() -> None:
            result = PublicationExportService().export_html_report(project_dir)
            _show_message(result.message)
            on_refresh()

        def do_export_docx() -> None:
            result = PublicationExportService().export_word_report(project_dir)
            _show_message(result.message)
            on_refresh()

        def do_export_report_package() -> None:
            path = _write_formal_report_package(project_dir)
            _show_message(f"已导出报告交付包：{path.name}")
            on_refresh()

        build_md.clicked.connect(do_build_md)
        show_location.clicked.connect(do_show_location)
        export_html.clicked.connect(do_export_html)
        export_docx.clicked.connect(do_export_docx)
        export_report_package.clicked.connect(do_export_report_package)
        next_button.clicked.connect(on_next)
        return frame


    def _reproducibility_package_page(project_dir: Path, *, on_refresh: Callable[[], None]) -> QFrame:
        exports = sorted((project_dir / "exports").glob("reproducibility_package_*.zip")) if (project_dir / "exports").exists() else []
        frame = QFrame()
        frame.setObjectName("metaReproducibilityPackagePage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(_page_header("可复现项目包", "打包项目关键 artifact，保留 schema/version。", "export"))
        layout.addWidget(_info_card("导出状态", [f"已有 package：{len(exports)}", "不包含不必要的本机绝对路径。", "用于内部 testing / 迁移复核。"], object_name="metaReproducibilitySummary"))
        package_list = QListWidget()
        package_list.setObjectName("metaReproducibilityPackageList")
        for path in exports:
            package_list.addItem(str(path.relative_to(project_dir)))
        layout.addWidget(package_list)
        export = QPushButton("导出可复现项目包")
        export.setObjectName("metaPrimaryButton")
        layout.addWidget(export)
        layout.addWidget(_developer_details(f"exports_dir={project_dir / 'exports'}"))
        layout.addStretch(1)

        def do_export() -> None:
            result = PublicationExportService().export_reproducibility_package(project_dir)
            _show_message(result.message)
            on_refresh()

        export.clicked.connect(do_export)
        return frame


    def _placeholder_step_page(step: MetaWorkflowStepState) -> QFrame:
        frame = QFrame()
        frame.setObjectName(f"metaPlaceholder_{step.route_key}")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(_page_header(step.title_zh, step.artifact_summary, "待开发 / testing-level"))
        layout.addWidget(_info_card("当前状态", [f"状态：{step.status}", f"artifact 数量：{step.artifact_count}", f"warning 数量：{step.warning_count}", f"下一步：{step.next_action_zh}"]))
        layout.addWidget(_info_card("边界", ["本轮不触发业务写入。", "不运行统计，不生成图表，不生成报告，不推进 PRISMA。"]))
        layout.addWidget(_developer_details(_step_debug_text(step)))
        layout.addStretch(1)
        return frame


    def _page_header(title: str, subtitle: str, badge: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("metaPageHeader")
        layout = QHBoxLayout(frame)
        title_col = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("metaPageTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("metaMutedText")
        subtitle_label.setWordWrap(True)
        title_col.addWidget(title_label)
        title_col.addWidget(subtitle_label)
        layout.addLayout(title_col, 1)
        badge_label = QLabel(badge)
        badge_label.setObjectName("metaStatusBadge")
        layout.addWidget(badge_label)
        return frame


    def _meta_home_header(summary: MetaProjectSummary | None, title: str, subtitle: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("metaPageHeader")
        layout = QHBoxLayout(frame)
        title_col = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("metaPageTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("metaMutedText")
        subtitle_label.setWordWrap(True)
        title_col.addWidget(title_label)
        title_col.addWidget(subtitle_label)
        if summary is not None:
            summary_label = QLabel(
                f"{summary.project_name} · {_compact_path(summary.project_root)} · 当前阶段：{_workflow_stage_zh(summary.workflow_stage)}"
            )
            summary_label.setObjectName("metaMutedText")
            summary_label.setWordWrap(True)
            title_col.addWidget(summary_label)
        layout.addLayout(title_col, 1)
        badge_label = QLabel("Developer Preview / 本地测试版")
        badge_label.setObjectName("metaStatusBadge")
        layout.addWidget(badge_label)
        return frame


    def _project_business_summary(project_dir: Path) -> QFrame:
        pico = PICOWorkspaceService()
        library = LiteratureLibraryService()
        extraction = ManualExtractionEffectRowService()
        analysis = AnalysisPlanService()
        screening_payload = _load_json_object(TitleAbstractScreeningV2Service().decisions_path(project_dir))
        screening_records = _items_from_payload(screening_payload, "screening_records")
        literature_count = len(library.list_records(project_dir))
        effect_rows = extraction.load_effect_rows(project_dir)
        lines = [
            f"研究问题：{'已确认' if pico.load_confirmed(project_dir) else '未填写'}",
            f"文献库：{literature_count} 篇",
            f"筛选记录：{len(screening_records)} 条",
            f"数据提取表：{'已创建' if effect_rows else '未创建'}",
            f"分析计划：{'已创建' if analysis.load_confirmed(project_dir) else '未创建'}",
        ]
        return _info_card("项目摘要", lines, object_name="metaProjectSummaryCard")


    def _progress_summary(state) -> QFrame:
        stage_labels = {
            "project_home": "项目首页",
            "page_button_audit": "页面能力审计",
            "pico_workspace": "研究问题与 PICO",
            "search_strategy": "检索策略",
            "literature_import": "文献库与导入",
            "screening": "去重与筛选",
            "exclusion_criteria": "排除标准",
            "title_abstract_screening": "标题摘要筛选",
            "fulltext_management": "全文管理",
            "manual_extraction": "数据提取",
            "extraction_quality": "数据提取",
            "ai_extraction": "AI 辅助提取",
            "quality_assessment": "质量评价",
            "analysis_plan": "分析计划",
            "statistics_analysis": "统计分析",
            "figure_results": "图表结果",
            "prisma": "PRISMA",
            "report_export": "报告导出",
            "reproducibility_package": "复现包",
            "analysis_results": "统计分析",
            "prisma_reporting": "报告导出",
        }
        complete_statuses = {"已完成", "已有项目", "已确认", "已生成", "已有记录", "已有人工评分"}
        current = next((step for step in state.steps if step.status not in complete_statuses), state.steps[-1])
        if current.step_id == "pico_workspace":
            current_line = "当前进度：项目已创建"
            next_line = "下一步：填写研究问题 / PICO"
        else:
            current_line = f"当前进度：{stage_labels.get(current.step_id, current.title_zh)}"
            next_line = f"下一步：{current.next_action_zh}"
        chips = []
        for step in state.steps:
            label = stage_labels.get(step.step_id, step.title_zh)
            if step.step_id == current.step_id:
                status = f"当前（{_main_stage_status_label(step.status)}）"
            else:
                status = _main_stage_status_label(step.status)
            chips.append(f"{label} {status}")
        return _info_card("流程进度", [current_line, next_line, " / ".join(chips)], object_name="metaProgressCard")


    def _developer_diagnostics_text(state, summary: MetaProjectSummary | None = None) -> str:
        lines = ["内部诊断信息"]
        if summary is not None:
            lines.extend(
                [
                    f"project_stage={summary.workflow_stage}",
                    f"status={summary.status}",
                    f"created_at={summary.created_at}",
                    f"manifest_path={summary.manifest_path}",
                    f"config_path={summary.config_path}",
                ]
            )
        lines.append("workflow_state:")
        lines.extend(f"{step.route_key}: {step.status} / {step.artifact_summary}" for step in state.steps)
        warnings = [warning for step in state.steps for warning in step.warnings]
        if warnings:
            lines.append("warnings:")
            lines.extend(warnings[:8])
        return "\n".join(lines)


    def _card(title: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("metaCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        label = QLabel(title)
        label.setObjectName("metaCardTitle")
        layout.addWidget(label)
        return frame


    def _info_card(title: str, lines: list[str], *, object_name: str = "metaInfoCard") -> QFrame:
        frame = _card(title)
        frame.setObjectName(object_name)
        body = QLabel("\n".join(str(line) for line in lines if str(line).strip()) or "暂无")
        body.setObjectName("metaCardBody")
        body.setWordWrap(True)
        frame.layout().addWidget(body)
        return frame


    def _developer_details(text: str, *, button_text: str = "开发者诊断") -> QFrame:
        frame = QFrame()
        frame.setObjectName("metaDeveloperDetails")
        layout = QVBoxLayout(frame)
        button = QPushButton(button_text)
        button.setObjectName("metaSecondaryButton")
        detail = QLabel(text)
        detail.setObjectName("metaDeveloperDetailsBody")
        detail.setWordWrap(True)
        detail.setVisible(False)
        button.clicked.connect(lambda: detail.setVisible(not detail.isVisible()))
        layout.addWidget(button)
        layout.addWidget(detail)
        return frame


    def _kv_label(label: str, value: str) -> QLabel:
        widget = QLabel(f"{label}：{value or '暂无'}")
        widget.setWordWrap(True)
        return widget


    def _warning_label(text: str) -> QLabel:
        widget = QLabel("Warnings：" + text)
        widget.setObjectName("metaWarningText")
        widget.setWordWrap(True)
        return widget


    def _analysis_plan_state_label(value: str) -> str:
        labels = {
            "draft": "草稿",
            "suggested": "建议",
            "user_edited": "用户编辑",
            "confirmed": "已确认",
            "needs_revision": "需要修订",
            "missing": "未生成",
            "未生成": "未生成",
        }
        return labels.get(value, value or "未生成")


    def _plan_text(value: object) -> str:
        if isinstance(value, dict):
            for key in ("user_plan", "description", "status"):
                if str(value.get(key, "")).strip():
                    return str(value.get(key))
            return "；".join(f"{key}: {item}" for key, item in value.items() if str(item).strip())
        if isinstance(value, (list, tuple)):
            return "；".join(str(item) for item in value if str(item).strip())
        return str(value or "")


    def _default_meta_type(candidates: tuple[dict[str, object], ...]) -> str:
        for candidate in candidates:
            value = str(candidate.get("meta_type") or candidate.get("type") or candidate.get("id") or candidate.get("name") or "")
            if value and "coming_soon" not in value:
                return value
        return "treatment_comparative_meta"


    def _default_inclusion_criteria(draft) -> str:
        if draft is None:
            return ""
        parts = [
            f"研究对象符合：{draft.population}" if draft.population else "",
            f"干预/暴露符合：{draft.exposure or draft.intervention}" if draft.exposure or draft.intervention else "",
            f"对照符合：{draft.comparator}" if draft.comparator else "",
            f"结局包含：{draft.outcome}" if draft.outcome else "",
            f"研究类型：{draft.study_design}" if draft.study_design else "",
        ]
        return "；".join(part for part in parts if part)


    def _recommended_effect_measure(draft) -> str:
        if draft is None:
            return ""
        meta_type = _default_meta_type(draft.meta_type_candidates)
        if "diagnostic" in meta_type:
            return "敏感度、特异度、诊断比值比"
        if "prevalence" in meta_type or "incidence" in meta_type:
            return "比例、发生率或率比"
        if "correlation" in meta_type:
            return "相关系数 r 或 Fisher z"
        if "survival" in meta_type or "prognostic" in meta_type:
            return "HR"
        if draft.pico_mode == "peco" or "risk" in meta_type:
            return "OR、RR 或 HR"
        return "RR、OR、MD 或 SMD"


    def _pico_ui_draft_path(project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "protocol" / "pico_workspace_ui_draft.json"


    def _save_pico_ui_draft(project_dir: Path, draft_fields: dict[str, QLineEdit]) -> None:
        payload = {
            "schema_version": "meta_pico_workspace_ui_draft.v1",
            "inclusion_criteria": draft_fields["inclusion_criteria"].text().strip(),
            "exclusion_criteria": draft_fields["exclusion_criteria"].text().strip(),
            "primary_outcomes": draft_fields["primary_outcomes"].text().strip(),
            "secondary_outcomes": draft_fields["secondary_outcomes"].text().strip(),
            "effect_measure": draft_fields["effect_measure"].text().strip(),
        }
        path = _pico_ui_draft_path(project_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


    def _database_label(database: str) -> str:
        labels = {
            "pubmed": "PubMed",
            "web_of_science": "Web of Science",
            "embase": "Embase",
            "cochrane": "Cochrane",
            "cnki": "CNKI",
            "wanfang": "万方",
            "vip": "维普",
        }
        return labels.get(database, database)


    def _search_database_order() -> tuple[str, ...]:
        return ("pubmed", "web_of_science", "embase", "cochrane", "cnki", "wanfang", "vip")


    def _search_strategy_status(draft, confirmed) -> str:
        if confirmed is not None and str(confirmed.execution_status) not in {"", "not_executed"}:
            if str(confirmed.execution_status) == "ready_for_pubmed_execution":
                return "已确认"
            return "已确认"
        if confirmed is not None:
            return "已确认"
        if draft is None:
            return "未生成"
        if draft.warnings:
            return "有警告" if "draft_only" not in draft.warnings else "草稿"
        return "已编辑" if int(draft.version) > 1 else "草稿"


    def _database_manual_notice(database: str) -> str:
        if database == "pubmed":
            return "PubMed 检索式确认后可执行 testing-level 在线检索；结果仍需人工复核。"
        manual_registry = {
            "wos": ("Web of Science", "https://www.webofscience.com", "plain text / tab-delimited"),
            "embase": ("Embase", "https://www.embase.com", "RIS"),
            "cochrane": ("Cochrane Library", "https://www.cochranelibrary.com", "RIS"),
            "cnki": ("CNKI", "https://www.cnki.net", "CNKI 本地导出"),
            "wanfang": ("万方", "https://www.wanfangdata.com.cn", "本地导出"),
            "vip": ("维普", "https://www.cqvip.com", "本地导出"),
        }
        label, url, formats = manual_registry.get(database, (_database_label(database), "", "本地导出"))
        url_text = f"官网：{url}" if url else "官网入口：请按机构权限访问"
        return f"{label} 当前走手动检索流程：复制检索式 -> 打开官网 -> 人工检索 -> 导入结果文件。{url_text}；建议导入格式：{formats}。"


    def _write_pubmed_execution_report(project_dir: Path, execution) -> Path:
        path = project_dir.expanduser().resolve() / "protocol" / "search_execution_report.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(execution.to_report(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path


    def _latest_pubmed_preview_payload(project_dir: Path) -> dict[str, object]:
        preview_paths = sorted((project_dir.expanduser().resolve() / "protocol" / "pubmed_candidates").glob("*_candidates_preview.json"))
        if not preview_paths:
            return {}
        return _load_json_object(preview_paths[-1])


    def _pubmed_preview_summary(preview: dict[str, object], *, execution_report: dict[str, object] | None = None) -> str:
        if not preview:
            return "尚无 PubMed 候选文献。请先确认 PubMed 检索式并执行 testing-level 检索。"
        candidates = _items_from_payload(preview, "candidates")
        with_abstract = len([item for item in candidates if str(item.get("abstract", "")).strip()])
        total_count = int((execution_report or {}).get("result_count") or len(candidates) or 0)
        fetched_count = int((execution_report or {}).get("returned_count") or len(candidates) or 0)
        return (
            f"检索总数 {total_count} 条；当前已保存候选 {len(candidates)} 条；"
            f"当前批次返回 {fetched_count} 条；有摘要 {with_abstract} 条；preview={preview.get('preview_id', '')}"
        )


    def _pubmed_page_info_text(preview: dict[str, object], *, execution_report: dict[str, object] | None = None) -> str:
        if not preview:
            return "默认不显示详情；请先执行 PubMed 检索并手动选择需要查看或导入的候选文献。"
        total_count = int((execution_report or {}).get("result_count") or len(_items_from_payload(preview, "candidates")) or 0)
        page_size = int((execution_report or {}).get("returned_count") or len(_items_from_payload(preview, "candidates")) or 0)
        if total_count > page_size > 0:
            return f"当前工作台已保留第 1 批 {page_size} 条候选结果；总召回 {total_count} 条。默认只展示已保存候选，导入只作用于已选中行。"
        return "候选文献按行展示；未点击任何行前，右侧详情面板保持空状态。"


    def _candidate_row_text(candidate: dict[str, object]) -> str:
        authors = candidate.get("authors", [])
        first_author = authors[0] if isinstance(authors, list) and authors else ""
        abstract_flag = "有摘要" if str(candidate.get("abstract", "")).strip() else "无摘要"
        return " · ".join(
            item
            for item in (
                str(candidate.get("title") or "Untitled"),
                str(first_author),
                str(candidate.get("year") or ""),
                str(candidate.get("journal") or ""),
                f"PMID {candidate.get('pmid') or '-'}",
                f"DOI {candidate.get('doi') or '-'}",
                abstract_flag,
                str(candidate.get("user_decision") or "pending"),
            )
            if item
        )


    def _candidate_detail_text(candidate: dict[str, object]) -> str:
        if not candidate:
            return "请选择一条候选文献以查看英文标题和摘要。"
        authors = candidate.get("authors", [])
        authors_text = "；".join(str(item) for item in authors) if isinstance(authors, list) else str(authors or "")
        return "\n".join(
            [
                f"英文标题：{candidate.get('title') or ''}",
                f"英文摘要：{candidate.get('abstract') or ''}",
                f"DOI：{candidate.get('doi') or ''}",
                f"PMID：{candidate.get('pmid') or ''}",
                f"期刊：{candidate.get('journal') or ''}",
                f"年份：{candidate.get('year') or ''}",
                f"作者：{authors_text}",
                "来源数据库：PubMed",
                "用户备注：仅用于人工查看，不参与内部识别、检索和去重逻辑。",
            ]
        )


    def _pubmed_candidate_status_label(candidate: dict[str, object]) -> str:
        decision = str(candidate.get("user_decision") or "pending")
        return {
            "selected": "已选中待导入",
            "rejected": "已忽略",
            "pending": "待处理",
        }.get(decision, decision or "待处理")


    def _selected_table_rows(table: QTableWidget) -> list[int]:
        rows = {item.row() for item in table.selectedItems()}
        return sorted(rows)


    def _set_all_list_items_selected(widget: QListWidget, selected: bool) -> None:
        for index in range(widget.count()):
            widget.item(index).setSelected(selected)


    def _literature_import_summary_lines(project_dir: Path, manifest: dict[str, object]) -> list[str]:
        batches_payload = _load_json_object(project_dir.expanduser().resolve() / "literature" / "import_batches.json")
        batches = _items_from_payload(batches_payload, "import_batches")
        latest = batches[-1] if batches else {}
        source_counts = dict(manifest.get("source_counts", {})) if isinstance(manifest.get("source_counts"), dict) else {}
        pubmed_count = int(source_counts.get("pubmed_confirmed_candidates", 0) or 0)
        diagnostics = latest.get("diagnostics", {}) if isinstance(latest.get("diagnostics"), dict) else {}
        warning_counts = dict(diagnostics.get("warning_counts", {})) if isinstance(diagnostics.get("warning_counts"), dict) else {}
        return [
            f"当前文献总数：{manifest.get('total_records', 0)}",
            f"PubMed 来源数量：{pubmed_count}",
            f"最近导入批次：{latest.get('import_batch_id') or latest.get('batch_id') or '暂无'}",
            f"导入成功数量：{latest.get('imported_count', 0)}",
            f"跳过/失败数量：{latest.get('skipped_count', 0)}",
            f"缺 DOI：{warning_counts.get('缺少 DOI', 0)}",
            f"缺摘要：{warning_counts.get('缺少摘要', 0)}",
            f"缺年份：{warning_counts.get('缺少年份', 0)}",
        ]


    def _latest_multisource_diagnostics_lines(project_dir: Path) -> list[str]:
        diagnostics_dir = project_dir.expanduser().resolve() / "literature" / "multisource_import_diagnostics"
        paths = sorted(diagnostics_dir.glob("*_diagnostics.json"))
        if not paths:
            return ["暂无本地导入诊断。"]
        payload = _load_json_object(paths[-1])
        warning_counts = dict(payload.get("warning_counts", {})) if isinstance(payload.get("warning_counts"), dict) else {}
        return [
            f"导入文件名：{Path(str(payload.get('source_path', ''))).name or '未知'}",
            f"来源格式：{payload.get('source_format', '')}",
            f"成功条数：{payload.get('parsed_record_count', 0)}",
            f"失败条数：{payload.get('failed_record_count', 0)}",
            f"缺 DOI 条数：{warning_counts.get('缺少 DOI', 0)}",
            f"缺摘要条数：{warning_counts.get('缺少摘要', 0)}",
            f"缺年份条数：{warning_counts.get('缺少年份', 0)}",
            f"字段映射警告：{payload.get('warning_count', 0)}",
        ]


    def _literature_library_diagnostics(project_dir: Path, *, records: list[dict[str, object]] | None = None) -> dict[str, object]:
        records = records if records is not None else LiteratureLibraryService().list_records(project_dir)
        batches_payload = _load_json_object(project_dir.expanduser().resolve() / "literature" / "import_batches.json")
        batches = _items_from_payload(batches_payload, "import_batches")
        latest = batches[-1] if batches else {}
        source_counts: dict[str, int] = {"PubMed": 0, "NBIB": 0, "RIS": 0, "CSV": 0, "PubMed XML": 0, "WOS": 0, "CNKI": 0, "其他": 0}
        for record in records:
            label = _source_bucket(str(record.get("source_type") or record.get("source") or record.get("database_source") or ""))
            source_counts[label] = source_counts.get(label, 0) + 1
        missing = {
            "doi": len([record for record in records if not str(record.get("doi", "")).strip()]),
            "pmid": len([record for record in records if not str(record.get("pmid", "")).strip()]),
            "abstract": len([record for record in records if not str(record.get("abstract", "")).strip()]),
            "year": len([record for record in records if not str(record.get("year", "")).strip()]),
            "journal": len([record for record in records if not str(record.get("journal") or record.get("publication_title") or "").strip()]),
        }
        title_abnormal = [str(record.get("title") or "") for record in records if _title_looks_abnormal(str(record.get("title") or ""))]
        diagnostics = latest.get("diagnostics", {}) if isinstance(latest.get("diagnostics"), dict) else {}
        warning_counts = dict(diagnostics.get("warning_counts", {})) if isinstance(diagnostics.get("warning_counts"), dict) else {}
        return {
            "total_records": len(records),
            "source_counts": source_counts,
            "latest_batch": latest,
            "imported_count": int(latest.get("imported_count", 0) or 0),
            "skipped_count": int(latest.get("skipped_count", 0) or 0),
            "failed_count": int(diagnostics.get("failed_record_count", 0) or latest.get("failed_count", 0) or 0),
            "missing": missing,
            "field_mapping_warnings": list(diagnostics.get("field_mapping_warnings", [])) if isinstance(diagnostics.get("field_mapping_warnings"), list) else [],
            "warning_counts": warning_counts,
            "title_abnormality_count": len(title_abnormal),
            "title_abnormality_examples": title_abnormal[:5],
        }


    def _literature_diagnostics_lines(diagnostics: dict[str, object]) -> list[str]:
        missing = dict(diagnostics.get("missing", {})) if isinstance(diagnostics.get("missing"), dict) else {}
        source_counts = dict(diagnostics.get("source_counts", {})) if isinstance(diagnostics.get("source_counts"), dict) else {}
        latest = dict(diagnostics.get("latest_batch", {})) if isinstance(diagnostics.get("latest_batch"), dict) else {}
        mapping = diagnostics.get("field_mapping_warnings", [])
        return [
            f"当前文献总数：{diagnostics.get('total_records', 0)}",
            "按来源统计：" + "；".join(f"{key} {value}" for key, value in source_counts.items()),
            f"最近导入批次：{latest.get('import_batch_id') or latest.get('batch_id') or '暂无'}",
            f"导入成功数：{diagnostics.get('imported_count', 0)}",
            f"跳过数：{diagnostics.get('skipped_count', 0)}",
            f"失败数：{diagnostics.get('failed_count', 0)}",
            f"缺 DOI 数：{missing.get('doi', 0)}",
            f"缺 PMID 数：{missing.get('pmid', 0)}",
            f"缺 abstract 数：{missing.get('abstract', 0)}",
            f"缺年份数：{missing.get('year', 0)}",
            f"缺期刊数：{missing.get('journal', 0)}",
            f"字段映射警告：{'；'.join(str(item) for item in mapping[:3]) if mapping else '暂无'}",
            f"可能乱码或标题异常：{diagnostics.get('title_abnormality_count', 0)}",
        ]


    def _literature_source_filter_values(records: list[dict[str, object]]) -> list[str]:
        values = sorted({str(record.get("source_type") or record.get("source") or "") for record in records if str(record.get("source_type") or record.get("source") or "").strip()})
        return values


    def _record_matches_literature_filters(record: dict[str, object], *, query: str, source_type: str, missing_field: str) -> bool:
        if source_type and str(record.get("source_type") or record.get("source") or "") != source_type:
            return False
        if missing_field:
            value = record.get("journal") or record.get("publication_title") if missing_field == "journal" else record.get(missing_field)
            if str(value or "").strip():
                return False
        needle = query.strip().lower()
        if not needle:
            return True
        haystack = " ".join(
            [
                str(record.get("title", "")),
                str(record.get("authors", "")),
                str(record.get("authors_text", "")),
                str(record.get("doi", "")),
                str(record.get("pmid", "")),
            ]
        ).lower()
        return needle in haystack


    def _record_status_label(record: dict[str, object]) -> str:
        return str(record.get("record_status") or record.get("dedup_status") or record.get("screening_status") or "未开始")


    def _source_bucket(source: str) -> str:
        text = source.lower()
        if "pubmed_confirmed" in text or text == "pubmed" or text.startswith("pubmed_"):
            return "PubMed"
        if "nbib" in text:
            return "NBIB"
        if "ris" in text:
            return "RIS"
        if text == "csv":
            return "CSV"
        if "pubmed_xml" in text:
            return "PubMed XML"
        if "wos" in text or "web_of_science" in text:
            return "WOS"
        if "cnki" in text:
            return "CNKI"
        return "其他"


    def _source_label(source: str) -> str:
        if not source:
            return "未知"
        return {
            "pubmed_confirmed_candidates": "PubMed",
            "pubmed_xml": "PubMed XML",
            "nbib": "NBIB",
            "ris": "RIS",
            "csv": "CSV",
            "wos_plain_text": "WOS",
            "wos_tab_delimited": "WOS",
            "cnki_export": "CNKI",
        }.get(source, source)


    def _title_looks_abnormal(title: str) -> bool:
        text = title.strip()
        if not text:
            return True
        if "\ufffd" in text or "�" in text:
            return True
        if text.count("?") >= 3:
            return True
        letters = sum(1 for char in text if char.isalpha())
        return len(text) >= 12 and letters == 0


    def _literature_notes_path(project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "literature" / "literature_record_notes.json"


    def _load_literature_note(project_dir: Path, record_id: str) -> str:
        payload = _load_json_object(_literature_notes_path(project_dir))
        notes = payload.get("notes", {}) if isinstance(payload, dict) else {}
        return str(notes.get(record_id, "")) if isinstance(notes, dict) else ""


    def _save_literature_note(project_dir: Path, record_id: str, note: str) -> None:
        path = _literature_notes_path(project_dir)
        payload = _load_json_object(path)
        notes = dict(payload.get("notes", {})) if isinstance(payload.get("notes"), dict) else {}
        notes[record_id] = note.strip()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"schema_version": "meta_literature_user_notes.v1", "notes": notes}, ensure_ascii=False, indent=2), encoding="utf-8")


    def _export_literature_library_summary(project_dir: Path, *, diagnostics: dict[str, object], records: list[dict[str, object]]) -> Path:
        path = project_dir.expanduser().resolve() / "literature" / "literature_library_summary.md"
        lines = ["# 文献库摘要", "", *_literature_diagnostics_lines(diagnostics), "", "## 文献", ""]
        for record in records:
            lines.append(f"- {record.get('title') or 'Untitled'} | {record.get('year') or '-'} | PMID {record.get('pmid') or '-'} | DOI {record.get('doi') or '-'}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")
        return path


    def _items_from_payload(payload: dict[str, object], key: str) -> list[dict[str, object]]:
        value = payload.get(key)
        if isinstance(value, list):
            return [dict(item) for item in value if isinstance(item, dict)]
        return []


    def _record_detail(record: dict[str, object], *, user_note: str = "") -> str:
        authors = record.get("authors", "")
        authors_text = "；".join(str(item) for item in authors) if isinstance(authors, list) else str(authors or record.get("authors_text", ""))
        return "\n".join(
            [
                f"英文标题：{record.get('title', '')}",
                f"作者：{authors_text}",
                f"期刊：{record.get('journal', '')}",
                f"年份：{record.get('year', '')}",
                f"PMID：{record.get('pmid', '')}",
                f"DOI：{record.get('doi', '')}",
                f"Abstract：{record.get('abstract', '')}",
                f"来源数据库：{record.get('database_source') or record.get('source_type', '')}",
                f"导入批次：{record.get('import_batch_id') or record.get('batch_id') or ''}",
                f"当前筛选状态：{record.get('screening_status', '')}",
                f"用户备注：{user_note}",
            ]
        )


    def _screening_decision_label(decision: str) -> str:
        return {
            "not_screened": "未筛选",
            "pending": "未筛选",
            "include": "纳入",
            "included": "纳入",
            "exclude": "排除",
            "excluded": "排除",
            "uncertain": "不确定",
            "maybe": "不确定",
            "need_full_text": "需要全文",
            "needs_review": "需要复核",
        }.get(decision, decision or "未筛选")


    def _author_year_text(authors: object, year: object) -> str:
        author_text = ""
        if isinstance(authors, (list, tuple)):
            author_text = "、".join(str(item).strip() for item in authors if str(item).strip())
        else:
            author_text = str(authors or "").strip()
        year_text = str(year or "").strip()
        if author_text and year_text:
            return f"{author_text} · {year_text}"
        return author_text or year_text or "作者/年份未记录"


    def _extraction_source_label(source: str) -> str:
        return {
            "full_text_confirmed": "全文已确认",
            "final_included_studies": "全文筛选纳入",
            "manual_full_text_unavailable": "全文不可获取：人工提取",
            "manual_library_fallback": "文献库人工提取",
        }.get(source, source or "来源未标记")


    def _evidence_state_label(state: str) -> str:
        return {
            "empty": "空",
            "draft": "草稿",
            "suggested": "建议",
            "user_accepted": "用户接受",
            "user_edited": "用户编辑",
            "confirmed": "已确认",
            "rejected": "已拒绝",
            "completed_by_user": "用户已完成",
            "missing_data": "缺失数据",
            "not_started": "未开始",
        }.get(state, state or "草稿")


    def _quality_rating_label(rating: str) -> str:
        return QUALITY_RATING_LABELS_ZH.get(rating, rating or "未评价")


    def _quality_state_label(state: str) -> str:
        return QUALITY_M6_STATE_LABELS_ZH.get(state, "已确认" if state == "completed_by_user" else state or "草稿")


    def _quality_study_rows_for_workspace(project_dir: Path) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        payload = _load_json_object(project_dir / "extraction" / "extraction_effect_rows.json")
        for item in _items_from_payload(payload, "effect_rows"):
            if str(item.get("evidence_state", "")) != "confirmed" and str(item.get("extraction_status", "")) != "completed_by_user":
                continue
            structured = dict(item.get("m5_structured_fields", {}) if isinstance(item.get("m5_structured_fields"), dict) else {})
            rows.append(
                {
                    "study_id": structured.get("study_id") or item.get("study_unit_label") or item.get("study_unit_id") or "",
                    "record_id": item.get("record_id", ""),
                    "title": structured.get("title") or item.get("study_unit_label") or "",
                    "first_author": structured.get("first_author", ""),
                    "year": structured.get("year", ""),
                    "study_design": structured.get("study_design", ""),
                }
            )
        if rows:
            return rows
        final = _load_json_object(project_dir / "fulltext" / "final_included_studies.json")
        for item in _items_from_payload(final, "included_studies"):
            rows.append(
                {
                    "study_id": item.get("study_id") or item.get("record_id") or "",
                    "record_id": item.get("record_id", ""),
                    "title": item.get("title", ""),
                    "first_author": item.get("first_author", ""),
                    "year": item.get("year", ""),
                    "study_design": item.get("study_design", ""),
                }
            )
        return rows


    def _first_author(record: dict[str, object]) -> str:
        first = str(record.get("first_author") or "").strip()
        if first:
            return first
        authors = record.get("authors")
        if isinstance(authors, list) and authors:
            return str(authors[0])
        authors_text = str(record.get("authors_text") or "").strip()
        return authors_text.split(";")[0].strip() if authors_text else ""


    def _screening_record_user_detail(record: dict[str, object], decision_payload: dict[str, object]) -> str:
        decision = str(decision_payload.get("decision") or record.get("decision") or DECISION_NOT_SCREENED)
        reason_code = str(decision_payload.get("exclusion_reason_code") or "")
        abstract = " ".join(str(record.get("abstract") or "").split())
        abstract_snippet = abstract if len(abstract) <= 320 else abstract[:319].rstrip() + "..."
        return "\n".join(
            [
                f"title：{record.get('title', '')}",
                f"作者：{_first_author(record)}",
                f"年份：{record.get('year', '')}",
                f"期刊：{record.get('journal', '')}",
                f"来源数据库：{record.get('database_source') or record.get('source_type') or '未知'}",
                f"摘要片段：{abstract_snippet or '暂无摘要'}",
                f"去重状态：{record.get('dedup_status') or '去重后待筛选'}",
                f"当前筛选状态：{_screening_decision_label(decision)}",
                f"排除原因：{EXCLUSION_REASON_LABELS_ZH.get(reason_code, str(decision_payload.get('exclusion_reason_text') or '暂无'))}",
            ]
        )


    def _screening_ai_suggestion_payload(project_dir: Path, record_id: str) -> dict[str, object]:
        payload = _load_json_object(TitleAbstractScreeningV2Service().suggestion_queue_path(project_dir))
        suggestions = _items_from_payload(payload, "suggestions")
        for suggestion in reversed(suggestions):
            if str(suggestion.get("record_id", "")) == record_id:
                return suggestion
        return {}


    def _screening_ai_suggestion_label(payload: dict[str, object]) -> str:
        if not payload:
            return "暂无"
        decision = _screening_decision_label(str(payload.get("suggested_decision") or ""))
        confidence = payload.get("confidence")
        if isinstance(confidence, (int, float)):
            return f"{decision}（{confidence:.0%}）"
        return decision


    def _screening_ai_suggestion_text(project_dir: Path, record_id: str) -> str:
        payload = _screening_ai_suggestion_payload(project_dir, record_id)
        if not payload:
            return "暂无 AI 建议。AI 建议不会自动写入人工筛选结果。"
        return "\n".join(
            [
                f"建议结果：{_screening_decision_label(str(payload.get('suggested_decision') or ''))}",
                f"置信度：{payload.get('confidence', '')}",
                f"命中依据：{payload.get('rationale') or '未记录'}",
                "说明：只有人工决定会进入正式筛选记录和 PRISMA 计数。",
            ]
        )


    def _next_unscreened_screening_row(
        records: list[dict[str, object]],
        decisions_by_record: dict[str, dict[str, object]],
        *,
        after_row: int,
    ) -> int:
        if not records:
            return -1
        start = max(after_row + 1, 0)
        for row in range(start, len(records)):
            record_id = str(records[row].get("record_id", ""))
            decision = str(decisions_by_record.get(record_id, {}).get("decision") or records[row].get("decision") or DECISION_NOT_SCREENED)
            if decision in {DECISION_NOT_SCREENED, "", "pending"}:
                return row
        return -1


    def _fulltext_record_detail_text(record: object, *, candidate: object | None, management: FullTextManagementService) -> str:
        record_id = getattr(record, "record_id", "")
        title = getattr(record, "title", "") or getattr(candidate, "title", "") or "未命名文献"
        authors = getattr(record, "authors", "") or getattr(candidate, "authors", "")
        year = getattr(record, "year", "") or getattr(candidate, "year", "")
        journal = getattr(record, "journal", "") or getattr(candidate, "journal", "") or "期刊未记录"
        screening = getattr(record, "source_screening_decision", "") or getattr(candidate, "screening_decision", "") or "未记录"
        status = getattr(record, "fulltext_status", getattr(record, "eligibility_status", "")) or "未记录"
        exclusion_reason = (
            getattr(record, "fulltext_exclusion_reason", "")
            or getattr(record, "unavailable_reason", "")
            or getattr(candidate, "exclusion_reason", "")
            or ""
        )
        file_label = management.safe_file_label(record) if hasattr(record, "pdf_path") else "未登记全文文件"
        return "\n".join(
            [
                f"标题：{title}",
                f"作者/年份：{_author_year_text(authors, year)}",
                f"期刊：{journal}",
                f"标题摘要决定：{_screening_decision_label(screening)}",
                f"全文状态：{FULLTEXT_STATUS_LABELS_ZH.get(status, status)}",
                f"PDF 文件：{file_label}",
                f"全文排除原因：{FULLTEXT_EXCLUSION_REASON_LABELS_ZH.get(exclusion_reason, exclusion_reason or '暂无')}",
                f"记录 ID：{record_id}",
            ]
        )


    def _risk_counts_text(risk_counts: dict[str, int]) -> str:
        if not risk_counts:
            return "暂无"
        return "；".join(f"{_risk_label(key)} {value}" for key, value in risk_counts.items())


    def _dedup_decision_label(decision: str) -> str:
        return {
            "merge": "已合并",
            "set_master_record": "已合并",
            "keep_both": "标记非重复",
            "mark_not_duplicate": "标记非重复",
            "skip": "跳过",
        }.get(decision, "未处理")


    def _dedup_log_text(decisions: list[dict[str, object]]) -> str:
        if not decisions:
            return "暂无去重日志。"
        lines = []
        for decision in decisions[-20:]:
            lines.append(
                " · ".join(
                    str(item)
                    for item in (
                        decision.get("created_at", ""),
                        decision.get("group_id", ""),
                        _dedup_decision_label(str(decision.get("decision", ""))),
                        decision.get("selected_record_id", ""),
                    )
                    if item
                )
            )
        return "\n".join(lines)


    def _stage_m3_prisma_lines(summary: dict[str, object]) -> list[str]:
        lines = [
            f"records identified from PubMed：{summary.get('records_identified_from_pubmed', 0)}",
            f"records identified from local imports：{summary.get('records_identified_from_local_imports', 0)}",
            f"total records before deduplication：{summary.get('total_records_before_deduplication', 0)}",
            f"duplicate records removed：{summary.get('duplicate_records_removed', 0)}",
            f"records after deduplication：{summary.get('records_after_deduplication', 0)}",
            f"records ready for title/abstract screening：{summary.get('records_ready_for_title_abstract_screening', 0)}",
        ]
        if str(summary.get("deduplication_status", "")) == "preliminary":
            lines.append("preliminary：去重完成后数字会更新")
        return lines


    def _dedup_group_detail(group: dict[str, object]) -> str:
        records = group.get("records", [])
        record_lines: list[str] = []
        if isinstance(records, list):
            for record in records:
                if isinstance(record, dict):
                    authors = record.get("authors", [])
                    authors_text = "；".join(str(item) for item in authors) if isinstance(authors, list) else str(authors or record.get("authors_text", ""))
                    abstract = str(record.get("abstract") or "")
                    record_lines.append(
                        "\n".join(
                            [
                                f"- {record.get('record_id', '')}",
                                f"  标题：{record.get('title', '')}",
                                f"  作者：{authors_text}",
                                f"  年份/期刊：{record.get('year', '')} / {record.get('journal', '')}",
                                f"  PMID/DOI：{record.get('pmid', '-') or '-'} / {record.get('doi', '-') or '-'}",
                                f"  Abstract：{abstract[:240]}",
                                f"  来源/批次：{record.get('source_type', '')} / {record.get('import_batch_id', '')}",
                            ]
                        )
                    )
        differences = group.get("field_differences", [])
        diff_lines: list[str] = []
        if isinstance(differences, list):
            for item in differences[:8]:
                if isinstance(item, dict):
                    diff_lines.append(f"- {item.get('field', '')}: {item.get('values', item)}")
        return "\n".join(
            [
                f"Group：{group.get('group_id', '')}",
                f"风险：{_risk_label(str(group.get('risk_level', '')))}",
                f"规则：{group.get('duplicate_rule', '')}",
                f"原因：{group.get('match_reason', '')}",
                f"置信度：{group.get('confidence', '')}",
                f"推荐保留：{group.get('retain_candidate_id', '')}",
                "记录：",
                *(record_lines or ["- 暂无记录"]),
                "字段差异：",
                *(diff_lines or ["- 暂无字段差异"]),
            ]
        )


    def _risk_label(risk: str) -> str:
        return {
            "red": "红色：高度重复",
            "yellow": "黄色：疑似重复",
            "gray": "灰色：轻度疑似",
            "green": "绿色：暂未发现重复",
        }.get(risk, risk or "未知风险")


    def _state_debug_text(state) -> str:
        return "\n".join(f"{step.route_key}: {step.status} / {step.artifact_summary}" for step in state.steps)


    def _step_debug_text(step: MetaWorkflowStepState) -> str:
        lines = [
            f"route={step.route_key}",
            f"status={step.status}",
            f"artifact_summary={step.artifact_summary}",
            f"updated_at={step.updated_at or '暂无'}",
        ]
        if step.artifact_paths:
            lines.append("paths=" + "；".join(step.artifact_paths[:5]))
        if step.warnings:
            lines.append("warnings=" + "；".join(step.warnings))
        return "\n".join(lines)


    def _show_message(text: str) -> None:
        if QMessageBox is not None:
            QMessageBox.information(None, "Meta 分析", text)


else:

    class MetaAnalysisWorkspaceWidget:  # type: ignore[no-redef]
        pass
