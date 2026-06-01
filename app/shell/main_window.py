from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QInputDialog,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.app_identity import APP_NAME, load_app_icon
from app.bioinformatics.workspace import BioinformaticsWorkspaceWidget
from app.labtools.workspace import LabToolsWorkspaceWidget
from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget
from app.shell.dashboard import DashboardModel, build_dashboard_model
from app.shell.centers_page import build_centers_page
from app.shell.login import BioMedPilotLoginWidget, LocalSession
from app.shell.module_selection import ModuleSelectionWidget
from app.shell.settings_page import build_settings_page
from app.shell.sidebar import SidebarWidget
from app.shell.status_panel import StatusPanel
from app.shared.project_center.service import ProjectCenter, ProjectRecord
from app.shared.testing_mode import generate_feedback_template, testing_mode_summary
from app.shared.ui import card_title_qss, page_title_qss, surface_card_qss


ABOUT_BIOMEDPILOT_TEXT = """关于 BioMedPilot / 医研智析

BioMedPilot / 医研智析 是一个面向生物医学研究的软件工具，围绕生信分析、Meta 分析和实验辅助工具，帮助研究者更高效地整理信息、完成分析、记录实验过程，并减少重复性工作。

我们希望它不只是一个工具，也是一位安静、可靠的研究助手。它可以帮助用户理清思路、规范流程、提高效率，但不会替代研究者的专业判断。重要的分析结果、实验计算和研究结论，仍应由使用者结合专业知识和实际场景进行复核。

BioMedPilot / 医研智析 希望继承开放协作与知识共享的精神。像开源社区一样，我们相信工具应当在共同使用、共同修正、共同贡献中成长；也相信科研知识和研究工具不应被过高的门槛隔开，不应只照亮少数拥有充足资源的人。

因此，我们会尽可能将大部分基础功能免费开放，让更多学生、青年研究者、基层实验人员和独立探索者，都能在自己的研究道路上少一些重复消耗，多一点清晰和支持。

如果未来接入联网 AI、云端模型等需要长期成本的能力，相关功能可能会设置必要且合理的费用，用于维持服务运行。但我们会尽量保持克制、透明和节制，不让成本成为阻断普通研究者使用基础工具的高墙。

我们也欢迎有相关经验和想法的人一起参与完善：无论是生物医学研究、生信分析、Meta 分析、实验流程、软件开发、界面设计、文档写作，还是对科研工具使用体验的建议，都可能帮助 BioMedPilot 变得更清晰、更实用、更贴近真实科研工作。

如果你愿意贡献一个想法、指出一个问题、补充一个场景、优化一句提示，都是这个项目继续成长的一部分。

“有一分热，发一分光，就令萤火一般，也可以在黑暗里发一点光，不必等候炬火。”鲁迅"""


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
        self._labtools_page = LabToolsWorkspaceWidget(on_back=self.show_dashboard)
        self._centers_page = self._build_centers_page()
        self._settings_page = self._build_settings_page()
        self._testing_page = self._build_testing_page()
        self._about_page = self._build_about_page()
        self._stack.addWidget(self._dashboard_page)
        self._stack.addWidget(self._bioinformatics_page)
        self._stack.addWidget(self._meta_analysis_page)
        self._stack.addWidget(self._labtools_page)
        self._stack.addWidget(self._centers_page)
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
            on_centers=self.show_centers,
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

    def show_centers(self) -> None:
        self._centers_page = self._build_centers_page()
        centers_index = self._stack.indexOf(self._centers_page)
        if centers_index < 0:
            old_centers = next((self._stack.widget(index) for index in range(self._stack.count()) if self._stack.widget(index).objectName() == "centersPage"), None)
            if old_centers is not None:
                old_index = self._stack.indexOf(old_centers)
                self._stack.insertWidget(old_index, self._centers_page)
                self._stack.removeWidget(old_centers)
                old_centers.deleteLater()
        self._stack.setCurrentWidget(self._centers_page)
        self._set_sidebar_active("centers")
        self.setWindowTitle("BioMedPilot / Centers")

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
        if current is self._centers_page:
            return "centers"
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
            on_logout=self.logout,
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
        frame.setStyleSheet(surface_card_qss("QFrame#entryCard"))
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 18, 20, 18)
        label = QLabel(title)
        label.setStyleSheet(page_title_qss())
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
        frame.setStyleSheet(surface_card_qss())
        layout = QVBoxLayout(frame)
        header = QLabel(title)
        header.setStyleSheet(card_title_qss())
        layout.addWidget(header)
        for row in rows:
            label = QLabel(row)
            label.setWordWrap(True)
            layout.addWidget(label)
        layout.addStretch(1)
        return frame

    def _recent_projects_card(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(surface_card_qss())
        layout = QVBoxLayout(frame)
        header = QLabel("最近项目")
        header.setStyleSheet(card_title_qss())
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

    def _build_settings_page(self) -> QWidget:
        return build_settings_page()

    def _build_centers_page(self) -> QWidget:
        return build_centers_page(project_center=self._project_center)

    def _build_testing_page(self) -> QWidget:
        summary = testing_mode_summary()
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)
        title = QLabel("Testing Mode / 用户测试模式")
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
        page = QScrollArea()
        page.setObjectName("aboutPage")
        page.setWidgetResizable(True)
        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(14)
        label = QLabel(ABOUT_BIOMEDPILOT_TEXT)
        label.setObjectName("aboutText")
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label.setStyleSheet("font-size: 14px; line-height: 1.45;")
        root.addWidget(label)
        root.addStretch(1)
        page.setWidget(content)
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
