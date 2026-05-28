from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from app.shared.ui_components.common import DataTableColumn, make_data_table, make_warning_list, WarningItem
from app.shared.ui_components.primitives import make_empty_state, make_section_title, make_status_chip, make_workbench_card
from app.ui_style_tokens import COLORS, FONT_SIZE, RADIUS, SPACING


@dataclass(frozen=True)
class WorkbenchPane:
    key: str
    title: str
    widget: object
    min_width: int = 180
    stretch: int = 1


@dataclass(frozen=True)
class LaneItem:
    key: str
    label: str
    sample: str = ""
    volume: str = ""
    semantic_state: str = "draft"
    warning: str = ""


@dataclass(frozen=True)
class WellItem:
    row: str
    column: int
    label: str = ""
    semantic_state: str = "draft"
    selected: bool = False


@dataclass(frozen=True)
class ReferenceItem:
    key: str
    title: str
    subtitle: str = ""
    status_key: str = "draft"
    semantic_state: str = "draft"


@dataclass(frozen=True)
class ExtractionField:
    key: str
    label: str
    value: str = ""
    status_key: str = "draft"
    semantic_state: str = "draft"
    notes: str = ""


def make_two_column_workbench(
    *,
    left_widget,
    right_widget,
    object_name: str = "twoColumnWorkbench",
    left_min_width: int = 360,
    right_min_width: int = 280,
):
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QSizePolicy

    frame = QFrame()
    frame.setObjectName(object_name)
    frame.setProperty("uiPrimitive", "two_column_workbench")
    frame.setProperty("layoutPolishNoOverlap", True)
    frame.setStyleSheet(_frame_stylesheet(object_name))
    frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    layout = QHBoxLayout(frame)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(SPACING["lg"])
    left_widget.setMinimumWidth(left_min_width)
    right_widget.setMinimumWidth(right_min_width)
    layout.addWidget(left_widget, 1)
    layout.addWidget(right_widget, 0)
    return frame


def make_three_column_workbench(
    *,
    left_widget,
    middle_widget,
    right_widget,
    object_name: str = "threeColumnWorkbench",
    sizes: Sequence[int] = (240, 760, 320),
):
    splitter = make_splitter_workbench(
        panes=[
            WorkbenchPane("left", "Left", left_widget, min_width=200, stretch=0),
            WorkbenchPane("middle", "Middle", middle_widget, min_width=420, stretch=1),
            WorkbenchPane("right", "Right", right_widget, min_width=280, stretch=0),
        ],
        object_name=object_name,
        sizes=sizes,
    )
    splitter.setProperty("uiPrimitive", "three_column_workbench")
    splitter.setProperty("rightPanelMinWidth", 280)
    splitter.setProperty("rightPanelMaxWidth", 360)
    right_widget.setMinimumWidth(280)
    right_widget.setMaximumWidth(360)
    return splitter


def make_left_list_middle_form_right_preview(
    *,
    list_widget,
    form_widget,
    preview_widget,
    object_name: str = "leftListMiddleFormRightPreview",
    sizes: Sequence[int] = (240, 620, 320),
):
    splitter = make_splitter_workbench(
        panes=[
            WorkbenchPane("list", "List", list_widget, min_width=200, stretch=0),
            WorkbenchPane("form", "Form", form_widget, min_width=420, stretch=1),
            WorkbenchPane("preview", "Preview", preview_widget, min_width=280, stretch=0),
        ],
        object_name=object_name,
        sizes=sizes,
    )
    splitter.setProperty("uiPrimitive", "left_list_middle_form_right_preview")
    preview_widget.setMinimumWidth(280)
    preview_widget.setMaximumWidth(360)
    return splitter


def make_right_summary_panel(
    *,
    title: str,
    status_items: Sequence[tuple[str, str]] = (),
    key_values: Sequence[tuple[str, str]] = (),
    warnings: Sequence[WarningItem] = (),
    object_name: str = "rightSummaryPanel",
):
    from PySide6.QtWidgets import QLabel, QVBoxLayout

    panel = make_workbench_card(object_name=object_name)
    panel.setProperty("uiPrimitive", "right_summary_panel")
    panel.setMinimumWidth(280)
    panel.setMaximumWidth(360)
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
    layout.setSpacing(SPACING["md"])
    layout.addWidget(make_section_title(title))
    for label, status_key in status_items:
        layout.addWidget(make_status_chip(label, status_key=status_key))
    for key, value in key_values:
        row = QLabel(f"{key}: {value}")
        row.setObjectName("rightSummaryPanelRow")
        row.setWordWrap(True)
        row.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONT_SIZE['body']}px;")
        layout.addWidget(row)
    if warnings:
        layout.addWidget(make_warning_list(warnings, title="Blockers"))
    layout.addStretch(1)
    return panel


