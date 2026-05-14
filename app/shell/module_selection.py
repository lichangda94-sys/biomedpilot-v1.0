from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QSize, Signal, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.app_identity import icon_asset_summary, load_module_pixmap, load_ui02_module_selection_icon, load_ui02_module_selection_pixmap
from app.shell.dashboard import DashboardModel
from app.shell.login import LocalSession
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
        self._tier_label.setText(f"当前账号等级：{display['tier']}")
        self._license_label.setText(f"License 状态：{display['license_status']}")

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
                title="生信分析模块",
                english_title="Bioinformatics Analyze Module",
                description="用于 GEO、TCGA、GTEx、本地表达矩阵、差异分析、富集分析、相关性分析、生存分析和报告生成。",
                button_text="进入生信分析模块",
                object_name="bioModuleButton",
                icon_key="bioinformatics",
                callback=self.open_bioinformatics_requested.emit,
            )
        )
        module_row.addWidget(
            self._module_card(
                title="Meta 分析模块",
                english_title="Meta Analysis Module",
                description="按中文 18 步工作流测试 PICO、检索策略、文献获取、文献库、去重、全文、提取、质量评价和分析计划；统计、图表、正式报告保持 testing-level / 待开发。",
                button_text="进入 Meta 分析模块",
                object_name="metaModuleButton",
                icon_key="meta_analysis",
                callback=self.open_meta_analysis_requested.emit,
            )
        )
        module_row.addWidget(
            self._module_card(
                title="LabTools 模块",
                english_title="LabTools Module",
                description="仅接入 shared ImageJ/Fiji 本机引擎检测和图像能力边界提示；未启用 WB/gel、agarose、自动 ROI、细胞计数、pathology 或真实图像算法。",
                button_text="进入 LabTools 模块",
                object_name="labToolsModuleButton",
                icon_key="labtools",
                callback=self.open_labtools_requested.emit,
            )
        )

        info_row = QHBoxLayout()
        info_row.setSpacing(SPACING["md"])
        info_row.addWidget(self._build_recent_projects_card(), 1)
        info_row.addWidget(self._build_support_panel(), 1)

        root.addLayout(module_row)
        root.addLayout(info_row)
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
        title = QLabel("BioMedPilot / 医研智析")
        title.setObjectName("dashboardTitle")
        subtitle = QLabel("统一模块入口，选择一个工作区开始本地测试。")
        subtitle.setObjectName("dashboardSubtitle")
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
        preview = QLabel("Developer Preview / 本地测试版")
        preview.setObjectName("previewBadge")
        layout.addWidget(preview)
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
        callback: Callable[[], None],
    ) -> QFrame:
        frame = ModuleEntryCard()
        frame.setObjectName("moduleCard")
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
        icon = load_module_pixmap(icon_key, 60)
        icon_label.setPixmap(icon)
        icon_label.setVisible(not icon.isNull())
        title_label = QLabel(title)
        title_label.setObjectName("moduleTitle")
        english = QLabel(english_title)
        english.setObjectName("moduleEnglishTitle")
        accent = QLabel("")
        accent.setObjectName("moduleAccentLine")
        accent.setFixedHeight(4)
        accent.setMaximumWidth(96)
        description_label = QLabel(description)
        description_label.setObjectName("moduleDescription")
        description_label.setWordWrap(True)

        button = QPushButton(button_text)
        button.setObjectName(object_name)
        button.setIcon(load_ui02_module_selection_icon("workspace"))
        button.setIconSize(QSize(18, 18))
        button.setMinimumWidth(168)
        button.setToolTip(f"进入{title}")
        button.clicked.connect(callback)

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(english)
        layout.addWidget(accent)
        layout.addSpacing(SPACING["sm"])
        layout.addWidget(description_label)
        layout.addWidget(button, alignment=Qt.AlignLeft)
        return frame

    def _build_recent_projects_card(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("supportCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        layout.setSpacing(SPACING["sm"])
        layout.addLayout(self._title_row("最近项目", "recent_projects"))
        projects = list(self._dashboard.recent_projects[:3])
        if not projects:
            layout.addLayout(self._support_line_with_icon("暂无最近项目，本阶段保留入口占位。", "project_entry"))
        for project in projects:
            layout.addLayout(self._support_line_with_icon(project.display_label(), "project_entry"))
        return frame

    def _build_support_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("supportCard")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])

        layout.addLayout(self._title_row("本地测试信息", "settings"))
        self._tier_label = self._support_line("")
        self._license_label = self._support_line("")
        layout.addWidget(self._tier_label)
        layout.addWidget(self._license_label)
        layout.addWidget(self._support_line("订阅 / VIP 服务：预留功能"))
        layout.addWidget(self._support_line("设置入口：占位"))
        icon_summary = icon_asset_summary()
        layout.addWidget(
            self._support_line(
                f"图标资源：已生成 {icon_summary['generated']} / {icon_summary['total']}；"
                f"待生成 {icon_summary['pending']}。详情见设置中心。"
            )
        )
        layout.addSpacing(SPACING["md"])

        layout.addLayout(self._title_row("本地环境状态", "local_environment"))
        environment = self._dashboard.environment
        layout.addWidget(self._support_line(f"Python：{environment.python_version}"))
        layout.addWidget(self._support_line(f"PySide6：{'可用' if environment.pyside6_available else '不可用'}"))
        layout.addWidget(self._support_line("环境检查详情：后续接入设置中心。"))
        layout.addStretch(1)

        settings_button = QPushButton("设置入口（预留）")
        settings_button.setObjectName("secondaryButton")
        settings_button.setIcon(load_ui02_module_selection_icon("settings"))
        settings_button.setIconSize(QSize(18, 18))
        settings_button.setEnabled(False)
        logout_button = QPushButton("退出登录")
        logout_button.setObjectName("logoutButton")
        logout_button.setIcon(load_ui02_module_selection_icon("logout"))
        logout_button.setIconSize(QSize(18, 18))
        logout_button.clicked.connect(self.logout_requested.emit)
        layout.addWidget(settings_button)
        layout.addWidget(logout_button)
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
