from __future__ import annotations

from app.meta_analysis.workspace import meta_workspace_layout_state


def test_meta_workspace_layout_state_defines_internal_beta_navigation() -> None:
    state = meta_workspace_layout_state()

    assert "0.1.0-internal-beta" in state.status_label
    assert "内部测试版 / Developer Preview / testing" in state.status_label
    assert state.title == "Meta 分析模块"
    assert state.default_page_key == "workflow_dashboard"
    page_keys = [item.page_key for item in state.navigation_items]
    assert page_keys[:4] == ["workflow_dashboard", "protocol", "literature_import", "import_quality"]
    assert {"extraction", "quality", "analysis", "reporting", "audit"} <= set(page_keys)
    assert "不能作为正式临床" in state.testing_notice


def test_meta_workspace_navigation_has_one_page_key_per_item() -> None:
    state = meta_workspace_layout_state()

    labels = [item.label for item in state.navigation_items]
    page_keys = [item.page_key for item in state.navigation_items]
    assert len(labels) == len(page_keys)
    assert len(set(page_keys)) == len(page_keys)
    assert "质量评价 Quality Assessment" in " ".join(labels)
    assert "结果报告 Reporting" in " ".join(labels)
