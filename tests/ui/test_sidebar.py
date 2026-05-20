from __future__ import annotations

import os

import pytest

from app.shell.sidebar import COMMON_SIDEBAR_ITEMS
from app.shared.semantic_keys import NavKey

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QPushButton

    from app.shell.sidebar import SidebarWidget
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    QPushButton = None  # type: ignore[assignment]
    SidebarWidget = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


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
    assert [item.semantic_key for item in COMMON_SIDEBAR_ITEMS] == [
        NavKey.DASHBOARD.value,
        NavKey.BIOINFORMATICS.value,
        NavKey.META_ANALYSIS.value,
        NavKey.LABTOOLS.value,
        NavKey.SETTINGS.value,
        NavKey.TEST_FEEDBACK.value,
        NavKey.ABOUT.value,
    ]


def test_sidebar_buttons_expose_semantic_nav_keys(qt_app) -> None:
    widget = SidebarWidget(
        on_dashboard=lambda: None,
        on_bioinformatics=lambda: None,
        on_meta_analysis=lambda: None,
        on_labtools=lambda: None,
        on_settings=lambda: None,
        on_test_feedback=lambda: None,
        on_about=lambda: None,
    )

    buttons = widget.findChildren(QPushButton)

    assert [button.property("pageKey") for button in buttons] == [item.key for item in COMMON_SIDEBAR_ITEMS]
    assert [button.property("semanticKey") for button in buttons] == [item.semantic_key for item in COMMON_SIDEBAR_ITEMS]
