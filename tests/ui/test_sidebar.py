from __future__ import annotations

from app.shell.sidebar import COMMON_SIDEBAR_ITEMS


def test_sidebar_exposes_primary_entries() -> None:
    keys = [item.key for item in COMMON_SIDEBAR_ITEMS]
    assert keys[:5] == ["dashboard", "bioinformatics", "meta_analysis", "labtools", "centers"]
    assert "settings" in keys
    assert "test_feedback" in keys
    assert "about" in keys
