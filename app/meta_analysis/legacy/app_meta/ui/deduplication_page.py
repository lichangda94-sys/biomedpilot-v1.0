from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app_meta.ui.components import MetricCard, SectionCard
from app_meta.ui.theme import Theme


@dataclass(frozen=True)
class DuplicateGroup:
    group_id: str
    duplicate_type: str
    records_in_group: str
    suggested_keep: str
    status: str
    left_title: str
    right_title: str
    left_meta: str
    right_meta: str


DEMO_GROUPS = (
    DuplicateGroup(
        "DG-001",
        "Exact DOI",
        "2",
        "REC-0001",
        "Unresolved",
        "Corticosteroids for severe pneumonia: randomized trial",
        "Corticosteroids for severe pneumonia",
        "Yang 2023 · JAMA · 10.1001/demo.001",
        "Yang et al. 2023 · PubMed · 10.1001/demo.001",
    ),
    DuplicateGroup(
        "DG-002",
        "Similar title",
        "3",
        "REC-0014",
        "Review needed",
        "Hydrocortisone therapy in critical pneumonia",
        "Hydrocortisone in adults with severe pneumonia",
        "Zhang 2022 · BMJ · Embase",
        "Zhang 2022 · Web of Science",
    ),
    DuplicateGroup(
        "DG-003",
        "Exact DOI",
        "2",
        "REC-0031",
        "Resolved",
        "Steroid therapy and mortality in severe CAP",
        "Steroid therapy and mortality in severe community-acquired pneumonia",
        "Li 2021 · Lancet Respir Med",
        "Li 2021 · PubMed",
    ),
)


class DeduplicationPage(QWidget):
    def __init__(self, on_action: Callable[[str], None]) -> None:
        super().__init__()
        self._on_action = on_action
        self._groups = list(DEMO_GROUPS)
        self._selected_group = self._groups[0]
        self._resolved_count = sum(1 for group in self._groups if group.status == "Resolved")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)
        root.addLayout(self._header())
        root.addLayout(self._summary_cards())

        body = QHBoxLayout()
        body.setSpacing(16)
        body.addWidget(self._groups_card(), 2)
        body.addWidget(self._comparison_card(), 1)
        root.addLayout(body, 1)

    def _header(self) -> QVBoxLayout:
        header = QVBoxLayout()
        title = QLabel("去重审查")
        title.setObjectName("pageTitle")
        subtitle = QLabel("审查 DOI 精确重复与标题相似记录，确认保留文献并标记未解决分组")
        subtitle.setObjectName("muted")
        header.addWidget(title)
        header.addWidget(subtitle)
        return header

    def _summary_cards(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        summaries = (
            ("Imported records", "1,248", "Demo import pool", "document"),
            ("Exact DOI duplicates", "42", "21 duplicate groups", "target"),
            ("Similar title duplicates", "68", "Review recommended", "wave"),
            ("Unique records", "1,138", "Ready for screening", "shield"),
            ("Manually resolved", str(self._resolved_count), "Current session", "shield"),
        )
        for index, (title, value, detail, icon) in enumerate(summaries):
            grid.addWidget(MetricCard(title, value, detail, icon), 0, index)
        return grid

    def _groups_card(self) -> SectionCard:
        card = SectionCard("Duplicate groups")
        self.table = QTableWidget(len(self._groups), 5)
        self.table.setHorizontalHeaderLabels(("Group ID", "Duplicate type", "Records in group", "Suggested keep", "Status"))
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for row_index, group in enumerate(self._groups):
            for column_index, value in enumerate(
                (group.group_id, group.duplicate_type, group.records_in_group, group.suggested_keep, group.status)
            ):
                self.table.setItem(row_index, column_index, QTableWidgetItem(value))
        self.table.itemSelectionChanged.connect(self._select_current_group)
        card.layout.addWidget(self.table, 1)
        return card

    def _comparison_card(self) -> SectionCard:
        card = SectionCard("Record comparison")
        self.left_record = _comparison_panel("Left record")
        self.right_record = _comparison_panel("Right record")
        row = QHBoxLayout()
        row.addWidget(self.left_record)
        row.addWidget(self.right_record)
        card.layout.addLayout(row, 1)

        actions = QGridLayout()
        for index, label in enumerate(("Keep Left", "Keep Right", "Keep Both", "Exclude Both", "Mark Unresolved")):
            button = QPushButton(label)
            if index == 0:
                button.setObjectName("primaryButton")
            button.clicked.connect(lambda checked=False, name=label: self._mark_decision(name))
            actions.addWidget(button, index // 2, index % 2)
        card.layout.addLayout(actions)

        self.decision_status = QLabel("Select a duplicate group and choose a resolution action.")
        self.decision_status.setObjectName("smallMuted")
        self.decision_status.setWordWrap(True)
        card.layout.addWidget(self.decision_status)
        self.table.selectRow(0)
        self._render_comparison()
        return card

    def _select_current_group(self) -> None:
        selected = self.table.currentRow()
        if 0 <= selected < len(self._groups):
            self._selected_group = self._groups[selected]
            self._render_comparison()

    def _render_comparison(self) -> None:
        _set_comparison_panel(self.left_record, self._selected_group.left_title, self._selected_group.left_meta)
        _set_comparison_panel(self.right_record, self._selected_group.right_title, self._selected_group.right_meta)

    def _mark_decision(self, decision: str) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        status = "Unresolved" if decision == "Mark Unresolved" else f"Resolved · {decision}"
        self.table.item(row, 4).setText(status)
        self.decision_status.setStyleSheet(f"color: {Theme.primary};")
        self.decision_status.setText(f"{self._groups[row].group_id}: {decision} recorded for review.")
        self._on_action(decision)


def _comparison_panel(title: str) -> SectionCard:
    panel = SectionCard(title)
    panel.setStyleSheet(
        f"background: #F8FAFC; border: 1px solid {Theme.border_soft}; border-radius: {Theme.radius_small}px;"
    )
    title_label = QLabel()
    title_label.setObjectName("comparisonTitle")
    title_label.setWordWrap(True)
    title_label.setStyleSheet("font-weight: 700;")
    meta = QLabel()
    meta.setObjectName("smallMuted")
    meta.setWordWrap(True)
    panel.layout.addWidget(title_label)
    panel.layout.addWidget(meta)
    panel.title_label = title_label
    panel.meta_label = meta
    return panel


def _set_comparison_panel(panel: SectionCard, title: str, meta: str) -> None:
    panel.title_label.setText(title)
    panel.meta_label.setText(meta)
