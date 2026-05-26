from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QFrame, QTableWidget

    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    MetaAnalysisWorkspaceWidget = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


@pytest.fixture
def meta_workspace(qt_app):
    widget = MetaAnalysisWorkspaceWidget()
    yield widget
    widget.close()
    widget.deleteLater()
    qt_app.processEvents()


def _table_values(table: QTableWidget) -> set[str]:
    values: set[str] = set()
    for row in range(table.rowCount()):
        for column in range(table.columnCount()):
            item = table.item(row, column)
            if item is not None:
                values.add(item.text())
    return values


def test_meta_result_review_page_renders_gate_summary_without_formal_result(meta_workspace) -> None:
    meta_workspace.show_target_ia_page("result_report")
    panel = meta_workspace.findChild(QFrame, "metaResultReviewRuntimePanel")
    pairwise_card = meta_workspace.findChild(QFrame, "metaPairwiseInputPreviewCard")
    forest_placeholder = meta_workspace.findChild(QFrame, "metaForestPlotPlaceholder")
    readiness = meta_workspace.findChild(QTableWidget, "metaResultReadinessSummaryTable")
    pairwise = meta_workspace.findChild(QTableWidget, "metaPairwiseInputPreviewTable")
    notice = meta_workspace.findChild(QLabel, "metaResultReviewHumanReviewNotice")

    assert panel is not None
    assert not panel.isHidden()
    assert panel.property("pageKey") == "result_report"
    assert panel.property("resultSemanticKey") == "testing_summary_only"
    assert panel.property("formalResultSemanticKey") == "no_formal_result"
    assert panel.property("reportStatusKey") == "report.status.draft"
    assert panel.property("exportGate") == "disabled_empty_result"
    assert panel.property("fileWriteAllowed") is False
    assert panel.property("formalActionEnabled") is False
    assert pairwise_card is not None
    assert pairwise_card.property("uiPrimitive") == "preview_card"
    assert pairwise_card.property("formalResult") is False
    assert forest_placeholder is not None
    assert forest_placeholder.property("uiPrimitive") == "plot_placeholder"
    assert forest_placeholder.property("formalPlot") is False
    assert forest_placeholder.property("fakePlotData") is False
    assert readiness is not None
    assert readiness.property("horizontalOverflow") is True
    assert {
        "testing_summary_only / no_formal_result",
        "formal_pooled_effect",
        "none",
        "forest_plot",
        "disabled_boundary",
        "heterogeneity",
        "publication_bias",
        "advisory_only",
    } <= _table_values(readiness)
    assert "formal_computed_result" not in _table_values(readiness)
    assert pairwise is not None
    assert pairwise.property("previewOnly") is True
    assert {"STUDY-001", "preflight_only", "warning_missing_adjustment", "incompatible_effect_type"} <= _table_values(pairwise)
    assert notice is not None
    assert "不能升级为正式结果" in notice.text()


def test_meta_report_ready_gate_blocks_report_generation(meta_workspace) -> None:
    meta_workspace.show_target_ia_page("result_report")
    blockers = meta_workspace.findChild(QTableWidget, "metaReportReadyBlockerChecklist")
    generate = meta_workspace.findChild(QPushButton, "metaGenerateReportDisabledButton")

    assert blockers is not None
    assert {
        "research question/type confirmation",
        "missing_or_draft",
        "search strategy",
        "draft",
        "screening",
        "not_final",
        "extraction",
        "risk of bias",
        "pairwise input",
        "not_formal",
        "formal result",
        "missing",
    } <= _table_values(blockers)
    assert generate is not None
    assert not generate.isEnabled()
    assert generate.property("actionSemantic") == "disabled_report_gate"
    assert generate.property("formalActionEnabled") is False
    assert generate.property("fileWriteAllowed") is False


def test_meta_report_export_page_disables_all_formats_and_file_writes(meta_workspace) -> None:
    meta_workspace.show_target_ia_page("report_export")
    panel = meta_workspace.findChild(QFrame, "metaReportExportGateRuntimePanel")
    shared_gate = meta_workspace.findChild(QFrame, "metaSharedExportGatePanel")
    gate = meta_workspace.findChild(QTableWidget, "metaReportExportGateReasonTable")
    export_buttons = meta_workspace.findChildren(QPushButton, "metaExportFormatDisabledButton")
    notice = meta_workspace.findChild(QLabel, "metaExportAfterGateNotice")

    assert panel is not None
    assert not panel.isHidden()
    assert panel.property("pageKey") == "report_export"
    assert panel.property("resultSemanticKey") == "no_formal_result"
    assert panel.property("reportStatusKey") == "report.status.draft"
    assert panel.property("reportReadyState") == "blocked"
    assert panel.property("exportGate") == "disabled_empty_result"
    assert panel.property("fileWriteAllowed") is False
    assert shared_gate is not None
    assert shared_gate.property("uiPrimitive") == "export_gate_panel"
    assert shared_gate.property("exportAllowed") is False
    assert shared_gate.property("reportGenerationAllowed") is False
    assert shared_gate.property("fileWriteAllowed") is False
    assert gate is not None
    assert gate.property("horizontalOverflow") is True
    assert {"no formal result", "report not ready", "export adapter missing", "no file write in gated shell"} <= _table_values(gate)
    assert {button.property("exportFormat") for button in export_buttons} == {"DOCX", "HTML", "PDF", "CSV", "XLSX", "ZIP"}
    assert all(not button.isEnabled() for button in export_buttons)
    assert all(button.property("formalActionEnabled") is False for button in export_buttons)
    assert all(button.property("fileWriteAllowed") is False for button in export_buttons)
    assert notice is not None
    assert notice.text() == "Export will be enabled after gate."


def test_meta_c2e_keeps_shared_rre_and_network_gates(meta_workspace) -> None:
    shared = meta_workspace.findChild(QFrame, "resultReportExportAdoptionPanel")
    network_button = meta_workspace.findChild(QPushButton, "metaNetworkMetaPlannedButton")

    assert shared is not None
    assert shared.property("resultSemanticKey") != "result.semantic.formal_computed_result"
    assert shared.property("reportStatusKey") != "report.status.report_ready"
    assert shared.property("exportGate") == "disabled_empty_result"
    assert shared.property("reportReadyPackageAllowed") is False
    assert all(not button.isEnabled() for button in shared.findChildren(QPushButton, "exportGatedButton"))
    assert network_button is not None
    assert not network_button.isEnabled()
    assert network_button.property("interactionMode") == "planned_disabled"
