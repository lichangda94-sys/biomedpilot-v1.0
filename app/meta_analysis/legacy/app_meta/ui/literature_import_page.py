from __future__ import annotations

import csv
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
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

from app_meta.ui.components import IconBadge, SectionCard
from app_meta.ui.theme import Theme


TABLE_COLUMNS = (
    "Record ID",
    "Title",
    "Authors",
    "Year",
    "Journal",
    "DOI",
    "Source",
    "Import Batch",
    "Duplicate Status",
)


@dataclass(frozen=True)
class LiteratureRecord:
    record_id: str
    title: str
    authors: str
    year: str
    journal: str
    doi: str
    source: str
    import_batch: str
    duplicate_status: str = "Unique"


def parse_csv_records(path: str | Path, import_batch: str | None = None) -> list[LiteratureRecord]:
    source_path = Path(path)
    batch = import_batch or source_path.name
    records: list[LiteratureRecord] = []
    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for index, raw_row in enumerate(reader, start=1):
            row = {_normalize_field_name(key): (value or "").strip() for key, value in raw_row.items() if key}
            records.append(
                LiteratureRecord(
                    record_id=f"REC-{index:04d}",
                    title=_first_value(row, "title", "article_title", "study_title"),
                    authors=_first_value(row, "authors", "author", "author_list", "creators"),
                    year=_first_value(row, "year", "publication_year", "pub_year", "date"),
                    journal=_first_value(row, "journal", "journal_title", "source_title", "publication"),
                    doi=_first_value(row, "doi", "digital_object_identifier"),
                    source=_first_value(row, "source", "database", "db", default="CSV"),
                    import_batch=batch,
                )
            )
    return _with_duplicate_status(records)


