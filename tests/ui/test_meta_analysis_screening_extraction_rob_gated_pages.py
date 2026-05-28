from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QFrame, QSplitter, QTableView, QTableWidget

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


def _table_values(table: QTableWidget) -> set[str]:
    values: set[str] = set()
    for row in range(table.rowCount()):
        for column in range(table.columnCount()):
            item = table.item(row, column)
            if item is not None:
                values.add(item.text())
    return values


def test_meta_screening_page_renders_draft_decisions_only(meta_workspace) -> None:
    meta_workspace.show_target_ia_page("screening")
    panel = meta_workspace.findChild(QFrame, "metaScreeningRuntimePanel")
    counts = meta_workspace.findChild(QTableWidget, "metaScreeningDraftCountsTable")
    queue = meta_workspace.findChild(QTableWidget, "metaScreeningReferenceQueue")
    shared_queue = meta_workspace.findChild(QSplitter, "metaSharedReferenceQueuePanel")
    decisions = meta_workspace.findChildren(QPushButton, "metaScreeningDecisionDraftButton")
    save_draft = meta_workspace.findChild(QPushButton, "metaSaveDraftScreeningDecisionButton")
    ai_card = meta_workspace.findChild(QLabel, "metaScreeningAISuggestionCard")
    labels = _all_label_text(meta_workspace)

    assert panel is not None
    assert not panel.isHidden()
    assert panel.property("pageKey") == "screening"
    assert panel.property("screeningState") == "draft_decisions_only"
    assert panel.property("resultSemanticKey") == "no_formal_result"
    assert counts is not None
    assert {"draft counts", "Include draft", "Exclude draft", "Uncertain", "Need full text"} <= _table_values(counts)
    assert "final PRISMA counts" not in labels
    assert queue is not None
    assert {"REF-001", "REF-002", "include_draft", "uncertain", "exclude_draft"} <= _table_values(queue)
    assert shared_queue is not None
    assert shared_queue.property("uiPrimitive") == "reference_queue_panel"
    assert shared_queue.property("screeningState") == "draft_decisions_only"
    assert shared_queue.property("finalDecisionEnabled") is False
    assert shared_queue.property("formalActionEnabled") is False
    assert {button.property("decisionId") for button in decisions} == {
        "include_draft",
        "exclude_draft",
        "uncertain",
        "need_full_text",
    }
    assert all(button.property("decisionState") == "draft_only" for button in decisions)
    assert all(button.property("formalActionEnabled") is False for button in decisions)
    decisions[0].click()
    assert meta_workspace.property("selectedScreeningDecisionDraft") == decisions[0].property("decisionId")
    assert save_draft is not None
    assert save_draft.text() == "Save Draft Decision"
    assert save_draft.property("formalActionEnabled") is False
    save_draft.click()
    assert meta_workspace.property("lastDraftAction") == "screening_save_draft"
    assert ai_card is not None
    assert ai_card.property("aiBoundary") == "advisory_only"
    assert "Advisory only" in ai_card.text()
    assert "Submit Decision" not in labels
    assert "final included studies" not in labels.lower()


def test_meta_fulltext_extraction_keeps_tabs_and_draft_fields(meta_workspace) -> None:
    meta_workspace.show_target_ia_page("fulltext_extraction")
    panel = meta_workspace.findChild(QFrame, "metaFulltextExtractionPanel")
    tabs = meta_workspace.findChildren(QPushButton, "metaFulltextExtractionTab")
    status = meta_workspace.findChild(QTableWidget, "metaFulltextStatusPreviewTable")
    shared_table = meta_workspace.findChild(QTableView, "metaSharedExtractionFormTable")
    fields = meta_workspace.findChildren(QLabel, "metaExtractionFieldCell")
    mark_draft = meta_workspace.findChild(QPushButton, "metaConfirmExtractionButton")
    labels = _all_label_text(meta_workspace)

    assert panel is not None
    assert not panel.isHidden()
    assert panel.property("extractionState") == "draft_extraction"
    assert panel.property("resultSemanticKey") == "no_formal_result"
    assert [tab.property("tabKey") for tab in tabs] == ["全文管理", "提取表设计", "提取完成核查", "历史记录"]
    assert status is not None
    assert status.property("horizontalOverflow") is True
    assert {"REF-001", "file pending", "needs retrieval", "not_started"} <= _table_values(status)
    assert shared_table is not None
    assert shared_table.property("uiPrimitive") == "extraction_form_table"
    assert shared_table.property("draftOnly") is True
    assert shared_table.property("formalAnalysisInput") is False
    assert shared_table.property("formalActionEnabled") is False
    field_texts = {field.text() for field in fields}
    assert {
        "first_author",
        "year",
        "cancer_type",
        "marker_name",
        "effect_measure",
        "effect_value",
        "ci_lower",
        "ci_upper",
        "adjusted_model",
        "outcome_name",
    } <= field_texts
    assert "mockup-only / draft extraction" in labels
    assert mark_draft is not None
    assert "Mark as Draft Extracted" in mark_draft.text()
    assert mark_draft.property("draftActionSemantic") == "draft_extraction_adapter_needed"
    assert not mark_draft.isEnabled()
    assert "automatic extraction" not in labels.lower()
    assert "中文 PDF 抽取" not in labels


def test_meta_risk_of_bias_page_renders_preview_only(meta_workspace) -> None:
    meta_workspace.show_target_ia_page("quality_assessment")
    panel = meta_workspace.findChild(QFrame, "metaRiskOfBiasRuntimePanel")
    table = meta_workspace.findChild(QTableWidget, "metaRiskOfBiasDomainTable")
    notice = meta_workspace.findChild(QLabel, "metaRiskOfBiasPreviewScoreNotice")
    save = meta_workspace.findChild(QPushButton, "metaSaveRiskOfBiasDraftButton")
    labels = _all_label_text(meta_workspace)

    assert panel is not None
    assert not panel.isHidden()
    assert panel.property("pageKey") == "quality_assessment"
    assert panel.property("riskOfBiasState") == "preview_in_progress"
    assert panel.property("resultSemanticKey") == "no_formal_result"
    assert table is not None
    assert {
        "NOS Selection",
        "NOS Comparability",
        "NOS Outcome",
        "ROBINS-I Confounding",
        "QUADAS-2",
        "Draft",
        "In progress",
        "preview score requires final confirmation",
    } <= _table_values(table)
    assert notice is not None
    assert "no automatic RoB final judgement" in notice.text()
    assert "no formal quality score" in notice.text()
    assert save is not None
    assert not save.isEnabled()
    assert save.property("formalActionEnabled") is False
    assert "automatic RoB final judgement" in labels
    assert "formal quality score." in labels


def test_meta_c2d_keeps_result_report_export_and_network_gates(meta_workspace) -> None:
    panel = meta_workspace.findChild(QFrame, "resultReportExportAdoptionPanel")
    network_button = meta_workspace.findChild(QPushButton, "metaNetworkMetaPlannedButton")

    assert panel is not None
    assert panel.property("exportGate") == "disabled_empty_result"
    assert panel.property("reportReadyPackageAllowed") is False
    assert all(not button.isEnabled() for button in panel.findChildren(QPushButton, "exportGatedButton"))
    assert network_button is not None
    assert not network_button.isEnabled()
    assert network_button.property("interactionMode") == "planned_disabled"