def make_splitter_workbench(
    *,
    panes: Sequence[WorkbenchPane],
    object_name: str = "splitterWorkbench",
    orientation: str = "horizontal",
    sizes: Sequence[int] = (),
):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QSplitter

    splitter = QSplitter(Qt.Horizontal if orientation == "horizontal" else Qt.Vertical)
    splitter.setObjectName(object_name)
    splitter.setProperty("uiPrimitive", "splitter_workbench")
    splitter.setProperty("orientation", orientation)
    splitter.setProperty("layoutPolishNoOverlap", True)
    for index, pane in enumerate(panes):
        pane.widget.setObjectName(pane.widget.objectName() or f"{object_name}_{pane.key}")
        pane.widget.setMinimumWidth(pane.min_width)
        splitter.addWidget(pane.widget)
        splitter.setStretchFactor(index, pane.stretch)
    if sizes:
        splitter.setSizes(list(sizes))
    return splitter


def make_dense_table_panel(
    *,
    title: str,
    columns: Sequence[DataTableColumn],
    rows: Sequence[Mapping[str, object] | Sequence[object]],
    object_name: str = "denseTablePanel",
    search_placeholder: str = "Filter rows",
):
    from PySide6.QtWidgets import QLineEdit, QVBoxLayout

    panel = make_workbench_card(object_name=object_name)
    panel.setProperty("uiPrimitive", "dense_table_panel")
    panel.setProperty("remoteFetchAllowed", False)
    panel.setProperty("formalActionEnabled", False)
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
    layout.setSpacing(SPACING["md"])
    layout.addWidget(make_section_title(title))
    search = QLineEdit()
    search.setObjectName("denseTablePanelFilter")
    search.setPlaceholderText(search_placeholder)
    search.setProperty("uiPrimitive", "dense_table_filter")
    search.setProperty("remoteFetchAllowed", False)
    layout.addWidget(search)
    table = make_data_table(columns=columns, rows=rows)
    table.setObjectName("denseTablePanelTable")
    layout.addWidget(table)
    return panel


def make_preview_card(
    *,
    title: str,
    preview_widget,
    status_key: str = "draft",
    semantic_state: str = "draft",
    caption: str = "",
    object_name: str = "previewCard",
):
    from PySide6.QtWidgets import QLabel, QVBoxLayout

    card = make_workbench_card(object_name=object_name, semantic_state=semantic_state)
    card.setProperty("uiPrimitive", "preview_card")
    card.setProperty("semanticState", semantic_state)
    card.setProperty("requiresNonFormalStatusChip", True)
    card.setProperty("formalResult", False)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
    layout.setSpacing(SPACING["md"])
    layout.addWidget(make_section_title(title, caption))
    layout.addWidget(make_status_chip(status_key=status_key, semantic_state=semantic_state))
    layout.addWidget(preview_widget)
    if caption:
        label = QLabel(caption)
        label.setObjectName("previewCardCaption")
        label.setWordWrap(True)
        label.setStyleSheet(f"color: {COLORS['muted']}; font-size: {FONT_SIZE['caption']}px;")
        layout.addWidget(label)
    return card


def make_lane_layout_preview(
    lanes: Sequence[LaneItem],
    *,
    object_name: str = "laneLayoutPreview",
):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QFrame, QGridLayout, QLabel

    frame = QFrame()
    frame.setObjectName(object_name)
    frame.setProperty("uiPrimitive", "lane_layout_preview")
    frame.setProperty("fakeBandRendering", False)
    frame.setProperty("imageAnalysisEnabled", False)
    frame.setStyleSheet(_frame_stylesheet(object_name))
    layout = QGridLayout(frame)
    layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
    layout.setSpacing(SPACING["sm"])
    for column, lane in enumerate(lanes):
        lane_box = QFrame()
        lane_box.setObjectName("laneLayoutPreviewLane")
        lane_box.setProperty("laneKey", lane.key)
        lane_box.setProperty("semanticState", lane.semantic_state)
        lane_box.setStyleSheet(
            f"QFrame#laneLayoutPreviewLane {{ background: {COLORS['surface']}; border: 1px solid {COLORS['border']}; border-radius: {RADIUS['sm']}px; }}"
        )
        lane_layout = QGridLayout(lane_box)
        lane_layout.setContentsMargins(SPACING["xs"], SPACING["xs"], SPACING["xs"], SPACING["xs"])
        for row, text in enumerate((lane.label, lane.sample, lane.volume, lane.warning)):
            label = QLabel(text)
            label.setAlignment(Qt.AlignCenter)
            label.setWordWrap(True)
            label.setStyleSheet(f"color: {COLORS['text'] if row == 0 else COLORS['muted']}; font-size: {FONT_SIZE['caption']}px;")
            lane_layout.addWidget(label, row, 0)
        layout.addWidget(lane_box, 0, column)
    return frame


