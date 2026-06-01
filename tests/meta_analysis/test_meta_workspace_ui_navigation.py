from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from app.meta_analysis.pages.workflow_integration_page import meta_workflow_integration_state_from_project
from app.meta_analysis.project_workspace import META_PROJECT_DIRECTORIES, create_meta_analysis_project
from app.meta_analysis.workspace import meta_workspace_layout_state

try:
    from PySide6.QtWidgets import QApplication, QComboBox, QFrame, QLabel, QLineEdit, QListWidget, QPlainTextEdit, QPushButton
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


def _visible_text(widget) -> str:
    texts: list[str] = []
    for child in [*widget.findChildren(QLabel), *widget.findChildren(QPushButton)]:
        if child.isVisibleTo(widget):
            value = child.text()
            if value:
                texts.append(value)
    return "\n".join(texts)


def _current_step_widget(widget):
    scroll = widget._page_stack.currentWidget()
    return scroll.widget()


def _button_by_text(widget, text: str):
    return next(button for button in widget.findChildren(QPushButton) if button.text() == text)


def _confirm_meta_pico_via_ui(widget, qt_app) -> None:
    widget.show_step("pico_workspace")
    current = _current_step_widget(widget)
    question = current.findChild(QPlainTextEdit, "metaPicoQuestionInput")
    mode = current.findChild(QComboBox, "metaPicoModeSelector")
    assert question is not None
    assert mode is not None
    question.setPlainText("高血压患者降压药与常规治疗相比对卒中风险的影响")
    mode.setCurrentIndex(mode.findData("pico"))
    _button_by_text(current, "生成 PICO 草稿").click()
    qt_app.processEvents()

    widget.show_step("pico_workspace")
    current = _current_step_widget(widget)
    primary = current.findChild(QLineEdit, "metaPicoPrimaryOutcomesInput")
    effect = current.findChild(QLineEdit, "metaPicoEffectMeasureInput")
    assert primary is not None
    assert effect is not None
    primary.setText("卒中发生率")
    effect.setText("RR")
    _button_by_text(current, "保存草稿编辑").click()
    qt_app.processEvents()

    widget.show_step("pico_workspace")
    current = _current_step_widget(widget)
    _button_by_text(current, "确认研究问题").click()
    qt_app.processEvents()


def _assert_meta_buttons_are_auditable(widget) -> None:
    buttons = widget.findChildren(QPushButton)
    assert buttons
    for button in buttons:
        assert button.property("buttonBehavior") is not None, button.text()
        assert not str(button.property("buttonBehavior")).startswith("meta_button_behavior_explicit_"), button.text()
        assert button.property("formalActionEnabled") is False
        if not button.isEnabled():
            assert button.property("disabledReason") is not None, button.text()


def test_meta_workspace_layout_state_uses_eight_user_facing_stages() -> None:
    state = meta_workspace_layout_state()

    assert "0.1.0-internal-beta" in state.status_label
    assert state.title == "Meta 分析模块"
    assert state.default_page_key == "workflow_home"
    assert [item.page_key for item in state.navigation_items] == [
        "workflow_home",
        "pico_workspace",
        "search_strategy",
        "literature_import",
        "screening_review",
        "manual_extraction",
        "statistics_analysis",
        "report_export",
    ]
    assert [item.label for item in state.navigation_items] == [
        "项目首页",
        "研究问题与 PICO",
        "检索策略",
        "文献库与导入",
        "去重与筛选",
        "数据提取与质量评价",
        "统计分析",
        "报告导出",
    ]
    assert "不能作为正式临床" in state.testing_notice


def test_meta_workspace_widget_mounts_project_sidebar_and_home(qt_app, tmp_path: Path) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    summary = create_meta_analysis_project("Mounted Pages", tmp_path)
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(summary.project_root)

    assert widget.meta_workspace_layout_state()["workflow_nav"] == "metaWorkflowNav"
    assert widget.meta_workspace_layout_state()["current_step_workspace"] == "metaCurrentStepWorkspace"
    assert widget.page_keys() == (
        "workflow_home",
        "pico_workspace",
        "search_strategy",
        "literature_import",
        "screening_review",
        "manual_extraction",
        "statistics_analysis",
        "report_export",
    )
    mounted_pages = {frame.objectName() for frame in widget.findChildren(QFrame)}
    assert {
        "metaProjectHomePage",
        "metaPicoPage",
        "metaSearchStrategyPage",
        "metaLiteratureAcquisitionPage",
        "metaTitleAbstractScreeningPage",
        "metaManualExtractionPage",
        "metaStatisticsAnalysisPage",
        "metaReportExportPage",
    } <= mounted_pages


