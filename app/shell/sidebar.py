from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

try:
    from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout
except Exception:  # pragma: no cover
    QFrame = QLabel = QPushButton = QVBoxLayout = None


@dataclass(frozen=True)
class SidebarItem:
    key: str
    label: str


COMMON_SIDEBAR_ITEMS = (
    SidebarItem("dashboard", "Dashboard"),
    SidebarItem("bioinformatics", "Bioinformatics / 生信分析"),
    SidebarItem("meta_analysis", "Meta Analysis / Meta 分析"),
    SidebarItem("labtools", "LabTools / 实验工具"),
    SidebarItem("settings", "设置中心"),
    SidebarItem("test_feedback", "Test Feedback / 测试反馈"),
    SidebarItem("about", "About / 关于"),
)


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
            for label, callback in (
                ("Dashboard", on_dashboard),
                ("Bioinformatics / 生信分析", on_bioinformatics),
                ("Meta Analysis / Meta 分析", on_meta_analysis),
                ("LabTools / 实验工具", on_labtools),
                ("设置中心", on_settings),
            ):
                button = QPushButton(label)
                button.setObjectName("sidebarButton")
                button.clicked.connect(callback)
                layout.addWidget(button)
            layout.addStretch(1)
            for label, callback in (
                ("Test Feedback / 测试反馈", on_test_feedback),
                ("About / 关于", on_about),
            ):
                button = QPushButton(label)
                button.setObjectName("sidebarAuxButton")
                button.clicked.connect(callback)
                layout.addWidget(button)
            footer = QLabel("Developer Preview")
            footer.setStyleSheet("color: #64748B;")
            layout.addWidget(footer)

else:

    class SidebarWidget:  # type: ignore[no-redef]
        pass
