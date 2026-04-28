from __future__ import annotations


class Theme:
    background = "#F4F7FB"
    sidebar = "#FFFFFF"
    card = "#FFFFFF"
    border = "#DDE5EF"
    border_soft = "#E8EEF6"
    text = "#172033"
    muted = "#667085"
    muted_light = "#98A2B3"
    primary = "#2563EB"
    primary_soft = "#EAF1FF"
    success = "#16A34A"
    success_soft = "#EAF8EF"
    warning = "#D97706"
    warning_soft = "#FFF7E8"
    danger = "#DC2626"
    danger_soft = "#FEECEC"
    radius = 16
    radius_small = 10
    spacing = 16
    font_body = 14
    font_small = 12
    font_title = 22
    font_large = 28


def app_stylesheet() -> str:
    return f"""
    QWidget {{
        background: {Theme.background};
        color: {Theme.text};
        font-size: {Theme.font_body}px;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
    }}
    QLabel {{
        background: transparent;
    }}
    QLabel#pageTitle {{
        font-size: {Theme.font_large}px;
        font-weight: 700;
    }}
    QLabel#sectionTitle {{
        font-size: 16px;
        font-weight: 700;
    }}
    QLabel#muted {{
        color: {Theme.muted};
    }}
    QLabel#smallMuted {{
        color: {Theme.muted};
        font-size: {Theme.font_small}px;
    }}
    QFrame#card {{
        background: {Theme.card};
        border: 1px solid {Theme.border_soft};
        border-radius: {Theme.radius}px;
    }}
    QFrame#sidebar {{
        background: {Theme.sidebar};
        border-right: 1px solid {Theme.border_soft};
    }}
    QPushButton {{
        background: {Theme.card};
        border: 1px solid {Theme.border};
        border-radius: {Theme.radius_small}px;
        padding: 8px 12px;
        color: {Theme.text};
    }}
    QPushButton:hover {{
        background: #F8FAFC;
    }}
    QPushButton#primaryButton {{
        color: white;
        background: {Theme.primary};
        border-color: {Theme.primary};
    }}
    QPushButton#sidebarButton {{
        border: 0;
        text-align: left;
        padding: 10px 12px;
        background: transparent;
    }}
    QPushButton#sidebarButton:checked {{
        color: {Theme.primary};
        background: {Theme.primary_soft};
        font-weight: 700;
    }}
    QLineEdit, QComboBox {{
        background: {Theme.card};
        border: 1px solid {Theme.border};
        border-radius: {Theme.radius_small}px;
        padding: 8px 10px;
    }}
    QProgressBar {{
        background: #EDF2F7;
        border: 0;
        border-radius: 7px;
        height: 14px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background: {Theme.primary};
        border-radius: 7px;
    }}
    QTableWidget {{
        background: {Theme.card};
        border: 0;
        gridline-color: {Theme.border_soft};
    }}
    QHeaderView::section {{
        background: #F8FAFC;
        border: 0;
        border-bottom: 1px solid {Theme.border_soft};
        padding: 7px;
        font-weight: 700;
    }}
    QStatusBar {{
        background: {Theme.card};
        color: {Theme.muted};
        border-top: 1px solid {Theme.border_soft};
    }}
    """
