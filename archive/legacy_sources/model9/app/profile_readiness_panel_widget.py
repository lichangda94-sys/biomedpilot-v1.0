from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from reporting.profile_readiness import (
    READINESS_DISCLAIMER,
    ProfileReadinessDashboard,
)


class ProfileReadinessPanelWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title = QLabel("Profile Analysis Readiness")
        self._title.setObjectName("sectionTitle")
        self._disclaimer = QLabel(READINESS_DISCLAIMER)
        self._disclaimer.setObjectName("mutedLabel")
        self._disclaimer.setWordWrap(True)
        self._empty_label = QLabel("No profile policy readiness summaries available yet.")
        self._empty_label.setObjectName("mutedLabel")

        self._table = QTableWidget(0, 8)
        self._table.setObjectName("profileReadinessTable")
        self._table.setHorizontalHeaderLabels(
            [
                "Profile",
                "Status",
                "Supported Now",
                "Policy Ready",
                "Unsupported",
                "Unimplemented",
                "Warnings",
                "Recommended Next Action",
            ]
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self._title)
        layout.addWidget(self._disclaimer)
        layout.addWidget(self._empty_label)
        layout.addWidget(self._table)
        self.set_dashboard(ProfileReadinessDashboard())

    def set_dashboard(self, dashboard: ProfileReadinessDashboard) -> None:
        self._table.setRowCount(len(dashboard.rows))
        self._empty_label.setVisible(not dashboard.rows)
        self._table.setVisible(bool(dashboard.rows))
        for row_index, row in enumerate(dashboard.rows):
            values = [
                row.profile,
                row.support_status,
                "yes" if row.supported_now else "no",
                "yes" if row.policy_ready else "no",
                row.unsupported,
                row.unimplemented,
                row.warnings,
                row.recommended_next_action,
            ]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(row_index, column_index, item)

    def disclaimer_text(self) -> str:
        return self._disclaimer.text()

    def empty_state_text(self) -> str:
        return self._empty_label.text()

    def readiness_cell_text(self, row: int, column: int) -> str:
        item = self._table.item(row, column)
        return item.text() if item is not None else ""
