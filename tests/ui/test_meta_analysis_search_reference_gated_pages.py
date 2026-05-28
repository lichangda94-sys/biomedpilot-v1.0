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


def _table_values(table: QTableWidget) -> set[str]:
    values: set[str] = set()
    for row in range(table.rowCount()):
        for column in range(table.columnCount()):
            item = table.item(row, column)
            if item is not None:
                values.add(item.text())
    return values


def test_meta_search_strategy_page_renders_english_draft_only(meta_workspace) -> None:
    meta_workspace.show_target_ia_page("search_strategy")
    panel = meta_workspace.findChild(QFrame, "metaSearchStrategyRuntimePanel")
    terms = meta_workspace.findChild(QTableWidget, "metaSearchTermGroupTable")
    query = meta_workspace.findChild(QLabel, "metaSearchPubMedStyleQueryDraft")
    databases = meta_workspace.findChildren(QPushButton, "metaDatabaseDraftScopeButton")
    copy_query = meta_workspace.findChild(QPushButton, "metaCopyQueryButton")
    save_draft = meta_workspace.findChild(QPushButton, "metaSaveSearchDraftButton")
    labels = _all_label_text(meta_workspace)

    assert panel is not None
    assert not panel.isHidden()
    assert panel.property("pageKey") == "search_strategy"
    assert panel.property("processingMode") == "english_first"
    assert panel.property("aiBoundary") == "advisory_only"
    assert panel.property("resultSemanticKey") == "no_formal_result"
    assert panel.property("exportGate") == "disabled_empty_result"
    assert panel.property("formalActionEnabled") is False
    assert terms is not None
    assert {"thyroid cancer OR thyroid carcinoma OR thyroid neoplasm", "adiponectin OR ADIPOQ", "prognosis OR survival OR recurrence OR clinicopathological"} <= _table_values(terms)
    assert query is not None
    assert query.property("queryState") == "draft_only"
    assert "PubMed-style query draft" in query.text()
    assert {button.property("databaseName") for button in databases} == {"PubMed", "Embase", "Web of Science"}
    assert all(button.property("selectionState") == "draft_scope_only" for button in databases)
    assert all(button.property("executedSearch") is False for button in databases)
    assert all(button.property("formalActionEnabled") is False for button in databases)
    assert copy_query is not None
    assert copy_query.property("actionSemantic") == "copy_only"
    assert copy_query.isEnabled()
    copy_query.click()
    assert meta_workspace.property("lastDraftAction") == "copy_search_query_draft"
    databases[0].click()
    assert databases[0].property("draftScopeState") in {"selected", "unselected"}
    assert save_draft is not None
    assert save_draft.property("actionSemantic") == "adapter_needed"
    assert not save_draft.isEnabled()
    assert "运行检索" not in labels
    for forbidden in ("CNKI", "WanFang", "VIP"):
        assert forbidden not in labels


def test_meta_reference_management_preview_and_import_gates(meta_workspace) -> None:
    meta_workspace.show_target_ia_page("import_dedup")
    panel = meta_workspace.findChild(QFrame, "metaReferenceDedupRuntimePanel")
    source_cards = meta_workspace.findChildren(QFrame, "metaImportSourceCard")
    import_buttons = meta_workspace.findChildren(QPushButton, "metaImportSourceButton")
    reference_table = meta_workspace.findChild(QTableWidget, "metaReferencePreviewTable")
    labels = _all_label_text(meta_workspace)

    assert panel is not None
    assert not panel.isHidden()
    assert panel.property("pageKey") == "import_dedup"
    assert panel.property("processingMode") == "english_first"
    assert panel.property("resultSemanticKey") == "no_formal_result"
    assert panel.property("reportStatusKey") == "report.status.draft"
    assert panel.property("exportGate") == "disabled_empty_result"
    assert len(source_cards) == 4
    assert {card.property("sourceId") for card in source_cards} == {
        "ris_bibtex_endnote",
        "csv_excel",
        "pubmed_result_file",
        "manual_entry",
    }
    assert all(card.property("importState") == "adapter_needed" for card in source_cards)
    assert len(import_buttons) == 4
    assert all(not button.isEnabled() for button in import_buttons)
    assert all(button.property("formalActionEnabled") is False for button in import_buttons)
    assert reference_table is not None
    values = _table_values(reference_table)
    assert {"REF-001", "REF-002", "REF-003", "REF-004", "not_started", "possible_duplicate"} <= values
    assert "mockup-only / local draft" in labels
    assert "final included studies" not in labels.lower()


def test_meta_deduplication_preview_keeps_mutating_actions_disabled(meta_workspace) -> None:
    meta_workspace.show_target_ia_page("import_dedup")
    dedup_table = meta_workspace.findChild(QTableWidget, "metaDedupRiskGroupTable")
    reviewer_chip = meta_workspace.findChild(QLabel, "metaDedupReviewerRequiredChip")
    auto_merge = meta_workspace.findChild(QPushButton, "metaAutoMergeDisabledButton")
    auto_delete = meta_workspace.findChild(QPushButton, "metaAutoDeleteDisabledButton")
    send_screening = meta_workspace.findChild(QPushButton, "metaSendToScreeningDisabledButton")
    labels = _all_label_text(meta_workspace)

    assert dedup_table is not None
    assert {"DUP-001", "possible duplicate", "REF-002, REF-003", "reviewer review required"} <= _table_values(dedup_table)
    assert reviewer_chip is not None
    assert "no automatic merge / reviewer review required" in reviewer_chip.text()
    for button in (auto_merge, auto_delete, send_screening):
        assert button is not None
        assert not button.isEnabled()
        assert button.property("actionSemantic") == "disabled_boundary"
        assert button.property("formalActionEnabled") is False
    assert "automatically sent" not in labels.lower()
    assert "自动发送" not in labels


def test_meta_c2c_keeps_result_report_export_and_network_gates(meta_workspace) -> None:
    panel = meta_workspace.findChild(QFrame, "resultReportExportAdoptionPanel")
    network_button = meta_workspace.findChild(QPushButton, "metaNetworkMetaPlannedButton")

    assert panel is not None
    assert panel.property("exportGate") == "disabled_empty_result"
    assert panel.property("reportReadyPackageAllowed") is False
    assert all(not button.isEnabled() for button in panel.findChildren(QPushButton, "exportGatedButton"))
    assert network_button is not None
    assert not network_button.isEnabled()
    assert network_button.property("interactionMode") == "planned_disabled"
