from __future__ import annotations

import sys

import pytest

QtCore = pytest.importorskip("PySide6.QtCore")
QtWidgets = pytest.importorskip("PySide6.QtWidgets")
QApplication = QtWidgets.QApplication
QFrame = QtWidgets.QFrame
QLabel = QtWidgets.QLabel
QLineEdit = QtWidgets.QLineEdit
QListView = QtWidgets.QListView
QSplitter = QtWidgets.QSplitter
QTableView = QtWidgets.QTableView
QTableWidget = QtWidgets.QTableWidget
Qt = QtCore.Qt

from app.shared.ui_components import (
    DataTableColumn,
    ExtractionField,
    LaneItem,
    ReferenceItem,
    WarningItem,
    WellItem,
    WorkbenchPane,
    make_dense_table_panel,
    make_extraction_form_table,
    make_lane_layout_preview,
    make_left_list_middle_form_right_preview,
    make_matrix_grid_96_well,
    make_preview_card,
    make_reference_queue_panel,
    make_right_summary_panel,
    make_splitter_workbench,
    make_three_column_workbench,
    make_two_column_workbench,
)


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication(sys.argv)


def _frame(name: str) -> QFrame:
    frame = QFrame()
    frame.setObjectName(name)
    return frame


def test_two_and_three_column_workbenches_set_layout_contracts(qt_app) -> None:
    two = make_two_column_workbench(left_widget=_frame("left"), right_widget=_frame("right"))
    assert isinstance(two, QFrame)
    assert two.property("uiPrimitive") == "two_column_workbench"
    assert two.property("layoutPolishNoOverlap") is True

    three = make_three_column_workbench(
        left_widget=_frame("leftPane"),
        middle_widget=_frame("middlePane"),
        right_widget=_frame("rightPane"),
    )
    assert isinstance(three, QSplitter)
    assert three.property("uiPrimitive") == "three_column_workbench"
    assert three.property("rightPanelMinWidth") == 280
    assert three.property("rightPanelMaxWidth") == 360
    assert three.count() == 3
    assert three.widget(2).minimumWidth() == 280
    assert three.widget(2).maximumWidth() == 360


def test_left_list_middle_form_right_preview_and_splitter_use_qsplitter(qt_app) -> None:
    composite = make_left_list_middle_form_right_preview(
        list_widget=_frame("listPane"),
        form_widget=_frame("formPane"),
        preview_widget=_frame("previewPane"),
    )
    assert isinstance(composite, QSplitter)
    assert composite.property("uiPrimitive") == "left_list_middle_form_right_preview"
    assert composite.count() == 3
    assert composite.widget(2).maximumWidth() == 360

    splitter = make_splitter_workbench(
        panes=[
            WorkbenchPane("a", "A", _frame("a"), min_width=100, stretch=0),
            WorkbenchPane("b", "B", _frame("b"), min_width=200, stretch=1),
        ],
        orientation="horizontal",
    )
    assert isinstance(splitter, QSplitter)
    assert splitter.property("uiPrimitive") == "splitter_workbench"
    assert splitter.count() == 2
    assert splitter.widget(0).minimumWidth() == 100


def test_right_summary_panel_is_constrained_to_review_width(qt_app) -> None:
    panel = make_right_summary_panel(
        title="Gate summary",
        status_items=[("Draft", "draft")],
        key_values=[("Result", "No formal output")],
        warnings=[WarningItem("blocked", "Export blocked", "No report-ready artifact.")],
    )
    assert panel.property("uiPrimitive") == "right_summary_panel"
    assert panel.minimumWidth() == 280
    assert panel.maximumWidth() == 360
    assert panel.findChild(QLabel, "rightSummaryPanelRow").text() == "Result: No formal output"