def test_meta_workspace_blocks_pico_entry_until_project_exists(qt_app) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    widget = MetaAnalysisWorkspaceWidget()
    widget.show()
    qt_app.processEvents()

    buttons = [button for button in widget.findChildren(QPushButton) if button.text() == "继续：研究问题 / PICO"]
    assert buttons
    assert all(not button.isEnabled() for button in buttons)
    _assert_meta_buttons_are_auditable(widget)
    assert "请先新建或打开 Meta 项目" in _visible_text(widget)


def test_meta_workspace_active_pages_expose_auditable_button_contracts(qt_app, tmp_path: Path) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    summary = create_meta_analysis_project("Button Contracts", tmp_path)
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(summary.project_root)

    for page_key in widget.page_keys():
        widget.show_step(page_key)
        current = _current_step_widget(widget)
        if current.findChildren(QPushButton):
            _assert_meta_buttons_are_auditable(current)


def test_meta_workspace_creates_meta_project_from_home_form(qt_app, tmp_path: Path) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    widget = MetaAnalysisWorkspaceWidget()
    widget.set_new_project_form(project_name="高血压 Meta", research_topic="降压治疗", save_location=tmp_path)

    summary = widget.create_meta_project_from_form()

    assert summary is not None
    assert widget.current_project_dir() == summary.project_root
    for directory in META_PROJECT_DIRECTORIES:
        assert (summary.project_root / directory).is_dir()
    manifest = json.loads((summary.project_root / "meta_project_manifest.json").read_text(encoding="utf-8"))
    config = json.loads((summary.project_root / "meta_project_config.json").read_text(encoding="utf-8"))
    assert manifest["project_type"] == "meta_analysis"
    assert manifest["project_name"] == "高血压 Meta"
    assert manifest["workflow_stage"] == "project_home"
    assert config["ui"]["current_page"] == "workflow_home"


def test_meta_workspace_opens_existing_project_and_rejects_invalid_folder(qt_app, tmp_path: Path) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    summary = create_meta_analysis_project("Existing Meta", tmp_path)
    invalid = tmp_path / "plain-folder"
    invalid.mkdir()
    widget = MetaAnalysisWorkspaceWidget()

    assert widget.open_meta_project_folder(summary.project_root) is True
    assert widget.current_project_dir() == summary.project_root
    assert widget.open_meta_project_folder(invalid) is False
    assert widget.current_project_dir() == summary.project_root


def test_meta_home_collapses_repeated_status_and_developer_terms(qt_app, tmp_path: Path) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    summary = create_meta_analysis_project("Clean Home", tmp_path)
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(summary.project_root)
    widget.show()
    qt_app.processEvents()

    visible = _visible_text(widget)
    assert "当前项目状态" not in visible
    assert "项目概览" not in visible
    assert "最近 warnings" not in visible
    assert "project_home" not in visible
    assert "manifest" not in visible
    assert "config" not in visible
    assert "workflow_state" not in visible
    assert visible.count("Developer Preview / 本地测试版") == 1
    assert "下一步：填写研究问题 / PICO" in visible
    assert "继续：研究问题 / PICO" in visible


