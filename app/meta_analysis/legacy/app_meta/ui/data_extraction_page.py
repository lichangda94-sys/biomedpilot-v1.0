from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app_meta.ui.components import SectionCard
from app_meta.ui.theme import Theme


@dataclass(frozen=True)
class IncludedStudy:
    study_id: str
    title: str
    year: str
    design: str


@dataclass(frozen=True)
class ExtractionRow:
    study_id: str
    treatment_events: str
    treatment_total: str
    control_events: str
    control_total: str
    effect_size: str
    notes: str


DEMO_STUDIES = (
    IncludedStudy("Yang 2023", "Corticosteroids for severe pneumonia", "2023", "Randomized trial"),
    IncludedStudy("Zhang 2022", "Hydrocortisone therapy in critical pneumonia", "2022", "Randomized trial"),
    IncludedStudy("Li 2021", "Steroid therapy and mortality in severe CAP", "2021", "Clinical trial"),
    IncludedStudy("Wang 2020", "Adjunctive corticosteroids in adult pneumonia", "2020", "Prospective cohort"),
)

DEMO_EXTRACTION_ROWS = (
    ExtractionRow("Yang 2023", "14", "96", "25", "101", "OR 0.52", "Primary endpoint at 28 days"),
    ExtractionRow("Zhang 2022", "18", "108", "29", "112", "OR 0.57", "Hospital mortality"),
    ExtractionRow("Li 2021", "9", "84", "18", "86", "OR 0.45", "All-cause mortality"),
)