class LiteratureImportPage(QWidget):
    def __init__(self, on_action: Callable[[str], None]) -> None:
        super().__init__()
        self._on_action = on_action
        self._records: list[LiteratureRecord] = []
        self._summary_cards: dict[str, _SummaryCard] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)
        root.addLayout(self._header())
        root.addWidget(self._import_action_card())
        root.addLayout(self._summary_cards_layout())

        body = QHBoxLayout()
        body.setSpacing(16)
        body.addWidget(self._records_card(), 1)
        body.addWidget(self._quality_card())
        root.addLayout(body, 1)
        self._refresh()

    def _header(self) -> QVBoxLayout:
        header = QVBoxLayout()
        title = QLabel("文献导入")
        title.setObjectName("pageTitle")
        subtitle = QLabel("导入检索结果文件，预览记录字段，并在筛选前检查来源与重复风险")
        subtitle.setObjectName("muted")
        header.addWidget(title)
        header.addWidget(subtitle)
        return header

    def _import_action_card(self) -> SectionCard:
        card = SectionCard("Import literature files")
        row = QHBoxLayout()
        actions = (
            ("Import NBIB", lambda: self._open_placeholder("NBIB")),
            ("Import RIS", lambda: self._open_placeholder("RIS")),
            ("Import CSV", self._open_csv),
            ("Import EndNote XML", lambda: self._open_placeholder("EndNote XML")),
            ("Clear Records", self.clear_records),
        )
        for index, (label, handler) in enumerate(actions):
            button = QPushButton(label)
            if index == 2:
                button.setObjectName("primaryButton")
            button.clicked.connect(lambda checked=False, callback=handler: callback())
            row.addWidget(button)
        row.addStretch(1)
        card.layout.addLayout(row)

        self.import_status = QLabel("Ready to import CSV records. NBIB, RIS, and XML parsers will be connected later.")
        self.import_status.setObjectName("smallMuted")
        self.import_status.setWordWrap(True)
        card.layout.addWidget(self.import_status)
        return card

    def _summary_cards_layout(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        for index, label in enumerate(
            (
                "Total imported",
                "PubMed",
                "Web of Science",
                "Embase",
                "Other",
                "Missing DOI",
                "Potential duplicates",
            )
        ):
            card = _SummaryCard(label)
            self._summary_cards[label] = card
            grid.addWidget(card, index // 4, index % 4)
        return grid

    def _records_card(self) -> SectionCard:
        card = SectionCard("Imported records")
        self.table = QTableWidget(0, len(TABLE_COLUMNS))
        self.table.setHorizontalHeaderLabels(TABLE_COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setMinimumHeight(380)
        card.layout.addWidget(self.table, 1)
        return card

    def _quality_card(self) -> SectionCard:
        card = SectionCard("Import Quality")
        card.setFixedWidth(330)
        self.quality_rows: dict[str, QLabel] = {}
        for label in (
            "Records imported",
            "Titles available",
            "DOI coverage",
            "Year coverage",
            "Source database recorded",
        ):
            row = QHBoxLayout()
            name = QLabel(label)
            name.setObjectName("smallMuted")
            value = QLabel("0")
            value.setAlignment(Qt.AlignRight)
            value.setStyleSheet("font-weight: 700;")
            row.addWidget(name)
            row.addWidget(value, 1)
            card.layout.addLayout(row)
            self.quality_rows[label] = value

        note = QLabel("Missing fields are allowed during import. Complete metadata can be normalized before screening.")
        note.setWordWrap(True)
        note.setStyleSheet(
            f"background: {Theme.primary_soft}; color: {Theme.primary}; border-radius: 10px; padding: 10px;"
        )
        card.layout.addWidget(note)
        card.layout.addStretch(1)
        return card

    def _open_csv(self) -> None:
        filename, _filter = QFileDialog.getOpenFileName(
            self,
            "Import CSV",
            "",
            "CSV files (*.csv);;All files (*)",
        )
        if not filename:
            return
        try:
            self.load_csv(filename)
        except (OSError, csv.Error, UnicodeDecodeError) as exc:
            self.import_status.setStyleSheet(f"color: {Theme.danger};")
            self.import_status.setText(f"CSV import failed: {exc}")

    def _open_placeholder(self, file_type: str) -> None:
        filename, _filter = QFileDialog.getOpenFileName(
            self,
            f"Import {file_type}",
            "",
            f"{file_type} files (*);;All files (*)",
        )
        if filename:
            self.import_status.setStyleSheet(f"color: {Theme.warning};")
            self.import_status.setText(f"{file_type} parser is not implemented yet. Selected file: {Path(filename).name}")
            self._on_action(f"Import {file_type}")

    def load_csv(self, path: str | Path) -> None:
        self._records = parse_csv_records(path)
        self.import_status.setStyleSheet(f"color: {Theme.success};")
        self.import_status.setText(f"Imported {len(self._records)} CSV records from {Path(path).name}.")
        self._refresh()
        self._on_action("Import CSV")

    def clear_records(self) -> None:
        self._records = []
        self.import_status.setStyleSheet(f"color: {Theme.muted};")
        self.import_status.setText("Records cleared. Import a CSV file to preview literature records.")
        self._refresh()
        self._on_action("Clear Records")

    def _refresh(self) -> None:
        self._refresh_table()
        self._refresh_summary()
        self._refresh_quality()

    def _refresh_table(self) -> None:
        self.table.setRowCount(len(self._records))
        for row_index, record in enumerate(self._records):
            values = (
                record.record_id,
                record.title,
                record.authors,
                record.year,
                record.journal,
                record.doi,
                record.source,
                record.import_batch,
                record.duplicate_status,
            )
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column_index == 8 and value != "Unique":
                    item.setForeground(QColor(Theme.warning))
                self.table.setItem(row_index, column_index, item)

    def _refresh_summary(self) -> None:
        total = len(self._records)
        source_counts = Counter(_source_group(record.source) for record in self._records)
        missing_doi = sum(1 for record in self._records if not record.doi)
        duplicates = sum(1 for record in self._records if record.duplicate_status != "Unique")
        values = {
            "Total imported": str(total),
            "PubMed": str(source_counts["PubMed"]),
            "Web of Science": str(source_counts["Web of Science"]),
            "Embase": str(source_counts["Embase"]),
            "Other": str(source_counts["Other"]),
            "Missing DOI": str(missing_doi),
            "Potential duplicates": str(duplicates),
        }
        for label, value in values.items():
            self._summary_cards[label].set_value(value)

    def _refresh_quality(self) -> None:
        total = len(self._records)
        titles = sum(1 for record in self._records if record.title)
        doi = sum(1 for record in self._records if record.doi)
        years = sum(1 for record in self._records if record.year)
        sources = sum(1 for record in self._records if record.source)
        values = {
            "Records imported": str(total),
            "Titles available": _coverage(titles, total),
            "DOI coverage": _coverage(doi, total),
            "Year coverage": _coverage(years, total),
            "Source database recorded": _coverage(sources, total),
        }
        for label, value in values.items():
            self.quality_rows[label].setText(value)


class _SummaryCard(SectionCard):
    def __init__(self, title: str) -> None:
        super().__init__()
        row = QHBoxLayout()
        text = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("smallMuted")
        self.value_label = QLabel("0")
        self.value_label.setStyleSheet("font-size: 22px; font-weight: 750;")
        text.addWidget(title_label)
        text.addWidget(self.value_label)
        row.addLayout(text, 1)
        row.addWidget(IconBadge("literature_import"))
        self.layout.addLayout(row)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


def _normalize_field_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def _first_value(row: dict[str, str], *keys: str, default: str = "") -> str:
    for key in keys:
        value = row.get(key, "")
        if value:
            return value
    return default


def _with_duplicate_status(records: list[LiteratureRecord]) -> list[LiteratureRecord]:
    doi_counts = Counter(record.doi.lower() for record in records if record.doi)
    title_counts = Counter(record.title.lower() for record in records if record.title)
    updated: list[LiteratureRecord] = []
    for record in records:
        is_duplicate = bool(record.doi and doi_counts[record.doi.lower()] > 1) or bool(
            record.title and title_counts[record.title.lower()] > 1
        )
        status = "Potential duplicate" if is_duplicate else "Unique"
        updated.append(
            LiteratureRecord(
                record_id=record.record_id,
                title=record.title,
                authors=record.authors,
                year=record.year,
                journal=record.journal,
                doi=record.doi,
                source=record.source,
                import_batch=record.import_batch,
                duplicate_status=status,
            )
        )
    return updated


def _source_group(source: str) -> str:
    value = source.lower()
    if "pubmed" in value or "medline" in value:
        return "PubMed"
    if "web of science" in value or value == "wos":
        return "Web of Science"
    if "embase" in value:
        return "Embase"
    return "Other"


def _coverage(count: int, total: int) -> str:
    if total == 0:
        return "0%"
    return f"{round(count / total * 100)}%"