def make_matrix_grid_96_well(
    wells: Sequence[WellItem] = (),
    *,
    object_name: str = "matrixGrid96Well",
):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QAbstractItemView, QTableWidget, QTableWidgetItem

    row_labels = tuple("ABCDEFGH")
    table = QTableWidget(8, 12)
    table.setObjectName(object_name)
    table.setProperty("uiPrimitive", "matrix_grid_96_well")
    table.setProperty("readOnly", True)
    table.setProperty("editable", False)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionMode(QAbstractItemView.ExtendedSelection)
    table.setSelectionBehavior(QAbstractItemView.SelectItems)
    table.setHorizontalHeaderLabels([str(index) for index in range(1, 13)])
    table.setVerticalHeaderLabels(row_labels)
    for row in range(8):
        for column in range(12):
            item = QTableWidgetItem("")
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, column, item)
    for well in wells:
        if well.row not in row_labels or not 1 <= well.column <= 12:
            continue
        item = table.item(row_labels.index(well.row), well.column - 1)
        item.setText(well.label)
        item.setData(Qt.UserRole, well.semantic_state)
        if well.selected:
            item.setSelected(True)
    table.resizeColumnsToContents()
    return table


def make_reference_queue_panel(
    *,
    references: Sequence[ReferenceItem],
    detail_widget=None,
    object_name: str = "referenceQueuePanel",
    on_reference_selected: Callable[[str], None] | None = None,
):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QStandardItem, QStandardItemModel
    from PySide6.QtWidgets import QListView

    list_view = QListView()
    list_view.setObjectName("referenceQueueList")
    list_view.setProperty("uiPrimitive", "reference_queue_list")
    model = QStandardItemModel(list_view)
    for reference in references:
        item = QStandardItem(reference.title)
        item.setEditable(False)
        item.setToolTip(reference.subtitle)
        item.setData(reference.key, Qt.UserRole)
        item.setData(reference.status_key, Qt.UserRole + 1)
        item.setData(reference.semantic_state, Qt.UserRole + 2)
        model.appendRow(item)
    list_view.setModel(model)
    if on_reference_selected is not None:
        list_view.selectionModel().currentChanged.connect(
            lambda current, previous: on_reference_selected(str(current.data(Qt.UserRole))) if current.isValid() else None
        )
    detail = detail_widget or make_empty_state("No reference selected", "Select a reference to review draft details.", semantic_state="draft")
    splitter = make_splitter_workbench(
        panes=[
            WorkbenchPane("queue", "Queue", list_view, min_width=260, stretch=0),
            WorkbenchPane("detail", "Detail", detail, min_width=420, stretch=1),
        ],
        object_name=object_name,
        sizes=(320, 680),
    )
    splitter.setProperty("uiPrimitive", "reference_queue_panel")
    splitter.setProperty("aiSuggestionAdvisoryOnly", True)
    splitter.setProperty("finalDecisionEnabled", False)
    return splitter


def make_extraction_form_table(
    fields: Sequence[ExtractionField],
    *,
    object_name: str = "extractionFormTable",
):
    table = make_data_table(
        columns=[
            DataTableColumn("label", "Field", 220),
            DataTableColumn("value", "Draft value", 180),
            DataTableColumn("status", "State", 140),
            DataTableColumn("notes", "Notes", 220),
        ],
        rows=[
            {
                "label": field.label,
                "value": field.value,
                "status": field.status_key,
                "notes": field.notes,
            }
            for field in fields
        ],
        object_name=object_name,
    )
    table.setProperty("uiPrimitive", "extraction_form_table")
    table.setProperty("draftOnly", True)
    table.setProperty("formalAnalysisInput", False)
    return table


def _frame_stylesheet(object_name: str) -> str:
    return f"""
    QFrame#{object_name} {{
        background: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["panel"]}px;
    }}
    """


__all__ = [
    "ExtractionField",
    "LaneItem",
    "ReferenceItem",
    "WellItem",
    "WorkbenchPane",
    "make_dense_table_panel",
    "make_extraction_form_table",
    "make_lane_layout_preview",
    "make_left_list_middle_form_right_preview",
    "make_matrix_grid_96_well",
    "make_preview_card",
    "make_reference_queue_panel",
    "make_right_summary_panel",
    "make_splitter_workbench",
    "make_three_column_workbench",
    "make_two_column_workbench",
]
