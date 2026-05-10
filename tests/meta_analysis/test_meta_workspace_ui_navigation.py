from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from app.meta_analysis.workspace import meta_workspace_layout_state

try:
    from PySide6.QtWidgets import QApplication
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
    assert page_keys == [
        "workflow_home",
        "pico_workspace",
        "search_strategy",
        "literature_acquisition",
        "literature_library",
        "dedup_review",
        "exclusion_criteria",
        "title_abstract_screening",
        "fulltext_management",
        "manual_extraction",
        "ai_extraction",
        "quality_assessment",
        "analysis_plan",
        "statistics_analysis",
        "figure_results",
        "prisma",
        "report_export",
        "reproducibility_package",
    ]
    assert "不能作为正式临床" in state.testing_notice


def test_meta_workspace_navigation_has_one_page_key_per_item() -> None:
    state = meta_workspace_layout_state()

    labels = [item.label for item in state.navigation_items]
    page_keys = [item.page_key for item in state.navigation_items]
    assert len(labels) == len(page_keys)
    assert len(set(page_keys)) == len(page_keys)
    assert "质量评价" in " ".join(labels)
    assert "报告导出" in " ".join(labels)
    assert "数据提取" in " ".join(labels)


def test_meta_workspace_widget_mounts_current_development_pages(qt_app) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    widget = MetaAnalysisWorkspaceWidget()
    page_keys = widget.page_keys()

    assert widget.meta_workspace_layout_state()["global_nav"] == "metaGlobalNav"
    assert widget.meta_workspace_layout_state()["workflow_nav"] == "metaWorkflowNav"
    assert widget.meta_workspace_layout_state()["current_step_workspace"] == "metaCurrentStepWorkspace"
    assert "manual_extraction" in page_keys
    assert "ai_extraction" in page_keys
    assert "statistics_analysis" in page_keys
    assert "literature_acquisition" in page_keys
    assert "reproducibility_package" in page_keys
