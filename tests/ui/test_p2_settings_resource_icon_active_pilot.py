from __future__ import annotations

import csv
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtGui import QPixmap
    from PySide6.QtWidgets import QApplication, QLabel, QListWidget, QPushButton

    from app.app_identity import SETTINGS_RESOURCE_ICON_PATHS, load_settings_resource_icon
    from app.shell.main_window import MainWindow
    from app.shared.semantic_keys import ModuleKey, PageKey
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    QPixmap = None  # type: ignore[assignment]
    QLabel = None  # type: ignore[assignment]
    QListWidget = None  # type: ignore[assignment]
    QPushButton = None  # type: ignore[assignment]
    MainWindow = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


ROOT = Path(__file__).resolve().parents[2]
PILOT_MANIFEST = ROOT / "docs/ui/UI_B8b5b_p2_settings_resource_icon_active_pilot_manifest_20260521.csv"
SETTINGS_RESOURCE_KEYS = (
    "resource_external_engine",
    "resource_image_analysis_engine",
    "resource_imagej_fiji",
    "resource_pdf_ocr",
    "resource_local_model",
    "resource_cloud_ai",
    "resource_python",
    "resource_r",
    "resource_go",
    "resource_kegg",
    "resource_analysis_package",
    "resource_plotting_package",
    "resource_developer_diagnostics",
)


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


@pytest.fixture
def settings_window(qt_app):
    window = MainWindow()
    window._welcome_page.enter_workspace()
    window.show_settings()
    yield window
    window.close()
    window.deleteLater()
    qt_app.processEvents()


def _read_manifest() -> list[dict[str, str]]:
    with PILOT_MANIFEST.open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_settings_resource_active_assets_exist_and_are_registered(qt_app) -> None:
    assert set(SETTINGS_RESOURCE_ICON_PATHS) == set(SETTINGS_RESOURCE_KEYS)
    for resource_key in SETTINGS_RESOURCE_KEYS:
        path = SETTINGS_RESOURCE_ICON_PATHS[resource_key]
        assert path.exists()
        assert path.parent == ROOT / "assets/icons/settings/resources"
        assert not load_settings_resource_icon(resource_key).isNull()


def test_settings_resource_icon_loader_keeps_safe_missing_icon_fallback() -> None:
    assert load_settings_resource_icon("resource_unknown").isNull()
    assert load_settings_resource_icon("status_testing").isNull()
    assert load_settings_resource_icon("export_pdf").isNull()
    assert load_settings_resource_icon("empty_project").isNull()
    assert load_settings_resource_icon("app_icon_deferred").isNull()


def test_settings_shell_renders_resource_icons_without_changing_gates(settings_window) -> None:
    icons = settings_window.findChildren(QLabel, "settingsResourceIcon")
    detect_buttons = settings_window.findChildren(QPushButton, "settingsDetectButton")
    install_buttons = settings_window.findChildren(QPushButton, "settingsInstallButton")
    cloud_buttons = settings_window.findChildren(QPushButton, "settingsCloudConfigButton")

    assert {icon.property("resourceKey") for icon in icons} == set(SETTINGS_RESOURCE_KEYS)
    assert all(icon.property("moduleKey") == ModuleKey.SETTINGS.value for icon in icons)
    assert all(icon.property("iconFallback") is False for icon in icons)
    assert all(str(icon.property("iconSource")).startswith(str(ROOT / "assets/icons/settings/resources")) for icon in icons)
    assert all(icon.property("statusKey") in {"available", "not_configured", "planned", "preflight_only", "developer_preview", "blocked"} for icon in icons)

    assert detect_buttons
    assert all(button.isEnabled() for button in detect_buttons)
    assert install_buttons
    assert all(not button.isEnabled() for button in install_buttons)
    assert cloud_buttons
    assert all(not button.isEnabled() for button in cloud_buttons)