def test_dense_table_panel_uses_table_view_with_horizontal_overflow(qt_app) -> None:
    panel = make_dense_table_panel(
        title="Readiness matrix",
        columns=[
            DataTableColumn("task", "Task", 180),
            DataTableColumn("status", "Long scientific status header", 260),
        ],
        rows=[{"task": "DEG", "status": "preflight-only"}],
    )
    assert panel.property("uiPrimitive") == "dense_table_panel"
    assert panel.property("remoteFetchAllowed") is False
    assert panel.findChild(QLineEdit, "denseTablePanelFilter").property("remoteFetchAllowed") is False
    table = panel.findChild(QTableView, "denseTablePanelTable")
    assert table is not None
    assert table.property("horizontalOverflow") is True
    assert table.columnWidth(1) >= 260


def test_preview_card_requires_non_formal_status_chip(qt_app) -> None:
    preview = make_preview_card(
        title="Draft report preview",
        preview_widget=QLabel("Preview only"),
        status_key="draft",
        semantic_state="draft",
        caption="Not a formal report.",
    )
    assert preview.property("uiPrimitive") == "preview_card"
    assert preview.property("requiresNonFormalStatusChip") is True
    assert preview.property("formalResult") is False
    assert preview.findChild(QLabel, "uiStatusChip").property("semanticState") == "draft"


def test_lane_layout_preview_has_no_fake_band_or_image_analysis_state(qt_app) -> None:
    preview = make_lane_layout_preview(
        [
            LaneItem("lane1", "L1", sample="Sample A", volume="12 ug", warning=""),
            LaneItem("lane2", "L2", sample="Sample B", volume="8 ug", warning="Low input"),
        ]
    )
    assert preview.property("uiPrimitive") == "lane_layout_preview"
    assert preview.property("fakeBandRendering") is False
    assert preview.property("imageAnalysisEnabled") is False
    assert len(preview.findChildren(QFrame, "laneLayoutPreviewLane")) == 2


def test_matrix_grid_96_well_is_read_only_and_selectable(qt_app) -> None:
    grid = make_matrix_grid_96_well(
        [
            WellItem("A", 1, "Ctrl", semantic_state="draft", selected=True),
            WellItem("H", 12, "Blank", semantic_state="planned"),
        ]
    )
    assert isinstance(grid, QTableWidget)
    assert grid.property("uiPrimitive") == "matrix_grid_96_well"
    assert grid.property("readOnly") is True
    assert grid.property("editable") is False
    assert grid.editTriggers() == QtWidgets.QAbstractItemView.NoEditTriggers
    assert grid.item(0, 0).text() == "Ctrl"
    assert grid.item(0, 0).data(Qt.UserRole) == "draft"
    assert grid.item(7, 11).text() == "Blank"


def test_reference_queue_panel_is_splitter_and_keeps_decisions_non_final(qt_app) -> None:
    selected = []
    panel = make_reference_queue_panel(
        references=[
            ReferenceItem("ref1", "Reference 1", "Draft screening", status_key="draft"),
            ReferenceItem("ref2", "Reference 2", "AI advisory only", status_key="testing"),
        ],
        on_reference_selected=selected.append,
    )
    assert isinstance(panel, QSplitter)
    assert panel.property("uiPrimitive") == "reference_queue_panel"
    assert panel.property("aiSuggestionAdvisoryOnly") is True
    assert panel.property("finalDecisionEnabled") is False
    queue = panel.findChild(QListView, "referenceQueueList")
    assert queue.model().rowCount() == 2
    queue.setCurrentIndex(queue.model().index(0, 0))
    assert selected == ["ref1"]


def test_extraction_form_table_is_draft_only_table_view(qt_app) -> None:
    table = make_extraction_form_table(
        [
            ExtractionField("effect", "Effect size", value="OR draft", status_key="draft", notes="Reviewer check required."),
        ]
    )
    assert isinstance(table, QTableView)
    assert table.property("uiPrimitive") == "extraction_form_table"
    assert table.property("draftOnly") is True
    assert table.property("formalAnalysisInput") is False
    assert table.model().rowCount() == 1
