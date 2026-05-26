from __future__ import annotations

from collections.abc import Callable

from app.shared.semantic_keys import NavKey
from app.shared.ui_components.primitives import AppSidebar, AppSidebarItem

try:
    from PySide6.QtWidgets import QPushButton
except Exception:  # pragma: no cover
    QPushButton = None


SidebarItem = AppSidebarItem


COMMON_SIDEBAR_ITEMS = (
    SidebarItem("dashboard", "工作台 / Dashboard", NavKey.DASHBOARD.value),
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


if QPushButton is not None:

    class SidebarWidget(AppSidebar):
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
            callbacks = {
                "dashboard": on_dashboard,
                "bioinformatics": on_bioinformatics,
                "meta_analysis": on_meta_analysis,
                "labtools": on_labtools,
                "settings": on_settings,
                "test_feedback": on_test_feedback,
                "about": on_about,
            }
            items = tuple(
                AppSidebarItem(
                    key=item.key,
                    label=item.label,
                    semantic_key=item.semantic_key,
                    icon_key=SIDEBAR_MODULE_ICON_KEYS.get(item.key, ""),
                    usability_role="primary_navigation" if index < 5 else "auxiliary_navigation",
                )
                for index, item in enumerate(COMMON_SIDEBAR_ITEMS)
            )
            super().__init__(
                items=items,
                callbacks=callbacks,
                title="萤火虫 Firefly\nBioMedPilot 医研智析",
                footer="Developer Preview\n本地测试版\nv0.1.0 internal beta",
                active_key="dashboard",
                width=248,
            )

else:

    class SidebarWidget:  # type: ignore[no-redef]
        pass
