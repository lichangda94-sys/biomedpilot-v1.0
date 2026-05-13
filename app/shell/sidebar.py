from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

try:
    from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout
except Exception:  # pragma: no cover
    QFrame = QLabel = QPushButton = QVBoxLayout = None

from app.shared.ui import helper_text_qss, page_title_qss, shell_sidebar_qss


@dataclass(frozen=True)
class SidebarItem:
    key: str
    label: str


COMMON_SIDEBAR_ITEMS = (
    SidebarItem("dashboard", "Dashboard"),
    SidebarItem("bioinformatics", "生信分析"),
    SidebarItem("meta_analysis", "Meta 分析"),
    SidebarItem("project_center", "项目中心"),
    SidebarItem("data_center", "数据中心"),
    SidebarItem("task_center", "任务中心"),
    SidebarItem("report_center", "报告中心"),
    SidebarItem("settings", "设置中心"),
    SidebarItem("environment", "本地环境检查"),
    SidebarItem("testing", "测试入口"),
    SidebarItem("packaging", "打包入口"),
)


if QFrame is not None:

    class SidebarWidget(QFrame):
        def __init__(
            self,
            *,
            on_dashboard: Callable[[], None],
            on_bioinformatics: Callable[[], None],
            on_meta_analysis: Callable[[], None],
            on_settings: Callable[[], None],
            on_testing: Callable[[], None],
        ) -> None:
            super().__init__()
            self.setFixedWidth(190)
            self.setStyleSheet(shell_sidebar_qss())
            layout = QVBoxLayout(self)
            layout.setContentsMargins(12, 14, 12, 14)
            layout.setSpacing(8)
            title = QLabel("BioMedPilot")
            title.setStyleSheet(page_title_qss())
            layout.addWidget(title)
            for label, callback in (
                ("Dashboard", on_dashboard),
                ("生信分析", on_bioinformatics),
                ("Meta 分析", on_meta_analysis),
                ("设置中心", on_settings),
                ("测试模式", on_testing),
            ):
                button = QPushButton(label)
                button.clicked.connect(callback)
                layout.addWidget(button)
            layout.addStretch(1)
            footer = QLabel("测试模式")
            footer.setStyleSheet(helper_text_qss())
            layout.addWidget(footer)

else:

    class SidebarWidget:  # type: ignore[no-redef]
        pass
