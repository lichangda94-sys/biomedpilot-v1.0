from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QInputDialog,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.app_identity import APP_NAME, icon_asset_statuses, icon_asset_summary, load_app_icon
from app.bioinformatics.workspace import BioinformaticsWorkspaceWidget
from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget
from app.shell.dashboard import DashboardModel, build_dashboard_model
from app.shell.login import BioMedPilotLoginWidget, LocalSession
from app.shell.module_selection import ModuleSelectionWidget
from app.shell.sidebar import SidebarWidget
from app.shell.status_panel import StatusPanel
from app.shared.project_center.service import ProjectCenter, ProjectRecord
from app.shared.semantic_keys import ModuleKey, PageKey
from app.shared.settings import SettingsProfile
from app.shared.testing_mode import generate_feedback_template, testing_mode_summary
from app.shared.ui_components.primitives import diagnostic_disclosure_title, make_button, make_status_chip


class MainWindow(QMainWindow):
    def __init__(self, dashboard: DashboardModel | None = None) -> None:
        super().__init__()
        self._project_center = ProjectCenter.default()
        self._dashboard = dashboard or build_dashboard_model()
        self._session: LocalSession | None = None
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
        content = QWidget()
        content.setObjectName("labtoolsShellContent")
        content.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        content.setProperty("pageKey", "home")
        content.setProperty("semanticKey", PageKey.LABTOOLS_HOME.value)
        root = QVBoxLayout(content)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)
        title = QLabel("LabTools / 实验工具")
        title.setObjectName("labtoolsShellTitle")
        title.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        title.setProperty("semanticKey", ModuleKey.LABTOOLS.value)
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        root.addWidget(title)
        note = QLabel("低保真 IA 壳层：LabTools 一级入口只保留通用计算器、试剂制备、实验模块。本阶段不接入真实实验计算、完整库存、云端协作或局域网共享。")
        note.setObjectName("labtoolsScopeNote")
        note.setWordWrap(True)
        root.addWidget(note)

        entry_row = QHBoxLayout()
        entry_row.setSpacing(14)
        entry_row.addWidget(
            self._labtools_primary_entry_card(
                title="通用计算器",
                page_key="general_calculators",
                semantic_key=PageKey.LABTOOLS_GENERAL_CALCULATORS.value,
                status_key="shell_only",
                rows=[
                    "跨实验场景的公式型动态求解器。",
                    "不包含 Western Blot、PCR/qPCR、ELISA、MTT/CCK-8/AlamarBlue 等实验专属计算。",
                ],
            )
        )
        entry_row.addWidget(
            self._labtools_primary_entry_card(
                title="试剂制备",
                page_key="reagent_preparation",
                semantic_key=PageKey.LABTOOLS_REAGENT_PREPARATION.value,
                status_key="planned",
                rows=[
                    "模板 -> 本次配制 -> 配制单 -> 配制记录。",
                    "可预留材料记录联动，但不实现完整库存系统。",
                ],
            )
        )
        entry_row.addWidget(
            self._labtools_primary_entry_card(
                title="实验模块",
                page_key="experiment_modules",
                semantic_key=PageKey.LABTOOLS_EXPERIMENT_MODULES.value,
                status_key="testing",
                rows=[
                    "按真实实验目的和流程组织。",
                    "实验专属计算、记录、数据处理和图像分析辅助归入对应实验模块。",
                ],
            )
        )
        root.addLayout(entry_row)

        module_grid = QGridLayout()
        module_grid.setHorizontalSpacing(14)
        module_grid.setVerticalSpacing(14)
        for index, (module_title, page_key, semantic_key, status_key, rows) in enumerate(
            (
                (
                    "细胞实验",
                    "cell_experiments",
                    PageKey.LABTOOLS_CELL_EXPERIMENTS.value,
                    "testing",
                    ["细胞培养与传代", "接种 / 铺板记录", "MTT / CCK-8 / AlamarBlue 归属此类"],
                ),
                (
                    "蛋白实验",
                    "protein_experiments",
                    PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value,
                    "planned",
                    ["蛋白样本与定量", "Western Blot 完整流程", "SDS-PAGE 配胶归入 Western Blot"],
                ),
                (
                    "核酸实验",
                    "nucleic_acid_experiments",
                    PageKey.LABTOOLS_NUCLEIC_ACID_EXPERIMENTS.value,
                    "planned",
                    ["样本与核酸提取记录", "PCR", "qPCR 与 plate layout"],
                ),
                (
                    "免疫与吸光度实验",
                    "immuno_absorbance",
                    PageKey.LABTOOLS_IMMUNO_ABSORBANCE.value,
                    "planned",
                    ["ELISA", "标准曲线与浓度计算", "结果记录与导出"],
                ),
                (
                    "免疫组化",
                    "ihc",
                    PageKey.LABTOOLS_IHC.value,
                    "shell_only",
                    ["切片 / 染色记录", "图像记录辅助", "结果记录"],
                ),
            )
        ):
            module_grid.addWidget(
                self._labtools_experiment_module_card(
                    module_title,
                    page_key=page_key,
                    semantic_key=semantic_key,
                    status_key=status_key,
                    rows=rows,
                ),
                index // 2,
                index % 2,
            )
        root.addLayout(module_grid)

        root.addWidget(
            self._labtools_boundary_card(
                "外部图像分析引擎",
                [
                    "不作为 LabTools 一级入口。",
                    "引擎检测、路径、版本和安装提示统一在 Settings / 外部能力中管理。",
                    "LabTools 仅在具体实验模块中显示图像分析辅助的 planned / shell-only 状态。",
                ],
            )
        )
        root.addWidget(
            self._labtools_boundary_card(
                "当前不实施范围",
                [
                    "不实现完整库存系统。",
                    "不做云端协作。",
                    "不做局域网共享。",
                    "不重写真实实验计算逻辑。",
                ],
            )
        )
        root.addStretch(1)
        page.setWidget(content)
        return page

    def _labtools_primary_entry_card(self, *, title: str, page_key: str, semantic_key: str, status_key: str, rows: list[str]) -> QFrame:
        frame = QFrame()
        frame.setObjectName("labtoolsPrimaryEntryCard")
        frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        frame.setProperty("pageKey", page_key)
        frame.setProperty("semanticKey", semantic_key)
        frame.setProperty("statusKey", status_key)
        frame.setStyleSheet("QFrame#labtoolsPrimaryEntryCard { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        header = QHBoxLayout()
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
        for row in rows:
            label = QLabel(row)
            label.setObjectName("labtoolsEntryDetail")
            label.setWordWrap(True)
            layout.addWidget(label)
        button = make_button("查看壳层", role="secondary")
        button.setObjectName("labtoolsEntryButton")
        button.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
        button.setProperty("pageKey", page_key)
        button.setProperty("semanticKey", semantic_key)
        button.setProperty("statusKey", status_key)
        button.setEnabled(False)
        layout.addWidget(button)
        return frame

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
        profile = SettingsProfile()
        page = QScrollArea()
        page.setObjectName("settingsPage")
        page.setWidgetResizable(True)
        page.setProperty("moduleKey", ModuleKey.SETTINGS.value)
        page.setProperty("pageKey", "settings")
        page.setProperty("semanticKey", ModuleKey.SETTINGS.value)
        page.setProperty("usabilityRole", "scrollable_shell_page")
        page.setAccessibleName("Settings shell page")
        content = QWidget()
        content.setObjectName("settingsContent")
        content.setProperty("moduleKey", ModuleKey.SETTINGS.value)
        content.setProperty("pageKey", "settings")
        content.setProperty("semanticKey", ModuleKey.SETTINGS.value)
        root = QVBoxLayout(content)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)
        title = QLabel("Settings / 设置中心")
        title.setObjectName("settingsTitle")
        title.setProperty("moduleKey", ModuleKey.SETTINGS.value)
        title.setProperty("semanticKey", ModuleKey.SETTINGS.value)
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        root.addWidget(title)
        note = QLabel("低保真 Settings 壳层：集中呈现外部能力、模型与分析资源状态。所有外部能力遵循 detect-first，安装、更新和云端配置仅保留禁用入口。")
        note.setObjectName("settingsScopeNote")
        note.setWordWrap(True)
        root.addWidget(note)

        body = QHBoxLayout()
        body.setSpacing(16)
        nav = QListWidget()
        nav.setObjectName("settingsSecondaryNav")
        nav.setFixedWidth(230)
        for label, page_key, semantic_key in (
            ("通用偏好", "general", PageKey.SETTINGS_GENERAL.value),
            ("外部能力", "external_capabilities", PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value),
            ("分析资源", "analysis_resources", PageKey.SETTINGS_ANALYSIS_RESOURCES.value),
            ("模型与引擎", "model_engine", PageKey.SETTINGS_MODEL_ENGINE.value),
            ("开发者诊断", "developer_diagnostics", PageKey.SETTINGS_DEVELOPER_DIAGNOSTICS.value),
        ):
            nav_item = QListWidgetItem(label)
            nav_item.setData(Qt.UserRole, page_key)
            nav_item.setData(Qt.UserRole + 1, semantic_key)
            nav.addItem(nav_item)

        stack = QStackedWidget()
        stack.setObjectName("settingsContentStack")
        stack.addWidget(self._build_settings_general_page(profile))
        stack.addWidget(self._build_settings_external_capabilities_page())
        stack.addWidget(self._build_settings_analysis_resources_page())
        stack.addWidget(self._build_settings_model_engine_page(profile))
        stack.addWidget(self._build_settings_developer_diagnostics_page())
        nav.currentRowChanged.connect(stack.setCurrentIndex)
        nav.setCurrentRow(0)

        body.addWidget(nav)
        body.addWidget(stack, 1)
        root.addLayout(body, 1)
        root.addStretch(1)
        page.setWidget(content)
        return page

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
        root.addWidget(self._icon_asset_status_card(detailed=True))
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
        for title, status_key, details in (
            (
                "Python 环境",
                "available",
                [
                    ("检测目标", "Python executable / package visibility"),
                    ("后续动作", "用户触发安装或更新，当前禁用"),
                ],
            ),
            (
                "R 环境",
                "not_configured",
                [
                    ("检测目标", "Rscript / R packages"),
                    ("后续动作", "检测后提示用户安装，当前禁用"),
                ],
            ),
            (
                "ImageJ/Fiji",
                "not_configured",
                [
                    ("检测目标", "本地 ImageJ/Fiji executable"),
                    ("归属", "LabTools 外部图像引擎，不进入主任务页"),
                ],
            ),
            (
                "外部图像分析引擎",
                "planned",
                [
                    ("检测目标", "engine path / version / capability manifest"),
                    ("边界", "仅壳层占位，不连接真实引擎"),
                ],
            ),
        ):
            root.addWidget(self._settings_capability_card(title, status_key=status_key, details=details))
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
        for title, status_key, details in (
            (
                "GO / KEGG / MSigDB 资源",
                "planned",
                [
                    ("检测目标", "本地资源 manifest 与版本"),
                    ("边界", "不自动下载数据库"),
                ],
            ),
            (
                "Bioinformatics resolver / input package",
                "preflight_only",
                [
                    ("检测目标", "standardized repository 与 analysis input package"),
                    ("边界", "resolver-first，未通过预检不显示正式运行承诺"),
                ],
            ),
            (
                "Report / Export templates",
                "developer_preview",
                [
                    ("检测目标", "Markdown / HTML / DOCX template availability"),
                    ("边界", "报告模板多语言化后再正式开放"),
                ],
            ),
        ):
            root.addWidget(self._settings_capability_card(title, status_key=status_key, details=details))
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
            rows=[
                ("用途", "仅供开发者查看本地检测槽位、图标资源状态和壳层边界。"),
                ("外部动作", "不会安装、下载、更新或连接云端。"),
                ("覆盖范围", "Settings 二级导航、状态标签、检测优先 UI。"),
            ],
        )
        panel.setObjectName("developerDiagnosticsPanel")
        panel.setVisible(False)
        toggle.toggled.connect(panel.setVisible)
        root.addWidget(panel)
        root.addStretch(1)
        return page

    def _settings_status_card(self, *, title: str, status_key: str, rows: list[tuple[str, str]]) -> QFrame:
        frame = QFrame()
        frame.setObjectName("settingsStatusCard")
        frame.setProperty("moduleKey", ModuleKey.SETTINGS.value)
        frame.setProperty("statusKey", status_key)
        frame.setStyleSheet("QFrame#settingsStatusCard { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        header = QHBoxLayout()
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

    def _settings_capability_card(self, title: str, *, status_key: str, details: list[tuple[str, str]]) -> QFrame:
        frame = self._settings_status_card(title=title, status_key=status_key, rows=details)
        frame.setObjectName("settingsCapabilityCard")
        frame.setProperty("moduleKey", ModuleKey.SETTINGS.value)
        frame.setProperty("statusKey", status_key)
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
