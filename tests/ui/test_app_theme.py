from __future__ import annotations

import sys

import pytest

QtGui = pytest.importorskip("PySide6.QtGui")
QtWidgets = pytest.importorskip("PySide6.QtWidgets")
QApplication = QtWidgets.QApplication
QPalette = QtGui.QPalette

from app.ui_theme import apply_light_app_theme
from app.ui_style_tokens import COLORS, THEME_PALETTE


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication(sys.argv)
    return app


def test_app_theme_uses_light_palette_even_after_dark_palette(qt_app) -> None:
    dark = QPalette()
    role = QPalette.ColorRole
    dark.setColor(role.Window, QtGui.QColor("#111827"))
    dark.setColor(role.WindowText, QtGui.QColor("#F9FAFB"))
    dark.setColor(role.Base, QtGui.QColor("#030712"))
    dark.setColor(role.Text, QtGui.QColor("#F9FAFB"))
    qt_app.setPalette(dark)

    apply_light_app_theme(qt_app)

    palette = qt_app.palette()
    assert palette.color(role.Window).lightness() > 220
    assert palette.color(role.Base).lightness() > 240
    assert palette.color(role.Text).lightness() < 80
    assert THEME_PALETTE["window"] == COLORS["background"]
    assert THEME_PALETTE["window_text"] == COLORS["text"]
    assert COLORS["background"] in qt_app.styleSheet()
    assert COLORS["text"] in qt_app.styleSheet()
