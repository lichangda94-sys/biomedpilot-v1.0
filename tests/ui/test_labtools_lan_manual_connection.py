from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton

    from app import labtools_runtime
    from app.shell.main_window import MainWindow
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    MainWindow = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    if not labtools_runtime.runtime_status().available:
        pytest.skip(labtools_runtime.runtime_status().message)
    return QApplication.instance() or QApplication([])


def _seed_lan_store(root: Path):
    labtools_runtime._ensure_labtools_importable()
    from labtools.local_data import LocalLabToolsDataSourceAdapter

    adapter = LocalLabToolsDataSourceAdapter(root)
    adapter.initialize()
    reagent = adapter.create_reagent({"name": "Tris-HCl"})
    sample = adapter.create_sample({"sample_name": "Tumor lysate", "sample_type": "protein_lysate", "concentration": "2.0"})
    cell = adapter.store.create_cell({"cell_name": "TPC-1"})
    batch = adapter.store.create_freeze_batch({"cell_id": cell.id, "batch_name": "TPC-1_P12"})
    adapter.store.create_freeze_vial({"freeze_batch_id": batch.id, "vial_label": "TPC-1 P12 #01"})
    adapter.create_record_index_entry(
        {
            "record_type": "wb_loading",
            "title": "WB loading",
            "linked_reagents": [reagent.id],
            "linked_samples": [sample.id],
            "linked_cells": [cell.id],
        }
    )
    return adapter


def test_labtools_home_manual_lan_connection_shows_readonly_counts(qt_app, tmp_path: Path) -> None:
    labtools_runtime._ensure_labtools_importable()
    from labtools.lan_server import LabToolsLanHealthServerConfig, build_lan_health_server

    _seed_lan_store(tmp_path)
    window = MainWindow()
    window._welcome_page.enter_workspace()
    window.show_labtools()
    window._show_labtools_home()
    try:
        url_input = window.findChild(QLineEdit, "labtoolsLanServerUrlInput")
        connect = window.findChild(QPushButton, "labtoolsLanConnectButton")
        pair_code = window.findChild(QLineEdit, "labtoolsLanPairingCodeInput")
        pair = window.findChild(QPushButton, "labtoolsLanPairButton")
        status = window.findChild(QLabel, "labtoolsLanStatusText")
        counts = window.findChild(QLabel, "labtoolsLanCountRow")
        note = window.findChild(QLabel, "labtoolsLanBoundaryNote")

        assert url_input is not None
        assert connect is not None
        assert pair_code is not None
        assert pair is not None
        assert status is not None
        assert counts is not None
        assert note is not None
        assert status.property("status") == "manual_connection_required"
        assert "自动发现" in note.text()
        assert "私有 LAN URL" in note.text()

        with build_lan_health_server(LabToolsLanHealthServerConfig(health_only=False, local_data_root=tmp_path)) as server:
            url_input.setText(server.url(""))
            connect.click()
            qt_app.processEvents()

        assert status.property("status") == "ready_readonly"
        assert status.property("dataSourceMode") == "future_lan"
        assert counts.property("reagentCount") == 1
        assert counts.property("sampleCount") == 1
        assert counts.property("cellCount") == 1
        assert counts.property("recordCount") == 1
        assert "不同步" in note.text()
        assert "不写入" in note.text()
        assert "paired viewer token" in note.text()
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_labtools_home_pairs_and_uses_saved_lan_token(qt_app, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    labtools_runtime._ensure_labtools_importable()
    from labtools.lan_server import LabToolsLanHealthServerConfig, build_lan_health_server

    monkeypatch.setenv("BIOMEDPILOT_LABTOOLS_LAN_CREDENTIALS_PATH", str(tmp_path / "settings" / "lan_credentials.json"))
    store_root = tmp_path / "store"
    _seed_lan_store(store_root)
    window = MainWindow()
    window._welcome_page.enter_workspace()
    window.show_labtools()
    window._show_labtools_home()
    try:
        url_input = window.findChild(QLineEdit, "labtoolsLanServerUrlInput")
        connect = window.findChild(QPushButton, "labtoolsLanConnectButton")
        pair_code = window.findChild(QLineEdit, "labtoolsLanPairingCodeInput")
        pair = window.findChild(QPushButton, "labtoolsLanPairButton")
        status = window.findChild(QLabel, "labtoolsLanStatusText")
        counts = window.findChild(QLabel, "labtoolsLanCountRow")

        assert url_input is not None
        assert connect is not None
        assert pair_code is not None
        assert pair is not None
        assert status is not None
        assert counts is not None

        with build_lan_health_server(
            LabToolsLanHealthServerConfig(
                health_only=False,
                local_data_root=store_root,
                auth_required=True,
                allow_unauthenticated_readonly=False,
            )
        ) as server:
            url_input.setText(server.url(""))
            connect.click()
            qt_app.processEvents()
            assert status.property("status") == "blocked_read_disabled"

            pairing = server.create_pairing_session(client_label="UIShell manual LAN client")
            pair_code.setText(pairing.pairing_code)
            pair.click()
            qt_app.processEvents()

        assert status.property("status") == "ready_readonly"
        assert counts.property("sampleCount") == 1
        assert counts.property("recordCount") == 1
        assert pair_code.text() == ""
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_labtools_shell_does_not_import_lan_client_or_store_directly() -> None:
    source = Path("app/shell/main_window.py").read_text(encoding="utf-8")

    assert "labtools.lan_client" not in source
    assert "LocalLabToolsDataStore" not in source
    assert "labtools.local_data" not in source