def test_meta_workspace_pico_protocol_round_trip_updates_status(qt_app, tmp_path: Path) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    summary = create_meta_analysis_project("PICO Round Trip", tmp_path)
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(summary.project_root)
    widget.show_step("pico_workspace")

    before = {step.step_id: step.status for step in meta_workflow_integration_state_from_project(summary.project_root).steps}
    assert before["pico_workspace"] == "未开始"

    question = widget.findChild(QPlainTextEdit, "metaPicoQuestionInput")
    assert question is not None
    question.setPlainText("高血压患者降压药与常规治疗相比对卒中风险的影响")
    mode = widget.findChild(QComboBox, "metaPicoModeSelector")
    assert mode is not None
    mode.setCurrentIndex(mode.findData("pico"))
    current = _current_step_widget(widget)
    generate = next(button for button in current.findChildren(QPushButton) if button.text() == "生成 PICO 草稿")
    generate.click()
    qt_app.processEvents()

    draft_state = {step.step_id: step.status for step in meta_workflow_integration_state_from_project(summary.project_root).steps}
    assert draft_state["pico_workspace"] == "草稿"
    assert (summary.project_root / "protocol" / "pico_workspace_draft.json").exists()

    widget.show_step("pico_workspace")
    current = _current_step_widget(widget)
    primary = current.findChild(QLineEdit, "metaPicoPrimaryOutcomesInput")
    effect = current.findChild(QLineEdit, "metaPicoEffectMeasureInput")
    assert primary is not None
    assert effect is not None
    primary.setText("卒中发生率")
    effect.setText("RR")
    save = next(button for button in current.findChildren(QPushButton) if button.text() == "保存草稿编辑")
    save.click()
    qt_app.processEvents()

    widget.show_step("pico_workspace")
    current = _current_step_widget(widget)
    confirm = next(button for button in current.findChildren(QPushButton) if button.text() == "确认研究问题")
    confirm.click()
    qt_app.processEvents()

    confirmed_path = summary.project_root / "protocol" / "pico_workspace_confirmed.json"
    protocol_manifest = summary.project_root / "protocol" / "pico_workspace_manifest.json"
    assert confirmed_path.exists()
    assert protocol_manifest.exists()
    confirmed = json.loads(confirmed_path.read_text(encoding="utf-8"))
    manifest = json.loads(protocol_manifest.read_text(encoding="utf-8"))
    assert confirmed["confirmed_pico_mode"] == "pico"
    assert "卒中发生率" in confirmed["confirmed_outcomes"]
    assert "推荐效应量类型：RR" in confirmed["user_notes"]
    assert manifest["confirmed_status"] == "confirmed"

    complete_state = {step.step_id: step.status for step in meta_workflow_integration_state_from_project(summary.project_root).steps}
    assert complete_state["pico_workspace"] == "已完成"

    widget.show_step("search_strategy")
    visible = _visible_text(widget)
    assert "下一阶段将基于该方案生成检索策略" in visible
    current = _current_step_widget(widget)
    _assert_meta_buttons_are_auditable(current)
    button_behaviors = {button.text(): button.property("buttonBehavior") for button in current.findChildren(QPushButton)}
    assert button_behaviors["生成检索策略"] == "calls_search_strategy_builder_generate_from_confirmed_protocol"
    assert button_behaviors["保存当前编辑"] == "calls_search_strategy_builder_edit_draft"
    assert button_behaviors["复制检索式"] == "copies_current_search_strategy_query_to_clipboard"
    assert button_behaviors["执行 PubMed testing-level 检索"] == "calls_pubmed_search_service_testing_level_and_writes_candidates_preview"


