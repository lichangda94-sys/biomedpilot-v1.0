from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from app_meta.ui.icon_registry import meta_icon
from app_meta.ui.theme import Theme


TOOLBAR_ICONS = {
    "新建项目": "new_project",
    "打开": "open_project",
    "保存": "save_project",
    "导出": "export_report",
    "分享": "share",
    "报告": "reporting",
}


class TopToolbar(QFrame):
    def __init__(self, on_action: Callable[[str], None], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background: {Theme.background}; border: 0;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        for label in ("新建项目", "打开", "保存", "导出", "分享"):
            button = QPushButton(label)
            button.setMinimumHeight(36)
            button.setIcon(meta_icon(TOOLBAR_ICONS[label]))
            button.setIconSize(QSize(18, 18))
            if label == "新建项目":
                button.setObjectName("primaryButton")
            button.clicked.connect(lambda checked=False, name=label: on_action(name))
            layout.addWidget(button)

        report = QPushButton("报告")
        report.setMinimumHeight(36)
        report.setIcon(meta_icon(TOOLBAR_ICONS["报告"]))
        report.setIconSize(QSize(18, 18))
        report.clicked.connect(lambda: on_action("报告"))
        layout.addWidget(report)

        layout.addStretch(1)
        search = QLineEdit()
        search.setPlaceholderText("搜索（⌘F）")
        search.setFixedWidth(260)
        search.setMinimumHeight(36)
        layout.addWidget(search)

        for symbol, icon_name in (("", "help"), ("", "notification"), ("JD", None)):
            chip = QLabel(symbol)
            chip.setAlignment(Qt.AlignCenter)
            chip.setFixedSize(34, 34)
            if icon_name:
                chip.setPixmap(meta_icon(icon_name).pixmap(QSize(18, 18)))
            chip.setStyleSheet(
                f"background: {Theme.card}; border: 1px solid {Theme.border}; border-radius: 17px; color: {Theme.muted};"
            )
            layout.addWidget(chip)