def test_settings_resource_icons_preserve_page_semantics(settings_window) -> None:
    icons = settings_window.findChildren(QLabel, "settingsResourceIcon")
    by_key = {icon.property("resourceKey"): icon for icon in icons}

    assert by_key["resource_imagej_fiji"].property("semanticKey") == PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value
    assert by_key["resource_pdf_ocr"].property("semanticKey") == PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value
    assert by_key["resource_local_model"].property("semanticKey") == PageKey.SETTINGS_MODEL_ENGINE.value
    assert by_key["resource_cloud_ai"].property("semanticKey") == PageKey.SETTINGS_MODEL_ENGINE.value
    assert by_key["resource_go"].property("semanticKey") == PageKey.SETTINGS_ANALYSIS_RESOURCES.value
    assert by_key["resource_kegg"].property("semanticKey") == PageKey.SETTINGS_ANALYSIS_RESOURCES.value
    assert by_key["resource_developer_diagnostics"].property("semanticKey") == PageKey.SETTINGS_DEVELOPER_DIAGNOSTICS.value


def test_settings_resource_icon_fallback_preserves_labels_chips_and_button_gates(qt_app, monkeypatch) -> None:
    import app.shell.main_window as main_window

    monkeypatch.setattr(main_window, "load_settings_resource_pixmap", lambda _resource_key, size=32: QPixmap())
    window = main_window.MainWindow()
    window._welcome_page.enter_workspace()
    window.show_settings()
    try:
        icons = window.findChildren(QLabel, "settingsResourceIcon")
        detect_buttons = window.findChildren(QPushButton, "settingsDetectButton")
        install_buttons = window.findChildren(QPushButton, "settingsInstallButton")
        cloud_buttons = window.findChildren(QPushButton, "settingsCloudConfigButton")
        labels = "\n".join(label.text() for label in window.findChildren(QLabel))

        assert {icon.property("resourceKey") for icon in icons} == set(SETTINGS_RESOURCE_KEYS)
        assert all(icon.property("iconFallback") is True for icon in icons)
        assert "ImageJ/Fiji" in labels
        assert "本地 AI 模型" in labels
        assert "外部云端模型配置" in labels
        assert all(button.isEnabled() for button in detect_buttons)
        assert all(not button.isEnabled() for button in install_buttons)
        assert all(not button.isEnabled() for button in cloud_buttons)
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_imagej_fiji_remains_out_of_labtools_primary_entries(settings_window) -> None:
    settings_window.show_labtools()
    labtools_content = settings_window.findChild(QLabel, "labtoolsShellTitle").parent()
    primary_titles = [label.text() for label in labtools_content.findChildren(QLabel, "labtoolsPrimaryEntryTitle")]
    labels = "\n".join(label.text() for label in labtools_content.findChildren(QLabel))

    assert all("ImageJ" not in title and "Fiji" not in title for title in primary_titles)
    assert "ImageJ/Fiji" not in labels


def test_settings_resource_icon_active_pilot_manifest_marks_only_settings_resources_active() -> None:
    rows = _read_manifest()

    assert len(rows) == 13
    assert {row["resource_id"] for row in rows} == set(SETTINGS_RESOURCE_KEYS)
    assert {row["resource_family"] for row in rows} == {"settings_resources"}
    assert all(row["active_pilot"] == "true" for row in rows)
    assert all(row["replacement_state"] == "pilot_only" for row in rows)
    assert all(row["replacement_ready"] == "pilot_only" for row in rows)
    assert all(row["active_asset_path"].startswith("assets/icons/settings/resources/") for row in rows)


def test_non_settings_resource_icon_families_are_not_in_settings_active_assets() -> None:
    forbidden_paths = [
        ROOT / "assets/icons/settings/resources/status_testing.svg",
        ROOT / "assets/icons/settings/resources/result_chart.svg",
        ROOT / "assets/icons/settings/resources/report_generate.svg",
        ROOT / "assets/icons/settings/resources/export_pdf.svg",
        ROOT / "assets/icons/settings/resources/empty_project.svg",
        ROOT / "assets/icons/app/resource_cloud_ai.svg",
    ]

    assert all(not path.exists() for path in forbidden_paths)
