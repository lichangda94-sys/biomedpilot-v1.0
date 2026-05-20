from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton

    from app.shared.result_report_export_shell import (
        empty_result_preview_state,
        make_export_buttons,
        make_report_draft_boundary,
        make_result_report_export_adoption_panel,
        make_result_preview_empty_state,
        report_ready_future_state,
        testing_summary_state as build_testing_summary_state,
    )
    from app.shared.semantic_keys import ExportKey, ReportStatusKey, ResultSemanticKey
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    QPushButton = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def test_result_preview_empty_state_carries_semantic_gating(qt_app) -> None:
    state = empty_result_preview_state(module="bioinformatics")
    empty = make_result_preview_empty_state(state)

    assert empty.objectName() == "resultPreviewEmptyState"
    assert empty.property("uiPrimitive") == "empty_state"
    assert empty.property("resultSemanticKey") == ResultSemanticKey.TESTING_SUMMARY_ONLY.value
    assert empty.property("semanticKey") == ResultSemanticKey.TESTING_SUMMARY_ONLY.value
    assert empty.property("reportStatusKey") == ReportStatusKey.DRAFT.value
    assert empty.property("exportGate") == "disabled_empty_result"
    assert "暂无结果预览" in empty.findChild(QLabel, "uiEmptyStateTitle").text()
    assert "不构成正式统计结果" in empty.findChild(QLabel, "uiEmptyStateBody").text()


def test_report_draft_boundary_disclaimer_is_visible(qt_app) -> None:
    boundary = make_report_draft_boundary(build_testing_summary_state(module="meta_analysis"))

    assert boundary.objectName() == "reportDraftBoundaryCard"
    assert boundary.property("reportStatusKey") == ReportStatusKey.TESTING_SUMMARY.value
    assert boundary.property("semanticKey") == ReportStatusKey.TESTING_SUMMARY.value
    assert boundary.findChild(QLabel, "uiStatusChip").property("semanticKey") == "feature.status.testing"


def test_export_buttons_are_disabled_without_results(qt_app) -> None:
    buttons = make_export_buttons(empty_result_preview_state(), (ExportKey.MARKDOWN, ExportKey.DOCX))

    assert [button.property("formatKey") for button in buttons] == ["export.format.markdown", "export.format.docx"]
    assert [button.property("exportFormatKey") for button in buttons] == ["export.format.markdown", "export.format.docx"]
    assert [button.property("semanticKey") for button in buttons] == ["export.format.markdown", "export.format.docx"]
    assert all(button.objectName() == "exportGatedButton" for button in buttons)
    assert all(not button.isEnabled() for button in buttons)
    assert all(button.property("exportGate") == "disabled_empty_result" for button in buttons)
    assert all(button.property("reportStatusKey") == ReportStatusKey.DRAFT.value for button in buttons)
    assert all(button.property("resultSemanticKey") == ResultSemanticKey.TESTING_SUMMARY_ONLY.value for button in buttons)
    assert all(button.property("formalActionEnabled") is False for button in buttons)
    assert all(button.property("reportReadyPackageAllowed") is False for button in buttons)


def test_export_buttons_allow_testing_summary_but_block_report_ready_future(qt_app) -> None:
    testing_buttons = make_export_buttons(build_testing_summary_state(module="bioinformatics"), (ExportKey.MARKDOWN,))
    future_buttons = make_export_buttons(report_ready_future_state(module="bioinformatics"), (ExportKey.MARKDOWN,))

    assert testing_buttons[0].isEnabled()
    assert testing_buttons[0].property("exportGate") == "enabled_testing_export"
    assert testing_buttons[0].property("reportStatusKey") == ReportStatusKey.TESTING_SUMMARY.value
    assert testing_buttons[0].property("reportReadyPackageAllowed") is False

    assert not future_buttons[0].isEnabled()
    assert future_buttons[0].property("exportGate") == "blocked_formal_report_ready"
    assert future_buttons[0].property("reportStatusKey") == ReportStatusKey.REPORT_READY_FUTURE.value
    assert future_buttons[0].property("formalActionEnabled") is False


def test_adoption_panel_keeps_empty_result_exports_gated(qt_app) -> None:
    panel = make_result_report_export_adoption_panel(module="bioinformatics", formats=(ExportKey.MARKDOWN, ExportKey.HTML))
    labels = panel.findChildren(QLabel)
    export_buttons = panel.findChildren(QPushButton, "exportGatedButton")

    assert panel.objectName() == "resultReportExportAdoptionPanel"
    assert panel.property("adoptionModule") == "bioinformatics"
    assert panel.property("resultSemanticKey") == ResultSemanticKey.TESTING_SUMMARY_ONLY.value
    assert panel.property("reportStatusKey") == ReportStatusKey.DRAFT.value
    assert panel.property("exportGate") == "disabled_empty_result"
    assert panel.property("reportReadyPackageAllowed") is False
    assert any(label.objectName() == "resultReportExportAdoptionTitle" for label in labels)
    assert [button.property("exportFormatKey") for button in export_buttons] == ["export.format.markdown", "export.format.html"]
    assert all(button.property("formalActionEnabled") is False for button in export_buttons)
    assert all(not button.isEnabled() for button in export_buttons)
