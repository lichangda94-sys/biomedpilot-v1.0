from __future__ import annotations

import csv
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtGui import QPixmap
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QFrame

    import app.shared.result_report_export_shell as shell
    from app.app_identity import RESULT_REPORT_EXPORT_ICON_PATHS, load_result_report_export_icon, load_result_report_export_pixmap
    from app.shared.result_report_export_shell import (
        empty_result_preview_state,
        make_export_buttons,
        make_result_report_export_adoption_panel,
    )
    from app.shared.semantic_keys import ExportKey, ReportStatusKey, ResultSemanticKey
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    QLabel = None  # type: ignore[assignment]
    QPushButton = None  # type: ignore[assignment]
    QFrame = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


ROOT = Path(__file__).resolve().parents[2]
PILOT_MANIFEST = ROOT / "docs/ui/UI_B8b7c_result_report_export_icon_active_pilot_manifest_20260521.csv"
ACTIVE_DIR = ROOT / "assets/icons/result_report_export"
ALLOWED_IDS = {"result_overview", "result_table", "result_summary", "report_template", "result_clear"}
BLOCKED_IDS = {
    "result_chart",
    "result_statistics",
    "report_generate",
    "export_result",
    "export_pdf",
    "export_excel",
    "export_csv",
    "export_archive",
    "share_result",
}


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def _read_manifest() -> list[dict[str, str]]:
    with PILOT_MANIFEST.open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_allowed_result_report_export_assets_exist_and_are_registered(qt_app) -> None:
    rows = _read_manifest()
    active = {row["resource_id"] for row in rows if row["active_pilot"] == "true"}

    assert active == ALLOWED_IDS
    assert set(RESULT_REPORT_EXPORT_ICON_PATHS) == ALLOWED_IDS
    for resource_id in ALLOWED_IDS:
        path = RESULT_REPORT_EXPORT_ICON_PATHS[resource_id]
        assert path == ROOT / "assets/icons/result_report_export" / f"{resource_id}.svg"
        assert path.exists()
        assert not load_result_report_export_icon(resource_id).isNull()
        assert not load_result_report_export_pixmap(resource_id, 22).isNull()


def test_blocked_future_icons_are_not_active_assets_or_registered() -> None:
    assert ACTIVE_DIR.exists()
    active_names = {path.name for path in ACTIVE_DIR.glob("*")}

    for resource_id in BLOCKED_IDS:
        assert resource_id not in RESULT_REPORT_EXPORT_ICON_PATHS
        assert f"{resource_id}.svg" not in active_names
        assert f"{resource_id}_24.png" not in active_names
        assert load_result_report_export_icon(resource_id).isNull()

    assert not any(name.startswith("status_") for name in active_names)
    assert not any("app_icon" in name for name in active_names)


def test_result_report_export_loader_keeps_unknown_fallback() -> None:
    assert load_result_report_export_icon("unknown").isNull()
    assert load_result_report_export_icon("status_testing").isNull()
    assert load_result_report_export_icon("empty_result").isNull()
    assert load_result_report_export_icon("export_pdf").isNull()
    assert load_result_report_export_icon("app_icon_deferred").isNull()


def test_result_report_export_panel_renders_allowed_markers_without_gate_changes(qt_app) -> None:
    panel = make_result_report_export_adoption_panel(module="bioinformatics", formats=(ExportKey.MARKDOWN, ExportKey.HTML))
    markers = panel.findChildren(QFrame, "resultReportExportIconMarker")
    marker_keys = [marker.property("resultReportExportIconKey") for marker in markers]

    assert panel.property("resultSemanticKey") == ResultSemanticKey.TESTING_SUMMARY_ONLY.value
    assert panel.property("reportStatusKey") == ReportStatusKey.DRAFT.value
    assert panel.property("exportGate") == "disabled_empty_result"
    assert set(marker_keys) == ALLOWED_IDS
    assert all(key not in marker_keys for key in BLOCKED_IDS)

    for marker in markers:
        assert marker.property("resultSemanticKey") == ResultSemanticKey.TESTING_SUMMARY_ONLY.value
        assert marker.property("reportStatusKey") == ReportStatusKey.DRAFT.value
        assert marker.property("exportGate") == "disabled_empty_result"
        assert marker.property("formalActionEnabled") is False
        assert marker.property("reportReadyPackageAllowed") is False
        label = marker.findChild(QLabel, "resultReportExportMarkerLabel")
        icon = marker.findChild(QLabel, "resultReportExportMarkerIcon")
        assert label is not None and label.text()
        assert icon is not None
        assert icon.property("iconFallback") is False
        assert icon.pixmap() is not None and not icon.pixmap().isNull()


