from __future__ import annotations

import sys

import pytest

QtCore = pytest.importorskip("PySide6.QtCore")
QtWidgets = pytest.importorskip("PySide6.QtWidgets")
QApplication = QtWidgets.QApplication
QFrame = QtWidgets.QFrame
QLabel = QtWidgets.QLabel
QListView = QtWidgets.QListView
QPushButton = QtWidgets.QPushButton
QStackedWidget = QtWidgets.QStackedWidget
QTableView = QtWidgets.QTableView

from app.shared.ui_components import (
    AuditLogEntry,
    EngineStatusItem,
    ExportFormatAction,
    ExportGateCheck,
    ProjectRecentItem,
    ReportSection,
    SettingsResourceItem,
    WizardStepSpec,
    make_audit_log_panel,
    make_export_gate_panel,
    make_external_engine_status_panel,
    make_plot_placeholder,
    make_project_recent_table,
    make_report_viewer_shell,
    make_review_confirmation_panel,
    make_settings_resource_table,
    make_wizard_flow_shell,
)


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication(sys.argv)


def test_report_viewer_shell_is_read_only_and_report_disabled(qt_app) -> None:
    requested = []
    shell = make_report_viewer_shell(
        title="Draft report",
        sections=[
            ReportSection("summary", "Summary", "Draft summary.", status_key="draft"),
            ReportSection("methods", "Methods", "Pending methods.", status_key="report_disabled", semantic_state="report_disabled"),
        ],
        active_key="summary",
        on_section_requested=requested.append,
    )

    assert isinstance(shell, QFrame)
    assert shell.property("uiPrimitive") == "report_viewer_shell"
    assert shell.property("readOnly") is True
    assert shell.property("reportGenerationAllowed") is False
    assert shell.property("exportAllowed") is False
    assert shell.findChild(QListView, "reportViewerSectionList").model().rowCount() == 2
    assert shell.findChild(QStackedWidget, "reportViewerStack").count() == 2
    shell.findChild(QListView, "reportViewerSectionList").setCurrentIndex(
        shell.findChild(QListView, "reportViewerSectionList").model().index(1, 0)
    )
    assert requested == ["methods"]


def test_export_gate_panel_keeps_export_actions_disabled_with_reasons(qt_app) -> None:
    panel = make_export_gate_panel(
        title="Export gate",
        checks=[
            ExportGateCheck("artifact", "Report artifact exists", passed=False, reason="No report artifact."),
            ExportGateCheck("review", "Review complete", passed=True, semantic_state="available"),
        ],
        formats=[
            ExportFormatAction("docx", "DOCX", "Formal report export is not enabled."),
            ExportFormatAction("xlsx", "XLSX", "Table export is not enabled."),
        ],
        artifact_exists=False,
    )

    assert panel.property("uiPrimitive") == "export_gate_panel"
    assert panel.property("exportAllowed") is False
    assert panel.property("fileWriteAllowed") is False
    assert panel.property("artifactExists") is False
    disabled_buttons = panel.findChildren(QPushButton, "disabledActionButton")
    assert len(disabled_buttons) == 2
    assert all(button.isEnabled() is False for button in disabled_buttons)
    assert [label.text() for label in panel.findChildren(QLabel, "disabledActionReason")] == [
        "Formal report export is not enabled.",
        "Table export is not enabled.",
    ]


def test_plot_placeholder_is_not_a_fake_formal_plot(qt_app) -> None:
    placeholder = make_plot_placeholder(
        title="Forest plot",
        plot_type="forest",
        message="Formal plotting is disabled.",
        status_key="planned",
    )

    assert placeholder.property("uiPrimitive") == "plot_placeholder"
    assert placeholder.property("plotType") == "forest"
    assert placeholder.property("formalPlot") is False
    assert placeholder.property("fakePlotData") is False
    assert placeholder.findChild(QLabel, "plotPlaceholderMessage").text() == "Formal plotting is disabled."


