from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QPushButton, QTableWidget, QTextEdit

    from app.bioinformatics.analysis_ui.state import build_analysis_center_state
    from app.bioinformatics.project_workspace import create_bioinformatics_project
    from app.bioinformatics.workspace import BioinformaticsWorkspaceWidget
    from app.bioinformatics.workflow_pages import (
        BioinformaticsReportViewerWidget,
        BioinformaticsResultsBrowserWidget,
    )
    from app.shared.semantic_keys import ReportStatusKey, ResultSemanticKey
except Exception as exc:  # pragma: no cover - optional GUI runtime.
    QApplication = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


@pytest.fixture
def bio_project(tmp_path: Path):
    return create_bioinformatics_project("C2f Result Report Export", tmp_path)


def _table_text(table: QTableWidget) -> str:
    return " ".join(
        table.item(row, column).text()
        for row in range(table.rowCount())
        for column in range(table.columnCount())
        if table.item(row, column) is not None
    )


def test_result_report_and_report_export_are_separate_ia_nodes(qt_app, bio_project) -> None:
    workspace = BioinformaticsWorkspaceWidget()
    try:
        assert workspace.main_flow_page_keys() == (
            "project_home",
            "data_source",
            "data_check_preparation",
            "group_design",
            "analysis_tasks",
            "result_report",
            "report_export",
        )

        workspace.show_results_browser(bio_project)
        assert workspace.current_page_object_name() == "bioinformaticsResultsBrowserPage"
        assert workspace.current_target_page_key() == "result_report"

        workspace.show_report_viewer(bio_project)
        assert workspace.current_page_object_name() == "bioinformaticsReportViewerPage"
        assert workspace.current_target_page_key() == "report_export"
    finally:
        workspace.close()
        workspace.deleteLater()


def test_result_report_page_is_preflight_and_draft_only(qt_app, bio_project) -> None:
    widget = BioinformaticsResultsBrowserWidget()
    try:
        widget.refresh_project(bio_project)

        gate_table = widget.findChild(QTableWidget, "bioinformaticsResultReportGateTable")
        preflight_log = widget.findChild(QTextEdit, "bioinformaticsPreflightLogPreview")
        result_preview = widget.findChild(QTextEdit, "bioinformaticsResultGatePreview")
        add_to_report = widget.findChild(QPushButton, "bioinformaticsAddToReportDisabledButton")
        generate_report = widget.findChild(QPushButton, "bioinformaticsResultReportGenerateReportDisabledButton")
        table_text = _table_text(gate_table)
        preflight_text = preflight_log.toPlainText()

        assert "result gate" in table_text
        assert "report draft gate" in table_text
        assert "formal result missing" in table_text
        assert "generate report" in table_text
        assert gate_table.property("resultSemanticKey") == ResultSemanticKey.TESTING_SUMMARY_ONLY.value
        assert gate_table.property("reportStatusKey") == ReportStatusKey.DRAFT.value
        assert gate_table.property("exportGate") == "disabled_missing_report_ready"
        assert preflight_log.property("resultSemanticKey") == "preflight_only"
        assert '"formal_computed_result": false' in preflight_text
        assert '"fake_deg_table_allowed": false' in preflight_text
        assert '"fake_plot_allowed": false' in preflight_text
        assert '"report_ready_package_allowed": false' in preflight_text
        assert result_preview.property("resultSemanticKey") != ResultSemanticKey.FORMAL_COMPUTED_RESULT.value
        assert result_preview.property("reportStatusKey") != "report.status.report_ready"
        assert add_to_report.isEnabled() is False
        assert add_to_report.property("formalActionEnabled") is False
        assert generate_report.isEnabled() is False
        assert generate_report.property("reportReadyPackageAllowed") is False
        assert "暂无 formal result" in widget.status_message()
    finally:
        widget.close()
        widget.deleteLater()


def test_report_export_page_keeps_all_formats_disabled_and_writes_no_files(qt_app, bio_project) -> None:
    widget = BioinformaticsReportViewerWidget()
    try:
        reports_dir = bio_project.project_root / "reports"
        exports_dir = bio_project.project_root / "exports"
        widget.refresh_project(bio_project)

        export_preview = widget.findChild(QTextEdit, "bioinformaticsReportExportGatePreview")
        format_gate = widget.findChild(QTableWidget, "bioinformaticsReportExportFormatGateTable")
        generate_report = widget.findChild(QPushButton, "bioinformaticsGenerateReportDisabledButton")
        legacy_export_buttons = widget.findChildren(QPushButton, "bioinformaticsReportExportDisabledButton")
        format_export_buttons = widget.findChildren(QPushButton, "bioinformaticsReportExportFormatDisabledButton")
        format_text = _table_text(format_gate)

        assert export_preview.property("exportGate") == "disabled_missing_report_ready"
        assert export_preview.property("reportReadyPackageAllowed") is False
        assert "formal result missing" in export_preview.toPlainText()
        assert "export adapter not connected" in export_preview.toPlainText()
        assert "split_report_export_page_no_report_generation_no_file_export" in export_preview.toPlainText()
        assert "DOCX" in format_text and "HTML" in format_text and "PDF" in format_text
        assert "CSV" in format_text and "XLSX" in format_text
        assert format_gate.property("exportGate") == "disabled_missing_report_ready"
        assert generate_report.isEnabled() is False
        assert generate_report.property("reportReadyPackageAllowed") is False
        assert legacy_export_buttons
        assert format_export_buttons
        assert all(button.isEnabled() is False for button in legacy_export_buttons)
        assert all(button.isEnabled() is False for button in format_export_buttons)
        assert all(button.property("exportGate") == "disabled_missing_report_ready" for button in format_export_buttons)
        assert {button.property("exportFormatKey") for button in format_export_buttons} == {
            "export.format.docx",
            "export.format.html",
            "export.format.pdf",
            "export.format.csv",
            "export.format.xlsx",
        }
        assert not (reports_dir / "project_analysis_report.md").exists()
        assert not exports_dir.exists()
    finally:
        widget.close()
        widget.deleteLater()


def test_c2f_gate_state_keeps_formal_result_report_and_export_blocked(qt_app, bio_project) -> None:
    state = build_analysis_center_state(bio_project.project_root)

    assert state["result_gate"]["result_semantic_key"] != ResultSemanticKey.FORMAL_COMPUTED_RESULT.value
    assert state["result_gate"]["fake_result_allowed"] is False
    assert state["result_gate"]["fake_plot_allowed"] is False
    assert state["report_gate"]["report_status_key"] == ReportStatusKey.DRAFT.value
    assert state["report_gate"]["report_ready_package_allowed"] is False
    assert state["export_gate"]["export_enabled"] is False
    assert state["export_gate"]["export_gate"] == "disabled_missing_report_ready"
