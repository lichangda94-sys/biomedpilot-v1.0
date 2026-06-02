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
    for button in widget.findChildren(QPushButton, "metaTargetIANavItem"):
        page_key = button.property("pageKey")
        assert button.property("buttonBehavior") == f"navigates_to_meta_target_ia_page_{page_key}"
        assert button.property("formalActionEnabled") is False
        assert button.property("fileWriteAllowed") is False


def test_meta_uishell_target_ia_nav_items_live_click_pages(qt_app) -> None:
    widget = MetaAnalysisWorkspaceWidget()
    by_page = {button.property("pageKey"): button for button in widget.findChildren(QPushButton, "metaTargetIANavItem")}

    for page_key in widget.target_ia_page_keys():
        by_page[page_key].click()
        qt_app.processEvents()

        assert widget.current_target_page_key() == page_key


def test_meta_target_ia_header_titles_follow_current_page(qt_app) -> None:
    widget = MetaAnalysisWorkspaceWidget()
    expected = {
        "project_home": "Meta 分析 / Meta Analysis",
        "question_meta_type": "Meta Analysis / 研究问题与 Meta 类型",
        "search_strategy": "检索策略 / Search Strategy Builder",
        "import_dedup": "文献导入与去重 / Import & Deduplication",
        "screening": "筛选 / Screening Workspace",
        "fulltext_extraction": "全文与数据提取 / Full-text & Extraction",
        "quality_assessment": "质量评价 / Quality Assessment",
        "analysis_tasks": "统计分析 / Meta Analysis Tasks",
        "result_report": "结果与报告 / Result & Report",
        "report_export": "报告导出 / Report Export",
        "meta_settings": "Meta 设置 / Meta Settings",
    }

    for page_key, title in expected.items():
        widget.show_target_ia_page(page_key)
        qt_app.processEvents()

        assert widget._workspace_title_label.text() == title


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
