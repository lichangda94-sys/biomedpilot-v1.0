from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, replace

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app_meta.ui.components import SectionCard
from app_meta.ui.theme import Theme


@dataclass(frozen=True)
class ScreeningRecord:
    record_id: str
    title: str
    abstract: str
    authors: str
    journal: str
    doi: str
    decision: str = "Unscreened"


DEMO_SCREENING_RECORDS = (
    ScreeningRecord(
        "REC-0001",
        "Corticosteroids for severe pneumonia: a randomized clinical trial",
        "This randomized trial evaluated systemic corticosteroids in adults hospitalized with severe pneumonia.",
        "Yang H, Zhang L, Chen M",
        "JAMA · 2023",
        "10.1001/demo.001",
    ),
    ScreeningRecord(
        "REC-0014",
        "Hydrocortisone therapy in critical pneumonia",
        "A multicenter study assessing clinical outcomes and mortality after hydrocortisone treatment.",
        "Zhang Y, Li P",
        "BMJ · 2022",
        "10.1136/demo.014",
    ),
    ScreeningRecord(
        "REC-0021",
        "Antibiotic timing and survival in community-acquired pneumonia",
        "Observational cohort focused on antibiotic timing rather than corticosteroid exposure.",
        "Wang Q, Sun J",
        "Chest · 2021",
        "10.1016/demo.021",
    ),
    ScreeningRecord(
        "REC-0032",
        "Steroid therapy and mortality in severe community-acquired pneumonia",
        "Meta-relevant trial reporting mortality and adverse events for corticosteroid therapy.",
        "Li X, Guo R",
        "Lancet Respiratory Medicine · 2020",
        "10.1016/demo.032",
    ),
)


