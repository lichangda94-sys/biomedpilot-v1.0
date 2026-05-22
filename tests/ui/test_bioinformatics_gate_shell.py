from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QPushButton, QTableWidget, QTextEdit

    from app.bioinformatics.analysis_ui.state import build_analysis_center_state
    from app.bioinformatics.project_workspace import create_bioinformatics_project
    from app.bioinformatics.workflow_pages import (
        BioinformaticsAnalysisTaskCenterWidget,
        BioinformaticsReportViewerWidget,
        BioinformaticsResultsBrowserWidget,
    )
    from app.bioinformatics.workspace import BioinformaticsWorkspaceWidget
    from app.shared.semantic_keys import AnalysisStatusKey, ReportStatusKey, ResultSemanticKey
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
    return create_bioinformatics_project("Gate Shell Project", tmp_path)


def _table_rows(table: QTableWidget) -> list[list[str]]:
    return [
        [table.item(row, column).text() if table.item(row, column) is not None else "" for column in range(table.columnCount())]
        for row in range(table.rowCount())
    ]


def test_gate_state_keeps_formal_actions_disabled_without_artifact_writes(bio_project) -> None:
    state = build_analysis_center_state(bio_project.project_root)
    actions = {row["action_id"]: row for row in state["action_rows"]}

    assert state["schema_version"] == "biomedpilot.bioinformatics_gate_shell_state.v1"
    assert state["source_policy"] == "read_only_gate_preview_no_executor_no_artifact_write"
    assert actions["deg_preflight"]["enabled"] is True
    assert actions["formal_deg"]["enabled"] is False
    assert actions["formal_ora"]["enabled"] is False
    assert actions["formal_gsea"]["enabled"] is False
    assert actions["km_logrank"]["enabled"] is False
    assert actions["cox_univariate"]["enabled"] is False
    assert actions["report_ready_package"]["enabled"] is False
    assert actions["export_package"]["enabled"] is False
    assert all(row["formal_action_enabled"] is False for row in actions.values())
    assert state["result_gate"]["fake_result_allowed"] is False
    assert state["result_gate"]["fake_plot_allowed"] is False
    assert state["report_gate"]["report_ready_package_allowed"] is False
    assert state["export_gate"]["export_enabled"] is False


def test_gate_state_does_not_upgrade_imported_testing_or_preflight_results(bio_project) -> None:
    index_path = bio_project.project_root / "results" / "summaries" / "result_index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps(
            {
                "entries": [
                    {"result_id": "imported-1", "result_semantics": "imported_external_result"},
                    {"result_id": "testing-1", "result_semantics": "testing_level"},
                    {"result_id": "preflight-1", "result_semantics": "preflight_only"},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    state = build_analysis_center_state(bio_project.project_root)

    assert state["result_gate"]["formal_computed_result_count"] == 0
    assert state["result_gate"]["imported_external_result_count"] == 1
    assert state["result_gate"]["preflight_only_count"] == 1
    assert state["result_gate"]["result_semantic_key"] == ResultSemanticKey.IMPORTED_EXTERNAL_RESULT.value
    assert state["report_gate"]["report_ready_package_allowed"] is False
    assert state["export_gate"]["export_gate"] == "disabled_missing_report_ready"


def test_analysis_task_center_shows_gate_matrix_and_disables_geo_formal_button(qt_app, bio_project) -> None:
    widget = BioinformaticsAnalysisTaskCenterWidget()
    try:
        widget.refresh_project(bio_project)
        geo_button = widget.findChild(QPushButton, "bioinformaticsFormalDegDisabledButton")
        gate_table = widget.findChild(QTableWidget, "bioinformaticsActionGateMatrix")
        rows = _table_rows(gate_table)
        by_action = {row[0]: row for row in rows}

        assert geo_button is not None
        assert geo_button.isEnabled() is False
        assert geo_button.property("formalActionEnabled") is False
        assert geo_button.property("gateState") == "developer_diagnostics_only"
        assert gate_table.property("formalActionEnabled") is False
        assert by_action["formal_deg"][2] == "disabled"
        assert by_action["formal_gsea"][2] == "disabled"
        assert by_action["km_logrank"][2] == "disabled"
        assert by_action["cox_univariate"][2] == "disabled"
    finally:
        widget.close()
        widget.deleteLater()


def test_result_and_report_export_gate_previews_remain_disabled(qt_app, bio_project) -> None:
    results = BioinformaticsResultsBrowserWidget()
    report = BioinformaticsReportViewerWidget()
    try:
        results.refresh_project(bio_project)
        report.refresh_project(bio_project)

        result_preview = results.findChild(QTextEdit, "bioinformaticsResultGatePreview")
        add_to_report = results.findChild(QPushButton, "bioinformaticsAddToReportDisabledButton")
        export_preview = report.findChild(QTextEdit, "bioinformaticsReportExportGatePreview")
        generate_report = report.findChild(QPushButton, "bioinformaticsGenerateReportDisabledButton")
        export_buttons = report.findChildren(QPushButton, "bioinformaticsReportExportDisabledButton")

        assert result_preview.property("formalActionEnabled") is False
        assert result_preview.property("resultSemanticKey") == ResultSemanticKey.TESTING_SUMMARY_ONLY.value
        assert result_preview.property("reportStatusKey") == ReportStatusKey.DRAFT.value
        assert result_preview.property("exportGate") == "disabled_missing_report_ready"
        assert add_to_report.isEnabled() is False
        assert add_to_report.property("formalActionEnabled") is False
        assert export_preview.property("exportGate") == "disabled_missing_report_ready"
        assert export_preview.property("reportReadyPackageAllowed") is False
        assert generate_report.isEnabled() is False
        assert generate_report.property("reportReadyPackageAllowed") is False
        assert export_buttons
        assert all(button.isEnabled() is False for button in export_buttons)
        assert all(button.property("exportGate") == "disabled_missing_report_ready" for button in export_buttons)
        assert '"fake_result_allowed": false' in result_preview.toPlainText()
        assert '"fake_plot_allowed": false' in result_preview.toPlainText()
    finally:
        results.close()
        report.close()
        results.deleteLater()
        report.deleteLater()


def test_bioinformatics_seven_step_ia_remains_unchanged(qt_app) -> None:
    widget = BioinformaticsWorkspaceWidget()
    try:
        assert widget.main_flow_page_keys() == (
            "project_home",
            "data_source",
            "data_check_preparation",
            "group_design",
            "analysis_tasks",
            "result_report",
            "report_export",
        )
        assert widget.target_ia_page_keys()[:7] == widget.main_flow_page_keys()
        nav_buttons = widget.findChildren(QPushButton, "bioinformaticsIANavItem")
        assert all(button.property("formalActionEnabled") is False for button in nav_buttons)
        result_button = next(button for button in nav_buttons if button.property("pageKey") == "result_report")
        export_button = next(button for button in nav_buttons if button.property("pageKey") == "report_export")
        assert result_button.property("statusSemanticKey") == ResultSemanticKey.TESTING_SUMMARY_ONLY.value
        assert export_button.property("statusSemanticKey") == ReportStatusKey.TESTING_SUMMARY.value
    finally:
        widget.close()
        widget.deleteLater()
