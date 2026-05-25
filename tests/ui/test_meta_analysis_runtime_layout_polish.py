from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QFrame, QPushButton, QStackedWidget

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


def test_meta_runtime_layout_uses_single_stacked_content_area(meta_workspace) -> None:
    shell = meta_workspace.findChild(QFrame, "metaTargetIAShell")
    nav_panel = meta_workspace.findChild(QFrame, "metaWorkflowNavigationPanel")
    content_panel = meta_workspace.findChild(QFrame, "metaRuntimeContentPanel")
    stack = meta_workspace.findChild(QStackedWidget, "metaTargetRuntimeStack")

    assert shell is not None
    assert shell.property("uiPrimitive") == "workbench_shell"
    assert shell.property("moduleKey") == "module.meta_analysis"
    assert shell.property("layoutPolishNoOverlap") is True
    assert nav_panel is not None
    assert nav_panel.property("uiPrimitive") == "workbench_secondary_nav"
    assert nav_panel.property("layoutPolishNoOverlap") is True
    assert content_panel is not None
    assert content_panel.property("uiPrimitive") == "workbench_content_panel"
    assert content_panel.property("layoutPolishNoOverlap") is True
    assert stack is not None
    assert stack.property("layoutPolishNoOverlap") is True
    assert stack.count() == len(meta_workspace.target_ia_page_keys())

    for page_key in meta_workspace.target_ia_page_keys():
        meta_workspace.show_target_ia_page(page_key)
        assert stack.currentWidget().property("pageKey") == page_key
        assert meta_workspace.current_target_page_key() == page_key


def test_meta_layout_polish_preserves_result_report_export_gates(meta_workspace) -> None:
    shared = meta_workspace.findChild(QFrame, "resultReportExportAdoptionPanel")
    network = meta_workspace.findChild(QPushButton, "metaNetworkMetaPlannedButton")

    meta_workspace.show_target_ia_page("question_meta_type")
    assert shared is not None
    assert shared.isHidden()
    assert network is not None
    assert not network.isEnabled()
    assert network.property("interactionMode") == "planned_disabled"
    assert network.property("formalActionEnabled") is False

    meta_workspace.show_target_ia_page("report_export")
    export_buttons = meta_workspace.findChildren(QPushButton, "metaExportFormatDisabledButton")
    assert not shared.isHidden()
    assert shared.property("resultSemanticKey") != "result.semantic.formal_computed_result"
    assert shared.property("reportStatusKey") != "report.status.report_ready"
    assert shared.property("exportGate") == "disabled_empty_result"
    assert all(not button.isEnabled() for button in export_buttons)
    assert all(button.property("fileWriteAllowed") is False for button in export_buttons)
