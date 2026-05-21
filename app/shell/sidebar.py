from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

from app.shared.semantic_keys import NavKey

try:
    from PySide6.QtCore import QSize
    from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout
    from app.app_identity import MODULE_ICON_PATHS, load_module_icon
except Exception:  # pragma: no cover
    QSize = None
    MODULE_ICON_PATHS = {}
    load_module_icon = None
    QFrame = QLabel = QPushButton = QVBoxLayout = None


@dataclass(frozen=True)
class SidebarItem:
    key: str
    label: str
    semantic_key: str


COMMON_SIDEBAR_ITEMS = (
    SidebarItem("dashboard", "Dashboard", NavKey.DASHBOARD.value),
    SidebarItem("bioinformatics", "Bioinformatics / 生信分析", NavKey.BIOINFORMATICS.value),
    SidebarItem("meta_analysis", "Meta Analysis / Meta 分析", NavKey.META_ANALYSIS.value),
    SidebarItem("labtools", "LabTools / 实验工具", NavKey.LABTOOLS.value),
    SidebarItem("settings", "设置中心", NavKey.SETTINGS.value),
    SidebarItem("test_feedback", "Test Feedback / 测试反馈", NavKey.TEST_FEEDBACK.value),
    SidebarItem("about", "About / 关于", NavKey.ABOUT.value),
)

SIDEBAR_MODULE_ICON_KEYS = {
    "bioinformatics": "module.bioinformatics",
    "meta_analysis": "module.meta_analysis",
    "labtools": "module.labtools",
    "settings": "module.settings",
}


if QFrame is not None:

    class SidebarWidget(QFrame):
        def __init__(
            self,
            *,
            on_dashboard: Callable[[], None],
            on_bioinformatics: Callable[[], None],
            on_meta_analysis: Callable[[], None],
            on_labtools: Callable[[], None],
            on_settings: Callable[[], None],
            on_test_feedback: Callable[[], None],
            on_about: Callable[[], None],
        ) -> None:
            super().__init__()
            self.setFixedWidth(220)
            self.setStyleSheet(
                "QFrame { background: #F8FAFC; border-right: 1px solid #D8DEE9; }"
                "QPushButton { text-align: left; padding: 8px 10px; border: 0; border-radius: 6px; }"
                "QPushButton:hover { background: #EAF0F7; }"
            )
            layout = QVBoxLayout(self)
            layout.setContentsMargins(12, 14, 12, 14)
            layout.setSpacing(8)
            title = QLabel("萤火虫 / Firefly")
            title.setStyleSheet("font-size: 18px; font-weight: 700;")
            layout.addWidget(title)
            for item, callback in (
                (COMMON_SIDEBAR_ITEMS[0], on_dashboard),
                (COMMON_SIDEBAR_ITEMS[1], on_bioinformatics),
                (COMMON_SIDEBAR_ITEMS[2], on_meta_analysis),
                (COMMON_SIDEBAR_ITEMS[3], on_labtools),
                (COMMON_SIDEBAR_ITEMS[4], on_settings),
            ):
                button = QPushButton(item.label)
                button.setObjectName("sidebarButton")
                button.setProperty("navKey", item.semantic_key)
                button.setProperty("semanticKey", item.semantic_key)
                button.setProperty("pageKey", item.key)
                button.setProperty("usabilityRole", "primary_navigation")
                button.setAccessibleName(item.label)
                button.setToolTip(item.label)
                button.setMinimumHeight(36)
                module_icon_key = SIDEBAR_MODULE_ICON_KEYS.get(item.key)
                if module_icon_key is not None:
                    icon = load_module_icon(module_icon_key)
                    if not icon.isNull():
                        button.setIcon(icon)
                        button.setIconSize(QSize(18, 18))
                    button.setProperty("moduleKey", module_icon_key)
                    button.setProperty("iconSource", str(MODULE_ICON_PATHS.get(module_icon_key, "")))
                    button.setProperty("iconFallback", icon.isNull())
                button.clicked.connect(callback)
                layout.addWidget(button)
            layout.addStretch(1)
            for item, callback in (
                (COMMON_SIDEBAR_ITEMS[5], on_test_feedback),
                (COMMON_SIDEBAR_ITEMS[6], on_about),
            ):
                button = QPushButton(item.label)
                button.setObjectName("sidebarAuxButton")
                button.setProperty("navKey", item.semantic_key)
                button.setProperty("semanticKey", item.semantic_key)
                button.setProperty("pageKey", item.key)
                button.setProperty("usabilityRole", "auxiliary_navigation")
                button.setAccessibleName(item.label)
                button.setToolTip(item.label)
                button.setMinimumHeight(36)
                button.clicked.connect(callback)
                layout.addWidget(button)
            footer = QLabel("Developer Preview")
            footer.setStyleSheet("color: #64748B;")
            layout.addWidget(footer)

else:

    class SidebarWidget:  # type: ignore[no-redef]
        pass
