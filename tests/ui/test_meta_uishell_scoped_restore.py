from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLineEdit, QPushButton

    from app.meta_analysis.project_workspace import create_meta_analysis_project
    from app.meta_analysis.search.pubmed_search_service import PubMedSearchExecution, PubMedSearchResult
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


def test_meta_pubmed_adapter_buttons_call_services_and_write_artifacts(qt_app, tmp_path: Path) -> None:
    summary = create_meta_analysis_project("UIShell PubMed Adapter", tmp_path)
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(summary.project_root)
    widget.set_pubmed_search_service_factory(lambda: _FakePubMedSearchService())

    widget.show_target_ia_page("search_strategy")
    _button(widget, "metaRunPubMedSearchButton").click()
    qt_app.processEvents()

    pubmed_gate = summary.project_root / "ui_runtime" / "meta_pubmed_search_adapter.json"
    assert pubmed_gate.exists()
    pubmed_payload = json.loads(pubmed_gate.read_text(encoding="utf-8"))
    assert pubmed_payload["service"] == "PubMedSearchService.search_pubmed"
    assert pubmed_payload["returned_count"] == 2
    assert (summary.project_root / pubmed_payload["search_execution_report"]).exists()
    assert (summary.project_root / pubmed_payload["pubmed_candidates_preview"]).exists()

    widget.show_target_ia_page("import_dedup")
    _button(widget, "metaLoadPubMedPreviewButton").click()
    qt_app.processEvents()

    preview_gate = summary.project_root / "ui_runtime" / "meta_pubmed_preview_adapter.json"
    assert preview_gate.exists()
    preview_payload = json.loads(preview_gate.read_text(encoding="utf-8"))
    assert preview_payload["candidate_count"] == 2
    selected_input = widget.findChild(QLineEdit, "metaPubMedSelectedCandidateIds")
    assert selected_input is not None
    assert "pcand-111" in selected_input.text()

    _button(widget, "metaImportSelectedPubMedCandidatesButton").click()
    qt_app.processEvents()

    handoff_gate = summary.project_root / "ui_runtime" / "meta_pubmed_handoff_adapter.json"
    assert handoff_gate.exists()
    handoff_payload = json.loads(handoff_gate.read_text(encoding="utf-8"))
    assert handoff_payload["service"] == "PubMedCandidatesHandoffService.import_selected_candidates"
    assert handoff_payload["imported_count"] == 2
    assert handoff_payload["auto_screened"] is False
    assert (summary.project_root / handoff_payload["literature_records_path"]).exists()
    assert (summary.project_root / handoff_payload["dedup_queue_path"]).exists()
    assert not list((summary.project_root / "screening").glob("*.json"))
    assert not (summary.project_root / "reports" / "prisma_flow_summary.json").exists()


def test_meta_dedup_to_screening_buttons_call_services_and_write_artifacts(qt_app, tmp_path: Path) -> None:
    summary = create_meta_analysis_project("UIShell Dedup Screening Adapter", tmp_path)
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(summary.project_root)
    widget.set_pubmed_search_service_factory(lambda: _FakePubMedSearchService())

    widget.show_target_ia_page("search_strategy")
    _button(widget, "metaRunPubMedSearchButton").click()
    qt_app.processEvents()

    widget.show_target_ia_page("import_dedup")
    _button(widget, "metaLoadPubMedPreviewButton").click()
    qt_app.processEvents()
    _button(widget, "metaImportSelectedPubMedCandidatesButton").click()
    qt_app.processEvents()

    _button(widget, "metaBuildDedupReviewQueueButton").click()
    qt_app.processEvents()
    dedup_queue_gate = summary.project_root / "ui_runtime" / "meta_dedup_review_queue_adapter.json"
    assert dedup_queue_gate.exists()
    dedup_queue_payload = json.loads(dedup_queue_gate.read_text(encoding="utf-8"))
    assert dedup_queue_payload["service"] == "DedupReviewV2Service.build_review_queue"
    assert dedup_queue_payload["auto_merged"] is False
    assert dedup_queue_payload["auto_deleted"] is False
    assert (summary.project_root / dedup_queue_payload["output_path"]).exists()

    _button(widget, "metaGenerateDeduplicatedSetButton").click()
    qt_app.processEvents()
    deduplicated_gate = summary.project_root / "ui_runtime" / "meta_deduplicated_set_adapter.json"
    assert deduplicated_gate.exists()
    deduplicated_payload = json.loads(deduplicated_gate.read_text(encoding="utf-8"))
    assert deduplicated_payload["service"] == "DedupReviewV2Service.generate_deduplicated_set"
    assert deduplicated_payload["active_record_count"] == 2
    assert deduplicated_payload["auto_screened"] is False
    assert (summary.project_root / deduplicated_payload["output_path"]).exists()

    _button(widget, "metaBuildScreeningQueueFromDedupButton").click()
    qt_app.processEvents()
    screening_gate = summary.project_root / "ui_runtime" / "meta_dedup_to_screening_queue_adapter.json"
    assert screening_gate.exists()
    screening_payload = json.loads(screening_gate.read_text(encoding="utf-8"))
    assert screening_payload["service"] == "TitleAbstractScreeningV2Service.build_queue"
    assert screening_payload["source_type"] == "deduplicated_literature_v2"
    assert screening_payload["record_count"] == 2
    assert screening_payload["auto_screening_enabled"] is False
    assert (summary.project_root / screening_payload["output_path"]).exists()
    assert not (summary.project_root / "reports" / "prisma_flow_summary.json").exists()


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


class _FakePubMedSearchService:
    def search_pubmed(self, query: str, *, max_results: int = 20, timeout_seconds: float = 10.0) -> PubMedSearchExecution:
        return PubMedSearchExecution(
            success=True,
            query_used=query,
            executed_at="2026-06-02T00:00:00+00:00",
            result_count=2,
            returned_count=2,
            search_execution_id="pubmedexec-ui-adapter",
            records=(
                PubMedSearchResult(
                    pmid="111",
                    doi="10.1000/ui111",
                    title="Serum adiponectin and thyroid cancer risk",
                    journal="Meta UI Journal",
                    year="2024",
                    publication_date="2024-01-02",
                    authors=("Alice Adams",),
                    abstract="UI adapter candidate one.",
                    snippet="UI adapter candidate one.",
                    url="https://pubmed.ncbi.nlm.nih.gov/111/",
                    query_used=query,
                ),
                PubMedSearchResult(
                    pmid="222",
                    doi="10.1000/ui222",
                    title="Adiponectin levels in thyroid carcinoma",
                    journal="Meta UI Journal",
                    year="2025",
                    publication_date="2025",
                    authors=("Ben Baker",),
                    abstract="UI adapter candidate two.",
                    snippet="UI adapter candidate two.",
                    url="https://pubmed.ncbi.nlm.nih.gov/222/",
                    query_used=query,
                ),
            ),
        )
