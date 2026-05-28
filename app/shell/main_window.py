from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QInputDialog,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app import labtools_runtime
from app.app_identity import (
    APP_NAME,
    LABTOOLS_ICON_PATHS,
    SETTINGS_RESOURCE_ICON_PATHS,
    icon_asset_statuses,
    icon_asset_summary,
    load_app_icon,
    load_labtools_pixmap,
    load_settings_resource_pixmap,
)
from app.bioinformatics.workspace import BioinformaticsWorkspaceWidget
from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget
from app.shell.dashboard import DashboardModel, build_dashboard_model
from app.shell.login import BioMedPilotLoginWidget, LocalSession
from app.shell.module_selection import ModuleSelectionWidget
from app.shell.settings_page import build_settings_page
from app.shell.sidebar import SidebarWidget
from app.shell.status_panel import StatusPanel
from app.shared.project_center.service import ProjectCenter, ProjectRecord
from app.shared.semantic_keys import ModuleKey, PageKey
from app.shared.settings import SettingsProfile
from app.shared.testing_mode import generate_feedback_template, generate_lan_feedback_template, lan_real_world_feedback_summary, testing_mode_summary
from app.shared.ui_components import (
    make_left_list_middle_form_right_preview,
    make_preview_card,
    make_section_title,
    make_three_column_workbench,
    make_workbench_card,
)
from app.shared.ui_components.primitives import diagnostic_disclosure_title, make_button, make_empty_state, make_status_chip


_SETTINGS_RESOURCE_SEMANTIC_KEYS = {
    "resource_external_engine": PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value,
    "resource_image_analysis_engine": PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value,
    "resource_imagej_fiji": PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value,
    "resource_pdf_ocr": PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value,
    "resource_local_model": PageKey.SETTINGS_MODEL_ENGINE.value,
    "resource_cloud_ai": PageKey.SETTINGS_MODEL_ENGINE.value,
    "resource_python": PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value,
    "resource_r": PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value,
    "resource_go": PageKey.SETTINGS_ANALYSIS_RESOURCES.value,
    "resource_kegg": PageKey.SETTINGS_ANALYSIS_RESOURCES.value,
    "resource_analysis_package": PageKey.SETTINGS_ANALYSIS_RESOURCES.value,
    "resource_plotting_package": PageKey.SETTINGS_ANALYSIS_RESOURCES.value,
    "resource_developer_diagnostics": PageKey.SETTINGS_DEVELOPER_DIAGNOSTICS.value,
}

LABTOOLS_HOME_TOKENS = {
    "background": "#F5F6FA",
    "surface": "#FFFFFF",
    "surface_subtle": "#FAFBFD",
    "border": "#E5E7EB",
    "divider": "#E5E7EB",
    "text": "#111827",
    "muted": "#6B7280",
    "faint": "#9CA3AF",
    "blue": "#2563EB",
    "blue_soft": "#EEF3FF",
    "green": "#059669",
    "green_soft": "#ECFDF5",
    "amber": "#B45309",
    "amber_soft": "#FFFBEB",
    "purple": "#7C3AED",
    "purple_soft": "#F5F3FF",
}

GENERAL_CALCULATOR_TOKENS = {
    "background": "#F6F7FB",
    "surface": "#FFFFFF",
    "surface_subtle": "#FAFBFD",
    "border": "#E5E7EB",
    "divider": "#E5E7EB",
    "text": "#111827",
    "muted": "#6B7280",
    "faint": "#9CA3AF",
    "blue": "#2563EB",
    "blue_soft": "#EEF3FF",
    "green": "#059669",
    "green_soft": "#ECFDF5",
    "amber": "#B45309",
    "amber_soft": "#FFFBEB",
}

REAGENT_PREP_TOKENS = {
    "background": "#F6F7FB",
    "surface": "#FFFFFF",
    "surface_subtle": "#FAFBFD",
    "surface_blue": "#F4F8FF",
    "border": "#E5E7EB",
    "divider": "#EEF2F7",
    "text": "#111827",
    "muted": "#6B7280",
    "faint": "#9CA3AF",
    "blue": "#2563EB",
    "blue_soft": "#EEF4FF",
    "green": "#059669",
    "green_soft": "#ECFDF5",
    "amber": "#B45309",
    "amber_soft": "#FFFBEB",
    "red": "#DC2626",
    "red_soft": "#FEF2F2",
}

PROTEIN_WB_TOKENS = {
    "background": "#F1F5F9",
    "surface": "#FFFFFF",
    "surface_subtle": "#F8FAFC",
    "field": "#EFF6FF",
    "field_disabled": "#F8FAFC",
    "border": "#E2E8F0",
    "divider": "#EEF2F7",
    "text": "#0F172A",
    "muted": "#64748B",
    "faint": "#94A3B8",
    "blue": "#2563EB",
    "blue_soft": "#EFF6FF",
    "green": "#059669",
    "green_soft": "#ECFDF5",
    "amber": "#D97706",
    "amber_soft": "#FFFBEB",
    "red": "#DC2626",
    "red_soft": "#FFF7ED",
    "navy": "#0F172A",
}


