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
from app.shared.testing_mode import generate_feedback_template, testing_mode_summary
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
        shell_layout.addWidget(
            SidebarWidget(
                on_dashboard=self.show_dashboard,
                on_bioinformatics=self.show_bioinformatics,
                on_meta_analysis=self.show_meta_analysis,
                on_labtools=self.show_labtools,
                on_settings=self.show_settings,
                on_test_feedback=self.show_test_feedback,
                on_about=self.show_about,
            )
        )
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
        self.setWindowTitle(APP_NAME)

    def show_bioinformatics(self) -> None:
        self._stack.setCurrentWidget(self._bioinformatics_page)
        self.setWindowTitle("BioMedPilot / 生信分析")

    def show_meta_analysis(self) -> None:
        self._stack.setCurrentWidget(self._meta_analysis_page)
        self.setWindowTitle("BioMedPilot / Meta 分析")

    def show_labtools(self) -> None:
        self._stack.setCurrentWidget(self._labtools_page)
        self.setWindowTitle("BioMedPilot / LabTools")

    def show_settings(self) -> None:
        self._stack.setCurrentWidget(self._settings_page)
        self.setWindowTitle("BioMedPilot / 设置中心")

    def show_test_feedback(self) -> None:
        self._stack.setCurrentWidget(self._testing_page)
        self.setWindowTitle("BioMedPilot / Test Feedback")

    def show_testing_mode(self) -> None:
        self.show_test_feedback()

    def show_about(self) -> None:
        self._stack.setCurrentWidget(self._about_page)
        self.setWindowTitle("BioMedPilot / About")

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
        title_label.setStyleSheet("font-size: 24px; font-weight: 700;")
        root.addWidget(title_label)
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("labtoolsShellSubtitle")
        subtitle_label.setWordWrap(True)
        root.addWidget(subtitle_label)
        root.addWidget(make_status_chip("Developer Preview / 本地测试版", status_key="developer_preview"))
        return content

    def _build_labtools_home_content(self) -> QWidget:
        content = self._build_labtools_base_content(
            page_key="home",
            semantic_key=PageKey.LABTOOLS_HOME.value,
            title="LabTools / 实验工具",
            subtitle="通用计算、试剂配制与实验流程工具集合，为生物医学实验提供可靠的计算与规划支持。",
        )
        root = content.layout()
        root.addWidget(self._labtools_local_data_status_panel(page_key="home", semantic_key=PageKey.LABTOOLS_HOME.value))
        root.addWidget(self._labtools_lan_host_management_panel(page_key="home", semantic_key=PageKey.LABTOOLS_HOME.value))
        root.addWidget(self._labtools_lan_manual_connection_panel(page_key="home", semantic_key=PageKey.LABTOOLS_HOME.value))

        entry_row = QHBoxLayout()
        entry_row.setSpacing(14)
        entry_row.addWidget(
            self._labtools_primary_entry_card(
                title="通用计算器",
                page_key="general_calculators",
                semantic_key=PageKey.LABTOOLS_GENERAL_CALCULATORS.value,
                status_key="shell_only",
                rows=[
                    "稀释计算",
                    "加样计算",
                    "分子量 / 摩尔量换算",
                    "单位换算",
                    "更多通用计算入口（规划中）",
                ],
                callback=self._show_labtools_general_calculator_shell,
            )
        )
        entry_row.addWidget(
            self._labtools_primary_entry_card(
                title="试剂制备",
                page_key="reagent_preparation",
                semantic_key=PageKey.LABTOOLS_REAGENT_PREPARATION.value,
                status_key="planned",
                rows=[
                    "溶液配制",
                    "稀释系列",
                    "缓冲液配方",
                    "配制复核提示",
                    "记录保存需适配",
                    "更多配制工具",
                ],
                callback=self._show_labtools_reagent_preparation_shell,
            )
        )
        entry_row.addWidget(
            self._labtools_primary_entry_card(
                title="实验模块",
                page_key="experiment_modules",
                semantic_key=PageKey.LABTOOLS_EXPERIMENT_MODULES.value,
                status_key="testing",
                rows=[
                    "包含以下实验模块：",
                    "细胞实验、蛋白实验、核酸实验、免疫与吸光度实验、免疫组化。",
                    "提供实验模块入口与计算辅助。",
                ],
                callback=self._show_labtools_experiment_modules_shell,
            )
        )
        root.addLayout(entry_row)
        root.addWidget(
            self._labtools_notice_card(
                "实验计算结果需由用户复核后用于台面操作。",
                object_name="labtoolsReviewNotice",
                semantic_key=PageKey.LABTOOLS_HOME.value,
            )
        )
        root.addWidget(
            self._quick_access_card(
                module_key=ModuleKey.LABTOOLS.value,
                object_name="labtoolsQuickAccessCard",
                items=("使用指南", "常见问题", "意见反馈", "最近使用"),
            )
        )
        root.addStretch(1)
        return content

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

    def _connect_labtools_lan_readonly(self) -> None:
        url_input = getattr(self, "_labtools_lan_url_input", None)
        status_label = getattr(self, "_labtools_lan_status_label", None)
        count_label = getattr(self, "_labtools_lan_count_label", None)
        if not isinstance(url_input, QLineEdit) or not isinstance(status_label, QLabel) or not isinstance(count_label, QLabel):
            return
        model = labtools_runtime.get_labtools_lan_read_model(url_input.text())
        self._labtools_lan_read_model = model
        status_label.setText(f"LAN：{model.status.status} · {model.status.reason}")
        status_label.setProperty("status", model.status.status)
        status_label.setProperty("dataSourceMode", model.status.data_source_mode)
        count_label.setText(
            f"reagent {model.status.reagent_count} · sample {model.status.sample_count} · "
            f"cell {model.status.cell_count} · freeze vial {model.status.freeze_vial_count} · record {model.status.record_count}"
        )
        count_label.setProperty("reagentCount", model.status.reagent_count)
        count_label.setProperty("sampleCount", model.status.sample_count)
        count_label.setProperty("cellCount", model.status.cell_count)
        count_label.setProperty("recordCount", model.status.record_count)

    def _show_labtools_general_calculator_shell(self) -> None:
        status = labtools_runtime.runtime_status()
        self._labtools_result_widgets: dict[str, dict[str, object]] = {}
        content = self._build_labtools_base_content(
            page_key="general_calculators",
            semantic_key=PageKey.LABTOOLS_GENERAL_CALCULATORS.value,
            title="通用计算器 / General Calculator",
            subtitle="Quick Calculator 与 Dynamic Formula Solver 已接入后端计算/公式求解；保存历史与文件导出仍保持禁用。",
        )
        root = content.layout()
        nav = QHBoxLayout()
        back = make_button("返回 LabTools 首页", role="secondary")
        back.setObjectName("labtoolsBackButton")
        back.clicked.connect(self._show_labtools_home)
        nav.addWidget(back)
        nav.addWidget(make_status_chip("backend_ready / ui_adapter_needed" if status.available else "backend unavailable", status_key="testing" if status.available else "blocked"))
        nav.addStretch(1)
        root.addLayout(nav)
        if not status.available:
            root.addWidget(self._labtools_notice_card(status.message, object_name="labtoolsAdapterNotice", semantic_key=PageKey.LABTOOLS_GENERAL_CALCULATORS.value))
            root.addStretch(1)
            self._set_labtools_content(content)
            return

        mode_row = QHBoxLayout()
        quick_button = make_button("快速计算", role="primary")
        quick_button.setObjectName("labtoolsGeneralModeButton")
        quick_button.setProperty("modeKey", "quick_calculator")
        formula_button = make_button("动态公式求解", role="secondary")
        formula_button.setObjectName("labtoolsGeneralModeButton")
        formula_button.setProperty("modeKey", "formula_solver")
        mode_row.addWidget(quick_button)
        mode_row.addWidget(formula_button)
        mode_row.addStretch(1)
        root.addLayout(mode_row)

        self._labtools_general_stack = QStackedWidget()
        self._labtools_general_stack.setObjectName("labtoolsGeneralCalculatorStack")
        quick_page = self._build_labtools_quick_calculator_page()
        formula_page = self._build_labtools_formula_solver_page()
        self._labtools_general_stack.addWidget(quick_page)
        self._labtools_general_stack.addWidget(formula_page)
        quick_button.clicked.connect(lambda: self._labtools_general_stack.setCurrentWidget(quick_page))
        formula_button.clicked.connect(lambda: self._labtools_general_stack.setCurrentWidget(formula_page))
        root.addWidget(self._labtools_general_stack)
        root.addStretch(1)
        self._set_labtools_content(content)

    def _build_labtools_quick_calculator_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("labtoolsQuickCalculatorPage")
        page.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        page.setProperty("pageKey", "quick_calculator")
        page.setProperty("semanticKey", "labtools.page.quick_calculator")
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        selector_card = QFrame()
        selector_card.setObjectName("labtoolsCalculatorSelectorCard")
        selector_card.setStyleSheet("QFrame#labtoolsCalculatorSelectorCard { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        selector_layout = QVBoxLayout(selector_card)
        selector_layout.setContentsMargins(16, 14, 16, 14)
        selector_layout.addWidget(QLabel("Quick Calculator 任务"))
        self._labtools_quick_task_combo = QComboBox()
        self._labtools_quick_task_combo.setObjectName("labtoolsQuickTaskCombo")
        self._labtools_quick_task_combo.setProperty("pageKey", "quick_calculator")
        for task in labtools_runtime.list_quick_tasks():
            label = f"{task.title} · {task.category}"
            self._labtools_quick_task_combo.addItem(label, task.task_id)
        selector_layout.addWidget(self._labtools_quick_task_combo)
        description = QLabel()
        description.setObjectName("labtoolsQuickTaskDescription")
        description.setWordWrap(True)
        selector_layout.addWidget(description)
        selector_layout.addWidget(make_status_chip("backend_ready / ui_adapter_needed", status_key="testing"))
        selector_layout.addStretch(1)
        layout.addWidget(selector_card, 1)

        form_card = QFrame()
        form_card.setObjectName("labtoolsCalculatorFormCard")
        form_card.setStyleSheet("QFrame#labtoolsCalculatorFormCard { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(16, 14, 16, 14)
        form_layout.setSpacing(10)
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
        layout.setSpacing(14)

        selector_card = QFrame()
        selector_card.setObjectName("labtoolsFormulaSelectorCard")
        selector_card.setStyleSheet("QFrame#labtoolsFormulaSelectorCard { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        selector_layout = QVBoxLayout(selector_card)
        selector_layout.setContentsMargins(16, 14, 16, 14)
        selector_layout.addWidget(QLabel("Dynamic Formula Solver"))
        self._labtools_formula_combo = QComboBox()
        self._labtools_formula_combo.setObjectName("labtoolsFormulaSpecCombo")
        for spec in labtools_runtime.list_formula_specs():
            self._labtools_formula_combo.addItem(spec.short_title, spec.spec_id)
        selector_layout.addWidget(self._labtools_formula_combo)
        self._labtools_formula_description = QLabel()
        self._labtools_formula_description.setObjectName("labtoolsFormulaDescription")
        self._labtools_formula_description.setWordWrap(True)
        selector_layout.addWidget(self._labtools_formula_description)
        self._labtools_formula_expression = QLabel()
        self._labtools_formula_expression.setObjectName("labtoolsFormulaExpression")
        self._labtools_formula_expression.setWordWrap(True)
        selector_layout.addWidget(self._labtools_formula_expression)
        selector_layout.addStretch(1)
        layout.addWidget(selector_card, 1)

        form_card = QFrame()
        form_card.setObjectName("labtoolsFormulaFormCard")
        form_card.setStyleSheet("QFrame#labtoolsFormulaFormCard { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(16, 14, 16, 14)
        form_layout.setSpacing(10)
        self._labtools_formula_form_layout = form_layout
        layout.addWidget(form_card, 2)

        result_card = self._labtools_result_panel(page_key="formula_solver", semantic_key="labtools.page.formula_solver")
        layout.addWidget(result_card, 2)

        self._labtools_formula_combo.currentIndexChanged.connect(lambda _index: self._populate_labtools_formula_form())
        self._populate_labtools_formula_form()
        return page

    def _populate_labtools_quick_form(self, description_label: QLabel) -> None:
        task_id = self._labtools_quick_task_combo.currentData()
        task = labtools_runtime.get_quick_task(task_id)
        description_label.setText(task.description + (" 细胞铺板仅计算辅助，不进入细胞记录保存。" if task.task_id == "quick_cell_seeding" else ""))
        self._clear_layout(self._labtools_quick_form_layout)
        self._labtools_quick_inputs: dict[str, QLineEdit] = {}
        self._labtools_quick_units: dict[str, QComboBox] = {}
        header = QLabel(task.title)
        header.setObjectName("labtoolsQuickFormTitle")
        header.setStyleSheet("font-weight: 700;")
        self._labtools_quick_form_layout.addWidget(header)
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
        target_label.setStyleSheet("font-weight: 700;")
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
        label_widget = QLabel(label)
        label_widget.setObjectName(f"{object_prefix}InputLabel")
        label_widget.setProperty("fieldId", field_id)
        row.addWidget(label_widget)
        field = QLineEdit(default_value)
        field.setObjectName(f"{object_prefix}Input")
        field.setProperty("fieldId", field_id)
        field.setPlaceholderText(placeholder)
        field.setEnabled(not disabled)
        input_store[field_id] = field
        row.addWidget(field, 1)
        if units:
            combo = QComboBox()
            combo.setObjectName(f"{object_prefix}UnitSelector")
            combo.setProperty("fieldId", field_id)
            combo.addItems(list(units))
            if selected_unit:
                index = combo.findText(selected_unit)
                if index >= 0:
                    combo.setCurrentIndex(index)
            unit_store[field_id] = combo
            row.addWidget(combo)
        return row

    def _labtools_result_panel(self, *, page_key: str, semantic_key: str) -> QFrame:
        frame = make_workbench_card(object_name="labtoolsResultPanel", semantic_state="draft")
        frame.setObjectName("labtoolsResultPanel")
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("pageKey", page_key)
        frame.setProperty("semanticKey", semantic_key)
        frame.setProperty("uiPrimitive", "result_panel")
        frame.setProperty("formalResult", False)
        frame.setProperty("reportGenerationAllowed", False)
        frame.setProperty("exportAllowed", False)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        layout.addWidget(make_section_title("结果预览", "Draft calculation output; not a formal report."))
        layout.addWidget(make_status_chip(status_key="draft", semantic_state="draft"))
        result_primary = QLabel("暂无结果")
        result_primary.setObjectName("labtoolsResultPrimary")
        result_primary.setProperty("pageKey", page_key)
        result_primary.setWordWrap(True)
        layout.addWidget(result_primary)
        result_text = QPlainTextEdit()
        result_text.setObjectName("labtoolsResultText")
        result_text.setProperty("pageKey", page_key)
        result_text.setReadOnly(True)
        result_text.setMinimumHeight(180)
        layout.addWidget(result_text)
        issue_label = QLabel(labtools_runtime.REVIEW_NOTICE)
        issue_label.setObjectName("labtoolsIssueRows")
        issue_label.setProperty("pageKey", page_key)
        issue_label.setWordWrap(True)
        layout.addWidget(issue_label)
        actions = QHBoxLayout()
        copy_button = make_button("复制结果", role="secondary")
        copy_button.setObjectName("labtoolsCopyResultButton")
        copy_button.setProperty("pageKey", page_key)
        copy_button.clicked.connect(lambda _checked=False, key=page_key: self._copy_labtools_result(key))
        save_button = make_button("保存本地记录摘要", role="secondary")
        save_button.setObjectName("labtoolsSaveHistoryButton")
        save_button.setProperty("pageKey", page_key)
        save_button.clicked.connect(lambda _checked=False, key=page_key: self._save_labtools_calculation_record(key))
        self._set_storage_gated_button_state(save_button, bool(self._labtools_project_root), "disabled_missing_storage_adapter")
        export_button = make_button("导出结果 - 暂未开放", role="secondary")
        export_button.setObjectName("labtoolsExportResultButton")
        export_button.setProperty("pageKey", page_key)
        export_button.setEnabled(False)
        export_button.setProperty("disabledState", "future")
        actions.addWidget(copy_button)
        actions.addWidget(save_button)
        actions.addWidget(export_button)
        actions.addStretch(1)
        layout.addLayout(actions)
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
        content = self._build_labtools_base_content(
            page_key="reagent_preparation",
            semantic_key=semantic_key,
            title="试剂制备 / Reagent Preparation",
            subtitle="展示试剂模板、模板详情和本次配制计算预览；保存历史仅在 BioMedPilot project storage 试点中启用，文件导出继续禁用。",
        )
        root = content.layout()
        nav = QHBoxLayout()
        back = make_button("返回 LabTools 首页", role="secondary")
        back.setObjectName("labtoolsBackButton")
        back.clicked.connect(self._show_labtools_home)
        nav.addWidget(back)
        nav.addWidget(make_status_chip("backend_ready / storage_adapter_needed", status_key="testing"))
        nav.addWidget(make_status_chip("storage_adapter_needed", status_key="planned"))
        nav.addStretch(1)
        root.addLayout(nav)
        root.addWidget(
            self._labtools_notice_card(
                "桌面 UI 不默认写入 ~/.labtools；保存试点仅写入 BioMedPilot project_storage/labtools/，文件导出仍等待 FilePickerExportAdapter。",
                object_name="labtoolsAdapterNotice",
                semantic_key=semantic_key,
            )
        )

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
        left_column.setMinimumWidth(280)
        left_column.setMaximumWidth(380)
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)
        left_layout.addWidget(self._labtools_reagent_template_list_panel(templates))
        left_layout.addWidget(self._labtools_local_reagent_list_panel(self._labtools_local_data_read_model))
        run_panel = self._labtools_reagent_run_panel()
        run_panel.setMinimumWidth(500)
        detail_panel = self._labtools_reagent_detail_panel()
        detail_panel.setMinimumWidth(280)
        detail_panel.setMaximumWidth(380)
        root.addWidget(
            make_left_list_middle_form_right_preview(
                list_widget=left_column,
                form_widget=run_panel,
                preview_widget=detail_panel,
                object_name="labtoolsReagentWorkbenchColumns",
                sizes=(320, 620, 320),
            )
        )
        root.addWidget(self._labtools_reagent_history_panel())
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
        frame.setStyleSheet("QFrame#labtoolsReagentTemplateListPanel { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        header = QLabel("试剂模板列表")
        header.setStyleSheet("font-weight: 700;")
        layout.addWidget(header)
        search = QLineEdit()
        search.setObjectName("labtoolsReagentSearchInput")
        search.setPlaceholderText("搜索模板（当前为本地示例过滤占位）")
        layout.addWidget(search)
        if not templates:
            layout.addWidget(make_empty_state("暂无模板", "未接入存储适配前不读取真实模板库。", empty_state_key="empty_project", semantic_key=PageKey.LABTOOLS_REAGENT_PREPARATION.value))
        for template in templates:
            row = QPushButton(f"{template.name}\n{template.category} · {template.default_volume} · {template.component_count} 组分")
            row.setObjectName("labtoolsReagentTemplateRow")
            row.setProperty("templateId", template.template_id)
            row.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
            row.setProperty("pageKey", "reagent_preparation")
            row.setProperty("semanticKey", PageKey.LABTOOLS_REAGENT_PREPARATION.value)
            row.clicked.connect(lambda _checked=False, item=template.template_id: self._select_labtools_reagent_template(item))
            layout.addWidget(row)
            status = make_status_chip(template.status_label, status_key="planned")
            status.setProperty("templateId", template.template_id)
            layout.addWidget(status)
        layout.addWidget(
            self._labtools_notice_card(
                "默认展示示例模板；如已启用项目存储试点则优先读取 project_storage/labtools/templates。仍不连接库存系统、批次放行或协作能力。",
                object_name="labtoolsAdapterNotice",
                semantic_key=PageKey.LABTOOLS_REAGENT_PREPARATION.value,
            )
        )
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
        header = QLabel("本地试剂引用")
        header.setStyleSheet("font-weight: 700;")
        layout.addWidget(header)
        status = QLabel(f"local_data: {model.status.status}")
        status.setObjectName("labtoolsLocalReagentStatus")
        status.setProperty("status", model.status.status)
        status.setWordWrap(True)
        layout.addWidget(status)
        if not model.reagents:
            layout.addWidget(
                make_empty_state(
                    "暂无本地试剂",
                    model.status.reason,
                    empty_state_key="empty_project",
                    semantic_key=PageKey.LABTOOLS_REAGENT_PREPARATION.value,
                )
            )
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
        form_header = QLabel("本地试剂管理")
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
        write_status = QLabel(_labtools_local_write_result_text(result) if result is not None else "本地保存，不会同步到其他设备。")
        write_status.setObjectName("labtoolsLocalReagentWriteStatus")
        write_status.setProperty("status", result.status if result is not None else "idle")
        write_status.setWordWrap(True)
        layout.addWidget(write_status)
        self._labtools_local_reagent_write_status = write_status
        layout.addWidget(
            self._labtools_notice_card(
                "本阶段只引用本地试剂信息；不会扣减库存，也不会覆盖 reagent template。",
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
        frame.setStyleSheet("QFrame#labtoolsReagentRunPanel { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        header = QLabel("本次配制计算预览")
        header.setStyleSheet("font-weight: 700;")
        layout.addWidget(header)
        self._labtools_reagent_run_inputs: dict[str, QLineEdit] = {}
        self._labtools_reagent_target_unit = QComboBox()
        self._labtools_reagent_target_unit.setObjectName("labtoolsReagentTargetVolumeUnit")
        self._labtools_reagent_target_unit.addItems(["mL", "µL", "L"])
        layout.addLayout(self._labtools_reagent_input_row("目标体积", "target_volume", "500", unit_widget=self._labtools_reagent_target_unit))
        layout.addLayout(self._labtools_reagent_input_row("操作者", "operator_name", "Researcher"))
        layout.addLayout(self._labtools_reagent_input_row("实测 pH", "measured_ph", "7.4"))
        layout.addLayout(self._labtools_reagent_input_row("pH 调整说明", "adjustment_note", "按 SOP 微调并人工记录"))
        calculate = make_button("重新计算预览", role="primary")
        calculate.setObjectName("labtoolsReagentCalculateButton")
        calculate.clicked.connect(self._run_labtools_reagent_preparation)
        layout.addWidget(calculate)
        self._labtools_reagent_result_primary = QLabel("请选择模板并计算。")
        self._labtools_reagent_result_primary.setObjectName("labtoolsReagentResultPrimary")
        self._labtools_reagent_result_primary.setWordWrap(True)
        layout.addWidget(self._labtools_reagent_result_primary)
        self._labtools_reagent_result_rows = QVBoxLayout()
        result_rows_frame = QFrame()
        result_rows_frame.setObjectName("labtoolsReagentResultTable")
        result_rows_frame.setStyleSheet("QFrame#labtoolsReagentResultTable { border: 1px solid #E5E7EB; border-radius: 8px; background: #F8FAFC; }")
        result_rows_frame.setLayout(self._labtools_reagent_result_rows)
        layout.addWidget(result_rows_frame)
        self._labtools_reagent_result_text = QPlainTextEdit()
        self._labtools_reagent_result_text.setObjectName("labtoolsReagentResultText")
        self._labtools_reagent_result_text.setReadOnly(True)
        self._labtools_reagent_result_text.setMinimumHeight(140)
        layout.addWidget(self._labtools_reagent_result_text)
        self._labtools_reagent_issue_rows = QLabel(labtools_runtime.REVIEW_NOTICE)
        self._labtools_reagent_issue_rows.setObjectName("labtoolsReagentIssueRows")
        self._labtools_reagent_issue_rows.setWordWrap(True)
        layout.addWidget(self._labtools_reagent_issue_rows)
        actions = QHBoxLayout()
        copy = make_button("复制摘要", role="secondary")
        copy.setObjectName("labtoolsReagentCopySummaryButton")
        copy.clicked.connect(self._copy_labtools_reagent_summary)
        save = make_button("保存本地记录摘要", role="secondary")
        save.setObjectName("labtoolsReagentSaveRecordButton")
        save.clicked.connect(self._save_labtools_reagent_record)
        export = make_button("PDF / DOCX 导出 - 未开放", role="secondary")
        export.setObjectName("labtoolsReagentExportButton")
        export.setEnabled(False)
        export.setProperty("disabledState", "future")
        export_md = make_button("导出 Markdown", role="secondary")
        export_md.setObjectName("labtoolsReagentExportMarkdownButton")
        export_md.setProperty("exportRequiresFilePicker", True)
        export_md.setProperty("exportFormat", "markdown")
        export_md.clicked.connect(self._export_labtools_reagent_markdown)
        export_csv = make_button("导出 CSV", role="secondary")
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
        self._labtools_local_reagent_reference = QLabel("未引用本地试剂。")
        self._labtools_local_reagent_reference.setObjectName("labtoolsLocalReagentReference")
        self._labtools_local_reagent_reference.setWordWrap(True)
        layout.addWidget(self._labtools_local_reagent_reference)
        self._set_storage_gated_button_state(save, bool(self._labtools_project_root), "disabled_missing_storage_adapter")
        return frame

    def _labtools_reagent_detail_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("labtoolsReagentDetailPanel")
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("pageKey", "reagent_preparation")
        frame.setProperty("semanticKey", PageKey.LABTOOLS_REAGENT_PREPARATION.value)
        frame.setStyleSheet("QFrame#labtoolsReagentDetailPanel { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        header = QLabel("模板详情 / 编辑侧栏")
        header.setStyleSheet("font-weight: 700;")
        layout.addWidget(header)
        dirty = make_status_chip("已修改未保存 / storage_adapter_needed", status_key="planned")
        dirty.setObjectName("labtoolsReagentDirtyState")
        layout.addWidget(dirty)
        detail_body = QFrame()
        detail_body.setObjectName("labtoolsReagentDetailBody")
        detail_body_layout = QVBoxLayout(detail_body)
        detail_body_layout.setContentsMargins(0, 0, 0, 0)
        detail_body_layout.setSpacing(8)
        self._labtools_reagent_detail_rows_layout = detail_body_layout
        layout.addWidget(detail_body)
        save = make_button("保存模板 - 项目存储试点", role="secondary")
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
        frame.setStyleSheet("QFrame#labtoolsReagentHistoryPanel { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        header = QLabel("项目存储历史记录 / History Preview")
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
        title = QLabel(label)
        title.setObjectName("labtoolsReagentInputLabel")
        title.setProperty("fieldId", field_id)
        row.addWidget(title)
        field = QLineEdit(default_value)
        field.setObjectName("labtoolsReagentInput")
        field.setProperty("fieldId", field_id)
        self._labtools_reagent_run_inputs[field_id] = field
        row.addWidget(field, 1)
        if unit_widget is not None:
            unit_widget.setProperty("fieldId", field_id)
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
            f"说明：{detail.notes}",
        ]
        for text in rows:
            label = QLabel(text)
            label.setObjectName("labtoolsReagentDetailRow")
            label.setWordWrap(True)
            layout.addWidget(label)
        component_header = QLabel("组分与 validation")
        component_header.setObjectName("labtoolsReagentComponentHeader")
        component_header.setStyleSheet("font-weight: 700;")
        layout.addWidget(component_header)
        for component in detail.components:
            label = QLabel(f"{component.stage} · {component.name} · {component.amount} · {component.notes or component.warning or '需人工复核'}")
            label.setObjectName("labtoolsReagentComponentRow")
            label.setWordWrap(True)
            layout.addWidget(label)
        validation_header = QLabel("Validation summary")
        validation_header.setStyleSheet("font-weight: 700;")
        layout.addWidget(validation_header)
        for row in detail.validation_rows:
            label = QLabel(row)
            label.setObjectName("labtoolsReagentValidationRow")
            label.setWordWrap(True)
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
            row = QLabel(f"{component.stage} | {component.name} | {component.amount} | {component.notes or component.warning or 'OK'}")
            row.setObjectName("labtoolsReagentResultRow")
            row.setWordWrap(True)
            self._labtools_reagent_result_rows.addWidget(row)
        if not result.component_rows:
            row = QLabel("未生成组分预览。")
            row.setObjectName("labtoolsReagentResultRow")
            self._labtools_reagent_result_rows.addWidget(row)
        issues = list(result.errors) + list(result.warnings)
        self._labtools_reagent_issue_rows.setText("\n".join(f"- {issue}" for issue in issues))
        self._labtools_reagent_issue_rows.setProperty("hasError", bool(result.errors))
        self._labtools_reagent_copy_text = result.copy_text if result.valid else ""
        if self._labtools_project_root:
            self._labtools_reagent_issue_rows.setText(
                f"{self._labtools_reagent_issue_rows.text()}\n- 保存试点路径：project_storage/labtools/"
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
            self._labtools_reagent_history_status.setText("暂无本地配制记录摘要；保存后会写入 local_data record index。")
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
        content = self._build_labtools_base_content(
            page_key="wb_loading",
            semantic_key=semantic_key,
            title="蛋白实验 / Protein Experiment",
            subtitle="当前仅展示 WB 上样计算；后续蛋白实验步骤为流程占位。",
        )
        root = content.layout()
        nav = QHBoxLayout()
        back = make_button("返回实验模块", role="secondary")
        back.setObjectName("labtoolsBackButton")
        back.clicked.connect(self._show_labtools_experiment_modules_shell)
        nav.addWidget(back)
        nav.addWidget(make_status_chip("backend_ready / WB loading", status_key="testing"))
        nav.addWidget(make_status_chip("save/export adapter needed", status_key="planned"))
        nav.addStretch(1)
        root.addLayout(nav)
        root.addLayout(self._labtools_wb_substep_bar())
        self._labtools_local_data_read_model = labtools_runtime.get_labtools_local_data_read_model(self._labtools_project_root)
        self._labtools_selected_local_sample_id = ""
        self._labtools_selected_local_sample_version = 0

        left_column = QWidget()
        left_column.setObjectName("labtoolsWbLeftColumn")
        left_column.setProperty("uiPrimitive", "workbench_secondary_column")
        left_column.setProperty("layoutPolishNoOverlap", True)
        left_column.setMinimumWidth(280)
        left_column.setMaximumWidth(360)
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)
        left_layout.addWidget(self._labtools_wb_config_panel())
        left_layout.addWidget(self._labtools_local_wb_sample_panel(self._labtools_local_data_read_model))
        results_panel = self._labtools_wb_results_panel()
        results_panel.setMinimumWidth(460)
        lane_panel = self._labtools_wb_lane_panel()
        lane_panel.setMinimumWidth(440)
        root.addWidget(
            make_three_column_workbench(
                left_widget=left_column,
                middle_widget=results_panel,
                right_widget=lane_panel,
                object_name="labtoolsWbWorkbenchColumns",
                sizes=(320, 560, 340),
            )
        )

        boundary = self._labtools_notice_card(
            "边界：此页不提供 SDS-PAGE 配胶、图像分析、自动条带识别、抗体推荐或完整 WB 协议；泳道布局仅作为 layout helper，不代表真实凝胶图或伪凝胶条带。",
            object_name="labtoolsAdapterNotice",
            semantic_key=semantic_key,
        )
        root.addWidget(boundary)
        actions = QHBoxLayout()
        copy = make_button("复制上样表", role="primary")
        copy.setObjectName("labtoolsWbCopyTableButton")
        copy.clicked.connect(self._copy_labtools_wb_summary)
        save = make_button("保存本地记录摘要", role="secondary")
        save.setObjectName("labtoolsWbSaveRecordButton")
        save.clicked.connect(self._save_labtools_wb_record)
        export = make_button("PDF / DOCX 导出 - 未开放", role="secondary")
        export.setObjectName("labtoolsWbExportButton")
        export.setEnabled(False)
        export.setProperty("disabledState", "future")
        export_md = make_button("导出 Markdown", role="secondary")
        export_md.setObjectName("labtoolsWbExportMarkdownButton")
        export_md.setProperty("exportRequiresFilePicker", True)
        export_md.setProperty("exportFormat", "markdown")
        export_md.clicked.connect(self._export_labtools_wb_markdown)
        export_csv = make_button("导出 CSV", role="secondary")
        export_csv.setObjectName("labtoolsWbExportCsvButton")
        export_csv.setProperty("exportRequiresFilePicker", True)
        export_csv.setProperty("exportFormat", "csv")
        export_csv.clicked.connect(self._export_labtools_wb_csv)
        history = make_button("历史记录 - 项目存储试点", role="secondary")
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
        root.addLayout(actions)
        root.addWidget(self._labtools_wb_history_panel())
        root.addStretch(1)
        self._labtools_wb_save_record_button = save
        self._labtools_wb_history_button = history
        self._labtools_wb_last_result = None
        self._set_labtools_content(content)
        self._run_labtools_wb_loading()
        self._refresh_labtools_wb_history()

    def _labtools_wb_substep_bar(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(6)
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
            color = "#EAF2FF" if status_key == "testing" else "#FFFFFF"
            chip.setStyleSheet(f"QFrame#labtoolsWbSubstep {{ border: 1px solid #D8DEE9; border-radius: 8px; background: {color}; }}")
            layout = QVBoxLayout(chip)
            layout.setContentsMargins(10, 8, 10, 8)
            title_label = QLabel(f"{number}. {title}")
            title_label.setObjectName("labtoolsWbSubstepTitle")
            title_label.setProperty("stepNumber", number)
            title_label.setStyleSheet("font-weight: 700;" if status_key == "testing" else "")
            state_label = QLabel(state)
            state_label.setObjectName("labtoolsWbSubstepState")
            state_label.setProperty("stepNumber", number)
            state_label.setStyleSheet("font-size: 11px; color: #64748B;")
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
        frame.setStyleSheet("QFrame#labtoolsWbConfigPanel { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        header = QLabel("WB 配置")
        header.setStyleSheet("font-weight: 700;")
        layout.addWidget(header)
        self._labtools_wb_inputs: dict[str, QLineEdit] = {}
        layout.addLayout(self._labtools_wb_input_row("目标上样蛋白量（每孔）", "target_protein_ug", "20", "µg"))
        layout.addLayout(self._labtools_wb_input_row("Sample buffer 倍数", "loading_buffer_factor", "4", "x"))
        layout.addLayout(self._labtools_wb_input_row("最终上样体积", "final_volume_ul", "20", "µL"))
        layout.addLayout(self._labtools_wb_input_row("固定泳道数", "lane_count", "10", "lanes"))
        reducing = QLabel("还原剂：Yes（当前示例视为已包含于上样体系，不额外占体积）")
        reducing.setObjectName("labtoolsWbConfigRow")
        reducing.setWordWrap(True)
        layout.addWidget(reducing)
        calculate = make_button("重新计算 WB 上样", role="primary")
        calculate.setObjectName("labtoolsWbCalculateButton")
        calculate.clicked.connect(self._run_labtools_wb_loading)
        layout.addWidget(calculate)
        layout.addWidget(self._labtools_notice_card("计算基于输入的蛋白浓度与目标上样量；结果需人工复核后用于台面操作。", object_name="labtoolsAdapterNotice", semantic_key=PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value))
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
        frame = make_workbench_card(object_name="labtoolsWbSampleResultPanel", semantic_state="draft")
        frame.setObjectName("labtoolsWbSampleResultPanel")
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("pageKey", "wb_loading")
        frame.setProperty("semanticKey", PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value)
        frame.setProperty("uiPrimitive", "result_panel")
        frame.setProperty("formalResult", False)
        frame.setProperty("fakeGelOutput", False)
        frame.setProperty("reportGenerationAllowed", False)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        layout.addWidget(make_section_title("样本列表与上样计算结果", "Calculation preview; no gel image or formal report."))
        layout.addWidget(make_status_chip(status_key="testing", semantic_state="testing"))
        self._labtools_wb_sample_rows = QVBoxLayout()
        sample_frame = QFrame()
        sample_frame.setObjectName("labtoolsWbSampleTable")
        sample_frame.setStyleSheet("QFrame#labtoolsWbSampleTable { border: 1px solid #E5E7EB; border-radius: 8px; background: #F8FAFC; }")
        sample_frame.setLayout(self._labtools_wb_sample_rows)
        layout.addWidget(sample_frame)
        self._labtools_wb_result_rows = QVBoxLayout()
        result_frame = QFrame()
        result_frame.setObjectName("labtoolsWbResultTable")
        result_frame.setStyleSheet("QFrame#labtoolsWbResultTable { border: 1px solid #E5E7EB; border-radius: 8px; background: #F8FAFC; }")
        result_frame.setLayout(self._labtools_wb_result_rows)
        layout.addWidget(result_frame)
        self._labtools_wb_issue_rows = QLabel("上样计算结果需由实验人员复核后用于台面操作。")
        self._labtools_wb_issue_rows.setObjectName("labtoolsWbIssueRows")
        self._labtools_wb_issue_rows.setWordWrap(True)
        layout.addWidget(self._labtools_wb_issue_rows)
        self._labtools_wb_detail_text = QPlainTextEdit()
        self._labtools_wb_detail_text.setObjectName("labtoolsWbDetailText")
        self._labtools_wb_detail_text.setReadOnly(True)
        self._labtools_wb_detail_text.setMinimumHeight(120)
        layout.addWidget(self._labtools_wb_detail_text)
        return frame

    def _labtools_wb_lane_panel(self) -> QFrame:
        lane_frame = QFrame()
        lane_frame.setObjectName("labtoolsWbLaneGrid")
        lane_frame.setStyleSheet("QFrame#labtoolsWbLaneGrid { border: 1px solid #E5E7EB; border-radius: 8px; background: #F8FAFC; }")
        self._labtools_wb_lane_grid = QGridLayout()
        self._labtools_wb_lane_grid.setSpacing(8)
        lane_frame.setLayout(self._labtools_wb_lane_grid)
        frame = make_preview_card(
            title="泳道布局预览（示意图）",
            preview_widget=lane_frame,
            status_key="testing",
            semantic_state="testing",
            caption="Legend：Marker / Sample / Empty；预览不显示伪凝胶条带。",
            object_name="labtoolsWbLanePreviewPanel",
        )
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("pageKey", "wb_loading")
        frame.setProperty("semanticKey", PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value)
        frame.setProperty("fakeGelBands", False)
        frame.setProperty("imageAnalysisEnabled", False)
        layout = frame.layout()
        edit = make_button("编辑布局 - 仅预览", role="secondary")
        edit.setObjectName("labtoolsWbEditLayoutButton")
        edit.setEnabled(False)
        edit.setProperty("disabledState", "preview_only")
        if isinstance(layout, QVBoxLayout):
            layout.addWidget(edit)
        return frame

    def _labtools_wb_input_row(self, label: str, field_id: str, default_value: str, unit: str) -> QHBoxLayout:
        row = QHBoxLayout()
        title = QLabel(label)
        title.setObjectName("labtoolsWbInputLabel")
        title.setProperty("fieldId", field_id)
        field = QLineEdit(default_value)
        field.setObjectName("labtoolsWbInput")
        field.setProperty("fieldId", field_id)
        self._labtools_wb_inputs[field_id] = field
        unit_label = QLabel(unit)
        unit_label.setObjectName("labtoolsWbInputUnit")
        unit_label.setProperty("fieldId", field_id)
        row.addWidget(title)
        row.addWidget(field, 1)
        row.addWidget(unit_label)
        return row

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
        for sample in result.samples:
            label = QLabel(f"{sample.sample_id} | {sample.concentration} | {sample.note}")
            label.setObjectName("labtoolsWbSampleRow")
            label.setProperty("sampleId", sample.sample_id)
            self._labtools_wb_sample_rows.addWidget(label)
        self._clear_layout(self._labtools_wb_result_rows)
        for row_data in result.rows:
            row = QLabel(
                f"{row_data.sample_id} | sample {row_data.sample_volume} | 4x buffer {row_data.loading_buffer_volume} | "
                f"water {row_data.diluent_volume} | total {row_data.final_volume} | {row_data.status}"
            )
            row.setObjectName("labtoolsWbResultRow")
            row.setProperty("sampleId", row_data.sample_id)
            row.setProperty("status", row_data.status)
            row.setWordWrap(True)
            self._labtools_wb_result_rows.addWidget(row)
            for issue in row_data.issues:
                issue_label = QLabel(f"{row_data.sample_id} warning: {issue}")
                issue_label.setObjectName("labtoolsWbWarningRow")
                issue_label.setProperty("sampleId", row_data.sample_id)
                issue_label.setWordWrap(True)
                self._labtools_wb_result_rows.addWidget(issue_label)
        self._clear_layout(self._labtools_wb_lane_grid)
        for index, lane in enumerate(result.lanes):
            card = QFrame()
            card.setObjectName("labtoolsWbLaneCard")
            card.setProperty("laneNumber", lane.lane_number)
            card.setProperty("laneType", lane.lane_type)
            card.setProperty("status", lane.status)
            color = "#FFF1F2" if lane.status == "Error" else ("#F8FAFC" if lane.lane_type == "empty" else "#EFF6FF")
            card.setStyleSheet(f"QFrame#labtoolsWbLaneCard {{ border: 1px solid #CBD5E1; border-radius: 8px; background: {color}; }}")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(8, 8, 8, 8)
            lane_label = QLabel(f"Lane {lane.lane_number}")
            lane_label.setObjectName("labtoolsWbLaneNumber")
            sample_label = QLabel(lane.sample_id)
            sample_label.setObjectName("labtoolsWbLaneSample")
            sample_label.setProperty("laneNumber", lane.lane_number)
            volume_label = QLabel(lane.sample_volume or "Empty / 空白")
            volume_label.setObjectName("labtoolsWbLaneVolume")
            volume_label.setProperty("laneNumber", lane.lane_number)
            layout.addWidget(lane_label)
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
            title="Cell Experiment Workspace / 细胞实验工作区",
            subtitle="细胞信息、实验记录模板和结果处理工具三主区；当前 record store 未接入，保存记录保持禁用。",
        )
        root = content.layout()
        root.addLayout(self._labtools_boundary_nav(status_label="shell_only / record_store_missing", status_key="shell_only"))
        local_model = labtools_runtime.get_labtools_local_data_read_model(self._labtools_project_root)
        body = QHBoxLayout()
        body.setSpacing(12)
        body.addWidget(
            self._labtools_boundary_panel(
                "细胞信息 / Cell Profile & Dynamic State",
                [
                    f"local_data status: {local_model.status.status}",
                    f"local cell profiles: {local_model.status.cell_count}",
                    "Cell line: A549（mock-labelled shell field）",
                    "Passage: P12",
                    "Culture condition: DMEM + 10% FBS, 37 C, 5% CO2",
                    "Current state: 培养中 / 待处理",
                    "污染 / 支原体 / 形态观察 / 汇合度：待记录",
                    *[
                        f"Local cell: {cell.cell_name} P{cell.passage} · {cell.storage_status}"
                        for cell in local_model.cells
                    ],
                ],
                object_name="labtoolsCellProfilePanel",
            ),
            1,
        )
        body.addWidget(
            self._labtools_boundary_panel(
                "细胞实验记录 / Experiment Record Templates",
                [
                    "传代、复苏、冻存、接种、给药 / 处理、转染",
                    "从上次记录创建：需 record store",
                    "接种：计算辅助可用；保存记录 disabled",
                    "不显示假保存记录或假时间线。",
                ],
                object_name="labtoolsCellRecordPanel",
            ),
            1,
        )
        result_panel = self._labtools_boundary_panel(
            "细胞结果处理工具 / Result Processing",
            [
                f"freeze vial overview: {', '.join(local_model.freeze_vial_status_rows)}",
                *[
                    f"Local vial: {vial.vial_label} · {vial.status} · {vial.location or 'no location'}"
                    for vial in local_model.freeze_vials[:6]
                ],
                "Scratch / Transwell / Fluorescence/Staining：规划中",
                "ImageJ/Fiji：Settings-linked 外部能力配置入口",
                "不显示自动 ROI、自动细胞计数或自动分析结果。",
            ],
            object_name="labtoolsCellProcessingPanel",
        )
        result_layout = result_panel.layout()
        settings_button = make_button("前往 Settings 外部能力配置", role="secondary")
        settings_button.setObjectName("labtoolsSettingsLinkButton")
        settings_button.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        settings_button.setProperty("pageKey", "cell_experiment_workspace")
        settings_button.setProperty("semanticKey", PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value)
        settings_button.clicked.connect(self.show_settings)
        result_layout.addWidget(settings_button)
        body.addWidget(result_panel, 1)
        root.addLayout(body)
        root.addWidget(self._labtools_notice_card("免疫与吸光度边界不属于细胞实验页面；细胞记录保存和图像分析运行均需后续 adapter。", object_name="labtoolsAdapterNotice", semantic_key=semantic_key))
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

    def _labtools_primary_entry_card(self, *, title: str, page_key: str, semantic_key: str, status_key: str, rows: list[str], callback) -> QFrame:
        frame = make_workbench_card(object_name="labtoolsPrimaryEntryCard", semantic_state=status_key)
        frame.setObjectName("labtoolsPrimaryEntryCard")
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("pageKey", page_key)
        frame.setProperty("semanticKey", semantic_key)
        frame.setProperty("statusKey", status_key)
        frame.setProperty("uiPrimitive", "module_entry_card")
        frame.setProperty("formalActionEnabled", False)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        header = QHBoxLayout()
        header.addWidget(self._labtools_icon_label(semantic_key, object_name="labtoolsEntryIcon", size=34))
        title_label = QLabel(title)
        title_label.setObjectName("labtoolsPrimaryEntryTitle")
        title_label.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        title_label.setProperty("pageKey", page_key)
        title_label.setProperty("semanticKey", semantic_key)
        title_label.setStyleSheet("font-weight: 700;")
        header.addWidget(title_label)
        header.addStretch(1)
        header.addWidget(make_status_chip(status_key=status_key))
        layout.addLayout(header)
        if semantic_key == PageKey.LABTOOLS_EXPERIMENT_MODULES.value:
            layout.addLayout(self._labtools_experiment_category_icon_row())
        for row in rows:
            label = QLabel(row)
            label.setObjectName("labtoolsEntryDetail")
            label.setWordWrap(True)
            layout.addWidget(label)
        button = make_button("查看壳层", role="secondary", semantic_state=status_key, action_key=page_key)
        button.setObjectName("labtoolsEntryButton")
        button.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        button.setProperty("pageKey", page_key)
        button.setProperty("semanticKey", semantic_key)
        button.setProperty("statusKey", status_key)
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
        label.setFixedSize(size + 8, size + 8)
        label.setAlignment(Qt.AlignCenter)
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
        content_layout.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)
        return page

    def _build_about_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("aboutPage")
        root = QVBoxLayout(page)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)
        title = QLabel("About / 关于")
        title.setObjectName("aboutTitle")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        root.addWidget(title)
        root.addWidget(
            self._list_card(
                "品牌关系",
                [
                    "主入口显示：萤火虫 / Firefly",
                    "当前 bundle 与工程名：BioMedPilot / 医研智析",
                    "模块：Bioinformatics、Meta Analysis、LabTools",
                ],
            )
        )
        root.addWidget(
            self._list_card(
                "阶段边界",
                [
                    "UI-B2 只重建全局低保真壳层。",
                    "Bioinformatics、Meta Analysis、LabTools 业务能力仍按各自 Developer Preview / planned 状态呈现。",
                    "本阶段不替换资源、不打包、不运行 packaged app。",
                ],
            )
        )
        root.addWidget(self._icon_asset_status_card(detailed=False))
        root.addStretch(1)
        return page

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


def _labtools_local_write_result_text(result: labtools_runtime.LabToolsLocalWriteResult) -> str:
    if result.success:
        version = f" v{result.new_version}" if result.new_version is not None else ""
        return f"{result.message} {result.entity_id}{version}".strip()
    blocker = f" blocker={result.blocker}" if result.blocker else ""
    return f"{result.message}{blocker}"