def test_meta_workspace_search_pubmed_candidate_import_click_chain(qt_app, tmp_path: Path, monkeypatch) -> None:
    from app.meta_analysis.search.pubmed_search_service import PubMedSearchExecution, PubMedSearchResult
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    class FakePubMedSearchService:
        def search_pubmed(self, query: str, *, max_results: int = 20, timeout_seconds: float = 10.0) -> PubMedSearchExecution:
            return PubMedSearchExecution(
                success=True,
                query_used=query,
                executed_at="2026-06-01T00:00:00Z",
                result_count=1,
                returned_count=1,
                records=(
                    PubMedSearchResult(
                        pmid="123456",
                        title="Antihypertensive therapy and stroke risk",
                        journal="Testing Journal",
                        year="2026",
                        authors=("Reviewer A",),
                        abstract="A testing-level PubMed record.",
                        snippet="stroke risk",
                        url="https://pubmed.ncbi.nlm.nih.gov/123456/",
                        query_used=query,
                        doi="10.1000/test",
                    ),
                ),
                dedup_summary={"requested_pmids": 1, "unique_pmids": 1, "duplicate_pmids_removed": 0},
                search_execution_id="pubmedexec-ui-test",
            )

    monkeypatch.setattr("app.meta_analysis.workspace.PubMedSearchService", FakePubMedSearchService)
    monkeypatch.setattr("app.meta_analysis.workspace._show_message", lambda _text: None)
    summary = create_meta_analysis_project("Search Click Chain", tmp_path)
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(summary.project_root)
    _confirm_meta_pico_via_ui(widget, qt_app)

    widget.show_step("search_strategy")
    current = _current_step_widget(widget)
    _button_by_text(current, "生成检索策略").click()
    qt_app.processEvents()
    assert (summary.project_root / "protocol" / "search_strategy_v2" / "search_strategy_drafts.json").exists()

    widget.show_step("search_strategy")
    current = _current_step_widget(widget)
    _button_by_text(current, "确认全部检索式").click()
    qt_app.processEvents()
    confirmed_path = summary.project_root / "protocol" / "search_strategy_v2" / "search_strategy_confirmed.json"
    assert confirmed_path.exists()

    widget.show_step("search_strategy")
    current = _current_step_widget(widget)
    execute = _button_by_text(current, "执行 PubMed testing-level 检索")
    assert execute.isEnabled()
    assert execute.property("buttonBehavior") == "calls_pubmed_search_service_testing_level_and_writes_candidates_preview"
    execute.click()
    qt_app.processEvents()
    assert (summary.project_root / "protocol" / "search_execution_report.json").exists()
    preview_files = sorted((summary.project_root / "protocol" / "pubmed_candidates").glob("*_candidates_preview.json"))
    assert preview_files

    widget.show_step("search_strategy")
    current = _current_step_widget(widget)
    candidate_list = current.findChild(QListWidget, "metaPubMedCandidateList")
    assert candidate_list is not None
    assert candidate_list.count() == 1
    candidate_list.item(0).setSelected(True)
    _button_by_text(current, "选择加入文献库").click()
    qt_app.processEvents()

    records_path = summary.project_root / "literature" / "literature_records.json"
    assert records_path.exists()
    records = json.loads(records_path.read_text(encoding="utf-8"))
    assert records["records"][0]["pmid"] == "123456"
    assert records["records"][0]["screening_status"] == "not_started"
    assert not (summary.project_root / "screening" / "title_abstract_queue_v2.json").exists()

    widget.show_step("screening_review")
    current = _current_step_widget(widget)
    _assert_meta_buttons_are_auditable(current)
    _button_by_text(current, "生成重复组").click()
    qt_app.processEvents()
    assert (summary.project_root / "deduplication" / "duplicate_groups_v2.json").exists()

    widget.show_step("screening_review")
    current = _current_step_widget(widget)
    _button_by_text(current, "生成去重后文献库").click()
    qt_app.processEvents()
    assert (summary.project_root / "deduplication" / "deduplicated_literature_v2.json").exists()

    widget.show_step("screening_review")
    current = _current_step_widget(widget)
    _button_by_text(current, "创建标题摘要筛选队列").click()
    qt_app.processEvents()
    screening_queue = summary.project_root / "screening" / "title_abstract_queue_v2.json"
    assert screening_queue.exists()
    screening_payload = json.loads(screening_queue.read_text(encoding="utf-8"))
    assert screening_payload["record_count"] == 1
    assert screening_payload["auto_screening_enabled"] is False

    widget.show_step("manual_extraction")
    current = _current_step_widget(widget)
    _assert_meta_buttons_are_auditable(current)
    _button_by_text(current, "新建 study unit").click()
    qt_app.processEvents()
    assert (summary.project_root / "extraction" / "extraction_study_units.json").exists()

    widget.show_step("manual_extraction")
    current = _current_step_widget(widget)
    _button_by_text(current, "新建提取行").click()
    qt_app.processEvents()
    assert (summary.project_root / "extraction" / "extraction_effect_rows.json").exists()

    widget.show_step("statistics_analysis")
    current = _current_step_widget(widget)
    run_stats = _button_by_text(current, "运行统计分析")
    assert not run_stats.isEnabled()
    assert run_stats.property("disabledReason") == "requires_confirmed_analysis_plan"

    widget.show_step("report_export")
    current = _current_step_widget(widget)
    _assert_meta_buttons_are_auditable(current)
    _button_by_text(current, "生成 Markdown 草稿").click()
    qt_app.processEvents()
    assert (summary.project_root / "reports" / "formal_meta_report.md").exists()

    widget.show_step("report_export")
    current = _current_step_widget(widget)
    html_button = _button_by_text(current, "导出 HTML")
    assert html_button.property("buttonBehavior") == "calls_publication_export_service_export_html_report"
    html_button.click()
    qt_app.processEvents()
    html_path = summary.project_root / "reports" / "formal_meta_report.html"
    assert html_path.exists()
    assert "<html" in html_path.read_text(encoding="utf-8").lower()

    widget.show_step("report_export")
    current = _current_step_widget(widget)
    docx_button = _button_by_text(current, "导出 DOCX")
    assert docx_button.property("buttonBehavior") == "calls_publication_export_service_export_word_report"
    docx_button.click()
    qt_app.processEvents()
    docx_path = summary.project_root / "reports" / "formal_meta_report.docx"
    assert docx_path.exists()
    assert zipfile.is_zipfile(docx_path)
