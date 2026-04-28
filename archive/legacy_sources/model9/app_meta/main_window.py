from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QMainWindow,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from app_meta.core.demo_data import PLACEHOLDER_DESCRIPTIONS
from app_meta.core.project_io import (
    PROJECT_JSON,
    create_project,
    export_project_attempt,
    log_project_event,
    open_project,
    save_project,
)
from app_meta.core.project_state import MetaProjectState, create_demo_project_state
from app_meta.ui.components import PlaceholderPage
from app_meta.ui.data_extraction_page import DataExtractionPage
from app_meta.ui.dashboard_page import DashboardPage
from app_meta.ui.deduplication_page import DeduplicationPage
from app_meta.ui.icon_registry import meta_icon
from app_meta.ui.literature_import_page import LiteratureImportPage
from app_meta.ui.output_pages import ForestPlotPage, FunnelPlotPage, ReportingPage
from app_meta.ui.pico_search_page import PicoSearchPage
from app_meta.ui.project_management_page import ProjectManagementPage
from app_meta.ui.screening_page import ScreeningPage
from app_meta.ui.sidebar import NAV_ITEMS, Sidebar
from app_meta.ui.theme import app_stylesheet
from app_meta.ui.top_toolbar import TopToolbar


class MetaMainWindow(QMainWindow):
    def __init__(self, project_state: MetaProjectState | None = None) -> None:
        super().__init__()
        self._project_state = project_state or create_demo_project_state()
        self.setWindowTitle("BioMedPilot · Meta分析")
        self.setWindowIcon(meta_icon("app"))
        self.setMinimumSize(1440, 900)
        self.resize(1500, 940)
        self.setStyleSheet(app_stylesheet())

        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._stack = QStackedWidget()
        self._pages: dict[str, QWidget] = {}
        self._sidebar = Sidebar(self.open_page, self._project_state)
        root.addWidget(self._sidebar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 18, 24, 18)
        content_layout.setSpacing(18)
        content_layout.addWidget(TopToolbar(self._handle_toolbar_action))
        content_layout.addWidget(self._stack, 1)
        root.addWidget(content, 1)
        self.setCentralWidget(central)

        self._install_pages()
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage(f"就绪 · Demo 数据已加载 · 当前项目进度 {self._project_state.progress_percent}%")
        self.open_page("首页")

    def _install_pages(self) -> None:
        for item in NAV_ITEMS:
            if item == "首页":
                page = DashboardPage(self._project_state, self._show_status)
            elif item == "PICO/Search":
                page = PicoSearchPage(self._project_state, self._show_status)
            elif item == "文献导入":
                page = LiteratureImportPage(self._handle_app_action)
            elif item == "去重审查":
                page = DeduplicationPage(self._handle_app_action)
            elif item == "筛选":
                page = ScreeningPage(self._handle_app_action)
            elif item == "数据提取":
                page = DataExtractionPage(self._handle_app_action)
            elif item == "Forest Plot":
                page = ForestPlotPage(self._project_state, self._handle_app_action)
            elif item == "Funnel Plot":
                page = FunnelPlotPage(self._project_state, self._handle_app_action)
            elif item == "Reporting":
                page = ReportingPage(self._project_state, self._handle_app_action)
            elif item == "项目管理":
                page = ProjectManagementPage(self._project_state, self._handle_toolbar_action)
            else:
                page = PlaceholderPage(item, PLACEHOLDER_DESCRIPTIONS[item])
            self._pages[item] = page
            self._stack.addWidget(page)

    def open_page(self, name: str) -> None:
        page = self._pages.get(name)
        if page is None:
            return
        self._stack.setCurrentWidget(page)
        self.statusBar().showMessage(f"{name} · 就绪")

    def _show_status(self, action: str) -> None:
        self.statusBar().showMessage(f"{action} · 当前为演示界面，真实功能将在后续接入", 3500)

    def _handle_app_action(self, action: str) -> None:
        lowered = action.lower()
        if action.startswith("Import") or "export" in lowered:
            log_project_event(self._project_state.project_dir, f"ui action attempt: {action}")
        self._show_status(action)

    def _handle_toolbar_action(self, action: str) -> None:
        if action in {"新建项目", "New Project"}:
            self._new_project()
        elif action in {"打开", "Open"}:
            self._open_project()
        elif action in {"保存", "Save", "Save Project"}:
            self._save_project()
        elif action in {"导出", "Export", "Export Project"}:
            export_project_attempt(self._project_state, action)
            self._show_status(f"{action} placeholder")
        elif action == "Open Project Folder":
            self._show_status("Open Project Folder placeholder")
        else:
            self._show_status(action)

    def _new_project(self) -> None:
        parent_dir = QFileDialog.getExistingDirectory(self, "Choose parent folder for meta_project")
        if not parent_dir:
            return
        name, accepted = QInputDialog.getText(self, "New Project", "Project name:")
        if not accepted:
            return
        self._project_state = create_project(parent_dir, name)
        self._rebuild_pages("项目管理")
        self.statusBar().showMessage(f"New project created · {self._project_state.project_dir}", 5000)

    def _open_project(self) -> None:
        filename, _filter = QFileDialog.getOpenFileName(
            self,
            "Open project.json",
            "",
            f"Meta project ({PROJECT_JSON});;JSON files (*.json);;All files (*)",
        )
        if not filename:
            return
        self._project_state = open_project(filename)
        self._rebuild_pages("首页")
        self.statusBar().showMessage(f"Project opened · {self._project_state.project_name}", 5000)

    def _save_project(self) -> None:
        self._project_state = save_project(self._project_state)
        current = self._current_page_name()
        self._rebuild_pages(current)
        self.statusBar().showMessage(f"Project saved · {self._project_state.project_dir / PROJECT_JSON}", 5000)

    def _rebuild_pages(self, active_page: str) -> None:
        while self._stack.count():
            widget = self._stack.widget(0)
            self._stack.removeWidget(widget)
            widget.deleteLater()
        self._pages.clear()
        self._install_pages()
        self.open_page(active_page if active_page in self._pages else "首页")

    def _current_page_name(self) -> str:
        current = self._stack.currentWidget()
        for name, widget in self._pages.items():
            if widget is current:
                return name
        return "首页"
