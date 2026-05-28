from __future__ import annotations

from typing import Any

from app.ui_style_tokens import THEME_PALETTE, global_app_stylesheet


def apply_light_app_theme(qt_app: Any) -> None:
    """Keep the desktop app on its own light theme instead of inheriting OS dark mode."""
    try:
        from PySide6.QtGui import QColor, QPalette
    except Exception:
        return

    qt_app.setStyle("Fusion")
    palette = QPalette()
    role = QPalette.ColorRole
    group = QPalette.ColorGroup

    palette.setColor(role.Window, QColor(THEME_PALETTE["window"]))
    palette.setColor(role.WindowText, QColor(THEME_PALETTE["window_text"]))
    palette.setColor(role.Base, QColor(THEME_PALETTE["base"]))
    palette.setColor(role.AlternateBase, QColor(THEME_PALETTE["alternate_base"]))
    palette.setColor(role.ToolTipBase, QColor(THEME_PALETTE["tooltip_base"]))
    palette.setColor(role.ToolTipText, QColor(THEME_PALETTE["tooltip_text"]))
    palette.setColor(role.Text, QColor(THEME_PALETTE["text"]))
    palette.setColor(role.Button, QColor(THEME_PALETTE["button"]))
    palette.setColor(role.ButtonText, QColor(THEME_PALETTE["button_text"]))
    palette.setColor(role.BrightText, QColor(THEME_PALETTE["bright_text"]))
    palette.setColor(role.Highlight, QColor(THEME_PALETTE["highlight"]))
    palette.setColor(role.HighlightedText, QColor(THEME_PALETTE["highlighted_text"]))
    palette.setColor(group.Disabled, role.Text, QColor(THEME_PALETTE["disabled_text"]))
    palette.setColor(group.Disabled, role.ButtonText, QColor(THEME_PALETTE["disabled_text"]))
    palette.setColor(group.Disabled, role.WindowText, QColor(THEME_PALETTE["disabled_text"]))
    qt_app.setPalette(palette)
    qt_app.setStyleSheet(global_app_stylesheet())
