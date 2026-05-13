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

from app.app_identity import APP_NAME, icon_asset_statuses, icon_asset_summary, load_app_icon
from app.bioinformatics.workspace import BioinformaticsWorkspaceWidget
from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget
from app.shell.dashboard import DashboardModel, build_dashboard_model
from app.shell.login import BioMedPilotLoginWidget, LocalSession
from app.shell.module_selection import ModuleSelectionWidget
from app.shell.sidebar import SidebarWidget
from app.shell.status_panel import StatusPanel
from app.shared.project_center.service import ProjectCenter, ProjectRecord
from app.shared.settings import SettingsProfile
from app.shared.testing_mode import generate_feedback_template, testing_mode_summary


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
        self._login_page = BioMedPilotLoginWidget(on_login=self._complete_login)
        self._root_stack.addWidget(self._login_page)

        self._stack = QStackedWidget()
        self._dashboard_page = self._build_dashboard_page()
        self._bioinformatics_page = self._build_bioinformatics_page()
        self._meta_analysis_page = MetaAnalysisWorkspaceWidget(on_back=self.show_dashboard)
        self._settings_page = self._build_settings_page()
        self._testing_page = self._build_testing_page()
        self._stack.addWidget(self._dashboard_page)
        self._stack.addWidget(self._bioinformatics_page)
        self._stack.addWidget(self._meta_analysis_page)
        self._stack.addWidget(self._settings_page)
        self._stack.addWidget(self._testing_page)

        self._shell_page = QWidget()
        shell_layout = QHBoxLayout(self._shell_page)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        shell_layout.addWidget(
            SidebarWidget(
                on_dashboard=self.show_dashboard,
                on_bioinformatics=self.show_bioinformatics,
                on_meta_analysis=self.show_meta_analysis,
                on_settings=self.show_settings,
                on_testing=self.show_testing_mode,
            )
        )
        shell_layout.addWidget(self._stack, 1)
        self._root_stack.addWidget(self._shell_page)
        self._root_stack.setCurrentWidget(self._login_page)
        self.setCentralWidget(self._root_stack)

    def current_session(self) -> LocalSession | None:
        return self._session

    def _complete_login(self, session: LocalSession) -> None:
        self._session = session
        self.show_dashboard()
        self._root_stack.setCurrentWidget(self._shell_page)

    def logout(self) -> None:
        self._session = None
        self._login_page.reset_session()
        self._root_stack.setCurrentWidget(self._login_page)
        self.setWindowTitle(APP_NAME)

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

    def show_settings(self) -> None:
        self._stack.setCurrentWidget(self._settings_page)
        self.setWindowTitle("BioMedPilot / 设置中心")

    def show_testing_mode(self) -> None:
        self._stack.setCurrentWidget(self._testing_page)
        self.setWindowTitle("BioMedPilot / 测试模式")

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
        if hasattr(self, "_root_stack") and self._root_stack.currentWidget() is self._login_page:
            return "login"
        current = self._stack.currentWidget()
        if current is self._bioinformatics_page:
            return "bioinformatics"
        if current is self._meta_analysis_page:
            return "meta_analysis"
        if current is self._settings_page:
            return "settings"
        if current is self._testing_page:
            return "testing"
        return "dashboard"

    def _build_dashboard_page(self) -> QWidget:
        return ModuleSelectionWidget(
            dashboard=self._dashboard,
            session=self._session,
            on_open_bioinformatics=self.show_bioinformatics,
            on_open_meta_analysis=self.show_meta_analysis,
            on_logout=self.logout,
        )

    def _build_bioinformatics_page(self) -> QWidget:
        try:
            page = BioinformaticsWorkspaceWidget(on_back=self.show_dashboard)
        except TypeError:
            page = BioinformaticsWorkspaceWidget()
        if isinstance(page, QWidget):
            return page
        fallback = QWidget()
        layout = QVBoxLayout(fallback)
        layout.setContentsMargins(28, 24, 28, 24)
        title = QLabel("Bioinformatics / 生信分析")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        layout.addWidget(title)
        message = QLabel("Bioinformatics workspace is unavailable in this Integration runtime; shell navigation remains testable.")
        message.setWordWrap(True)
        layout.addWidget(message)
        layout.addStretch(1)
        return fallback

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

    def _build_settings_page(self) -> QWidget:
        profile = SettingsProfile()
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)
        title = QLabel("Settings / 设置中心")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        root.addWidget(title)
        note = QLabel("设置中心当前为占位页，用于统一管理默认项目路径、语言、Python/R 环境、本地 AI 模型、数据库、图表样式、导出格式和缓存清理。")
        note.setWordWrap(True)
        root.addWidget(note)
        root.addWidget(self._icon_asset_status_card(detailed=True))
        rows = [
            ("默认项目路径", profile.default_project_path),
            ("语言", profile.language),
            ("Python 环境", profile.python_environment),
            ("R 环境", profile.r_environment),
            ("本地 AI 模型", profile.local_ai_model),
            ("数据库设置", profile.database_settings),
            ("图表样式", profile.chart_style),
            ("导出格式", profile.export_format),
            ("缓存清理", profile.cache_cleanup),
        ]
        for label, value in rows:
            root.addWidget(self._list_card(label, [value]))
        root.addStretch(1)
        return page

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
        feedback_button.clicked.connect(self.generate_testing_feedback_template)
        content_layout.addWidget(feedback_button)
        content_layout.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)
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
