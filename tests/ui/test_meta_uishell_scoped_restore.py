from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QPushButton

    from app.meta_analysis.project_workspace import create_meta_analysis_project
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget, meta_target_ia_pages
except Exception as exc:  # pragma: no cover
    QApplication = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def _button(widget, object_name: str) -> QPushButton:
    button = widget.findChild(QPushButton, object_name)
    assert button is not None, object_name
    return button


def test_meta_uishell_target_ia_is_final_visual_baseline(qt_app) -> None:
    widget = MetaAnalysisWorkspaceWidget()

    assert widget.page_keys() == ("target_ia",)
    assert widget.target_ia_page_keys() == tuple(page.key for page in meta_target_ia_pages())
    assert widget.target_ia_page_keys() == (
        "project_home",
        "question_meta_type",
        "search_strategy",
        "import_dedup",
        "screening",
        "fulltext_extraction",
        "quality_assessment",
        "analysis_tasks",
        "result_report",
        "report_export",
        "meta_settings",
    )
    assert widget.findChild(QPushButton, "metaTargetIANavItem") is not None
    assert not hasattr(widget, "execute_confirmed_pubmed_search")


def test_meta_uishell_buttons_are_not_empty_and_disabled_buttons_explain_gate(qt_app) -> None:
    widget = MetaAnalysisWorkspaceWidget()
    gaps: list[str] = []

    for button in widget.findChildren(QPushButton):
        if button.property("buttonBehavior") is None:
            gaps.append(f"{button.objectName()}:{button.text()}:missing-buttonBehavior")
        if not button.isEnabled() and button.property("disabledReason") is None:
            gaps.append(f"{button.objectName()}:{button.text()}:missing-disabledReason")
        assert button.property("formalActionEnabled") is False

    assert gaps == []


def test_meta_question_type_and_search_buttons_call_services_or_write_gate_artifacts(qt_app, tmp_path: Path) -> None:
    summary = create_meta_analysis_project("UIShell Restore Meta", tmp_path)
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(summary.project_root)

    widget.show_target_ia_page("question_meta_type")
    type_button = widget.findChildren(QPushButton, "metaActiveTypeSelectButton")[0]
    type_button.click()
    qt_app.processEvents()

    assert (summary.project_root / "protocol" / "pico_workspace_draft.json").exists()
    question_gate = summary.project_root / "ui_runtime" / "meta_question_type_gate.json"
    assert question_gate.exists()
    question_payload = json.loads(question_gate.read_text(encoding="utf-8"))
    assert question_payload["service"] == "PICOWorkspaceService.generate_draft"
    assert question_payload["formal_action_enabled"] is False

    widget.show_target_ia_page("search_strategy")
    search_button = _button(widget, "metaSaveSearchDraftButton")
    assert search_button.isEnabled()
    search_button.click()
    qt_app.processEvents()

    search_reason = summary.project_root / "ui_runtime" / "meta_search_strategy_disabled_reason.json"
    assert search_reason.exists()
    search_payload = json.loads(search_reason.read_text(encoding="utf-8"))
    assert search_payload["service_checked"] == "PICOWorkspaceService.load_confirmed"
    assert search_payload["formal_action_enabled"] is False


def test_meta_later_stage_buttons_write_gate_artifacts_without_enabling_formal_actions(qt_app, tmp_path: Path) -> None:
    summary = create_meta_analysis_project("UIShell Later Gates", tmp_path)
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(summary.project_root)

    widget.show_target_ia_page("screening")
    _button(widget, "metaSaveDraftScreeningDecisionButton").click()
    qt_app.processEvents()
    screening_gate = summary.project_root / "ui_runtime" / "meta_screening_draft_decision_gate.json"
    assert screening_gate.exists()

    widget.show_target_ia_page("fulltext_extraction")
    _button(widget, "metaSaveExtractionDesignButton").click()
    qt_app.processEvents()
    extraction_gate = summary.project_root / "ui_runtime" / "meta_extraction_design_gate.json"
    assert extraction_gate.exists()
    extraction_payload = json.loads(extraction_gate.read_text(encoding="utf-8"))
    assert extraction_payload["service"] == "ExtractionSchemaRegistryV1Service.default_schemas"
    assert extraction_payload["schema_count"] >= 1

    widget.show_target_ia_page("quality_assessment")
    _button(widget, "metaSaveRiskOfBiasDraftButton").click()
    qt_app.processEvents()
    rob_gate = summary.project_root / "ui_runtime" / "meta_risk_of_bias_disabled_reason.json"
    assert rob_gate.exists()

    widget.show_target_ia_page("result_report")
    report_button = _button(widget, "metaGenerateReportDisabledButton")
    assert not report_button.isEnabled()
    assert report_button.property("disabledReason")
