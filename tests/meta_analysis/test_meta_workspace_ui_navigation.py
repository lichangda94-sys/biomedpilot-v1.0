from __future__ import annotations

import json
import os

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


def test_meta_workspace_layout_state_defines_internal_beta_navigation() -> None:
    state = meta_workspace_layout_state()

    assert "0.1.0-internal-beta" in state.status_label
    assert "内部测试版 / Developer Preview / testing" in state.status_label
    assert state.title == "Meta 分析模块"
    assert state.default_page_key == "workflow_home"
    page_keys = [item.page_key for item in state.navigation_items]
    assert page_keys == ["workflow_home", "pico_workspace", "search_strategy", "title_abstract_screening", "manual_extraction", "statistics_analysis", "report_export"]
    assert [item.label for item in state.navigation_items] == [
        "Meta 项目首页",
        "研究问题 / PICO",
        "检索与文献导入",
        "文献筛选",
        "数据提取与质量评价",
        "统计分析与结果",
        "PRISMA 与报告导出",
    ]
    assert "不能作为正式临床" in state.testing_notice


def test_meta_workspace_navigation_has_one_page_key_per_item() -> None:
    state = meta_workspace_layout_state()

    labels = [item.label for item in state.navigation_items]
    page_keys = [item.page_key for item in state.navigation_items]
    assert len(labels) == len(page_keys)
    assert len(set(page_keys)) == len(page_keys)
    assert labels == [
        "Meta 项目首页",
        "研究问题 / PICO",
        "检索与文献导入",
        "文献筛选",
        "数据提取与质量评价",
        "统计分析与结果",
        "PRISMA 与报告导出",
    ]


def test_meta_workspace_widget_mounts_current_development_pages(qt_app) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    widget = MetaAnalysisWorkspaceWidget()
    page_keys = widget.page_keys()

    assert widget.meta_workspace_layout_state()["global_nav"] == "metaGlobalNav"
    assert widget.meta_workspace_layout_state()["workflow_nav"] == "metaWorkflowNav"
    assert widget.meta_workspace_layout_state()["current_step_workspace"] == "metaCurrentStepWorkspace"
    assert "manual_extraction" in page_keys
    assert "statistics_analysis" in page_keys
    assert "search_strategy" in page_keys
    assert "report_export" in page_keys
    assert len(page_keys) == 7


def test_meta_workspace_mounts_seven_main_pages_without_auto_outputs(qt_app, tmp_path) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(tmp_path)

    expected_pages = {
        "metaProjectHomePage",
        "metaPicoPage",
        "metaSearchStrategyPage",
        "metaTitleAbstractScreeningPage",
        "metaManualExtractionPage",
        "metaStatisticsAnalysisPage",
        "metaReportExportPage",
    }
    mounted_pages = {frame.objectName() for frame in widget.findChildren(QFrame)}

    assert expected_pages <= mounted_pages
    assert not (tmp_path / "analysis" / "runs").exists()
    assert not (tmp_path / "analysis" / "results").exists()
    assert not (tmp_path / "reports" / "formal_meta_report.md").exists()
    assert not list((tmp_path / "exports").glob("reproducibility_package_*.zip"))


def test_meta_workspace_no_project_disables_research_question_entry(qt_app) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    widget = MetaAnalysisWorkspaceWidget()
    buttons = [button for button in widget.findChildren(QPushButton) if button.text() == "继续：研究问题 / PICO"]

    assert buttons
    assert all(not button.isEnabled() for button in buttons)
    assert "请先新建或打开 Meta 项目" in " ".join(label.text() for label in widget.findChildren(QLabel))


def test_meta_workspace_creates_project_and_manifest_from_home(qt_app, tmp_path) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    widget = MetaAnalysisWorkspaceWidget()
    widget.set_new_project_form(project_name="Thyroid Cancer Review", research_topic="肥胖与甲状腺癌风险", save_location=tmp_path)
    summary = widget.create_meta_project_from_form()

    assert summary is not None
    assert summary.project_name == "Thyroid Cancer Review"
    assert widget.current_project_dir() == summary.project_root
    assert (summary.project_root / "meta_project_manifest.json").exists()
    assert (summary.project_root / "meta_project_config.json").exists()
    for directory in META_PROJECT_DIRECTORIES:
        assert (summary.project_root / directory).is_dir()
    manifest = json.loads((summary.project_root / "meta_project_manifest.json").read_text(encoding="utf-8"))
    assert manifest["project_type"] == "meta_analysis"
    assert manifest["developer_preview"] is True
    assert manifest["workflow_stage"] == "project_home"
    assert manifest["status"] == "created"
    assert widget.current_page_key() == "workflow_home"
    buttons = [button for button in widget.findChildren(QPushButton) if button.text() == "继续：研究问题 / PICO"]
    assert any(button.isEnabled() for button in buttons)


def test_meta_workspace_opens_existing_project_and_rejects_invalid_folder(qt_app, tmp_path) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    summary = create_meta_analysis_project("Opened Meta", tmp_path)
    widget = MetaAnalysisWorkspaceWidget()
    assert widget.open_meta_project_folder(summary.project_root) is True
    assert widget.current_project_dir() == summary.project_root
    assert "Opened Meta" in " ".join(label.text() for label in widget.findChildren(QLabel))

    invalid = tmp_path / "not_a_meta_project"
    invalid.mkdir()
    assert widget.open_meta_project_folder(invalid) is False
    assert "不是有效的 Meta 项目" in " ".join(label.text() for label in widget.findChildren(QLabel))
