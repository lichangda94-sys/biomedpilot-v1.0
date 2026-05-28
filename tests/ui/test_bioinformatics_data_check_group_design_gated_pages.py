from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QPushButton, QTableWidget, QTextEdit

    from app.bioinformatics.analysis_ui.state import build_analysis_center_state
    from app.bioinformatics.project_workspace import create_bioinformatics_project
    from app.bioinformatics.workflow_pages import (
        BioinformaticsGroupComparisonDesignWidget,
        BioinformaticsReadinessDashboardWidget,
        BioinformaticsStandardizedAssetsWidget,
    )
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
    return create_bioinformatics_project("C2d Gated Project", tmp_path)


def _table_text(table: QTableWidget) -> str:
    return " ".join(
        table.item(row, column).text()
        for row in range(table.rowCount())
        for column in range(table.columnCount())
        if table.item(row, column) is not None
    )


def test_data_check_preparation_page_shows_readiness_table_without_formal_outputs(qt_app, bio_project) -> None:
    widget = BioinformaticsReadinessDashboardWidget()
    widget.refresh_project(bio_project)

    table = widget.findChild(QTableWidget, "bioinformaticsDataCheckReadinessTable")
    summary = widget.findChild(QTextEdit, "bioinformaticsDataCheckReadinessSummary")
    save_report = widget.findChild(QPushButton, "bioinformaticsDataCheckSaveReportDisabledButton")
    table_text = _table_text(table)

    assert widget.objectName() == "bioinformaticsReadinessDashboardPage"
    assert "expression matrix integrity" in table_text
    assert "sample annotation completeness" in table_text
    assert "clinical data completeness" in table_text
    assert "gene annotation mapping" in table_text
    assert "batch/platform consistency" in table_text
    assert "missing rate check" in table_text
    assert "outlier sample detection" in table_text
    assert "formal quality score" not in summary.toPlainText().lower()
    assert "No fake matrix, result, plot, report, or export" in summary.toPlainText()
    assert save_report.isEnabled() is False
    assert save_report.property("formalActionEnabled") is False
    assert not (bio_project.project_root / "results" / "summaries" / "result_index.json").exists()


def test_standardization_report_export_is_gated_not_written(qt_app, bio_project) -> None:
    widget = BioinformaticsStandardizedAssetsWidget()
    widget.refresh_project(bio_project)
    button = widget.findChild(QPushButton, "bioinformaticsStandardizationExportReportDisabledButton")

    result = widget.export_standardization_report()

    assert result is None
    assert button.isEnabled() is False
    assert button.property("buttonBehavior") == "disabled_file_picker_required"
    assert "未生成报告文件" in widget.status_message()
    assert not (bio_project.project_root / "reports" / "standardization_report.md").exists()


def test_group_design_page_shows_draft_groups_covariates_and_gated_preflight(qt_app, bio_project) -> None:
    widget = BioinformaticsGroupComparisonDesignWidget()
    widget.refresh_project(bio_project)

    group_table = widget.findChild(QTableWidget, "bioinformaticsGroupSetupGatedTable")
    comparison_table = widget.findChild(QTableWidget, "bioinformaticsComparisonSetupGatedTable")
    covariate_table = widget.findChild(QTableWidget, "bioinformaticsCovariateSettingsTable")
    design_summary = widget.findChild(QTextEdit, "bioinformaticsDesignSummary")
    run_preflight = widget.findChild(QPushButton, "bioinformaticsRunPreflightGatedButton")

    assert "Tumor" in _table_text(group_table)
    assert "Normal" in _table_text(group_table)
    assert "Optional unused group" in _table_text(group_table)
    assert "Tumor_vs_Normal" in _table_text(comparison_table)
    assert "Age" in _table_text(covariate_table)
    assert "Gender" in _table_text(covariate_table)
    assert "Smoking History" in _table_text(covariate_table)
    assert "Stage" in _table_text(covariate_table)
    assert "ready_for_preflight does not create formal_computed_result" in design_summary.toPlainText()
    assert run_preflight.isEnabled() is False
    assert run_preflight.property("formalActionEnabled") is False
    assert run_preflight.property("buttonBehavior") == "disabled_gated_preflight_preview"


def test_c2d_gates_do_not_enable_result_report_or_export(qt_app, bio_project) -> None:
    state = build_analysis_center_state(bio_project.project_root)

    assert state["result_gate"]["fake_result_allowed"] is False
    assert state["result_gate"]["fake_plot_allowed"] is False
    assert state["report_gate"]["report_ready_package_allowed"] is False
    assert state["export_gate"]["export_enabled"] is False
    assert state["export_gate"]["export_gate"] == "disabled_missing_report_ready"
