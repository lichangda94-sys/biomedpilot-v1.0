from __future__ import annotations

import csv
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication, QPushButton

    from app.app_identity import META_PAGE_ICON_PATHS, load_meta_page_icon
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget, meta_target_ia_pages
    from app.shared.semantic_keys import ModuleKey, PageKey
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    QIcon = None  # type: ignore[assignment]
    QPushButton = None  # type: ignore[assignment]
    MetaAnalysisWorkspaceWidget = None  # type: ignore[assignment]
    meta_target_ia_pages = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


ROOT = Path(__file__).resolve().parents[2]
PILOT_MANIFEST = ROOT / "docs/ui/UI_B8b4c_2_p1_meta_page_icon_active_pilot_manifest_20260521.csv"
META_PAGE_KEYS = (
    PageKey.META_PROJECT_HOME.value,
    PageKey.META_QUESTION_TYPE.value,
    PageKey.META_SEARCH_STRATEGY.value,
    PageKey.META_IMPORT_DEDUP.value,
    PageKey.META_SCREENING.value,
    PageKey.META_FULLTEXT_EXTRACTION.value,
    PageKey.META_QUALITY_ASSESSMENT.value,
    PageKey.META_ANALYSIS_TASKS.value,
    PageKey.META_RESULT_REPORT.value,
    PageKey.META_REPORT_EXPORT.value,
)
EXPECTED_TARGET_PAGE_KEYS = (
    "project_home",
    "question_meta_type",
    "search_strategy",
    "import_dedup",
    "screening",
    "fulltext_extraction",
    "quality_assessment",
    "analysis_tasks",
    "result_report",
    "report_export",
    "meta_settings",
)


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


@pytest.fixture
def meta_workspace(qt_app):
    widget = MetaAnalysisWorkspaceWidget()
    yield widget
    widget.close()
    widget.deleteLater()
    qt_app.processEvents()


def _read_manifest() -> list[dict[str, str]]:
    with PILOT_MANIFEST.open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_meta_page_active_icon_assets_exist_and_are_registered(qt_app) -> None:
    assert set(META_PAGE_ICON_PATHS) == set(META_PAGE_KEYS)
    for semantic_key in META_PAGE_KEYS:
        path = META_PAGE_ICON_PATHS[semantic_key]
        assert path.exists()
        assert path.parent == ROOT / "assets/icons/meta/pages"
        assert not load_meta_page_icon(semantic_key).isNull()


def test_meta_page_icon_loader_keeps_safe_missing_icon_fallback() -> None:
    assert load_meta_page_icon("meta.page.unknown").isNull()
    assert load_meta_page_icon(PageKey.META_SETTINGS.value).isNull()
    assert load_meta_page_icon("bio.page.project_home").isNull()
    assert load_meta_page_icon("feature.status.testing").isNull()


def test_meta_target_ia_nav_renders_meta_page_icons_with_settings_fallback(meta_workspace) -> None:
    nav_items = meta_workspace.findChildren(QPushButton, "metaTargetIANavItem")

    assert len(nav_items) == len(meta_target_ia_pages())
    assert tuple(item.property("pageKey") for item in nav_items) == meta_workspace.target_ia_page_keys()
    assert meta_workspace.target_ia_page_keys() == EXPECTED_TARGET_PAGE_KEYS
    assert all(item.property("moduleKey") == ModuleKey.META_ANALYSIS.value for item in nav_items)
    assert all(item.property("formalActionEnabled") is False for item in nav_items)

    by_semantic_key = {item.property("semanticKey"): item for item in nav_items}
    for semantic_key in META_PAGE_KEYS:
        item = by_semantic_key[semantic_key]
        assert item.property("iconFallback") is False
        assert not item.icon().isNull()
        assert str(item.property("iconSource")).startswith(str(ROOT / "assets/icons/meta/pages"))

    settings = by_semantic_key[PageKey.META_SETTINGS.value]
    assert settings.property("pageKey") == "meta_settings"
    assert settings.property("iconSource") == ""
    assert settings.property("iconFallback") is True
    assert settings.text()


def test_meta_page_icons_do_not_change_ia_or_execution_gates(meta_workspace) -> None:
    nav_items = meta_workspace.findChildren(QPushButton, "metaTargetIANavItem")
    pages = meta_target_ia_pages()

    assert [page.key for page in pages] == list(EXPECTED_TARGET_PAGE_KEYS)
    assert [page.flow_index for page in pages if page.page_group == "main_flow"] == list(range(1, 11))
    assert [page.key for page in pages if page.page_group == "auxiliary"] == ["meta_settings"]
    assert meta_workspace.network_meta_enabled() is False
    assert all(item.property("interactionMode") == "select_only" for item in nav_items)
    assert all(item.property("formalActionEnabled") is False for item in nav_items)
    assert {item.property("pageKey") for item in nav_items if item.property("semanticState") == "planned"} == {
        "quality_assessment",
        "analysis_tasks",
    }
    assert {item.property("pageKey") for item in nav_items if item.property("semanticState") == "shell_only"} == {
        "project_home",
        "result_report",
        "report_export",
        "meta_settings",
    }


def test_meta_page_icon_fallback_preserves_nav_labels_and_gates(qt_app, monkeypatch) -> None:
    import app.meta_analysis.workspace as workspace

    monkeypatch.setattr(workspace, "load_meta_page_icon", lambda _semantic_key: QIcon())
    widget = workspace.MetaAnalysisWorkspaceWidget()
    try:
        nav_items = widget.findChildren(QPushButton, "metaTargetIANavItem")

        assert len(nav_items) == len(workspace.meta_target_ia_pages())
        assert all(item.text() for item in nav_items)
        assert all("\n" in item.text() for item in nav_items)
        assert all(item.property("iconFallback") is True for item in nav_items)
        assert all(item.icon().isNull() for item in nav_items)
        assert all(item.isEnabled() for item in nav_items)
        assert all(item.property("formalActionEnabled") is False for item in nav_items)
    finally:
        widget.close()
        widget.deleteLater()
        qt_app.processEvents()


def test_meta_page_icon_pilot_manifest_marks_only_meta_pages_active() -> None:
    rows = _read_manifest()
    active = [row for row in rows if row["active_pilot"] == "true"]
    prior = [row for row in rows if row["prior_active_pilot"] == "true"]
    future = [row for row in rows if row["future_target"] == "true"]

    assert len(rows) == 31
    assert len(active) == 10
    assert {row["resource_family"] for row in active} == {"meta_pages"}
    assert all(row["active_asset_path"].startswith("assets/icons/meta/pages/") for row in active)
    assert len(prior) == 21
    assert {row["resource_family"] for row in prior} == {"modules", "labtools", "bio_pages"}
    assert len(future) == 0


def test_non_meta_icon_families_are_not_in_meta_page_active_assets() -> None:
    forbidden_paths = [
        ROOT / "assets/icons/meta/pages/bio_page_project_home.svg",
        ROOT / "assets/icons/meta/pages/status_testing.svg",
        ROOT / "assets/icons/meta/pages/resource_cloud_ai.svg",
        ROOT / "assets/icons/meta/pages/export_pdf.svg",
        ROOT / "assets/icons/meta/pages/empty_project.svg",
        ROOT / "assets/icons/app/meta_page_project_home.svg",
    ]

    assert all(not path.exists() for path in forbidden_paths)