def test_marker_icon_fallback_preserves_labels_and_export_button_gates(qt_app, monkeypatch) -> None:
    monkeypatch.setattr(shell, "load_result_report_export_pixmap", lambda _resource_id, _size=24: QPixmap())
    panel = shell.make_result_report_export_adoption_panel(module="bioinformatics", formats=(ExportKey.MARKDOWN, ExportKey.HTML))
    markers = panel.findChildren(QFrame, "resultReportExportIconMarker")
    export_buttons = panel.findChildren(QPushButton, "exportGatedButton")

    assert {marker.property("resultReportExportIconKey") for marker in markers} == ALLOWED_IDS
    assert all(marker.findChild(QLabel, "resultReportExportMarkerLabel").text() for marker in markers)
    assert all(marker.findChild(QLabel, "resultReportExportMarkerIcon").property("iconFallback") is True for marker in markers)
    assert all(not button.isEnabled() for button in export_buttons)
    assert all(button.property("exportGate") == "disabled_empty_result" for button in export_buttons)
    assert all(button.property("resultSemanticKey") == ResultSemanticKey.TESTING_SUMMARY_ONLY.value for button in export_buttons)
    assert all(button.property("reportStatusKey") == ReportStatusKey.DRAFT.value for button in export_buttons)


def test_export_buttons_do_not_receive_blocked_export_icons(qt_app) -> None:
    buttons = make_export_buttons(empty_result_preview_state(), (ExportKey.MARKDOWN, ExportKey.DOCX, ExportKey.CSV))

    assert all(button.icon().isNull() for button in buttons)
    assert all(not button.isEnabled() for button in buttons)
    assert all(button.property("exportGate") == "disabled_empty_result" for button in buttons)
    assert all(button.property("formalActionEnabled") is False for button in buttons)
    assert all(button.property("reportReadyPackageAllowed") is False for button in buttons)


def test_active_pilot_manifest_preserves_blocked_and_future_status() -> None:
    rows = _read_manifest()
    by_id = {row["resource_id"]: row for row in rows}

    assert len(rows) == 14
    for resource_id in ALLOWED_IDS:
        assert by_id[resource_id]["active_pilot"] == "true"
        assert by_id[resource_id]["replacement_state"] == "pilot_only"
        assert by_id[resource_id]["must_preserve_gate"] == "true"
        assert by_id[resource_id]["active_asset_path"].startswith("assets/icons/result_report_export/")

    assert by_id["result_chart"]["replacement_state"] == "disabled_affordance_only"
    assert by_id["result_statistics"]["replacement_state"] == "disabled_affordance_only"
    assert by_id["export_archive"]["replacement_state"] == "future_only"
    assert by_id["share_result"]["replacement_state"] == "future_only"
    for resource_id in BLOCKED_IDS:
        assert by_id[resource_id]["active_pilot"] == "false"
        assert by_id[resource_id]["active_asset_path"] == ""
        assert by_id[resource_id]["blocked_or_future_reason"]


def test_no_fake_chart_statistics_report_ready_or_app_icon_assets_enter_pilot() -> None:
    active_names = {path.name for path in ACTIVE_DIR.glob("*")}

    assert "result_chart.svg" not in active_names
    assert "result_statistics.svg" not in active_names
    assert "report_generate.svg" not in active_names
    assert "export_pdf.svg" not in active_names
    assert "export_excel.svg" not in active_names
    assert "export_csv.svg" not in active_names
    assert "export_archive.svg" not in active_names
    assert "share_result.svg" not in active_names
    assert not any(name.startswith("status_") for name in active_names)
    assert not any("app_icon" in name for name in active_names)
