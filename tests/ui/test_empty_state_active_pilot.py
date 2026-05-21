from __future__ import annotations

import csv
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtGui import QPixmap
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton

    import app.shared.ui_components.primitives as primitives
    from app.app_identity import (
        EMPTY_STATE_IMAGE_PATHS,
        EMPTY_STATE_SEMANTIC_IMAGE_KEYS,
        load_empty_state_illustration,
        load_empty_state_pixmap,
    )
    from app.shared.result_report_export_shell import empty_result_preview_state, make_result_preview_empty_state
    from app.shared.semantic_keys import AnalysisStatusKey, ResourceStatusKey, ResultSemanticKey
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    QLabel = None  # type: ignore[assignment]
    QPushButton = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


ROOT = Path(__file__).resolve().parents[2]
PILOT_MANIFEST = ROOT / "docs/ui/UI_B8b6b_empty_state_active_pilot_manifest_20260521.csv"
ACTIVE_DIR = ROOT / "assets/images/empty_states"


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def _read_manifest() -> list[dict[str, str]]:
    with PILOT_MANIFEST.open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_empty_state_active_assets_exist_and_are_registered(qt_app) -> None:
    rows = _read_manifest()

    assert len(rows) == 6
    assert set(EMPTY_STATE_IMAGE_PATHS) == {row["resource_id"] for row in rows}
    for row in rows:
        path = EMPTY_STATE_IMAGE_PATHS[row["resource_id"]]
        assert path == ROOT / row["active_asset_path"]
        assert path.exists()
        assert not load_empty_state_illustration(row["resource_id"]).isNull()
        assert not load_empty_state_pixmap(row["resource_id"], size=72).isNull()


def test_empty_state_loader_keeps_safe_missing_family_fallback() -> None:
    assert load_empty_state_illustration("empty_unknown").isNull()
    assert load_empty_state_illustration("status_testing").isNull()
    assert load_empty_state_illustration("result_overview").isNull()
    assert load_empty_state_illustration("export_pdf").isNull()
    assert load_empty_state_illustration("app_icon_deferred").isNull()


def test_empty_state_semantic_aliases_are_scoped_to_six_resources() -> None:
    assert EMPTY_STATE_SEMANTIC_IMAGE_KEYS[ResultSemanticKey.TESTING_SUMMARY_ONLY.value] == "empty_result"
    assert EMPTY_STATE_SEMANTIC_IMAGE_KEYS[ResourceStatusKey.NOT_CONFIGURED.value] == "empty_missing_resource"
    assert EMPTY_STATE_SEMANTIC_IMAGE_KEYS[AnalysisStatusKey.PREFLIGHT_ONLY.value] == "empty_preflight_only"
    assert ResultSemanticKey.FORMAL_COMPUTED_RESULT.value not in EMPTY_STATE_SEMANTIC_IMAGE_KEYS


def test_shared_empty_state_renders_illustration_without_changing_text_or_action(qt_app) -> None:
    empty = primitives.make_empty_state(
        "No project",
        "Create or open a project first.",
        action_text="Open",
        empty_state_key="empty_project",
    )
    illustration = empty.findChild(QLabel, "uiEmptyStateIllustration")

    assert empty.objectName() == "uiEmptyState"
    assert empty.property("uiPrimitive") == "empty_state"
    assert empty.property("emptyStateKey") == "empty_project"
    assert empty.property("emptyStateImageFallback") is False
    assert illustration is not None
    assert illustration.property("emptyStateKey") == "empty_project"
    assert illustration.pixmap() is not None and not illustration.pixmap().isNull()
    assert empty.findChild(QLabel, "uiEmptyStateTitle").text() == "No project"
    assert empty.findChild(QLabel, "uiEmptyStateBody").text() == "Create or open a project first."
    assert empty.findChild(QPushButton).property("buttonRole") == "secondary"


def test_shared_empty_state_missing_illustration_fallback_preserves_content(qt_app, monkeypatch) -> None:
    monkeypatch.setattr("app.app_identity.load_empty_state_pixmap", lambda *_args, **_kwargs: QPixmap())
    empty = primitives.make_empty_state(
        "No data",
        "The table has no rows yet.",
        action_text="Refresh",
        empty_state_key="empty_result",
    )

    assert empty.property("emptyStateKey") == "empty_result"
    assert empty.property("emptyStateImageFallback") is True
    assert empty.findChild(QLabel, "uiEmptyStateIllustration") is None
    assert empty.findChild(QLabel, "uiEmptyStateTitle").text() == "No data"
    assert empty.findChild(QLabel, "uiEmptyStateBody").text() == "The table has no rows yet."
    assert empty.findChild(QPushButton).text() == "Refresh"


def test_result_preview_empty_state_keeps_semantics_and_gating_with_illustration(qt_app) -> None:
    state = empty_result_preview_state(module="bioinformatics")
    empty = make_result_preview_empty_state(state)
    illustration = empty.findChild(QLabel, "uiEmptyStateIllustration")

    assert empty.property("emptyStateKey") == "empty_result"
    assert empty.property("resultSemanticKey") == ResultSemanticKey.TESTING_SUMMARY_ONLY.value
    assert empty.property("semanticKey") == ResultSemanticKey.TESTING_SUMMARY_ONLY.value
    assert empty.property("exportGate") == "disabled_empty_result"
    assert empty.property("reportReadyPackageAllowed") is None
    assert illustration is not None
    assert illustration.property("emptyStateKey") == "empty_result"
    assert "不构成正式统计结果" in empty.findChild(QLabel, "uiEmptyStateBody").text()


def test_empty_state_active_pilot_manifest_marks_only_empty_states_active() -> None:
    rows = _read_manifest()

    assert len(rows) == 6
    assert all(row["resource_family"] == "empty_states" for row in rows)
    assert all(row["active_pilot"] == "true" for row in rows)
    assert all(row["replacement_state"] == "pilot_only" for row in rows)
    assert all(row["replacement_ready"] == "pilot_only" for row in rows)
    assert all(row["fallback_required"] == "true" for row in rows)
    assert all(row["active_asset_path"].startswith("assets/images/empty_states/") for row in rows)
    assert all(not row["resource_id"].startswith(("status_", "result_", "report_", "export_", "share_")) for row in rows)
    assert all("app_icon" not in row["resource_id"] for row in rows)


def test_active_empty_state_directory_excludes_deferred_icon_families() -> None:
    active_names = {path.name for path in ACTIVE_DIR.glob("*")}

    assert "status_testing.svg" not in active_names
    assert "result_overview.svg" not in active_names
    assert "report_generate.svg" not in active_names
    assert "export_pdf.svg" not in active_names
    assert "app_icon_deferred.svg" not in active_names
    assert all(name.startswith("empty_") for name in active_names)