class ScreeningPage(QWidget):
    def __init__(self, on_action: Callable[[str], None]) -> None:
        super().__init__()
        self._on_action = on_action
        self._records = list(DEMO_SCREENING_RECORDS)
        self._current_index = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)
        root.addLayout(self._header())
        root.addLayout(self._mode_selector())

        body = QHBoxLayout()
        body.setSpacing(16)
        body.addWidget(self._record_list_card())
        body.addWidget(self._detail_card(), 1)
        body.addWidget(self._progress_card())
        root.addLayout(body, 1)
        self.record_list.setCurrentRow(0)
        self._render_record()
        self._refresh_progress()

    def _header(self) -> QVBoxLayout:
        header = QVBoxLayout()
        title = QLabel("筛选")
        title.setObjectName("pageTitle")
        subtitle = QLabel("按题名摘要和全文阶段记录纳入、排除、待定与全文获取需求")
        subtitle.setObjectName("muted")
        header.addWidget(title)
        header.addWidget(subtitle)
        return header

    def _mode_selector(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        self.title_abstract_button = QPushButton("Title / Abstract")
        self.full_text_button = QPushButton("Full Text")
        for button in (self.title_abstract_button, self.full_text_button):
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, selected=button: self._select_mode(selected))
            row.addWidget(button)
        self.title_abstract_button.setChecked(True)
        row.addStretch(1)
        return row

    def _record_list_card(self) -> SectionCard:
        card = SectionCard("Records")
        card.setFixedWidth(310)
        self.record_list = QListWidget()
        for record in self._records:
            self.record_list.addItem(QListWidgetItem(f"{record.record_id}\n{record.title}"))
        self.record_list.currentRowChanged.connect(self._select_record)
        card.layout.addWidget(self.record_list, 1)
        return card

    def _detail_card(self) -> SectionCard:
        card = SectionCard("Record detail")
        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("font-size: 20px; font-weight: 750;")
        self.abstract_label = QLabel()
        self.abstract_label.setWordWrap(True)
        self.abstract_label.setStyleSheet(f"line-height: 150%; color: {Theme.text};")
        self.authors_label = QLabel()
        self.journal_label = QLabel()
        self.doi_label = QLabel()
        for label in (self.authors_label, self.journal_label, self.doi_label):
            label.setObjectName("smallMuted")
            label.setWordWrap(True)

        card.layout.addWidget(self.title_label)
        card.layout.addWidget(self.abstract_label)
        card.layout.addWidget(self.authors_label)
        card.layout.addWidget(self.journal_label)
        card.layout.addWidget(self.doi_label)

        self.reason = QComboBox()
        self.reason.addItems(
            (
                "Exclusion reason",
                "Wrong population",
                "Wrong intervention",
                "Wrong comparator",
                "Wrong outcome",
                "Not original research",
                "Duplicate publication",
            )
        )
        card.layout.addWidget(self.reason)

        decisions = QHBoxLayout()
        for index, label in enumerate(("Include", "Exclude", "Maybe", "Need Full Text")):
            button = QPushButton(label)
            if index == 0:
                button.setObjectName("primaryButton")
            button.clicked.connect(lambda checked=False, decision=label: self._record_decision(decision))
            decisions.addWidget(button)
        decisions.addStretch(1)
        card.layout.addLayout(decisions)

        self.decision_status = QLabel("No decision recorded for the current record.")
        self.decision_status.setObjectName("smallMuted")
        self.decision_status.setWordWrap(True)
        card.layout.addWidget(self.decision_status)
        card.layout.addStretch(1)
        return card

    def _progress_card(self) -> SectionCard:
        card = SectionCard("Screening progress")
        card.setFixedWidth(300)
        self.progress_rows: dict[str, QLabel] = {}
        for label in ("Total", "Screened", "Included", "Excluded", "Maybe", "Full text needed"):
            row = QHBoxLayout()
            name = QLabel(label)
            name.setObjectName("smallMuted")
            value = QLabel("0")
            value.setAlignment(Qt.AlignRight)
            value.setStyleSheet("font-weight: 750;")
            row.addWidget(name)
            row.addWidget(value, 1)
            card.layout.addLayout(row)
            self.progress_rows[label] = value
        card.layout.addStretch(1)
        return card

    def _select_mode(self, selected: QPushButton) -> None:
        self.title_abstract_button.setChecked(selected is self.title_abstract_button)
        self.full_text_button.setChecked(selected is self.full_text_button)
        self._on_action(f"Screening mode: {selected.text()}")

    def _select_record(self, row: int) -> None:
        if 0 <= row < len(self._records):
            self._current_index = row
            self._render_record()

    def _render_record(self) -> None:
        record = self._records[self._current_index]
        self.title_label.setText(record.title)
        self.abstract_label.setText(record.abstract)
        self.authors_label.setText(f"Authors: {record.authors}")
        self.journal_label.setText(f"Journal: {record.journal}")
        self.doi_label.setText(f"DOI: {record.doi or 'Missing'}")
        self.decision_status.setText(f"Current decision: {record.decision}")

    def _record_decision(self, decision: str) -> None:
        record = self._records[self._current_index]
        if decision == "Exclude" and self.reason.currentIndex() == 0:
            self.decision_status.setStyleSheet(f"color: {Theme.warning};")
            self.decision_status.setText("Please select an exclusion reason before excluding this record.")
            return
        self._records[self._current_index] = replace(record, decision=decision)
        self.decision_status.setStyleSheet(f"color: {Theme.primary};")
        self.decision_status.setText(f"{decision} recorded for {record.record_id}.")
        self.record_list.currentItem().setText(f"{record.record_id} · {decision}\n{record.title}")
        self._refresh_progress()
        self._on_action(decision)

    def _refresh_progress(self) -> None:
        counts = Counter(record.decision for record in self._records)
        values = {
            "Total": len(self._records),
            "Screened": sum(1 for record in self._records if record.decision != "Unscreened"),
            "Included": counts["Include"],
            "Excluded": counts["Exclude"],
            "Maybe": counts["Maybe"],
            "Full text needed": counts["Need Full Text"],
        }
        for label, value in values.items():
            self.progress_rows[label].setText(str(value))
