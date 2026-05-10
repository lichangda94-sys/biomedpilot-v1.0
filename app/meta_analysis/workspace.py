from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import json
from pathlib import Path

from app.shared.feature_availability import FeatureAvailability, list_features
from app.shared.feature_status import FeatureItem, feature_item_from_availability
from app.shared.storage import default_storage_root
from app.version import APP_VERSION

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
        description="用中文串联 Meta 分析主流程：状态可见、按钮清楚、下一步明确；未完成能力保持 testing-level / 待开发。",
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
    summaries.extend(_legacy_import_batch_summaries(root))
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


def _legacy_import_batch_summaries(root: Path) -> list[ImportBatchQualitySummary]:
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


try:
    from PySide6.QtWidgets import (
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
    QComboBox = QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QListWidget = QListWidgetItem = QMessageBox = QPlainTextEdit = QPushButton = QScrollArea = QStackedWidget = QTableWidget = QTableWidgetItem = QTextEdit = QVBoxLayout = QWidget = None
    Qt = None


if QWidget is not None:
    from app.meta_analysis.search.pubmed_candidates_handoff_service import PubMedCandidatesHandoffService
    from app.meta_analysis.search.search_strategy_builder_service import SearchStrategyBuilderService
    from app.meta_analysis.services.literature_library_service import LiteratureLibraryService
    from app.meta_analysis.services.multisource_literature_import_service import MultiSourceLiteratureImportService
    from app.meta_analysis.services.pico_workspace_service import PICOWorkspaceService

    class MetaAnalysisWorkspaceWidget(QWidget):
        def __init__(self, on_back: Callable[[], None] | None = None) -> None:
            super().__init__()
            self.setObjectName("metaWorkspace")
            self.setStyleSheet(_meta_workspace_stylesheet())
            self._layout_state = meta_workspace_layout_state()
            self._on_back = on_back
            self._current_project_record = None
            self._current_project_dir: Path | None = None
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
            status = QLabel("Developer Preview")
            status.setObjectName("metaStatusBadge")
            global_layout.addWidget(status)
            notice = QLabel("testing-level；所有研究判断需要人工确认。")
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
            self._workflow_nav.setFixedWidth(280)
            workflow_layout = QVBoxLayout(self._workflow_nav)
            workflow_layout.setContentsMargins(14, 18, 14, 18)
            workflow_layout.setSpacing(10)
            workflow_title = QLabel("Meta 工作流")
            workflow_title.setObjectName("metaPanelTitle")
            workflow_layout.addWidget(workflow_title)
            self._navigation_list = QListWidget()
            self._navigation_list.setObjectName("metaWorkflowStepList")
            workflow_layout.addWidget(self._navigation_list, 1)

            self._workspace = QFrame()
            self._workspace.setObjectName("metaCurrentStepWorkspace")
            workspace_layout = QVBoxLayout(self._workspace)
            workspace_layout.setContentsMargins(18, 18, 18, 18)
            workspace_layout.setSpacing(0)
            self._page_stack = QStackedWidget()
            self._page_stack.setObjectName("metaCurrentStepStack")
            workspace_layout.addWidget(self._page_stack, 1)

            self._navigation_list.currentRowChanged.connect(self._page_stack.setCurrentIndex)
            root.addWidget(self._global_nav)
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
            self._rebuild_pages()

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
                item = QListWidgetItem(f"{step.order}. {step.title_zh}\n{step.status}")
                item.setToolTip(f"{step.primary_action_zh}\n{step.next_action_zh}")
                self._navigation_list.addItem(item)
                self._page_stack.addWidget(_scroll_page(self._page_for_step(step, state)))
                self._page_keys.append(step.route_key)
            self._navigation_list.setCurrentRow(0)

        def _project_dir_for_state(self) -> Path:
            return self._current_project_dir or (default_storage_root() / "projects" / "__meta_empty_state__" / "meta_analysis")

        def _update_project_summary(self) -> None:
            if self._current_project_dir is None:
                self._project_summary_label.setText("当前项目：未选择\n进入项目后显示真实 Meta 工作区。")
                return
            name = getattr(self._current_project_record, "name", "") or self._current_project_dir.parent.name
            self._project_summary_label.setText(f"当前项目：{name}\n{self._current_project_dir}")

        def _page_for_step(self, step: MetaWorkflowStepState, state) -> QWidget:
            if self._current_project_dir is None:
                return _no_project_page(step, on_go_pico=lambda: self.show_step("pico_workspace"))
            project_dir = self._current_project_dir
            if step.route_key == "workflow_home":
                return _project_home_page(state, project_dir, on_go_pico=lambda: self.show_step("pico_workspace"))
            if step.route_key == "pico_workspace":
                return _pico_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("search_strategy"))
            if step.route_key == "search_strategy":
                return _search_strategy_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("literature_acquisition"))
            if step.route_key == "literature_acquisition":
                return _literature_acquisition_page(project_dir, on_refresh=self._rebuild_pages, on_next=lambda: self.show_step("literature_library"))
            if step.route_key == "literature_library":
                return _literature_library_page(project_dir)
            return _placeholder_step_page(step)

    def _feature_row(feature: FeatureAvailability) -> QFrame:
        frame = QFrame()
        frame.setObjectName("metaCard")
        layout = QVBoxLayout(frame)
        title = QLabel(feature.display_label())
        title.setObjectName("metaCardTitle")
        detail = QLabel(feature.description)
        detail.setWordWrap(True)
        source = QLabel(f"legacy 来源：{feature.legacy_source or '统一壳子占位'}")
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


    def _project_home_page(state, project_dir: Path, *, on_go_pico: Callable[[], None]) -> QFrame:
        frame = QFrame()
        frame.setObjectName("metaProjectHomePage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(_page_header("Meta 项目首页", "项目概览、当前阶段和下一步。", "Developer Preview"))
        steps = {step.step_id: step for step in state.steps}
        home = steps.get("project_home")
        pico = steps.get("pico_workspace")
        library = steps.get("literature_library")
        plan = steps.get("analysis_plan")
        overview_lines = [
            f"项目目录：{project_dir}",
            "当前阶段：" + ("尚未开始，请先进入研究问题" if pico and pico.status == "未开始" else f"研究问题：{pico.status if pico else '未开始'}"),
            f"文献库：{library.artifact_summary if library else 'records=0'}",
            f"分析计划：{plan.status if plan else '未开始'}",
        ]
        layout.addWidget(_info_card("项目概览", overview_lines, object_name="metaProjectOverviewCard"))
        completed = len([step for step in state.steps if step.status in {"已确认", "已生成", "已有记录", "已有项目", "已有草稿", "有待审核建议", "已有人工评分"}])
        layout.addWidget(_info_card("流程进度", [f"已产生状态的步骤：{completed}/{state.step_count}", f"下一步：{state.next_recommended_step_id}"], object_name="metaProgressCard"))
        warnings = [warning for step in state.steps for warning in step.warnings][:5]
        layout.addWidget(_info_card("最近 warnings", warnings or ["暂无 warning"], object_name="metaWarningsCard"))
        action_card = _card("下一步操作")
        action_layout = action_card.layout()
        next_button = QPushButton("进入研究问题")
        next_button.setObjectName("metaPrimaryButton")
        next_button.clicked.connect(on_go_pico)
        action_layout.addWidget(QLabel("从中文研究问题开始，生成并确认 PICO / PICOS / PECO。"))
        action_layout.addWidget(next_button)
        layout.addWidget(action_card)
        layout.addWidget(_developer_details(_state_debug_text(state)))
        layout.addStretch(1)
        return frame


    def _no_project_page(step: MetaWorkflowStepState, *, on_go_pico: Callable[[], None]) -> QFrame:
        frame = QFrame()
        frame.setObjectName("metaNoProjectPage")
        layout = QVBoxLayout(frame)
        layout.addWidget(_page_header(step.title_zh, "当前未绑定 Meta 项目。", "空状态"))
        layout.addWidget(_info_card("尚未开始", ["请先从桌面主 APP 新建或打开 Meta 项目。", "空项目状态不会写入任何业务文件。"]))
        if step.route_key == "workflow_home":
            button = QPushButton("进入研究问题")
            button.setObjectName("metaSecondaryButton")
            button.clicked.connect(on_go_pico)
            layout.addWidget(button)
        layout.addStretch(1)
        return frame


    def _pico_page(project_dir: Path, *, on_refresh: Callable[[], None], on_next: Callable[[], None]) -> QFrame:
        service = PICOWorkspaceService()
        draft = service.load_draft(project_dir)
        confirmed = service.load_confirmed(project_dir)
        frame = QFrame()
        frame.setObjectName("metaPicoPage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(_page_header("中文研究问题 / PICO", "生成草稿、编辑字段，再由用户确认。", "需要人工确认"))
        input_card = _card("输入研究问题")
        input_layout = input_card.layout()
        question = QPlainTextEdit()
        question.setObjectName("metaPicoQuestionInput")
        question.setPlaceholderText("例如：高血压患者降压药对卒中风险的影响")
        if draft:
            question.setPlainText(draft.research_question_original)
        input_layout.addWidget(question)
        generate = QPushButton("生成 PICO 草稿")
        generate.setObjectName("metaPrimaryButton")
        input_layout.addWidget(generate)
        layout.addWidget(input_card)

        draft_fields = {
            "pico_mode": QLineEdit(draft.pico_mode if draft else "pico"),
            "population": QLineEdit(draft.population if draft else ""),
            "intervention": QLineEdit(draft.intervention if draft else ""),
            "exposure": QLineEdit(draft.exposure if draft else ""),
            "comparator": QLineEdit(draft.comparator if draft else ""),
            "outcome": QLineEdit(draft.outcome if draft else ""),
            "study_design": QLineEdit(draft.study_design if draft else ""),
        }
        draft_card = _card("PICO / PICOS / PECO 草稿")
        draft_layout = draft_card.layout()
        if draft:
            draft_layout.addWidget(_kv_label("Draft ID", draft.protocol_id))
            for label, key in (("模式", "pico_mode"), ("P 研究对象", "population"), ("I 干预", "intervention"), ("E 暴露", "exposure"), ("C 对照", "comparator"), ("O 结局", "outcome"), ("S 研究类型", "study_design")):
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
            ]
        layout.addWidget(_info_card("已确认研究问题", confirmed_lines, object_name="metaConfirmedProtocolCard"))
        layout.addWidget(_developer_details(f"project_dir={project_dir}\ndraft={bool(draft)} confirmed={bool(confirmed)}"))
        layout.addStretch(1)

        def do_generate() -> None:
            text = question.toPlainText().strip()
            if not text:
                _show_message("请输入研究问题")
                return
            service.generate_draft(project_dir, text, actor="reviewer")
            on_refresh()

        def do_save() -> None:
            if not service.load_draft(project_dir):
                _show_message("请先生成草稿")
                return
            service.edit_draft(
                project_dir,
                actor="reviewer",
                updates={key: field.text().strip() for key, field in draft_fields.items()},
            )
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
                overrides={
                    "confirmed_pico_mode": draft_fields["pico_mode"].text().strip(),
                    "confirmed_population": draft_fields["population"].text().strip(),
                    "confirmed_intervention_or_exposure": draft_fields["exposure"].text().strip() or draft_fields["intervention"].text().strip(),
                    "confirmed_comparator": draft_fields["comparator"].text().strip(),
                    "confirmed_outcomes": draft_fields["outcome"].text().strip(),
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
        frame = QFrame()
        frame.setObjectName("metaSearchStrategyPage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(_page_header("检索策略", "基于已确认研究问题生成多数据库检索式。", "draft-only"))
        if not (project_dir / "protocol" / "pico_workspace_confirmed.json").exists():
            layout.addWidget(_info_card("请先确认研究问题", ["没有 confirmed protocol 时不能生成正式检索策略草稿。"]))
            layout.addStretch(1)
            return frame
        actions = _card("主操作")
        action_layout = actions.layout()
        generate = QPushButton("生成检索策略")
        generate.setObjectName("metaPrimaryButton")
        save_edit = QPushButton("保存当前编辑")
        confirm = QPushButton("确认检索式")
        export = QPushButton("导出 Markdown / TXT")
        next_button = QPushButton("下一步：文献获取")
        for button in (save_edit, confirm, export, next_button):
            button.setObjectName("metaSecondaryButton")
        row = QHBoxLayout()
        for button in (generate, save_edit, confirm, export, next_button):
            row.addWidget(button)
        row.addStretch(1)
        action_layout.addLayout(row)
        layout.addWidget(actions)
        selector = QComboBox()
        selector.setObjectName("metaSearchDraftSelector")
        editor = QPlainTextEdit()
        editor.setObjectName("metaSearchQueryEditor")
        for draft in drafts:
            selector.addItem(f"{_database_label(draft.database)} · {draft.search_execution_status}", draft.search_strategy_id)
        if drafts:
            editor.setPlainText(drafts[0].boolean_query)
        draft_card = _card("多数据库 query draft")
        draft_layout = draft_card.layout()
        draft_layout.addWidget(selector)
        draft_layout.addWidget(editor)
        if drafts:
            for draft in drafts:
                status = "PubMed 可执行入口" if draft.database == "pubmed" else "draft-only / 手动检索"
                draft_layout.addWidget(_info_card(_database_label(draft.database), [status, draft.boolean_query[:600] or "暂无 query"], object_name="metaQueryDraftCard"))
        else:
            draft_layout.addWidget(QLabel("尚未生成检索策略草稿。"))
        layout.addWidget(draft_card)
        layout.addWidget(_info_card("已确认检索式", [f"confirmed={len(confirmed)}", "确认后不会自动执行检索；PubMed 仍需明确入口。"], object_name="metaConfirmedSearchCard"))
        pubmed_hint = QPushButton("PubMed 可执行入口（本轮不自动执行）")
        pubmed_hint.setObjectName("metaSecondaryButton")
        pubmed_hint.setEnabled(False)
        layout.addWidget(pubmed_hint)
        layout.addWidget(_developer_details(f"drafts={len(drafts)} confirmed={len(confirmed)} project_dir={project_dir}"))
        layout.addStretch(1)

        def update_editor(index: int) -> None:
            if index < 0 or index >= len(drafts):
                return
            editor.setPlainText(drafts[index].boolean_query)

        def do_generate() -> None:
            try:
                service.generate_from_confirmed_protocol(project_dir, actor="reviewer")
            except Exception as exc:
                _show_message(str(exc))
                return
            on_refresh()

        def do_save_edit() -> None:
            strategy_id = selector.currentData()
            if not strategy_id:
                _show_message("请先生成检索策略")
                return
            service.edit_draft(project_dir, search_strategy_id=str(strategy_id), updates={"boolean_query": editor.toPlainText()}, actor="reviewer")
            on_refresh()

        def do_confirm() -> None:
            try:
                service.confirm_strategies(project_dir, actor="reviewer")
            except Exception as exc:
                _show_message(str(exc))
                return
            on_refresh()

        def do_export() -> None:
            try:
                md_path, txt_path = service.export_drafts(project_dir)
            except Exception as exc:
                _show_message(str(exc))
                return
            _show_message(f"已导出：{md_path.name} / {txt_path.name}")

        selector.currentIndexChanged.connect(update_editor)
        generate.clicked.connect(do_generate)
        save_edit.clicked.connect(do_save_edit)
        confirm.clicked.connect(do_confirm)
        export.clicked.connect(do_export)
        next_button.clicked.connect(on_next)
        return frame


    def _literature_acquisition_page(project_dir: Path, *, on_refresh: Callable[[], None], on_next: Callable[[], None]) -> QFrame:
        preview_paths = sorted((project_dir / "protocol" / "pubmed_candidates").glob("*_candidates_preview.json"))
        library = LiteratureLibraryService()
        manifest = library.read_manifest(project_dir)
        frame = QFrame()
        frame.setObjectName("metaLiteratureAcquisitionPage")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.addWidget(_page_header("文献获取", "PubMed candidates 和本地 NBIB/RIS/CSV 导入。", "不自动筛选"))
        candidate_card = _card("PubMed candidates preview")
        candidate_layout = candidate_card.layout()
        preview_selector = QComboBox()
        preview_selector.setObjectName("metaPubMedPreviewSelector")
        candidate_list = QListWidget()
        candidate_list.setObjectName("metaPubMedCandidateList")
        candidate_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        previews = [_load_json_object(path) for path in preview_paths]
        for path, preview in zip(preview_paths, previews):
            preview_id = str(preview.get("preview_id") or path.name.replace("_candidates_preview.json", ""))
            preview_selector.addItem(f"{preview_id} · {len(_items_from_payload(preview, 'candidates'))} 条", preview_id)
        candidate_layout.addWidget(preview_selector)
        candidate_layout.addWidget(candidate_list)
        import_selected = QPushButton("导入选中文献")
        import_selected.setObjectName("metaPrimaryButton")
        candidate_layout.addWidget(import_selected)
        layout.addWidget(candidate_card)
        local_card = _card("本地文献导入")
        local_layout = local_card.layout()
        local_layout.addWidget(QLabel("支持 NBIB / RIS / CSV。导入后进入统一文献库，不进入筛选。"))
        import_file = QPushButton("选择文件导入")
        import_file.setObjectName("metaSecondaryButton")
        local_layout.addWidget(import_file)
        layout.addWidget(local_card)
        layout.addWidget(_info_card("Import batch 摘要", [f"total_records={manifest.get('total_records', 0)}", f"total_batches={manifest.get('total_batches', 0)}", f"sources={manifest.get('source_counts', {})}"], object_name="metaImportBatchSummary"))
        next_button = QPushButton("下一步：文献库")
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
                candidate_list.addItem(item)

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
            filename, _ = QFileDialog.getOpenFileName(frame, "选择文献文件", str(project_dir), "Literature (*.nbib *.ris *.csv);;All files (*)")
            if not filename:
                return
            result = MultiSourceLiteratureImportService().import_file(project_dir, source_path=Path(filename), source_format="auto")
            _show_message(result.message)
            on_refresh()

        preview_selector.currentIndexChanged.connect(load_preview)
        import_selected.clicked.connect(do_import_selected)
        import_file.clicked.connect(do_import_file)
        next_button.clicked.connect(on_next)
        load_preview(0)
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


    def _developer_details(text: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("metaDeveloperDetails")
        layout = QVBoxLayout(frame)
        button = QPushButton("开发详情")
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


    def _default_meta_type(candidates: tuple[dict[str, object], ...]) -> str:
        for candidate in candidates:
            value = str(candidate.get("meta_type") or candidate.get("type") or candidate.get("id") or candidate.get("name") or "")
            if value and "coming_soon" not in value:
                return value
        return "treatment_comparative_meta"


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


    def _items_from_payload(payload: dict[str, object], key: str) -> list[dict[str, object]]:
        value = payload.get(key)
        if isinstance(value, list):
            return [dict(item) for item in value if isinstance(item, dict)]
        return []


    def _record_detail(record: dict[str, object]) -> str:
        return "\n".join(
            [
                f"题名：{record.get('title', '')}",
                f"作者：{record.get('authors', '')}",
                f"期刊：{record.get('journal', '')}",
                f"年份：{record.get('year', '')}",
                f"DOI：{record.get('doi', '')}",
                f"PMID：{record.get('pmid', '')}",
                f"来源：{record.get('source_type', '')}",
                f"摘要：{record.get('abstract', '')}",
            ]
        )


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


    def _meta_workspace_stylesheet() -> str:
        return """
        QWidget#metaWorkspace { background: #F5F7F9; color: #111827; }
        QFrame#metaGlobalNav, QFrame#metaWorkflowNav { background: #FFFFFF; border-right: 1px solid #D8DEE9; }
        QFrame#metaCurrentStepWorkspace { background: #F5F7F9; }
        QFrame#metaPageHeader, QFrame#metaCard, QFrame#metaInfoCard, QFrame#metaProjectOverviewCard,
        QFrame#metaProgressCard, QFrame#metaWarningsCard, QFrame#metaLibrarySummary,
        QFrame#metaLibraryDiagnostics, QFrame#metaImportBatchSummary, QFrame#metaQueryDraftCard,
        QFrame#metaConfirmedProtocolCard, QFrame#metaConfirmedSearchCard {
            background: #FFFFFF;
            border: 1px solid #D8DEE9;
            border-radius: 8px;
        }
        QFrame#metaDeveloperDetails { background: transparent; border: none; }
        QLabel#metaSideTitle { font-size: 22px; font-weight: 700; }
        QLabel#metaPanelTitle { font-size: 16px; font-weight: 700; }
        QLabel#metaPageTitle { font-size: 22px; font-weight: 700; }
        QLabel#metaCardTitle { font-size: 15px; font-weight: 700; }
        QLabel#metaMutedText, QLabel#metaCardBody { color: #4B5563; }
        QLabel#metaWarningText { color: #92400E; font-weight: 600; }
        QLabel#metaStatusBadge {
            color: #0F766E;
            background: #E6FFFB;
            border: 1px solid #99F6E4;
            border-radius: 8px;
            padding: 4px 8px;
            font-weight: 700;
        }
        QListWidget#metaWorkflowStepList {
            background: #F8FAFC;
            border: 1px solid #E5E7EB;
            border-radius: 8px;
        }
        QPushButton#metaPrimaryButton {
            background: #0F766E;
            color: #FFFFFF;
            border: 1px solid #0F766E;
            border-radius: 8px;
            padding: 8px 12px;
            font-weight: 700;
        }
        QPushButton#metaSecondaryButton {
            background: #FFFFFF;
            color: #111827;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            padding: 8px 12px;
        }
        """

else:

    class MetaAnalysisWorkspaceWidget:  # type: ignore[no-redef]
        pass
