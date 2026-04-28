from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from app.ui_icon_registry import APP_ICON_ICNS_PATH, APP_ICON_PNG_PATH, IconFactory


APP_NAME = "BioMedPilot"
APP_WINDOW_TITLE = "BioMedPilot · 生信分析"
BIOINFORMATICS_WINDOW_TITLE = APP_WINDOW_TITLE
META_ANALYSIS_WINDOW_TITLE = "BioMedPilot · Meta 分析"
APP_ORGANIZATION_NAME = "BioMedPilot"

APP_RESOURCE_DIR = Path(__file__).resolve().parent / "resources"


def load_app_icon() -> QIcon:
    return IconFactory.app_icon()


def apply_app_identity(app: QApplication) -> None:
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setOrganizationName(APP_ORGANIZATION_NAME)
    app.setWindowIcon(load_app_icon())
