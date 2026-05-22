from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtGui import QPixmap
    from PySide6.QtWidgets import QApplication

    import app.shared.ui_components.primitives as primitives
    from app.app_identity import STATUS_ICON_PATHS, load_status_icon, load_status_pixmap
    from app.shared.ui_components import make_status_chip
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    QPixmap = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


ROOT = Path(__file__).resolve().parents[2]
PILOT_MANIFEST = ROOT / "docs/ui/UI_B8b8c_status_icon_active_pilot_manifest_20260522.csv"
ACTIVE_STATUS_DIR = ROOT / "assets/icons/status"
EXPECTED = {
    "testing": ("status_testing", "feature.status.testing"),
    "planned": ("status_planned", "feature.status.planned"),
    "shell_only": ("status_shell_only", "feature.status.shell_only"),
    "developer_preview": ("status_developer_preview", "feature.status.developer_preview"),
    "blocked": ("status_blocked", "feature.status.blocked"),
    "available": ("status_available", "resource.status.available"),
    "not_configured": ("status_not_configured", "resource.status.not_configured"),
    "failed": ("status_failed", "resource.status.failed"),
    "preflight_only": ("status_preflight_only", "analysis.status.preflight_only"),
    "draft": ("status_draft", "report.status.draft"),
}


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication(sys.argv)


def _read_manifest() -> list[dict[str, str]]:
    with PILOT_MANIFEST.open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_status_active_assets_exist_and_are_registered(qt_app) -> None:
    expected_semantic_keys = {semantic_key for _resource_id, semantic_key in EXPECTED.values()}

    assert set(STATUS_ICON_PATHS) == expected_semantic_keys
    for _status_key, (resource_id, semantic_key) in EXPECTED.items():
        path = STATUS_ICON_PATHS[semantic_key]
        assert path == ROOT / "assets/icons/status" / f"{resource_id}.svg"
        assert path.exists()
        assert not load_status_icon(semantic_key).isNull()
        assert not load_status_pixmap(semantic_key, 14).isNull()


def test_status_loader_uses_semantic_keys_and_keeps_unknown_fallback() -> None:
    assert load_status_icon("feature.status.testing").isNull() is False
    assert load_status_icon("testing").isNull()
    assert load_status_icon("available").isNull()
    assert load_status_icon("result.semantic.formal_computed_result").isNull()
    assert load_status_icon("report.status.report_ready").isNull()
    assert load_status_icon("app_icon_deferred").isNull()


def test_active_status_asset_directory_contains_only_status_family() -> None:
    assert ACTIVE_STATUS_DIR.exists()
    active_files = list(ACTIVE_STATUS_DIR.glob("*"))
    active_stems = {path.stem.removesuffix("_24").removesuffix("_32").removesuffix("_48").removesuffix("_64") for path in active_files}

    assert active_stems == {resource_id for resource_id, _semantic_key in EXPECTED.values()}
    assert len(active_files) == 50
    assert not any(path.name.startswith(("result_", "report_", "export_", "share_", "empty_", "resource_")) for path in active_files)
    assert not any("app_icon" in path.name for path in active_files)


def test_status_chip_renders_icon_as_auxiliary_marker_without_losing_label(qt_app) -> None:
    for status_key, (_resource_id, semantic_key) in EXPECTED.items():
        chip = make_status_chip(status_key=status_key)
        label = chip.property("statusLabel")

        assert chip.objectName() == "uiStatusChip"
        assert chip.property("uiPrimitive") == "status_chip"
        assert chip.property("statusKey") == status_key
        assert chip.property("semanticKey") == semantic_key
        assert chip.property("statusIconSemanticKey") == semantic_key
        assert chip.property("statusIconRole") == "auxiliary_status_marker"
        assert chip.property("statusIconFallback") is False
        assert chip.property("statusIconActivePilot") is True
        assert str(chip.property("statusIconSource")).startswith(str(ROOT / "assets/icons/status"))
        assert label
        assert label in chip.text()
        assert chip.toolTip()


def test_status_chip_icon_fallback_preserves_text_label_tooltip_and_semantics(qt_app, monkeypatch) -> None:
    monkeypatch.setattr(primitives, "load_status_pixmap", lambda _semantic_key, _size=14: QPixmap())

    chip = primitives.make_status_chip("Developer Preview / 本地测试版", status_key="developer_preview")

    assert chip.text() == "Developer Preview / 本地测试版"
    assert chip.property("statusLabel") == "Developer Preview / 本地测试版"
    assert chip.property("statusKey") == "developer_preview"
    assert chip.property("semanticKey") == "feature.status.developer_preview"
    assert chip.property("statusIconFallback") is True
    assert chip.property("statusIconActivePilot") is False
    assert chip.toolTip()


def test_status_available_icon_is_limited_to_confirmed_resource_available_semantics(qt_app) -> None:
    available = make_status_chip(status_key="available")
    not_configured = make_status_chip(status_key="not_configured")

    assert available.property("semanticKey") == "resource.status.available"
    assert available.property("statusAvailableRequiresDetectedResource") is True
    assert available.property("statusIconSemanticKey") == "resource.status.available"
    assert "Detected resource available only" in available.toolTip()
    assert "install" in available.toolTip()
    assert not_configured.property("semanticKey") == "resource.status.not_configured"
    assert not_configured.property("statusAvailableRequiresDetectedResource") is False


def test_status_active_pilot_manifest_preserves_gating_boundaries() -> None:
    rows = _read_manifest()

    assert len(rows) == 10
    assert {row["resource_id"] for row in rows} == {resource_id for resource_id, _semantic_key in EXPECTED.values()}
    assert {row["resource_family"] for row in rows} == {"status"}
    assert all(row["active_pilot"] == "true" for row in rows)
    assert all(row["replacement_state"] == "pilot_only" for row in rows)
    assert all(row["replacement_ready"] == "pilot_only" for row in rows)
    assert all(row["must_preserve_label"] == "true" for row in rows)
    assert all(row["must_preserve_status_chip"] == "true" for row in rows)
    assert all(row["must_preserve_tooltip"] == "true" for row in rows)
    assert all(row["must_preserve_status_logic"] == "true" for row in rows)
    assert all(row["active_asset_path"].startswith("assets/icons/status/") for row in rows)
    assert all("formal_computed_result" not in row["semantic_key"] for row in rows)
    assert all("report_ready" not in row["semantic_key"] for row in rows)

    by_id = {row["resource_id"]: row for row in rows}
    assert by_id["status_available"]["active_usage_rule"] == "only_after_confirmed_resource_status_available"