class MainWindow(QMainWindow):
    def __init__(self, dashboard: DashboardModel | None = None) -> None:
        super().__init__()
        self._project_center = ProjectCenter.default()
        self._dashboard = dashboard or build_dashboard_model()
        self._session: LocalSession | None = None
        self._labtools_project_root = None
        self.setWindowTitle(APP_NAME)
        icon = load_app_icon()
        if not icon.isNull():
            self.setWindowIcon(icon)
        self.resize(1120, 720)
        self.setMinimumSize(860, 560)

        self._root_stack = QStackedWidget()
        self._welcome_page = BioMedPilotLoginWidget(
            on_login=self._complete_login,
            on_settings=self._open_settings_from_welcome,
            on_about=self._open_about_from_welcome,
        )
        self._login_page = self._welcome_page
        self._root_stack.addWidget(self._welcome_page)

        self._stack = QStackedWidget()
        self._dashboard_page = self._build_dashboard_page()
        self._bioinformatics_page = BioinformaticsWorkspaceWidget(on_back=self.show_dashboard)
        self._meta_analysis_page = MetaAnalysisWorkspaceWidget(on_back=self.show_dashboard)
        self._labtools_page = self._build_labtools_page()
        self._settings_page = self._build_settings_page()
        self._testing_page = self._build_test_feedback_page()
        self._about_page = self._build_about_page()
        self._stack.addWidget(self._dashboard_page)
        self._stack.addWidget(self._bioinformatics_page)
        self._stack.addWidget(self._meta_analysis_page)
        self._stack.addWidget(self._labtools_page)
        self._stack.addWidget(self._settings_page)
        self._stack.addWidget(self._testing_page)
        self._stack.addWidget(self._about_page)

        self._shell_page = QWidget()
        shell_layout = QHBoxLayout(self._shell_page)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        self._sidebar = SidebarWidget(
            on_dashboard=self.show_dashboard,
            on_bioinformatics=self.show_bioinformatics,
            on_meta_analysis=self.show_meta_analysis,
            on_labtools=self.show_labtools,
            on_settings=self.show_settings,
            on_test_feedback=self.show_test_feedback,
            on_about=self.show_about,
        )
        shell_layout.addWidget(self._sidebar)
        shell_layout.addWidget(self._stack, 1)
        self._root_stack.addWidget(self._shell_page)
        self._root_stack.setCurrentWidget(self._welcome_page)
        self.setCentralWidget(self._root_stack)

    def current_session(self) -> LocalSession | None:
        return self._session

    def set_labtools_project_root(self, project_root) -> None:
        self._labtools_project_root = project_root

    def _complete_login(self, session: LocalSession) -> None:
        self._session = session
        self.show_dashboard()
        self._root_stack.setCurrentWidget(self._shell_page)

    def logout(self) -> None:
        self._session = None
        self._welcome_page.reset_session()
        self._root_stack.setCurrentWidget(self._welcome_page)
        self.setWindowTitle(APP_NAME)

    def _open_settings_from_welcome(self) -> None:
        if self._session is None:
            self._welcome_page.enter_workspace()
        self.show_settings()

    def _open_about_from_welcome(self) -> None:
        if self._session is None:
            self._welcome_page.enter_workspace()
        self.show_about()

    def show_dashboard(self) -> None:
        self._refresh_dashboard_page()
        self._stack.setCurrentWidget(self._dashboard_page)
        self._set_sidebar_active("dashboard")
        self.setWindowTitle(APP_NAME)

    def show_bioinformatics(self) -> None:
        self._stack.setCurrentWidget(self._bioinformatics_page)
        self._set_sidebar_active("bioinformatics")
        self.setWindowTitle("BioMedPilot / 生信分析")

    def show_meta_analysis(self) -> None:
        self._stack.setCurrentWidget(self._meta_analysis_page)
        self._set_sidebar_active("meta_analysis")
        self.setWindowTitle("BioMedPilot / Meta 分析")

    def show_labtools(self) -> None:
        self._stack.setCurrentWidget(self._labtools_page)
        self._set_sidebar_active("labtools")
        self.setWindowTitle("BioMedPilot / LabTools")

    def show_settings(self) -> None:
        self._stack.setCurrentWidget(self._settings_page)
        self._set_sidebar_active("settings")
        self.setWindowTitle("BioMedPilot / 设置中心")

    def show_test_feedback(self) -> None:
        self._stack.setCurrentWidget(self._testing_page)
        self._set_sidebar_active("test_feedback")
        self.setWindowTitle("BioMedPilot / Test Feedback")

    def show_testing_mode(self) -> None:
        self.show_test_feedback()

    def show_about(self) -> None:
        self._stack.setCurrentWidget(self._about_page)
        self._set_sidebar_active("about")
        self.setWindowTitle("BioMedPilot / About")

    def _set_sidebar_active(self, key: str) -> None:
        sidebar = getattr(self, "_sidebar", None)
        if sidebar is not None and hasattr(sidebar, "set_active_key"):
            sidebar.set_active_key(key)

    def create_bioinformatics_project(self) -> None:
        self._create_project_and_open("bioinformatics")

    def create_meta_analysis_project(self) -> None:
        self._create_project_and_open("meta_analysis")

    def open_project_record(self, record: ProjectRecord) -> None:
        if record.project_type == "bioinformatics":
            self.show_bioinformatics()
        else:
            self._meta_analysis_page.set_project_record(record)
            self.show_meta_analysis()

    def current_workspace_key(self) -> str:
        if hasattr(self, "_root_stack") and self._root_stack.currentWidget() is self._welcome_page:
            return "welcome"
        current = self._stack.currentWidget()
        if current is self._bioinformatics_page:
            return "bioinformatics"
        if current is self._meta_analysis_page:
            return "meta_analysis"
        if current is self._labtools_page:
            return "labtools"
        if current is self._settings_page:
            return "settings"
        if current is self._testing_page:
            return "test_feedback"
        if current is self._about_page:
            return "about"
        return "dashboard"

    def _build_dashboard_page(self) -> QWidget:
        return ModuleSelectionWidget(
            dashboard=self._dashboard,
            session=self._session,
            on_open_bioinformatics=self.show_bioinformatics,
            on_open_meta_analysis=self.show_meta_analysis,
            on_open_labtools=self.show_labtools,
        )

    def _refresh_dashboard_page(self) -> None:
        if not hasattr(self, "_stack"):
            return
        old_page = self._dashboard_page
        old_index = self._stack.indexOf(old_page)
        self._dashboard = build_dashboard_model(project_center=self._project_center)
        self._dashboard_page = self._build_dashboard_page()
        if old_index >= 0:
            self._stack.insertWidget(old_index, self._dashboard_page)
            self._stack.removeWidget(old_page)
            old_page.deleteLater()

    def _entry_card(self, title: str, features: tuple[str, ...], callback) -> QFrame:
        frame = QFrame()
        frame.setObjectName("entryCard")
        frame.setStyleSheet("QFrame#entryCard { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 18, 20, 18)
        label = QLabel(title)
        label.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(label)
        list_widget = QListWidget()
        list_widget.setFocusPolicy(Qt.NoFocus)
        for feature in features:
            QListWidgetItem(feature, list_widget)
        layout.addWidget(list_widget, 1)
        button = QPushButton("进入工作台")
        button.clicked.connect(callback)
        layout.addWidget(button)
        return frame

    def _list_card(self, title: str, rows: list[str]) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        header = QLabel(title)
        header.setStyleSheet("font-weight: 700;")
        layout.addWidget(header)
        for row in rows:
            label = QLabel(row)
            label.setWordWrap(True)
            layout.addWidget(label)
        layout.addStretch(1)
        return frame

    def _quick_access_card(self, *, module_key: str, object_name: str, items: tuple[str, ...]) -> QFrame:
        frame = QFrame()
        frame.setObjectName(object_name)
        frame.setProperty("moduleKey", module_key)
        frame.setStyleSheet(f"QFrame#{object_name} {{ border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }}")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)
        title = QLabel("快速入口")
        title.setObjectName("quickAccessTitle")
        title.setStyleSheet("font-weight: 700;")
        layout.addWidget(title)
        row = QHBoxLayout()
        row.setSpacing(12)
        for item in items:
            button = make_button(item, role="secondary")
            button.setObjectName("quickAccessButton")
            button.setProperty("moduleKey", module_key)
            button.setProperty("quickAccessKey", item)
            button.setEnabled(False)
            row.addWidget(button)
        row.addStretch(1)
        layout.addLayout(row)
        return frame

    def _recent_projects_card(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        header = QLabel("最近项目")
        header.setStyleSheet("font-weight: 700;")
        layout.addWidget(header)
        recent_projects = self._project_center.recent_projects(limit=5)
        if not recent_projects:
            layout.addWidget(QLabel("暂无最近项目"))
        for record in recent_projects:
            button = QPushButton(record.display_label())
            button.clicked.connect(lambda _checked=False, item=record: self.open_project_record(item))
            layout.addWidget(button)
        layout.addStretch(1)
        return frame

    def _build_labtools_page(self) -> QWidget:
        page = QScrollArea()
        page.setObjectName("labtoolsShellPage")
        page.setWidgetResizable(True)
        page.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        page.setProperty("pageKey", "home")
        page.setProperty("semanticKey", PageKey.LABTOOLS_HOME.value)
        page.setProperty("usabilityRole", "scrollable_shell_page")
        page.setAccessibleName("LabTools shell page")
        self._labtools_shell_page = page
        self._set_labtools_content(self._build_labtools_home_content())
        return page

    def _set_labtools_content(self, content: QWidget) -> None:
        page = self._labtools_shell_page
        old_widget = page.takeWidget()
        if old_widget is not None:
            old_widget.deleteLater()
        page.setProperty("pageKey", content.property("pageKey"))
        page.setProperty("semanticKey", content.property("semanticKey"))
        page.setWidget(content)

    def _build_labtools_base_content(self, *, page_key: str, semantic_key: str, title: str, subtitle: str) -> QWidget:
        content = QWidget()
        content.setObjectName("labtoolsShellContent")
        content.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        content.setProperty("pageKey", page_key)
        content.setProperty("semanticKey", semantic_key)
        content.setProperty("uiPrimitive", "page_shell")
        content.setProperty("layoutPolishNoOverlap", True)
        root = QVBoxLayout(content)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)
        title_label = QLabel(title)
        title_label.setObjectName("labtoolsShellTitle")
        title_label.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        title_label.setProperty("semanticKey", semantic_key)
        title_label.setStyleSheet("font-size: 30px; font-weight: 800; color: #0F172A;")
        root.addWidget(title_label)
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("labtoolsShellSubtitle")
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet("font-size: 15px; color: #334155;")
        root.addWidget(subtitle_label)
        root.addWidget(make_status_chip("Developer Preview / 本地测试版", status_key="developer_preview"), 0, Qt.AlignLeft)
        return content

    def _build_labtools_home_content(self) -> QWidget:
        content = QWidget()
        content.setObjectName("labtoolsShellContent")
        content.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        content.setProperty("pageKey", "home")
        content.setProperty("semanticKey", PageKey.LABTOOLS_HOME.value)
        content.setProperty("uiPrimitive", "labtools_home_page")
        content.setProperty("layoutPolishNoOverlap", True)
        content.setStyleSheet(f"QWidget#labtoolsShellContent {{ background: {LABTOOLS_HOME_TOKENS['background']}; }}")
        root = QVBoxLayout(content)
        root.setContentsMargins(30, 22, 30, 24)
        root.setSpacing(22)

        root.addLayout(self._labtools_home_header())
        root.addWidget(self._labtools_home_section_label("功能入口 · Feature Tools"))

        entry_row = QHBoxLayout()
        entry_row.setSpacing(18)
        entry_row.addWidget(
            self._labtools_primary_entry_card(
                title="通用计算器",
                english_title="General Calculator",
                description="常用科学计算与单位换算，满足日常实验计算需求。",
                button_text="打开计算器",
                page_key="general_calculators",
                semantic_key=PageKey.LABTOOLS_GENERAL_CALCULATORS.value,
                status_key="shell_only",
                rows=[
                    "稀释计算",
                    "加样计算",
                    "分子量 / 摩尔量换算",
                    "单位换算",
                    "更多计算工具",
                ],
                callback=self._show_labtools_general_calculator_shell,
            )
        )
        entry_row.addWidget(
            self._labtools_primary_entry_card(
                title="试剂制备",
                english_title="Reagent Preparation",
                description="试剂配制与浓度换算，快速规划实验所需试剂。",
                button_text="进入试剂制备",
                page_key="reagent_preparation",
                semantic_key=PageKey.LABTOOLS_REAGENT_PREPARATION.value,
                status_key="planned",
                rows=[
                    "溶液配制",
                    "稀释系列",
                    "缓冲液配方",
                    "保存与稳定性提示",
                    "更多配制工具",
                ],
                callback=self._show_labtools_reagent_preparation_shell,
            )
        )
        entry_row.addWidget(
            self._labtools_primary_entry_card(
                title="实验模块",
                english_title="Experiment Modules",
                description="面向不同实验类型的专用工具，提供完整的实验方案与计算支持。",
                button_text="选择实验模块",
                page_key="experiment_modules",
                semantic_key=PageKey.LABTOOLS_EXPERIMENT_MODULES.value,
                status_key="testing",
                rows=[
                    "细胞实验",
                    "蛋白实验",
                    "核酸实验",
                    "免疫与吸光度实验",
                    "免疫组化",
                ],
                callback=self._show_labtools_experiment_modules_shell,
            )
        )
        root.addLayout(entry_row)
        root.addWidget(self._labtools_quick_entry_section())
        root.addWidget(self._labtools_hidden_home_state_panels())
        root.addStretch(1)
        return content

    def _labtools_home_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(16)
        title_col = QVBoxLayout()
        title_col.setSpacing(7)
        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        title_row.addWidget(self._labtools_icon_label(PageKey.LABTOOLS_EXPERIMENT_MODULES.value, object_name="labtoolsHomeHeaderIcon", size=16), 0)
        title = QLabel("实验工具/LabTools")
        title.setObjectName("labtoolsShellTitle")
        title.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        title.setProperty("semanticKey", PageKey.LABTOOLS_HOME.value)
        title.setStyleSheet(f"color: {LABTOOLS_HOME_TOKENS['text']}; font-size: 20px; font-weight: 800;")
        title_row.addWidget(title, 0)
        title_row.addWidget(make_status_chip("Developer Preview · 本地测试版", status_key="developer_preview"), 0)
        title_row.addStretch(1)
        subtitle = QLabel("通用计算、试剂配制与实验流程工具集合，为生物医学实验提供可靠的计算与规划支持。")
        subtitle.setObjectName("labtoolsShellSubtitle")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"color: {LABTOOLS_HOME_TOKENS['muted']}; font-size: 13px;")
        title_col.addLayout(title_row)
        title_col.addWidget(subtitle)
        header.addLayout(title_col, 1)
        header.addWidget(self._labtools_header_icon_button("指南"), 0, Qt.AlignTop)
        header.addWidget(self._labtools_header_icon_button("设置"), 0, Qt.AlignTop)
        user = QLabel("Researcher")
        user.setObjectName("labtoolsHomeUserBadge")
        user.setAlignment(Qt.AlignCenter)
        user.setStyleSheet(
            f"background: {LABTOOLS_HOME_TOKENS['surface']}; border: 1px solid {LABTOOLS_HOME_TOKENS['border']}; "
            f"border-radius: 8px; color: {LABTOOLS_HOME_TOKENS['text']}; font-size: 12px; font-weight: 650; padding: 8px 14px;"
        )
        header.addWidget(user, 0, Qt.AlignTop)
        return header

    def _labtools_header_icon_button(self, label: str) -> QPushButton:
        button = QPushButton(label[:1])
        button.setObjectName("labtoolsHomeHeaderButton")
        button.setAccessibleName(label)
        button.setEnabled(False)
        button.setFixedSize(30, 30)
        button.setStyleSheet(
            f"QPushButton#labtoolsHomeHeaderButton {{ background: {LABTOOLS_HOME_TOKENS['surface']}; "
            f"border: 1px solid {LABTOOLS_HOME_TOKENS['border']}; border-radius: 8px; color: {LABTOOLS_HOME_TOKENS['blue']}; font-weight: 800; }}"
        )
        return button

    def _labtools_home_section_label(self, text: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("labtoolsHomeSectionLabel")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)
        label = QLabel(text)
        label.setObjectName("labtoolsHomeSectionText")
        label.setStyleSheet(f"color: {LABTOOLS_HOME_TOKENS['muted']}; font-size: 12px; font-weight: 750;")
        layout.addWidget(label, 0)
        divider = QFrame()
        divider.setObjectName("labtoolsHomeSectionDivider")
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background: {LABTOOLS_HOME_TOKENS['divider']}; border: 0;")
        layout.addWidget(divider, 1)
        return frame

    def _labtools_quick_entry_section(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("labtoolsQuickAccessCard")
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setStyleSheet("QFrame#labtoolsQuickAccessCard { background: transparent; border: 0; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        layout.addWidget(self._labtools_home_section_label("快速入口"))
        row = QHBoxLayout()
        row.setSpacing(14)
        for title, body, icon_text, icon_bg in (
            ("使用指南", "查看各工具使用说明与示例", "G", LABTOOLS_HOME_TOKENS["blue_soft"]),
            ("常见问题", "浏览常见问题与解决方案", "Q", LABTOOLS_HOME_TOKENS["green_soft"]),
            ("意见反馈", "提出建议或报告问题", "F", LABTOOLS_HOME_TOKENS["amber_soft"]),
            ("最近使用", "快速访问最近使用的工具或模块", "R", LABTOOLS_HOME_TOKENS["purple_soft"]),
        ):
            row.addWidget(self._labtools_quick_entry_card(title, body, icon_text=icon_text, icon_bg=icon_bg), 1)
        layout.addLayout(row)
        return frame

    def _labtools_quick_entry_card(self, title: str, body: str, *, icon_text: str, icon_bg: str) -> QPushButton:
        button = QPushButton()
        button.setObjectName("quickAccessButton")
        button.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        button.setProperty("quickAccessKey", title)
        button.setEnabled(False)
        button.setMinimumHeight(62)
        button.setStyleSheet(
            f"""
            QPushButton#quickAccessButton {{
                text-align: left;
                background: {LABTOOLS_HOME_TOKENS['surface']};
                border: 1px solid {LABTOOLS_HOME_TOKENS['border']};
                border-radius: 11px;
                color: {LABTOOLS_HOME_TOKENS['text']};
                padding: 10px 14px;
                font-size: 12px;
                font-weight: 750;
            }}
            QPushButton#quickAccessButton:disabled {{
                color: {LABTOOLS_HOME_TOKENS['text']};
            }}
            """
        )
        button.setText(f"{icon_text}    {title}\n      {body}        >")
        return button

    def _labtools_hidden_home_state_panels(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("labtoolsHomeHiddenStatePanels")
        frame.setVisible(False)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._labtools_local_data_status_panel(page_key="home", semantic_key=PageKey.LABTOOLS_HOME.value))
        layout.addWidget(self._labtools_lan_host_management_panel(page_key="home", semantic_key=PageKey.LABTOOLS_HOME.value))
        layout.addWidget(self._labtools_lan_manual_connection_panel(page_key="home", semantic_key=PageKey.LABTOOLS_HOME.value))
        layout.addWidget(make_status_chip(status_key="shell_only"))
        layout.addWidget(make_status_chip(status_key="planned"))
        layout.addWidget(make_status_chip(status_key="testing"))
        return frame

    def _show_labtools_home(self) -> None:
        self._set_labtools_content(self._build_labtools_home_content())

    def _labtools_local_data_status_panel(self, *, page_key: str, semantic_key: str) -> QFrame:
        model = labtools_runtime.get_labtools_local_data_read_model(self._labtools_project_root)
        frame = make_workbench_card(object_name="labtoolsLocalDataStatusPanel", semantic_state="testing")
        frame.setObjectName("labtoolsLocalDataStatusPanel")
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("pageKey", page_key)
        frame.setProperty("semanticKey", semantic_key)
        frame.setProperty("uiPrimitive", "labtools_local_data_status_panel")
        frame.setProperty("readOnly", True)
        frame.setProperty("cloudSyncAllowed", False)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        layout.addWidget(make_section_title("本地数据 / Local Data"))
        status = QLabel(f"数据源：本地模式 · 状态：{model.status.status} · {model.status.reason}")
        status.setObjectName("labtoolsLocalDataStatusText")
        status.setProperty("status", model.status.status)
        status.setProperty("dataSourceMode", model.status.data_source_mode)
        status.setWordWrap(True)
        layout.addWidget(status)
        counts = QLabel(
            f"reagent {model.status.reagent_count} · sample {model.status.sample_count} · "
            f"cell {model.status.cell_count} · freeze vial {model.status.freeze_vial_count} · record {model.status.record_count}"
        )
        counts.setObjectName("labtoolsLocalDataCountRow")
        counts.setProperty("reagentCount", model.status.reagent_count)
        counts.setProperty("sampleCount", model.status.sample_count)
        counts.setProperty("cellCount", model.status.cell_count)
        counts.setProperty("recordCount", model.status.record_count)
        counts.setWordWrap(True)
        layout.addWidget(counts)
        return frame

    def _labtools_lan_host_management_panel(self, *, page_key: str, semantic_key: str) -> QFrame:
        frame = make_workbench_card(object_name="labtoolsLanHostManagementPanel", semantic_state="preflight_only")
        frame.setObjectName("labtoolsLanHostManagementPanel")
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("pageKey", page_key)
        frame.setProperty("semanticKey", semantic_key)
        frame.setProperty("uiPrimitive", "labtools_lan_host_management_panel")
        frame.setProperty("readOnly", True)
        frame.setProperty("writeEnabled", False)
        frame.setProperty("syncEnabled", False)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        layout.addWidget(make_section_title("局域网 Host 管理 / LAN Host", "Read-only host controls; no sync or writes."))

        mode_row = QHBoxLayout()
        mode_row.setSpacing(12)
        self._labtools_lan_host_auth_radio = QRadioButton("Auth required")
        self._labtools_lan_host_auth_radio.setObjectName("labtoolsLanHostAuthRequiredRadio")
        self._labtools_lan_host_auth_radio.setChecked(True)
        self._labtools_lan_host_auth_radio.setProperty("serverMode", "auth_required")
        self._labtools_lan_host_compat_radio = QRadioButton("Compatibility read-only")
        self._labtools_lan_host_compat_radio.setObjectName("labtoolsLanHostCompatibilityRadio")
        self._labtools_lan_host_compat_radio.setProperty("serverMode", "compatibility")
        self._labtools_lan_host_mode_group = QButtonGroup(frame)
        self._labtools_lan_host_mode_group.addButton(self._labtools_lan_host_auth_radio)
        self._labtools_lan_host_mode_group.addButton(self._labtools_lan_host_compat_radio)
        mode_row.addWidget(self._labtools_lan_host_auth_radio)
        mode_row.addWidget(self._labtools_lan_host_compat_radio)
        mode_row.addStretch(1)
        layout.addLayout(mode_row)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        start = make_button("启动只读 Host", role="secondary")
        start.setObjectName("labtoolsLanHostStartButton")
        start.clicked.connect(self._start_labtools_lan_host)
        stop = make_button("停止 Host", role="secondary")
        stop.setObjectName("labtoolsLanHostStopButton")
        stop.clicked.connect(self._stop_labtools_lan_host)
        pairing = make_button("创建 Pairing Code", role="secondary")
        pairing.setObjectName("labtoolsLanHostCreatePairingButton")
        pairing.clicked.connect(self._create_labtools_lan_host_pairing)
        refresh = make_button("刷新", role="secondary")
        refresh.setObjectName("labtoolsLanHostRefreshButton")
        refresh.clicked.connect(self._refresh_labtools_lan_host_panel)
        action_row.addWidget(start)
        action_row.addWidget(stop)
        action_row.addWidget(pairing)
        action_row.addWidget(refresh)
        action_row.addStretch(1)
        layout.addLayout(action_row)

        self._labtools_lan_host_mode_label = QLabel("Server mode：auth required · host 未启动")
        self._labtools_lan_host_mode_label.setObjectName("labtoolsLanHostModeText")
        self._labtools_lan_host_mode_label.setProperty("serverMode", "auth_required")
        self._labtools_lan_host_mode_label.setWordWrap(True)
        layout.addWidget(self._labtools_lan_host_mode_label)

        self._labtools_lan_host_pairing_label = QLabel("Pairing code：未创建")
        self._labtools_lan_host_pairing_label.setObjectName("labtoolsLanHostPairingCodeText")
        self._labtools_lan_host_pairing_label.setProperty("pairingActive", False)
        self._labtools_lan_host_pairing_label.setWordWrap(True)
        layout.addWidget(self._labtools_lan_host_pairing_label)

        self._labtools_lan_host_clients = QListWidget()
        self._labtools_lan_host_clients.setObjectName("labtoolsLanHostPairedClientList")
        self._labtools_lan_host_clients.setProperty("tokenMaterialVisible", False)
        self._labtools_lan_host_clients.setMinimumHeight(84)
        layout.addWidget(self._labtools_lan_host_clients)

        revoke_row = QHBoxLayout()
        revoke = make_button("Revoke selected", role="secondary")
        revoke.setObjectName("labtoolsLanHostRevokeButton")
        revoke.clicked.connect(self._revoke_labtools_lan_host_client)
        revoke_row.addWidget(revoke)
        revoke_row.addStretch(1)
        layout.addLayout(revoke_row)

        note = QLabel("Host 只提供本地 LabTools 摘要读取；不同步、不启用 LAN 写入、不自动扣减库存或样本体积。Compatibility read-only 是显式兼容入口，不是默认安全路径。")
        note.setObjectName("labtoolsLanHostBoundaryNote")
        note.setWordWrap(True)
        layout.addWidget(note)
        self._refresh_labtools_lan_host_panel()
        return frame

    def _start_labtools_lan_host(self) -> None:
        compatibility = bool(getattr(self, "_labtools_lan_host_compat_radio", None) and self._labtools_lan_host_compat_radio.isChecked())
        result = labtools_runtime.start_labtools_lan_host(self._labtools_project_root, compatibility_mode=compatibility)
        self._apply_labtools_lan_host_status(result.host_status, message=result.message)

    def _stop_labtools_lan_host(self) -> None:
        result = labtools_runtime.stop_labtools_lan_host(self._labtools_project_root)
        self._apply_labtools_lan_host_status(result.host_status, message=result.message)

    def _create_labtools_lan_host_pairing(self) -> None:
        result = labtools_runtime.create_labtools_lan_host_pairing(self._labtools_project_root, client_label="UIShell manual LAN client")
        self._apply_labtools_lan_host_status(result.host_status, message=result.message)

    def _revoke_labtools_lan_host_client(self) -> None:
        clients = getattr(self, "_labtools_lan_host_clients", None)
        if not isinstance(clients, QListWidget):
            return
        item = clients.currentItem()
        token_id = item.data(Qt.UserRole) if item is not None else ""
        result = labtools_runtime.revoke_labtools_lan_host_client(self._labtools_project_root, str(token_id or ""))
        self._apply_labtools_lan_host_status(result.host_status, message=result.message)

    def _refresh_labtools_lan_host_panel(self) -> None:
        status = labtools_runtime.get_labtools_lan_host_status(self._labtools_project_root)
        self._apply_labtools_lan_host_status(status)

    def _apply_labtools_lan_host_status(self, status: labtools_runtime.LabToolsLanHostStatus, *, message: str | None = None) -> None:
        mode_label = getattr(self, "_labtools_lan_host_mode_label", None)
        pairing_label = getattr(self, "_labtools_lan_host_pairing_label", None)
        clients = getattr(self, "_labtools_lan_host_clients", None)
        if not isinstance(mode_label, QLabel) or not isinstance(pairing_label, QLabel) or not isinstance(clients, QListWidget):
            return
        mode_text = "auth required" if status.auth_required else "compatibility read-only"
        url_text = status.server_url or "未启动"
        mode_label.setText(f"Server mode：{mode_text} · {status.status} · {url_text} · {message or status.message}")
        mode_label.setProperty("serverMode", status.server_mode)
        mode_label.setProperty("status", status.status)
        mode_label.setProperty("authRequired", status.auth_required)
        mode_label.setProperty("compatibilityMode", status.compatibility_mode)
        mode_label.setProperty("readOnly", status.read_only)
        mode_label.setProperty("syncEnabled", status.sync_enabled)
        mode_label.setProperty("writeEnabled", status.write_enabled)
        if status.pairing_code:
            pairing_label.setText(f"Pairing code：{status.pairing_code} · expires {status.pairing_expires_at}")
            pairing_label.setProperty("pairingActive", True)
            pairing_label.setProperty("pairingCode", status.pairing_code)
        else:
            pairing_label.setText("Pairing code：未创建")
            pairing_label.setProperty("pairingActive", False)
            pairing_label.setProperty("pairingCode", "")
        clients.clear()
        if not status.paired_clients:
            empty = QListWidgetItem("No paired clients")
            empty.setData(Qt.UserRole, "")
            clients.addItem(empty)
        for client in status.paired_clients:
            item = QListWidgetItem(f"{client.client_label or 'Unnamed client'} · {client.role} · {client.state} · expires {client.expires_at}")
            item.setData(Qt.UserRole, client.token_id)
            item.setData(Qt.UserRole + 1, client.state)
            clients.addItem(item)

    def _labtools_lan_manual_connection_panel(self, *, page_key: str, semantic_key: str) -> QFrame:
        frame = make_workbench_card(object_name="labtoolsLanManualConnectionPanel", semantic_state="preflight_only")
        frame.setObjectName("labtoolsLanManualConnectionPanel")
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("pageKey", page_key)
        frame.setProperty("semanticKey", semantic_key)
        frame.setProperty("uiPrimitive", "labtools_lan_manual_connection_panel")
        frame.setProperty("readOnly", True)
        frame.setProperty("autoDiscoveryAllowed", False)
        frame.setProperty("cloudSyncAllowed", False)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        layout.addWidget(make_section_title("局域网只读连接 / LAN Read-only", "Manual read-only connection; no sync or auto-discovery."))
        row = QHBoxLayout()
        row.setSpacing(8)
        self._labtools_lan_url_input = QLineEdit("http://127.0.0.1:8787")
        self._labtools_lan_url_input.setObjectName("labtoolsLanServerUrlInput")
        self._labtools_lan_url_input.setProperty("dataSourceMode", "future_lan")
        connect = make_button("手动连接只读 LAN", role="secondary")
        connect.setObjectName("labtoolsLanConnectButton")
        connect.setProperty("dataSourceMode", "future_lan")
        connect.clicked.connect(self._connect_labtools_lan_readonly)
        row.addWidget(self._labtools_lan_url_input, 1)
        row.addWidget(connect)
        layout.addLayout(row)
        pair_row = QHBoxLayout()
        pair_row.setSpacing(8)
        self._labtools_lan_pairing_code_input = QLineEdit()
        self._labtools_lan_pairing_code_input.setObjectName("labtoolsLanPairingCodeInput")
        self._labtools_lan_pairing_code_input.setPlaceholderText("Pairing code")
        self._labtools_lan_pairing_code_input.setMaxLength(8)
        self._labtools_lan_pairing_code_input.setProperty("dataSourceMode", "future_lan")
        pair = make_button("保存本机只读 token", role="secondary")
        pair.setObjectName("labtoolsLanPairButton")
        pair.setProperty("dataSourceMode", "future_lan")
        pair.clicked.connect(self._pair_labtools_lan_readonly)
        pair_row.addWidget(self._labtools_lan_pairing_code_input, 1)
        pair_row.addWidget(pair)
        layout.addLayout(pair_row)
        token_row = QHBoxLayout()
        token_row.setSpacing(8)
        self._labtools_lan_token_status_label = QLabel("Saved token：none")
        self._labtools_lan_token_status_label.setObjectName("labtoolsLanSavedTokenStatusText")
        self._labtools_lan_token_status_label.setProperty("hasSavedToken", False)
        self._labtools_lan_token_status_label.setProperty("authFailed", False)
        self._labtools_lan_token_status_label.setProperty("compatibilityMode", False)
        self._labtools_lan_token_status_label.setWordWrap(True)
        clear_token = make_button("清除 saved token", role="secondary")
        clear_token.setObjectName("labtoolsLanClearTokenButton")
        clear_token.setProperty("dataSourceMode", "future_lan")
        clear_token.clicked.connect(self._clear_labtools_lan_saved_token)
        token_row.addWidget(self._labtools_lan_token_status_label, 1)
        token_row.addWidget(clear_token)
        layout.addLayout(token_row)
        self._labtools_lan_status_label = QLabel("未连接；请输入 LAN read-only URL 后手动连接。不自动发现、不同步、不写入。")
        self._labtools_lan_status_label.setObjectName("labtoolsLanStatusText")
        self._labtools_lan_status_label.setProperty("status", "manual_connection_required")
        self._labtools_lan_status_label.setProperty("dataSourceMode", "future_lan")
        self._labtools_lan_status_label.setWordWrap(True)
        layout.addWidget(self._labtools_lan_status_label)
        self._labtools_lan_count_label = QLabel("reagent 0 · sample 0 · cell 0 · freeze vial 0 · record 0")
        self._labtools_lan_count_label.setObjectName("labtoolsLanCountRow")
        self._labtools_lan_count_label.setProperty("reagentCount", 0)
        self._labtools_lan_count_label.setProperty("sampleCount", 0)
        self._labtools_lan_count_label.setProperty("cellCount", 0)
        self._labtools_lan_count_label.setProperty("recordCount", 0)
        layout.addWidget(self._labtools_lan_count_label)
        note = QLabel("LAN 只读摘要不是同步功能；可手动连接私有 LAN URL，并将 paired viewer token 保存到本机设置文件。不同步、不写入、不自动发现、不启用云端同步。")
        note.setObjectName("labtoolsLanBoundaryNote")
        note.setWordWrap(True)
        layout.addWidget(note)
        feedback_row = QHBoxLayout()
        feedback = make_button("生成 LAN 真实测试反馈报告", role="secondary")
        feedback.setObjectName("labtoolsGenerateLanFeedbackButton")
        feedback.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        feedback.setProperty("feedbackType", "labtools_lan_real_world")
        feedback.setProperty("networkRequestAllowed", False)
        feedback.clicked.connect(self.generate_lan_testing_feedback_template)
        feedback_row.addWidget(feedback)
        feedback_row.addStretch(1)
        layout.addLayout(feedback_row)
        self._refresh_labtools_lan_client_token_status()
        return frame

    def _pair_labtools_lan_readonly(self) -> None:
        url_input = getattr(self, "_labtools_lan_url_input", None)
        code_input = getattr(self, "_labtools_lan_pairing_code_input", None)
        status_label = getattr(self, "_labtools_lan_status_label", None)
        if not isinstance(url_input, QLineEdit) or not isinstance(code_input, QLineEdit) or not isinstance(status_label, QLabel):
            return
        result = labtools_runtime.claim_labtools_lan_pairing(
            url_input.text(),
            code_input.text(),
            client_label="UIShell manual LAN client",
        )
        status_label.setText(f"LAN pairing：{result.status} · {result.message}")
        status_label.setProperty("status", result.status)
        status_label.setProperty("dataSourceMode", "future_lan")
        if result.success:
            code_input.clear()
            self._connect_labtools_lan_readonly()
        else:
            self._refresh_labtools_lan_client_token_status()

    def _clear_labtools_lan_saved_token(self) -> None:
        url_input = getattr(self, "_labtools_lan_url_input", None)
        status_label = getattr(self, "_labtools_lan_status_label", None)
        if not isinstance(url_input, QLineEdit):
            return
        result = labtools_runtime.clear_labtools_lan_credential(url_input.text())
        if isinstance(status_label, QLabel):
            status_label.setText(f"LAN token：{result.status} · {result.message}")
            status_label.setProperty("status", result.status)
            status_label.setProperty("dataSourceMode", "future_lan")
        self._refresh_labtools_lan_client_token_status()

    def _refresh_labtools_lan_client_token_status(self, model: labtools_runtime.LabToolsLocalDataReadModel | None = None) -> None:
        url_input = getattr(self, "_labtools_lan_url_input", None)
        token_label = getattr(self, "_labtools_lan_token_status_label", None)
        if not isinstance(url_input, QLineEdit) or not isinstance(token_label, QLabel):
            return
        credential = labtools_runtime.get_labtools_lan_client_credential_status(url_input.text(), read_model=model)
        if credential.has_saved_token:
            token_label.setText(
                f"Saved token：{credential.status} · role {credential.role or 'viewer'} · "
                f"expires {credential.expires_at or 'unknown'} · {credential.message}"
            )
        elif credential.compatibility_mode:
            token_label.setText("Saved token：none · compatibility read-only connected；当前 host 未要求 token。")
        else:
            token_label.setText(f"Saved token：none · {credential.message}")
        token_label.setProperty("status", credential.status)
        token_label.setProperty("hasSavedToken", credential.has_saved_token)
        token_label.setProperty("tokenRole", credential.role)
        token_label.setProperty("tokenExpiresAt", credential.expires_at)
        token_label.setProperty("authFailed", credential.auth_failed)
        token_label.setProperty("compatibilityMode", credential.compatibility_mode)

    def _connect_labtools_lan_readonly(self) -> None:
        url_input = getattr(self, "_labtools_lan_url_input", None)
        status_label = getattr(self, "_labtools_lan_status_label", None)
        count_label = getattr(self, "_labtools_lan_count_label", None)
        if not isinstance(url_input, QLineEdit) or not isinstance(status_label, QLabel) or not isinstance(count_label, QLabel):
            return
        model = labtools_runtime.get_labtools_lan_read_model(url_input.text())
        self._labtools_lan_read_model = model
        credential = labtools_runtime.get_labtools_lan_client_credential_status(url_input.text(), read_model=model)
        if credential.auth_failed:
            status_text = f"LAN：{model.status.status} · saved token failed，请重新 pairing。{model.status.reason}"
        elif credential.compatibility_mode:
            status_text = f"LAN：{model.status.status} · compatibility read-only risk：host 未要求 token。{model.status.reason}"
        else:
            status_text = f"LAN：{model.status.status} · {model.status.reason}"
        status_label.setText(status_text)
        status_label.setProperty("status", model.status.status)
        status_label.setProperty("dataSourceMode", model.status.data_source_mode)
        status_label.setProperty("authFailed", credential.auth_failed)
        status_label.setProperty("compatibilityMode", credential.compatibility_mode)
        count_label.setText(
            f"reagent {model.status.reagent_count} · sample {model.status.sample_count} · "
            f"cell {model.status.cell_count} · freeze vial {model.status.freeze_vial_count} · record {model.status.record_count}"
        )
        count_label.setProperty("reagentCount", model.status.reagent_count)
        count_label.setProperty("sampleCount", model.status.sample_count)
        count_label.setProperty("cellCount", model.status.cell_count)
        count_label.setProperty("recordCount", model.status.record_count)
        self._refresh_labtools_lan_client_token_status(model)

    def _show_labtools_general_calculator_shell(self) -> None:
        status = labtools_runtime.runtime_status()
        self._labtools_result_widgets: dict[str, dict[str, object]] = {}
        content = QWidget()
        content.setObjectName("labtoolsShellContent")
        content.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        content.setProperty("pageKey", "general_calculators")
        content.setProperty("semanticKey", PageKey.LABTOOLS_GENERAL_CALCULATORS.value)
        content.setProperty("uiPrimitive", "general_calculator_workbench")
        content.setProperty("layoutPolishNoOverlap", True)
        content.setStyleSheet(f"QWidget#labtoolsShellContent {{ background: {GENERAL_CALCULATOR_TOKENS['background']}; }}")
        root = QVBoxLayout(content)
        root.setContentsMargins(22, 15, 22, 0)
        root.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 14)
        header.setSpacing(12)
        title_col = QVBoxLayout()
        title_col.setSpacing(3)
        title_row = QHBoxLayout()
        title_row.setSpacing(7)
        title = QLabel("通用计算器")
        title.setObjectName("labtoolsShellTitle")
        title.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        title.setProperty("semanticKey", PageKey.LABTOOLS_GENERAL_CALCULATORS.value)
        title.setStyleSheet(f"color: {GENERAL_CALCULATOR_TOKENS['text']}; font-size: 20px; font-weight: 800;")
        title_row.addWidget(title)
        slash = QLabel("/")
        slash.setStyleSheet(f"color: {GENERAL_CALCULATOR_TOKENS['faint']}; font-size: 18px;")
        title_row.addWidget(slash)
        english = QLabel("General Calculator")
        english.setStyleSheet(f"color: {GENERAL_CALCULATOR_TOKENS['muted']}; font-size: 16px; font-weight: 700;")
        title_row.addWidget(english)
        title_row.addWidget(make_status_chip("本地测试版", status_key="developer_preview"), 0)
        title_row.addStretch(1)
        subtitle = QLabel("快速计算与动态公式求解，结果需用户复核。")
        subtitle.setObjectName("labtoolsShellSubtitle")
        subtitle.setStyleSheet(f"color: {GENERAL_CALCULATOR_TOKENS['muted']}; font-size: 12px;")
        title_col.addLayout(title_row)
        title_col.addWidget(subtitle)
        header.addLayout(title_col, 1)

        back = make_button("返回首页", role="secondary", size="small")
        back.setObjectName("labtoolsBackButton")
        back.clicked.connect(self._show_labtools_home)
        header.addWidget(back, 0, Qt.AlignTop)
        guide = make_button("使用指南", role="ghost", size="small", enabled=False, semantic_state="disabled")
        guide.setObjectName("labtoolsGeneralGuideButton")
        faq = make_button("常见问题", role="ghost", size="small", enabled=False, semantic_state="disabled")
        faq.setObjectName("labtoolsGeneralFaqButton")
        header.addWidget(guide, 0, Qt.AlignTop)
        header.addWidget(faq, 0, Qt.AlignTop)
        user = QLabel("Researcher")
        user.setObjectName("labtoolsGeneralUserBadge")
        user.setAlignment(Qt.AlignCenter)
        user.setStyleSheet(
            f"background: {GENERAL_CALCULATOR_TOKENS['surface']}; border: 1px solid {GENERAL_CALCULATOR_TOKENS['border']}; "
            f"border-radius: 8px; color: {GENERAL_CALCULATOR_TOKENS['text']}; font-size: 12px; font-weight: 650; padding: 8px 13px;"
        )
        header.addWidget(user, 0, Qt.AlignTop)
        root.addLayout(header)
        if not status.available:
            root.addWidget(self._labtools_notice_card(status.message, object_name="labtoolsAdapterNotice", semantic_key=PageKey.LABTOOLS_GENERAL_CALCULATORS.value))
            root.addStretch(1)
            self._set_labtools_content(content)
            return

        mode_row = QHBoxLayout()
        mode_row.setContentsMargins(0, 0, 0, 12)
        mode_row.setSpacing(8)
        quick_button = make_button("快速计算", role="secondary", size="small")
        quick_button.setObjectName("labtoolsGeneralModeButton")
        quick_button.setProperty("modeKey", "quick_calculator")
        formula_button = make_button("动态公式求解", role="secondary", size="small")
        formula_button.setObjectName("labtoolsGeneralModeButton")
        formula_button.setProperty("modeKey", "formula_solver")
        mode_row.addWidget(quick_button)
        mode_row.addWidget(formula_button)
        mode_row.addWidget(make_status_chip("需复核", status_key="testing" if status.available else "blocked"), 0)
        mode_row.addStretch(1)
        root.addLayout(mode_row)

        self._labtools_general_stack = QStackedWidget()
        self._labtools_general_stack.setObjectName("labtoolsGeneralCalculatorStack")
        self._labtools_general_stack.setStyleSheet("QStackedWidget#labtoolsGeneralCalculatorStack { background: transparent; border: 0; }")
        quick_page = self._build_labtools_quick_calculator_page()
        formula_page = self._build_labtools_formula_solver_page()
        self._labtools_general_stack.addWidget(quick_page)
        self._labtools_general_stack.addWidget(formula_page)
        quick_button.clicked.connect(lambda: self._labtools_general_stack.setCurrentWidget(quick_page))
        formula_button.clicked.connect(lambda: self._labtools_general_stack.setCurrentWidget(formula_page))
        root.addWidget(self._labtools_general_stack, 1)
        root.addWidget(
            self._labtools_notice_card(
                "本工具提供计算辅助，不替代实验设计与结果判断。请在正式实验前自行确认单位、浓度、体积与操作条件。",
                object_name="labtoolsReviewNotice",
                semantic_key=PageKey.LABTOOLS_GENERAL_CALCULATORS.value,
            )
        )
        self._set_labtools_content(content)

    def _build_labtools_quick_calculator_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("labtoolsQuickCalculatorPage")
        page.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        page.setProperty("pageKey", "quick_calculator")
        page.setProperty("semanticKey", "labtools.page.quick_calculator")
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        selector_card = QFrame()
        selector_card.setObjectName("labtoolsCalculatorSelectorCard")
        selector_card.setFixedWidth(220)
        selector_card.setStyleSheet(
            f"QFrame#labtoolsCalculatorSelectorCard {{ border: 1px solid {GENERAL_CALCULATOR_TOKENS['border']}; border-radius: 0; background: {GENERAL_CALCULATOR_TOKENS['surface']}; }}"
        )
        selector_layout = QVBoxLayout(selector_card)
        selector_layout.setContentsMargins(15, 15, 15, 15)
        selector_layout.setSpacing(10)
        section_title = QLabel("计算任务")
        section_title.setObjectName("labtoolsCalculatorTaskTitle")
        section_title.setStyleSheet(f"color: {GENERAL_CALCULATOR_TOKENS['text']}; font-size: 13px; font-weight: 800;")
        selector_layout.addWidget(section_title)
        search = QLineEdit()
        search.setObjectName("labtoolsCalculatorTaskSearchInput")
        search.setPlaceholderText("搜索计算任务...")
        search.setMinimumHeight(30)
        search.setStyleSheet(
            f"background: {GENERAL_CALCULATOR_TOKENS['surface_subtle']}; border: 1px solid {GENERAL_CALCULATOR_TOKENS['border']}; border-radius: 8px; padding: 5px 10px;"
        )
        selector_layout.addWidget(search)
        self._labtools_quick_task_combo = QComboBox()
        self._labtools_quick_task_combo.setObjectName("labtoolsQuickTaskCombo")
        self._labtools_quick_task_combo.setProperty("pageKey", "quick_calculator")
        for task in labtools_runtime.list_quick_tasks():
            label = f"{task.title} · {task.category}"
            self._labtools_quick_task_combo.addItem(label, task.task_id)
        self._labtools_quick_task_combo.setVisible(False)
        selector_layout.addWidget(self._labtools_quick_task_combo)
        for task in labtools_runtime.list_quick_tasks():
            task_button = make_button(f"{task.title}\n{task.description}", role="ghost", size="small", semantic_state="testing")
            task_button.setObjectName("labtoolsCalculatorTaskItem")
            task_button.setProperty("taskId", task.task_id)
            task_button.setMinimumHeight(48)
            task_button.setStyleSheet(
                f"""
                QPushButton#labtoolsCalculatorTaskItem {{
                    text-align: left;
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: 10px;
                    color: {GENERAL_CALCULATOR_TOKENS['text']};
                    padding: 6px 10px;
                    font-size: 11px;
                }}
                QPushButton#labtoolsCalculatorTaskItem:hover {{
                    background: {GENERAL_CALCULATOR_TOKENS['blue_soft']};
                }}
                """
            )
            task_button.clicked.connect(lambda _checked=False, item=task.task_id: self._select_labtools_quick_task(item))
            selector_layout.addWidget(task_button)
        description = QLabel()
        description.setObjectName("labtoolsQuickTaskDescription")
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {GENERAL_CALCULATOR_TOKENS['muted']}; font-size: 11px;")
        selector_layout.addWidget(description)
        selector_layout.addStretch(1)
        layout.addWidget(selector_card)

        form_card = QFrame()
        form_card.setObjectName("labtoolsCalculatorFormCard")
        form_card.setStyleSheet(
            f"QFrame#labtoolsCalculatorFormCard {{ border: 1px solid {GENERAL_CALCULATOR_TOKENS['border']}; border-radius: 12px; background: {GENERAL_CALCULATOR_TOKENS['surface']}; }}"
        )
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(20, 18, 20, 18)
        form_layout.setSpacing(12)
        self._labtools_quick_form_layout = form_layout
        layout.addWidget(form_card, 2)

        result_card = self._labtools_result_panel(page_key="quick_calculator", semantic_key="labtools.page.quick_calculator")
        layout.addWidget(result_card, 2)

        self._labtools_quick_task_combo.currentIndexChanged.connect(lambda _index: self._populate_labtools_quick_form(description))
        self._populate_labtools_quick_form(description)
        return page

    def _build_labtools_formula_solver_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("labtoolsFormulaSolverPage")
        page.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        page.setProperty("pageKey", "formula_solver")
        page.setProperty("semanticKey", "labtools.page.formula_solver")
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        selector_card = QFrame()
        selector_card.setObjectName("labtoolsFormulaSelectorCard")
        selector_card.setFixedWidth(220)
        selector_card.setStyleSheet(
            f"QFrame#labtoolsFormulaSelectorCard {{ border: 1px solid {GENERAL_CALCULATOR_TOKENS['border']}; border-radius: 0; background: {GENERAL_CALCULATOR_TOKENS['surface']}; }}"
        )
        selector_layout = QVBoxLayout(selector_card)
        selector_layout.setContentsMargins(15, 15, 15, 15)
        selector_layout.setSpacing(10)
        formula_title = QLabel("动态公式求解")
        formula_title.setObjectName("labtoolsFormulaSelectorTitle")
        formula_title.setStyleSheet(f"color: {GENERAL_CALCULATOR_TOKENS['text']}; font-size: 13px; font-weight: 800;")
        selector_layout.addWidget(formula_title)
        self._labtools_formula_combo = QComboBox()
        self._labtools_formula_combo.setObjectName("labtoolsFormulaSpecCombo")
        for spec in labtools_runtime.list_formula_specs():
            self._labtools_formula_combo.addItem(spec.short_title, spec.spec_id)
        self._labtools_formula_combo.setMinimumHeight(32)
        selector_layout.addWidget(self._labtools_formula_combo)
        self._labtools_formula_description = QLabel()
        self._labtools_formula_description.setObjectName("labtoolsFormulaDescription")
        self._labtools_formula_description.setWordWrap(True)
        self._labtools_formula_description.setStyleSheet(f"color: {GENERAL_CALCULATOR_TOKENS['muted']}; font-size: 11px;")
        selector_layout.addWidget(self._labtools_formula_description)
        self._labtools_formula_expression = QLabel()
        self._labtools_formula_expression.setObjectName("labtoolsFormulaExpression")
        self._labtools_formula_expression.setWordWrap(True)
        self._labtools_formula_expression.setStyleSheet(
            f"background: {GENERAL_CALCULATOR_TOKENS['surface_subtle']}; border: 1px solid {GENERAL_CALCULATOR_TOKENS['border']}; "
            f"border-radius: 8px; color: {GENERAL_CALCULATOR_TOKENS['text']}; padding: 8px; font-size: 11px;"
        )
        selector_layout.addWidget(self._labtools_formula_expression)
        selector_layout.addStretch(1)
        layout.addWidget(selector_card)

        form_card = QFrame()
        form_card.setObjectName("labtoolsFormulaFormCard")
        form_card.setStyleSheet(
            f"QFrame#labtoolsFormulaFormCard {{ border: 1px solid {GENERAL_CALCULATOR_TOKENS['border']}; border-radius: 12px; background: {GENERAL_CALCULATOR_TOKENS['surface']}; }}"
        )
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(20, 18, 20, 18)
        form_layout.setSpacing(12)
        self._labtools_formula_form_layout = form_layout
        layout.addWidget(form_card, 2)

        result_card = self._labtools_result_panel(page_key="formula_solver", semantic_key="labtools.page.formula_solver")
        layout.addWidget(result_card, 2)

        self._labtools_formula_combo.currentIndexChanged.connect(lambda _index: self._populate_labtools_formula_form())
        self._populate_labtools_formula_form()
        return page

    def _select_labtools_quick_task(self, task_id: str) -> None:
        combo = getattr(self, "_labtools_quick_task_combo", None)
        if not isinstance(combo, QComboBox):
            return
        index = combo.findData(task_id)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _open_labtools_quick_task(self, task_id: str) -> None:
        self._show_labtools_general_calculator_shell()
        self._select_labtools_quick_task(task_id)

    def _populate_labtools_quick_form(self, description_label: QLabel) -> None:
        task_id = self._labtools_quick_task_combo.currentData()
        task = labtools_runtime.get_quick_task(task_id)
        description_label.setText(task.description + (" 细胞铺板仅计算辅助，不进入细胞记录保存。" if task.task_id == "quick_cell_seeding" else ""))
        self._clear_layout(self._labtools_quick_form_layout)
        self._labtools_quick_inputs: dict[str, QLineEdit] = {}
        self._labtools_quick_units: dict[str, QComboBox] = {}
        header = QLabel(task.title)
        header.setObjectName("labtoolsQuickFormTitle")
        header.setStyleSheet(f"color: {GENERAL_CALCULATOR_TOKENS['text']}; font-size: 15px; font-weight: 800;")
        self._labtools_quick_form_layout.addWidget(header)
        badge = make_status_chip("快速计算", status_key="testing")
        self._labtools_quick_form_layout.addWidget(badge, 0, Qt.AlignLeft)
        for field_id in task.input_field_ids:
            self._labtools_quick_form_layout.addLayout(
                self._labtools_input_row(
                    field_id=field_id,
                    label=labtools_runtime.quick_field_label(field_id),
                    default_value=labtools_runtime.quick_field_default(field_id),
                    units=labtools_runtime.quick_field_units(field_id),
                    input_store=self._labtools_quick_inputs,
                    unit_store=self._labtools_quick_units,
                    object_prefix="labtoolsQuick",
                    disabled=field_id == "mass" and task.calculator_name == "solve_solution_preparation_formula",
                )
            )
        if task.task_id == "quick_cell_seeding":
            self._labtools_quick_form_layout.addWidget(self._labtools_notice_card("细胞铺板仅计算辅助；不保存细胞实验记录。", object_name="labtoolsAdapterNotice", semantic_key="labtools.page.quick_calculator"))
        calculate = make_button("计算", role="primary")
        calculate.setObjectName("labtoolsQuickCalculateButton")
        calculate.setMinimumHeight(36)
        calculate.clicked.connect(self._run_labtools_quick_calculation)
        self._labtools_quick_form_layout.addWidget(calculate)
        self._labtools_quick_form_layout.addStretch(1)
        self._set_labtools_result_empty("请选择任务并输入参数。", page_key="quick_calculator")

    def _populate_labtools_formula_form(self) -> None:
        spec_id = self._labtools_formula_combo.currentData()
        spec = labtools_runtime.get_formula_spec(spec_id)
        self._labtools_formula_description.setText(spec.description)
        self._labtools_formula_expression.setText(f"公式：{spec.equation}")
        self._clear_layout(self._labtools_formula_form_layout)
        self._labtools_formula_inputs: dict[str, QLineEdit] = {}
        self._labtools_formula_units: dict[str, QComboBox] = {}
        self._labtools_formula_target_group = QButtonGroup(self)
        self._labtools_formula_target_group.setObjectName("labtoolsFormulaSolveTargetGroup")
        target_label = QLabel("求解目标")
        target_label.setStyleSheet(f"color: {GENERAL_CALCULATOR_TOKENS['text']}; font-size: 13px; font-weight: 800;")
        self._labtools_formula_form_layout.addWidget(target_label)
        target_row = QHBoxLayout()
        for target in spec.solve_targets:
            button = QRadioButton(target.label)
            button.setObjectName("labtoolsFormulaSolveTarget")
            button.setProperty("targetId", target.target_id)
            button.setProperty("semanticKey", "labtools.page.formula_solver")
            self._labtools_formula_target_group.addButton(button)
            target_row.addWidget(button)
            if target.target_id == spec.default_solve_target:
                button.setChecked(True)
        target_row.addStretch(1)
        self._labtools_formula_form_layout.addLayout(target_row)
        for button in self._labtools_formula_target_group.buttons():
            button.toggled.connect(lambda checked, target_button=button: checked and self._sync_formula_target_fields(target_button.property("targetId")))
        for field in spec.fields:
            self._labtools_formula_form_layout.addLayout(
                self._labtools_input_row(
                    field_id=field.field_id,
                    label=field.label,
                    default_value="" if field.field_id == spec.default_solve_target else self._formula_default_value(field.field_id),
                    units=labtools_runtime.supported_units_for_formula_field(field),
                    input_store=self._labtools_formula_inputs,
                    unit_store=self._labtools_formula_units,
                    object_prefix="labtoolsFormula",
                    disabled=field.field_id == spec.default_solve_target,
                    placeholder=field.placeholder,
                    selected_unit=field.default_unit,
                )
            )
        calculate = make_button("求解", role="primary")
        calculate.setObjectName("labtoolsFormulaCalculateButton")
        calculate.setMinimumHeight(36)
        calculate.clicked.connect(self._run_labtools_formula_solver)
        self._labtools_formula_form_layout.addWidget(calculate)
        self._labtools_formula_form_layout.addStretch(1)
        self._sync_formula_target_fields(spec.default_solve_target)
        self._set_labtools_result_empty("请选择公式和求解目标。", page_key="formula_solver")

    def _labtools_input_row(
        self,
        *,
        field_id: str,
        label: str,
        default_value: str,
        units: tuple[str, ...],
        input_store: dict[str, QLineEdit],
        unit_store: dict[str, QComboBox],
        object_prefix: str,
        disabled: bool = False,
        placeholder: str = "",
        selected_unit: str = "",
    ) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        label_widget = QLabel(label)
        label_widget.setObjectName(f"{object_prefix}InputLabel")
        label_widget.setProperty("fieldId", field_id)
        label_widget.setMinimumWidth(118)
        label_widget.setStyleSheet(f"color: {GENERAL_CALCULATOR_TOKENS['text']}; font-size: 12px; font-weight: 650;")
        row.addWidget(label_widget)
        field = QLineEdit(default_value)
        field.setObjectName(f"{object_prefix}Input")
        field.setProperty("fieldId", field_id)
        field.setPlaceholderText(placeholder)
        field.setEnabled(not disabled)
        field.setMinimumHeight(34)
        field.setStyleSheet(
            f"background: {GENERAL_CALCULATOR_TOKENS['surface_subtle']}; border: 1px solid {GENERAL_CALCULATOR_TOKENS['border']}; "
            f"border-radius: 8px; padding: 6px 10px; color: {GENERAL_CALCULATOR_TOKENS['text']};"
        )
        input_store[field_id] = field
        row.addWidget(field, 1)
        if units:
            combo = QComboBox()
            combo.setObjectName(f"{object_prefix}UnitSelector")
            combo.setProperty("fieldId", field_id)
            combo.addItems(list(units))
            combo.setMinimumHeight(32)
            combo.setStyleSheet(
                f"background: {GENERAL_CALCULATOR_TOKENS['surface_subtle']}; border: 1px solid {GENERAL_CALCULATOR_TOKENS['border']}; "
                f"border-radius: 8px; padding: 4px 8px;"
            )
            if selected_unit:
                index = combo.findText(selected_unit)
                if index >= 0:
                    combo.setCurrentIndex(index)
            unit_store[field_id] = combo
            row.addWidget(combo)
        return row

    def _labtools_result_panel(self, *, page_key: str, semantic_key: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("labtoolsResultPanel")
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("pageKey", page_key)
        frame.setProperty("semanticKey", semantic_key)
        frame.setProperty("uiPrimitive", "result_panel")
        frame.setProperty("formalResult", False)
        frame.setProperty("reportGenerationAllowed", False)
        frame.setProperty("exportAllowed", False)
        frame.setFixedWidth(260)
        frame.setStyleSheet(
            f"QFrame#labtoolsResultPanel {{ border: 1px solid {GENERAL_CALCULATOR_TOKENS['border']}; border-radius: 12px; background: {GENERAL_CALCULATOR_TOKENS['surface']}; }}"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        header = QHBoxLayout()
        title = QLabel("计算结果")
        title.setObjectName("labtoolsResultPanelTitle")
        title.setStyleSheet(f"color: {GENERAL_CALCULATOR_TOKENS['text']}; font-size: 14px; font-weight: 800;")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(make_status_chip("可计算 · 需复核", status_key="testing", semantic_state="testing"))
        layout.addLayout(header)
        result_primary = QLabel("等待输入")
        result_primary.setObjectName("labtoolsResultPrimary")
        result_primary.setProperty("pageKey", page_key)
        result_primary.setWordWrap(True)
        result_primary.setStyleSheet(
            f"font-size: 20px; font-weight: 800; color: {GENERAL_CALCULATOR_TOKENS['green']}; "
            f"background: {GENERAL_CALCULATOR_TOKENS['green_soft']}; border: 1px solid #BBF7D0; border-radius: 12px; padding: 14px;"
        )
        layout.addWidget(result_primary)
        result_text = QPlainTextEdit()
        result_text.setObjectName("labtoolsResultText")
        result_text.setProperty("pageKey", page_key)
        result_text.setReadOnly(True)
        result_text.setMinimumHeight(154)
        result_text.setStyleSheet(
            f"background: {GENERAL_CALCULATOR_TOKENS['surface_subtle']}; border: 1px solid {GENERAL_CALCULATOR_TOKENS['border']}; "
            f"border-radius: 10px; color: {GENERAL_CALCULATOR_TOKENS['text']}; font-size: 12px;"
        )
        layout.addWidget(result_text)
        issue_label = QLabel(labtools_runtime.REVIEW_NOTICE)
        issue_label.setObjectName("labtoolsIssueRows")
        issue_label.setProperty("pageKey", page_key)
        issue_label.setWordWrap(True)
        issue_label.setStyleSheet(
            f"background: {GENERAL_CALCULATOR_TOKENS['amber_soft']}; border: 1px solid #FDE68A; border-radius: 10px; "
            f"color: {GENERAL_CALCULATOR_TOKENS['amber']}; padding: 10px; font-size: 11px;"
        )
        layout.addWidget(issue_label)
        actions_title = QLabel("操作")
        actions_title.setObjectName("labtoolsResultActionsTitle")
        actions_title.setStyleSheet(f"color: {GENERAL_CALCULATOR_TOKENS['text']}; font-size: 13px; font-weight: 800;")
        layout.addWidget(actions_title)
        actions = QVBoxLayout()
        actions.setSpacing(8)
        copy_button = make_button("复制结果", role="primary_action")
        copy_button.setObjectName("labtoolsCopyResultButton")
        copy_button.setProperty("pageKey", page_key)
        copy_button.clicked.connect(lambda _checked=False, key=page_key: self._copy_labtools_result(key))
        save_button = make_button("保存到历史 - 需适配", role="disabled_action")
        save_button.setObjectName("labtoolsSaveHistoryButton")
        save_button.setProperty("pageKey", page_key)
        save_button.clicked.connect(lambda _checked=False, key=page_key: self._save_labtools_calculation_record(key))
        self._set_storage_gated_button_state(save_button, bool(self._labtools_project_root), "disabled_missing_storage_adapter")
        export_button = make_button("导出结果 - 暂未开放", role="disabled_action")
        export_button.setObjectName("labtoolsExportResultButton")
        export_button.setProperty("pageKey", page_key)
        export_button.setEnabled(False)
        export_button.setProperty("disabledState", "future")
        copy_button.setMinimumHeight(36)
        save_button.setMinimumHeight(34)
        export_button.setMinimumHeight(34)
        actions.addWidget(copy_button)
        actions.addWidget(save_button)
        actions.addWidget(export_button)
        layout.addLayout(actions)
        layout.addStretch(1)
        self._labtools_result_widgets[page_key] = {
            "primary": result_primary,
            "text": result_text,
            "issue": issue_label,
            "copy_text": "",
            "last_result": None,
        }
        return frame

    def _run_labtools_quick_calculation(self) -> None:
        task_id = self._labtools_quick_task_combo.currentData()
        values = {field_id: widget.text().strip() for field_id, widget in self._labtools_quick_inputs.items()}
        units = {field_id: combo.currentText() for field_id, combo in self._labtools_quick_units.items()}
        self._render_labtools_result(labtools_runtime.execute_quick_task(task_id, values, units), page_key="quick_calculator")

    def _run_labtools_formula_solver(self) -> None:
        spec_id = self._labtools_formula_combo.currentData()
        target = self._selected_formula_target()
        values = {field_id: widget.text().strip() for field_id, widget in self._labtools_formula_inputs.items()}
        units = {field_id: combo.currentText() for field_id, combo in self._labtools_formula_units.items()}
        self._render_labtools_result(labtools_runtime.execute_formula(spec_id, target, values, units), page_key="formula_solver")

    def _render_labtools_result(self, result: labtools_runtime.LabToolsUiResult, *, page_key: str) -> None:
        widgets = self._labtools_result_widgets[page_key]
        result_primary = widgets["primary"]
        result_text = widgets["text"]
        issue_label = widgets["issue"]
        assert isinstance(result_primary, QLabel)
        assert isinstance(result_text, QPlainTextEdit)
        assert isinstance(issue_label, QLabel)
        result_primary.setText(result.primary_result)
        result_text.setPlainText(result.detail_text)
        issues = list(result.errors) + list(result.warnings)
        issue_label.setText("\n".join(f"- {issue}" for issue in issues))
        issue_label.setProperty("hasError", bool(result.errors))
        widgets["copy_text"] = result.copy_text if result.valid else ""
        widgets["last_result"] = result if result.valid else None

    def _set_labtools_result_empty(self, message: str, *, page_key: str) -> None:
        if hasattr(self, "_labtools_result_widgets") and page_key in self._labtools_result_widgets:
            widgets = self._labtools_result_widgets[page_key]
            result_primary = widgets["primary"]
            result_text = widgets["text"]
            issue_label = widgets["issue"]
            assert isinstance(result_primary, QLabel)
            assert isinstance(result_text, QPlainTextEdit)
            assert isinstance(issue_label, QLabel)
            result_primary.setText(message)
            result_text.setPlainText("")
            issue_label.setText(labtools_runtime.REVIEW_NOTICE)
            issue_label.setProperty("hasError", False)
            widgets["copy_text"] = ""
            widgets["last_result"] = None

    def _copy_labtools_result(self, page_key: str) -> None:
        from PySide6.QtWidgets import QApplication

        copy_text = self._labtools_result_widgets.get(page_key, {}).get("copy_text", "")
        if copy_text:
            QApplication.clipboard().setText(str(copy_text))

    def _save_labtools_calculation_record(self, page_key: str) -> None:
        widgets = self._labtools_result_widgets.get(page_key, {})
        issue_label = widgets.get("issue")
        result = widgets.get("last_result")
        if not isinstance(issue_label, QLabel) or not isinstance(result, labtools_runtime.LabToolsUiResult):
            return
        record_type = "formula_solver" if page_key == "formula_solver" else "quick_calculation"
        write_result = labtools_runtime.create_local_record_summary(
            self._labtools_project_root,
            {
                "record_type": record_type,
                "title": result.title,
                "summary": result.primary_result,
                "artifact_refs": [f"ui:{page_key}:local-summary-only"],
                "status": "draft",
            },
        )
        self._report_labtools_local_write_result(write_result, issue_label)
        self._labtools_local_data_read_model = labtools_runtime.get_labtools_local_data_read_model(self._labtools_project_root)

    def _selected_formula_target(self) -> str:
        for button in self._labtools_formula_target_group.buttons():
            if button.isChecked():
                return str(button.property("targetId"))
        return ""

    def _sync_formula_target_fields(self, target_id: str) -> None:
        for field_id, widget in self._labtools_formula_inputs.items():
            is_target = field_id == target_id
            widget.setEnabled(not is_target)
            if is_target:
                widget.setText("")
            elif not widget.text():
                widget.setText(self._formula_default_value(field_id))

    def _formula_default_value(self, field_id: str) -> str:
        return {
            "mass_concentration": "1",
            "molar_concentration": "10",
            "molecular_weight": "180.16",
            "stock_concentration": "100",
            "stock_volume": "100",
            "target_concentration": "10",
            "final_volume": "1",
            "mass": "58.44",
            "concentration": "100",
            "volume": "10",
            "percent": "1",
            "percent_type": "w/v",
            "solute_amount": "1",
            "total_amount": "100",
            "start_concentration": "100",
            "dilution_factor": "10",
            "levels": "6",
            "final_volume_per_level": "100",
        }.get(field_id, "")

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            if child_layout is not None:
                self._clear_layout(child_layout)

    def _show_labtools_reagent_preparation_shell(self) -> None:
        semantic_key = PageKey.LABTOOLS_REAGENT_PREPARATION.value
        self._labtools_storage_state = labtools_runtime.get_labtools_storage_adapter_status(self._labtools_project_root)
        content = QWidget()
        content.setObjectName("labtoolsShellContent")
        content.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        content.setProperty("pageKey", "reagent_preparation")
        content.setProperty("semanticKey", semantic_key)
        content.setProperty("uiPrimitive", "labtools_reagent_preparation_page")
        content.setProperty("layoutPolishNoOverlap", True)
        content.setStyleSheet(f"QWidget#labtoolsShellContent {{ background: {REAGENT_PREP_TOKENS['background']}; }}")
        root = QVBoxLayout(content)
        root.setContentsMargins(15, 10, 15, 10)
        root.setSpacing(9)

        header = QHBoxLayout()
        header.setSpacing(12)
        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title = QLabel("试剂制备")
        title.setObjectName("labtoolsShellTitle")
        title.setStyleSheet(f"color: {REAGENT_PREP_TOKENS['text']}; font-size: 22px; font-weight: 850;")
        slash = QLabel("/")
        slash.setStyleSheet(f"color: {REAGENT_PREP_TOKENS['faint']}; font-size: 18px;")
        english = QLabel("Reagent Preparation")
        english.setStyleSheet(f"color: {REAGENT_PREP_TOKENS['muted']}; font-size: 16px; font-weight: 700;")
        title_row.addWidget(title)
        title_row.addWidget(slash)
        title_row.addWidget(english)
        title_row.addWidget(make_status_chip("本地测试版", status_key="developer_preview"))
        title_row.addWidget(make_status_chip("需复核", status_key="testing"))
        title_row.addStretch(1)
        title_block.addLayout(title_row)
        subtitle = QLabel("试剂模板、本次配制与复核清单，计算结果需用户复核后用于实验。")
        subtitle.setObjectName("labtoolsShellSubtitle")
        subtitle.setStyleSheet(f"color: {REAGENT_PREP_TOKENS['muted']}; font-size: 12px;")
        subtitle.setWordWrap(True)
        title_block.addWidget(subtitle)
        header.addLayout(title_block, 1)
        back = make_button("返回 LabTools 首页", role="secondary")
        back.setObjectName("labtoolsBackButton")
        back.clicked.connect(self._show_labtools_home)
        back.setStyleSheet(
            f"background: {REAGENT_PREP_TOKENS['surface']}; border: 1px solid {REAGENT_PREP_TOKENS['border']}; "
            f"border-radius: 8px; color: {REAGENT_PREP_TOKENS['text']}; font-size: 12px; font-weight: 650; padding: 8px 13px;"
        )
        header.addWidget(back, 0, Qt.AlignTop)
        root.addLayout(header)

        try:
            templates = labtools_runtime.list_reagent_templates(self._labtools_project_root)
        except Exception as exc:
            root.addWidget(
                make_empty_state(
                    "试剂模板暂不可用",
                    f"LabTools reagent backend 未就绪：{exc}",
                    empty_state_key="empty_missing_resource",
                    semantic_key=semantic_key,
                )
            )
            self._set_labtools_content(content)
            return

        self._labtools_reagent_templates = {template.template_id: template for template in templates}
        self._labtools_reagent_selected_template_id = templates[0].template_id if templates else ""
        self._labtools_local_data_read_model = labtools_runtime.get_labtools_local_data_read_model(self._labtools_project_root)
        self._labtools_selected_local_reagent_id = ""
        left_column = QWidget()
        left_column.setObjectName("labtoolsReagentLeftColumn")
        left_column.setProperty("uiPrimitive", "workbench_secondary_column")
        left_column.setProperty("layoutPolishNoOverlap", True)
        left_column.setMinimumWidth(252)
        left_column.setMaximumWidth(300)
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        left_layout.addWidget(self._labtools_reagent_template_list_panel(templates))
        local_reagent_panel = self._labtools_local_reagent_list_panel(self._labtools_local_data_read_model)
        local_reagent_panel.setVisible(False)
        left_layout.addWidget(local_reagent_panel)
        run_panel = self._labtools_reagent_run_panel()
        run_panel.setMinimumWidth(420)
        detail_panel = self._labtools_reagent_detail_panel()
        detail_panel.setMinimumWidth(280)
        detail_panel.setMaximumWidth(360)
        root.addWidget(
            make_left_list_middle_form_right_preview(
                list_widget=left_column,
                form_widget=run_panel,
                preview_widget=detail_panel,
                object_name="labtoolsReagentWorkbenchColumns",
                sizes=(252, 434, 296),
            )
        )
        root.addWidget(self._labtools_reagent_action_bar())
        root.addWidget(
            self._labtools_notice_card(
                "提示：保存路径由 BioMedPilot 存储适配器提供，当前桌面 UI 不默认写入个人目录。",
                object_name="labtoolsAdapterNotice",
                semantic_key=semantic_key,
            )
        )
        root.addWidget(
            self._labtools_notice_card(
                "实验计算结果需由用户复核后用于台面操作。请核对 SOP、试剂纯度、pH、温度和安全要求。",
                object_name="labtoolsReviewNotice",
                semantic_key=semantic_key,
            )
        )
        history_panel = self._labtools_reagent_history_panel()
        history_panel.setVisible(False)
        root.addWidget(history_panel)
        root.addStretch(1)
        self._set_labtools_content(content)
        if templates:
            self._select_labtools_reagent_template(self._labtools_reagent_selected_template_id)
            self._run_labtools_reagent_preparation()
        self._refresh_labtools_reagent_history()

    def _labtools_reagent_template_list_panel(self, templates: tuple[labtools_runtime.ReagentTemplateSummary, ...]) -> QFrame:
        frame = QFrame()
        frame.setObjectName("labtoolsReagentTemplateListPanel")
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("pageKey", "reagent_preparation")
        frame.setProperty("semanticKey", PageKey.LABTOOLS_REAGENT_PREPARATION.value)
        frame.setStyleSheet(
            f"QFrame#labtoolsReagentTemplateListPanel {{ border: 1px solid {REAGENT_PREP_TOKENS['border']}; "
            f"border-radius: 12px; background: {REAGENT_PREP_TOKENS['surface']}; }}"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 13, 14, 13)
        layout.setSpacing(10)
        header_row = QHBoxLayout()
        header = QLabel("试剂模板")
        header.setStyleSheet(f"color: {REAGENT_PREP_TOKENS['text']}; font-size: 14px; font-weight: 850;")
        add_marker = QLabel("+")
        add_marker.setAlignment(Qt.AlignCenter)
        add_marker.setFixedSize(24, 24)
        add_marker.setStyleSheet(
            f"background: {REAGENT_PREP_TOKENS['blue_soft']}; color: {REAGENT_PREP_TOKENS['blue']}; "
            "border-radius: 8px; font-size: 15px; font-weight: 850;"
        )
        header_row.addWidget(header)
        header_row.addStretch(1)
        header_row.addWidget(add_marker)
        layout.addLayout(header_row)
        search = QLineEdit()
        search.setObjectName("labtoolsReagentSearchInput")
        search.setPlaceholderText("搜索模板名称、分类或备注...")
        search.setMinimumHeight(34)
        search.setStyleSheet(
            f"background: {REAGENT_PREP_TOKENS['surface_subtle']}; border: 1px solid {REAGENT_PREP_TOKENS['border']}; "
            f"border-radius: 8px; padding: 6px 10px; color: {REAGENT_PREP_TOKENS['text']};"
        )
        layout.addWidget(search)
        filter_row = QHBoxLayout()
        category_filter = QComboBox()
        category_filter.addItems(["全部分类", "Buffer", "Solution"])
        sort_filter = QComboBox()
        sort_filter.addItems(["最近编辑", "名称排序"])
        for widget in (category_filter, sort_filter):
            widget.setMinimumHeight(30)
            widget.setStyleSheet(
                f"background: {REAGENT_PREP_TOKENS['surface']}; border: 1px solid {REAGENT_PREP_TOKENS['border']}; "
                f"border-radius: 8px; padding: 4px 8px; color: {REAGENT_PREP_TOKENS['muted']};"
            )
            filter_row.addWidget(widget, 1)
        layout.addLayout(filter_row)
        if not templates:
            layout.addWidget(make_empty_state("暂无模板", "未接入存储适配前不读取真实模板库。", empty_state_key="empty_project", semantic_key=PageKey.LABTOOLS_REAGENT_PREPARATION.value))
        for template in templates:
            row = QPushButton(
                f"{template.name}\n{template.category} · volume {template.default_volume} · {template.component_count} components"
            )
            row.setObjectName("labtoolsReagentTemplateRow")
            row.setProperty("templateId", template.template_id)
            row.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
            row.setProperty("pageKey", "reagent_preparation")
            row.setProperty("semanticKey", PageKey.LABTOOLS_REAGENT_PREPARATION.value)
            row.setMinimumHeight(72)
            row.setStyleSheet(
                f"QPushButton#labtoolsReagentTemplateRow {{ background: {REAGENT_PREP_TOKENS['surface']}; "
                f"border: 1px solid {REAGENT_PREP_TOKENS['border']}; border-radius: 10px; color: {REAGENT_PREP_TOKENS['text']}; "
                "font-size: 12px; font-weight: bold; padding: 10px; }"
            )
            row.clicked.connect(lambda _checked=False, item=template.template_id: self._select_labtools_reagent_template(item))
            layout.addWidget(row)
            status = make_status_chip("示例模板 / 需存储适配", status_key="planned")
            status.setProperty("templateId", template.template_id)
            layout.addWidget(status)
        layout.addStretch(1)
        return frame

    def _labtools_local_reagent_list_panel(self, model: labtools_runtime.LabToolsLocalDataReadModel) -> QFrame:
        frame = QFrame()
        frame.setObjectName("labtoolsLocalReagentPanel")
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("pageKey", "reagent_preparation")
        frame.setProperty("semanticKey", PageKey.LABTOOLS_REAGENT_PREPARATION.value)
        frame.setStyleSheet("QFrame#labtoolsLocalReagentPanel { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        self._labtools_local_reagent_layout = layout
        self._populate_labtools_local_reagent_panel(model)
        return frame

    def _populate_labtools_local_reagent_panel(
        self,
        model: labtools_runtime.LabToolsLocalDataReadModel,
        result: labtools_runtime.LabToolsLocalWriteResult | None = None,
    ) -> None:
        layout = self._labtools_local_reagent_layout
        self._clear_layout(layout)
        header = QLabel("本地试剂库（试点入口）")
        header.setStyleSheet("font-weight: 700;")
        layout.addWidget(header)
        status = QLabel(f"本地试剂库：{_user_facing_labtools_status(model.status.status)} · {_user_facing_reagent_note(model.status.reason)}")
        status.setObjectName("labtoolsLocalReagentStatus")
        status.setProperty("status", model.status.status)
        status.setWordWrap(True)
        layout.addWidget(status)
        if not model.reagents:
            layout.addWidget(
                make_empty_state(
                    "暂无本地试剂",
                    "连接 BioMedPilot 项目后可读取本地试剂库；当前不在主流程中管理库存。",
                    empty_state_key="empty_project",
                    semantic_key=PageKey.LABTOOLS_REAGENT_PREPARATION.value,
                )
            )
            if model.status.status == "missing_project_context":
                layout.addStretch(1)
                return
        for reagent in model.reagents:
            row = QPushButton(
                f"{reagent.name}\n{reagent.category or 'uncategorized'} · {reagent.concentration or 'no concentration'} · {reagent.storage_location or 'no location'}"
            )
            row.setObjectName("labtoolsLocalReagentRow")
            row.setProperty("reagentId", reagent.reagent_id)
            row.setProperty("reagentName", reagent.name)
            row.setProperty("version", reagent.version)
            row.setProperty("status", reagent.status)
            row.clicked.connect(lambda _checked=False, item=reagent: self._select_labtools_local_reagent(item))
            layout.addWidget(row)
        form_header = QLabel("本地试剂管理（开发者诊断 / 试点）")
        form_header.setStyleSheet("font-weight: 700;")
        layout.addWidget(form_header)
        self._labtools_local_reagent_inputs = {}
        for label_text, field_id in (
            ("名称", "name"),
            ("分类", "category"),
            ("浓度", "concentration"),
            ("存放位置", "storage_location"),
        ):
            layout.addLayout(self._labtools_local_reagent_input_row(label_text, field_id))
        actions = QHBoxLayout()
        create = make_button("新增本地试剂", role="secondary")
        create.setObjectName("labtoolsLocalReagentCreateButton")
        create.clicked.connect(self._create_labtools_local_reagent)
        update = make_button("编辑本地试剂", role="secondary")
        update.setObjectName("labtoolsLocalReagentUpdateButton")
        update.clicked.connect(self._update_labtools_local_reagent)
        archive = make_button("归档本地试剂", role="secondary")
        archive.setObjectName("labtoolsLocalReagentArchiveButton")
        archive.clicked.connect(self._archive_labtools_local_reagent)
        write_enabled = model.status.write_enabled or model.status.status in {"blocked", "missing_project_context"}
        for button in (create, update, archive):
            button.setEnabled(write_enabled)
            button.setProperty("disabledState", "" if write_enabled else "disabled_local_data_write")
            actions.addWidget(button)
        actions.addStretch(1)
        layout.addLayout(actions)
        self._labtools_local_reagent_create_button = create
        self._labtools_local_reagent_update_button = update
        self._labtools_local_reagent_archive_button = archive
        write_status = QLabel(_labtools_local_write_result_text(result) if result is not None else "本地保存入口为试点能力，不会同步到其他设备。")
        write_status.setObjectName("labtoolsLocalReagentWriteStatus")
        write_status.setProperty("status", result.status if result is not None else "idle")
        write_status.setWordWrap(True)
        layout.addWidget(write_status)
        self._labtools_local_reagent_write_status = write_status
        layout.addWidget(
            self._labtools_notice_card(
                "本阶段只引用本地试剂信息；不会扣减库存，也不会覆盖试剂模板。",
                object_name="labtoolsAdapterNotice",
                semantic_key=PageKey.LABTOOLS_REAGENT_PREPARATION.value,
            )
        )
        layout.addStretch(1)

    def _labtools_local_reagent_input_row(self, label: str, field_id: str) -> QHBoxLayout:
        row = QHBoxLayout()
        title = QLabel(label)
        title.setObjectName("labtoolsLocalReagentInputLabel")
        title.setProperty("fieldId", field_id)
        field = QLineEdit()
        field.setObjectName("labtoolsLocalReagentInput")
        field.setProperty("fieldId", field_id)
        self._labtools_local_reagent_inputs[field_id] = field
        row.addWidget(title)
        row.addWidget(field, 1)
        return row

    def _labtools_reagent_run_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("labtoolsReagentRunPanel")
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("pageKey", "reagent_preparation")
        frame.setProperty("semanticKey", PageKey.LABTOOLS_REAGENT_PREPARATION.value)
        frame.setStyleSheet(
            f"QFrame#labtoolsReagentRunPanel {{ border: 1px solid {REAGENT_PREP_TOKENS['border']}; "
            f"border-radius: 12px; background: {REAGENT_PREP_TOKENS['surface']}; }}"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(7)
        header_row = QHBoxLayout()
        header = QLabel("本次配制")
        header.setStyleSheet(f"color: {REAGENT_PREP_TOKENS['text']}; font-size: 15px; font-weight: 850;")
        header_row.addWidget(header)
        header_row.addStretch(1)
        header_row.addWidget(make_status_chip("后端可用 / 需复核", status_key="testing"))
        layout.addLayout(header_row)
        selected = QLabel("Selected template · PBS 1x 示例模板")
        selected.setStyleSheet(f"color: {REAGENT_PREP_TOKENS['muted']}; font-size: 12px;")
        layout.addWidget(selected)
        self._labtools_reagent_run_inputs: dict[str, QLineEdit] = {}
        self._labtools_reagent_target_unit = QComboBox()
        self._labtools_reagent_target_unit.setObjectName("labtoolsReagentTargetVolumeUnit")
        self._labtools_reagent_target_unit.addItems(["mL", "µL", "L"])
        layout.addLayout(self._labtools_reagent_input_row("目标体积 Target volume", "target_volume", "500", unit_widget=self._labtools_reagent_target_unit))
        layout.addLayout(self._labtools_reagent_input_row("操作人 Operator", "operator_name", "Researcher"))
        layout.addLayout(self._labtools_reagent_input_row("pH 实测值 pH measured", "measured_ph", "7.4"))
        layout.addLayout(self._labtools_reagent_input_row("批次备注 / pH 调整后", "adjustment_note", "按 SOP 微调并人工记录"))
        calculate = make_button("更新配制结果", role="primary")
        calculate.setObjectName("labtoolsReagentCalculateButton")
        calculate.clicked.connect(self._run_labtools_reagent_preparation)
        layout.addWidget(calculate)
        self._labtools_reagent_result_primary = QLabel("请选择模板并计算。")
        self._labtools_reagent_result_primary.setObjectName("labtoolsReagentResultPrimary")
        self._labtools_reagent_result_primary.setWordWrap(True)
        self._labtools_reagent_result_primary.setStyleSheet(
            f"background: {REAGENT_PREP_TOKENS['green_soft']}; border: 1px solid #BBF7D0; border-radius: 12px; "
            f"color: {REAGENT_PREP_TOKENS['green']}; font-size: 14px; font-weight: 800; padding: 12px;"
        )
        layout.addWidget(self._labtools_reagent_result_primary)
        result_header = QLabel("组分预览")
        result_header.setStyleSheet(f"color: {REAGENT_PREP_TOKENS['text']}; font-size: 13px; font-weight: 800;")
        layout.addWidget(result_header)
        self._labtools_reagent_result_rows = QVBoxLayout()
        self._labtools_reagent_result_rows.setSpacing(6)
        self._labtools_reagent_result_rows.setContentsMargins(8, 8, 8, 8)
        result_rows_frame = QFrame()
        result_rows_frame.setObjectName("labtoolsReagentResultTable")
        result_rows_frame.setMinimumHeight(148)
        result_rows_frame.setStyleSheet(
            f"QFrame#labtoolsReagentResultTable {{ border: 1px solid {REAGENT_PREP_TOKENS['border']}; "
            f"border-radius: 12px; background: {REAGENT_PREP_TOKENS['surface_subtle']}; }}"
        )
        result_rows_frame.setLayout(self._labtools_reagent_result_rows)
        layout.addWidget(result_rows_frame)
        self._labtools_reagent_result_text = QPlainTextEdit()
        self._labtools_reagent_result_text.setObjectName("labtoolsReagentResultText")
        self._labtools_reagent_result_text.setReadOnly(True)
        self._labtools_reagent_result_text.setMinimumHeight(80)
        self._labtools_reagent_result_text.setVisible(False)
        layout.addWidget(self._labtools_reagent_result_text)
        self._labtools_reagent_issue_rows = QLabel(labtools_runtime.REVIEW_NOTICE)
        self._labtools_reagent_issue_rows.setObjectName("labtoolsReagentIssueRows")
        self._labtools_reagent_issue_rows.setWordWrap(True)
        self._labtools_reagent_issue_rows.setStyleSheet(
            f"background: {REAGENT_PREP_TOKENS['amber_soft']}; border: 1px solid #FDE68A; border-radius: 10px; "
            f"color: {REAGENT_PREP_TOKENS['amber']}; padding: 10px; font-size: 11px;"
        )
        layout.addWidget(self._labtools_reagent_issue_rows)
        self._labtools_local_reagent_reference = QLabel("未引用本地试剂。")
        self._labtools_local_reagent_reference.setObjectName("labtoolsLocalReagentReference")
        self._labtools_local_reagent_reference.setWordWrap(True)
        self._labtools_local_reagent_reference.setStyleSheet(f"color: {REAGENT_PREP_TOKENS['muted']}; font-size: 11px;")
        layout.addWidget(self._labtools_local_reagent_reference)
        layout.addStretch(1)
        return frame

    def _labtools_reagent_action_bar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("labtoolsReagentActionBar")
        frame.setProperty("pageKey", "reagent_preparation")
        frame.setProperty("semanticKey", PageKey.LABTOOLS_REAGENT_PREPARATION.value)
        frame.setStyleSheet(
            f"QFrame#labtoolsReagentActionBar {{ border: 1px solid {REAGENT_PREP_TOKENS['border']}; "
            f"border-radius: 12px; background: {REAGENT_PREP_TOKENS['surface']}; }}"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)
        title = QLabel("配制操作")
        title.setStyleSheet(f"color: {REAGENT_PREP_TOKENS['text']}; font-size: 13px; font-weight: 850;")
        layout.addWidget(title)
        layout.addStretch(1)
        actions = QHBoxLayout()
        actions.setSpacing(8)
        copy = make_button("复制配制摘要", role="primary_action")
        copy.setObjectName("labtoolsReagentCopySummaryButton")
        copy.clicked.connect(self._copy_labtools_reagent_summary)
        save = make_button("保存配制记录", role="disabled_action")
        save.setObjectName("labtoolsReagentSaveRecordButton")
        save.clicked.connect(self._save_labtools_reagent_record)
        export = make_button("导出记录", role="disabled_action")
        export.setObjectName("labtoolsReagentExportButton")
        export.setEnabled(False)
        export.setProperty("disabledState", "future")
        export_md = make_button("MD", role="secondary")
        export_md.setObjectName("labtoolsReagentExportMarkdownButton")
        export_md.setProperty("exportRequiresFilePicker", True)
        export_md.setProperty("exportFormat", "markdown")
        export_md.clicked.connect(self._export_labtools_reagent_markdown)
        export_csv = make_button("CSV", role="secondary")
        export_csv.setObjectName("labtoolsReagentExportCsvButton")
        export_csv.setProperty("exportRequiresFilePicker", True)
        export_csv.setProperty("exportFormat", "csv")
        export_csv.clicked.connect(self._export_labtools_reagent_csv)
        actions.addWidget(copy)
        actions.addWidget(save)
        actions.addWidget(export_md)
        actions.addWidget(export_csv)
        actions.addWidget(export)
        actions.addStretch(1)
        layout.addLayout(actions)
        self._labtools_reagent_save_record_button = save
        self._labtools_reagent_copy_text = ""
        self._labtools_reagent_last_result = None
        self._set_storage_gated_button_state(save, bool(self._labtools_project_root), "disabled_missing_storage_adapter")
        return frame

    def _labtools_reagent_detail_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("labtoolsReagentDetailPanel")
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("pageKey", "reagent_preparation")
        frame.setProperty("semanticKey", PageKey.LABTOOLS_REAGENT_PREPARATION.value)
        frame.setStyleSheet(
            f"QFrame#labtoolsReagentDetailPanel {{ border: 1px solid {REAGENT_PREP_TOKENS['border']}; "
            f"border-radius: 12px; background: {REAGENT_PREP_TOKENS['surface']}; }}"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 13, 14, 13)
        layout.setSpacing(8)
        header = QLabel("模板编辑：PBS 1x")
        header.setStyleSheet(f"color: {REAGENT_PREP_TOKENS['text']}; font-size: 14px; font-weight: 850;")
        layout.addWidget(header)
        dirty = make_status_chip("已修改未保存 / 需存储适配", status_key="planned")
        dirty.setObjectName("labtoolsReagentDirtyState")
        layout.addWidget(dirty)
        detail_body = QFrame()
        detail_body.setObjectName("labtoolsReagentDetailBody")
        detail_body.setStyleSheet("QFrame#labtoolsReagentDetailBody { border: 0; background: transparent; }")
        detail_body_layout = QVBoxLayout(detail_body)
        detail_body_layout.setContentsMargins(0, 0, 0, 0)
        detail_body_layout.setSpacing(5)
        self._labtools_reagent_detail_rows_layout = detail_body_layout
        layout.addWidget(detail_body)
        save = make_button("保存模板", role="disabled_action")
        save.setObjectName("labtoolsReagentSaveTemplateButton")
        save.clicked.connect(self._save_labtools_reagent_template)
        self._set_storage_gated_button_state(save, bool(self._labtools_project_root), "disabled_missing_storage_adapter")
        self._labtools_reagent_save_template_button = save
        layout.addWidget(save)
        layout.addStretch(1)
        return frame

    def _labtools_reagent_history_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("labtoolsReagentHistoryPanel")
        frame.setProperty("pageKey", "reagent_preparation")
        frame.setProperty("semanticKey", PageKey.LABTOOLS_REAGENT_PREPARATION.value)
        frame.setStyleSheet(
            f"QFrame#labtoolsReagentHistoryPanel {{ border: 1px solid {REAGENT_PREP_TOKENS['border']}; "
            f"border-radius: 12px; background: {REAGENT_PREP_TOKENS['surface']}; }}"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        header = QLabel("配制记录预览 / History Preview")
        header.setStyleSheet("font-weight: 700;")
        layout.addWidget(header)
        self._labtools_reagent_history_status = QLabel("未连接项目存储上下文。")
        self._labtools_reagent_history_status.setObjectName("labtoolsReagentHistoryStatus")
        self._labtools_reagent_history_status.setWordWrap(True)
        layout.addWidget(self._labtools_reagent_history_status)
        self._labtools_reagent_history_list = QListWidget()
        self._labtools_reagent_history_list.setObjectName("labtoolsReagentHistoryList")
        self._labtools_reagent_history_list.currentItemChanged.connect(self._select_labtools_reagent_history_item)
        layout.addWidget(self._labtools_reagent_history_list)
        self._labtools_reagent_history_detail = QPlainTextEdit()
        self._labtools_reagent_history_detail.setObjectName("labtoolsReagentHistoryDetail")
        self._labtools_reagent_history_detail.setReadOnly(True)
        self._labtools_reagent_history_detail.setMinimumHeight(90)
        layout.addWidget(self._labtools_reagent_history_detail)
        return frame

    def _labtools_reagent_input_row(self, label: str, field_id: str, default_value: str, *, unit_widget: QComboBox | None = None) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        title = QLabel(label)
        title.setObjectName("labtoolsReagentInputLabel")
        title.setProperty("fieldId", field_id)
        title.setMinimumWidth(140)
        title.setStyleSheet(f"color: {REAGENT_PREP_TOKENS['text']}; font-size: 12px; font-weight: 650;")
        row.addWidget(title)
        field = QLineEdit(default_value)
        field.setObjectName("labtoolsReagentInput")
        field.setProperty("fieldId", field_id)
        field.setMinimumHeight(34)
        field.setStyleSheet(
            f"background: {REAGENT_PREP_TOKENS['surface_subtle']}; border: 1px solid {REAGENT_PREP_TOKENS['border']}; "
            f"border-radius: 8px; padding: 6px 10px; color: {REAGENT_PREP_TOKENS['text']};"
        )
        self._labtools_reagent_run_inputs[field_id] = field
        row.addWidget(field, 1)
        if unit_widget is not None:
            unit_widget.setProperty("fieldId", field_id)
            unit_widget.setMinimumHeight(34)
            unit_widget.setStyleSheet(
                f"background: {REAGENT_PREP_TOKENS['surface']}; border: 1px solid {REAGENT_PREP_TOKENS['border']}; "
                f"border-radius: 8px; padding: 4px 8px; color: {REAGENT_PREP_TOKENS['text']};"
            )
            row.addWidget(unit_widget)
        return row

    def _select_labtools_reagent_template(self, template_id: str) -> None:
        self._labtools_reagent_selected_template_id = template_id
        detail = labtools_runtime.get_reagent_template_detail(template_id, self._labtools_project_root)
        self._render_labtools_reagent_template_detail(detail)

    def _select_labtools_local_reagent(self, reagent: labtools_runtime.LabToolsLocalReagentSummary) -> None:
        self._labtools_selected_local_reagent_id = reagent.reagent_id
        self._labtools_selected_local_reagent_version = reagent.version
        if hasattr(self, "_labtools_local_reagent_inputs"):
            self._labtools_local_reagent_inputs["name"].setText(reagent.name)
            self._labtools_local_reagent_inputs["category"].setText(reagent.category)
            self._labtools_local_reagent_inputs["concentration"].setText(reagent.concentration)
            self._labtools_local_reagent_inputs["storage_location"].setText(reagent.storage_location)
        if hasattr(self, "_labtools_local_reagent_reference"):
            self._labtools_local_reagent_reference.setText(
                f"已引用本地试剂：{reagent.name} · {reagent.concentration or 'no concentration'} · {reagent.storage_location or 'no location'}"
            )
            self._labtools_local_reagent_reference.setProperty("reagentId", reagent.reagent_id)

    def _local_reagent_payload_from_inputs(self) -> dict[str, object]:
        return {field_id: widget.text().strip() for field_id, widget in self._labtools_local_reagent_inputs.items()}

    def _create_labtools_local_reagent(self) -> None:
        result = labtools_runtime.create_local_reagent(self._labtools_project_root, self._local_reagent_payload_from_inputs())
        self._refresh_labtools_local_reagent_after_write(result)

    def _update_labtools_local_reagent(self) -> None:
        reagent_id = getattr(self, "_labtools_selected_local_reagent_id", "")
        expected_version = int(getattr(self, "_labtools_selected_local_reagent_version", 0) or 0)
        if not reagent_id or expected_version < 1:
            result = labtools_runtime.LabToolsLocalWriteResult(
                success=False,
                status="blocked_no_selection",
                message="请先选择一个本地试剂。",
                blocker="no_reagent_selected",
            )
        else:
            result = labtools_runtime.update_local_reagent(
                self._labtools_project_root,
                reagent_id,
                self._local_reagent_payload_from_inputs(),
                expected_version=expected_version,
            )
        self._refresh_labtools_local_reagent_after_write(result)

    def _archive_labtools_local_reagent(self) -> None:
        reagent_id = getattr(self, "_labtools_selected_local_reagent_id", "")
        expected_version = int(getattr(self, "_labtools_selected_local_reagent_version", 0) or 0)
        if not reagent_id or expected_version < 1:
            result = labtools_runtime.LabToolsLocalWriteResult(
                success=False,
                status="blocked_no_selection",
                message="请先选择一个本地试剂。",
                blocker="no_reagent_selected",
            )
        else:
            result = labtools_runtime.archive_local_reagent(self._labtools_project_root, reagent_id, expected_version=expected_version)
        self._refresh_labtools_local_reagent_after_write(result)

    def _refresh_labtools_local_reagent_after_write(self, result: labtools_runtime.LabToolsLocalWriteResult) -> None:
        self._labtools_local_data_read_model = labtools_runtime.get_labtools_local_data_read_model(self._labtools_project_root)
        if result.success:
            self._labtools_selected_local_reagent_id = result.entity_id
            self._labtools_selected_local_reagent_version = result.new_version or 0
        self._populate_labtools_local_reagent_panel(self._labtools_local_data_read_model, result)

    def _select_labtools_local_sample(self, sample: labtools_runtime.LabToolsLocalSampleSummary) -> None:
        self._labtools_selected_local_sample_id = sample.sample_id
        self._labtools_selected_local_sample_version = sample.version
        if hasattr(self, "_labtools_local_sample_inputs"):
            self._labtools_local_sample_inputs["sample_name"].setText(sample.sample_name)
            self._labtools_local_sample_inputs["sample_type"].setText(sample.sample_type)
            self._labtools_local_sample_inputs["concentration"].setText(sample.concentration)
            self._labtools_local_sample_inputs["concentration_unit"].setText(sample.concentration_unit)
            self._labtools_local_sample_inputs["volume"].setText(sample.volume)
            self._labtools_local_sample_inputs["volume_unit"].setText(sample.volume_unit)
            self._labtools_local_sample_inputs["storage_location"].setText(sample.storage_location)

    def _local_sample_payload_from_inputs(self) -> dict[str, object]:
        return {field_id: widget.text().strip() for field_id, widget in self._labtools_local_sample_inputs.items()}

    def _create_labtools_local_sample(self) -> None:
        result = labtools_runtime.create_local_sample(self._labtools_project_root, self._local_sample_payload_from_inputs())
        self._refresh_labtools_local_sample_after_write(result)

    def _update_labtools_local_sample(self) -> None:
        sample_id = getattr(self, "_labtools_selected_local_sample_id", "")
        expected_version = int(getattr(self, "_labtools_selected_local_sample_version", 0) or 0)
        if not sample_id or expected_version < 1:
            result = labtools_runtime.LabToolsLocalWriteResult(
                success=False,
                status="blocked_no_selection",
                message="请先选择一个本地样本。",
                blocker="no_sample_selected",
            )
        else:
            result = labtools_runtime.update_local_sample(
                self._labtools_project_root,
                sample_id,
                self._local_sample_payload_from_inputs(),
                expected_version=expected_version,
            )
        self._refresh_labtools_local_sample_after_write(result)

    def _archive_labtools_local_sample(self) -> None:
        sample_id = getattr(self, "_labtools_selected_local_sample_id", "")
        expected_version = int(getattr(self, "_labtools_selected_local_sample_version", 0) or 0)
        if not sample_id or expected_version < 1:
            result = labtools_runtime.LabToolsLocalWriteResult(
                success=False,
                status="blocked_no_selection",
                message="请先选择一个本地样本。",
                blocker="no_sample_selected",
            )
        else:
            result = labtools_runtime.archive_local_sample(self._labtools_project_root, sample_id, expected_version=expected_version)
        self._refresh_labtools_local_sample_after_write(result)

    def _refresh_labtools_local_sample_after_write(self, result: labtools_runtime.LabToolsLocalWriteResult) -> None:
        self._labtools_local_data_read_model = labtools_runtime.get_labtools_local_data_read_model(self._labtools_project_root)
        if result.success:
            self._labtools_selected_local_sample_id = result.entity_id
            self._labtools_selected_local_sample_version = result.new_version or 0
        self._populate_labtools_local_wb_sample_panel(self._labtools_local_data_read_model, result)
        self._run_labtools_wb_loading()

    def _select_labtools_bca_sample(self, sample: labtools_runtime.LabToolsLocalSampleSummary) -> None:
        self._labtools_bca_selected_sample_id = sample.sample_id
        if hasattr(self, "_labtools_bca_proposal_status"):
            self._labtools_bca_proposal_status.setText(
                f"已选择：{sample.sample_name} · current {sample.concentration or 'no concentration'} {sample.concentration_unit or ''}".strip()
            )
            self._labtools_bca_proposal_status.setProperty("sampleId", sample.sample_id)

    def _create_labtools_bca_sample_proposal(self) -> None:
        sample_id = getattr(self, "_labtools_bca_selected_sample_id", "")
        proposal = labtools_runtime.create_sample_concentration_update_proposal(
            self._labtools_project_root,
            sample_id,
            self._labtools_bca_proposal_inputs["concentration"].text().strip(),
            self._labtools_bca_proposal_inputs["concentration_unit"].text().strip(),
        )
        self._labtools_bca_pending_proposal = proposal if proposal.can_apply else None
        self._labtools_bca_proposal_status.setText(proposal.message)
        self._labtools_bca_proposal_status.setProperty("status", proposal.status)
        self._labtools_bca_proposal_status.setProperty("sampleId", proposal.sample_id)
        self._labtools_bca_confirm_proposal_button.setEnabled(proposal.can_apply)
        self._labtools_bca_confirm_proposal_button.setProperty("disabledState", "" if proposal.can_apply else "proposal_required")

    def _confirm_labtools_bca_sample_proposal(self) -> None:
        proposal = getattr(self, "_labtools_bca_pending_proposal", None)
        if proposal is None:
            result = labtools_runtime.LabToolsLocalWriteResult(
                success=False,
                status="blocked_no_proposal",
                message="请先生成 sample concentration update proposal。",
                blocker="no_proposal",
            )
        else:
            result = labtools_runtime.confirm_sample_concentration_update(self._labtools_project_root, proposal)
        self._labtools_bca_proposal_status.setText(_labtools_local_write_result_text(result))
        self._labtools_bca_proposal_status.setProperty("status", result.status)
        if result.success:
            self._labtools_bca_confirm_proposal_button.setEnabled(False)
            self._labtools_bca_confirm_proposal_button.setProperty("disabledState", "proposal_required")
            self._labtools_bca_pending_proposal = None
            self._labtools_local_data_read_model = labtools_runtime.get_labtools_local_data_read_model(self._labtools_project_root)

    def _render_labtools_reagent_template_detail(self, detail: labtools_runtime.ReagentTemplateDetail) -> None:
        layout = self._labtools_reagent_detail_rows_layout
        self._clear_layout(layout)
        rows = [
            f"模板名称：{detail.summary.name}",
            f"分类：{detail.summary.category}",
            f"默认体积：{detail.summary.default_volume}",
            f"pH 目标：{detail.ph_target or '未设置'}",
            f"备注：{_user_facing_reagent_note(detail.notes)}",
        ]
        for text in rows:
            label = QLabel(text)
            label.setObjectName("labtoolsReagentDetailRow")
            label.setWordWrap(False)
            label.setMinimumHeight(23)
            label.setToolTip(text)
            label.setStyleSheet(
                f"background: {REAGENT_PREP_TOKENS['surface_subtle']}; border: 1px solid {REAGENT_PREP_TOKENS['border']}; "
                f"border-radius: 8px; color: {REAGENT_PREP_TOKENS['text']}; font-size: 11px;"
            )
            layout.addWidget(label)
        component_header = QLabel(f"组分设置（共 {len(detail.components)} 项）")
        component_header.setObjectName("labtoolsReagentComponentHeader")
        component_header.setStyleSheet(f"color: {REAGENT_PREP_TOKENS['text']}; font-size: 13px; font-weight: 850;")
        layout.addWidget(component_header)
        for component in detail.components:
            label = QLabel(f"{component.name} · {component.stage} · {component.amount} · {component.notes or component.warning or '需人工复核'}")
            label.setObjectName("labtoolsReagentComponentRow")
            label.setWordWrap(False)
            label.setMinimumHeight(24)
            label.setToolTip(label.text())
            label.setStyleSheet(
                f"background: {REAGENT_PREP_TOKENS['surface']}; border: 1px solid {REAGENT_PREP_TOKENS['divider']}; "
                f"border-radius: 8px; color: {REAGENT_PREP_TOKENS['muted']}; font-size: 11px;"
            )
            layout.addWidget(label)
        validation_header = QLabel("验证与提示")
        validation_header.setStyleSheet(f"color: {REAGENT_PREP_TOKENS['text']}; font-size: 13px; font-weight: 850;")
        layout.addWidget(validation_header)
        for row in detail.validation_rows:
            label = QLabel(_user_facing_reagent_note(row))
            label.setObjectName("labtoolsReagentValidationRow")
            label.setWordWrap(False)
            label.setMinimumHeight(25)
            label.setToolTip(label.text())
            label.setStyleSheet(
                f"background: {REAGENT_PREP_TOKENS['blue_soft']}; border: 1px solid #DBEAFE; "
                f"border-radius: 8px; color: {REAGENT_PREP_TOKENS['blue']}; font-size: 11px;"
            )
            layout.addWidget(label)
        layout.addStretch(1)

    def _run_labtools_reagent_preparation(self) -> None:
        result = labtools_runtime.calculate_reagent_preparation(
            template_id=self._labtools_reagent_selected_template_id,
            target_volume=self._labtools_reagent_run_inputs["target_volume"].text().strip(),
            target_volume_unit=self._labtools_reagent_target_unit.currentText(),
            operator_name=self._labtools_reagent_run_inputs["operator_name"].text().strip(),
            measured_ph=self._labtools_reagent_run_inputs["measured_ph"].text().strip(),
            adjustment_note=self._labtools_reagent_run_inputs["adjustment_note"].text().strip(),
        )
        self._render_labtools_reagent_preparation_result(result)

    def _render_labtools_reagent_preparation_result(self, result: labtools_runtime.ReagentPreparationUiResult) -> None:
        self._labtools_reagent_last_result = result
        self._labtools_reagent_result_primary.setText(result.primary_result)
        self._labtools_reagent_result_text.setPlainText(result.detail_text)
        self._clear_layout(self._labtools_reagent_result_rows)
        for component in result.component_rows:
            row = QLabel(f"☐ {component.name}  |  {component.stage}  |  {component.amount}  |  {component.notes or component.warning or '需用户复核'}")
            row.setObjectName("labtoolsReagentResultRow")
            row.setWordWrap(False)
            row.setMinimumHeight(23)
            row.setToolTip(row.text())
            row.setStyleSheet(
                f"background: {REAGENT_PREP_TOKENS['surface']}; border: 1px solid {REAGENT_PREP_TOKENS['divider']}; "
                f"border-radius: 8px; color: {REAGENT_PREP_TOKENS['text']}; font-size: 11px;"
            )
            self._labtools_reagent_result_rows.addWidget(row)
        if not result.component_rows:
            row = QLabel("未生成组分预览。")
            row.setObjectName("labtoolsReagentResultRow")
            row.setStyleSheet(f"color: {REAGENT_PREP_TOKENS['muted']}; font-size: 12px;")
            self._labtools_reagent_result_rows.addWidget(row)
        issues = list(result.errors) + list(result.warnings)
        self._labtools_reagent_issue_rows.setText("\n".join(f"- {_user_facing_reagent_note(issue)}" for issue in issues))
        self._labtools_reagent_issue_rows.setProperty("hasError", bool(result.errors))
        self._labtools_reagent_copy_text = result.copy_text if result.valid else ""
        if self._labtools_project_root:
            self._labtools_reagent_issue_rows.setText(
                f"{self._labtools_reagent_issue_rows.text()}\n- 保存路径由 BioMedPilot 存储适配器提供。"
            )

    def _copy_labtools_reagent_summary(self) -> None:
        from PySide6.QtWidgets import QApplication

        if self._labtools_reagent_copy_text:
            QApplication.clipboard().setText(self._labtools_reagent_copy_text)

    def _save_labtools_reagent_template(self) -> None:
        result = labtools_runtime.save_reagent_template_to_project(self._labtools_project_root, self._labtools_reagent_selected_template_id or "demo_pbs_1x")
        self._report_labtools_storage_result(result, self._labtools_reagent_issue_rows)
        if result.ok:
            templates = labtools_runtime.list_reagent_templates(self._labtools_project_root)
            self._labtools_reagent_templates = {template.template_id: template for template in templates}
            self._refresh_labtools_reagent_history()

    def _save_labtools_reagent_record(self) -> None:
        result_data = getattr(self, "_labtools_reagent_last_result", None)
        if result_data is None:
            return
        result = labtools_runtime.create_local_record_summary(
            self._labtools_project_root,
            {
                "record_type": "reagent_preparation",
                "title": f"Reagent preparation: {result_data.primary_result}",
                "summary": result_data.primary_result,
                "linked_reagents": [getattr(self, "_labtools_selected_local_reagent_id", "")],
                "artifact_refs": [f"template:{self._labtools_reagent_selected_template_id or 'demo_pbs_1x'}", "ui:reagent_preparation:local-summary-only"],
                "status": "draft",
            },
        )
        self._report_labtools_local_write_result(result, self._labtools_reagent_issue_rows)
        self._labtools_local_data_read_model = labtools_runtime.get_labtools_local_data_read_model(self._labtools_project_root)
        self._refresh_labtools_reagent_history()

    def _export_labtools_reagent_markdown(self) -> None:
        result_data = getattr(self, "_labtools_reagent_last_result", None)
        if result_data is None:
            return
        path = self._choose_labtools_export_path("导出试剂配制 Markdown", ".md", "reagent_preparation.md", "Markdown (*.md)")
        if path is None:
            self._report_labtools_export_cancelled(self._labtools_reagent_issue_rows)
            return
        result = labtools_runtime.export_reagent_preparation_markdown(path, result_data)
        self._report_labtools_storage_result(result, self._labtools_reagent_issue_rows)

    def _export_labtools_reagent_csv(self) -> None:
        result_data = getattr(self, "_labtools_reagent_last_result", None)
        if result_data is None:
            return
        path = self._choose_labtools_export_path("导出试剂配制 CSV", ".csv", "reagent_preparation.csv", "CSV (*.csv)")
        if path is None:
            self._report_labtools_export_cancelled(self._labtools_reagent_issue_rows)
            return
        result = labtools_runtime.export_reagent_preparation_csv(path, result_data)
        self._report_labtools_storage_result(result, self._labtools_reagent_issue_rows)

    def _refresh_labtools_reagent_history(self) -> None:
        if not hasattr(self, "_labtools_reagent_history_list"):
            return
        self._labtools_reagent_history_list.clear()
        records = labtools_runtime.list_local_record_summaries(self._labtools_project_root, record_type="reagent_preparation")
        if not records:
            self._labtools_reagent_history_status.setText("暂无本地配制记录摘要；保存入口仍需存储适配。")
            self._labtools_reagent_history_detail.setPlainText("")
            return
        self._labtools_reagent_history_status.setText("本地实验记录摘要；不是正式报告。")
        for record in records:
            item = QListWidgetItem(f"{record.created_at} | {record.title}")
            item.setData(Qt.UserRole, record)
            self._labtools_reagent_history_list.addItem(item)
        self._labtools_reagent_history_list.setCurrentRow(self._labtools_reagent_history_list.count() - 1)

    def _select_labtools_reagent_history_item(self, current, _previous) -> None:
        if current is None:
            self._labtools_reagent_history_detail.setPlainText("")
            return
        record = current.data(Qt.UserRole)
        if record is None:
            self._labtools_reagent_history_detail.setPlainText("")
            return
        self._labtools_reagent_history_detail.setPlainText(
            f"record_id: {record.record_id}\nstatus: {record.status}\nversion: {record.version}\n"
            f"linked_reagents: {', '.join(record.linked_reagents) or 'none'}\nsummary: {record.summary}\n\n本地实验记录摘要，不是正式报告。"
        )

    def _show_labtools_wb_loading_page(self) -> None:
        semantic_key = PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value
        content = QWidget()
        content.setObjectName("labtoolsShellContent")
        content.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        content.setProperty("pageKey", "wb_loading")
        content.setProperty("semanticKey", semantic_key)
        content.setProperty("uiPrimitive", "protein_wb_calculation_page")
        content.setProperty("layoutPolishNoOverlap", True)
        content.setStyleSheet(f"QWidget#labtoolsShellContent {{ background: {PROTEIN_WB_TOKENS['background']}; }}")
        root = QVBoxLayout(content)
        root.setContentsMargins(20, 10, 20, 0)
        root.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(12)
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_row = QHBoxLayout()
        title_row.setSpacing(7)
        title = QLabel("蛋白实验")
        title.setObjectName("labtoolsShellTitle")
        title.setStyleSheet(f"color: {PROTEIN_WB_TOKENS['text']}; font-size: 20px; font-weight: 850;")
        slash = QLabel("/")
        slash.setStyleSheet(f"color: {PROTEIN_WB_TOKENS['faint']}; font-size: 17px;")
        english = QLabel("Protein Experiment")
        english.setStyleSheet(f"color: {PROTEIN_WB_TOKENS['muted']}; font-size: 15px; font-weight: 700;")
        info = QLabel("i")
        info.setAlignment(Qt.AlignCenter)
        info.setFixedSize(18, 18)
        info.setStyleSheet(
            f"border: 1px solid {PROTEIN_WB_TOKENS['border']}; border-radius: 9px; color: {PROTEIN_WB_TOKENS['muted']}; font-size: 11px;"
        )
        title_row.addWidget(title)
        title_row.addWidget(slash)
        title_row.addWidget(english)
        title_row.addWidget(info)
        title_row.addWidget(make_status_chip("本地测试版", status_key="developer_preview"))
        title_row.addStretch(1)
        title_col.addLayout(title_row)
        subtitle = QLabel("蛋白实验流程：以计算辅助为主，结果需用户复核后用于实验。")
        subtitle.setObjectName("labtoolsShellSubtitle")
        subtitle.setStyleSheet(f"color: {PROTEIN_WB_TOKENS['muted']}; font-size: 12px;")
        title_col.addWidget(subtitle)
        header.addLayout(title_col, 1)
        header.addWidget(make_status_chip("后端可用", status_key="testing"), 0, Qt.AlignTop)
        header.addWidget(make_status_chip("需文件适配", status_key="planned"), 0, Qt.AlignTop)
        header.addWidget(make_status_chip("需复核", status_key="testing"), 0, Qt.AlignTop)
        user = QLabel("R  Researcher")
        user.setObjectName("labtoolsWbUserBadge")
        user.setAlignment(Qt.AlignCenter)
        user.setStyleSheet(
            f"background: {PROTEIN_WB_TOKENS['surface']}; border: 1px solid {PROTEIN_WB_TOKENS['border']}; "
            f"border-radius: 8px; color: {PROTEIN_WB_TOKENS['text']}; padding: 7px 12px; font-size: 12px; font-weight: 650;"
        )
        header.addWidget(user, 0, Qt.AlignTop)
        back = make_button("使用指南", role="secondary")
        back.setObjectName("labtoolsBackButton")
        back.clicked.connect(self._show_labtools_experiment_modules_shell)
        back.setStyleSheet(
            f"background: {PROTEIN_WB_TOKENS['surface']}; border: 1px solid {PROTEIN_WB_TOKENS['border']}; "
            f"border-radius: 8px; color: {PROTEIN_WB_TOKENS['text']}; font-size: 12px; font-weight: 650; padding: 7px 12px;"
        )
        header.addWidget(back, 0, Qt.AlignTop)
        root.addLayout(header)
        root.addLayout(self._labtools_wb_substep_bar())
        self._labtools_local_data_read_model = labtools_runtime.get_labtools_local_data_read_model(self._labtools_project_root)
        self._labtools_selected_local_sample_id = ""
        self._labtools_selected_local_sample_version = 0

        left_column = QWidget()
        left_column.setObjectName("labtoolsWbLeftColumn")
        left_column.setProperty("uiPrimitive", "workbench_secondary_column")
        left_column.setProperty("layoutPolishNoOverlap", True)
        left_column.setMinimumWidth(256)
        left_column.setMaximumWidth(280)
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.addWidget(self._labtools_wb_config_panel())
        local_sample_panel = self._labtools_local_wb_sample_panel(self._labtools_local_data_read_model)
        local_sample_panel.setVisible(False)
        left_layout.addWidget(local_sample_panel)
        results_panel = self._labtools_wb_results_panel()
        results_panel.setMinimumWidth(390)
        lane_panel = self._labtools_wb_lane_panel()
        lane_panel.setMinimumWidth(320)
        root.addWidget(
            make_three_column_workbench(
                left_widget=left_column,
                middle_widget=results_panel,
                right_widget=lane_panel,
                object_name="labtoolsWbWorkbenchColumns",
                sizes=(256, 388, 340),
            )
        )

        boundary = self._labtools_notice_card(
            "边界：此页不提供 SDS-PAGE 配胶、图像分析、自动条带识别、抗体推荐或完整 WB 协议；泳道布局仅作为 layout helper，不代表真实凝胶图或伪凝胶条带。",
            object_name="labtoolsAdapterNotice",
            semantic_key=semantic_key,
        )
        boundary.setVisible(False)
        root.addWidget(boundary)
        root.addWidget(self._labtools_wb_action_bar())
        root.addWidget(
            self._labtools_notice_card(
                "保存路径由 BioMedPilot 存储适配器提供；桌面 UI 不应默认写入个人目录。所有计算结果需由实验人员复核后使用。",
                object_name="labtoolsWbBottomNotice",
                semantic_key=semantic_key,
            )
        )
        history_panel = self._labtools_wb_history_panel()
        history_panel.setVisible(False)
        root.addWidget(history_panel)
        root.addStretch(1)
        self._labtools_wb_last_result = None
        self._set_labtools_content(content)
        self._run_labtools_wb_loading()
        self._refresh_labtools_wb_history()

    def _labtools_wb_action_bar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("labtoolsWbActionBar")
        frame.setProperty("pageKey", "wb_loading")
        frame.setProperty("semanticKey", PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value)
        frame.setStyleSheet(
            f"QFrame#labtoolsWbActionBar {{ border: 1px solid {PROTEIN_WB_TOKENS['border']}; "
            f"border-radius: 12px; background: {PROTEIN_WB_TOKENS['surface']}; }}"
        )
        actions = QHBoxLayout(frame)
        actions.setContentsMargins(12, 10, 12, 10)
        actions.setSpacing(10)
        copy = make_button("复制上样表", role="primary")
        copy.setObjectName("labtoolsWbCopyTableButton")
        copy.clicked.connect(self._copy_labtools_wb_summary)
        save = make_button("保存 WB 记录", role="secondary")
        save.setObjectName("labtoolsWbSaveRecordButton")
        save.clicked.connect(self._save_labtools_wb_record)
        export_md = make_button("导出 CSV / Markdown", role="secondary")
        export_md.setObjectName("labtoolsWbExportMarkdownButton")
        export_md.setProperty("exportRequiresFilePicker", True)
        export_md.setProperty("exportFormat", "markdown")
        export_md.clicked.connect(self._export_labtools_wb_markdown)
        export_csv = make_button("CSV", role="secondary")
        export_csv.setObjectName("labtoolsWbExportCsvButton")
        export_csv.setProperty("exportRequiresFilePicker", True)
        export_csv.setProperty("exportFormat", "csv")
        export_csv.clicked.connect(self._export_labtools_wb_csv)
        export = make_button("导出结果摘要", role="secondary")
        export.setObjectName("labtoolsWbExportButton")
        export.setEnabled(False)
        export.setProperty("disabledState", "future")
        history = make_button("历史记录", role="secondary")
        history.setObjectName("labtoolsWbHistoryButton")
        history.clicked.connect(self._refresh_labtools_wb_history)
        self._set_storage_gated_button_state(save, bool(self._labtools_project_root), "disabled_missing_storage_adapter")
        self._set_storage_gated_button_state(history, bool(self._labtools_project_root), "disabled_missing_storage_adapter")
        actions.addWidget(copy)
        actions.addWidget(save)
        actions.addWidget(export_md)
        actions.addWidget(export_csv)
        actions.addWidget(export)
        actions.addWidget(history)
        actions.addStretch(1)
        self._labtools_wb_save_record_button = save
        self._labtools_wb_history_button = history
        return frame

    def _labtools_wb_substep_bar(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(4)
        steps = (
            ("1", "蛋白定量", "流程占位", "planned"),
            ("2", "WB 上样计算", "当前步骤", "testing"),
            ("3", "SDS-PAGE 配胶", "流程占位", "planned"),
            ("4", "泳道布局", "预览辅助", "testing"),
            ("5", "转膜", "流程占位", "planned"),
            ("6", "抗体孵育", "流程占位", "planned"),
            ("7", "曝光记录", "流程占位", "planned"),
            ("8", "结果辅助", "流程占位", "planned"),
            ("9", "导出记录", "流程占位", "planned"),
        )
        for number, title, state, status_key in steps:
            chip = QFrame()
            chip.setObjectName("labtoolsWbSubstep")
            chip.setProperty("stepNumber", number)
            chip.setProperty("statusKey", status_key)
            color = PROTEIN_WB_TOKENS["blue_soft"] if status_key == "testing" else PROTEIN_WB_TOKENS["surface"]
            border = "#BFDBFE" if status_key == "testing" else PROTEIN_WB_TOKENS["border"]
            chip.setStyleSheet(f"QFrame#labtoolsWbSubstep {{ border: 1px solid {border}; border-radius: 10px; background: {color}; }}")
            chip.setMinimumHeight(34)
            layout = QVBoxLayout(chip)
            layout.setContentsMargins(8, 5, 8, 5)
            layout.setSpacing(0)
            title_label = QLabel(f"{number}. {title}")
            title_label.setObjectName("labtoolsWbSubstepTitle")
            title_label.setProperty("stepNumber", number)
            title_label.setStyleSheet(
                f"color: {PROTEIN_WB_TOKENS['blue'] if status_key == 'testing' else PROTEIN_WB_TOKENS['muted']}; "
                f"font-size: 10px; font-weight: {'800' if status_key == 'testing' else '650'};"
            )
            state_label = QLabel(state)
            state_label.setObjectName("labtoolsWbSubstepState")
            state_label.setProperty("stepNumber", number)
            state_label.setStyleSheet(f"font-size: 9px; color: {PROTEIN_WB_TOKENS['faint']};")
            layout.addWidget(title_label)
            layout.addWidget(state_label)
            row.addWidget(chip)
        return row

    def _labtools_wb_config_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("labtoolsWbConfigPanel")
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("pageKey", "wb_loading")
        frame.setProperty("semanticKey", PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value)
        frame.setStyleSheet(
            f"QFrame#labtoolsWbConfigPanel {{ border: 1px solid {PROTEIN_WB_TOKENS['border']}; "
            f"border-radius: 12px; background: {PROTEIN_WB_TOKENS['surface']}; }}"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)
        header_row = QHBoxLayout()
        header = QLabel("WB 配置")
        header.setStyleSheet(f"color: {PROTEIN_WB_TOKENS['text']}; font-size: 14px; font-weight: 850;")
        edit = QLabel("编辑")
        edit.setStyleSheet(f"color: {PROTEIN_WB_TOKENS['blue']}; font-size: 12px; font-weight: 750;")
        header_row.addWidget(header)
        header_row.addStretch(1)
        header_row.addWidget(edit)
        layout.addLayout(header_row)
        self._labtools_wb_inputs: dict[str, QLineEdit] = {}
        layout.addLayout(self._labtools_wb_input_row("目标上样蛋白量（每孔）", "target_protein_ug", "20", "µg"))
        layout.addLayout(self._labtools_wb_input_row("Sample buffer 倍数", "loading_buffer_factor", "4", "x"))
        layout.addLayout(self._labtools_wb_input_row("最终上样体积", "final_volume_ul", "20", "µL"))
        layout.addLayout(self._labtools_wb_input_row("固定泳道数", "lane_count", "10", "lanes"))
        reducing = QLabel("还原剂：Yes（当前示例视为已包含于上样体系，不额外占体积）")
        reducing.setObjectName("labtoolsWbConfigRow")
        reducing.setWordWrap(True)
        reducing.setStyleSheet(
            f"background: {PROTEIN_WB_TOKENS['field_disabled']}; border: 1px solid {PROTEIN_WB_TOKENS['divider']}; "
            f"border-radius: 8px; color: {PROTEIN_WB_TOKENS['muted']}; padding: 8px; font-size: 11px;"
        )
        layout.addWidget(reducing)
        calculate = make_button("重新计算 WB 上样", role="primary")
        calculate.setObjectName("labtoolsWbCalculateButton")
        calculate.clicked.connect(self._run_labtools_wb_loading)
        calculate.setVisible(False)
        layout.addWidget(calculate)
        note = self._labtools_notice_card(
            "计算基于输入的蛋白浓度与目标上样量；结果需结合实际实验条件复核使用。",
            object_name="labtoolsWbConfigNotice",
            semantic_key=PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value,
        )
        layout.addWidget(note)
        layout.addStretch(1)
        return frame

    def _labtools_local_wb_sample_panel(self, model: labtools_runtime.LabToolsLocalDataReadModel) -> QFrame:
        frame = QFrame()
        frame.setObjectName("labtoolsLocalWbSamplePanel")
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("pageKey", "wb_loading")
        frame.setProperty("semanticKey", PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value)
        frame.setStyleSheet("QFrame#labtoolsLocalWbSamplePanel { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        self._labtools_local_wb_sample_layout = layout
        self._populate_labtools_local_wb_sample_panel(model)
        return frame

    def _populate_labtools_local_wb_sample_panel(
        self,
        model: labtools_runtime.LabToolsLocalDataReadModel,
        result: labtools_runtime.LabToolsLocalWriteResult | None = None,
    ) -> None:
        layout = self._labtools_local_wb_sample_layout
        self._clear_layout(layout)
        header = QLabel("本地 protein sample")
        header.setStyleSheet("font-weight: 700;")
        layout.addWidget(header)
        status = QLabel(f"local_data: {model.status.status}")
        status.setObjectName("labtoolsLocalWbSampleStatus")
        status.setProperty("status", model.status.status)
        status.setWordWrap(True)
        layout.addWidget(status)
        if not model.samples:
            layout.addWidget(
                make_empty_state(
                    "暂无本地 sample",
                    model.status.reason,
                    empty_state_key="empty_project",
                    semantic_key=PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value,
                )
            )
        for sample in model.samples:
            row = QPushButton(
                f"{sample.sample_name} | {sample.sample_type} | {sample.concentration} {sample.concentration_unit} | {sample.storage_location or 'no location'}"
            )
            row.setObjectName("labtoolsLocalWbSampleRow")
            row.setProperty("sampleId", sample.sample_id)
            row.setProperty("sampleType", sample.sample_type)
            row.setProperty("sampleName", sample.sample_name)
            row.setProperty("version", sample.version)
            row.setProperty("wbCompatible", sample.wb_compatible)
            row.clicked.connect(lambda _checked=False, item=sample: self._select_labtools_local_sample(item))
            layout.addWidget(row)
        form_header = QLabel("本地样本管理")
        form_header.setStyleSheet("font-weight: 700;")
        layout.addWidget(form_header)
        self._labtools_local_sample_inputs = {}
        for label_text, field_id, default_text in (
            ("样本名称", "sample_name", ""),
            ("样本类型", "sample_type", "protein_lysate"),
            ("浓度", "concentration", ""),
            ("浓度单位", "concentration_unit", "mg/mL"),
            ("体积", "volume", ""),
            ("体积单位", "volume_unit", "µL"),
            ("存放位置", "storage_location", ""),
        ):
            layout.addLayout(self._labtools_local_sample_input_row(label_text, field_id, default_text))
        actions = QHBoxLayout()
        create = make_button("新增本地样本", role="secondary")
        create.setObjectName("labtoolsLocalSampleCreateButton")
        create.clicked.connect(self._create_labtools_local_sample)
        update = make_button("编辑本地样本", role="secondary")
        update.setObjectName("labtoolsLocalSampleUpdateButton")
        update.clicked.connect(self._update_labtools_local_sample)
        archive = make_button("归档本地样本", role="secondary")
        archive.setObjectName("labtoolsLocalSampleArchiveButton")
        archive.clicked.connect(self._archive_labtools_local_sample)
        write_enabled = model.status.write_enabled or model.status.status in {"blocked", "missing_project_context"}
        for button in (create, update, archive):
            button.setEnabled(write_enabled)
            button.setProperty("disabledState", "" if write_enabled else "disabled_local_data_write")
            actions.addWidget(button)
        actions.addStretch(1)
        layout.addLayout(actions)
        self._labtools_local_sample_create_button = create
        self._labtools_local_sample_update_button = update
        self._labtools_local_sample_archive_button = archive
        write_status = QLabel(_labtools_local_write_result_text(result) if result is not None else "本地保存，不会同步到其他设备。")
        write_status.setObjectName("labtoolsLocalSampleWriteStatus")
        write_status.setProperty("status", result.status if result is not None else "idle")
        write_status.setWordWrap(True)
        layout.addWidget(write_status)
        self._labtools_local_sample_write_status = write_status
        layout.addWidget(
            self._labtools_notice_card(
                "WB 只读取 protein_lysate / WB-compatible sample 的浓度用于预览；不会扣减样本体积，也不会自动修改 sample status。",
                object_name="labtoolsAdapterNotice",
                semantic_key=PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value,
            )
        )
        layout.addStretch(1)

    def _labtools_local_sample_input_row(self, label: str, field_id: str, default_text: str = "") -> QHBoxLayout:
        row = QHBoxLayout()
        title = QLabel(label)
        title.setObjectName("labtoolsLocalSampleInputLabel")
        title.setProperty("fieldId", field_id)
        field = QLineEdit(default_text)
        field.setObjectName("labtoolsLocalSampleInput")
        field.setProperty("fieldId", field_id)
        self._labtools_local_sample_inputs[field_id] = field
        row.addWidget(title)
        row.addWidget(field, 1)
        return row

    def _labtools_bca_sample_proposal_panel(self, model: labtools_runtime.LabToolsLocalDataReadModel) -> QFrame:
        frame = QFrame()
        frame.setObjectName("labtoolsBcaSampleProposalPanel")
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("pageKey", "bca_od_mvp")
        frame.setProperty("semanticKey", PageKey.LABTOOLS_IMMUNO_ABSORBANCE.value)
        frame.setStyleSheet("QFrame#labtoolsBcaSampleProposalPanel { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        header = QLabel("Sample concentration proposal")
        header.setStyleSheet("font-weight: 700;")
        layout.addWidget(header)
        status = QLabel(f"local_data: {model.status.status}")
        status.setObjectName("labtoolsBcaLocalDataStatus")
        status.setProperty("status", model.status.status)
        status.setWordWrap(True)
        layout.addWidget(status)
        compatible_samples = tuple(sample for sample in model.samples if sample.wb_compatible or sample.sample_type in {"", "unknown"})
        if not compatible_samples:
            layout.addWidget(
                make_empty_state(
                    "暂无可生成 proposal 的 sample",
                    model.status.reason,
                    empty_state_key="empty_project",
                    semantic_key=PageKey.LABTOOLS_IMMUNO_ABSORBANCE.value,
                )
            )
        for sample in compatible_samples:
            row = QPushButton(
                f"{sample.sample_name} | current {sample.concentration or 'no concentration'} {sample.concentration_unit or ''}".strip()
            )
            row.setObjectName("labtoolsBcaSampleRow")
            row.setProperty("sampleId", sample.sample_id)
            row.setProperty("version", sample.version)
            row.clicked.connect(lambda _checked=False, item=sample: self._select_labtools_bca_sample(item))
            layout.addWidget(row)
        self._labtools_bca_proposal_inputs = {}
        layout.addLayout(self._labtools_bca_proposal_input_row("拟更新浓度", "concentration", "2.5"))
        layout.addLayout(self._labtools_bca_proposal_input_row("浓度单位", "concentration_unit", "mg/mL"))
        actions = QHBoxLayout()
        propose = make_button("生成 sample concentration update proposal", role="secondary")
        propose.setObjectName("labtoolsBcaProposalButton")
        propose.clicked.connect(self._create_labtools_bca_sample_proposal)
        confirm = make_button("确认写入 sample concentration", role="secondary")
        confirm.setObjectName("labtoolsBcaConfirmProposalButton")
        confirm.setEnabled(False)
        confirm.setProperty("disabledState", "proposal_required")
        confirm.clicked.connect(self._confirm_labtools_bca_sample_proposal)
        actions.addWidget(propose)
        actions.addWidget(confirm)
        actions.addStretch(1)
        layout.addLayout(actions)
        self._labtools_bca_proposal_button = propose
        self._labtools_bca_confirm_proposal_button = confirm
        proposal_status = QLabel("proposal 默认不写入 sample；确认后才更新本地 sample concentration。")
        proposal_status.setObjectName("labtoolsBcaProposalStatus")
        proposal_status.setProperty("status", "idle")
        proposal_status.setWordWrap(True)
        layout.addWidget(proposal_status)
        self._labtools_bca_proposal_status = proposal_status
        if compatible_samples:
            self._select_labtools_bca_sample(compatible_samples[0])
        layout.addWidget(
            self._labtools_notice_card(
                "BCA/OD 仅生成 sample concentration update proposal；不会自动覆盖 sample concentration。",
                object_name="labtoolsAdapterNotice",
                semantic_key=PageKey.LABTOOLS_IMMUNO_ABSORBANCE.value,
            )
        )
        layout.addStretch(1)
        return frame

    def _labtools_bca_proposal_input_row(self, label: str, field_id: str, default_text: str) -> QHBoxLayout:
        row = QHBoxLayout()
        title = QLabel(label)
        title.setObjectName("labtoolsBcaProposalInputLabel")
        title.setProperty("fieldId", field_id)
        field = QLineEdit(default_text)
        field.setObjectName("labtoolsBcaProposalInput")
        field.setProperty("fieldId", field_id)
        self._labtools_bca_proposal_inputs[field_id] = field
        row.addWidget(title)
        row.addWidget(field, 1)
        return row

    def _labtools_wb_results_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("labtoolsWbSampleResultPanel")
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("pageKey", "wb_loading")
        frame.setProperty("semanticKey", PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value)
        frame.setProperty("uiPrimitive", "result_panel")
        frame.setProperty("formalResult", False)
        frame.setProperty("fakeGelOutput", False)
        frame.setProperty("reportGenerationAllowed", False)
        frame.setStyleSheet("QFrame#labtoolsWbSampleResultPanel { background: transparent; border: 0; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        sample_panel = QFrame()
        sample_panel.setObjectName("labtoolsWbSampleListPanel")
        sample_panel.setStyleSheet(
            f"QFrame#labtoolsWbSampleListPanel {{ border: 1px solid {PROTEIN_WB_TOKENS['border']}; "
            f"border-radius: 12px; background: {PROTEIN_WB_TOKENS['surface']}; }}"
        )
        sample_layout = QVBoxLayout(sample_panel)
        sample_layout.setContentsMargins(16, 14, 16, 14)
        sample_layout.setSpacing(9)
        sample_header = QHBoxLayout()
        sample_title = QLabel("样本列表")
        sample_title.setStyleSheet(f"color: {PROTEIN_WB_TOKENS['text']}; font-size: 14px; font-weight: 850;")
        add = make_button("添加样本", role="primary")
        add.setEnabled(False)
        add.setFixedHeight(30)
        import_btn = make_button("导入样本", role="secondary")
        import_btn.setEnabled(False)
        import_btn.setFixedHeight(30)
        sample_header.addWidget(sample_title)
        sample_header.addStretch(1)
        sample_header.addWidget(add)
        sample_header.addWidget(import_btn)
        sample_layout.addLayout(sample_header)
        self._labtools_wb_sample_rows = QVBoxLayout()
        self._labtools_wb_sample_rows.setSpacing(4)
        sample_frame = QFrame()
        sample_frame.setObjectName("labtoolsWbSampleTable")
        sample_frame.setMinimumHeight(104)
        sample_frame.setStyleSheet(
            f"QFrame#labtoolsWbSampleTable {{ border: 0; border-radius: 0; background: {PROTEIN_WB_TOKENS['surface']}; }}"
        )
        sample_frame.setLayout(self._labtools_wb_sample_rows)
        sample_layout.addWidget(sample_frame)
        layout.addWidget(sample_panel)

        result_panel = QFrame()
        result_panel.setObjectName("labtoolsWbResultPanel")
        result_panel.setStyleSheet(
            f"QFrame#labtoolsWbResultPanel {{ border: 1px solid {PROTEIN_WB_TOKENS['border']}; "
            f"border-radius: 12px; background: {PROTEIN_WB_TOKENS['surface']}; }}"
        )
        result_layout = QVBoxLayout(result_panel)
        result_layout.setContentsMargins(16, 14, 16, 14)
        result_layout.setSpacing(9)
        result_title = QLabel("上样计算结果")
        result_title.setStyleSheet(f"color: {PROTEIN_WB_TOKENS['text']}; font-size: 14px; font-weight: 850;")
        result_subtitle = QLabel("基于最终上样体积 20 uL")
        result_subtitle.setStyleSheet(f"color: {PROTEIN_WB_TOKENS['muted']}; font-size: 11px;")
        result_layout.addWidget(result_title)
        result_layout.addWidget(result_subtitle)
        self._labtools_wb_result_rows = QVBoxLayout()
        self._labtools_wb_result_rows.setSpacing(4)
        result_frame = QFrame()
        result_frame.setObjectName("labtoolsWbResultTable")
        result_frame.setMinimumHeight(112)
        result_frame.setStyleSheet(
            f"QFrame#labtoolsWbResultTable {{ border: 0; border-radius: 0; background: {PROTEIN_WB_TOKENS['surface']}; }}"
        )
        result_frame.setLayout(self._labtools_wb_result_rows)
        result_layout.addWidget(result_frame)
        self._labtools_wb_issue_rows = QLabel("上样计算结果需由实验人员复核后用于台面操作。")
        self._labtools_wb_issue_rows.setObjectName("labtoolsWbIssueRows")
        self._labtools_wb_issue_rows.setWordWrap(True)
        self._labtools_wb_issue_rows.setStyleSheet(
            f"background: {PROTEIN_WB_TOKENS['red_soft']}; border: 1px solid #FDBA74; border-radius: 8px; "
            f"color: {PROTEIN_WB_TOKENS['red']}; padding: 10px; font-size: 11px;"
        )
        result_layout.addWidget(self._labtools_wb_issue_rows)
        layout.addWidget(result_panel)

        tips_panel = QFrame()
        tips_panel.setObjectName("labtoolsWbTipsPanel")
        tips_panel.setStyleSheet(
            f"QFrame#labtoolsWbTipsPanel {{ border: 1px solid {PROTEIN_WB_TOKENS['border']}; "
            f"border-radius: 12px; background: {PROTEIN_WB_TOKENS['surface']}; }}"
        )
        tips_layout = QVBoxLayout(tips_panel)
        tips_layout.setContentsMargins(16, 12, 16, 12)
        tips_layout.setSpacing(6)
        tips_title = QLabel("提示与注意事项")
        tips_title.setStyleSheet(f"color: {PROTEIN_WB_TOKENS['text']}; font-size: 13px; font-weight: 850;")
        tips_layout.addWidget(tips_title)
        for text in ("单位兼容性需确认（浓度 / 体积 / 质量）", "小体积移液需注意精度，建议复核", "实验计算结果需由用户复核后用于台面操作"):
            item = QLabel(f"• {text}")
            item.setStyleSheet(f"color: {PROTEIN_WB_TOKENS['muted']}; font-size: 11px;")
            tips_layout.addWidget(item)
        layout.addWidget(tips_panel)
        self._labtools_wb_detail_text = QPlainTextEdit()
        self._labtools_wb_detail_text.setObjectName("labtoolsWbDetailText")
        self._labtools_wb_detail_text.setReadOnly(True)
        self._labtools_wb_detail_text.setMinimumHeight(120)
        self._labtools_wb_detail_text.setVisible(False)
        layout.addWidget(self._labtools_wb_detail_text)
        return frame

    def _labtools_wb_lane_panel(self) -> QFrame:
        outer = QFrame()
        outer.setObjectName("labtoolsWbRightColumn")
        outer.setProperty("pageKey", "wb_loading")
        outer.setProperty("semanticKey", PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value)
        outer.setStyleSheet("QFrame#labtoolsWbRightColumn { background: transparent; border: 0; }")
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(12)
        lane_frame = QFrame()
        lane_frame.setObjectName("labtoolsWbLaneGrid")
        lane_frame.setMinimumHeight(270)
        lane_frame.setStyleSheet(
            f"QFrame#labtoolsWbLaneGrid {{ border: 0; border-radius: 0; background: {PROTEIN_WB_TOKENS['surface_subtle']}; }}"
        )
        self._labtools_wb_lane_grid = QGridLayout()
        self._labtools_wb_lane_grid.setSpacing(4)
        self._labtools_wb_lane_grid.setContentsMargins(8, 8, 8, 8)
        lane_frame.setLayout(self._labtools_wb_lane_grid)
        frame = make_preview_card(
            title="泳道布局预览",
            preview_widget=lane_frame,
            status_key="testing",
            semantic_state="testing",
            caption="布局为示意，不代表实际电泳或成像结果。",
            object_name="labtoolsWbLanePreviewPanel",
        )
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("pageKey", "wb_loading")
        frame.setProperty("semanticKey", PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value)
        frame.setProperty("fakeGelBands", False)
        frame.setProperty("imageAnalysisEnabled", False)
        frame.setStyleSheet(
            f"QFrame#labtoolsWbLanePreviewPanel {{ border: 1px solid {PROTEIN_WB_TOKENS['border']}; "
            f"border-radius: 12px; background: {PROTEIN_WB_TOKENS['surface']}; }}"
        )
        layout = frame.layout()
        edit = make_button("编辑布局", role="secondary")
        edit.setObjectName("labtoolsWbEditLayoutButton")
        edit.setEnabled(False)
        edit.setProperty("disabledState", "preview_only")
        if isinstance(layout, QVBoxLayout):
            layout.addWidget(edit)
        outer_layout.addWidget(frame)

        review = QFrame()
        review.setObjectName("labtoolsWbStatusReviewCard")
        review.setStyleSheet(
            f"QFrame#labtoolsWbStatusReviewCard {{ border: 1px solid {PROTEIN_WB_TOKENS['border']}; "
            f"border-radius: 12px; background: {PROTEIN_WB_TOKENS['surface']}; }}"
        )
        review_layout = QVBoxLayout(review)
        review_layout.setContentsMargins(17, 16, 17, 16)
        review_layout.setSpacing(11)
        title = QLabel("状态与复核")
        title.setStyleSheet(f"color: {PROTEIN_WB_TOKENS['text']}; font-size: 15px; font-weight: 850;")
        review_layout.addWidget(title)
        chip_row = QHBoxLayout()
        chip_row.setSpacing(6)
        chip_row.addWidget(make_status_chip("后端可用", status_key="testing"))
        chip_row.addWidget(make_status_chip("需文件适配", status_key="planned"))
        chip_row.addWidget(make_status_chip("需复核", status_key="testing"))
        chip_row.addStretch(1)
        review_layout.addLayout(chip_row)
        warning = QLabel("请复核样品浓度、上样体积与泳道布局后再进入下一步。")
        warning.setWordWrap(True)
        warning.setStyleSheet(
            f"background: {PROTEIN_WB_TOKENS['amber_soft']}; border: 1px solid #FCD34D; "
            f"border-radius: 8px; color: {PROTEIN_WB_TOKENS['amber']}; padding: 10px; font-size: 12px;"
        )
        review_layout.addWidget(warning)
        outer_layout.addWidget(review)
        outer_layout.addStretch(1)
        return outer

    def _labtools_wb_input_row(self, label: str, field_id: str, default_value: str, unit: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        column = QVBoxLayout()
        column.setSpacing(6)
        title = QLabel(label)
        title.setObjectName("labtoolsWbInputLabel")
        title.setProperty("fieldId", field_id)
        title.setStyleSheet(f"color: {PROTEIN_WB_TOKENS['muted']}; font-size: 11px; font-weight: 700;")
        field = QLineEdit(default_value)
        field.setObjectName("labtoolsWbInput")
        field.setProperty("fieldId", field_id)
        field.setMinimumHeight(32)
        field.setStyleSheet(
            f"background: {PROTEIN_WB_TOKENS['field']}; border: 1px solid #BFDBFE; "
            f"border-radius: 7px; color: {PROTEIN_WB_TOKENS['blue']}; padding: 5px 9px; font-size: 12px;"
        )
        self._labtools_wb_inputs[field_id] = field
        unit_label = QLabel(unit)
        unit_label.setObjectName("labtoolsWbInputUnit")
        unit_label.setProperty("fieldId", field_id)
        unit_label.setMinimumWidth(34)
        unit_label.setAlignment(Qt.AlignCenter)
        unit_label.setStyleSheet(f"color: {PROTEIN_WB_TOKENS['muted']}; font-size: 11px;")
        row.addWidget(field, 1)
        row.addWidget(unit_label)
        column.addWidget(title)
        column.addLayout(row)
        wrapper = QHBoxLayout()
        wrapper.addLayout(column, 1)
        return wrapper

    def _run_labtools_wb_loading(self) -> None:
        result = labtools_runtime.calculate_wb_loading_preview(
            target_protein_ug=self._labtools_wb_inputs["target_protein_ug"].text().strip(),
            loading_buffer_factor=self._labtools_wb_inputs["loading_buffer_factor"].text().strip(),
            final_volume_ul=self._labtools_wb_inputs["final_volume_ul"].text().strip(),
            reducing_agent_enabled=True,
            lane_count=self._labtools_wb_inputs["lane_count"].text().strip() or "10",
            local_samples=getattr(self, "_labtools_local_data_read_model", labtools_runtime.LabToolsLocalDataReadModel(labtools_runtime.get_labtools_local_data_status(None))).wb_samples,
        )
        self._render_labtools_wb_loading_result(result)

    def _render_labtools_wb_loading_result(self, result: labtools_runtime.WBLoadingUiResult) -> None:
        self._labtools_wb_last_result = result
        self._clear_layout(self._labtools_wb_sample_rows)
        sample_header = QLabel("#      样本 ID        蛋白浓度        单位        重复        备注")
        sample_header.setObjectName("labtoolsWbSampleHeader")
        sample_header.setStyleSheet(f"color: {PROTEIN_WB_TOKENS['muted']}; font-size: 11px; font-weight: 750;")
        self._labtools_wb_sample_rows.addWidget(sample_header)
        for sample in result.samples:
            label = QLabel(f"{sample.sample_id} | {sample.concentration} | {sample.note}")
            label.setObjectName("labtoolsWbSampleRow")
            label.setProperty("sampleId", sample.sample_id)
            label.setMinimumHeight(28)
            label.setStyleSheet(
                f"color: {PROTEIN_WB_TOKENS['text']}; font-size: 12px; border-top: 1px solid {PROTEIN_WB_TOKENS['divider']}; padding-top: 5px;"
            )
            self._labtools_wb_sample_rows.addWidget(label)
        self._clear_layout(self._labtools_wb_result_rows)
        result_header = QLabel("#      样本 ID        样品体积 (uL)        4X Buffer (uL)        水 (uL)        总体积")
        result_header.setObjectName("labtoolsWbResultHeader")
        result_header.setStyleSheet(f"color: {PROTEIN_WB_TOKENS['muted']}; font-size: 11px; font-weight: 750;")
        self._labtools_wb_result_rows.addWidget(result_header)
        for row_data in result.rows:
            row = QLabel(
                f"{row_data.sample_id} | sample {row_data.sample_volume} | buffer {row_data.loading_buffer_volume} | "
                f"water {row_data.diluent_volume} | total {row_data.final_volume} | {row_data.status}"
            )
            row.setObjectName("labtoolsWbResultRow")
            row.setProperty("sampleId", row_data.sample_id)
            row.setProperty("status", row_data.status)
            row.setWordWrap(False)
            row.setMinimumHeight(24)
            row.setToolTip(row.text())
            result_color = PROTEIN_WB_TOKENS["red"] if row_data.status != "OK" else PROTEIN_WB_TOKENS["text"]
            row.setStyleSheet(
                f"color: {result_color}; font-size: 11px; font-weight: {'800' if row_data.status != 'OK' else '650'}; "
                f"border-top: 1px solid {PROTEIN_WB_TOKENS['divider']};"
            )
            self._labtools_wb_result_rows.addWidget(row)
            for issue in row_data.issues:
                issue_label = QLabel(f"{row_data.sample_id} warning: {issue}")
                issue_label.setObjectName("labtoolsWbWarningRow")
                issue_label.setProperty("sampleId", row_data.sample_id)
                issue_label.setWordWrap(True)
                issue_label.setVisible(False)
                issue_label.setStyleSheet(
                    f"background: {PROTEIN_WB_TOKENS['red_soft']}; color: {PROTEIN_WB_TOKENS['red']}; "
                    f"border: 1px solid #FED7AA; border-radius: 8px; padding: 8px; font-size: 11px;"
                )
                self._labtools_wb_result_rows.addWidget(issue_label)
        self._clear_layout(self._labtools_wb_lane_grid)
        for index, lane in enumerate(result.lanes):
            card = QFrame()
            card.setObjectName("labtoolsWbLaneCard")
            card.setProperty("laneNumber", lane.lane_number)
            card.setProperty("laneType", lane.lane_type)
            card.setProperty("status", lane.status)
            color = "#FEF2F2" if lane.status == "Error" else ("#F8FAFC" if lane.lane_type == "empty" else "#EFF6FF")
            border = "#EF4444" if lane.status == "Error" else ("#CBD5E1" if lane.lane_type == "empty" else "#93C5FD")
            card.setMinimumHeight(108)
            card.setStyleSheet(f"QFrame#labtoolsWbLaneCard {{ border: 1px solid {border}; border-radius: 4px; background: {color}; }}")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(4, 6, 4, 6)
            layout.setSpacing(5)
            lane_label = QLabel(f"Lane {lane.lane_number}")
            lane_label.setObjectName("labtoolsWbLaneNumber")
            lane_label.setAlignment(Qt.AlignCenter)
            lane_label.setStyleSheet(f"color: {PROTEIN_WB_TOKENS['muted']}; font-size: 9px; font-weight: 750;")
            sample_label = QLabel(lane.sample_id)
            sample_label.setObjectName("labtoolsWbLaneSample")
            sample_label.setProperty("laneNumber", lane.lane_number)
            sample_label.setAlignment(Qt.AlignCenter)
            sample_label.setStyleSheet(f"color: {PROTEIN_WB_TOKENS['text']}; font-size: 10px; font-weight: 800;")
            band = QFrame()
            band.setObjectName("labtoolsWbLaneBandMarker")
            band.setFixedHeight(4)
            band.setStyleSheet(f"background: {border}; border: 0; border-radius: 2px;")
            volume_label = QLabel(lane.sample_volume or "Empty / 空白")
            volume_label.setObjectName("labtoolsWbLaneVolume")
            volume_label.setProperty("laneNumber", lane.lane_number)
            volume_label.setAlignment(Qt.AlignCenter)
            volume_label.setStyleSheet(f"color: {PROTEIN_WB_TOKENS['muted']}; font-size: 9px;")
            layout.addWidget(lane_label)
            layout.addStretch(1)
            layout.addWidget(band)
            layout.addStretch(1)
            layout.addWidget(sample_label)
            layout.addWidget(volume_label)
            self._labtools_wb_lane_grid.addWidget(card, index // 5, index % 5)
        issues = list(result.errors) + list(result.warnings)
        self._labtools_wb_issue_rows.setText("\n".join(f"- {issue}" for issue in issues))
        self._labtools_wb_issue_rows.setProperty("hasError", bool(result.errors))
        self._labtools_wb_detail_text.setPlainText(result.detail_text)
        self._labtools_wb_copy_text = result.copy_text if result.valid else result.detail_text

    def _copy_labtools_wb_summary(self) -> None:
        from PySide6.QtWidgets import QApplication

        if getattr(self, "_labtools_wb_copy_text", ""):
            QApplication.clipboard().setText(self._labtools_wb_copy_text)

    def _labtools_wb_history_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("labtoolsWbHistoryPanel")
        frame.setProperty("pageKey", "wb_loading")
        frame.setProperty("semanticKey", PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value)
        frame.setStyleSheet("QFrame#labtoolsWbHistoryPanel { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(8)
        title = QLabel("WB 项目存储历史 / WB History Preview")
        title.setStyleSheet("font-weight: 700;")
        layout.addWidget(title)
        self._labtools_wb_history_status = QLabel("未连接项目存储上下文。")
        self._labtools_wb_history_status.setObjectName("labtoolsWbHistoryStatus")
        self._labtools_wb_history_status.setWordWrap(True)
        layout.addWidget(self._labtools_wb_history_status)
        self._labtools_wb_history_list = QListWidget()
        self._labtools_wb_history_list.setObjectName("labtoolsWbHistoryList")
        self._labtools_wb_history_list.currentItemChanged.connect(self._select_labtools_wb_history_item)
        layout.addWidget(self._labtools_wb_history_list)
        self._labtools_wb_history_detail = QPlainTextEdit()
        self._labtools_wb_history_detail.setObjectName("labtoolsWbHistoryDetail")
        self._labtools_wb_history_detail.setReadOnly(True)
        self._labtools_wb_history_detail.setMinimumHeight(90)
        layout.addWidget(self._labtools_wb_history_detail)
        return frame

    def _save_labtools_wb_record(self) -> None:
        result_data = getattr(self, "_labtools_wb_last_result", None)
        if result_data is None:
            return
        result = labtools_runtime.create_local_record_summary(
            self._labtools_project_root,
            {
                "record_type": "wb_loading",
                "title": result_data.title,
                "summary": result_data.primary_result,
                "linked_samples": [sample.sample_id for sample in getattr(self, "_labtools_local_data_read_model", labtools_runtime.LabToolsLocalDataReadModel(labtools_runtime.get_labtools_local_data_status(None))).wb_samples],
                "artifact_refs": ["ui:wb_loading:local-summary-only"],
                "status": "draft",
            },
        )
        self._report_labtools_local_write_result(result, self._labtools_wb_issue_rows)
        self._labtools_local_data_read_model = labtools_runtime.get_labtools_local_data_read_model(self._labtools_project_root)
        self._refresh_labtools_wb_history()

    def _export_labtools_wb_markdown(self) -> None:
        result_data = getattr(self, "_labtools_wb_last_result", None)
        if result_data is None:
            return
        path = self._choose_labtools_export_path("导出 WB Loading Markdown", ".md", "wb_loading.md", "Markdown (*.md)")
        if path is None:
            self._report_labtools_export_cancelled(self._labtools_wb_issue_rows)
            return
        result = labtools_runtime.export_wb_loading_markdown(path, result_data)
        self._report_labtools_storage_result(result, self._labtools_wb_issue_rows)

    def _export_labtools_wb_csv(self) -> None:
        result_data = getattr(self, "_labtools_wb_last_result", None)
        if result_data is None:
            return
        path = self._choose_labtools_export_path("导出 WB Loading CSV", ".csv", "wb_loading.csv", "CSV (*.csv)")
        if path is None:
            self._report_labtools_export_cancelled(self._labtools_wb_issue_rows)
            return
        result = labtools_runtime.export_wb_loading_csv(path, result_data)
        self._report_labtools_storage_result(result, self._labtools_wb_issue_rows)

    def _refresh_labtools_wb_history(self) -> None:
        if not hasattr(self, "_labtools_wb_history_list"):
            return
        self._labtools_wb_history_list.clear()
        records = labtools_runtime.list_local_record_summaries(self._labtools_project_root, record_type="wb_loading")
        if not records:
            self._labtools_wb_history_status.setText("暂无 WB 本地记录摘要；保存后会写入 local_data record index。")
            self._labtools_wb_history_detail.setPlainText("")
            return
        self._labtools_wb_history_status.setText("本地实验记录摘要；不是正式报告。")
        for record in records:
            item = QListWidgetItem(f"{record.created_at} | {record.title}")
            item.setData(Qt.UserRole, record)
            self._labtools_wb_history_list.addItem(item)
        self._labtools_wb_history_list.setCurrentRow(self._labtools_wb_history_list.count() - 1)

    def _select_labtools_wb_history_item(self, current, _previous) -> None:
        if current is None:
            self._labtools_wb_history_detail.setPlainText("")
            return
        record = current.data(Qt.UserRole)
        if record is None:
            self._labtools_wb_history_detail.setPlainText("")
            return
        self._labtools_wb_history_detail.setPlainText(
            f"record_id: {record.record_id}\nstatus: {record.status}\nversion: {record.version}\n"
            f"linked_samples: {', '.join(record.linked_samples) or 'none'}\nsummary: {record.summary}\n\n本地实验记录摘要，不是正式报告。"
        )

    def _set_storage_gated_button_state(self, button: QPushButton, enabled: bool, disabled_state: str) -> None:
        button.setEnabled(enabled)
        button.setProperty("disabledState", "" if enabled else disabled_state)

    def _report_labtools_storage_result(self, result, issue_label: QLabel) -> None:
        lines = [f"- {result.message}"]
        if result.path is not None:
            lines.append(f"- 路径：{result.path}")
        if result.record_id:
            lines.append(f"- record_id: {result.record_id}")
        for warning in result.warnings:
            lines.append(f"- warning: {warning}")
        for error in result.errors:
            lines.append(f"- error: {error}")
        issue_label.setText("\n".join(lines))
        issue_label.setProperty("hasError", not result.ok)

    def _report_labtools_local_write_result(self, result: labtools_runtime.LabToolsLocalWriteResult, issue_label: QLabel) -> None:
        lines = [f"- {result.message}"]
        if result.entity_id:
            lines.append(f"- record_id: {result.entity_id}")
        if result.new_version is not None:
            lines.append(f"- version: {result.new_version}")
        lines.append("- 保存的是本地实验记录摘要，不是正式报告。")
        issue_label.setText("\n".join(lines))
        issue_label.setProperty("hasError", not result.success)
        issue_label.setProperty("status", result.status)

    def _report_labtools_export_cancelled(self, issue_label: QLabel) -> None:
        issue_label.setText("- 导出已取消；未写入任何文件。")
        issue_label.setProperty("hasError", False)

    def _choose_labtools_export_path(self, caption: str, suffix: str, suggested_name: str, file_filter: str):
        start = suggested_name
        if self._labtools_project_root is not None:
            start = str(self._labtools_project_root / "project_storage" / "labtools" / "exports" / suggested_name)
        selected, _filter = QFileDialog.getSaveFileName(self, caption, start, file_filter)
        if not selected:
            return None
        path = Path(selected)
        if path.suffix.lower() != suffix:
            path = path.with_suffix(suffix)
        return path

    def _show_labtools_sds_page_boundary(self) -> None:
        semantic_key = PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value
        content = self._build_labtools_base_content(
            page_key="sds_page",
            semantic_key=semantic_key,
            title="SDS-PAGE / 配胶边界页",
            subtitle="SDS-PAGE 属于 Protein Experiment 后续 subpage；当前只展示 adapter-needed 结构，不执行真实保存或 XLSX 导出。",
        )
        root = content.layout()
        root.addLayout(self._labtools_boundary_nav(status_label="adapter_needed / file_picker_needed", status_key="planned"))
        body = QHBoxLayout()
        body.setSpacing(12)
        body.addWidget(
            self._labtools_boundary_panel(
                "模板选择",
                ["Mini-PROTEAN TGX 4-20%（示例）", "10 孔 / 1 胶（静态布局）", "模板保存需存储适配。"],
                object_name="labtoolsSdsTemplatePanel",
            )
        )
        body.addWidget(
            self._labtools_boundary_panel(
                "Resolving gel section",
                ["Acrylamide %：待用户确认", "Buffer / APS / TEMED：adapter-needed placeholder", "配胶计算需后续 UI adapter。"],
                object_name="labtoolsSdsResolvingPanel",
            )
        )
        body.addWidget(
            self._labtools_boundary_panel(
                "Stacking gel section",
                ["Stacking %：静态占位", "体积与组分表暂不导出。", "导出 XLSX 需文件选择器适配。"],
                object_name="labtoolsSdsStackingPanel",
            )
        )
        root.addLayout(body)
        root.addWidget(self._labtools_notice_card("配胶计算 / 导出 XLSX 需文件选择器适配；本页不启用模板保存、历史记录或 XLSX export。", object_name="labtoolsAdapterNotice", semantic_key=semantic_key))
        root.addLayout(
            self._labtools_boundary_actions(
                page_key="sds_page",
                semantic_key=semantic_key,
                actions=(
                    ("保存配胶模板 - 需存储适配", "disabled_missing_storage_adapter"),
                    ("导出 XLSX - 需文件选择器", "disabled_missing_file_picker"),
                    ("历史记录 - 需存储适配", "disabled_missing_storage_adapter"),
                ),
            )
        )
        root.addStretch(1)
        self._set_labtools_content(content)

    def _show_labtools_bca_od_boundary(self) -> None:
        semantic_key = PageKey.LABTOOLS_IMMUNO_ABSORBANCE.value
        content = self._build_labtools_base_content(
            page_key="bca_od_mvp",
            semantic_key=semantic_key,
            title="BCA / OD MVP Boundary",
            subtitle="8 x 12 OD matrix、孔位标注和 linear-fit summary 仅作为 testing / MVP preview；不保存、不导出、不生成正式报告。",
        )
        root = content.layout()
        root.addLayout(self._labtools_boundary_nav(status_label="testing / MVP preview", status_key="testing"))
        self._labtools_local_data_read_model = labtools_runtime.get_labtools_local_data_read_model(self._labtools_project_root)
        self._labtools_bca_selected_sample_id = ""
        self._labtools_bca_pending_proposal = None
        body = QHBoxLayout()
        body.setSpacing(12)
        matrix_panel = QFrame()
        matrix_panel.setObjectName("labtoolsBcaMatrixPanel")
        matrix_panel.setStyleSheet("QFrame#labtoolsBcaMatrixPanel { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        matrix_layout = QGridLayout(matrix_panel)
        matrix_layout.setContentsMargins(12, 12, 12, 12)
        matrix_layout.setSpacing(4)
        for col in range(12):
            header = QLabel(str(col + 1))
            header.setAlignment(Qt.AlignCenter)
            header.setObjectName("labtoolsBcaMatrixHeader")
            matrix_layout.addWidget(header, 0, col + 1)
        for row_index, row_name in enumerate("ABCDEFGH", start=1):
            row_header = QLabel(row_name)
            row_header.setAlignment(Qt.AlignCenter)
            row_header.setObjectName("labtoolsBcaMatrixHeader")
            matrix_layout.addWidget(row_header, row_index, 0)
            for col in range(1, 13):
                well = QLabel("空")
                if row_name == "A" and col <= 3:
                    well.setText(f"Std {col}")
                elif row_name in ("B", "C") and col <= 2:
                    well.setText("Sample")
                well.setObjectName("labtoolsBcaWellCell")
                well.setProperty("wellId", f"{row_name}{col}")
                well.setAlignment(Qt.AlignCenter)
                well.setStyleSheet("border: 1px solid #E5E7EB; border-radius: 4px; padding: 4px; background: #F8FAFC;")
                matrix_layout.addWidget(well, row_index, col)
        body.addWidget(matrix_panel, 3)
        side = self._labtools_boundary_panel(
            "孔位标注 / Summary",
            [
                "标准孔：A1-A3；样本孔：B1-C2（示例）",
                "Linear-fit summary：testing / MVP preview",
                "R2: 0.91 low R2 warning",
                "High CV warning",
                "Negative corrected OD warning",
                "Out-of-range warning",
            ],
            object_name="labtoolsBcaSidePanel",
        )
        body.addWidget(side, 1)
        body.addWidget(self._labtools_bca_sample_proposal_panel(self._labtools_local_data_read_model), 1)
        root.addLayout(body)
        root.addWidget(self._labtools_notice_card("BCA / OD MVP 不包含免疫吸光度后续分析、正式报告或临床级定量；保存 BCA 记录和导出结果保持禁用。", object_name="labtoolsAdapterNotice", semantic_key=semantic_key))
        root.addLayout(
            self._labtools_boundary_actions(
                page_key="bca_od_mvp",
                semantic_key=semantic_key,
                actions=(
                    ("保存 BCA 记录 - 后端记录模型未完成", "disabled_backend_missing"),
                    ("导出结果 - 暂未开放", "disabled_missing_file_picker"),
                    ("历史记录 - 暂未开放", "disabled_missing_storage_adapter"),
                ),
            )
        )
        root.addStretch(1)
        self._set_labtools_content(content)

    def _show_labtools_cell_experiment_workspace(self) -> None:
        semantic_key = PageKey.LABTOOLS_CELL_EXPERIMENTS.value
        content = self._build_labtools_base_content(
            page_key="cell_experiment_workspace",
            semantic_key=semantic_key,
            title="细胞实验 / Cell Experiment",
            subtitle="细胞信息、实验记录模板与结果处理工具的独立工作区；当前 record store 未接入，保存记录保持禁用。",
        )
        content.setStyleSheet(
            """
            QWidget#labtoolsContentPanel {
                background: #F5F7FB;
            }
            QFrame#labtoolsCellExperimentTabBar,
            QFrame#labtoolsCellExperimentMainCard,
            QFrame#labtoolsCellTemplateCard,
            QFrame#labtoolsCellHistoryCard,
            QFrame#labtoolsCellProfilePanel,
            QFrame#labtoolsCellProcessingPanel {
                background: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
            }
            QFrame#labtoolsCellExperimentTab {
                background: #F1F5F9;
                border: 1px solid transparent;
                border-radius: 0;
            }
            QFrame#labtoolsCellExperimentTab[selected="true"] {
                background: #FFFFFF;
                border-color: #BFDBFE;
                border-bottom: 2px solid #0EA5E9;
            }
            QLabel#labtoolsCellTitle,
            QLabel#labtoolsBoundaryPanelTitle {
                color: #111827;
                font-size: 13px;
                font-weight: 850;
            }
            QLabel#labtoolsCellMuted,
            QLabel#labtoolsCellSmall {
                color: #64748B;
                font-size: 11px;
            }
            QLabel#labtoolsCellTemplateIcon {
                background: #EFF6FF;
                border-radius: 8px;
                color: #0284C7;
                font-size: 15px;
                font-weight: 900;
            }
            QLabel#labtoolsCellCapabilityChip {
                background: #DCFCE7;
                border: 1px solid #86EFAC;
                border-radius: 10px;
                color: #059669;
                font-size: 10px;
                font-weight: 850;
                padding: 3px 7px;
            }
            QLabel#labtoolsCellStorageChip {
                background: #FFF7ED;
                border: 1px solid #FDBA74;
                border-radius: 10px;
                color: #EA580C;
                font-size: 10px;
                font-weight: 850;
                padding: 3px 7px;
            }
            QLabel#labtoolsCellProfileRow,
            QLabel#labtoolsCellProcessingRow {
                background: #F8FAFC;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                color: #334155;
                font-size: 11px;
                padding: 7px 9px;
            }
            QPushButton#labtoolsCellTemplateButton {
                background: #F1F5F9;
                border: 1px solid #D8E1EC;
                border-radius: 8px;
                color: #475569;
                font-size: 11px;
                font-weight: 750;
                padding: 8px 10px;
            }
            QPushButton#labtoolsCellTemplateButton[primary="true"] {
                background: #0EA5E9;
                border-color: #0EA5E9;
                color: #FFFFFF;
            }
            """
        )
        root = content.layout()
        root.addLayout(self._labtools_boundary_nav(status_label="shell_only / record_store_missing", status_key="shell_only"))
        local_model = labtools_runtime.get_labtools_local_data_read_model(self._labtools_project_root)

        chips = QHBoxLayout()
        chips.setSpacing(8)
        for text, key in (
            ("Developer Preview / 本地测试版", "testing"),
            ("记录保存需适配", "blocked"),
            ("结果处理仅外部能力配置", "testing"),
        ):
            chips.addWidget(make_status_chip(text, status_key=key))
        chips.addStretch(1)
        root.addLayout(chips)

        tab_bar = QFrame()
        tab_bar.setObjectName("labtoolsCellExperimentTabBar")
        tab_layout = QHBoxLayout(tab_bar)
        tab_layout.setContentsMargins(12, 0, 12, 0)
        tab_layout.setSpacing(0)
        for title, subtitle, selected in (
            ("细胞信息 / Cell Profile & Dynamic State", "Cell Information", False),
            ("细胞实验记录 / Experiment Record Templates", "Experiment Records", True),
            ("细胞结果处理工具 / Result Processing", "Result Processing", False),
        ):
            tab = QFrame()
            tab.setObjectName("labtoolsCellExperimentTab")
            tab.setProperty("selected", selected)
            tab.setMinimumHeight(66)
            tab_inner = QVBoxLayout(tab)
            tab_inner.setContentsMargins(20, 10, 20, 10)
            tab_inner.setSpacing(2)
            tab_title = QLabel(title)
            tab_title.setObjectName("labtoolsBoundaryPanelTitle")
            tab_subtitle = QLabel(subtitle)
            tab_subtitle.setObjectName("labtoolsCellMuted")
            tab_inner.addWidget(tab_title)
            tab_inner.addWidget(tab_subtitle)
            tab_layout.addWidget(tab, 1)
        root.addWidget(tab_bar)

        main_card = QFrame()
        main_card.setObjectName("labtoolsCellExperimentMainCard")
        main_layout = QVBoxLayout(main_card)
        main_layout.setContentsMargins(20, 18, 20, 20)
        main_layout.setSpacing(12)
        header = QHBoxLayout()
        title = QLabel("细胞实验记录")
        title.setObjectName("labtoolsCellTitle")
        subtitle = QLabel("Experiment Record Templates")
        subtitle.setObjectName("labtoolsCellMuted")
        header.addWidget(title)
        header.addWidget(subtitle)
        header.addStretch(1)
        main_layout.addLayout(header)
        template_summary = QLabel("传代、复苏、冻存、接种、给药 / 处理、转染")
        template_summary.setObjectName("labtoolsCellMuted")
        main_layout.addWidget(template_summary)

        def template_card(title_text: str, subtitle_text: str, description: str, *, primary: bool = False) -> QFrame:
            card = QFrame()
            card.setObjectName("labtoolsCellTemplateCard")
            card.setMinimumHeight(136)
            layout = QVBoxLayout(card)
            layout.setContentsMargins(14, 14, 14, 14)
            layout.setSpacing(8)
            top = QHBoxLayout()
            icon = QLabel("+" if title_text == "接种" else "↻")
            icon.setObjectName("labtoolsCellTemplateIcon")
            icon.setFixedSize(28, 28)
            icon.setAlignment(Qt.AlignCenter)
            labels = QVBoxLayout()
            label = QLabel(title_text)
            label.setObjectName("labtoolsCellTitle")
            sub = QLabel(subtitle_text)
            sub.setObjectName("labtoolsCellMuted")
            labels.addWidget(label)
            labels.addWidget(sub)
            top.addWidget(icon)
            top.addLayout(labels, 1)
            layout.addLayout(top)
            desc = QLabel(description)
            desc.setObjectName("labtoolsCellMuted")
            desc.setWordWrap(True)
            layout.addWidget(desc)
            if primary:
                chip_row = QHBoxLayout()
                chip_row.addWidget(QLabel("接种：计算辅助可用；保存记录 disabled"))
                chip_row.itemAt(0).widget().setObjectName("labtoolsCellCapabilityChip")
                chip_row.addWidget(QLabel("保存需适配"))
                chip_row.itemAt(1).widget().setObjectName("labtoolsCellStorageChip")
                chip_row.addStretch(1)
                layout.addLayout(chip_row)
            button = QPushButton("+ 打开接种计算辅助" if primary else "+ 新建记录 · 需记录存储适配")
            button.setObjectName("labtoolsCellTemplateButton")
            button.setProperty("primary", primary)
            button.setProperty("formalActionEnabled", False)
            button.setMinimumHeight(34)
            button.setEnabled(primary)
            if primary:
                button.clicked.connect(lambda _checked=False: self._open_labtools_quick_task("quick_cell_seeding"))
            layout.addWidget(button)
            return card

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        cards = (
            ("传代", "Passage", "记录传代比例、消化时间、接种密度", False),
            ("复苏", "Revival", "记录复苏批次、复苏时间、培养条件", False),
            ("冻存", "Cryopreservation", "记录冻存批次、冻存管、冻存液", False),
            ("接种", "Cell Seeding", "记录接种密度、孔板格式、体积", True),
            ("给药 / 处理", "Drug Treatment", "记录处理条件、剂量、时间点", False),
            ("转染", "Transfection", "记录转染试剂、核酸量、时间点", False),
        )
        for index, (label, sub, desc, primary) in enumerate(cards):
            grid.addWidget(template_card(label, sub, desc, primary=primary), index // 3, index % 3)
        main_layout.addLayout(grid)
        history = QFrame()
        history.setObjectName("labtoolsCellHistoryCard")
        history_layout = QHBoxLayout(history)
        history_layout.setContentsMargins(16, 14, 16, 14)
        history_layout.setSpacing(12)
        history_text = QVBoxLayout()
        history_title = QLabel("从上次记录创建")
        history_title.setObjectName("labtoolsCellTitle")
        history_desc = QLabel("基于历史记录继续实验流程\n需要历史记录存储；不显示假保存记录或假时间线。")
        history_desc.setObjectName("labtoolsCellMuted")
        history_text.addWidget(history_title)
        history_text.addWidget(history_desc)
        history_layout.addLayout(history_text, 1)
        history_button = QPushButton("创建记录 · 暂不可用")
        history_button.setObjectName("labtoolsCellTemplateButton")
        history_button.setEnabled(False)
        history_button.setProperty("formalActionEnabled", False)
        history_button.setMinimumHeight(34)
        history_layout.addWidget(history_button)
        main_layout.addWidget(history)
        root.addWidget(main_card)

        summary_row = QHBoxLayout()
        summary_row.setSpacing(12)
        profile_panel = QFrame()
        profile_panel.setObjectName("labtoolsCellProfilePanel")
        profile_layout = QVBoxLayout(profile_panel)
        profile_layout.setContentsMargins(14, 12, 14, 12)
        profile_layout.setSpacing(8)
        profile_title = QLabel("细胞信息 / Cell Profile & Dynamic State")
        profile_title.setObjectName("labtoolsBoundaryPanelTitle")
        profile_layout.addWidget(profile_title)
        for text in (
            f"local_data status: {local_model.status.status}",
            f"local cell profiles: {local_model.status.cell_count}",
            "Cell line: A549（mock-labelled shell field）",
            "Passage: P12",
            "Culture condition: DMEM + 10% FBS, 37 C, 5% CO2",
            "Current state: 培养中 / 待处理",
            *[f"Local cell: {cell.cell_name} P{cell.passage} · {cell.storage_status}" for cell in local_model.cells],
        ):
            row = QLabel(text)
            row.setObjectName("labtoolsCellProfileRow")
            row.setWordWrap(True)
            profile_layout.addWidget(row)
        summary_row.addWidget(profile_panel, 1)

        result_panel = QFrame()
        result_panel.setObjectName("labtoolsCellProcessingPanel")
        result_layout = QVBoxLayout(result_panel)
        result_layout.setContentsMargins(14, 12, 14, 12)
        result_layout.setSpacing(8)
        result_title = QLabel("细胞结果处理工具 / Result Processing")
        result_title.setObjectName("labtoolsBoundaryPanelTitle")
        result_layout.addWidget(result_title)
        for text in (
            f"freeze vial overview: {', '.join(local_model.freeze_vial_status_rows)}",
            *[f"Local vial: {vial.vial_label} · {vial.status} · {vial.location or 'no location'}" for vial in local_model.freeze_vials[:6]],
            "Scratch / Transwell / Fluorescence/Staining：规划中",
            "ImageJ/Fiji：Settings-linked 外部能力配置入口",
            "不显示自动 ROI、自动细胞计数或自动分析结果。",
        ):
            row = QLabel(text)
            row.setObjectName("labtoolsCellProcessingRow")
            row.setWordWrap(True)
            result_layout.addWidget(row)
        settings_button = make_button("前往 Settings 外部能力配置", role="secondary")
        settings_button.setObjectName("labtoolsSettingsLinkButton")
        settings_button.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        settings_button.setProperty("pageKey", "cell_experiment_workspace")
        settings_button.setProperty("semanticKey", PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value)
        settings_button.clicked.connect(self.show_settings)
        result_layout.addWidget(settings_button)
        summary_row.addWidget(result_panel, 1)
        root.addLayout(summary_row)
        root.addWidget(self._labtools_notice_card("当前项目暂无保存的细胞实验记录；记录保存需要后续 CellExperimentRecordStore 适配完成后方可启用。", object_name="labtoolsAdapterNotice", semantic_key=semantic_key))
        root.addLayout(
            self._labtools_boundary_actions(
                page_key="cell_experiment_workspace",
                semantic_key=semantic_key,
                actions=(
                    ("保存细胞记录 - 后端未完成", "disabled_backend_missing"),
                    ("导出细胞记录 - 后端未完成", "disabled_backend_missing"),
                    ("运行图像分析 - 暂未开放", "disabled_backend_missing"),
                    ("历史记录 - 需存储适配", "disabled_missing_storage_adapter"),
                ),
            )
        )
        root.addStretch(1)
        self._set_labtools_content(content)

    def _show_labtools_elisa_boundary(self) -> None:
        semantic_key = PageKey.LABTOOLS_IMMUNO_ABSORBANCE.value
        content = self._build_labtools_base_content(
            page_key="elisa_boundary",
            semantic_key=semantic_key,
            title="ELISA / Immuno-Absorbance Boundary",
            subtitle="路径：LabTools > 实验模块 > 免疫与吸光度。状态 blocked_until_backend；当前不运行 ELISA 分析。",
        )
        root = content.layout()
        root.addLayout(self._labtools_boundary_nav(status_label="blocked_until_backend", status_key="blocked"))
        body = QHBoxLayout()
        body.setSpacing(12)
        body.addWidget(
            self._labtools_boundary_panel(
                "标准曲线与样本稀释",
                ["标准曲线模型尚未固化。", "样本稀释流程尚未接入。", "当前不生成正式结果。"],
                object_name="labtoolsElisaStandardCurvePanel",
            )
        )
        body.addWidget(
            self._labtools_boundary_panel(
                "记录 / 报告 / 导出",
                ["记录保存：disabled", "报告：不生成正式报告", "生产级保存 / 导出：disabled"],
                object_name="labtoolsElisaReportPanel",
            )
        )
        root.addLayout(body)
        root.addWidget(self._labtools_notice_card("ELISA 后端未完成；运行分析、保存记录和导出报告都保持禁用。", object_name="labtoolsAdapterNotice", semantic_key=semantic_key))
        root.addLayout(
            self._labtools_boundary_actions(
                page_key="elisa_boundary",
                semantic_key=semantic_key,
                actions=(
                    ("运行 ELISA 分析 - 后端未完成", "disabled_backend_missing"),
                    ("保存记录 - 后端未完成", "disabled_backend_missing"),
                    ("导出报告 - 后端未完成", "disabled_backend_missing"),
                ),
            )
        )
        root.addStretch(1)
        self._set_labtools_content(content)

    def _show_labtools_image_processing_boundary(self) -> None:
        semantic_key = "labtools.page.image_processing_boundary"
        content = self._build_labtools_base_content(
            page_key="image_processing_boundary",
            semantic_key=semantic_key,
            title="Image Processing Workspace / 图像处理边界",
            subtitle="通用图像处理工作台结构预览；ImageJ/Fiji 仅作为 Settings-linked 外部能力配置，不运行图像分析。",
        )
        root = content.layout()
        root.addLayout(self._labtools_boundary_nav(status_label="shell_only / external_engine_adapter_missing", status_key="shell_only"))
        body = QHBoxLayout()
        body.setSpacing(12)
        body.addWidget(self._labtools_boundary_panel("图像列表", ["未导入图像", "本阶段不读取文件、不批量处理。"], object_name="labtoolsImageListPanel"), 1)
        body.addWidget(self._labtools_boundary_panel("中央图像预览", ["空预览区域", "不显示自动 ROI 或分析结果。"], object_name="labtoolsImagePreviewPanel"), 2)
        option_panel = self._labtools_boundary_panel(
            "功能选项",
            [
                "Scratch：planned",
                "Transwell：planned",
                "WB band ROI：planned",
                "IHC / staining：planned",
                "ImageJ/Fiji：外部能力配置",
            ],
            object_name="labtoolsImageOptionPanel",
        )
        option_layout = option_panel.layout()
        settings_button = make_button("前往 Settings 外部能力配置", role="secondary")
        settings_button.setObjectName("labtoolsSettingsLinkButton")
        settings_button.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        settings_button.setProperty("pageKey", "image_processing_boundary")
        settings_button.setProperty("semanticKey", PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value)
        settings_button.clicked.connect(self.show_settings)
        option_layout.addWidget(settings_button)
        body.addWidget(option_panel, 1)
        root.addLayout(body)
        root.addWidget(self._labtools_notice_card("不启用自动 ROI、自动细胞计数、自动条带识别、自动 IHC scoring；运行分析、保存和导出均保持 disabled。", object_name="labtoolsAdapterNotice", semantic_key=semantic_key))
        root.addLayout(
            self._labtools_boundary_actions(
                page_key="image_processing_boundary",
                semantic_key=semantic_key,
                actions=(
                    ("运行分析 - 暂未开放", "disabled_backend_missing"),
                    ("保存图像结果 - 暂未开放", "disabled_missing_storage_adapter"),
                    ("导出结果 - 暂未开放", "disabled_missing_file_picker"),
                ),
            )
        )
        root.addStretch(1)
        self._set_labtools_content(content)

    def _labtools_boundary_nav(self, *, status_label: str, status_key: str) -> QHBoxLayout:
        nav = QHBoxLayout()
        back = make_button("返回实验模块", role="secondary")
        back.setObjectName("labtoolsBackButton")
        back.clicked.connect(self._show_labtools_experiment_modules_shell)
        nav.addWidget(back)
        nav.addWidget(make_status_chip(status_label, status_key=status_key))
        nav.addStretch(1)
        return nav

    def _labtools_boundary_panel(self, title: str, rows: list[str], *, object_name: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName(object_name)
        frame.setStyleSheet(f"QFrame#{object_name} {{ border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }}")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        header = QLabel(title)
        header.setObjectName("labtoolsBoundaryPanelTitle")
        header.setStyleSheet("font-weight: 700;")
        layout.addWidget(header)
        for row in rows:
            label = QLabel(row)
            label.setObjectName("labtoolsBoundaryPanelRow")
            label.setWordWrap(True)
            layout.addWidget(label)
        layout.addStretch(1)
        return frame

    def _labtools_boundary_actions(self, *, page_key: str, semantic_key: str, actions: tuple[tuple[str, str], ...]) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)
        for text, disabled_state in actions:
            action = make_button(text, role="secondary")
            action.setObjectName("labtoolsBoundaryActionButton")
            action.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
            action.setProperty("pageKey", page_key)
            action.setProperty("semanticKey", semantic_key)
            action.setProperty("disabledState", disabled_state)
            action.setEnabled(False)
            row.addWidget(action)
        row.addStretch(1)
        return row

    def _show_labtools_experiment_modules_shell(self) -> None:
        content = self._build_labtools_section_content(
            page_key="experiment_modules",
            semantic_key=PageKey.LABTOOLS_EXPERIMENT_MODULES.value,
            title="实验模块 / Experiment Modules",
            subtitle="实验模块只建立二级占位路由；不会启用 WB、BCA、ELISA、细胞记录或 ImageJ/Fiji 的真实执行。",
            status_label="testing / shell-only boundaries",
            status_key="testing",
            cards=[
                {
                    "title": "Western Blot Loading",
                    "page_key": "wb_loading",
                    "semantic_key": PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value,
                    "status_label": "active_backend_ready / adapter_needed",
                    "status_key": "testing",
                    "rows": ["WB 上样计算 focused UI。", "调用只读计算预览；保存和导出保持禁用。"],
                    "callback": self._show_labtools_wb_loading_page,
                },
                {
                    "title": "SDS-PAGE",
                    "page_key": "sds_page",
                    "semantic_key": PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value,
                    "status_label": "active_backend_ready / adapter_needed",
                    "status_key": "planned",
                    "rows": ["配胶子页面占位。", "XLSX 导出和模板持久化未启用。"],
                    "callback": self._show_labtools_sds_page_boundary,
                },
                {
                    "title": "BCA / OD MVP Boundary",
                    "page_key": "bca_od_mvp",
                    "semantic_key": PageKey.LABTOOLS_IMMUNO_ABSORBANCE.value,
                    "status_label": "testing_preview_only",
                    "status_key": "testing",
                    "rows": ["8 x 12 OD matrix / annotation / linear-fit summary 仅保留边界占位。", "不声明正式保存、导出或临床级定量。"],
                    "callback": self._show_labtools_bca_od_boundary,
                },
                {
                    "title": "Cell Experiment Workspace",
                    "page_key": "cell_experiment_workspace",
                    "semantic_key": PageKey.LABTOOLS_CELL_EXPERIMENTS.value,
                    "status_label": "shell_only / record_store_missing",
                    "status_key": "shell_only",
                    "rows": ["细胞信息、实验记录模板、结果处理工具三主区占位。", "保存细胞记录保持禁用。"],
                    "callback": self._show_labtools_cell_experiment_workspace,
                },
                {
                    "title": "ELISA / Immuno-Absorbance",
                    "page_key": "elisa_boundary",
                    "semantic_key": PageKey.LABTOOLS_IMMUNO_ABSORBANCE.value,
                    "status_label": "blocked_until_backend",
                    "status_key": "blocked",
                    "rows": ["ELISA backend 未完成。", "不启用正式报告、保存或导出。"],
                    "callback": self._show_labtools_elisa_boundary,
                },
                {
                    "title": "Image Processing Workspace",
                    "page_key": "image_processing_boundary",
                    "semantic_key": "labtools.page.image_processing_boundary",
                    "status_label": "shell_only / external_engine_adapter_missing",
                    "status_key": "shell_only",
                    "rows": ["ImageJ/Fiji 仅作为 Settings-linked 外部能力入口。", "不运行自动 ROI、自动细胞计数或条带识别。"],
                    "callback": self._show_labtools_image_processing_boundary,
                },
            ],
        )
        self._set_labtools_content(content)

    def _build_labtools_section_content(
        self,
        *,
        page_key: str,
        semantic_key: str,
        title: str,
        subtitle: str,
        status_label: str,
        status_key: str,
        cards: list[dict],
        notice_rows: list[str] | None = None,
    ) -> QWidget:
        content = self._build_labtools_base_content(page_key=page_key, semantic_key=semantic_key, title=title, subtitle=subtitle)
        root = content.layout()
        nav = QHBoxLayout()
        back = make_button("返回 LabTools 首页", role="secondary")
        back.setObjectName("labtoolsBackButton")
        back.clicked.connect(self._show_labtools_home)
        nav.addWidget(back)
        nav.addWidget(make_status_chip(status_label, status_key=status_key))
        nav.addStretch(1)
        root.addLayout(nav)
        if notice_rows:
            for row in notice_rows:
                root.addWidget(self._labtools_notice_card(row, object_name="labtoolsAdapterNotice", semantic_key=semantic_key))

        grid = QGridLayout()
        grid.setSpacing(12)
        for index, card in enumerate(cards):
            grid.addWidget(self._labtools_secondary_entry_card(**card), index // 2, index % 2)
        root.addLayout(grid)
        root.addWidget(
            make_empty_state(
                "暂无历史记录",
                "历史记录、保存和导出需要 storage/export adapter；本阶段只保留安全壳层。",
                empty_state_key="empty_history",
                semantic_key=semantic_key,
            )
        )
        root.addStretch(1)
        return content

    def _show_labtools_placeholder_page(
        self,
        *,
        title: str,
        page_key: str,
        semantic_key: str,
        status_label: str,
        status_key: str,
        body_rows: list[str],
        disabled_actions: tuple[str, ...],
        settings_link: bool = False,
    ) -> None:
        content = self._build_labtools_base_content(
            page_key=page_key,
            semantic_key=semantic_key,
            title=title,
            subtitle="UI-C2b 导航壳层：只展示页面入口、状态边界和禁用动作，不执行真实业务逻辑。",
        )
        root = content.layout()
        nav = QHBoxLayout()
        back_home = make_button("返回 LabTools 首页", role="secondary")
        back_home.setObjectName("labtoolsBackButton")
        back_home.clicked.connect(self._show_labtools_home)
        nav.addWidget(back_home)
        nav.addWidget(make_status_chip(status_label, status_key=status_key))
        nav.addStretch(1)
        root.addLayout(nav)
        card = self._labtools_boundary_card("页面边界", body_rows)
        card.setProperty("pageKey", page_key)
        card.setProperty("semanticKey", semantic_key)
        root.addWidget(card)
        root.addWidget(
            make_empty_state(
                "暂无运行结果",
                "本阶段不生成计算结果、报告、导出文件或保存记录。",
                empty_state_key="empty_result",
                semantic_key=semantic_key,
            )
        )
        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        for text in disabled_actions:
            action = make_button(text, role="secondary")
            action.setObjectName("labtoolsDisabledActionButton")
            action.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
            action.setProperty("pageKey", page_key)
            action.setProperty("semanticKey", semantic_key)
            action.setProperty("disabledState", "adapter_needed_or_blocked")
            action.setEnabled(False)
            action_row.addWidget(action)
        if settings_link:
            settings_button = make_button("前往 Settings 外部能力配置", role="secondary")
            settings_button.setObjectName("labtoolsSettingsLinkButton")
            settings_button.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
            settings_button.setProperty("pageKey", page_key)
            settings_button.setProperty("semanticKey", PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value)
            settings_button.clicked.connect(self.show_settings)
            action_row.addWidget(settings_button)
        action_row.addStretch(1)
        root.addLayout(action_row)
        root.addStretch(1)
        self._set_labtools_content(content)

    def _labtools_primary_entry_card(
        self,
        *,
        title: str,
        page_key: str,
        semantic_key: str,
        status_key: str,
        rows: list[str],
        callback,
        english_title: str = "",
        description: str = "",
        button_text: str = "查看壳层",
    ) -> QFrame:
        frame = QFrame()
        frame.setObjectName("labtoolsPrimaryEntryCard")
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("pageKey", page_key)
        frame.setProperty("semanticKey", semantic_key)
        frame.setProperty("statusKey", status_key)
        frame.setProperty("uiPrimitive", "module_entry_card")
        frame.setProperty("formalActionEnabled", False)
        frame.setStyleSheet(
            f"""
            QFrame#labtoolsPrimaryEntryCard {{
                background: {LABTOOLS_HOME_TOKENS['surface']};
                border: 1px solid {LABTOOLS_HOME_TOKENS['border']};
                border-radius: 12px;
            }}
            """
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(13)
        header = QVBoxLayout()
        header.setSpacing(16)
        header.addWidget(self._labtools_icon_label(semantic_key, object_name="labtoolsEntryIcon", size=26), 0, Qt.AlignLeft)
        title_label = QLabel(title)
        title_label.setObjectName("labtoolsPrimaryEntryTitle")
        title_label.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        title_label.setProperty("pageKey", page_key)
        title_label.setProperty("semanticKey", semantic_key)
        title_label.setStyleSheet(f"color: {LABTOOLS_HOME_TOKENS['text']}; font-size: 20px; font-weight: 800;")
        header.addWidget(title_label)
        if english_title:
            english = QLabel(english_title)
            english.setObjectName("labtoolsPrimaryEntryEnglishTitle")
            english.setStyleSheet(f"color: {LABTOOLS_HOME_TOKENS['blue']}; font-size: 13px; font-weight: 800;")
            header.addWidget(english)
        layout.addLayout(header)
        if description:
            desc = QLabel(description)
            desc.setObjectName("labtoolsPrimaryEntryDescription")
            desc.setWordWrap(True)
            desc.setStyleSheet(f"color: {LABTOOLS_HOME_TOKENS['muted']}; font-size: 13px; line-height: 18px;")
            layout.addWidget(desc)
        hidden_chip = make_status_chip(status_key=status_key)
        hidden_chip.setVisible(False)
        layout.addWidget(hidden_chip)
        hidden_categories = None
        if semantic_key == PageKey.LABTOOLS_EXPERIMENT_MODULES.value:
            hidden_categories = QWidget()
            hidden_categories.setObjectName("labtoolsHiddenCategoryIconHost")
            hidden_categories.setVisible(False)
            hidden_categories.setLayout(self._labtools_experiment_category_icon_row())
            layout.addWidget(hidden_categories)
            legacy_summary = QLabel("细胞实验、蛋白实验、核酸实验、免疫与吸光度实验、免疫组化。")
            legacy_summary.setObjectName("labtoolsEntryDetail")
            legacy_summary.setVisible(False)
            layout.addWidget(legacy_summary)
        list_container = QVBoxLayout()
        list_container.setSpacing(8)
        for row in rows:
            item = QHBoxLayout()
            item.setSpacing(9)
            bullet = QLabel("✓")
            bullet.setObjectName("labtoolsEntryBulletIcon")
            bullet.setFixedSize(18, 18)
            bullet.setAlignment(Qt.AlignCenter)
            bullet.setStyleSheet(
                f"background: {LABTOOLS_HOME_TOKENS['green_soft']}; color: {LABTOOLS_HOME_TOKENS['green']}; border-radius: 9px; font-size: 10px; font-weight: 800;"
            )
            label = QLabel(row)
            label.setObjectName("labtoolsEntryDetail")
            label.setWordWrap(True)
            label.setStyleSheet(f"color: {LABTOOLS_HOME_TOKENS['text']}; font-size: 13px;")
            item.addWidget(bullet, 0, Qt.AlignTop)
            item.addWidget(label, 1)
            list_container.addLayout(item)
        layout.addLayout(list_container)
        layout.addStretch(1)
        button = make_button(button_text, role="primary", semantic_state=status_key, action_key=page_key)
        button.setObjectName("labtoolsEntryButton")
        button.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        button.setProperty("pageKey", page_key)
        button.setProperty("semanticKey", semantic_key)
        button.setProperty("statusKey", status_key)
        button.setMinimumHeight(40)
        button.clicked.connect(callback)
        layout.addWidget(button)
        return frame

    def _labtools_secondary_entry_card(self, *, title: str, page_key: str, semantic_key: str, status_label: str, status_key: str, rows: list[str], callback) -> QFrame:
        frame = QFrame()
        frame.setObjectName("labtoolsSecondaryEntryCard")
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("pageKey", page_key)
        frame.setProperty("semanticKey", semantic_key)
        frame.setProperty("statusKey", status_key)
        frame.setStyleSheet("QFrame#labtoolsSecondaryEntryCard { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        header = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("labtoolsSecondaryEntryTitle")
        title_label.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        title_label.setProperty("pageKey", page_key)
        title_label.setProperty("semanticKey", semantic_key)
        title_label.setStyleSheet("font-weight: 700;")
        header.addWidget(title_label)
        header.addStretch(1)
        header.addWidget(make_status_chip(status_label, status_key=status_key))
        layout.addLayout(header)
        for row in rows:
            label = QLabel(row)
            label.setObjectName("labtoolsSecondaryEntryDetail")
            label.setWordWrap(True)
            layout.addWidget(label)
        button = make_button("查看占位页", role="secondary")
        button.setObjectName("labtoolsSecondaryEntryButton")
        button.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        button.setProperty("pageKey", page_key)
        button.setProperty("semanticKey", semantic_key)
        button.setProperty("statusKey", status_key)
        button.clicked.connect(callback)
        layout.addWidget(button)
        return frame

    def _labtools_notice_card(self, text: str, *, object_name: str, semantic_key: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName(object_name)
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("semanticKey", semantic_key)
        frame.setStyleSheet(f"QFrame#{object_name} {{ border: 1px solid #F5D899; border-radius: 8px; background: #FFF7E6; }}")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        label = QLabel(text)
        label.setObjectName("labtoolsNoticeText")
        label.setWordWrap(True)
        layout.addWidget(label)
        return frame

    def _labtools_icon_label(self, semantic_key: str, *, object_name: str, size: int = 28) -> QLabel:
        label = QLabel()
        label.setObjectName(object_name)
        label.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        label.setProperty("semanticKey", semantic_key)
        label.setProperty("iconSource", str(LABTOOLS_ICON_PATHS.get(semantic_key, "")))
        container_size = 52 if object_name == "labtoolsEntryIcon" else size + 14 if object_name == "labtoolsHomeHeaderIcon" else size + 8
        label.setFixedSize(container_size, container_size)
        label.setAlignment(Qt.AlignCenter)
        if object_name in {"labtoolsEntryIcon", "labtoolsHomeHeaderIcon"}:
            radius = 14 if object_name == "labtoolsEntryIcon" else 8
            label.setStyleSheet(
                f"background: {LABTOOLS_HOME_TOKENS['blue_soft']}; border: 0; border-radius: {radius}px; color: {LABTOOLS_HOME_TOKENS['blue']};"
            )
        pixmap = load_labtools_pixmap(semantic_key, size)
        if pixmap.isNull():
            label.setText("•")
            label.setProperty("iconFallback", True)
        else:
            label.setPixmap(pixmap)
            label.setProperty("iconFallback", False)
        return label

    def _labtools_experiment_category_icon_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        categories = (
            ("细胞实验", PageKey.LABTOOLS_CELL_EXPERIMENTS.value),
            ("蛋白实验", PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value),
            ("核酸实验", PageKey.LABTOOLS_NUCLEIC_ACID_EXPERIMENTS.value),
            ("免疫与吸光度", PageKey.LABTOOLS_IMMUNO_ABSORBANCE.value),
            ("免疫组化", PageKey.LABTOOLS_IHC.value),
        )
        for title, semantic_key in categories:
            chip = QFrame()
            chip.setObjectName("labtoolsExperimentCategoryIconChip")
            chip.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
            chip.setProperty("semanticKey", semantic_key)
            chip.setStyleSheet("QFrame#labtoolsExperimentCategoryIconChip { border: 0; background: transparent; }")
            chip_layout = QVBoxLayout(chip)
            chip_layout.setContentsMargins(0, 0, 0, 0)
            chip_layout.setSpacing(2)
            chip_layout.addWidget(self._labtools_icon_label(semantic_key, object_name="labtoolsCategoryIcon", size=24), alignment=Qt.AlignCenter)
            text = QLabel(title)
            text.setObjectName("labtoolsCategoryIconLabel")
            text.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
            text.setProperty("semanticKey", semantic_key)
            text.setAlignment(Qt.AlignCenter)
            text.setStyleSheet("font-size: 11px; color: #64748B;")
            chip_layout.addWidget(text)
            row.addWidget(chip)
        row.addStretch(1)
        return row

    def _labtools_experiment_module_card(self, title: str, *, page_key: str, semantic_key: str, status_key: str, rows: list[str]) -> QFrame:
        frame = QFrame()
        frame.setObjectName("labtoolsExperimentModuleCard")
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("pageKey", page_key)
        frame.setProperty("semanticKey", semantic_key)
        frame.setProperty("statusKey", status_key)
        frame.setStyleSheet("QFrame#labtoolsExperimentModuleCard { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        header = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("labtoolsExperimentModuleTitle")
        title_label.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        title_label.setProperty("pageKey", page_key)
        title_label.setProperty("semanticKey", semantic_key)
        title_label.setStyleSheet("font-weight: 700;")
        header.addWidget(title_label)
        header.addStretch(1)
        header.addWidget(make_status_chip(status_key=status_key))
        layout.addLayout(header)
        for row in rows:
            label = QLabel(row)
            label.setObjectName("labtoolsExperimentModuleDetail")
            label.setWordWrap(True)
            layout.addWidget(label)
        return frame

    def _labtools_boundary_card(self, title: str, rows: list[str]) -> QFrame:
        frame = QFrame()
        frame.setObjectName("labtoolsBoundaryCard")
        frame.setStyleSheet("QFrame#labtoolsBoundaryCard { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        header = QLabel(title)
        header.setObjectName("labtoolsBoundaryTitle")
        header.setStyleSheet("font-weight: 700;")
        layout.addWidget(header)
        for row in rows:
            label = QLabel(row)
            label.setObjectName("labtoolsBoundaryDetail")
            label.setWordWrap(True)
            layout.addWidget(label)
        return frame

    def _build_settings_page(self) -> QWidget:
        return build_settings_page(
            profile=SettingsProfile(),
            settings_resource_pixmap_loader=load_settings_resource_pixmap,
        )

    def _build_settings_general_page(self, profile: SettingsProfile) -> QWidget:
        page = QWidget()
        page.setObjectName("settingsGeneralPage")
        page.setProperty("moduleKey", ModuleKey.SETTINGS.value)
        page.setProperty("pageKey", "general")
        page.setProperty("semanticKey", PageKey.SETTINGS_GENERAL.value)
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)
        root.addWidget(
            self._settings_status_card(
                title="通用偏好",
                status_key="shell_only",
                rows=[
                    ("默认项目路径", profile.default_project_path),
                    ("语言", profile.language),
                    ("图表样式", profile.chart_style),
                    ("导出格式", profile.export_format),
                    ("缓存清理", profile.cache_cleanup),
                ],
            )
        )
        root.addWidget(self._icon_asset_status_card(detailed=False))
        root.addStretch(1)
        return page

    def _build_settings_external_capabilities_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("settingsExternalCapabilitiesPage")
        page.setProperty("moduleKey", ModuleKey.SETTINGS.value)
        page.setProperty("pageKey", "external_capabilities")
        page.setProperty("semanticKey", PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value)
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)
        root.addWidget(QLabel("检测优先：先显示本机状态，再由用户主动触发安装或更新；本阶段不执行真实安装、下载或云端配置。"))
        for title, status_key, resource_keys, details in (
            (
                "Python 环境",
                "available",
                ["resource_python"],
                [
                    ("检测目标", "Python executable / package visibility"),
                    ("后续动作", "用户触发安装或更新，当前禁用"),
                ],
            ),
            (
                "R 环境",
                "not_configured",
                ["resource_r"],
                [
                    ("检测目标", "Rscript / R packages"),
                    ("后续动作", "检测后提示用户安装，当前禁用"),
                ],
            ),
            (
                "ImageJ/Fiji",
                "not_configured",
                ["resource_imagej_fiji"],
                [
                    ("检测目标", "本地 ImageJ/Fiji executable"),
                    ("归属", "LabTools 外部图像引擎，不进入主任务页"),
                ],
            ),
            (
                "外部图像分析引擎",
                "planned",
                ["resource_image_analysis_engine", "resource_external_engine", "resource_pdf_ocr"],
                [
                    ("检测目标", "engine path / version / capability manifest"),
                    ("边界", "仅壳层占位，不连接真实引擎"),
                ],
            ),
        ):
            root.addWidget(self._settings_capability_card(title, status_key=status_key, resource_keys=resource_keys, details=details))
        root.addStretch(1)
        return page

    def _build_settings_analysis_resources_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("settingsAnalysisResourcesPage")
        page.setProperty("moduleKey", ModuleKey.SETTINGS.value)
        page.setProperty("pageKey", "analysis_resources")
        page.setProperty("semanticKey", PageKey.SETTINGS_ANALYSIS_RESOURCES.value)
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)
        for title, status_key, resource_keys, details in (
            (
                "GO / KEGG / MSigDB 资源",
                "planned",
                ["resource_go", "resource_kegg"],
                [
                    ("检测目标", "本地资源 manifest 与版本"),
                    ("边界", "不自动下载数据库"),
                ],
            ),
            (
                "Bioinformatics resolver / input package",
                "preflight_only",
                ["resource_analysis_package"],
                [
                    ("检测目标", "standardized repository 与 analysis input package"),
                    ("边界", "resolver-first，未通过预检不显示正式运行承诺"),
                ],
            ),
            (
                "Report / Export templates",
                "developer_preview",
                ["resource_plotting_package"],
                [
                    ("检测目标", "Markdown / HTML / DOCX template availability"),
                    ("边界", "报告模板多语言化后再正式开放"),
                ],
            ),
        ):
            root.addWidget(self._settings_capability_card(title, status_key=status_key, resource_keys=resource_keys, details=details))
        root.addStretch(1)
        return page

    def _build_settings_model_engine_page(self, profile: SettingsProfile) -> QWidget:
        page = QWidget()
        page.setObjectName("settingsModelEnginePage")
        page.setProperty("moduleKey", ModuleKey.SETTINGS.value)
        page.setProperty("pageKey", "model_engine")
        page.setProperty("semanticKey", PageKey.SETTINGS_MODEL_ENGINE.value)
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)
        root.addWidget(
            self._settings_capability_card(
                "本地 AI 模型",
                status_key="not_configured",
                resource_keys=["resource_local_model"],
                details=[
                    ("当前配置", profile.local_ai_model),
                    ("检测目标", "local model gateway / provider availability"),
                    ("边界", "AI suggestion 仅为辅助建议，不自动生成结论"),
                ],
            )
        )
        root.addWidget(
            self._settings_capability_card(
                "外部云端模型配置",
                status_key="blocked",
                resource_keys=["resource_cloud_ai"],
                details=[
                    ("当前状态", "本阶段不配置云端服务"),
                    ("后续动作", "需要安全策略、密钥策略和用户确认流程"),
                ],
            )
        )
        root.addStretch(1)
        return page

    def _build_settings_developer_diagnostics_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("settingsDeveloperDiagnosticsPage")
        page.setProperty("moduleKey", ModuleKey.SETTINGS.value)
        page.setProperty("pageKey", "developer_diagnostics")
        page.setProperty("semanticKey", PageKey.SETTINGS_DEVELOPER_DIAGNOSTICS.value)
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        toggle = QToolButton()
        toggle.setObjectName("developerDiagnosticsToggle")
        toggle.setText(diagnostic_disclosure_title("Settings resources"))
        toggle.setCheckable(True)
        toggle.setChecked(False)
        toggle.setToolButtonStyle(Qt.ToolButtonTextOnly)
        root.addWidget(toggle)

        panel = self._settings_status_card(
            title="诊断信息",
            status_key="developer_preview",
            resource_keys=["resource_developer_diagnostics"],
            rows=[
                ("用途", "仅供开发者查看本地检测槽位、图标资源状态和壳层边界。"),
                ("外部动作", "不会安装、下载、更新或连接云端。"),
                ("覆盖范围", "Settings 二级导航、状态标签、检测优先 UI。"),
            ],
        )
        panel.setObjectName("developerDiagnosticsPanel")
        panel.setVisible(False)
        panel_layout = panel.layout()
        if isinstance(panel_layout, QVBoxLayout):
            panel_layout.addWidget(self._icon_asset_status_card(detailed=True))
        toggle.toggled.connect(panel.setVisible)
        root.addWidget(panel)
        root.addStretch(1)
        return page

    def _settings_resource_icon_label(self, resource_key: str, *, status_key: str, size: int = 28) -> QLabel:
        label = QLabel()
        label.setObjectName("settingsResourceIcon")
        label.setFixedSize(size + 8, size + 8)
        label.setProperty("moduleKey", ModuleKey.SETTINGS.value)
        label.setProperty("resourceKey", resource_key)
        label.setProperty("semanticKey", _SETTINGS_RESOURCE_SEMANTIC_KEYS.get(resource_key, ""))
        label.setProperty("statusKey", status_key)
        icon_source = SETTINGS_RESOURCE_ICON_PATHS.get(resource_key)
        pixmap = load_settings_resource_pixmap(resource_key, size=size)
        if pixmap.isNull():
            label.setText("·")
            label.setAlignment(Qt.AlignCenter)
            label.setProperty("iconFallback", True)
        else:
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignCenter)
            label.setProperty("iconFallback", False)
        label.setProperty("iconSource", str(icon_source) if icon_source is not None else "")
        label.setToolTip(resource_key.replace("resource_", "").replace("_", " "))
        return label

    def _settings_status_card(
        self,
        *,
        title: str,
        status_key: str,
        rows: list[tuple[str, str]],
        resource_keys: list[str] | None = None,
    ) -> QFrame:
        frame = QFrame()
        frame.setObjectName("settingsStatusCard")
        frame.setProperty("moduleKey", ModuleKey.SETTINGS.value)
        frame.setProperty("statusKey", status_key)
        frame.setProperty("resourceKeys", tuple(resource_keys or ()))
        frame.setStyleSheet("QFrame#settingsStatusCard { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        header = QHBoxLayout()
        for resource_key in resource_keys or []:
            header.addWidget(self._settings_resource_icon_label(resource_key, status_key=status_key))
        label = QLabel(title)
        label.setObjectName("settingsCardTitle")
        label.setProperty("moduleKey", ModuleKey.SETTINGS.value)
        label.setProperty("statusKey", status_key)
        label.setStyleSheet("font-weight: 700;")
        header.addWidget(label)
        header.addStretch(1)
        header.addWidget(make_status_chip(status_key=status_key))
        layout.addLayout(header)
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        for row, (name, value) in enumerate(rows):
            key_label = QLabel(name)
            key_label.setObjectName("settingsFieldLabel")
            key_label.setStyleSheet("color: #64748B;")
            value_label = QLabel(value)
            value_label.setObjectName("settingsFieldValue")
            value_label.setWordWrap(True)
            grid.addWidget(key_label, row, 0)
            grid.addWidget(value_label, row, 1)
        layout.addLayout(grid)
        return frame

    def _settings_capability_card(
        self,
        title: str,
        *,
        status_key: str,
        details: list[tuple[str, str]],
        resource_keys: list[str] | None = None,
    ) -> QFrame:
        frame = self._settings_status_card(title=title, status_key=status_key, rows=details, resource_keys=resource_keys)
        frame.setObjectName("settingsCapabilityCard")
        frame.setProperty("moduleKey", ModuleKey.SETTINGS.value)
        frame.setProperty("statusKey", status_key)
        frame.setProperty("resourceKeys", tuple(resource_keys or ()))
        frame.setStyleSheet("QFrame#settingsCapabilityCard { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        actions = QHBoxLayout()
        detect_button = make_button("检测状态", role="secondary")
        detect_button.setObjectName("settingsDetectButton")
        detect_button.setProperty("moduleKey", ModuleKey.SETTINGS.value)
        detect_button.setProperty("statusKey", status_key)
        detect_button.setProperty("semanticKey", PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value)
        install_button = make_button("安装 / 更新（检测后由用户触发）", role="ghost")
        install_button.setObjectName("settingsInstallButton")
        install_button.setProperty("moduleKey", ModuleKey.SETTINGS.value)
        install_button.setProperty("statusKey", status_key)
        install_button.setProperty("semanticKey", PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value)
        install_button.setEnabled(False)
        cloud_button = make_button("云端配置（未开放）", role="ghost")
        cloud_button.setObjectName("settingsCloudConfigButton")
        cloud_button.setProperty("moduleKey", ModuleKey.SETTINGS.value)
        cloud_button.setProperty("statusKey", status_key)
        cloud_button.setProperty("semanticKey", PageKey.SETTINGS_MODEL_ENGINE.value)
        cloud_button.setEnabled(False)
        actions.addWidget(detect_button)
        actions.addWidget(install_button)
        actions.addWidget(cloud_button)
        actions.addStretch(1)
        layout = frame.layout()
        if isinstance(layout, QVBoxLayout):
            layout.addLayout(actions)
        return frame

    def _icon_asset_status_card(self, *, detailed: bool = False) -> QFrame:
        summary = icon_asset_summary()
        rows = [
            f"图标槽位：{summary['total']}",
            f"已生成：{summary['generated']}",
            f"已接入：{summary['connected']}",
            f"已生成待接入：{summary['generated_waiting']}",
            f"待生成：{summary['pending']}",
        ]
        if detailed:
            rows.append("明细：")
            for item in icon_asset_statuses():
                usages = "；".join(item.usages) if item.usages else "未分配"
                rows.append(f"{item.state_label} · {item.category} · {item.label} · 调用：{usages}")
        return self._list_card("图标资源状态", rows)

    def _build_test_feedback_page(self) -> QWidget:
        summary = testing_mode_summary()
        lan_summary = lan_real_world_feedback_summary()
        page = QWidget()
        page.setObjectName("testFeedbackPage")
        root = QVBoxLayout(page)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)
        title = QLabel("Test Feedback / 测试反馈")
        title.setObjectName("testFeedbackTitle")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        root.addWidget(title)
        goal = QLabel(str(summary["goal"]))
        goal.setWordWrap(True)
        root.addWidget(goal)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.addWidget(self._list_card("推荐测试流程", list(summary["recommended_flow"])))
        content_layout.addWidget(self._list_card("可测试功能", list(summary["testable_features"])))
        content_layout.addWidget(self._list_card("暂未开放功能", list(summary["unavailable_features"])))
        content_layout.addWidget(self._list_card("已知限制", list(summary["known_limitations"])))
        content_layout.addWidget(self._list_card("反馈记录位置", [str(summary["feedback_location"])]))
        feedback_button = QPushButton("生成测试反馈模板")
        feedback_button.setObjectName("generateTestFeedbackButton")
        feedback_button.clicked.connect(self.generate_testing_feedback_template)
        content_layout.addWidget(feedback_button)
        content_layout.addWidget(
            self._list_card(
                "LabTools LAN 真实测试检查点",
                [
                    str(lan_summary["goal"]),
                    "人工真实局域网测试延后到界面完成后执行；当前只预留报告入口。",
                    "报告只保存本机 Markdown 文件，不自动发送网络请求。",
                    f"报告位置：{lan_summary['feedback_location']}",
                ],
            )
        )
        lan_feedback_button = QPushButton("生成 LAN 真实测试反馈报告")
        lan_feedback_button.setObjectName("generateLanFeedbackButton")
        lan_feedback_button.setProperty("feedbackType", "labtools_lan_real_world")
        lan_feedback_button.setProperty("networkRequestAllowed", False)
        lan_feedback_button.clicked.connect(self.generate_lan_testing_feedback_template)
        content_layout.addWidget(lan_feedback_button)
        content_layout.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)
        return page

    def _build_about_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("aboutPage")
        page.setStyleSheet(
            """
            QWidget#aboutPage {
                background: #0D1B2D;
                color: #E7EEF8;
            }
            QWidget#aboutContent {
                background: transparent;
            }
            QLabel#aboutTitle {
                color: #F8FAFC;
                font-size: 24px;
                font-weight: 800;
            }
            QLabel#aboutBrandTitle {
                color: #F8FAFC;
                font-size: 28px;
                font-weight: 850;
            }
            QLabel#aboutBrandSubtitle, QLabel#aboutBodyText {
                color: #CBD5E1;
                font-size: 13px;
            }
            QLabel#aboutMutedText {
                color: #8EA0B8;
                font-size: 12px;
            }
            QFrame#aboutHeroPanel, QFrame#aboutInfoCard {
                background: #142238;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 10px;
            }
            QLabel#aboutAppIcon {
                background: transparent;
                border: 0;
            }
            """
        )
        root = QVBoxLayout(page)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(16)
        title = QLabel("About / 关于")
        title.setObjectName("aboutTitle")
        root.addWidget(title)

        hero = QFrame()
        hero.setObjectName("aboutHeroPanel")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(20, 18, 20, 18)
        hero_layout.setSpacing(16)

        icon_label = QLabel()
        icon_label.setObjectName("aboutAppIcon")
        icon_label.setFixedSize(64, 64)
        icon = load_app_icon()
        if not icon.isNull():
            icon_label.setPixmap(icon.pixmap(58, 58))
        hero_layout.addWidget(icon_label, alignment=Qt.AlignTop)

        brand = QVBoxLayout()
        brand.setSpacing(6)
        brand_title = QLabel("萤火虫 / Firefly")
        brand_title.setObjectName("aboutBrandTitle")
        brand_subtitle = QLabel("BioMedPilot / 医研智析")
        brand_subtitle.setObjectName("aboutBrandSubtitle")
        version = QLabel("0.1.0-internal-beta · Developer Preview · Local desktop workspace")
        version.setObjectName("aboutMutedText")
        brand.addWidget(brand_title)
        brand.addWidget(brand_subtitle)
        brand.addWidget(version)
        hero_layout.addLayout(brand, 1)
        root.addWidget(hero)

        cards = QWidget()
        cards.setObjectName("aboutContent")
        cards_layout = QGridLayout(cards)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setHorizontalSpacing(14)
        cards_layout.setVerticalSpacing(14)
        cards_layout.addWidget(
            self._about_info_card(
                "产品入口",
                [
                    "欢迎页进入本地工作台。",
                    "主模块保留 Bioinformatics、Meta Analysis、LabTools。",
                    "设置、测试反馈与关于页属于统一壳层。",
                ],
            ),
            0,
            0,
        )
        cards_layout.addWidget(
            self._about_info_card(
                "本地边界",
                [
                    "当前版本不包含正式账号、订阅或授权流程。",
                    "测试反馈保存到本机项目目录。",
                    "不会因打开 About 页面触发网络请求。",
                ],
            ),
            0,
            1,
        )
        cards_layout.addWidget(
            self._about_info_card(
                "阶段状态",
                [
                    "桌面壳层为 Developer Preview。",
                    "分析能力按各自模块页面状态呈现。",
                    "图标与资源状态可在 Settings 查看。",
                ],
            ),
            1,
            0,
        )
        summary = icon_asset_summary()
        cards_layout.addWidget(
            self._about_info_card(
                "图标资源状态",
                [
                    f"图标槽位：{summary['total']}",
                    f"已生成：{summary['generated']}",
                    f"已接入：{summary['connected']}",
                    f"待生成：{summary['pending']}",
                ],
            ),
            1,
            1,
        )
        root.addWidget(cards)
        root.addStretch(1)
        return page

    def _about_info_card(self, title: str, rows: list[str]) -> QFrame:
        card = QFrame()
        card.setObjectName("aboutInfoCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        header = QLabel(title)
        header.setObjectName("aboutBrandSubtitle")
        header.setStyleSheet("font-weight: 750;")
        layout.addWidget(header)
        for row in rows:
            label = QLabel(row)
            label.setObjectName("aboutBodyText")
            label.setWordWrap(True)
            layout.addWidget(label)
        layout.addStretch(1)
        return card

    def _create_project_and_open(self, project_type: str) -> None:
        default_name = "生信分析项目" if project_type == "bioinformatics" else "Meta 分析项目"
        project_name, accepted = QInputDialog.getText(self, "新建项目", "项目名称：", text=default_name)
        if not accepted or not project_name.strip():
            return
        record = self._project_center.create_project(
            project_name=project_name.strip(),
            project_type=project_type,  # type: ignore[arg-type]
        )
        self.open_project_record(record)

    def generate_testing_feedback_template(self) -> None:
        path = generate_feedback_template()
        self.statusBar().showMessage(f"已生成反馈模板：{path}", 8000)

    def generate_lan_testing_feedback_template(self) -> None:
        path = generate_lan_feedback_template()
        self.statusBar().showMessage(f"已生成 LAN 真实测试反馈报告：{path}", 8000)


def _labtools_local_write_result_text(result: labtools_runtime.LabToolsLocalWriteResult) -> str:
    if result.success:
        version = f" v{result.new_version}" if result.new_version is not None else ""
        return f"{result.message} {result.entity_id}{version}".strip()
    blocker = f" blocker={result.blocker}" if result.blocker else ""
    return f"{result.message}{blocker}"


def _user_facing_labtools_status(status: str) -> str:
    return {
        "ready": "可读取",
        "available": "可读取",
        "blocked": "未连接",
        "missing_project_context": "未连接本地试剂库",
        "adapter_needed": "需适配",
        "disabled": "暂不可用",
    }.get(status, status.replace("_", " "))


def _user_facing_reagent_note(text: str) -> str:
    replacements = {
        "UI-C2d in-memory demo template; not stored and not linked to inventory.": "示例模板，仅用于配制流程预览；当前不保存到本地模板库，也不关联库存。",
        "保存模板需要 BioMedPilotLabToolsStorageAdapter.": "模板保存需存储适配器，当前暂不可直接保存到本地。",
        "保存模板需要 BioMedPilotLabToolsStorageAdapter。": "模板保存需存储适配器，当前暂不可直接保存到本地。",
        "BioMedPilot project context is required before LabTools local_data can be read.": "连接 BioMedPilot 项目后可读取本地试剂库；当前不在主流程中管理库存。",
        "保存模板和配制记录需要存储适配；当前不会写入 ~/.labtools。": "保存模板和配制记录需要存储适配；当前不会写入个人目录。",
        "Validation summary": "验证与提示",
    }
    value = replacements.get(text, text)
    value = value.replace("BioMedPilotLabToolsStorageAdapter", "存储适配器")
    value = value.replace("~/.labtools", "个人目录")
    value = value.replace("project_storage", "BioMedPilot 存储")
    return value