class DataExtractionPage(QWidget):
    def __init__(self, on_action: Callable[[str], None]) -> None:
        super().__init__()
        self._on_action = on_action

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)
        root.addLayout(self._header())

        actions = QHBoxLayout()
        self.outcome_selector = QComboBox()
        self.outcome_selector.addItems(("死亡率（All-cause）", "临床治愈率", "ICU length of stay", "Adverse events"))
        actions.addWidget(QLabel("Outcome"))
        actions.addWidget(self.outcome_selector)
        actions.addStretch(1)
        for index, label in enumerate(("Add Study Row", "Add Outcome", "Validate Extraction", "Save Extraction Table")):
            button = QPushButton(label)
            if index == 2:
                button.setObjectName("primaryButton")
            button.clicked.connect(lambda checked=False, name=label: self._handle_action(name))
            actions.addWidget(button)
        root.addLayout(actions)

        body = QHBoxLayout()
        body.setSpacing(16)
        main = QVBoxLayout()
        main.setSpacing(16)
        main.addWidget(self._included_studies_card(), 1)
        main.addWidget(self._extraction_table_card(), 2)
        body.addLayout(main, 1)
        body.addWidget(self._validation_card())
        root.addLayout(body, 1)
        self._refresh_validation()

    def _header(self) -> QVBoxLayout:
        header = QVBoxLayout()
        title = QLabel("数据提取")
        title.setObjectName("pageTitle")
        subtitle = QLabel("结构化录入纳入研究、二分类结局样本量与事件数，并进行基础完整性检查")
        subtitle.setObjectName("muted")
        header.addWidget(title)
        header.addWidget(subtitle)
        return header

    def _included_studies_card(self) -> SectionCard:
        card = SectionCard("Included studies")
        self.studies_table = QTableWidget(len(DEMO_STUDIES), 4)
        self.studies_table.setHorizontalHeaderLabels(("Study ID", "Title", "Year", "Design"))
        self.studies_table.verticalHeader().setVisible(False)
        self.studies_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.studies_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.studies_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for row_index, study in enumerate(DEMO_STUDIES):
            for column_index, value in enumerate((study.study_id, study.title, study.year, study.design)):
                self.studies_table.setItem(row_index, column_index, QTableWidgetItem(value))
        card.layout.addWidget(self.studies_table)
        return card

    def _extraction_table_card(self) -> SectionCard:
        card = SectionCard("Binary outcome extraction")
        self.extraction_table = QTableWidget(len(DEMO_EXTRACTION_ROWS), 7)
        self.extraction_table.setHorizontalHeaderLabels(
            (
                "Study ID",
                "Treatment events",
                "Treatment total",
                "Control events",
                "Control total",
                "Effect size",
                "Notes",
            )
        )
        self.extraction_table.verticalHeader().setVisible(False)
        self.extraction_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.extraction_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.extraction_table.blockSignals(True)
        for row_index, row in enumerate(DEMO_EXTRACTION_ROWS):
            self._set_extraction_row(row_index, row)
        self.extraction_table.blockSignals(False)
        self.extraction_table.itemChanged.connect(lambda _item: self._refresh_validation())
        card.layout.addWidget(self.extraction_table, 1)
        return card

    def _validation_card(self) -> SectionCard:
        card = SectionCard("Validation")
        card.setFixedWidth(330)
        self.validation_rows: dict[str, QLabel] = {}
        for label in (
            "Missing sample size",
            "Missing event count",
            "Event count greater than total",
            "Duplicate study ID",
        ):
            row = QHBoxLayout()
            name = QLabel(label)
            name.setObjectName("smallMuted")
            value = QLabel("0")
            value.setAlignment(Qt.AlignRight)
            value.setStyleSheet("font-weight: 750;")
            row.addWidget(name)
            row.addWidget(value, 1)
            card.layout.addLayout(row)
            self.validation_rows[label] = value
        self.validation_status = QLabel("Extraction table is ready for validation.")
        self.validation_status.setWordWrap(True)
        self.validation_status.setStyleSheet(
            f"background: {Theme.primary_soft}; color: {Theme.primary}; border-radius: 10px; padding: 10px;"
        )
        card.layout.addWidget(self.validation_status)
        card.layout.addStretch(1)
        return card

    def _handle_action(self, action: str) -> None:
        if action == "Add Study Row":
            row = self.extraction_table.rowCount()
            self.extraction_table.insertRow(row)
            self._set_extraction_row(row, ExtractionRow("", "", "", "", "", "", ""))
            self.validation_status.setText("Blank study row added. Complete required sample size and event fields.")
        elif action == "Add Outcome":
            self.outcome_selector.addItem("New outcome draft")
            self.outcome_selector.setCurrentText("New outcome draft")
            self.validation_status.setText("New outcome draft added. Configure outcome details before analysis.")
        elif action == "Validate Extraction":
            self._refresh_validation(show_status=True)
        elif action == "Save Extraction Table":
            self.validation_status.setText("Extraction table saved as a draft in the current demo session.")
        self._on_action(action)

    def _set_extraction_row(self, row_index: int, row: ExtractionRow) -> None:
        values = (
            row.study_id,
            row.treatment_events,
            row.treatment_total,
            row.control_events,
            row.control_total,
            row.effect_size,
            row.notes,
        )
        for column_index, value in enumerate(values):
            self.extraction_table.setItem(row_index, column_index, QTableWidgetItem(value))

    def _refresh_validation(self, show_status: bool = False) -> None:
        issues = _validate_extraction_rows(self._table_rows())
        for label, value in issues.items():
            widget = self.validation_rows[label]
            widget.setText(str(value))
            widget.setStyleSheet(f"font-weight: 750; color: {Theme.danger if value else Theme.success};")
        total_issues = sum(issues.values())
        if show_status or total_issues:
            if total_issues:
                self.validation_status.setStyleSheet(
                    f"background: {Theme.danger_soft}; color: {Theme.danger}; border-radius: 10px; padding: 10px;"
                )
                self.validation_status.setText(f"{total_issues} validation issue(s) need review before analysis.")
            else:
                self.validation_status.setStyleSheet(
                    f"background: {Theme.success_soft}; color: {Theme.success}; border-radius: 10px; padding: 10px;"
                )
                self.validation_status.setText("No validation issues detected in the current extraction table.")

    def _table_rows(self) -> list[ExtractionRow]:
        rows: list[ExtractionRow] = []
        for row_index in range(self.extraction_table.rowCount()):
            values = [
                self.extraction_table.item(row_index, column_index).text()
                if self.extraction_table.item(row_index, column_index)
                else ""
                for column_index in range(7)
            ]
            rows.append(ExtractionRow(*values))
        return rows


def _validate_extraction_rows(rows: list[ExtractionRow]) -> dict[str, int]:
    missing_sample_size = 0
    missing_event_count = 0
    event_greater_than_total = 0
    for row in rows:
        treatment_total = _to_int(row.treatment_total)
        control_total = _to_int(row.control_total)
        treatment_events = _to_int(row.treatment_events)
        control_events = _to_int(row.control_events)
        if treatment_total is None or control_total is None:
            missing_sample_size += 1
        if treatment_events is None or control_events is None:
            missing_event_count += 1
        if (
            treatment_events is not None
            and treatment_total is not None
            and treatment_events > treatment_total
        ) or (control_events is not None and control_total is not None and control_events > control_total):
            event_greater_than_total += 1
    study_counts = Counter(row.study_id.strip().lower() for row in rows if row.study_id.strip())
    duplicate_study_id = sum(1 for count in study_counts.values() if count > 1)
    return {
        "Missing sample size": missing_sample_size,
        "Missing event count": missing_event_count,
        "Event count greater than total": event_greater_than_total,
        "Duplicate study ID": duplicate_study_id,
    }


def _to_int(value: str) -> int | None:
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None
