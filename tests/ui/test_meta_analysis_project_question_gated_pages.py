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


def _all_label_text(widget) -> str:
    return "\n".join(label.text() for label in widget.findChildren(QLabel))


def _table_values(table: QTableWidget) -> list[str]:
    values: list[str] = []
    for row in range(table.rowCount()):
        for column in range(table.columnCount()):
            item = table.item(row, column)
            if item is not None:
                values.append(item.text())
    return values


def test_meta_project_home_runtime_panel_shows_gated_status(meta_workspace) -> None:
    meta_workspace.show_target_ia_page("project_home")
    panel = meta_workspace.findChild(QFrame, "metaProjectHomeRuntimePanel")
    summary = meta_workspace.findChild(QTableWidget, "metaProjectHomeSummaryTable")
    workflow = meta_workspace.findChild(QTableWidget, "metaProjectHomeWorkflowOverview")
    labels = _all_label_text(meta_workspace)

    assert panel is not None
    assert not panel.isHidden()
    assert panel.property("pageKey") == "project_home"
    assert panel.property("runtimeStatus") == "shell_only"
    assert panel.property("processingMode") == "english_first"
    assert panel.property("aiBoundary") == "advisory_only"
    assert panel.property("resultSemanticKey") == "no_formal_result"
    assert panel.property("reportStatusKey") == "report.status.draft"
    assert panel.property("exportGate") == "disabled_empty_result"
    assert panel.property("formalActionEnabled") is False
    assert "Developer Preview / 本地测试版" in labels
    assert "English-first processing" in labels
    assert "AI suggestion only" in labels
    assert "Report not ready" in labels
    assert summary is not None
    assert workflow is not None
    assert workflow.rowCount() == 11
    assert {"References", "0 imported", "Screening", "not started", "Formal pooled result", "none", "Report-ready", "blocked", "Export", "disabled"} <= set(_table_values(summary))
    assert "fake forest plot" not in labels.lower()
    assert "report-ready success" not in labels.lower()
    assert "active export" not in labels.lower()


def test_meta_question_type_runtime_panel_shows_drafts_and_mockup_cards(meta_workspace) -> None:
    meta_workspace.show_target_ia_page("question_meta_type")
    section = meta_workspace.findChild(QFrame, "metaActiveTypeSection")
    draft_panel = meta_workspace.findChild(QFrame, "metaQuestionTypeDraftPanel")
    pico = meta_workspace.findChild(QTableWidget, "metaPicoPecoDraftTable")
    suggested = meta_workspace.findChild(QLabel, "metaSuggestedMetaTypeDraft")
    cards = meta_workspace.findChildren(QFrame, "metaQuestionTypeCandidateCard")
    next_search = meta_workspace.findChild(QPushButton, "metaQuestionNextSearchStrategyButton")
    labels = _all_label_text(meta_workspace)

    assert section is not None
    assert not section.isHidden()
    assert section.property("pageKey") == "question_meta_type"
    assert section.property("runtimeStatus") == "testing"
    assert section.property("networkMetaState") == "planned_disabled"
    assert section.property("resultSemanticKey") == "no_formal_result"
    assert draft_panel is not None
    assert not draft_panel.isHidden()
    assert "中文工作问题" in labels
    assert "English question draft" in labels
    assert pico is not None
    assert {"Population", "Exposure / Index", "Comparator", "Outcome", "Study type"} <= set(_table_values(pico))
    assert suggested is not None
    assert "AI suggestion is advisory only" in suggested.text()
    assert {card.property("typeId") for card in cards} == {
        "prognostic_factor_meta",
        "biomarker_expression_difference_meta",
        "diagnostic_accuracy_meta",
        "intervention_effect_meta",
        "adverse_event_meta",
        "other_meta_type",
    }
    assert all(card.property("formalActionEnabled") is False for card in cards)
    assert next_search is not None
    assert next_search.property("targetPageKey") == "search_strategy"
    assert next_search.property("actionSemantic") == "navigation_only"
    assert next_search.property("formalActionEnabled") is False
    assert "Notes & Confirmation" not in labels
    assert "reviewer confirmation" not in labels.lower()


def test_meta_question_network_and_forbidden_inputs_remain_disabled(meta_workspace) -> None:
    meta_workspace.show_target_ia_page("question_meta_type")
    planned_button = meta_workspace.findChild(QPushButton, "metaNetworkMetaPlannedButton")
    labels = _all_label_text(meta_workspace)

    assert planned_button is not None
    assert planned_button.property("typeId") == "network_meta_analysis"
    assert planned_button.property("interactionMode") == "planned_disabled"
    assert planned_button.property("formalActionEnabled") is False
    assert not planned_button.isEnabled()
    assert meta_workspace.network_meta_enabled() is False
    forbidden = ("CNKI", "WanFang", "VIP", "中文数据库直接检索", "中文 PDF 抽取", "pooled effect", "forest plot")
    for text in forbidden:
        assert text not in labels


def test_meta_c2b_preserves_existing_ia_contract(meta_workspace) -> None:
    assert meta_workspace.page_keys() == ("workflow_home", "project_contract", "dev_branch")
    assert meta_workspace.target_ia_page_keys() == (
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
    assert len(meta_workspace.findChildren(QFrame, "metaActiveTypeCard")) == 10
