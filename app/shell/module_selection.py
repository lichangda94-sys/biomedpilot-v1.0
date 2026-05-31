from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QSize, Signal, Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.app_identity import MODULE_ICON_PATHS, load_module_pixmap, load_ui02_module_selection_icon, load_ui02_module_selection_pixmap
from app.shell.dashboard import DashboardModel
from app.shell.login import LocalSession
from app.shared.semantic_keys import BrandKey, ModuleKey, NavKey
from app.shared.ui_components import make_action_button
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
        self.setProperty("designTokenSet", "dashboard_target_figma_make")
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
        root.setContentsMargins(26, 0, 26, 24)
        root.setSpacing(SPACING["lg"])

        root.addWidget(self._build_header())
        root.addWidget(self._build_module_panel())
        root.addWidget(self._build_recent_projects_card())
        root.addStretch(1)
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _build_header(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("dashboardHeader")
        frame.setProperty("uiPrimitive", "dashboard_hero")
        frame.setProperty("designReference", "figma_make_dashboard_target")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 14, 0, 14)
        layout.setSpacing(SPACING["lg"])

        title_col = QVBoxLayout()
        title_col.setSpacing(3)
        title_row = QHBoxLayout()
        title_row.setSpacing(SPACING["sm"])
        title = QLabel("萤火虫 工作台/ Firefly Workbench")
        title.setObjectName("dashboardTitle")
        title.setProperty("semanticKey", BrandKey.PRIMARY.value)
        title_row.addWidget(title)
        preview = QLabel("Developer Preview · 本地测试版")
        preview.setObjectName("previewBadge")
        title_row.addWidget(preview)
        title_row.addStretch(1)
        subtitle = QLabel("欢迎回来！这是您本地生物医学研究的统一工作台。")
        subtitle.setObjectName("dashboardSubtitle")
        subtitle.setProperty("semanticKey", BrandKey.SECONDARY.value)
        subtitle.setWordWrap(True)
        title_col.addLayout(title_row)
        title_col.addWidget(subtitle)
        layout.addLayout(title_col, 1)

        layout.addWidget(self._header_icon_button("通知", "developer_preview"), 0, Qt.AlignVCenter)
        layout.addWidget(self._header_icon_button("帮助", "settings"), 0, Qt.AlignVCenter)
        self._user_badge = QLabel("")
        self._user_badge.setObjectName("sessionBadge")
        self._user_badge.setAlignment(Qt.AlignCenter)
        self._user_badge.setMinimumHeight(36)
        self._user_badge.setMaximumHeight(36)
        self._user_badge.setMinimumWidth(128)
        layout.addWidget(self._user_badge, 0, Qt.AlignVCenter)
        self._tier_label = QLabel("Developer Preview / 本地测试版")
        self._tier_label.setObjectName("previewBadge")
        self._tier_label.setVisible(False)
        self._license_label = QLabel("")
        self._license_label.setVisible(False)
        return frame

    def _build_module_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("dashboardModulePanel")
        frame.setProperty("uiPrimitive", "dashboard_module_panel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        module_grid = QGridLayout()
        module_grid.setContentsMargins(0, 0, 0, 0)
        module_grid.setHorizontalSpacing(18)
        module_grid.setVerticalSpacing(18)
        module_grid.addWidget(
            self._module_card(
                title="生信分析",
                english_title="BIOINFORMATICS",
                description="数据来源、检查准备、分组设计、分析任务、结果与报告。",
                button_text="进入模块",
                object_name="bioModuleButton",
                icon_key="bioinformatics",
                module_key=ModuleKey.BIOINFORMATICS.value,
                nav_key=NavKey.BIOINFORMATICS.value,
                callback=self.open_bioinformatics_requested.emit,
            ),
            0,
            0,
        )
        module_grid.addWidget(
            self._module_card(
                title="Meta 分析",
                english_title="META ANALYSIS",
                description="研究问题、检索、筛选、数据提取、质量评价、统计分析。",
                button_text="进入模块",
                object_name="metaModuleButton",
                icon_key="meta_analysis",
                module_key=ModuleKey.META_ANALYSIS.value,
                nav_key=NavKey.META_ANALYSIS.value,
                callback=self.open_meta_analysis_requested.emit,
            ),
            0,
            1,
        )
        module_grid.addWidget(
            self._module_card(
                title="实验工具",
                english_title="LABTOOLS",
                description="通用计算器、试剂制备、实验模块工具集合。",
                button_text="进入模块",
                object_name="labtoolsModuleButton",
                icon_key="labtools",
                module_key=ModuleKey.LABTOOLS.value,
                nav_key=NavKey.LABTOOLS.value,
                callback=self.open_labtools_requested.emit,
            ),
            0,
            2,
        )
        for column in range(3):
            module_grid.setColumnStretch(column, 1)
        layout.addLayout(module_grid)
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
        frame.setMinimumHeight(295)
        frame.setToolTip(f"点击进入{title}")
        frame.clicked.connect(callback)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(9)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(SPACING["sm"])
        icon_label = QLabel()
        icon_label.setObjectName("moduleIcon")
        icon_label.setFixedSize(72, 72)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_source = MODULE_ICON_PATHS.get(module_key) or MODULE_ICON_PATHS.get(icon_key)
        icon = load_module_pixmap(module_key, 56)
        if icon.isNull():
            icon = load_ui02_module_selection_pixmap("workspace", 56)
            icon_label.setProperty("iconFallback", True)
        else:
            icon_label.setProperty("iconFallback", False)
        icon_label.setProperty("moduleKey", module_key)
        icon_label.setProperty("iconSource", str(icon_source) if icon_source is not None else "")
        icon_label.setPixmap(icon)
        icon_label.setVisible(not icon.isNull())
        top_row.addWidget(icon_label, 0, Qt.AlignLeft)
        top_row.addStretch(1)
        top_row.addWidget(self._testing_pill(), 0, Qt.AlignTop)

        title_label = QLabel(title)
        title_label.setObjectName("moduleTitle")
        title_label.setProperty("moduleKey", module_key)
        title_label.setProperty("semanticKey", module_key)
        legacy_label = QLabel(_legacy_module_title(module_key))
        legacy_label.setObjectName("moduleLegacyTitle")
        legacy_label.setVisible(False)
        english = QLabel(english_title)
        english.setObjectName("moduleEnglishTitle")
        english.setProperty("moduleKey", module_key)
        description_label = QLabel(description)
        description_label.setObjectName("moduleDescription")
        description_label.setWordWrap(True)

        button = QPushButton(button_text)
        button.setObjectName(object_name)
        button.setProperty("uiPrimitive", "button")
        button.setProperty("buttonRole", "dashboard_module_action")
        button.setProperty("buttonSize", "regular")
        button.setProperty("actionKey", nav_key)
        button.setProperty("semanticState", "testing")
        button.setProperty("formalActionEnabled", False)
        button.setProperty("fileWriteAllowed", False)
        button.setProperty("moduleKey", module_key)
        button.setProperty("navKey", nav_key)
        button.setProperty("semanticKey", module_key)
        button.setProperty("usabilityRole", "module_entry_action")
        button.setAccessibleName(button_text)
        button.setIcon(load_ui02_module_selection_icon("workspace"))
        button.setIconSize(QSize(18, 18))
        button.setMinimumHeight(44)
        button.setToolTip(f"进入{title}")
        button.clicked.connect(callback)

        layout.addLayout(top_row)
        layout.addSpacing(SPACING["sm"])
        layout.addWidget(title_label)
        layout.addWidget(legacy_label)
        layout.addWidget(english)
        layout.addSpacing(SPACING["md"])
        layout.addWidget(description_label)
        layout.addStretch(1)
        layout.addWidget(button)
        if object_name == "labtoolsModuleButton":
            legacy_button = QPushButton(button_text, frame)
            legacy_button.setObjectName("labToolsModuleButton")
            legacy_button.setProperty("moduleKey", module_key)
            legacy_button.setProperty("navKey", nav_key)
            legacy_button.setProperty("semanticKey", module_key)
            legacy_button.clicked.connect(callback)
            legacy_button.setVisible(False)
        return frame

    def _build_recent_projects_card(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("dashboardRecentProjectsCard")
        frame.setProperty("uiPrimitive", "dashboard_recent_projects")
        frame.setProperty("projectCenter", False)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        title_row = QHBoxLayout()
        title_row.setContentsMargins(18, 14, 18, 12)
        title_row.setSpacing(SPACING["sm"])
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("最近项目 / Recent Projects")
        title.setObjectName("dashboardSectionTitle")
        subtitle = QLabel("继续打开最近使用的本地研究项目。")
        subtitle.setObjectName("dashboardSectionSubtitle")
        subtitle.setWordWrap(True)
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        title_row.addLayout(title_col, 1)
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

        table = self._recent_projects_table()
        table.setProperty("dashboardOnly", True)
        layout.addWidget(table)
        view_all = QPushButton("查看全部项目（12）")
        view_all.setObjectName("dashboardViewAllProjectsButton")
        view_all.setEnabled(False)
        view_all.setToolTip("Project Center 尚未作为正式项目中心开放。")
        layout.addWidget(view_all, 0, Qt.AlignHCenter)
        return frame

    def _recent_projects_table(self) -> QTableWidget:
        rows = self._recent_project_rows()
        table = QTableWidget(len(rows), 5)
        table.setObjectName("dashboardRecentProjectsTable")
        table.setProperty("uiPrimitive", "project_recent_table")
        table.setProperty("readOnly", True)
        table.setProperty("createsProject", False)
        table.setProperty("opensProject", False)
        table.setProperty("horizontalOverflow", True)
        table.setProperty("fakeRecords", not self._dashboard.recent_projects)
        table.setHorizontalHeaderLabels(("项目名称", "模块类型", "最近修改时间", "状态", "操作"))
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setAlternatingRowColors(False)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setFocusPolicy(Qt.NoFocus)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setMinimumHeight(356)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                item = QTableWidgetItem(value)
                item.setFlags(Qt.ItemIsEnabled)
                if column_index in (2, 4):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                table.setItem(row_index, column_index, item)
            table.setRowHeight(row_index, 52)
        return table

    def _recent_project_rows(self) -> list[tuple[str, str, str, str, str]]:
        projects = list(self._dashboard.recent_projects[:5])
        if projects:
            return [
                (
                    project.project_name,
                    "生信分析" if project.project_type == "bioinformatics" else "Meta 分析",
                    project.updated_at,
                    "测试中 testing",
                    "打开",
                )
                for project in projects
            ]
        return [
            ("BRCA 单细胞表达分析", "生信分析", "2025-05-20 14:30", "测试中 testing", "打开"),
            ("肺癌生存 Meta 分析", "Meta 分析", "2025-05-19 09:15", "测试中 testing", "打开"),
            ("Western Blot 灰度分析记录", "实验工具", "2025-05-18 17:22", "测试中 testing", "打开"),
            ("蛋白浓度计算与配制", "实验工具", "2025-05-17 16:05", "测试中 testing", "打开"),
            ("GEO 数据预处理流程", "生信分析", "2025-05-16 11:48", "测试中 testing", "打开"),
        ]

    def _testing_pill(self) -> QLabel:
        pill = QLabel("● 测试中 testing")
        pill.setObjectName("dashboardTestingPill")
        pill.setAlignment(Qt.AlignCenter)
        pill.setProperty("uiPrimitive", "status_chip")
        pill.setProperty("statusKey", "testing")
        pill.setProperty("semanticKey", NavKey.DASHBOARD.value)
        return pill

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

    def _header_icon_button(self, text: str, icon_key: str) -> QPushButton:
        button = make_action_button(text, role="secondary", size="small", semantic_state="available")
        button.setObjectName("dashboardHeaderIconButton")
        button.setMinimumSize(40, 40)
        button.setMaximumSize(44, 44)
        button.setToolTip(text)
        button.setText("")
        button.setIcon(load_ui02_module_selection_icon(icon_key))
        button.setIconSize(QSize(18, 18))
        button.setAccessibleName(text)
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


def _legacy_module_title(module_key: str) -> str:
    if module_key == ModuleKey.BIOINFORMATICS.value:
        return "Bioinformatics / 生信分析"
    if module_key == ModuleKey.META_ANALYSIS.value:
        return "Meta Analysis / Meta 分析"
    if module_key == ModuleKey.LABTOOLS.value:
        return "LabTools / 实验工具"
    return ""
