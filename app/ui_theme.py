from __future__ import annotations

from typing import Any


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

    palette.setColor(role.Window, QColor("#F8FAFC"))
    palette.setColor(role.WindowText, QColor("#0F172A"))
    palette.setColor(role.Base, QColor("#FFFFFF"))
    palette.setColor(role.AlternateBase, QColor("#F1F5F9"))
    palette.setColor(role.ToolTipBase, QColor("#FFFFFF"))
    palette.setColor(role.ToolTipText, QColor("#0F172A"))
    palette.setColor(role.Text, QColor("#0F172A"))
    palette.setColor(role.Button, QColor("#FFFFFF"))
    palette.setColor(role.ButtonText, QColor("#0F172A"))
    palette.setColor(role.BrightText, QColor("#FFFFFF"))
    palette.setColor(role.Highlight, QColor("#2563EB"))
    palette.setColor(role.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(group.Disabled, role.Text, QColor("#94A3B8"))
    palette.setColor(group.Disabled, role.ButtonText, QColor("#94A3B8"))
    palette.setColor(group.Disabled, role.WindowText, QColor("#94A3B8"))
    qt_app.setPalette(palette)
    qt_app.setStyleSheet(
        """
        QWidget {
            background-color: #F8FAFC;
            color: #0F172A;
        }
        QFrame, QGroupBox, QTabWidget::pane {
            background-color: #FFFFFF;
            color: #0F172A;
        }
        QLabel {
            background: transparent;
            color: #0F172A;
        }
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox,
        QTableWidget, QTreeWidget, QListWidget {
            background-color: #FFFFFF;
            color: #0F172A;
            selection-background-color: #DBEAFE;
            selection-color: #0F172A;
        }
        QPushButton {
            background-color: #FFFFFF;
            color: #0F172A;
            border: 1px solid #CBD5E1;
            border-radius: 6px;
            padding: 6px 10px;
        }
        QPushButton:hover {
            background-color: #F1F5F9;
        }
        QPushButton:disabled {
            background-color: #F8FAFC;
            color: #94A3B8;
        }
        QHeaderView::section {
            background-color: #F1F5F9;
            color: #0F172A;
            border: 1px solid #CBD5E1;
            padding: 4px;
        }
        QScrollArea, QScrollArea > QWidget > QWidget {
            background-color: #F8FAFC;
        }
        """
    )
