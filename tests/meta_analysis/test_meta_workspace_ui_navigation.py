from __future__ import annotations

from app.meta_analysis.workspace import meta_workspace_layout_state


def test_meta_workspace_layout_state_defines_internal_beta_navigation() -> None:
    state = meta_workspace_layout_state()

    assert state.status_label == "Developer Preview / testing"
    assert state.default_page_key == "workflow_dashboard"
    page_keys = [item.page_key for item in state.navigation_items]
    assert page_keys[:4] == ["workflow_dashboard", "protocol", "literature_import", "import_quality"]
    assert {"extraction", "quality", "analysis", "reporting", "audit"} <= set(page_keys)
    assert "不能作为 production" in state.testing_notice


def test_meta_workspace_navigation_has_one_page_key_per_item() -> None:
    state = meta_workspace_layout_state()

    labels = [item.label for item in state.navigation_items]
    page_keys = [item.page_key for item in state.navigation_items]
    assert len(labels) == len(page_keys)
    assert len(set(page_keys)) == len(page_keys)
    assert "Quality" in " ".join(labels)
    assert "Reporting" in " ".join(labels)
