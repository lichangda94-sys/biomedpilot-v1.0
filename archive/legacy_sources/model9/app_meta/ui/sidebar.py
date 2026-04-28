from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget

from app_meta.core.project_state import MetaProjectState
from app_meta.ui.components import ProjectProgressCard, SidebarItem


NAV_ITEMS = (
    "首页",
    "PICO/Search",
    "文献导入",
    "去重审查",
    "筛选",
    "数据提取",
    "分析设置",
    "Forest Plot",
    "Funnel Plot",
    "Reporting",
    "项目管理",
)

NAV_ICON_NAMES = {
    "首页": "home",
    "PICO/Search": "pico",
    "文献导入": "literature_import",
    "去重审查": "deduplication",
    "筛选": "screening",
    "数据提取": "data_extraction",
    "分析设置": "analysis_settings",
    "Forest Plot": "forest_plot",
    "Funnel Plot": "funnel_plot",
    "Reporting": "reporting",
    "项目管理": "project_management",
}


class Sidebar(QFrame):
    def __init__(
        self,
        on_select: Callable[[str], None],
        project_state: MetaProjectState,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(260)
        self._on_select = on_select
        self._buttons: dict[str, QPushButton] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 22, 18, 18)
        layout.setSpacing(8)

        brand = QLabel("BioMedPilot")
        brand.setStyleSheet("font-size: 22px; font-weight: 760;")
        subtitle = QLabel("Meta Analysis")
        subtitle.setObjectName("smallMuted")
        layout.addWidget(brand)
        layout.addWidget(subtitle)
        layout.addSpacing(18)

        for item in NAV_ITEMS:
            button = SidebarItem(item, NAV_ICON_NAMES[item])
            button.clicked.connect(lambda checked=False, name=item: self.select(name))
            self._buttons[item] = button
            layout.addWidget(button)

        layout.addStretch(1)
        progress = ProjectProgressCard(project_state)
        progress.settings_button.clicked.connect(lambda: self._on_select("项目管理"))
        layout.addWidget(progress)
        self.select("首页")

    def select(self, name: str) -> None:
        for item, button in self._buttons.items():
            button.setChecked(item == name)
        self._on_select(name)
