from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QListWidget, QPushButton, QTableWidget, QTextEdit
except Exception as exc:  # pragma: no cover
    QApplication = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

from app.meta_analysis.project_workspace import create_meta_analysis_project
from app.meta_analysis.services.literature_library_service import LiteratureLibraryService


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
    for child in widget.findChildren(QTextEdit):
        if child.isVisibleTo(widget) and child.toPlainText():
            texts.append(child.toPlainText())
    return "\n".join(texts)


def test_stage_m3_literature_page_shows_diagnostics_and_detail(qt_app, tmp_path: Path) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    project_dir = _stage_m3_project(tmp_path)
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(project_dir)
    widget.show()
    widget.show_step("literature_import")
    qt_app.processEvents()

    current = _current_step_widget(widget)
    table = current.findChild(QTableWidget, "metaLiteratureRecordsTable")
    assert table is not None
    assert table.rowCount() == 3
    assert "缺 DOI 数：1" in _visible_text(current)
    assert "缺 PMID 数：1" in _visible_text(current)
    assert "按来源统计" in _visible_text(current)

    table.selectRow(0)
    table.cellClicked.emit(0, 0)
    qt_app.processEvents()
    detail = current.findChild(QTextEdit, "metaLiteratureDetailPanel")
    assert detail is not None
    assert "英文标题：" in detail.toPlainText()
    assert "用户备注：" in detail.toPlainText()


def test_stage_m3_dedup_review_merge_prisma_and_screening_queue(qt_app, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import app.meta_analysis.workspace as workspace
    from app.meta_analysis.pages.workflow_integration_page import meta_workflow_integration_state_from_project
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    monkeypatch.setattr(workspace, "_show_message", lambda _text: None)
    project_dir = _stage_m3_project(tmp_path)
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(project_dir)
    widget.show()
    widget.show_step("screening_review")
    qt_app.processEvents()

    current = _current_step_widget(widget)
    _button(current, "生成重复组").click()
    qt_app.processEvents()
    widget.show_step("screening_review")
    current = _current_step_widget(widget)
    groups = current.findChild(QListWidget, "metaDedupGroupList")
    assert groups is not None
    assert groups.count() >= 1
    groups.setCurrentRow(0)
    qt_app.processEvents()
    detail = current.findChild(QTextEdit, "metaDedupGroupDetail")
    assert detail is not None
    assert "PMID/DOI" in detail.toPlainText()
    assert "推荐保留" in detail.toPlainText()

    _button(current, "保存人工决定").click()
    qt_app.processEvents()
    widget.show_step("screening_review")
    current = _current_step_widget(widget)
    assert "已合并" in _visible_text(current)

    _button(current, "生成去重后文献库").click()
    qt_app.processEvents()
    widget.show_step("screening_review")
    current = _current_step_widget(widget)
    assert "duplicate records removed：1" in _visible_text(current)
    assert "records after deduplication：2" in _visible_text(current)

    _button(current, "创建标题摘要筛选队列").click()
    qt_app.processEvents()
    statuses = {step.step_id: step.status for step in meta_workflow_integration_state_from_project(project_dir).steps}
    assert statuses["screening"] == "待筛选"
    assert (project_dir / "screening" / "title_abstract_queue_v2.json").exists()


def _stage_m3_project(tmp_path: Path) -> Path:
    summary = create_meta_analysis_project("Stage M3", tmp_path)
    project_dir = summary.project_root
    LiteratureLibraryService().import_records(
        project_dir,
        project_id="stage-m3-ui",
        source_type="pubmed_confirmed_candidates",
        source_name="PubMed",
        raw_records=[
            {
                "record_id": "lit-ui-a",
                "title": "Obesity and thyroid cancer risk",
                "abstract": "Candidate abstract.",
                "authors": ["Alice Adams"],
                "journal": "Journal A",
                "year": "2024",
                "pmid": "111",
                "doi": "10.1000/ui-a",
            },
            {
                "record_id": "lit-ui-b",
                "title": "Obesity and thyroid cancer risk extended",
                "abstract": "Candidate abstract, longer.",
                "authors": ["Alice Adams", "Ben Baker"],
                "journal": "Journal A",
                "year": "2024",
                "pmid": "111",
                "doi": "10.1000/ui-b",
            },
        ],
    )
    LiteratureLibraryService().import_records(
        project_dir,
        project_id="stage-m3-ui",
        source_type="csv",
        source_name="CSV",
        raw_records=[
            {
                "record_id": "lit-ui-c",
                "title": "Local sparse import",
                "authors": ["Carol Chen"],
                "year": "2023",
            }
        ],
    )
    return project_dir
