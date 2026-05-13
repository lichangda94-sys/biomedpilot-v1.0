from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QListWidget, QPushButton, QTextEdit
except Exception as exc:  # pragma: no cover
    QApplication = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

from app.meta_analysis.project_workspace import create_meta_analysis_project
from app.meta_analysis.search.pubmed_search_service import PubMedSearchExecution, PubMedSearchResult
from app.meta_analysis.services.pico_workspace_service import PICOWorkspaceService


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def _current_step_widget(widget):
    scroll = widget._page_stack.currentWidget()
    return scroll.widget()


def _button(widget, text: str) -> QPushButton:
    return next(button for button in widget.findChildren(QPushButton) if button.text() == text)


def _visible_text(widget) -> str:
    texts: list[str] = []
    for child in [*widget.findChildren(QLabel), *widget.findChildren(QPushButton)]:
        if child.isVisibleTo(widget) and child.text():
            texts.append(child.text())
    return "\n".join(texts)


def _confirmed_meta_project(tmp_path: Path) -> Path:
    summary = create_meta_analysis_project("Stage M2", tmp_path)
    service = PICOWorkspaceService()
    service.generate_draft(summary.project_root, "肥胖暴露与甲状腺癌风险是否相关？", pico_mode="peco")
    service.edit_draft(
        summary.project_root,
        actor="reviewer",
        updates={
            "population": "甲状腺癌人群",
            "exposure": "肥胖",
            "comparator": "非肥胖",
            "outcome": "发病风险",
            "study_design": "observational study",
        },
    )
    service.confirm_protocol(
        summary.project_root,
        actor="reviewer",
        confirmed_meta_type="exposure_disease_risk_meta",
        overrides={
            "confirmed_pico_mode": "peco",
            "confirmed_population": "甲状腺癌人群",
            "confirmed_intervention_or_exposure": "肥胖",
            "confirmed_comparator": "非肥胖",
            "confirmed_outcomes": ("发病风险",),
            "confirmed_study_design": "observational study",
        },
    )
    return summary.project_root


class FakePubMedSearchService:
    def search_pubmed(self, query: str, *, max_results: int = 20, timeout_seconds: float = 10.0) -> PubMedSearchExecution:
        return PubMedSearchExecution(
            success=True,
            query_used=query,
            executed_at="2026-05-12T00:00:00+00:00",
            result_count=2,
            returned_count=2,
            search_execution_id="pubmedexec-ui-m2",
            records=(
                PubMedSearchResult(
                    pmid="111",
                    doi="10.1000/ui111",
                    title="Obesity and thyroid cancer risk",
                    journal="Meta UI Journal",
                    year="2024",
                    publication_date="2024",
                    authors=("Alice Adams",),
                    abstract="Candidate abstract.",
                    snippet="Candidate abstract.",
                    url="https://pubmed.ncbi.nlm.nih.gov/111/",
                    query_used=query,
                ),
                PubMedSearchResult(
                    pmid="222",
                    doi="10.1000/ui222",
                    title="BMI and thyroid neoplasms",
                    journal="Meta UI Journal",
                    year="2025",
                    publication_date="2025",
                    authors=("Ben Baker",),
                    abstract="Second abstract.",
                    snippet="Second abstract.",
                    url="https://pubmed.ncbi.nlm.nih.gov/222/",
                    query_used=query,
                ),
            ),
        )


def test_search_strategy_page_reads_confirmed_protocol_and_blocks_pubmed_until_confirmed(qt_app, tmp_path: Path) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    project_dir = _confirmed_meta_project(tmp_path)
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(project_dir)
    widget.show()
    widget.show_step("search_strategy")
    qt_app.processEvents()

    current = _current_step_widget(widget)
    assert "下一阶段将基于该方案生成检索策略" in _visible_text(current)
    execute_button = current.findChild(QPushButton, "metaPubMedExecuteButton")
    assert execute_button is not None
    assert not execute_button.isEnabled()

    _button(current, "生成检索策略").click()
    qt_app.processEvents()
    widget.show_step("search_strategy")
    current = _current_step_widget(widget)
    assert not current.findChild(QPushButton, "metaPubMedExecuteButton").isEnabled()

    _button(current, "确认当前检索式").click()
    qt_app.processEvents()
    widget.show_step("search_strategy")
    current = _current_step_widget(widget)
    assert current.findChild(QPushButton, "metaPubMedExecuteButton").isEnabled()


def test_non_pubmed_database_hides_online_execution_button(qt_app, tmp_path: Path) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    project_dir = _confirmed_meta_project(tmp_path)
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(project_dir)
    widget.show()
    widget.show_step("search_strategy")
    current = _current_step_widget(widget)
    _button(current, "生成检索策略").click()
    qt_app.processEvents()

    widget.show_step("search_strategy")
    current = _current_step_widget(widget)
    database_list = current.findChild(QListWidget, "metaSearchDatabaseList")
    execute_button = current.findChild(QPushButton, "metaPubMedExecuteButton")
    assert database_list is not None
    assert execute_button is not None

    database_list.setCurrentRow(1)
    qt_app.processEvents()

    assert "当前版本支持检索式生成与本地导入，不执行联网检索" in _visible_text(current)
    assert not execute_button.isVisibleTo(current)


def test_pubmed_candidates_can_be_selected_and_added_to_library(qt_app, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import app.meta_analysis.workspace as workspace
    from app.meta_analysis.pages.workflow_integration_page import meta_workflow_integration_state_from_project
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    monkeypatch.setattr(workspace, "PubMedSearchService", FakePubMedSearchService)
    monkeypatch.setattr(workspace, "_show_message", lambda _text: None)
    project_dir = _confirmed_meta_project(tmp_path)
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(project_dir)
    widget.show()
    widget.show_step("search_strategy")
    current = _current_step_widget(widget)
    _button(current, "生成检索策略").click()
    qt_app.processEvents()

    widget.show_step("search_strategy")
    current = _current_step_widget(widget)
    _button(current, "确认当前检索式").click()
    qt_app.processEvents()

    widget.show_step("search_strategy")
    current = _current_step_widget(widget)
    current.findChild(QPushButton, "metaPubMedExecuteButton").click()
    qt_app.processEvents()

    widget.show_step("search_strategy")
    current = _current_step_widget(widget)
    candidates = current.findChild(QListWidget, "metaPubMedCandidateList")
    assert candidates is not None
    assert candidates.count() == 2
    candidates.item(0).setSelected(True)
    _button(current, "选择加入文献库").click()
    qt_app.processEvents()

    library = json.loads((project_dir / "literature" / "literature_records.json").read_text(encoding="utf-8"))
    statuses = {step.step_id: step.status for step in meta_workflow_integration_state_from_project(project_dir).steps}
    assert library["record_count"] == 1
    assert library["records"][0]["pmid"] == "111"
    assert statuses["search_strategy"] == "已完成"
    assert statuses["literature_import"] == "已完成"
    assert statuses["screening"] in {"草稿", "待确认"}

    widget.show_step("literature_import")
    current = _current_step_widget(widget)
    assert "当前文献总数：1" in _visible_text(current)
    assert "PubMed 来源数量：1" in _visible_text(current)
