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
from app.shell.sidebar import SidebarWidget
from app.shell.status_panel import StatusPanel
from app.shared.project_center.service import ProjectCenter, ProjectRecord
from app.shared.semantic_keys import ModuleKey, PageKey
from app.shared.settings import SettingsProfile
from app.shared.testing_mode import generate_feedback_template, testing_mode_summary
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

    def _show_labtools_general_calculator_shell(self) -> None:
        content = self._build_labtools_section_content(
            page_key="general_calculators",
            semantic_key=PageKey.LABTOOLS_GENERAL_CALCULATORS.value,
            title="通用计算器 / General Calculator",
            subtitle="仅建立 Quick Calculator 与 Dynamic Formula Solver 的安全占位路由；本阶段不执行真实计算。",
            status_label="后端可用 / 需 UI 适配",
            status_key="testing",
            cards=[
                {
                    "title": "Quick Calculator",
                    "page_key": "quick_calculator",
                    "semantic_key": "labtools.page.quick_calculator",
                    "status_label": "backend_ready / ui_adapter_needed",
                    "status_key": "testing",
                    "rows": ["稀释、单位换算、细胞铺板辅助仅作为计算入口占位。", "保存历史与导出保持禁用。"],
                    "callback": lambda: self._show_labtools_placeholder_page(
                        title="Quick Calculator / 快速计算",
                        page_key="quick_calculator",
                        semantic_key="labtools.page.quick_calculator",
                        status_label="backend_ready / ui_adapter_needed",
                        status_key="testing",
                        body_rows=[
                            "本阶段只展示计算器占位页面和状态边界，不调用 LabTools calculator execution。",
                            "细胞铺板只作为计算辅助，不是细胞实验记录保存。",
                        ],
                        disabled_actions=("保存到历史 - 需存储适配", "导出结果 - 暂未开放"),
                    ),
                },
                {
                    "title": "Dynamic Formula Solver",
                    "page_key": "formula_solver",
                    "semantic_key": "labtools.page.formula_solver",
                    "status_label": "backend_ready / ui_adapter_needed",
                    "status_key": "testing",
                    "rows": ["公式选择、求解目标与单位输入将在后续 adapter 层接入。", "本阶段不生成计算结果。"],
                    "callback": lambda: self._show_labtools_placeholder_page(
                        title="Dynamic Formula Solver / 动态公式求解",
                        page_key="formula_solver",
                        semantic_key="labtools.page.formula_solver",
                        status_label="backend_ready / ui_adapter_needed",
                        status_key="testing",
                        body_rows=[
                            "保留公式求解页面壳层、结果区空状态和复核提示。",
                            "无效输入不会生成假结果；真实求解等待 UI adapter。",
                        ],
                        disabled_actions=("保存公式运行 - 需存储适配", "导出结果 - 暂未开放"),
                    ),
                },
            ],
        )
        self._set_labtools_content(content)

    def _show_labtools_reagent_preparation_shell(self) -> None:
        content = self._build_labtools_section_content(
            page_key="reagent_preparation",
            semantic_key=PageKey.LABTOOLS_REAGENT_PREPARATION.value,
            title="试剂制备 / Reagent Preparation",
            subtitle="模板、编辑侧栏和本次配制只建立安全占位路由；本阶段不读取或写入真实 store。",
            status_label="backend_ready / storage_adapter_needed",
            status_key="planned",
            cards=[
                {
                    "title": "Reagent Template List",
                    "page_key": "reagent_template_list",
                    "semantic_key": "labtools.page.reagent_template_list",
                    "status_label": "需存储适配",
                    "status_key": "planned",
                    "rows": ["项目内试剂模板列表占位。", "未接入 BioMedPilotLabToolsStorageAdapter 前保持空状态。"],
                    "callback": lambda: self._show_labtools_placeholder_page(
                        title="Reagent Template List / 试剂模板列表",
                        page_key="reagent_template_list",
                        semantic_key="labtools.page.reagent_template_list",
                        status_label="storage_adapter_needed",
                        status_key="planned",
                        body_rows=[
                            "当前项目暂无试剂模板；列表不会默认读取或写入 ~/.labtools。",
                            "模板保存必须等待 BioMedPilot project storage adapter。",
                        ],
                        disabled_actions=("新建模板 - 需存储适配", "保存模板 - 需存储适配"),
                    ),
                },
                {
                    "title": "Template Editor Side Panel",
                    "page_key": "reagent_template_editor",
                    "semantic_key": "labtools.page.reagent_template_editor",
                    "status_label": "需存储适配",
                    "status_key": "planned",
                    "rows": ["模板编辑侧栏占位，显示 dirty state 和 validation 入口。", "保存按钮保持禁用。"],
                    "callback": lambda: self._show_labtools_placeholder_page(
                        title="Reagent Template Editor / 模板编辑侧栏",
                        page_key="reagent_template_editor",
                        semantic_key="labtools.page.reagent_template_editor",
                        status_label="storage_adapter_needed",
                        status_key="planned",
                        body_rows=[
                            "侧栏用于后续承载组分表、pH 字段和 validation summary。",
                            "已修改未保存只能表示 UI dirty state，不表示版本管理已完成。",
                        ],
                        disabled_actions=("保存模板 - 需存储适配",),
                    ),
                },
                {
                    "title": "Reagent Preparation Run",
                    "page_key": "reagent_preparation_run",
                    "semantic_key": "labtools.page.reagent_preparation_run",
                    "status_label": "backend_ready / adapter_needed",
                    "status_key": "testing",
                    "rows": ["本次配制计算预览占位。", "保存配制记录和导出仍需 adapter。"],
                    "callback": lambda: self._show_labtools_placeholder_page(
                        title="Reagent Preparation Run / 本次试剂配制",
                        page_key="reagent_preparation_run",
                        semantic_key="labtools.page.reagent_preparation_run",
                        status_label="backend_ready / adapter_needed",
                        status_key="testing",
                        body_rows=[
                            "后续可显示配制计算预览，但本阶段不调用真实计算或保存记录。",
                            "不启用库存扣减、生产批次放行、云模板库或多人同步。",
                        ],
                        disabled_actions=("保存配制记录 - 需存储适配", "导出配制摘要 - 需文件选择器"),
                    ),
                },
            ],
            notice_rows=["桌面 UI 不默认写入 ~/.labtools；所有保存路径必须由 BioMedPilotLabToolsStorageAdapter 提供。"],
        )
        self._set_labtools_content(content)

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
                    "rows": ["WB 上样计算页面占位。", "不执行真实 WB calculation；保存和导出保持禁用。"],
                    "callback": lambda: self._show_labtools_placeholder_page(
                        title="Western Blot Loading / WB 上样计算",
                        page_key="wb_loading",
                        semantic_key=PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value,
                        status_label="active_backend_ready / adapter_needed",
                        status_key="testing",
                        body_rows=[
                            "当前仅提供 WB 上样计算壳层；不调用 calculate_wb_loading。",
                            "泳道布局是后续示意区域，不生成假胶图、假条带或图像分析结果。",
                        ],
                        disabled_actions=("保存 WB 记录 - 需存储适配", "导出 CSV / Markdown - 需文件选择器"),
                    ),
                },
                {
                    "title": "SDS-PAGE",
                    "page_key": "sds_page",
                    "semantic_key": PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value,
                    "status_label": "active_backend_ready / adapter_needed",
                    "status_key": "planned",
                    "rows": ["配胶子页面占位。", "XLSX 导出和模板持久化未启用。"],
                    "callback": lambda: self._show_labtools_placeholder_page(
                        title="SDS-PAGE / 配胶",
                        page_key="sds_page",
                        semantic_key=PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value,
                        status_label="adapter_needed",
                        status_key="planned",
                        body_rows=["SDS-PAGE 后端 helper 可规划接入，但本阶段只显示子页面占位。"],
                        disabled_actions=("保存配胶模板 - 需存储适配", "导出 XLSX - 需文件选择器"),
                    ),
                },
                {
                    "title": "BCA / OD MVP Boundary",
                    "page_key": "bca_od_mvp",
                    "semantic_key": PageKey.LABTOOLS_IMMUNO_ABSORBANCE.value,
                    "status_label": "testing_preview_only",
                    "status_key": "testing",
                    "rows": ["8 x 12 OD matrix / annotation / linear-fit summary 仅保留边界占位。", "不声明正式保存、导出或临床级定量。"],
                    "callback": lambda: self._show_labtools_placeholder_page(
                        title="BCA / OD MVP Boundary",
                        page_key="bca_od_mvp",
                        semantic_key=PageKey.LABTOOLS_IMMUNO_ABSORBANCE.value,
                        status_label="testing_preview_only",
                        status_key="testing",
                        body_rows=["BCA / OD 可以显示 MVP 边界，但本阶段不运行 BCA helper、不保存、不导出。"],
                        disabled_actions=("保存 BCA 记录 - 后端记录模型未完成", "导出 BCA 结果 - 暂未开放"),
                    ),
                },
                {
                    "title": "Cell Experiment Workspace",
                    "page_key": "cell_experiment_workspace",
                    "semantic_key": PageKey.LABTOOLS_CELL_EXPERIMENTS.value,
                    "status_label": "shell_only / record_store_missing",
                    "status_key": "shell_only",
                    "rows": ["细胞信息、实验记录模板、结果处理工具三主区占位。", "保存细胞记录保持禁用。"],
                    "callback": lambda: self._show_labtools_placeholder_page(
                        title="Cell Experiment Workspace / 细胞实验工作区",
                        page_key="cell_experiment_workspace",
                        semantic_key=PageKey.LABTOOLS_CELL_EXPERIMENTS.value,
                        status_label="shell_only / record_store_missing",
                        status_key="shell_only",
                        body_rows=[
                            "细胞实验记录 store 尚未接入；不显示假记录、假时间线或真实保存。",
                            "ELISA 不属于此页面。",
                        ],
                        disabled_actions=("保存细胞记录 - 后端未完成", "运行图像分析 - 暂未开放"),
                    ),
                },
                {
                    "title": "ELISA / Immuno-Absorbance",
                    "page_key": "elisa_boundary",
                    "semantic_key": PageKey.LABTOOLS_IMMUNO_ABSORBANCE.value,
                    "status_label": "blocked_until_backend",
                    "status_key": "blocked",
                    "rows": ["ELISA backend 未完成。", "不启用 4PL、正式报告、保存或导出。"],
                    "callback": lambda: self._show_labtools_placeholder_page(
                        title="ELISA / Immuno-Absorbance Boundary",
                        page_key="elisa_boundary",
                        semantic_key=PageKey.LABTOOLS_IMMUNO_ABSORBANCE.value,
                        status_label="blocked_until_backend",
                        status_key="blocked",
                        body_rows=["ELISA 后端缺失；4PL、正式结果、报告和导出都保持禁用。"],
                        disabled_actions=("运行 ELISA 分析 - 后端未完成", "保存记录 - 后端未完成", "导出报告 - 后端未完成"),
                    ),
                },
                {
                    "title": "Image Processing Workspace",
                    "page_key": "image_processing_boundary",
                    "semantic_key": "labtools.page.image_processing_boundary",
                    "status_label": "shell_only / external_engine_adapter_missing",
                    "status_key": "shell_only",
                    "rows": ["ImageJ/Fiji 仅作为 Settings-linked 外部能力入口。", "不运行 macro、自动 ROI、自动细胞计数或条带识别。"],
                    "callback": lambda: self._show_labtools_placeholder_page(
                        title="Image Processing Workspace / 图像处理边界",
                        page_key="image_processing_boundary",
                        semantic_key="labtools.page.image_processing_boundary",
                        status_label="shell_only / external_engine_adapter_missing",
                        status_key="shell_only",
                        body_rows=[
                            "ImageJ/Fiji 仅显示为 Settings-linked 外部能力配置入口。",
                            "本阶段不实现可执行检测、macro runner、ROI model、result parser 或批量处理。",
                        ],
                        disabled_actions=("运行图像分析 - 暂未开放", "保存图像结果 - 暂未开放"),
                        settings_link=True,
                    ),
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
        button = make_button("查看壳层", role="secondary")
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
