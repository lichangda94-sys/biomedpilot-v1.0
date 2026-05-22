from __future__ import annotations

import csv
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtGui import QPixmap
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton

    from app.app_identity import MODULE_ICON_PATHS, load_module_icon
    from app.shell.dashboard import build_dashboard_model
    from app.shell.module_selection import ModuleSelectionWidget
    from app.shell.sidebar import SidebarWidget
    from app.shared.semantic_keys import ModuleKey
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    QLabel = None  # type: ignore[assignment]
    QPushButton = None  # type: ignore[assignment]
    ModuleSelectionWidget = None  # type: ignore[assignment]
    SidebarWidget = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


ROOT = Path(__file__).resolve().parents[2]
PILOT_MANIFEST = ROOT / "docs/ui/icon_production/UI_B8b4a_p1_module_icon_active_pilot_manifest_20260521.csv"


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def _read_manifest() -> list[dict[str, str]]:
    with PILOT_MANIFEST.open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_active_module_icon_assets_exist_and_are_registered(qt_app) -> None:
    expected = {
        ModuleKey.BIOINFORMATICS.value: "module_bioinformatics.svg",
        ModuleKey.META_ANALYSIS.value: "module_meta_analysis.svg",
        ModuleKey.LABTOOLS.value: "module_labtools.svg",
        ModuleKey.SETTINGS.value: "module_settings.svg",
    }

    for module_key, filename in expected.items():
        path = MODULE_ICON_PATHS[module_key]
        assert path == ROOT / "assets/icons/modules" / filename
        assert path.exists()
        assert not load_module_icon(module_key).isNull()


def test_module_icon_loader_keeps_safe_missing_icon_fallback() -> None:
    assert load_module_icon("module.unknown").isNull()
    assert load_module_icon("status_testing").isNull()


def test_dashboard_module_cards_render_with_active_module_icons(qt_app) -> None:
    widget = ModuleSelectionWidget(dashboard=build_dashboard_model())
    icons = widget.findChildren(QLabel, "moduleIcon")

    assert len(icons) == 3
    assert [icon.property("moduleKey") for icon in icons] == [
        ModuleKey.BIOINFORMATICS.value,
        ModuleKey.META_ANALYSIS.value,
        ModuleKey.LABTOOLS.value,
    ]
    assert all(icon.property("iconFallback") is False for icon in icons)
    assert all(str(icon.property("iconSource")).startswith(str(ROOT / "assets/icons/modules")) for icon in icons)
    assert all(icon.pixmap() is not None and not icon.pixmap().isNull() for icon in icons)


def test_dashboard_module_icon_fallback_preserves_text_labels(qt_app, monkeypatch) -> None:
    import app.shell.module_selection as module_selection

    monkeypatch.setattr(module_selection, "load_module_pixmap", lambda _module_key, _size=72: QPixmap())
    widget = module_selection.ModuleSelectionWidget(dashboard=build_dashboard_model())

    labels = "\n".join(label.text() for label in widget.findChildren(QLabel))
    icons = widget.findChildren(QLabel, "moduleIcon")

    assert "Bioinformatics / 生信分析" in labels
    assert "Meta Analysis / Meta 分析" in labels
    assert "LabTools / 实验工具" in labels
    assert all(icon.property("iconFallback") is True for icon in icons)
    assert all(icon.pixmap() is not None and not icon.pixmap().isNull() for icon in icons)


def test_sidebar_module_entries_render_with_active_module_icons(qt_app) -> None:
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
    module_buttons = [button for button in buttons if button.property("moduleKey")]

    assert [button.property("moduleKey") for button in module_buttons] == [
        ModuleKey.BIOINFORMATICS.value,
        ModuleKey.META_ANALYSIS.value,
        ModuleKey.LABTOOLS.value,
        ModuleKey.SETTINGS.value,
    ]
    assert all(button.text() for button in module_buttons)
    assert all(not button.icon().isNull() for button in module_buttons)
    assert all(button.property("iconFallback") is False for button in module_buttons)


def test_pilot_manifest_marks_only_modules_active() -> None:
    rows = _read_manifest()
    active = [row for row in rows if row["active_pilot"] == "true"]
    inactive = [row for row in rows if row["active_pilot"] == "false"]

    assert len(rows) == 31
    assert len(active) == 4
    assert {row["resource_family"] for row in active} == {"modules"}
    assert all(row["replacement_state"] == "pilot_only" for row in active)
    assert all(row["replacement_ready"] == "pilot_only" for row in active)
    assert all(row["active_asset_path"].startswith("assets/icons/modules/") for row in active)
    assert all(row["active_asset_path"] == "" for row in inactive)
    assert all(row["resource_family"] in {"labtools", "bio_pages", "meta_pages"} for row in inactive)


def test_non_p1_icon_families_are_not_in_active_pilot_assets() -> None:
    forbidden_paths = [
        ROOT / "assets/icons/modules/resource_cloud_ai.svg",
        ROOT / "assets/icons/modules/export_pdf.svg",
        ROOT / "assets/icons/modules/empty_project.svg",
        ROOT / "assets/icons/modules/status_testing.svg",
        ROOT / "assets/icons/app/module_bioinformatics.svg",
    ]

    assert all(not path.exists() for path in forbidden_paths)