def test_external_engine_status_panel_is_detect_only(qt_app) -> None:
    detected = []
    panel = make_external_engine_status_panel(
        title="External engines",
        engines=[
            EngineStatusItem("r", "R", status_key="not_configured", detail="User-managed install required."),
            EngineStatusItem("blast", "BLAST", status_key="adapter_needed", semantic_state="adapter_needed"),
        ],
        on_detect_requested=lambda: detected.append("detect"),
    )

    assert panel.property("uiPrimitive") == "external_engine_status_panel"
    assert panel.property("detectOnly") is True
    assert panel.property("installAllowed") is False
    assert panel.property("engineExecutionAllowed") is False
    assert panel.property("cloudConfigAllowed") is False
    assert len(panel.findChildren(QFrame, "externalEngineStatusRow")) == 2
    button = panel.findChild(QPushButton)
    button.click()
    assert detected == ["detect"]


def test_settings_resource_and_project_recent_tables_are_read_only(qt_app) -> None:
    resources = make_settings_resource_table(
        [
            SettingsResourceItem("r", "R binary", group="Engine", status_key="not_configured", path="/usr/local/bin/R"),
        ]
    )
    assert isinstance(resources, QTableView)
    assert resources.property("uiPrimitive") == "settings_resource_table"
    assert resources.property("resourceDetectionOnly") is True
    assert resources.property("installAllowed") is False
    assert resources.property("horizontalOverflow") is True
    assert resources.model().rowCount() == 1

    projects = make_project_recent_table(
        [
            ProjectRecentItem("p1", "Pilot project", module="LabTools", last_opened="2026-05-25", path="/tmp/pilot"),
        ]
    )
    assert isinstance(projects, QTableView)
    assert projects.property("uiPrimitive") == "project_recent_table"
    assert projects.property("readOnly") is True
    assert projects.property("opensProject") is False
    assert projects.property("fakeRecords") is False
    assert projects.model().rowCount() == 1


def test_wizard_flow_shell_uses_stacked_widget_and_callback_only_navigation(qt_app) -> None:
    requested = []
    shell = make_wizard_flow_shell(
        title="Bio workflow",
        steps=[
            WizardStepSpec("input", "Input", "Prepare files.", status_key="testing", semantic_state="testing"),
            WizardStepSpec("export", "Export", "Disabled.", status_key="export_disabled", semantic_state="export_disabled", enabled=False),
        ],
        current_key="input",
        content_widgets={"input": QLabel("Input content")},
        on_next_requested=requested.append,
    )

    assert shell.property("uiPrimitive") == "wizard_flow_shell"
    assert shell.property("executorAllowed") is False
    assert shell.property("reportGenerationAllowed") is False
    stack = shell.findChild(QStackedWidget, "wizardFlowStack")
    assert stack.count() == 2
    buttons = shell.findChildren(QPushButton)
    next_button = [button for button in buttons if button.property("actionKey") == "wizard_next"][0]
    next_button.click()
    assert requested == ["input"]
    back_button = [button for button in buttons if button.property("actionKey") == "wizard_back"][0]
    assert back_button.isEnabled() is False
    assert back_button.property("disabledReason") == "Back navigation callback is not connected."


def test_review_confirmation_panel_never_enables_final_decision(qt_app) -> None:
    panel = make_review_confirmation_panel(
        title="Review",
        summary_items=[("Dataset", "Draft only")],
        blockers=["Formal analysis is not available."],
        disabled_reason="Reviewer confirmation is gated.",
    )

    assert panel.property("uiPrimitive") == "review_confirmation_panel"
    assert panel.property("finalDecisionEnabled") is False
    assert panel.property("formalApprovalAllowed") is False
    assert panel.findChild(QLabel, "reviewConfirmationSummaryRow").text() == "Dataset: Draft only"
    assert panel.findChild(QLabel, "disabledActionReason").text() == "Reviewer confirmation is gated."


def test_audit_log_panel_is_read_only_and_not_exportable(qt_app) -> None:
    panel = make_audit_log_panel(
        [
            AuditLogEntry("2026-05-25 10:00", "UI", "INFO", "Draft state rendered.", semantic_state="draft"),
        ]
    )

    assert panel.property("uiPrimitive") == "audit_log_panel"
    assert panel.property("readOnly") is True
    assert panel.property("diagnosticOnly") is True
    assert panel.property("exportAllowed") is False
    table = panel.findChild(QTableView, "auditLogTable")
    assert table.property("uiPrimitive") == "audit_log_table"
    assert table.model().rowCount() == 1
    assert table.property("horizontalOverflow") is True
