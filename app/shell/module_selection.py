from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QSize, Signal, Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.app_identity import MODULE_ICON_PATHS, load_module_pixmap, load_ui02_module_selection_icon, load_ui02_module_selection_pixmap
from app.shell.dashboard import DashboardModel
from app.shell.login import LocalSession
from app.shared.semantic_keys import BrandKey, ModuleKey, NavKey
from app.shared.ui_components import ProjectRecentItem, make_action_button, make_project_recent_table, make_status_chip
from app.ui_style_tokens import SPACING, module_selection_stylesheet


class ModuleEntryCard(QFrame):
    clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)


class ModuleSelectionWidget(QWidget):
    open_bioinformatics_requested = Signal()
    open_meta_analysis_requested = Signal()
    open_labtools_requested = Signal()
    logout_requested = Signal()

    def __init__(
        self,
        *,
        dashboard: DashboardModel,
        session: LocalSession | None = None,
        on_open_bioinformatics: Callable[[], None] | None = None,
        on_open_meta_analysis: Callable[[], None] | None = None,
        on_open_labtools: Callable[[], None] | None = None,
        on_logout: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._dashboard = dashboard
        self._session = session
        self.setObjectName("moduleSelectionPage")
        self.setProperty("designTokenSet", "dashboard_target_figma_make")
        self.setStyleSheet(module_selection_stylesheet())
        self._build_ui()
        if on_open_bioinformatics is not None:
            self.open_bioinformatics_requested.connect(on_open_bioinformatics)
        if on_open_meta_analysis is not None:
            self.open_meta_analysis_requested.connect(on_open_meta_analysis)
        if on_open_labtools is not None:
            self.open_labtools_requested.connect(on_open_labtools)
        if on_logout is not None:
            self.logout_requested.connect(on_logout)
        self.set_session(session)

    def session_display(self) -> dict[str, str]:
        if self._session is None:
            return {
                "username": "未登录本地测试用户",
                "tier": "Developer Preview",
                "license_status": "local_testing",
            }
        return {
            "username": self._session.username,
            "tier": self._session.tier,
            "license_status": self._session.license_status,
        }

    def set_session(self, session: LocalSession | None) -> None:
        self._session = session
        display = self.session_display()
        self._user_badge.setText(f"当前用户：{display['username']}")
        self._tier_label.setText("Developer Preview / 本地测试版")
        self._license_label.setText(f"测试状态：{display['license_status']}")

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("moduleSelectionScrollArea")
        content = QWidget()
        content.setObjectName("moduleSelectionContent")
        root = QVBoxLayout(content)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(SPACING["lg"])

        root.addWidget(self._build_header())
        root.addWidget(self._build_metric_strip())
        root.addWidget(self._build_module_panel())

        lower_row = QHBoxLayout()
        lower_row.setSpacing(SPACING["lg"])
        lower_row.addWidget(self._build_recent_projects_card(), 2)
        lower_row.addWidget(self._build_activity_card(), 1)
        root.addLayout(lower_row)
        root.addStretch(1)
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _build_header(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("dashboardHeader")
        frame.setProperty("uiPrimitive", "dashboard_hero")
        frame.setProperty("designReference", "figma_make_dashboard_target")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(SPACING["xl"])

        icon = self._ui02_icon_label("dashboard", 42)
        icon.setObjectName("dashboardHeroIcon")
        layout.addWidget(icon, 0, Qt.AlignTop)
        title_col = QVBoxLayout()
        title_col.setSpacing(SPACING["sm"])
        eyebrow = QLabel("BioMedPilot Dashboard")
        eyebrow.setObjectName("dashboardEyebrow")
        eyebrow.setProperty("semanticKey", BrandKey.SECONDARY.value)
        title = QLabel("医研智析工作台")
        title.setObjectName("dashboardTitle")
        title.setProperty("semanticKey", BrandKey.PRIMARY.value)
        subtitle = QLabel("集中进入生信分析、Meta 分析与 LabTools，并保持本地项目、任务和测试状态可见。")
        subtitle.setObjectName("dashboardSubtitle")
        subtitle.setProperty("semanticKey", BrandKey.SECONDARY.value)
        subtitle.setWordWrap(True)
        title_col.addWidget(eyebrow)
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        status_row = QHBoxLayout()
        status_row.setSpacing(SPACING["sm"])
        preview = make_status_chip("Developer Preview", status_key="developer_preview")
        preview.setObjectName("previewBadge")
        status_row.addWidget(preview)
        status_row.addWidget(make_status_chip("Local workspace", status_key="testing"))
        status_row.addStretch(1)
        title_col.addLayout(status_row)
        layout.addLayout(title_col, 1)

        layout.addWidget(self._header_icon_button("设置", "settings"), 0, Qt.AlignTop)
        layout.addWidget(self._header_icon_button("测试说明", "developer_preview"), 0, Qt.AlignTop)
        self._user_badge = QLabel("")
        self._user_badge.setObjectName("sessionBadge")
        self._user_badge.setAlignment(Qt.AlignCenter)
        self._user_badge.setMinimumHeight(42)
        self._user_badge.setMaximumHeight(42)
        self._user_badge.setMinimumWidth(158)
        layout.addWidget(self._user_badge, 0, Qt.AlignTop)
        self._tier_label = QLabel("Developer Preview / 本地测试版")
        self._tier_label.setObjectName("previewBadge")
        self._tier_label.setVisible(False)
        self._license_label = QLabel("")
        self._license_label.setVisible(False)
        return frame

    def _build_metric_strip(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("dashboardMetricStrip")
        frame.setProperty("uiPrimitive", "dashboard_metric_strip")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["md"])
        layout.addWidget(
            self._metric_card(
                "近期项目",
                str(len(self._dashboard.recent_projects)),
                "最近打开的本地研究项目",
                "recent_projects",
            )
        )
        layout.addWidget(
            self._metric_card(
                "模块入口",
                "3",
                "Bioinformatics · Meta · LabTools",
                "workspace",
            )
        )
        layout.addWidget(
            self._metric_card(
                "本地状态",
                self._environment_summary(),
                "依赖检测只作为启动前提示",
                "local_environment",
            )
        )
        return frame

    def _environment_summary(self) -> str:
        return "PySide Ready" if self._dashboard.environment.pyside6_available else "Console fallback"

    def _metric_card(self, label: str, value: str, caption: str, icon_key: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("dashboardMetricCard")
        frame.setProperty("uiPrimitive", "dashboard_metric_card")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(SPACING["md"])
        layout.addWidget(self._ui02_icon_label(icon_key, 24))
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        label_widget = QLabel(label)
        label_widget.setObjectName("dashboardMetricLabel")
        value_widget = QLabel(value)
        value_widget.setObjectName("dashboardMetricValue")
        value_widget.setWordWrap(True)
        caption_widget = QLabel(caption)
        caption_widget.setObjectName("dashboardMetricCaption")
        caption_widget.setWordWrap(True)
        text_col.addWidget(label_widget)
        text_col.addWidget(value_widget)
        text_col.addWidget(caption_widget)
        layout.addLayout(text_col, 1)
        return frame

    def _build_module_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("dashboardModulePanel")
        frame.setProperty("uiPrimitive", "dashboard_module_panel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["xl"], SPACING["lg"], SPACING["xl"], SPACING["xl"])
        layout.setSpacing(SPACING["lg"])
        layout.addLayout(self._title_row("研究模块 / Workspaces", "workspace"))

        module_grid = QGridLayout()
        module_grid.setContentsMargins(0, 0, 0, 0)
        module_grid.setHorizontalSpacing(SPACING["md"])
        module_grid.setVerticalSpacing(SPACING["md"])
        module_grid.addWidget(
            self._module_card(
                title="Bioinformatics / 生信分析",
                english_title="Bioinformatics",
                description="项目创建、数据来源、检查准备、分组设计、分析任务与报告出口。",
                button_text="进入生信分析",
                object_name="bioModuleButton",
                icon_key="bioinformatics",
                module_key=ModuleKey.BIOINFORMATICS.value,
                nav_key=NavKey.BIOINFORMATICS.value,
                callback=self.open_bioinformatics_requested.emit,
            ),
            0,
            0,
        )
        module_grid.addWidget(
            self._module_card(
                title="Meta Analysis / Meta 分析",
                english_title="Meta Analysis",
                description="研究问题、检索筛选、数据提取、质量评价与统计分析工作流。",
                button_text="进入 Meta 分析",
                object_name="metaModuleButton",
                icon_key="meta_analysis",
                module_key=ModuleKey.META_ANALYSIS.value,
                nav_key=NavKey.META_ANALYSIS.value,
                callback=self.open_meta_analysis_requested.emit,
            ),
            0,
            1,
        )
        module_grid.addWidget(
            self._module_card(
                title="LabTools / 实验工具",
                english_title="LabTools",
                description="通用计算、试剂制备、实验模块与本地记录辅助入口。",
                button_text="进入 LabTools",
                object_name="labtoolsModuleButton",
                icon_key="labtools",
                module_key=ModuleKey.LABTOOLS.value,
                nav_key=NavKey.LABTOOLS.value,
                callback=self.open_labtools_requested.emit,
            ),
            0,
            2,
        )
        for column in range(3):
            module_grid.setColumnStretch(column, 1)
        layout.addLayout(module_grid)
        return frame

    def _module_card(
        self,
        *,
        title: str,
        english_title: str,
        description: str,
        button_text: str,
        object_name: str,
        icon_key: str,
        module_key: str,
        nav_key: str,
        callback: Callable[[], None],
    ) -> QFrame:
        frame = ModuleEntryCard()
        frame.setObjectName("moduleCard")
        frame.setProperty("uiPrimitive", "module_entry_card")
        frame.setProperty("moduleKey", module_key)
        frame.setProperty("navKey", nav_key)
        frame.setProperty("semanticKey", module_key)
        frame.setProperty("usabilityRole", "module_entry_card")
        frame.setProperty("moduleAccent", _module_accent_name(module_key))
        frame.setAccessibleName(title)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        frame.setMinimumHeight(258)
        frame.setToolTip(f"点击进入{title}")
        frame.clicked.connect(callback)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["sm"])

        icon_label = QLabel()
        icon_label.setObjectName("moduleIcon")
        icon_label.setFixedSize(72, 72)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_source = MODULE_ICON_PATHS.get(module_key) or MODULE_ICON_PATHS.get(icon_key)
        icon = load_module_pixmap(module_key, 56)
        if icon.isNull():
            icon = load_ui02_module_selection_pixmap("workspace", 56)
            icon_label.setProperty("iconFallback", True)
        else:
            icon_label.setProperty("iconFallback", False)
        icon_label.setProperty("moduleKey", module_key)
        icon_label.setProperty("iconSource", str(icon_source) if icon_source is not None else "")
        icon_label.setPixmap(icon)
        icon_label.setVisible(not icon.isNull())
        title_label = QLabel(title)
        title_label.setObjectName("moduleTitle")
        title_label.setProperty("moduleKey", module_key)
        title_label.setProperty("semanticKey", module_key)
        english = QLabel(english_title)
        english.setObjectName("moduleEnglishTitle")
        english.setProperty("moduleKey", module_key)
        accent = QLabel("")
        accent.setObjectName("moduleAccentLine")
        accent.setFixedHeight(3)
        accent.setMaximumWidth(72)
        description_label = QLabel(description)
        description_label.setObjectName("moduleDescription")
        description_label.setWordWrap(True)

        button = make_action_button(button_text, role="secondary", action_key=nav_key, semantic_state="testing")
        button.setObjectName(object_name)
        button.setProperty("moduleKey", module_key)
        button.setProperty("navKey", nav_key)
        button.setProperty("semanticKey", module_key)
        button.setProperty("usabilityRole", "module_entry_action")
        button.setAccessibleName(button_text)
        button.setIcon(load_ui02_module_selection_icon("workspace"))
        button.setIconSize(QSize(18, 18))
        button.setMinimumHeight(42)
        button.setToolTip(f"进入{title}")
        button.clicked.connect(callback)

        layout.addWidget(icon_label, 0, Qt.AlignLeft)
        layout.addWidget(title_label)
        layout.addWidget(english)
        layout.addWidget(accent)
        layout.addWidget(make_status_chip(status_key=_module_status_key(module_key)))
        layout.addSpacing(SPACING["sm"])
        layout.addWidget(description_label)
        layout.addStretch(1)
        layout.addWidget(button)
        return frame

    def _build_recent_projects_card(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("dashboardRecentProjectsCard")
        frame.setProperty("uiPrimitive", "dashboard_recent_projects")
        frame.setProperty("projectCenter", False)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["xl"], SPACING["lg"], SPACING["xl"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])
        title_row = QHBoxLayout()
        title_row.setSpacing(SPACING["sm"])
        title_row.addWidget(self._ui02_icon_label("recent_projects", 22))
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("最近项目 / Recent Projects")
        title.setObjectName("dashboardSectionTitle")
        subtitle = QLabel("继续打开最近使用的本地研究项目。")
        subtitle.setObjectName("dashboardSectionSubtitle")
        subtitle.setWordWrap(True)
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        title_row.addLayout(title_col, 1)
        open_more = make_action_button(
            "打开更多项目...",
            role="secondary",
            semantic_state="disabled",
            action_key="open_more_projects",
            enabled=False,
            disabled_reason="Project Center 尚未作为正式项目中心开放。",
        )
        open_more.setObjectName("dashboardOpenMoreProjectsButton")
        open_more.setIcon(load_ui02_module_selection_icon("project_entry"))
        open_more.setIconSize(QSize(18, 18))
        title_row.addWidget(open_more)
        layout.addLayout(title_row)

        projects = list(self._dashboard.recent_projects[:5])
        table = make_project_recent_table(
            [
                ProjectRecentItem(
                    key=project.project_id,
                    name=project.project_name,
                    module="生信分析" if project.project_type == "bioinformatics" else "Meta 分析",
                    last_opened=project.updated_at,
                    path=project.project_dir,
                    status_key="testing",
                )
                for project in projects
            ],
            object_name="dashboardRecentProjectsTable",
        )
        table.setProperty("dashboardOnly", True)
        if projects:
            layout.addWidget(table)
        else:
            table.setVisible(False)
            layout.addWidget(table)
            layout.addWidget(self._inline_empty_state("暂无最近项目", "您可以从 Bioinformatics、Meta Analysis 或 LabTools 创建或打开项目。"))
        return frame

    def _build_activity_card(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("dashboardActivityCard")
        frame.setProperty("uiPrimitive", "dashboard_activity_card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])
        layout.addLayout(self._title_row("任务动态 / Activity", "developer_preview"))

        tasks = list(self._dashboard.recent_tasks[:4])
        if not tasks:
            layout.addWidget(self._inline_empty_state("暂无任务动态", "启动分析或导入后，最近任务会在这里汇总。"))
            return frame

        for task in tasks:
            item = QFrame()
            item.setObjectName("dashboardActivityItem")
            item.setProperty("uiPrimitive", "dashboard_activity_item")
            item_layout = QVBoxLayout(item)
            item_layout.setContentsMargins(12, 10, 12, 10)
            item_layout.setSpacing(3)
            title = QLabel(task.title)
            title.setObjectName("dashboardActivityTitle")
            title.setWordWrap(True)
            meta = QLabel(f"{task.module} · {task.status.value}")
            meta.setObjectName("dashboardActivityMeta")
            meta.setWordWrap(True)
            item_layout.addWidget(title)
            item_layout.addWidget(meta)
            layout.addWidget(item)
        layout.addStretch(1)
        return frame

    def _inline_empty_state(self, title: str, body: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("dashboardInlineEmptyState")
        frame.setProperty("uiPrimitive", "dashboard_inline_empty_state")
        frame.setProperty("semanticKey", NavKey.DASHBOARD.value)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)
        title_label = QLabel(title)
        title_label.setObjectName("dashboardEmptyTitle")
        body_label = QLabel(body)
        body_label.setObjectName("dashboardEmptyBody")
        body_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(body_label)
        return frame

    def _support_line(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("supportLine")
        label.setWordWrap(True)
        return label

    def _ui02_icon_label(self, icon_key: str, size: int = 24) -> QLabel:
        label = QLabel()
        label.setObjectName("ui02Icon")
        label.setFixedSize(size + 4, size + 4)
        label.setAlignment(Qt.AlignCenter)
        pixmap = load_ui02_module_selection_pixmap(icon_key, size)
        label.setPixmap(pixmap)
        label.setVisible(not pixmap.isNull())
        return label

    def _header_icon_button(self, text: str, icon_key: str) -> QPushButton:
        button = make_action_button(text, role="secondary", size="small", semantic_state="available")
        button.setObjectName("dashboardHeaderIconButton")
        button.setMinimumSize(40, 40)
        button.setMaximumSize(44, 44)
        button.setToolTip(text)
        button.setText("")
        button.setIcon(load_ui02_module_selection_icon(icon_key))
        button.setIconSize(QSize(18, 18))
        button.setAccessibleName(text)
        return button

    def _title_row(self, title: str, icon_key: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACING["sm"])
        row.addWidget(self._ui02_icon_label(icon_key, 22))
        label = QLabel(title)
        label.setObjectName("supportTitle")
        row.addWidget(label)
        row.addStretch(1)
        return row

    def _support_line_with_icon(self, text: str, icon_key: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACING["sm"])
        row.addWidget(self._ui02_icon_label(icon_key, 18))
        row.addWidget(self._support_line(text), 1)
        return row


def _module_status_key(module_key: str) -> str:
    if module_key == ModuleKey.META_ANALYSIS.value:
        return "testing"
    return "testing"


def _module_accent_name(module_key: str) -> str:
    if module_key == ModuleKey.BIOINFORMATICS.value:
        return "bio"
    if module_key == ModuleKey.META_ANALYSIS.value:
        return "meta"
    if module_key == ModuleKey.LABTOOLS.value:
        return "labtools"
    return "default"
