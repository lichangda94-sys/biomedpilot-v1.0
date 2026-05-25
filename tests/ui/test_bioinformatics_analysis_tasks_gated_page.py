from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QPushButton, QTableWidget, QTextEdit

    from app.bioinformatics.analysis_ui.state import build_analysis_center_state
    from app.bioinformatics.project_workspace import create_bioinformatics_project
    from app.bioinformatics.workflow_pages import BioinformaticsAnalysisTaskCenterWidget
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
    return create_bioinformatics_project("C2e Analysis Tasks", tmp_path)


def _table_text(table: QTableWidget) -> str:
    return " ".join(
        table.item(row, column).text()
        for row in range(table.rowCount())
        for column in range(table.columnCount())
        if table.item(row, column) is not None
    )


def test_analysis_tasks_page_shows_gated_task_matrix(qt_app, bio_project) -> None:
    widget = BioinformaticsAnalysisTaskCenterWidget()
    widget.refresh_project(bio_project)

    matrix = widget.findChild(QTableWidget, "bioinformaticsAnalysisTaskGatedMatrix")
    text = _table_text(matrix)

    assert widget.objectName() == "bioinformaticsAnalysisTaskCenterPage"
    assert widget.property("uiPrimitive") == "workbench_gated_page"
    assert widget.property("layoutPolishNoOverlap") is True
    assert widget.property("formalActionEnabled") is False
    assert "DEG" in text
    assert "preflight / parameter review" in text
    assert "ORA" in text and "requires DEG result" in text
    assert "GSEA" in text and "planned / disabled" in text
    assert "KM / log-rank" in text and "requires survival audit" in text
    assert "Cox" in text and "planned / disabled" in text
    assert "Clinical Association" in text and "audit required / disabled" in text
    assert "formal DEG executor" in text


def test_deg_parameter_review_and_preflight_checklist_are_preflight_only(qt_app, bio_project) -> None:
    widget = BioinformaticsAnalysisTaskCenterWidget()
    widget.refresh_project(bio_project)

    params = widget.findChild(QTableWidget, "bioinformaticsDegParameterReviewTable")
    checklist = widget.findChild(QTableWidget, "bioinformaticsDegPreflightChecklist")
    summary = widget.findChild(QTextEdit, "bioinformaticsAnalysisTaskGateSummary")
    param_text = _table_text(params)
    checklist_text = _table_text(checklist)

    assert "comparison" in param_text
    assert "input matrix state" in param_text
    assert "method policy" in param_text
    assert "planned DESeq2 / limma policy" in param_text
    assert "FDR threshold" in param_text
    assert "log2FC threshold" in param_text
    assert "low-expression filter" in param_text
    assert "normalization" in param_text
    assert "missing value handling" in param_text
    assert "batch handling" in param_text
    assert params.property("resultSemanticKey") == "preflight_only"
    assert "input matrix exists" in checklist_text
    assert "sample metadata complete" in checklist_text
    assert "group design valid" in checklist_text
    assert "comparison valid" in checklist_text
    assert "sample name matching" in checklist_text
    assert "minimal group size" in checklist_text
    assert "output plan / result schema" in checklist_text
    assert checklist.property("resultSemanticKey") == "preflight_only"
    assert "not formal_computed_result" in summary.toPlainText()


def test_analysis_task_actions_are_disabled_and_not_formal_runs(qt_app, bio_project) -> None:
    widget = BioinformaticsAnalysisTaskCenterWidget()
    widget.refresh_project(bio_project)

    action_names = {
        "bioinformaticsRunPreflightReviewDisabledButton": "disabled_preflight_preview",
        "bioinformaticsRunFormalDegDisabledButton": "disabled_formal_executor",
        "bioinformaticsGeneratePlotDisabledButton": "disabled_no_result",
        "bioinformaticsAnalysisAddToReportDisabledButton": "disabled_report_draft",
        "bioinformaticsAnalysisExportResultDisabledButton": "disabled_export_gate",
    }
    for object_name, behavior in action_names.items():
        button = widget.findChild(QPushButton, object_name)
        assert button is not None
        assert button.isEnabled() is False
        assert button.property("formalActionEnabled") is False
        assert button.property("buttonBehavior") == behavior

    old_preflight_button = next(button for button in widget.findChildren(QPushButton) if button.text() == "生成并校验 DEG 输入")
    assert old_preflight_button.isEnabled() is False
    assert old_preflight_button.property("buttonBehavior") == "disabled_preflight_preview"
    formal_geo_button = widget.findChild(QPushButton, "bioinformaticsFormalDegDisabledButton")
    assert formal_geo_button.isEnabled() is False
    assert formal_geo_button.property("formalActionEnabled") is False


def test_c2e_preflight_states_do_not_create_formal_result_or_export(qt_app, bio_project) -> None:
    widget = BioinformaticsAnalysisTaskCenterWidget()
    widget.refresh_project(bio_project)
    state = build_analysis_center_state(bio_project.project_root)

    assert state["result_gate"]["fake_result_allowed"] is False
    assert state["result_gate"]["fake_plot_allowed"] is False
    assert state["result_gate"].get("formal_computed_result_count", 0) == 0
    assert state["report_gate"]["report_ready_package_allowed"] is False
    assert state["export_gate"]["export_enabled"] is False
    assert not (bio_project.project_root / "results" / "summaries" / "result_index.json").exists()
    assert not (bio_project.project_root / "reports" / "project_analysis_report.md").exists()
