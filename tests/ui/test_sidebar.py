from __future__ import annotations

from app.shell.sidebar import COMMON_SIDEBAR_ITEMS


def test_sidebar_exposes_primary_entries() -> None:
    keys = [item.key for item in COMMON_SIDEBAR_ITEMS]
    assert keys[:4] == ["dashboard", "bioinformatics", "meta_analysis", "labtools"]
    assert "settings" in keys
    assert "testing" in keys
