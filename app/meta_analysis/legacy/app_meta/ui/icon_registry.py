from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon


ASSET_ROOT = Path(__file__).resolve().parents[2] / "assets"
META_ICON_ROOT = ASSET_ROOT / "meta_icons"

META_ICON_NAMES = {
    "home": "meta_home",
    "pico": "pico_search",
    "literature_import": "literature_import",
    "deduplication": "deduplication",
    "screening": "screening",
    "data_extraction": "data_extraction",
    "analysis_settings": "analysis_settings",
    "forest_plot": "forest_plot",
    "funnel_plot": "funnel_plot",
    "reporting": "reporting",
    "project_management": "project_management",
    "new_project": "new_project",
    "open_project": "open_project",
    "save_project": "save_project",
    "export_report": "export_report",
    "share": "share",
    "help": "help",
    "notification": "notification",
}


def meta_icon(name: str) -> QIcon:
    if name == "app":
        return QIcon(str(ASSET_ROOT / "meta_app_icon.png"))
    icon_name = META_ICON_NAMES.get(name, name)
    png_path = META_ICON_ROOT / "png" / f"{icon_name}.png"
    if png_path.exists():
        return QIcon(str(png_path))
    return QIcon(str(META_ICON_ROOT / "symbol" / f"{icon_name}.svg"))
