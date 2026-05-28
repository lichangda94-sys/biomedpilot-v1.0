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
QPushButton = QtWidgets.QPushButton
QTabBar = QtWidgets.QTabBar
QTableView = QtWidgets.QTableView
Qt = QtCore.Qt

from app.shared.ui_components import (
    ComponentAction,
    DataTableColumn,
    HistoryItem,
    KeyValueItem,
    NavTab,
    WarningItem,
    WorkflowStep,
    make_data_table,
    make_disabled_action_button,
    make_file_picker_button,
    make_form_field_row,
    make_gate_notice,
    make_history_list,
    make_key_value_panel,
    make_module_entry_card,
    make_result_panel,
    make_secondary_nav_tabs,
    make_warning_list,
    make_workflow_stepper,
)


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication(sys.argv)


def test_module_entry_card_is_navigation_only(qt_app) -> None:
    card = make_module_entry_card(
        title="Bioinformatics / 生信分析",
        description="Project workflow entry.",
        module_key="module.bioinformatics",
        page_key="bio.page.project_home",
        icon_key="module.bioinformatics",
        status_key="testing",
        action=ComponentAction("open_bio", "进入", callback=lambda: None),
    )

    assert isinstance(card, QFrame)
    assert card.property("uiPrimitive") == "module_entry_card"
    assert card.property("moduleKey") == "module.bioinformatics"
    button = card.findChild(QPushButton)
    assert button.property("formalActionEnabled") is False
    assert button.property("fileWriteAllowed") is False


def test_workflow_stepper_uses_vertical_steps_and_safe_callbacks(qt_app) -> None:
    requested = []
    stepper = make_workflow_stepper(
        [
            WorkflowStep("home", "Project Home", status_key="testing", semantic_state="testing", current=True),
            WorkflowStep("export", "Report Export", status_key="blocked", semantic_state="export_disabled", enabled=False, disabled_reason="Export disabled."),
        ],
        title="Bio workflow",
        on_step_requested=requested.append,
    )

    assert stepper.property("uiPrimitive") == "workflow_stepper"
    assert stepper.property("orientation") == "vertical"
    buttons = stepper.findChildren(QPushButton, "workflowStepperButton")
    assert [button.property("actionKey") for button in buttons] == ["home", "export"]
    assert buttons[0].property("semanticState") == "testing"
    assert buttons[1].isEnabled() is False
    assert buttons[1].property("disabledReason") == "Export disabled."
    buttons[0].click()
    assert requested == ["home"]


def test_secondary_nav_tabs_wrap_qtabbar_without_content_ownership(qt_app) -> None:
    changed = []
    tabs = make_secondary_nav_tabs(
        [
            NavTab("general", "常规设置"),
            NavTab("engines", "外部引擎", enabled=False, tooltip="Detect-only."),
        ],
        active_key="general",
        on_tab_changed=changed.append,
    )

    assert isinstance(tabs, QTabBar)
    assert tabs.property("uiPrimitive") == "secondary_nav_tabs"
    assert tabs.tabData(0) == "general"
    assert tabs.isTabEnabled(1) is False
    assert tabs.property("activeKey") == "general"


def test_data_table_uses_table_view_model_and_horizontal_overflow(qt_app) -> None:
    table = make_data_table(
        columns=[
            DataTableColumn("name", "Dataset name", min_width=180),
            DataTableColumn("state", "Very long scientific readiness state", min_width=240),
        ],
        rows=[
            {"name": "GSE000001", "state": "preflight-only"},
            {"name": "GSE000002", "state": "blocked"},
        ],
    )

    assert isinstance(table, QTableView)
    assert table.property("uiPrimitive") == "data_table"
    assert table.property("readOnly") is True
    assert table.property("horizontalOverflow") is True
    assert table.horizontalScrollBarPolicy() == Qt.ScrollBarAsNeeded
    assert table.model().rowCount() == 2
    assert table.model().columnCount() == 2
    assert table.columnWidth(1) >= 240


