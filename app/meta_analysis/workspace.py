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
        "extraction_quality": "数据提取与质量评价",
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
        "提取与质量评价": "数据提取与质量评价",
        "数据提取与质量评价": "数据提取与质量评价",
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
                return _no_project_page(step)
            project_dir = self._current_project_dir
            if step.route_key == "workflow_home":
                return _project_home_page(state, project_dir, self._current_meta_project, on_go_pico=lambda: self.show_step("pico_workspace"))
            if step.route_key == "pico_workspace":
                return _pico_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("search_strategy"))
            if step.route_key == "search_strategy":
                return _search_strategy_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("literature_import"))
            if step.route_key == "literature_import":
                return _literature_acquisition_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("screening_review"))
            if step.route_key == "screening_review":
                return _dedup_review_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("manual_extraction"))
            if step.route_key == "manual_extraction":
                return _manual_extraction_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("statistics_analysis"))
            if step.route_key == "statistics_analysis":
                return _analysis_plan_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("report_export"))
            if step.route_key == "report_export":
                return _report_export_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("workflow_home"))
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
        pubmed_execute = QPushButton("执行 PubMed testing-level 检索")
        pubmed_execute.setObjectName("metaPubMedExecuteButton")
        next_button = QPushButton("下一步：文献库与导入")
        next_button.setObjectName("metaSecondaryButton")
        for button in (generate, save_edit, confirm_one, confirm_all, export, copy_query, pubmed_execute, next_button):
            actions.addWidget(button)
        actions.addStretch(1)
        workbench_layout.addLayout(actions)
        layout.addWidget(workbench)

        preview = _latest_pubmed_preview_payload(project_dir)
        candidate_card = _card("PubMed 候选文献")
        candidate_layout = candidate_card.layout()
        candidate_summary = QLabel(_pubmed_preview_summary(preview))
        candidate_summary.setObjectName("metaMutedText")
        candidate_summary.setWordWrap(True)
        candidate_layout.addWidget(candidate_summary)
        candidate_list = QListWidget()
        candidate_list.setObjectName("metaPubMedCandidateList")
        candidate_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        candidate_detail = QTextEdit()
        candidate_detail.setObjectName("metaPubMedCandidateDetail")
        candidate_detail.setReadOnly(True)
        user_note = QPlainTextEdit()
        user_note.setObjectName("metaPubMedCandidateUserNote")
        user_note.setPlaceholderText("用户备注，仅显示在当前界面，不参与检索、识别或去重。")
        user_note.setMaximumHeight(70)
        for candidate in _items_from_payload(preview, "candidates"):
            item = QListWidgetItem(_candidate_row_text(candidate))
            item.setData(Qt.ItemDataRole.UserRole, str(candidate.get("candidate_id", "")))
            item.setToolTip(_candidate_detail_text(candidate))
            candidate_list.addItem(item)
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
        candidate_layout.addWidget(candidate_list)
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
            _show_message(f"已导出：{txt_path.name} / {md_path.name} / {json_path.name}")

        def do_copy_query() -> None:
            clipboard = QApplication.clipboard() if QApplication is not None else None
            if clipboard is not None:
                clipboard.setText(editor.toPlainText())

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

        def update_candidate_detail() -> None:
            item = candidate_list.currentItem()
            if item is None:
                candidate_detail.setPlainText("暂无候选文献。")
                return
            candidate_id = str(item.data(Qt.ItemDataRole.UserRole))
            candidate = next((item for item in _items_from_payload(preview, "candidates") if str(item.get("candidate_id", "")) == candidate_id), {})
            candidate_detail.setPlainText(_candidate_detail_text(candidate))

        def do_import_selected() -> None:
            preview_id = str(preview.get("preview_id", ""))
            selected_ids = tuple(str(item.data(Qt.ItemDataRole.UserRole)) for item in candidate_list.selectedItems())
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
            candidate_list.clearSelection()
            _show_message("已忽略当前候选批次；未写入文献库。")

        database_list.currentRowChanged.connect(update_editor)
        generate.clicked.connect(do_generate)
        save_edit.clicked.connect(do_save_edit)
        confirm_one.clicked.connect(do_confirm_one)
        confirm_all.clicked.connect(do_confirm_all)
        export.clicked.connect(do_export)
        copy_query.clicked.connect(do_copy_query)
        pubmed_execute.clicked.connect(do_pubmed_execute)
        next_button.clicked.connect(on_next)
        select_all.clicked.connect(lambda: _set_all_list_items_selected(candidate_list, True))
        clear_selection.clicked.connect(lambda: _set_all_list_items_selected(candidate_list, False))
        import_selected.clicked.connect(do_import_selected)
        ignore_batch.clicked.connect(do_ignore_batch)
        candidate_list.currentRowChanged.connect(lambda _row: update_candidate_detail())
        database_list.setCurrentRow(0)
        update_candidate_detail()
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
        filter_row.addWidget(search_input, 2)
        filter_row.addWidget(source_filter)
        filter_row.addWidget(missing_filter)
        filter_row.addWidget(export_summary)
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
        library_layout.addWidget(detail)
        library_layout.addWidget(note_input)
        library_layout.addWidget(save_note)
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

        def do_export_summary() -> None:
            path = _export_literature_library_summary(project_dir, diagnostics=library_diagnostics, records=records)
            _show_message(f"已导出：{path}")

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
        export_summary.clicked.connect(do_export_summary)
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
        next_button = QPushButton("下一步：全文管理")
        next_button.setObjectName("metaSecondaryButton")
        action_row = QHBoxLayout()
        action_row.addWidget(build_queue)
        action_row.addWidget(save_decision)
        action_row.addWidget(generate_deduped)
        action_row.addWidget(build_screening_queue)
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
        screening_record_list = QListWidget()
        screening_record_list.setObjectName("metaScreeningWorkspaceRecordList")
        screening_record_list.setMinimumWidth(360)
        for record in screening_records:
            decision_payload = screening_decisions_by_record.get(str(record.get("record_id", "")), {})
            decision_label = _screening_decision_label(str(decision_payload.get("decision") or record.get("decision") or DECISION_NOT_SCREENED))
            item = QListWidgetItem(
                "\n".join(
                    [
                        str(record.get("title") or "Untitled"),
                        " · ".join(
                            part
                            for part in (
                                _first_author(record),
                                str(record.get("year") or ""),
                                str(record.get("journal") or ""),
                                decision_label,
                            )
                            if part
                        ),
                    ]
                )
            )
            item.setData(Qt.ItemDataRole.UserRole, str(record.get("record_id", "")))
            screening_record_list.addItem(item)
        screening_content.addWidget(screening_record_list, 1)
        screening_panel = _card("当前文献库")
        screening_panel_layout = screening_panel.layout()
        screening_detail = QTextEdit()
        screening_detail.setObjectName("metaScreeningWorkspaceRecordDetail")
        screening_detail.setReadOnly(True)
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
        save_screening_decision = QPushButton("保存筛选决定")
        save_screening_decision.setObjectName("metaPrimaryButton")
        screening_panel_layout.addWidget(QLabel("文献信息"))
        screening_panel_layout.addWidget(screening_detail)
        screening_panel_layout.addWidget(QLabel("筛选决策"))
        screening_panel_layout.addWidget(screening_decision)
        screening_panel_layout.addWidget(QLabel("排除原因"))
        screening_panel_layout.addWidget(screening_reason)
        screening_panel_layout.addWidget(screening_notes)
        screening_panel_layout.addWidget(save_screening_decision)
        screening_content.addWidget(screening_panel, 2)
        screening_layout.addLayout(screening_content)
        screening_layout.addWidget(QLabel("下一步：全文管理"))
        layout.addWidget(screening_card)
        layout.addWidget(_fulltext_management_page(project_dir, on_refresh=on_refresh, on_next=on_next))
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

        def selected_screening_record_id() -> str:
            item = screening_record_list.currentItem()
            return str(item.data(Qt.ItemDataRole.UserRole)) if item is not None else ""

        def refresh_screening_detail(index: int = 0) -> None:
            if index < 0 or index >= len(screening_records):
                screening_detail.setPlainText("暂无待筛选文献。")
                return
            record = screening_records[index]
            decision_payload = screening_decisions_by_record.get(str(record.get("record_id", "")), {})
            screening_detail.setPlainText(_screening_record_user_detail(record, decision_payload))

        def do_save_screening_decision() -> None:
            record_id = selected_screening_record_id()
            if not record_id:
                _show_message("请选择文献")
                return
            selected_decision = str(screening_decision.currentData() or DECISION_NOT_SCREENED)
            selected_reason = str(screening_reason.currentData() or "")
            if selected_decision == DECISION_EXCLUDE and not selected_reason:
                _show_message("排除必须选择排除原因")
                return
            result = screening_service.save_decision(
                project_dir,
                record_id=record_id,
                decision=selected_decision,
                actor="reviewer",
                exclusion_reason_code=selected_reason,
                notes=screening_notes.toPlainText(),
            )
            _show_message(result.message)
            on_refresh()

        group_list.currentRowChanged.connect(refresh_group_detail)
        record_selector.currentIndexChanged.connect(update_preview)
        screening_record_list.currentRowChanged.connect(refresh_screening_detail)
        build_queue.clicked.connect(do_build_queue)
        save_decision.clicked.connect(do_save_decision)
        generate_deduped.clicked.connect(do_generate_deduped)
        build_screening_queue.clicked.connect(do_build_screening_queue)
        save_screening_decision.clicked.connect(do_save_screening_decision)
        next_button.clicked.connect(on_next)
        group_list.setCurrentRow(0 if groups else -1)
        refresh_group_detail(group_list.currentRow())
        screening_record_list.setCurrentRow(0 if screening_records else -1)
        refresh_screening_detail(screening_record_list.currentRow())
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
        layout.addWidget(_page_header("去重与筛选", "从去重结果进入逐篇人工筛选；AI 只能作为 suggestion。", "人工决定"))
        layout.addWidget(_info_card("筛选摘要", [f"队列文献：{len(records)}", f"人工决定：{len(decisions)}", "PRISMA screened/excluded 只来自用户决定。"], object_name="metaScreeningSummary"))
        actions = QHBoxLayout()
        build_queue = QPushButton("生成筛选队列")
        save_decision = QPushButton("保存人工决定")
        next_button = QPushButton("下一步：数据提取与质量评价")
        for button in (build_queue, save_decision, next_button):
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
        for label, value in (("纳入", "include"), ("排除", "exclude"), ("不确定", "uncertain"), ("需复核", "needs_review")):
            decision.addItem(label, value)
        reason = QComboBox()
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

        record_list.currentRowChanged.connect(update_detail)
        build_queue.clicked.connect(do_build_queue)
        save_decision.clicked.connect(do_save_decision)
        next_button.clicked.connect(on_next)
        record_list.setCurrentRow(0 if records else -1)
        update_detail(record_list.currentRow())
        return frame


    def _fulltext_management_page(project_dir: Path, *, on_refresh: Callable[[], None], on_next: Callable[[], None]) -> QFrame:
        management = FullTextManagementService()
        eligibility = FullTextEligibilityService()
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
        mark_unavailable = QPushButton("标记无法获取")
        confirm_fulltext = QPushButton("全文确认")
        save_status = QPushButton("保存全文状态")
        save_eligibility = QPushButton("保存全文筛选")
        next_button = QPushButton("下一步：数据提取")
        for button in (build_registry, attach_pdf, mark_unavailable, confirm_fulltext, save_status, save_eligibility, next_button):
            button.setObjectName("metaSecondaryButton")
            buttons.addWidget(button)
        build_registry.setObjectName("metaPrimaryButton")
        buttons.addStretch(1)
        layout.addLayout(buttons)
        record_list = QListWidget()
        record_list.setObjectName("metaFulltextRecordList")
        source_records = records or candidates
        for record in source_records:
            record_id = getattr(record, "record_id", "")
            title = getattr(record, "title", "")
            candidate = candidates_by_id.get(record_id)
            author_year = _author_year_text(getattr(record, "authors", "") or getattr(candidate, "authors", ""), getattr(record, "year", "") or getattr(candidate, "year", ""))
            journal = getattr(record, "journal", "") or getattr(candidate, "journal", "") or "期刊未记录"
            screening_decision = getattr(record, "source_screening_decision", "") or getattr(candidate, "screening_decision", "") or "未记录"
            status = getattr(record, "fulltext_status", getattr(record, "eligibility_status", ""))
            status_label = FULLTEXT_STATUS_LABELS_ZH.get(status, status or "未记录")
            file_label = management.safe_file_label(record) if hasattr(record, "pdf_path") else "未登记全文文件"
            exclusion_reason = getattr(record, "fulltext_exclusion_reason", "") or getattr(record, "unavailable_reason", "") or getattr(candidate, "exclusion_reason", "")
            reason_label = FULLTEXT_EXCLUSION_REASON_LABELS_ZH.get(exclusion_reason, "无全文排除原因")
            item = QListWidgetItem(
                "\n".join(
                    [
                        title or "未命名文献",
                        f"{author_year} · {journal}",
                        f"标题摘要决定：{_screening_decision_label(screening_decision)} · 全文状态：{status_label}",
                        f"{file_label} · 排除原因：{reason_label}",
                    ]
                )
            )
            item.setData(Qt.ItemDataRole.UserRole, record_id)
            record_list.addItem(item)
        layout.addWidget(record_list)
        form = _card("人工全文状态")
        form_layout = form.layout()
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

        def selected_record_id() -> str:
            item = record_list.currentItem()
            return str(item.data(Qt.ItemDataRole.UserRole)) if item is not None else ""

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

        build_registry.clicked.connect(do_build_registry)
        attach_pdf.clicked.connect(do_attach_pdf)
        mark_unavailable.clicked.connect(do_mark_unavailable)
        confirm_fulltext.clicked.connect(do_confirm_fulltext)
        save_status.clicked.connect(do_save_status)
        save_eligibility.clicked.connect(do_save_eligibility)
        next_button.clicked.connect(on_next)
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
        next_button = QPushButton("下一步：质量评价")
        for button in (create_unit, create_row, save_structured, complete_row, confirm_structured, mark_missing, export_template, export_current, import_csv, next_button):
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
        layout.addWidget(_quality_assessment_page(project_dir, on_refresh=on_refresh, on_next=on_next))
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

        create_unit.clicked.connect(do_create_unit)
        create_row.clicked.connect(do_create_row)
        save_structured.clicked.connect(do_save_structured)
        complete_row.clicked.connect(do_complete_row)
        confirm_structured.clicked.connect(do_confirm_structured)
        mark_missing.clicked.connect(do_mark_missing)
        export_template.clicked.connect(lambda: _show_message(service.export_empty_template_csv(project_dir, actor="reviewer").message))
        export_current.clicked.connect(lambda: _show_message(service.export_current_csv(project_dir, actor="reviewer").message))
        import_csv.clicked.connect(do_import_csv)
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
        next_button = QPushButton("下一步：分析计划")
        for button in (save_draft, complete, export_csv, next_button):
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
        next_button = QPushButton("下一步：结果与报告")
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
        next_button = QPushButton("下一步：报告导出")
        next_button.setObjectName("metaSecondaryButton")
        buttons.addWidget(run)
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

        run.clicked.connect(do_run)
        next_button.clicked.connect(on_next)
        return frame


    def _figure_results_page(project_dir: Path, *, on_next: Callable[[], None]) -> QFrame:
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
            values = [artifact.figure_id, artifact.figure_type, artifact.output_format, artifact.output_path]
            for col, value in enumerate(values):
                table.setItem(row, col, QTableWidgetItem(str(value)))
        layout.addWidget(table)
        next_button = QPushButton("下一步：PRISMA")
        next_button.setObjectName("metaSecondaryButton")
        next_button.clicked.connect(on_next)
        layout.addWidget(next_button)
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
        next_button = QPushButton("下一步：报告导出")
        for button in (collect, export_md, next_button):
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

        collect.clicked.connect(do_collect)
        export_md.clicked.connect(do_export_md)
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
        next_button = QPushButton("返回项目首页")
        for button in (build_md, show_location, export_html, export_docx, next_button):
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
            _show_message("报告位置：项目 reports 目录。未自动打开外部应用。")

        def do_export_html() -> None:
            result = PublicationExportService().export_html_report(project_dir)
            _show_message(result.message)
            on_refresh()

        def do_export_docx() -> None:
            result = PublicationExportService().export_word_report(project_dir)
            _show_message(result.message)
            on_refresh()

        build_md.clicked.connect(do_build_md)
        show_location.clicked.connect(do_show_location)
        export_html.clicked.connect(do_export_html)
        export_docx.clicked.connect(do_export_docx)
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
            "pico_workspace": "研究问题与 PICO",
            "search_strategy": "检索策略",
            "literature_import": "文献库与导入",
            "screening": "去重与筛选",
            "extraction_quality": "数据提取与质量评价",
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
        return "当前版本支持检索式生成与本地导入，不执行联网检索。"


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


    def _pubmed_preview_summary(preview: dict[str, object]) -> str:
        if not preview:
            return "尚无 PubMed 候选文献。请先确认 PubMed 检索式并执行 testing-level 检索。"
        candidates = _items_from_payload(preview, "candidates")
        with_abstract = len([item for item in candidates if str(item.get("abstract", "")).strip()])
        return f"候选 {len(candidates)} 条；有摘要 {with_abstract} 条；preview={preview.get('preview_id', '')}"


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
            return "暂无候选文献。"
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
