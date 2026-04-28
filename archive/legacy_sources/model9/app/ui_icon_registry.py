from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

from app.biomed_icons import biomed_icon
from app.ui_style_tokens import ICON_SIZE


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ICON_ASSET_ROOT = PROJECT_ROOT / "assets" / "icons"

APP_ICON_DIR = ICON_ASSET_ROOT / "app_icon"
SIDEBAR_ICON_DIR = ICON_ASSET_ROOT / "sidebar_icons"
STATUS_ICON_DIR = ICON_ASSET_ROOT / "status_icons"
DASHBOARD_ICON_DIR = ICON_ASSET_ROOT / "dashboard_icons"
TOOLBAR_ICON_DIR = ICON_ASSET_ROOT / "toolbar_icons"
EMPTY_STATE_ILLUSTRATION_DIR = ICON_ASSET_ROOT / "empty_state_illustrations"
CONTACT_SHEET_DIR = ICON_ASSET_ROOT / "contact_sheets"
ICON_MANIFEST_PATH = ICON_ASSET_ROOT / "manifest.json"

APP_ICON_PNG_PATH = APP_ICON_DIR / "app_icon.png"
APP_ICON_ICNS_PATH = APP_ICON_DIR / "app_icon.icns"


SIDEBAR_ICON_NAMES = {
    "home": "home",
    "data-search": "search",
    "data-assets": "assets",
    "sample-groups": "groups",
    "deg": "deg",
    "enrichment": "enrichment",
    "correlation": "correlation",
    "survival": "survival",
    "visualization": "visualization",
    "reporting": "reporting",
    "tasks": "tasks",
}

STATUS_ICON_NAMES = {
    "ready": "completed",
    "needs_attention": "attention",
    "running": "running",
    "completed": "completed",
    "locked": "locked",
    "not_started": "not_started",
}

DASHBOARD_ICON_NAMES = {
    "data_sources": "assets",
    "current_project": "project",
    "active_tasks": "running",
    "sample_count": "samples",
}

EMPTY_STATE_NAMES = {
    "no_project": "project",
    "no_data": "assets",
    "no_report": "reporting",
    "no_task": "tasks",
}

TOOLBAR_ICON_NAMES = {
    "import": "download",
    "pipeline": "enrichment",
    "results": "completed",
    "charts": "visualization",
    "export": "reporting",
    "notifications": "running",
}


class IconFactory:
    @staticmethod
    def app_icon() -> QIcon:
        return _icon_from_asset(APP_ICON_PNG_PATH, "project", ICON_SIZE["stat"])

    @staticmethod
    def sidebar_icon(key: str) -> QIcon:
        return _registered_icon(SIDEBAR_ICON_DIR, key, SIDEBAR_ICON_NAMES, ICON_SIZE["nav"])

    @staticmethod
    def status_icon(key: str) -> QIcon:
        return _registered_icon(STATUS_ICON_DIR, key, STATUS_ICON_NAMES, ICON_SIZE["status"])

    @staticmethod
    def dashboard_icon(key: str) -> QIcon:
        return _registered_icon(DASHBOARD_ICON_DIR, key, DASHBOARD_ICON_NAMES, ICON_SIZE["stat"])

    @staticmethod
    def empty_state_icon(key: str) -> QIcon:
        return _registered_icon(EMPTY_STATE_ILLUSTRATION_DIR, key, EMPTY_STATE_NAMES, ICON_SIZE["empty"])

    @staticmethod
    def toolbar_icon(key: str) -> QIcon:
        return _registered_icon(TOOLBAR_ICON_DIR, key, TOOLBAR_ICON_NAMES, ICON_SIZE["toolbar"])

    @staticmethod
    def icon_size(kind: str) -> QSize:
        value = ICON_SIZE[kind]
        return QSize(value, value)


def _registered_icon(asset_dir: Path, key: str, registry: dict[str, str], size: int) -> QIcon:
    fallback_name = registry.get(key, key)
    return _icon_from_asset(asset_dir / f"{key}.png", fallback_name, size)


def _icon_from_asset(path: Path, fallback_name: str, size: int) -> QIcon:
    if path.exists() and path.stat().st_size > 0:
        icon = QIcon(str(path))
        if not icon.isNull():
            return icon
    return biomed_icon(fallback_name, size)
