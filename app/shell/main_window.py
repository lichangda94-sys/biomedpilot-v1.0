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

from app.bioinformatics.workspace import BioinformaticsWorkspaceWidget
from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget
from app.shell.dashboard import DashboardModel, build_dashboard_model
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
        self.setWindowTitle("BioMedPilot / 医研智析")
        self.resize(1180, 760)

        self._stack = QStackedWidget()
        self._dashboard_page = self._build_dashboard_page()
        self._bioinformatics_page = BioinformaticsWorkspaceWidget(on_back=self.show_dashboard)
        self._meta_analysis_page = MetaAnalysisWorkspaceWidget(on_back=self.show_dashboard)
        self._settings_page = self._build_settings_page()
        self._testing_page = self._build_testing_page()
        self._stack.addWidget(self._dashboard_page)
        self._stack.addWidget(self._bioinformatics_page)
        self._stack.addWidget(self._meta_analysis_page)
        self._stack.addWidget(self._settings_page)
        self._stack.addWidget(self._testing_page)

        shell = QWidget()
        shell_layout = QHBoxLayout(shell)
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
        self.setCentralWidget(shell)

    def show_dashboard(self) -> None:
        self._refresh_dashboard_page()
        self._stack.setCurrentWidget(self._dashboard_page)
        self.setWindowTitle("BioMedPilot / 医研智析")

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
            self.show_meta_analysis()

    def current_workspace_key(self) -> str:
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
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)

        title = QLabel(self._dashboard.product_name)
        title.setObjectName("appTitle")
        title.setStyleSheet("font-size: 30px; font-weight: 700;")
        subtitle = QLabel(self._dashboard.product_subtitle)
        subtitle.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(subtitle)

        create_row = QHBoxLayout()
        create_bio = QPushButton("新建生信项目")
        create_bio.clicked.connect(self.create_bioinformatics_project)
        create_meta = QPushButton("新建 Meta 项目")
        create_meta.clicked.connect(self.create_meta_analysis_project)
        create_row.addWidget(create_bio)
        create_row.addWidget(create_meta)
        create_row.addStretch(1)
        root.addLayout(create_row)

        entry_row = QHBoxLayout()
        entry_row.addWidget(self._entry_card("生信分析 Bioinformatics Analysis", self._dashboard.bioinformatics_features, self.show_bioinformatics))
        entry_row.addWidget(self._entry_card("Meta 分析 Meta Analysis", self._dashboard.meta_analysis_features, self.show_meta_analysis))
        root.addLayout(entry_row, 2)

        lower = QHBoxLayout()
        lower.addWidget(self._recent_projects_card())
        lower.addWidget(self._list_card("最近任务", [task.display_label() for task in self._dashboard.recent_tasks] or ["暂无最近任务"]))
        lower.addWidget(StatusPanel(self._dashboard.environment, self._dashboard.test_mode_label))
        root.addLayout(lower, 1)
        return page

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
