from __future__ import annotations

import sys

import pytest

QtWidgets = pytest.importorskip("PySide6.QtWidgets")
QApplication = QtWidgets.QApplication
QFrame = QtWidgets.QFrame
QLabel = QtWidgets.QLabel
QPushButton = QtWidgets.QPushButton
QScrollArea = QtWidgets.QScrollArea
QTableWidget = QtWidgets.QTableWidget

from app.shared.ui_components import (
    WorkbenchActionSpec,
    WorkbenchNavItem,
    make_status_chip,
    make_workbench_action_bar,
    make_workbench_content_area,
    make_workbench_disabled_action,
    make_workbench_notice,
    make_workbench_right_panel,
    make_workbench_secondary_nav,
    make_workbench_section,
    make_workbench_shell,
    make_workbench_status_row,
    make_workbench_table,
)


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication(sys.argv)


def test_workbench_shell_sets_stable_layout_properties(qt_app) -> None:
    nav = make_workbench_secondary_nav(
        [
            WorkbenchNavItem("home", "Home", status_key="testing", current=True),
            WorkbenchNavItem("export", "Export", status_key="blocked", enabled=False),
        ]
    )
    content = make_workbench_content_area([make_workbench_section(title="Main")])
    right_panel = make_workbench_right_panel(title="Gate", content_widgets=[make_workbench_notice("Export disabled.")])
    action_bar = make_workbench_action_bar(
        [WorkbenchActionSpec("export", "Export", enabled=False, disabled_state="export_gate_disabled")]
    )

    shell = make_workbench_shell(
        title="Runtime Page",
        subtitle="Uses shared layout primitives.",
        object_name="testWorkbenchShell",
        module_key="meta",
        page_key="result_review",
        status_widgets=[make_status_chip("No formal result", status_key="blocked")],
        secondary_nav=nav,
        main_content=content,
        right_panel=right_panel,
        action_bar=action_bar,
    )

    assert shell.objectName() == "testWorkbenchShell"
    assert shell.property("uiPrimitive") == "workbench_shell"
    assert shell.property("moduleKey") == "meta"
    assert shell.property("pageKey") == "result_review"
    assert shell.property("layoutPolishNoOverlap") is True
    assert shell.findChild(QFrame, "workbenchBody") is not None
    assert shell.findChild(QScrollArea, "workbenchContentArea") is not None
    assert shell.findChild(QFrame, "workbenchRightPanel") is not None
    assert shell.findChild(QFrame, "workbenchActionBar") is not None


def test_secondary_nav_keeps_navigation_separate_from_formal_actions(qt_app) -> None:
    nav = make_workbench_secondary_nav(
        [
            WorkbenchNavItem("project_home", "Project Home", status_key="testing", current=True),
            WorkbenchNavItem("export", "Report Export", status_key="blocked", enabled=False),
        ],
        title="Meta workflow",
    )

    buttons = nav.findChildren(QPushButton, "workbenchSecondaryNavItem")
    assert [button.property("pageKey") for button in buttons] == ["project_home", "export"]
    assert buttons[0].property("currentStep") is True
    assert buttons[1].isEnabled() is False
    assert all(button.property("formalActionEnabled") is False for button in buttons)
    assert all(button.property("fileWriteAllowed") is False for button in buttons)


def test_workbench_disabled_actions_preserve_gate_semantics(qt_app) -> None:
    button = make_workbench_disabled_action(
        "Generate Report",
        action_key="generate_report",
        disabled_state="report_not_ready",
        tooltip="Formal report generation is disabled.",
    )
    assert button.objectName() == "workbenchDisabledAction"
    assert button.isEnabled() is False
    assert button.property("actionKey") == "generate_report"
    assert button.property("disabledState") == "report_not_ready"
    assert button.property("formalActionEnabled") is False
    assert button.property("fileWriteAllowed") is False


def test_status_row_notice_table_and_right_panel_are_readable_primitives(qt_app) -> None:
    status_row = make_workbench_status_row(
        [("Developer Preview", "developer_preview"), ("Export disabled", "blocked")]
    )
    assert status_row.property("uiPrimitive") == "workbench_status_row"
    assert len(status_row.findChildren(QLabel, "uiStatusChip")) == 2

    table = make_workbench_table(
        headers=["Key", "State"],
        rows=[["result_semantic", "no_formal_result"], ["export_gate", "disabled"]],
    )
    assert isinstance(table, QTableWidget)
    assert table.objectName() == "workbenchTable"
    assert table.property("uiPrimitive") == "workbench_table"
    assert table.property("readOnly") is True
    assert table.item(0, 1).text() == "no_formal_result"

    panel = make_workbench_right_panel(title="Gate Summary", content_widgets=[status_row, table])
    assert panel.property("uiPrimitive") == "workbench_right_panel"
    assert panel.minimumWidth() >= 280
    assert panel.maximumWidth() <= 360
