from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from app.shared.feature_availability import FeatureAvailability, FeatureAvailabilityStatus, list_features
from app.shared.feature_status import FeatureItem, feature_item_from_availability
from app.shared.ui_components.primitives import make_status_chip
from app.version import APP_VERSION

from app.meta_analysis.project_workspace import MetaProjectSummary, open_meta_analysis_project
from app.meta_analysis.version import META_ANALYSIS_MAINLINE_CONTRACT_VERSION

try:
    from PySide6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )
except Exception:  # pragma: no cover
    QWidget = None  # type: ignore[assignment]


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
                "Developer Preview / testing：目标 IA 只展示结构和状态边界。"
                "AI suggestion 仅为人工可审核建议，不自动生成结论；当前不启用 Network Meta，不声明生产级系统综述能力。"
            )
            boundary.setObjectName("metaTargetIABoundary")
            boundary.setWordWrap(True)
            layout.addWidget(boundary)

            self._target_interaction_status = QLabel("")
            self._target_interaction_status.setObjectName("metaTargetInteractionStatus")
            self._target_interaction_status.setWordWrap(True)
            layout.addWidget(self._target_interaction_status)

            page_row = QHBoxLayout()
            page_row.setSpacing(8)
            for page in meta_target_ia_pages():
                item = QPushButton(page.label)
                item.setObjectName("metaTargetIANavItem")
                item.setCheckable(True)
                item.setProperty("pageKey", page.key)
                item.setProperty("pageGroup", page.page_group)
                item.setProperty("flowIndex", page.flow_index)
                item.setProperty("statusKey", page.status_key)
                item.setProperty("interactionMode", "select_only")
                item.setProperty("formalActionEnabled", False)
                item.setToolTip(page.boundary)
                item.clicked.connect(lambda _checked=False, key=page.key: self.show_target_ia_page(key))
                self._target_ia_buttons[page.key] = item
                page_row.addWidget(item)
            layout.addLayout(page_row)

            self._active_type_status = QLabel("")
            self._active_type_status.setObjectName("metaActiveTypeInteractionStatus")
            self._active_type_status.setWordWrap(True)
            layout.addWidget(self._active_type_status)

            type_groups: dict[str, list[MetaActiveType]] = {}
            for meta_type in meta_active_types_v1():
                type_groups.setdefault(meta_type.group, []).append(meta_type)
            for group, meta_types in type_groups.items():
                group_label = QLabel(group)
                group_label.setObjectName("metaTypeGroupTitle")
                group_label.setStyleSheet("font-weight: 700;")
                layout.addWidget(group_label)
                type_row = QHBoxLayout()
                type_row.setSpacing(8)
                for meta_type in meta_types:
                    card = QFrame()
                    card.setObjectName("metaActiveTypeCard")
                    card.setProperty("typeId", meta_type.type_id)
                    card.setProperty("statusKey", meta_type.status_key)
                    card.setStyleSheet("QFrame#metaActiveTypeCard { border: 1px solid #CBD5E1; border-radius: 8px; background: #FFFFFF; }")
                    card_layout = QVBoxLayout(card)
                    card_layout.setContentsMargins(10, 8, 10, 8)
                    card_layout.setSpacing(6)
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
                    select.setProperty("statusKey", meta_type.status_key)
                    select.setProperty("interactionMode", meta_type.interaction_mode)
                    select.setProperty("formalActionEnabled", False)
                    select.clicked.connect(lambda _checked=False, type_id=meta_type.type_id: self.select_active_meta_type(type_id))
                    self._active_type_buttons[meta_type.type_id] = select
                    card_layout.addWidget(type_id)
                    card_layout.addWidget(label)
                    card_layout.addWidget(effect)
                    card_layout.addWidget(select)
                    type_row.addWidget(card)
                layout.addLayout(type_row)

            planned = QLabel("Network Meta：planned only / not enabled，不属于当前 active Meta 类型。")
            planned.setObjectName("metaNetworkMetaBoundary")
            planned.setProperty("typeId", "network_meta_analysis")
            planned.setProperty("statusKey", "planned")
            planned.setProperty("formalActionEnabled", False)
            planned.setWordWrap(True)
            planned.setStyleSheet("border: 1px solid #F5D899; border-radius: 6px; padding: 6px 8px; background: #FFF7E6;")
            layout.addWidget(planned)
            network_button = QPushButton("Network Meta planned")
            network_button.setObjectName("metaNetworkMetaPlannedButton")
            network_button.setProperty("typeId", "network_meta_analysis")
            network_button.setProperty("statusKey", "planned")
            network_button.setProperty("interactionMode", "planned_disabled")
            network_button.setProperty("formalActionEnabled", False)
            network_button.setEnabled(False)
            layout.addWidget(network_button)
            self._sync_target_interaction_state()
            self._sync_type_interaction_state()
            return frame

        def _sync_target_interaction_state(self) -> None:
            pages = {page.key: page for page in meta_target_ia_pages()}
            current = pages[self._current_target_page_key]
            for key, button in self._target_ia_buttons.items():
                button.setChecked(key == self._current_target_page_key)
            if hasattr(self, "_target_interaction_status"):
                self._target_interaction_status.setText(
                    f"Selected target page: {current.key} · {current.status_key} · shell selection only. {current.boundary}"
                )

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
