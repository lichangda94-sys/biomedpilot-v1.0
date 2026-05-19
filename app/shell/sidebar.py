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
    SidebarItem("bioinformatics", "生信分析"),
    SidebarItem("meta_analysis", "Meta 分析"),
    SidebarItem("settings", "设置中心"),
    SidebarItem("testing", "测试入口"),
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
            self.setStyleSheet(
                "QFrame { background: #F8FAFC; border-right: 1px solid #D8DEE9; }"
                "QPushButton { text-align: left; padding: 8px 10px; border: 0; border-radius: 6px; }"
                "QPushButton:hover { background: #EAF0F7; }"
            )
            layout = QVBoxLayout(self)
            layout.setContentsMargins(12, 14, 12, 14)
            layout.setSpacing(8)
            title = QLabel("BioMedPilot")
            title.setStyleSheet("font-size: 18px; font-weight: 700;")
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
            footer.setStyleSheet("color: #64748B;")
            layout.addWidget(footer)

else:

    class SidebarWidget:  # type: ignore[no-redef]
        pass
