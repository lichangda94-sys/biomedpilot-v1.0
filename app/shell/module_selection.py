from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QSize, Signal, Qt
from PySide6.QtWidgets import (
    QFrame,
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
from app.shared.ui_components import ProjectRecentItem, make_action_button, make_project_recent_table, make_section_title, make_status_chip, make_workbench_card
from app.shared.ui_components.primitives import make_empty_state
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
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(SPACING["xl"])

        root.addWidget(self._build_header())

        module_row = QHBoxLayout()
        module_row.setSpacing(SPACING["md"])
        module_row.addWidget(
            self._module_card(
                title="Bioinformatics / 生信分析",
                english_title="Bioinformatics",
                description="数据来源、检查准备、分组设计、分析任务、结果与报告。",
                button_text="进入模块  →",
                object_name="bioModuleButton",
                icon_key="bioinformatics",
                module_key=ModuleKey.BIOINFORMATICS.value,
                nav_key=NavKey.BIOINFORMATICS.value,
                callback=self.open_bioinformatics_requested.emit,
            )
        )
        module_row.addWidget(
            self._module_card(
                title="Meta Analysis / Meta 分析",
                english_title="Meta Analysis",
                description="研究问题、检索、筛选、数据提取、质量评价、统计分析。",
                button_text="进入模块  →",
                object_name="metaModuleButton",
                icon_key="meta_analysis",
                module_key=ModuleKey.META_ANALYSIS.value,
                nav_key=NavKey.META_ANALYSIS.value,
                callback=self.open_meta_analysis_requested.emit,
            )
        )
        module_row.addWidget(
            self._module_card(
                title="LabTools / 实验工具",
                english_title="LabTools",
                description="通用计算、试剂制备、实验模块工具集合。",
                button_text="进入模块  →",
                object_name="labtoolsModuleButton",
                icon_key="labtools",
                module_key=ModuleKey.LABTOOLS.value,
                nav_key=NavKey.LABTOOLS.value,
                callback=self.open_labtools_requested.emit,
            )
        )

        root.addLayout(module_row)
        root.addWidget(self._build_recent_projects_card())
        root.addStretch(1)
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _build_header(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("dashboardHeader")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["lg"])

        title_col = QVBoxLayout()
        title = QLabel("萤火虫 工作台 / Firefly Workbench")
        title.setObjectName("dashboardTitle")
        title.setProperty("semanticKey", BrandKey.PRIMARY.value)
        subtitle = QLabel("欢迎回来！这是您本地生物医学研究的统一工作台。")
        subtitle.setObjectName("dashboardSubtitle")
        subtitle.setProperty("semanticKey", BrandKey.SECONDARY.value)
        subtitle.setWordWrap(True)
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        preview = make_status_chip("Developer Preview / 本地测试版", status_key="developer_preview")
        preview.setObjectName("previewBadge")
        title_col.addWidget(preview, 0, Qt.AlignLeft)
        layout.addLayout(title_col, 1)

        layout.addWidget(self._header_icon_button("通知"))
        layout.addWidget(self._header_icon_button("帮助"))
        self._user_badge = QLabel("")
        self._user_badge.setObjectName("sessionBadge")
        layout.addWidget(self._user_badge)
        self._tier_label = QLabel("Developer Preview / 本地测试版")
        self._tier_label.setObjectName("previewBadge")
        self._tier_label.setVisible(False)
        self._license_label = QLabel("")
        self._license_label.setVisible(False)
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
        frame.setMinimumHeight(310)
        frame.setToolTip(f"点击进入{title}")
        frame.clicked.connect(callback)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
        layout.setSpacing(SPACING["md"])

        icon_label = QLabel()
        icon_label.setObjectName("moduleIcon")
        icon_label.setFixedSize(112, 112)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_source = MODULE_ICON_PATHS.get(module_key) or MODULE_ICON_PATHS.get(icon_key)
        icon = load_module_pixmap(module_key, 96)
        if icon.isNull():
            icon = load_ui02_module_selection_pixmap("workspace", 96)
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
        accent.setFixedHeight(4)
        accent.setMaximumWidth(96)
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
        button.setMinimumHeight(50)
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
        frame = make_workbench_card(object_name="dashboardRecentProjectsCard")
        frame.setProperty("uiPrimitive", "dashboard_recent_projects")
        frame.setProperty("projectCenter", False)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["xl"], SPACING["lg"], SPACING["xl"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])
        title_row = QHBoxLayout()
        title_row.setSpacing(SPACING["sm"])
        title_row.addWidget(self._ui02_icon_label("recent_projects", 22))
        title_row.addWidget(make_section_title("最近项目 / Recent Projects", "继续打开最近使用的本地研究项目。"), 1)
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
            layout.addWidget(
                make_empty_state(
                    "暂无最近项目",
                    "您可以从 Bioinformatics、Meta Analysis 或 LabTools 创建或打开项目。",
                    action_text="打开更多项目...",
                    empty_state_key="empty_project",
                    semantic_key=NavKey.DASHBOARD.value,
                    semantic_state="planned",
                )
            )
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

    def _header_icon_button(self, text: str) -> QPushButton:
        button = make_action_button(text, role="secondary", size="small", semantic_state="available")
        button.setObjectName("dashboardHeaderIconButton")
        button.setMinimumSize(40, 40)
        button.setMaximumSize(44, 44)
        button.setToolTip(text)
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
