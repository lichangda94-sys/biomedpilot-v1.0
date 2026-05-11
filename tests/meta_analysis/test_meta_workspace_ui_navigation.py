from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from app.meta_analysis.project_workspace import META_PROJECT_DIRECTORIES, create_meta_analysis_project
from app.meta_analysis.workspace import meta_workspace_layout_state

try:
    from PySide6.QtWidgets import QApplication, QFrame, QLabel, QPushButton
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


def test_meta_workspace_layout_state_uses_seven_user_facing_stages() -> None:
    state = meta_workspace_layout_state()

    assert "0.1.0-internal-beta" in state.status_label
    assert state.title == "Meta 分析模块"
    assert state.default_page_key == "workflow_home"
    assert [item.page_key for item in state.navigation_items] == [
        "workflow_home",
        "pico_workspace",
        "search_strategy",
        "title_abstract_screening",
        "manual_extraction",
        "statistics_analysis",
        "report_export",
    ]
    assert [item.label for item in state.navigation_items] == [
        "Meta 项目首页",
        "研究问题 / PICO",
        "检索与导入",
        "文献筛选",
        "提取与质量评价",
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
        "title_abstract_screening",
        "manual_extraction",
        "statistics_analysis",
        "report_export",
    )
    mounted_pages = {frame.objectName() for frame in widget.findChildren(QFrame)}
    assert {
        "metaProjectHomePage",
        "metaPicoPage",
        "metaSearchStrategyPage",
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
    assert "请先新建或打开 Meta 项目" in _visible_text(widget)


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
