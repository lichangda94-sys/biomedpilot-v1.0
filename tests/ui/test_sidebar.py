from __future__ import annotations

from app.shell.sidebar import COMMON_SIDEBAR_ITEMS


def test_sidebar_exposes_primary_entries() -> None:
    keys = [item.key for item in COMMON_SIDEBAR_ITEMS]
    assert keys == [
        "dashboard",
        "bioinformatics",
        "meta_analysis",
        "labtools",
        "settings",
        "test_feedback",
        "about",
    ]
