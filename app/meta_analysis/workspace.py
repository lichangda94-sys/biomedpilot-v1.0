from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from app.shared.feature_availability import FeatureAvailability, FeatureAvailabilityStatus, list_features
from app.shared.feature_status import FeatureItem, feature_item_from_availability
from app.shared.result_report_export_shell import make_result_report_export_adoption_panel
from app.shared.semantic_keys import FeatureStatusKey, ModuleKey, PageKey
from app.shared.ui_components.primitives import make_status_chip
from app.version import APP_VERSION

from app.meta_analysis.project_workspace import MetaProjectSummary, open_meta_analysis_project
from app.meta_analysis.version import META_ANALYSIS_MAINLINE_CONTRACT_VERSION

try:
    from PySide6.QtCore import QSize
    from PySide6.QtWidgets import (
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QPushButton,
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
    features = list_features("meta_analysis")
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
    version_status = f"{APP_VERSION} · {META_ANALYSIS_MAINLINE_CONTRACT_VERSION}"
    return MetaWorkspaceLayoutState(
        title="Meta 分析模块",
        status_label=version_status,
        description="主线保留 Meta 入口和项目壳；具体 PICO、检索、筛选、提取、统计和报告功能在 dev/meta-analysis 开发。",
        navigation_items=(
            MetaWorkspaceNavigationItem("project_home", "Meta 项目首页", "项目绑定、状态摘要和分支边界说明。", "workflow_home"),
            MetaWorkspaceNavigationItem("project_contract", "项目契约", "创建和打开 Meta 项目的最小 manifest contract。", "project_contract"),
            MetaWorkspaceNavigationItem("dev_branch", "功能开发线", "完整 Meta workflow 位于 dev/meta-analysis。", "dev_branch"),
        ),
        default_page_key="workflow_home",
        testing_notice="当前 mainline 只保留 Meta 模块壳和接口；完整功能请在 dev/meta-analysis 分支开发和验收。",
        version_status_label=version_status,
    )


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
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
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

        def show_step(self, page_key: str) -> None:
            if page_key in self._page_keys:
                self._navigation_list.setCurrentRow(self._page_keys.index(page_key))

        def show_target_ia_page(self, page_key: str) -> None:
            if page_key not in {page.key for page in meta_target_ia_pages()}:
                return
            self._current_target_page_key = page_key
            self._sync_target_interaction_state()

        def select_active_meta_type(self, type_id: str) -> None:
            if type_id not in {meta_type.type_id for meta_type in meta_active_types_v1()}:
                return
            self._selected_active_meta_type_id = type_id
            self._sync_type_interaction_state()

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
            title = QLabel("Meta 分析模块")
            title.setObjectName("metaWorkspaceTitle")
            title.setStyleSheet("font-size: 22px; font-weight: 700;")
            subtitle = QLabel("mainline 入口与项目壳；完整功能开发保留在 dev/meta-analysis。")
            subtitle.setObjectName("metaWorkspaceSubtitle")
            title_col.addWidget(title)
            title_col.addWidget(subtitle)
            header_layout.addLayout(title_col, 1)
            if self._on_back is not None:
                back = QPushButton("返回模块首页")
                back.setObjectName("metaBackButton")
                back.clicked.connect(self._on_back)
                header_layout.addWidget(back)
            root.addWidget(header)
            root.addWidget(self._build_target_ia_shell())

            self._status_label = QLabel("")
            self._status_label.setObjectName("metaProjectStatus")
            root.addWidget(self._status_label)

            body = QHBoxLayout()
            self._navigation_list = QListWidget()
            self._navigation_list.setObjectName("metaWorkflowStepList")
            self._navigation_list.setMaximumWidth(260)
            self._page_stack = QStackedWidget()
            self._page_stack.setObjectName("metaCurrentStepWorkspace")
            body.addWidget(self._navigation_list)
            body.addWidget(self._page_stack, 1)
            root.addLayout(body, 1)

            self._navigation_list.currentRowChanged.connect(self._page_stack.setCurrentIndex)
            self._build_pages()
            self._refresh_summary()

        def target_ia_page_keys(self) -> tuple[str, ...]:
            return tuple(page.key for page in meta_target_ia_pages())

        def active_meta_type_ids(self) -> tuple[str, ...]:
            return tuple(meta_type.type_id for meta_type in meta_active_types_v1())

        def _build_target_ia_shell(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("metaTargetIAShell")
            frame.setStyleSheet("QFrame#metaTargetIAShell { border: 1px solid #D8DEE9; border-radius: 8px; background: #F8FAFC; }")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(16, 14, 16, 14)
            layout.setSpacing(10)

            title = QLabel("Meta Analysis / Meta 分析目标 IA shell")
            title.setObjectName("metaTargetIATitle")
            title.setStyleSheet("font-weight: 750;")
            layout.addWidget(title)

            boundary = QLabel(
                "定义研究问题，选择适合的 Meta 分析类型，并按流程进入检索、筛选、全文管理、质量评价与报告草稿。"
            )
            boundary.setObjectName("metaTargetIABoundary")
            boundary.setWordWrap(True)
            layout.addWidget(boundary)
            preview = make_status_chip("Developer Preview / 本地测试版", status_key="developer_preview")
            preview.setObjectName("metaDeveloperPreviewChip")
            layout.addWidget(preview)
            self._result_export_panel = make_result_report_export_adoption_panel(module="meta_analysis")
            layout.addWidget(self._result_export_panel)

            self._target_interaction_status = QLabel("")
            self._target_interaction_status.setObjectName("metaTargetInteractionStatus")
            self._target_interaction_status.setWordWrap(True)
            layout.addWidget(self._target_interaction_status)

            page_grid = QGridLayout()
            page_grid.setHorizontalSpacing(10)
            page_grid.setVerticalSpacing(10)
            for index, page in enumerate(meta_target_ia_pages()):
                item = QPushButton(_meta_flow_button_text(page))
                item.setObjectName("metaTargetIANavItem")
                item.setCheckable(True)
                item.setMinimumHeight(74)
                item.setMinimumWidth(138)
                item.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                item.setProperty("pageKey", page.key)
                item.setProperty("pageGroup", page.page_group)
                item.setProperty("flowIndex", page.flow_index)
                item.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
                item.setProperty("statusKey", page.status_key)
                item.setProperty("semanticKey", _META_PAGE_SEMANTIC_KEYS[page.key])
                item.setProperty("statusSemanticKey", _META_STATUS_SEMANTIC_KEYS[page.status_key])
                item.setProperty("currentStep", False)
                item.setProperty("interactionMode", "select_only")
                item.setProperty("formalActionEnabled", False)
                item.setToolTip(page.boundary)
                item.setStyleSheet(_META_FLOW_BUTTON_STYLESHEET)
                _apply_meta_page_icon(item, _META_PAGE_SEMANTIC_KEYS[page.key], size=22)
                item.clicked.connect(lambda _checked=False, key=page.key: self.show_target_ia_page(key))
                self._target_ia_buttons[page.key] = item
                page_grid.addWidget(item, index // 4, index % 4)
            layout.addLayout(page_grid)

            self._project_home_panel = self._build_project_home_runtime_panel()
            layout.addWidget(self._project_home_panel)

            self._fulltext_extraction_panel = self._build_fulltext_extraction_panel()
            layout.addWidget(self._fulltext_extraction_panel)

            self._risk_of_bias_panel = self._build_risk_of_bias_panel()
            layout.addWidget(self._risk_of_bias_panel)

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
            active_type_layout = QVBoxLayout(self._active_type_section)
            active_type_layout.setContentsMargins(0, 0, 0, 0)
            active_type_layout.setSpacing(10)

            draft_panel = self._build_question_type_draft_panel()
            active_type_layout.addWidget(draft_panel)

            self._active_type_status = QLabel("")
            self._active_type_status.setObjectName("metaActiveTypeInteractionStatus")
            self._active_type_status.setWordWrap(True)
            active_type_layout.addWidget(self._active_type_status)

            type_groups: dict[str, list[MetaActiveType]] = {}
            for meta_type in meta_active_types_v1():
                type_groups.setdefault(meta_type.group, []).append(meta_type)
            for group, meta_types in type_groups.items():
                group_label = QLabel(group)
                group_label.setObjectName("metaTypeGroupTitle")
                group_label.setStyleSheet("font-weight: 700;")
                active_type_layout.addWidget(group_label)
                type_row = QHBoxLayout()
                type_row.setSpacing(8)
                for meta_type in meta_types:
                    card = QFrame()
                    card.setObjectName("metaActiveTypeCard")
                    card.setProperty("typeId", meta_type.type_id)
                    card.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
                    card.setProperty("statusKey", meta_type.status_key)
                    card.setProperty("semanticKey", FeatureStatusKey.TESTING.value)
                    card.setMinimumHeight(154)
                    card.setMinimumWidth(240)
                    card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                    card.setStyleSheet("QFrame#metaActiveTypeCard { border: 1px solid #CBD5E1; border-radius: 8px; background: #FFFFFF; }")
                    card_layout = QVBoxLayout(card)
                    card_layout.setContentsMargins(12, 10, 12, 10)
                    card_layout.setSpacing(8)
                    card_layout.addWidget(make_status_chip(status_key=meta_type.status_key))
                    type_id = QLabel(meta_type.type_id)
                    type_id.setObjectName("metaActiveTypeId")
                    type_id.setWordWrap(True)
                    label = QLabel(meta_type.label_zh)
                    label.setObjectName("metaActiveTypeLabel")
                    label.setWordWrap(True)
                    effect = QLabel(meta_type.effect_size)
                    effect.setObjectName("metaActiveTypeEffect")
                    effect.setWordWrap(True)
                    select = QPushButton("选择类型")
                    select.setObjectName("metaActiveTypeSelectButton")
                    select.setCheckable(True)
                    select.setProperty("typeId", meta_type.type_id)
                    select.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
                    select.setProperty("statusKey", meta_type.status_key)
                    select.setProperty("semanticKey", FeatureStatusKey.TESTING.value)
                    select.setProperty("interactionMode", meta_type.interaction_mode)
                    select.setProperty("formalActionEnabled", False)
                    select.setMinimumHeight(34)
                    select.clicked.connect(lambda _checked=False, type_id=meta_type.type_id: self.select_active_meta_type(type_id))
                    self._active_type_buttons[meta_type.type_id] = select
                    card_layout.addWidget(type_id)
                    card_layout.addWidget(label)
                    card_layout.addWidget(effect)
                    card_layout.addStretch(1)
                    card_layout.addWidget(select)
                    type_row.addWidget(card)
                active_type_layout.addLayout(type_row)

            planned = QLabel("Network Meta：planned only / not enabled，不属于当前 active Meta 类型。")
            planned.setObjectName("metaNetworkMetaBoundary")
            planned.setProperty("typeId", "network_meta_analysis")
            planned.setProperty("statusKey", "planned")
            planned.setProperty("formalActionEnabled", False)
            planned.setWordWrap(True)
            planned.setStyleSheet("border: 1px solid #F5D899; border-radius: 6px; padding: 6px 8px; background: #FFF7E6;")
            active_type_layout.addWidget(planned)
            network_button = QPushButton("Network Meta planned")
            network_button.setObjectName("metaNetworkMetaPlannedButton")
            network_button.setProperty("typeId", "network_meta_analysis")
            network_button.setProperty("statusKey", "planned")
            network_button.setProperty("interactionMode", "planned_disabled")
            network_button.setProperty("formalActionEnabled", False)
            network_button.setEnabled(False)
            active_type_layout.addWidget(network_button)

            next_search = QPushButton("下一步：检索策略 / Next: Search Strategy")
            next_search.setObjectName("metaQuestionNextSearchStrategyButton")
            next_search.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
            next_search.setProperty("pageKey", "question_meta_type")
            next_search.setProperty("targetPageKey", "search_strategy")
            next_search.setProperty("actionSemantic", "navigation_only")
            next_search.setProperty("formalActionEnabled", False)
            next_search.setMinimumHeight(36)
            next_search.clicked.connect(lambda _checked=False: self.show_target_ia_page("search_strategy"))
            active_type_layout.addWidget(next_search)
            layout.addWidget(self._active_type_section)

            self._search_strategy_panel = self._build_search_strategy_panel()
            layout.addWidget(self._search_strategy_panel)

            self._reference_dedup_panel = self._build_reference_dedup_panel()
            layout.addWidget(self._reference_dedup_panel)

            self._screening_panel = self._build_screening_panel()
            layout.addWidget(self._screening_panel)

            self._result_review_panel = self._build_result_review_panel()
            layout.addWidget(self._result_review_panel)

            self._report_export_gate_panel = self._build_report_export_gate_panel()
            layout.addWidget(self._report_export_gate_panel)

            self._sync_target_interaction_state()
            self._sync_type_interaction_state()
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
            frame.setStyleSheet("QFrame#metaProjectHomeRuntimePanel { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(10)

            title = QLabel("Meta Project Home / 项目首页")
            title.setObjectName("metaProjectHomeRuntimeTitle")
            title.setStyleSheet("font-weight: 750;")
            layout.addWidget(title)

            chip_row = QHBoxLayout()
            for object_name, text, status_key in (
                ("metaProjectHomeDeveloperPreviewChip", "Developer Preview / 本地测试版", "developer_preview"),
                ("metaProjectHomeEnglishFirstChip", "English-first processing", "testing"),
                ("metaProjectHomeAISuggestionChip", "AI suggestion only", "testing"),
                ("metaProjectHomeReportNotReadyChip", "Report not ready", "blocked"),
            ):
                chip = make_status_chip(text, status_key=status_key)
                chip.setObjectName(object_name)
                chip_row.addWidget(chip)
            chip_row.addStretch(1)
            layout.addLayout(chip_row)

            overview_title = QLabel("Workflow overview")
            overview_title.setObjectName("metaProjectHomeWorkflowOverviewTitle")
            overview_title.setStyleSheet("font-weight: 700;")
            layout.addWidget(overview_title)
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
            layout.addWidget(workflow)

            summary_title = QLabel("Project Summary")
            summary_title.setObjectName("metaProjectHomeSummaryTitle")
            summary_title.setStyleSheet("font-weight: 700;")
            layout.addWidget(summary_title)
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
            layout.addWidget(summary)
            return frame

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
            frame.setStyleSheet("QFrame#metaQuestionTypeDraftPanel { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(10)

            title = QLabel("Question & Meta Type / 研究问题与 Meta 类型")
            title.setObjectName("metaQuestionTypeRuntimeTitle")
            title.setStyleSheet("font-weight: 750;")
            layout.addWidget(title)

            chinese = QLabel("中文工作问题：脂联素表达与甲状腺癌预后或诊断价值之间的关系。")
            chinese.setObjectName("metaChineseWorkingQuestionDraft")
            chinese.setWordWrap(True)
            english = QLabel("English question draft: Is adiponectin associated with thyroid cancer diagnosis or prognosis in human studies?")
            english.setObjectName("metaEnglishQuestionDraft")
            english.setWordWrap(True)
            layout.addWidget(chinese)
            layout.addWidget(english)

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
            layout.addWidget(pico)

            suggested = QLabel("Suggested Meta type draft: Prognostic factor meta or Biomarker expression difference meta. AI suggestion is advisory only.")
            suggested.setObjectName("metaSuggestedMetaTypeDraft")
            suggested.setWordWrap(True)
            suggested.setStyleSheet("border: 1px solid #BFD7FF; border-radius: 6px; padding: 6px 8px; background: #EFF6FF;")
            layout.addWidget(suggested)

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
            layout.addLayout(card_grid)
            return frame

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
            frame.setStyleSheet("QFrame#metaSearchStrategyRuntimePanel { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(10)

            title = QLabel("Search Strategy / 检索策略")
            title.setObjectName("metaSearchStrategyRuntimeTitle")
            title.setStyleSheet("font-weight: 750;")
            layout.addWidget(title)

            status_row = QHBoxLayout()
            for object_name, text, status_key in (
                ("metaSearchEnglishFirstChip", "English query draft", "testing"),
                ("metaSearchLocalDraftChip", "local draft only", "shell_only"),
                ("metaSearchNoExecutionChip", "search execution disabled", "blocked"),
            ):
                chip = make_status_chip(text, status_key=status_key)
                chip.setObjectName(object_name)
                status_row.addWidget(chip)
            status_row.addStretch(1)
            layout.addLayout(status_row)

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
            layout.addWidget(term_table)

            logic = QLabel("Boolean logic preview: Disease AND Biomarker AND Outcome")
            logic.setObjectName("metaSearchBooleanLogicPreview")
            logic.setWordWrap(True)
            layout.addWidget(logic)

            query = QLabel(
                'PubMed-style query draft: ("thyroid cancer"[Title/Abstract] OR "thyroid carcinoma"[Title/Abstract] OR '
                '"thyroid neoplasm"[Title/Abstract]) AND ("adiponectin"[Title/Abstract] OR "ADIPOQ"[Title/Abstract]) '
                'AND ("prognosis"[Title/Abstract] OR "survival"[Title/Abstract] OR "recurrence"[Title/Abstract] OR '
                '"clinicopathological"[Title/Abstract])'
            )
            query.setObjectName("metaSearchPubMedStyleQueryDraft")
            query.setProperty("queryState", "draft_only")
            query.setWordWrap(True)
            query.setStyleSheet("border: 1px solid #BFD7FF; border-radius: 6px; padding: 8px; background: #EFF6FF;")
            layout.addWidget(query)

            database_scope = QFrame()
            database_scope.setObjectName("metaDatabaseDraftScope")
            database_scope.setProperty("selectionState", "draft_scope_only")
            database_layout = QHBoxLayout(database_scope)
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
                item.setMinimumHeight(32)
                database_layout.addWidget(item)
            database_layout.addStretch(1)
            layout.addWidget(database_scope)

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
            layout.addLayout(action_row)
            return frame

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
            frame.setStyleSheet("QFrame#metaReferenceDedupRuntimePanel { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
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
            frame.setStyleSheet("QFrame#metaScreeningRuntimePanel { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(10)

            title = QLabel("Screening / 文献筛选")
            title.setObjectName("metaScreeningRuntimeTitle")
            title.setStyleSheet("font-weight: 750;")
            layout.addWidget(title)

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
            layout.addWidget(counts)

            body = QHBoxLayout()
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
            body.addWidget(queue, 2)

            detail = QFrame()
            detail.setObjectName("metaScreeningReferenceDetail")
            detail.setStyleSheet("QFrame#metaScreeningReferenceDetail { border: 1px solid #CBD5E1; border-radius: 8px; background: #F8FAFC; }")
            detail_layout = QVBoxLayout(detail)
            detail_layout.setContentsMargins(10, 8, 10, 8)
            for text in (
                "Reference detail: REF-001",
                "Title/abstract review state: draft only",
                "Reason draft: biomarker association in target population",
            ):
                label = QLabel(text)
                label.setObjectName("metaScreeningReferenceDetailLabel")
                label.setWordWrap(True)
                detail_layout.addWidget(label)
            body.addWidget(detail, 1)
            layout.addLayout(body)

            decision_row = QHBoxLayout()
            for decision_id, text in (
                ("include_draft", "Include draft"),
                ("exclude_draft", "Exclude draft"),
                ("uncertain", "Uncertain"),
                ("need_full_text", "Need full text"),
            ):
                button = QPushButton(text)
                button.setObjectName("metaScreeningDecisionDraftButton")
                button.setProperty("decisionId", decision_id)
                button.setProperty("decisionState", "draft_only")
                button.setProperty("formalActionEnabled", False)
                button.setMinimumHeight(34)
                decision_row.addWidget(button)
            layout.addLayout(decision_row)

            ai_card = QLabel("AI suggestion: likely_include, confidence 0.72. Advisory only; reviewer remains the authority.")
            ai_card.setObjectName("metaScreeningAISuggestionCard")
            ai_card.setProperty("aiBoundary", "advisory_only")
            ai_card.setWordWrap(True)
            ai_card.setStyleSheet("border: 1px solid #BFD7FF; border-radius: 6px; padding: 8px; background: #EFF6FF;")
            layout.addWidget(ai_card)

            save_draft = QPushButton("Save Draft Decision")
            save_draft.setObjectName("metaSaveDraftScreeningDecisionButton")
            save_draft.setProperty("actionSemantic", "draft_only")
            save_draft.setProperty("formalActionEnabled", False)
            save_draft.setMinimumHeight(34)
            layout.addWidget(save_draft)
            return frame

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
            frame.setMinimumHeight(360)
            frame.setStyleSheet("QFrame#metaFulltextExtractionPanel { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(10)

            tab_row = QHBoxLayout()
            tab_row.setSpacing(8)
            self._fulltext_extraction_tabs: dict[str, QPushButton] = {}
            for index, tab in enumerate(("全文管理", "提取表设计", "提取完成核查", "历史记录")):
                button = QPushButton(tab)
                button.setObjectName("metaFulltextExtractionTab")
                button.setCheckable(True)
                button.setChecked(index == 0)
                button.setMinimumHeight(34)
                button.setMinimumWidth(92)
                button.setProperty("moduleKey", ModuleKey.META_ANALYSIS.value)
                button.setProperty("pageKey", "fulltext_extraction")
                button.setProperty("tabKey", tab)
                button.clicked.connect(lambda _checked=False, tab_key=tab: self._select_fulltext_extraction_tab(tab_key))
                self._fulltext_extraction_tabs[tab] = button
                tab_row.addWidget(button)
            tab_row.addStretch(1)
            layout.addLayout(tab_row)

            self._fulltext_management_body = QFrame()
            self._fulltext_management_body.setObjectName("metaFulltextManagementBody")
            self._fulltext_management_body.setMinimumHeight(260)
            self._fulltext_management_body.setStyleSheet("QFrame#metaFulltextManagementBody { border: 1px solid #E2E8F0; border-radius: 8px; background: #F8FAFC; }")
            management_layout = QVBoxLayout(self._fulltext_management_body)
            management_layout.setContentsMargins(12, 10, 12, 10)
            management_layout.setSpacing(8)
            management_title = QLabel("全文管理")
            management_title.setObjectName("metaFulltextManagementTitle")
            management_title.setStyleSheet("font-weight: 700;")
            management_layout.addWidget(management_title)
            for text in (
                "全文文件：待绑定 PDF / HTML；当前不自动抽取正文。",
                "提取准备：仅做 shell 级状态核查，不生成研究数据。",
                "下一步：确认全文齐备后进入提取表设计与人工提取阶段。",
            ):
                label = QLabel(text)
                label.setObjectName("metaFulltextManagementStatus")
                label.setWordWrap(True)
                management_layout.addWidget(label)
            fulltext_status = _readonly_table(
                "metaFulltextStatusPreviewTable",
                ("ref_id", "full_text_state", "extraction_state"),
                (
                    ("REF-001", "file pending", "not_started"),
                    ("REF-002", "needs retrieval", "not_started"),
                    ("REF-004", "not requested", "not_started"),
                ),
            )
            fulltext_status.setMinimumHeight(92)
            management_layout.addWidget(fulltext_status)
            management_layout.addStretch(1)
            layout.addWidget(self._fulltext_management_body)

            self._extraction_design_body = QFrame()
            self._extraction_design_body.setObjectName("metaExtractionDesignBody")
            self._extraction_design_body.setStyleSheet("QFrame#metaExtractionDesignBody { border: 1px solid #E2E8F0; border-radius: 8px; background: #FFFFFF; }")
            body = QHBoxLayout(self._extraction_design_body)
            body.setContentsMargins(12, 10, 12, 10)
            body.setSpacing(12)
            structure = QFrame()
            structure.setObjectName("metaExtractionStructurePanel")
            structure.setMinimumWidth(260)
            structure.setStyleSheet("QFrame#metaExtractionStructurePanel { border: 1px solid #E2E8F0; border-radius: 8px; background: #F8FAFC; }")
            structure_layout = QVBoxLayout(structure)
            structure_layout.setContentsMargins(12, 10, 12, 10)
            structure_layout.setSpacing(8)
            structure_title = QLabel("提取表结构")
            structure_title.setObjectName("metaExtractionStructureTitle")
            structure_title.setStyleSheet("font-weight: 700;")
            structure_layout.addWidget(structure_title)
            for section, count in (
                ("研究基本信息", "6"),
                ("研究对象与分组", "4"),
                ("干预 / 暴露", "3"),
                ("对照措施", "2"),
                ("结局指标", "5"),
                ("效应量数据（二分类）", "8"),
                ("备注与来源", "3"),
                ("复核字段", "2"),
            ):
                label = QLabel(f"{section}  {count}")
                label.setObjectName("metaExtractionStructureItem")
                label.setProperty("sectionKey", section)
                label.setMinimumHeight(24)
                structure_layout.addWidget(label)
            body.addWidget(structure, 1)

            fields = QFrame()
            fields.setObjectName("metaExtractionFieldStructure")
            fields.setMinimumWidth(620)
            fields.setMinimumHeight(260)
            fields.setStyleSheet("QFrame#metaExtractionFieldStructure { border: 1px solid #E2E8F0; border-radius: 8px; background: #FFFFFF; }")
            fields_layout = QVBoxLayout(fields)
            fields_layout.setContentsMargins(12, 10, 12, 10)
            fields_layout.setSpacing(8)
            fields_title = QLabel("Draft extraction fields（Biomarker / Prognostic Meta）")
            fields_title.setObjectName("metaExtractionFieldTitle")
            fields_title.setStyleSheet("font-weight: 700;")
            fields_layout.addWidget(fields_title)
            legacy_contract = QLabel("当前提取表字段（Binary Outcome Meta 专用）")
            legacy_contract.setObjectName("metaExtractionLegacyContractLabel")
            legacy_contract.setProperty("legacyCompatibilityOnly", True)
            fields_layout.addWidget(legacy_contract)
            field_grid = QGridLayout()
            field_grid.setHorizontalSpacing(10)
            field_grid.setVerticalSpacing(6)
            for column, header in enumerate(("field", "example / draft note", "required", "state", "analysis use")):
                header_label = QLabel(header)
                header_label.setObjectName("metaExtractionFieldHeader")
                header_label.setStyleSheet("font-weight: 700; color: #64748B;")
                header_label.setMinimumHeight(26)
                field_grid.addWidget(header_label, 0, column)
            for row, values in enumerate(
                (
                    ("first_author", "Zhang", "yes", "draft extraction", "-"),
                    ("year", "2020", "yes", "draft extraction", "-"),
                    ("研究设计", "observational cohort / case-control", "yes", "draft extraction", "yes"),
                    ("cancer_type", "thyroid carcinoma", "yes", "reviewer confirmed later", "yes"),
                    ("marker_name", "adiponectin / ADIPOQ", "yes", "draft extraction", "yes"),
                    ("effect_measure", "HR", "yes", "draft extraction", "yes"),
                    ("effect_value", "1.48 mockup-only / draft extraction", "yes", "not final", "yes"),
                    ("ci_lower", "1.05 mockup-only / draft extraction", "yes", "not final", "yes"),
                    ("ci_upper", "2.10 mockup-only / draft extraction", "yes", "not final", "yes"),
                    ("adjusted_model", "multivariable", "optional", "draft extraction", "yes"),
                    ("outcome_name", "overall survival", "yes", "draft extraction", "yes"),
                ),
                start=1,
            ):
                for column, value in enumerate(values):
                    label = QLabel(value)
                    label.setObjectName("metaExtractionFieldCell")
                    label.setMinimumHeight(24)
                    field_grid.addWidget(label, row, column)
            fields_layout.addLayout(field_grid)
            body.addWidget(fields, 3)
            layout.addWidget(self._extraction_design_body)

            self._extraction_action_bar = QFrame()
            self._extraction_action_bar.setObjectName("metaExtractionActionBar")
            action_row = QHBoxLayout(self._extraction_action_bar)
            action_row.setContentsMargins(0, 0, 0, 0)
            save = QPushButton("保存提取表设计 - adapter needed")
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
            back.setEnabled(False)
            action_row.addWidget(save)
            action_row.addStretch(1)
            action_row.addWidget(mark_draft)
            action_row.addWidget(back)
            layout.addWidget(self._extraction_action_bar)
            self._select_fulltext_extraction_tab("全文管理")
            return frame

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
            frame.setStyleSheet("QFrame#metaRiskOfBiasRuntimePanel { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
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
            frame.setStyleSheet("QFrame#metaResultReviewRuntimePanel { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(10)

            title = QLabel("Result Review + Report-ready Gate / 结果复核与报告门控")
            title.setObjectName("metaResultReviewRuntimeTitle")
            title.setStyleSheet("font-weight: 750;")
            layout.addWidget(title)

            review_notice = QLabel("人工复核集中在此页面：前置草稿、提取和 RoB 预览不能升级为正式结果。")
            review_notice.setObjectName("metaResultReviewHumanReviewNotice")
            review_notice.setProperty("reviewBoundary", "human_review_required")
            review_notice.setWordWrap(True)
            review_notice.setStyleSheet("border: 1px solid #F5D899; border-radius: 6px; padding: 8px; background: #FFF7E6;")
            layout.addWidget(review_notice)

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
            layout.addWidget(readiness)

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
            layout.addWidget(pairwise)

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
            layout.addWidget(blockers)

            generate = QPushButton("Generate Report disabled")
            generate.setObjectName("metaGenerateReportDisabledButton")
            generate.setProperty("actionSemantic", "disabled_report_gate")
            generate.setProperty("formalActionEnabled", False)
            generate.setProperty("fileWriteAllowed", False)
            generate.setEnabled(False)
            generate.setMinimumHeight(34)
            layout.addWidget(generate)
            return frame

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
            frame.setStyleSheet("QFrame#metaReportExportGateRuntimePanel { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(10)

            title = QLabel("Report Export / 报告导出门控")
            title.setObjectName("metaReportExportGateRuntimeTitle")
            title.setStyleSheet("font-weight: 750;")
            layout.addWidget(title)

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
            for key, button in self._target_ia_buttons.items():
                is_current = key == self._current_target_page_key
                button.setChecked(is_current)
                button.setProperty("currentStep", is_current)
                _refresh_dynamic_style(button)
            if hasattr(self, "_target_interaction_status"):
                self._target_interaction_status.setText(
                    f"当前页面：{current.label} · {current.status_key}"
                )
            if hasattr(self, "_fulltext_extraction_panel"):
                self._fulltext_extraction_panel.setVisible(self._current_target_page_key == "fulltext_extraction")
            if hasattr(self, "_risk_of_bias_panel"):
                self._risk_of_bias_panel.setVisible(self._current_target_page_key == "quality_assessment")
            if hasattr(self, "_project_home_panel"):
                self._project_home_panel.setVisible(self._current_target_page_key == "project_home")
            if hasattr(self, "_active_type_section"):
                self._active_type_section.setVisible(self._current_target_page_key == "question_meta_type")
            if hasattr(self, "_search_strategy_panel"):
                self._search_strategy_panel.setVisible(self._current_target_page_key == "search_strategy")
            if hasattr(self, "_reference_dedup_panel"):
                self._reference_dedup_panel.setVisible(self._current_target_page_key == "import_dedup")
            if hasattr(self, "_screening_panel"):
                self._screening_panel.setVisible(self._current_target_page_key == "screening")
            if hasattr(self, "_result_review_panel"):
                self._result_review_panel.setVisible(self._current_target_page_key == "result_report")
            if hasattr(self, "_report_export_gate_panel"):
                self._report_export_gate_panel.setVisible(self._current_target_page_key == "report_export")
            if hasattr(self, "_result_export_panel"):
                self._result_export_panel.setVisible(self._current_target_page_key in {"result_report", "report_export"})

        def _sync_type_interaction_state(self) -> None:
            types = {meta_type.type_id: meta_type for meta_type in meta_active_types_v1()}
            current = types[self._selected_active_meta_type_id]
            for type_id, button in self._active_type_buttons.items():
                button.setChecked(type_id == self._selected_active_meta_type_id)
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