def test_form_field_row_exposes_help_validation_and_disabled_reason(qt_app) -> None:
    field = QLineEdit()
    row = make_form_field_row(
        label="Concentration",
        field_widget=field,
        help_text="Use project units.",
        validation_text="Missing value.",
        semantic_state="blocked",
        required=True,
        disabled_reason="Adapter needed.",
    )

    assert row.property("uiPrimitive") == "form_field_row"
    assert row.property("semanticState") == "blocked"
    assert row.property("required") is True
    assert row.property("disabledReason") == "Adapter needed."
    assert row.findChild(QLineEdit) is field
    assert row.findChild(QLabel, "formFieldRowValidation").text() == "Missing value."


def test_key_value_panel_and_history_list_are_read_only_state_surfaces(qt_app) -> None:
    panel = make_key_value_panel(
        title="Project status",
        items=[
            KeyValueItem("project", "Project", "Demo", status_key="testing", semantic_state="testing"),
            KeyValueItem("export", "Export", "Disabled", status_key="export_disabled", semantic_state="export_disabled"),
        ],
    )
    assert panel.property("uiPrimitive") == "key_value_panel"
    assert len(panel.findChildren(QLabel, "keyValuePanelValue")) == 2

    history = make_history_list(
        items=[
            HistoryItem("draft-1", "Draft preparation", timestamp="2026-05-25", status_key="draft"),
        ]
    )
    assert isinstance(history, QListView)
    assert history.property("uiPrimitive") == "history_list"
    assert history.property("readOnly") is True
    assert history.model().rowCount() == 1


def test_result_panel_warning_list_and_gate_notice_preserve_disabled_states(qt_app) -> None:
    result = make_result_panel(
        title="Result preview",
        semantic_state="preflight_only",
        status_key="preflight_only",
        actions=[
            ComponentAction("export", "Export", enabled=False, semantic_state="export_disabled", disabled_reason="No report artifact."),
        ],
    )
    assert result.property("uiPrimitive") == "result_panel"
    assert result.property("semanticState") == "preflight_only"
    assert result.findChild(QPushButton).isEnabled() is False
    assert result.findChild(QPushButton).property("disabledReason") == "No report artifact."

    warnings = make_warning_list(
        [
            WarningItem("missing", "Missing input", "Select a project first.", source="Bioinformatics"),
        ]
    )
    assert warnings.property("uiPrimitive") == "warning_list"
    assert warnings.findChild(QFrame, "uiInfoBanner") is not None

    gate = make_gate_notice(
        title="Export gate",
        body="Export is disabled.",
        blockers=["No report-ready artifact."],
        disabled_actions=[
            ComponentAction("docx", "DOCX", enabled=False, semantic_state="export_disabled", disabled_reason="Report gate not passed."),
        ],
        semantic_state="export_disabled",
    )
    assert gate.property("uiPrimitive") == "gate_notice"
    assert gate.property("semanticState") == "export_disabled"
    assert gate.findChild(QLabel, "disabledActionReason").text() == "Report gate not passed."


def test_file_picker_and_disabled_action_button_are_callback_only_and_reason_visible(qt_app) -> None:
    requested = []
    picker = make_file_picker_button("选择本地目录", on_requested=lambda: requested.append("pick"))
    assert picker.property("uiPrimitive") == "file_picker_button"
    assert picker.property("localOnly") is True
    assert picker.property("formalExport") is False
    assert picker.property("fileWriteAllowed") is False
    picker.click()
    assert requested == ["pick"]

    disabled = make_disabled_action_button(
        "Generate report",
        action_key="generate_report",
        semantic_state="report_disabled",
        disabled_reason="Formal report generation is disabled.",
    )
    assert disabled.property("uiPrimitive") == "disabled_action_button"
    assert disabled.property("disabledReason") == "Formal report generation is disabled."
    button = disabled.findChild(QPushButton, "disabledActionButton")
    assert button.isEnabled() is False
    assert disabled.findChild(QLabel, "disabledActionReason").text() == "Formal report generation is disabled."
