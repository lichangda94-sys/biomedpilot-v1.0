from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from reporting.models import AnalysisSummaryTable


class ReportingSummaryWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._profile_label = QLabel("Profile: Not linked")
        self._profile_label.setObjectName("profileSourceLabel")

        self._table = QTableWidget(0, 8)
        self._table.setObjectName("analysisSummaryTable")
        self._table.setHorizontalHeaderLabels(
            [
                "Analysis ID",
                "Profile ID",
                "Profile Name",
                "Metric",
                "Model",
                "Studies",
                "Pooled Effect",
                "I2",
            ]
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self._profile_label)
        layout.addWidget(self._table)

    def set_analysis_summary(self, table: AnalysisSummaryTable) -> None:
        self._table.setRowCount(len(table.rows))
        if not table.rows:
            self._profile_label.setText("Profile: Not linked")
            return

        first_row = table.rows[0]
        self._profile_label.setText(self._profile_text(first_row.analysis_profile_id, first_row.analysis_profile_name))
        for row_index, row in enumerate(table.rows):
            values = [
                row.analysis_id,
                row.analysis_profile_id or "",
                row.analysis_profile_name,
                row.metric.value,
                row.model_type.value,
                str(row.study_count),
                f"{row.pooled_effect:.3f}",
                f"{row.i2:.1f}",
            ]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(row_index, column_index, item)

    def profile_source_text(self) -> str:
        return self._profile_label.text()

    def summary_cell_text(self, row: int, column: int) -> str:
        item = self._table.item(row, column)
        return item.text() if item is not None else ""

    def _profile_text(self, profile_id: str | None, profile_name: str) -> str:
        if profile_id is None:
            return "Profile: Not linked"
        if profile_name:
            return f"Profile: {profile_name} ({profile_id})"
        return f"Profile: {profile_id}"
