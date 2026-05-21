from __future__ import annotations

import csv
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication, QPushButton

    from app.app_identity import BIOINFORMATICS_PAGE_ICON_PATHS, load_bioinformatics_page_icon
    from app.bioinformatics.workspace import BioinformaticsWorkspaceWidget
    from app.shared.semantic_keys import ModuleKey, PageKey
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    QIcon = None  # type: ignore[assignment]
    QPushButton = None  # type: ignore[assignment]
    BioinformaticsWorkspaceWidget = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


ROOT = Path(__file__).resolve().parents[2]
PILOT_MANIFEST = ROOT / "docs/ui/UI_B8b4c_1_p1_bio_page_icon_active_pilot_manifest_20260521.csv"
BIO_PAGE_KEYS = (
    PageKey.BIO_PROJECT_HOME.value,
    PageKey.BIO_DATA_SOURCE.value,
    PageKey.BIO_DATA_CHECK_PREPARATION.value,
    PageKey.BIO_GROUP_DESIGN.value,
    PageKey.BIO_ANALYSIS_TASKS.value,
    PageKey.BIO_RESULT_REPORT.value,
    PageKey.BIO_REPORT_EXPORT.value,
    PageKey.BIO_SETTINGS_RESOURCES.value,
    PageKey.BIO_PROJECT_LOGS_TECHNICAL_DETAILS.value,
)


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


@pytest.fixture
def bio_workspace(qt_app):
    widget = BioinformaticsWorkspaceWidget()
    yield widget
    widget.close()
    widget.deleteLater()
    qt_app.processEvents()


def _read_manifest() -> list[dict[str, str]]:
    with PILOT_MANIFEST.open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_bio_page_active_icon_assets_exist_and_are_registered(qt_app) -> None:
    assert set(BIOINFORMATICS_PAGE_ICON_PATHS) == set(BIO_PAGE_KEYS)
    for semantic_key in BIO_PAGE_KEYS:
        path = BIOINFORMATICS_PAGE_ICON_PATHS[semantic_key]
        assert path.exists()
        assert path.parent == ROOT / "assets/icons/bioinformatics/pages"
        assert not load_bioinformatics_page_icon(semantic_key).isNull()


def test_bio_page_icon_loader_keeps_safe_missing_icon_fallback() -> None:
    assert load_bioinformatics_page_icon("bio.page.unknown").isNull()
    assert load_bioinformatics_page_icon("meta.page.project_home").isNull()
    assert load_bioinformatics_page_icon("feature.status.testing").isNull()


def test_bioinformatics_target_ia_nav_renders_bio_page_icons(bio_workspace) -> None:
    nav_items = bio_workspace.findChildren(QPushButton, "bioinformaticsIANavItem")

    assert len(nav_items) == 9
    assert tuple(item.property("pageKey") for item in nav_items) == bio_workspace.target_ia_page_keys()
    assert [item.property("semanticKey") for item in nav_items] == list(BIO_PAGE_KEYS)
    assert all(item.property("moduleKey") == ModuleKey.BIOINFORMATICS.value for item in nav_items)
    assert all(item.property("iconFallback") is False for item in nav_items)
    assert all(not item.icon().isNull() for item in nav_items)
    assert all(str(item.property("iconSource")).startswith(str(ROOT / "assets/icons/bioinformatics/pages")) for item in nav_items)


def test_bioinformatics_seven_step_main_flow_and_auxiliary_pages_remain_unchanged(bio_workspace) -> None:
    nav_items = bio_workspace.findChildren(QPushButton, "bioinformaticsIANavItem")
    main_items = [item for item in nav_items if item.property("pageGroup") == "main_flow"]
    auxiliary_items = [item for item in nav_items if item.property("pageGroup") == "auxiliary"]

    assert [item.property("pageKey") for item in main_items] == [
        "project_home",
        "data_source",
        "data_check_preparation",
        "group_design",
        "analysis_tasks",
        "result_report",
        "report_export",
    ]
    assert [item.property("flowIndex") for item in main_items] == list(range(1, 8))
    assert [item.property("pageKey") for item in auxiliary_items] == [
        "settings_resources",
        "project_logs_technical_details",
    ]
    assert [item.property("flowIndex") for item in auxiliary_items] == [1, 2]
    assert all(not item.isEnabled() for item in nav_items)
    assert all(item.property("formalActionEnabled") is False for item in nav_items)


def test_bio_page_icon_fallback_preserves_nav_labels_and_gates(qt_app, monkeypatch) -> None:
    import app.bioinformatics.workspace as workspace

    monkeypatch.setattr(workspace, "load_bioinformatics_page_icon", lambda _semantic_key: QIcon())
    widget = workspace.BioinformaticsWorkspaceWidget()
    try:
        nav_items = widget.findChildren(QPushButton, "bioinformaticsIANavItem")

        assert len(nav_items) == 9
        assert all(item.text() for item in nav_items)
        assert all("\n" in item.text() for item in nav_items)
        assert all(item.property("iconFallback") is True for item in nav_items)
        assert all(item.icon().isNull() for item in nav_items)
        assert all(not item.isEnabled() for item in nav_items)
        assert all(item.property("formalActionEnabled") is False for item in nav_items)
    finally:
        widget.close()
        widget.deleteLater()
        qt_app.processEvents()


def test_bio_page_icon_pilot_manifest_marks_only_bio_pages_active() -> None:
    rows = _read_manifest()
    active = [row for row in rows if row["active_pilot"] == "true"]
    prior = [row for row in rows if row["prior_active_pilot"] == "true"]
    future = [row for row in rows if row["future_target"] == "true"]

    assert len(rows) == 31
    assert len(active) == 9
    assert {row["resource_family"] for row in active} == {"bio_pages"}
    assert all(row["active_asset_path"].startswith("assets/icons/bioinformatics/pages/") for row in active)
    assert len(prior) == 12
    assert {row["resource_family"] for row in prior} == {"modules", "labtools"}
    assert len(future) == 10
    assert {row["resource_family"] for row in future} == {"meta_pages"}


def test_non_bio_icon_families_are_not_in_bioinformatics_page_active_assets() -> None:
    forbidden_paths = [
        ROOT / "assets/icons/bioinformatics/pages/meta_page_project_home.svg",
        ROOT / "assets/icons/bioinformatics/pages/status_testing.svg",
        ROOT / "assets/icons/bioinformatics/pages/resource_cloud_ai.svg",
        ROOT / "assets/icons/bioinformatics/pages/export_pdf.svg",
        ROOT / "assets/icons/bioinformatics/pages/empty_project.svg",
        ROOT / "assets/icons/app/bio_page_project_home.svg",
    ]

    assert all(not path.exists() for path in forbidden_paths)
