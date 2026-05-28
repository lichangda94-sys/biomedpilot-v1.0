from __future__ import annotations

import csv
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtGui import QPixmap
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QScrollArea

    from app.app_identity import LABTOOLS_ICON_PATHS, load_labtools_icon
    from app.shell.main_window import MainWindow
    from app.shared.semantic_keys import ModuleKey, PageKey
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    QLabel = None  # type: ignore[assignment]
    QPushButton = None  # type: ignore[assignment]
    QScrollArea = None  # type: ignore[assignment]
    MainWindow = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


ROOT = Path(__file__).resolve().parents[2]
PILOT_MANIFEST = ROOT / "docs/ui/UI_B8b4b_p1_labtools_icon_active_pilot_manifest_20260521.csv"
LABTOOLS_KEYS = (
    PageKey.LABTOOLS_GENERAL_CALCULATORS.value,
    PageKey.LABTOOLS_REAGENT_PREPARATION.value,
    PageKey.LABTOOLS_EXPERIMENT_MODULES.value,
    PageKey.LABTOOLS_CELL_EXPERIMENTS.value,
    PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value,
    PageKey.LABTOOLS_NUCLEIC_ACID_EXPERIMENTS.value,
    PageKey.LABTOOLS_IMMUNO_ABSORBANCE.value,
    PageKey.LABTOOLS_IHC.value,
)


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


@pytest.fixture
def labtools_window(qt_app):
    window = MainWindow()
    window._welcome_page.enter_workspace()
    window.show_labtools()
    yield window
    window.close()
    window.deleteLater()
    qt_app.processEvents()


def _read_manifest() -> list[dict[str, str]]:
    with PILOT_MANIFEST.open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_labtools_active_icon_assets_exist_and_are_registered(qt_app) -> None:
    assert set(LABTOOLS_ICON_PATHS) == set(LABTOOLS_KEYS)
    for semantic_key in LABTOOLS_KEYS:
        path = LABTOOLS_ICON_PATHS[semantic_key]
        assert path.exists()
        assert path.parent == ROOT / "assets/icons/labtools"
        assert not load_labtools_icon(semantic_key).isNull()


def test_labtools_icon_loader_keeps_safe_missing_icon_fallback() -> None:
    assert load_labtools_icon("labtools.page.unknown").isNull()
    assert load_labtools_icon("bio.page.project_home").isNull()
    assert load_labtools_icon("feature.status.testing").isNull()


def test_labtools_home_renders_three_primary_entry_icons(labtools_window) -> None:
    icons = labtools_window.findChildren(QLabel, "labtoolsEntryIcon")
    titles = labtools_window.findChildren(QLabel, "labtoolsPrimaryEntryTitle")

    assert [label.property("semanticKey") for label in titles] == [
        PageKey.LABTOOLS_GENERAL_CALCULATORS.value,
        PageKey.LABTOOLS_REAGENT_PREPARATION.value,
        PageKey.LABTOOLS_EXPERIMENT_MODULES.value,
    ]
    assert [icon.property("semanticKey") for icon in icons] == [
        PageKey.LABTOOLS_GENERAL_CALCULATORS.value,
        PageKey.LABTOOLS_REAGENT_PREPARATION.value,
        PageKey.LABTOOLS_EXPERIMENT_MODULES.value,
    ]
    assert all(icon.property("moduleKey") == ModuleKey.LABTOOLS.value for icon in icons)
    assert all(icon.property("iconFallback") is False for icon in icons)
    assert all(icon.pixmap() is not None and not icon.pixmap().isNull() for icon in icons)


def test_labtools_experiment_categories_render_as_nested_icons_not_primary_entries(labtools_window) -> None:
    category_icons = labtools_window.findChildren(QLabel, "labtoolsCategoryIcon")
    category_labels = labtools_window.findChildren(QLabel, "labtoolsCategoryIconLabel")
    primary_titles = [label.text() for label in labtools_window.findChildren(QLabel, "labtoolsPrimaryEntryTitle")]

    assert primary_titles == ["通用计算器", "试剂制备", "实验模块"]
    assert [icon.property("semanticKey") for icon in category_icons] == [
        PageKey.LABTOOLS_CELL_EXPERIMENTS.value,
        PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value,
        PageKey.LABTOOLS_NUCLEIC_ACID_EXPERIMENTS.value,
        PageKey.LABTOOLS_IMMUNO_ABSORBANCE.value,
        PageKey.LABTOOLS_IHC.value,
    ]
    assert [label.text() for label in category_labels] == [
        "细胞实验",
        "蛋白实验",
        "核酸实验",
        "免疫与吸光度",
        "免疫组化",
    ]
    assert all(icon.property("iconFallback") is False for icon in category_icons)


def test_labtools_icon_fallback_preserves_labels_and_disabled_shell_buttons(qt_app, monkeypatch) -> None:
    import app.shell.main_window as main_window

    monkeypatch.setattr(main_window, "load_labtools_pixmap", lambda _semantic_key, _size=48: QPixmap())
    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()
        window.show_labtools()
        content = window.findChild(QScrollArea, "labtoolsShellPage").widget()
        labels = "\n".join(label.text() for label in content.findChildren(QLabel))
        icons = content.findChildren(QLabel, "labtoolsEntryIcon") + content.findChildren(QLabel, "labtoolsCategoryIcon")
        buttons = content.findChildren(QPushButton, "labtoolsEntryButton")

        assert "通用计算器" in labels
        assert "试剂制备" in labels
        assert "实验模块" in labels
        assert "细胞实验" in labels
        assert all(icon.property("iconFallback") is True for icon in icons)
        assert all(button.property("moduleKey") == ModuleKey.LABTOOLS.value for button in buttons)
        assert all(button.isEnabled() for button in buttons)
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_labtools_icon_pilot_manifest_marks_only_labtools_active() -> None:
    rows = _read_manifest()
    active = [row for row in rows if row["active_pilot"] == "true"]
    prior = [row for row in rows if row["prior_active_pilot"] == "true"]
    inactive = [row for row in rows if row["active_pilot"] == "false" and row["prior_active_pilot"] == "false"]

    assert len(rows) == 31
    assert len(active) == 8
    assert {row["resource_family"] for row in active} == {"labtools"}
    assert all(row["active_asset_path"].startswith("assets/icons/labtools/") for row in active)
    assert all(row["replacement_state"] == "pilot_only" for row in active)
    assert len(prior) == 4
    assert {row["resource_family"] for row in prior} == {"modules"}
    assert all(row["resource_family"] in {"bio_pages", "meta_pages"} for row in inactive)


def test_non_labtools_icon_families_are_not_in_labtools_active_assets() -> None:
    forbidden_paths = [
        ROOT / "assets/icons/labtools/bio_page_project_home.svg",
        ROOT / "assets/icons/labtools/meta_page_project_home.svg",
        ROOT / "assets/icons/labtools/status_testing.svg",
        ROOT / "assets/icons/labtools/resource_cloud_ai.svg",
        ROOT / "assets/icons/labtools/export_pdf.svg",
        ROOT / "assets/icons/labtools/empty_project.svg",
        ROOT / "assets/icons/app/labtools_general_calculator.svg",
    ]

    assert all(not path.exists() for path in forbidden_paths)
