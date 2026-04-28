from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.profile_row_templates import (
    PROFILE_ROW_TEMPLATE_FIELDS,
    ProfileTemplateType,
    supported_profile_row_template_types,
)
from core.profile_row_editor_policy import (
    ProfileRowEditorActionDecision,
    evaluate_profile_row_load,
    evaluate_profile_row_save,
    evaluate_profile_row_switch,
)
from core.profile_row_validation import (
    ProfileRowValidationIssue,
    validate_profile_rows,
)


class ProfileRowEditorWidget(QWidget):
    def __init__(
        self,
        profile_type: ProfileTemplateType = "TREATMENT_EFFECT_META",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._profile_type = profile_type
        self._dirty = False
        self._save_rows_handler: Callable[[], Path | None] | None = None
        self._load_rows_handler: Callable[[ProfileTemplateType], list[dict[str, str]]] | None = None
        self._title = QLabel("Profile Row Editor")
        self._title.setObjectName("sectionTitle")
        self._note = QLabel(
            "Template-based row editing preview. Edits are not auto-saved; "
            "Save rows only saves CSV. Load rows only loads CSV. "
            "This does not run meta-analysis and does not generate reports. "
            "Invalid rows cannot be saved; dirty rows must be saved before loading another file. "
            f"CSV templates currently cover: {', '.join(supported_profile_row_template_types())}."
        )
        self._note.setObjectName("mutedLabel")
        self._note.setWordWrap(True)
        self._state_label = QLabel("")
        self._state_label.setObjectName("mutedLabel")
        self._action_status_label = QLabel("Row file actions: no project action selected.")
        self._action_status_label.setObjectName("mutedLabel")
        self._action_status_label.setWordWrap(True)
        self._save_rows_button = QPushButton("Save rows")
        self._save_rows_button.setObjectName("saveProfileRowsButton")
        self._save_rows_button.setEnabled(False)
        self._save_rows_button.clicked.connect(self.trigger_save_rows)
        self._load_rows_button = QPushButton("Load rows")
        self._load_rows_button.setObjectName("loadProfileRowsButton")
        self._load_rows_button.setEnabled(False)
        self._load_rows_button.clicked.connect(self.trigger_load_rows)
        self._table = QTableWidget(0, 0)
        self._table.setObjectName("profileRowEditorTable")
        self._table.itemChanged.connect(self._handle_item_changed)

        controls = QHBoxLayout()
        controls.addWidget(self._save_rows_button)
        controls.addWidget(self._load_rows_button)
        controls.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(self._title)
        layout.addWidget(self._note)
        layout.addWidget(self._state_label)
        layout.addLayout(controls)
        layout.addWidget(self._action_status_label)
        layout.addWidget(self._table)
        self.set_profile_type(profile_type)

    def set_profile_type(self, profile_type: ProfileTemplateType) -> None:
        if profile_type not in PROFILE_ROW_TEMPLATE_FIELDS:
            raise ValueError(f"Unsupported profile row editor template: {profile_type}")
        self._profile_type = profile_type
        fields = PROFILE_ROW_TEMPLATE_FIELDS[profile_type]
        self._table.setColumnCount(len(fields))
        self._table.setHorizontalHeaderLabels(list(fields))
        self._table.setRowCount(0)
        self.mark_clean()

    def set_rows(self, rows: list[dict[str, object]]) -> None:
        fields = PROFILE_ROW_TEMPLATE_FIELDS[self._profile_type]
        self._table.blockSignals(True)
        self._table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, field in enumerate(fields):
                item = QTableWidgetItem(str(row.get(field, "")))
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(row_index, column_index, item)
        self._table.blockSignals(False)
        self.mark_clean()

    def set_profile_io_handlers(
        self,
        *,
        save_handler: Callable[[], Path | None] | None,
        load_handler: Callable[[ProfileTemplateType], list[dict[str, str]]] | None,
    ) -> None:
        self._save_rows_handler = save_handler
        self._load_rows_handler = load_handler
        self._save_rows_button.setEnabled(save_handler is not None)
        self._load_rows_button.setEnabled(load_handler is not None)

    def add_empty_row(self) -> None:
        row_index = self._table.rowCount()
        self._table.insertRow(row_index)
        for column_index in range(self._table.columnCount()):
            item = QTableWidgetItem("")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row_index, column_index, item)
        self.mark_dirty()

    def rows(self) -> list[dict[str, str]]:
        fields = PROFILE_ROW_TEMPLATE_FIELDS[self._profile_type]
        output: list[dict[str, str]] = []
        for row_index in range(self._table.rowCount()):
            row: dict[str, str] = {}
            for column_index, field in enumerate(fields):
                item = self._table.item(row_index, column_index)
                row[field] = item.text() if item is not None else ""
            output.append(row)
        return output

    def profile_type(self) -> ProfileTemplateType:
        return self._profile_type

    def note_text(self) -> str:
        return self._note.text()

    def mark_clean(self) -> None:
        self._dirty = False
        self._refresh_state_label()

    def mark_dirty(self) -> None:
        self._dirty = True
        self._refresh_state_label()

    def is_dirty(self) -> bool:
        return self._dirty

    def validation_issues(self) -> list[ProfileRowValidationIssue]:
        return validate_profile_rows(self._profile_type, self.rows())

    def save_decision(self) -> ProfileRowEditorActionDecision:
        return evaluate_profile_row_save(self._profile_type, self.rows())

    def load_decision(self) -> ProfileRowEditorActionDecision:
        return evaluate_profile_row_load(self._dirty)

    def switch_profile_decision(self) -> ProfileRowEditorActionDecision:
        return evaluate_profile_row_switch(self._dirty)

    def trigger_save_rows(self) -> None:
        decision = self.save_decision()
        if not decision.allowed:
            self._action_status_label.setText(decision.message)
            return
        if self._save_rows_handler is None:
            self._action_status_label.setText("Save unavailable: no project save handler is connected.")
            return
        output_path = self._save_rows_handler()
        if output_path is None:
            self._action_status_label.setText("Save unavailable: no Meta Analysis project is open.")
            return
        self.mark_clean()
        self._action_status_label.setText(f"Rows saved to {output_path}.")

    def trigger_load_rows(self) -> None:
        decision = self.load_decision()
        if not decision.allowed:
            self._action_status_label.setText(decision.message)
            return
        if self._load_rows_handler is None:
            self._action_status_label.setText("Load unavailable: no project load handler is connected.")
            return
        rows = self._load_rows_handler(self._profile_type)
        self._action_status_label.setText(f"Loaded {len(rows)} row(s) from project file.")

    def state_text(self) -> str:
        return self._state_label.text()

    def action_status_text(self) -> str:
        return self._action_status_label.text()

    def save_rows_button_enabled(self) -> bool:
        return self._save_rows_button.isEnabled()

    def load_rows_button_enabled(self) -> bool:
        return self._load_rows_button.isEnabled()

    def cell_text(self, row: int, column: int) -> str:
        item = self._table.item(row, column)
        return item.text() if item is not None else ""

    def _handle_item_changed(self, _item: QTableWidgetItem) -> None:
        self.mark_dirty()

    def _refresh_state_label(self) -> None:
        dirty_text = "Unsaved changes" if self._dirty else "No unsaved changes"
        issue_count = len(self.validation_issues())
        if issue_count:
            validation_text = f"{issue_count} validation issue(s)"
        else:
            validation_text = "No validation issues"
        self._state_label.setText(f"{dirty_text} · {validation_text}")
