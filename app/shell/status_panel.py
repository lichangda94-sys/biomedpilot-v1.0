from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from app.shared.environment.checks import EnvironmentStatus


class StatusPanel(QFrame):
    def __init__(self, environment: EnvironmentStatus, test_mode_label: str) -> None:
        super().__init__()
        self.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(self)
        header = QLabel("本地环境状态")
        header.setStyleSheet("font-weight: 700;")
        layout.addWidget(header)
        for line in (
            f"Python: {environment.python_version}",
            f"PySide6: {'可用' if environment.pyside6_available else '不可用'}",
            f"R 环境: {environment.r_status}",
            f"存储目录: {environment.storage_root}",
            test_mode_label,
        ):
            label = QLabel(line)
            label.setWordWrap(True)
            layout.addWidget(label)
        layout.addStretch(1)

