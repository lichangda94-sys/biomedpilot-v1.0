from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QSize, Signal, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
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
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(SPACING["md"])

        root.addWidget(self._build_header())

        module_row = QHBoxLayout()
        module_row.setSpacing(SPACING["md"])
        module_row.addWidget(
            self._module_card(
                title="Bioinformatics / 生信分析",
                english_title="Resolver-first analysis workspace",
                description="从数据来源、准备检查、分组设计到结果与报告的生信工作流。",
                button_text="进入生信分析模块",
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
                english_title="Systematic review workflow shell",
                description="围绕研究问题、Meta 类型、检索、筛选、提取与报告草稿的流程工作台。",
                button_text="进入 Meta 分析模块",
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
                english_title="Calculators, reagents, records",
                description="通用计算器、试剂制备和实验模块三入口，按实验场景组织工具。",
                button_text="进入 LabTools",
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
        layout.setContentsMargins(SPACING["xl"], SPACING["lg"], SPACING["xl"], SPACING["lg"])
        layout.setSpacing(SPACING["lg"])

        layout.addWidget(self._ui02_icon_label("dashboard", 42))
        title_col = QVBoxLayout()
        title = QLabel("萤火虫 / Firefly")
        title.setObjectName("dashboardTitle")
        title.setProperty("semanticKey", BrandKey.PRIMARY.value)
        subtitle = QLabel("BioMedPilot / 医研智析工作台：选择 Bioinformatics、Meta Analysis 或 LabTools。")
        subtitle.setObjectName("dashboardSubtitle")
        subtitle.setProperty("semanticKey", BrandKey.SECONDARY.value)
        subtitle.setWordWrap(True)
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        layout.addLayout(title_col, 1)

        layout.addWidget(self._ui02_icon_label("current_user", 24))
        self._user_badge = QLabel("")
        self._user_badge.setObjectName("sessionBadge")
        layout.addWidget(self._user_badge)
        layout.addWidget(self._ui02_icon_label("version", 24))
        version = QLabel("版本：0.1.0-internal-beta")
        version.setObjectName("sessionBadge")
        layout.addWidget(version)
        layout.addWidget(self._ui02_icon_label("developer_preview", 24))
        self._tier_label = QLabel("Developer Preview / 本地测试版")
        self._tier_label.setObjectName("previewBadge")
        layout.addWidget(self._tier_label)
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
        frame.setAccessibleName(title)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        frame.setToolTip(f"点击进入{title}")
        frame.clicked.connect(callback)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
        layout.setSpacing(SPACING["md"])

        icon_label = QLabel()
        icon_label.setObjectName("moduleIcon")
        icon_label.setFixedSize(64, 64)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_source = MODULE_ICON_PATHS.get(module_key) or MODULE_ICON_PATHS.get(icon_key)
        icon = load_module_pixmap(module_key, 60)
        if icon.isNull():
            icon = load_ui02_module_selection_pixmap("workspace", 60)
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
        button.setMinimumWidth(168)
        button.setToolTip(f"进入{title}")
        button.clicked.connect(callback)

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(english)
        layout.addWidget(accent)
        layout.addWidget(make_status_chip(status_key=_module_status_key(module_key)))
        layout.addSpacing(SPACING["sm"])
        layout.addWidget(description_label)
        layout.addWidget(button, alignment=Qt.AlignLeft)
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
        title_row.addWidget(make_section_title("最近项目 / Recent Projects", "Dashboard only lists recent project records; it is not a Project Center."), 1)
        open_more = make_action_button(
            "打开更多项目...",
            role="secondary",
            semantic_state="disabled",
            action_key="open_more_projects",
            enabled=False,
            disabled_reason="Project Center is not part of the UI-D2 Dashboard rebuild.",
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
        layout.addWidget(table)
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
        return "shell_only"
    return "testing"
