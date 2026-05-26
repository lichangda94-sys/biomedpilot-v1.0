from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QListWidget, QPushButton, QRadioButton

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
        token_status = window.findChild(QLabel, "labtoolsLanSavedTokenStatusText")
        clear_token = window.findChild(QPushButton, "labtoolsLanClearTokenButton")
        status = window.findChild(QLabel, "labtoolsLanStatusText")
        counts = window.findChild(QLabel, "labtoolsLanCountRow")
        note = window.findChild(QLabel, "labtoolsLanBoundaryNote")
        feedback = window.findChild(QPushButton, "labtoolsGenerateLanFeedbackButton")

        assert url_input is not None
        assert connect is not None
        assert pair_code is not None
        assert pair is not None
        assert token_status is not None
        assert clear_token is not None
        assert status is not None
        assert counts is not None
        assert note is not None
        assert feedback is not None
        assert status.property("status") == "manual_connection_required"
        assert "自动发现" in note.text()
        assert "私有 LAN URL" in note.text()
        assert token_status.property("hasSavedToken") is False
        assert feedback.text() == "生成 LAN 真实测试反馈报告"
        assert feedback.property("feedbackType") == "labtools_lan_real_world"
        assert feedback.property("networkRequestAllowed") is False

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
        assert status.property("compatibilityMode") is True
        assert token_status.property("compatibilityMode") is True
        assert "compatibility" in token_status.text()
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
        token_status = window.findChild(QLabel, "labtoolsLanSavedTokenStatusText")
        clear_token = window.findChild(QPushButton, "labtoolsLanClearTokenButton")
        status = window.findChild(QLabel, "labtoolsLanStatusText")
        counts = window.findChild(QLabel, "labtoolsLanCountRow")

        assert url_input is not None
        assert connect is not None
        assert pair_code is not None
        assert pair is not None
        assert token_status is not None
        assert clear_token is not None
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
            assert token_status.property("hasSavedToken") is True
            assert token_status.property("tokenRole") == "viewer"
            assert token_status.property("tokenExpiresAt")

        assert status.property("status") == "ready_readonly"
        assert counts.property("sampleCount") == 1
        assert counts.property("recordCount") == 1
        assert pair_code.text() == ""
        clear_token.click()
        qt_app.processEvents()
        assert token_status.property("hasSavedToken") is False
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_labtools_home_client_saved_token_failure_prompts_repairing(qt_app, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    labtools_runtime._ensure_labtools_importable()

    monkeypatch.setenv("BIOMEDPILOT_LABTOOLS_LAN_CREDENTIALS_PATH", str(tmp_path / "settings" / "lan_credentials.json"))
    store_root = tmp_path / "store"
    _seed_lan_store(store_root)
    window = MainWindow()
    window.set_labtools_project_root(store_root)
    window._welcome_page.enter_workspace()
    window.show_labtools()
    window._show_labtools_home()
    try:
        url_input = window.findChild(QLineEdit, "labtoolsLanServerUrlInput")
        pair_code = window.findChild(QLineEdit, "labtoolsLanPairingCodeInput")
        pair = window.findChild(QPushButton, "labtoolsLanPairButton")
        connect = window.findChild(QPushButton, "labtoolsLanConnectButton")
        token_status = window.findChild(QLabel, "labtoolsLanSavedTokenStatusText")
        status = window.findChild(QLabel, "labtoolsLanStatusText")

        assert url_input is not None
        assert pair_code is not None
        assert pair is not None
        assert connect is not None
        assert token_status is not None
        assert status is not None

        start = labtools_runtime.start_labtools_lan_host(store_root, compatibility_mode=False)
        pairing = labtools_runtime.create_labtools_lan_host_pairing(store_root, client_label="UIShell manual LAN client")
        url_input.setText(start.host_status.server_url)
        pair_code.setText(pairing.pairing_code)
        pair.click()
        qt_app.processEvents()
        assert token_status.property("hasSavedToken") is True

        credential = labtools_runtime.get_labtools_lan_credential(start.host_status.server_url)
        assert credential is not None
        revoked = labtools_runtime.revoke_labtools_lan_host_client(store_root, credential.token_id)
        assert revoked.success is True
        connect.click()
        qt_app.processEvents()

        assert status.property("authFailed") is True
        assert token_status.property("authFailed") is True
        assert "重新 pairing" in status.text()
        assert "重新 pairing" in token_status.text()
    finally:
        labtools_runtime.stop_labtools_lan_host(store_root)
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_labtools_home_host_management_creates_pairing_lists_and_revokes(qt_app, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    labtools_runtime._ensure_labtools_importable()

    monkeypatch.setenv("BIOMEDPILOT_LABTOOLS_LAN_CREDENTIALS_PATH", str(tmp_path / "settings" / "lan_credentials.json"))
    store_root = tmp_path / "store"
    _seed_lan_store(store_root)
    window = MainWindow()
    window.set_labtools_project_root(store_root)
    window._welcome_page.enter_workspace()
    window.show_labtools()
    window._show_labtools_home()
    try:
        panel = window.findChild(QLabel, "labtoolsLanHostModeText")
        auth_radio = window.findChild(QRadioButton, "labtoolsLanHostAuthRequiredRadio")
        compat_radio = window.findChild(QRadioButton, "labtoolsLanHostCompatibilityRadio")
        start = window.findChild(QPushButton, "labtoolsLanHostStartButton")
        create_pairing = window.findChild(QPushButton, "labtoolsLanHostCreatePairingButton")
        pairing_label = window.findChild(QLabel, "labtoolsLanHostPairingCodeText")
        clients = window.findChild(QListWidget, "labtoolsLanHostPairedClientList")
        refresh = window.findChild(QPushButton, "labtoolsLanHostRefreshButton")
        revoke = window.findChild(QPushButton, "labtoolsLanHostRevokeButton")
        note = window.findChild(QLabel, "labtoolsLanHostBoundaryNote")

        assert panel is not None
        assert auth_radio is not None
        assert compat_radio is not None
        assert start is not None
        assert create_pairing is not None
        assert pairing_label is not None
        assert clients is not None
        assert refresh is not None
        assert revoke is not None
        assert note is not None
        assert auth_radio.isChecked()
        assert "Compatibility read-only" in compat_radio.text()
        assert "不同步" in note.text()
        assert "不启用 LAN 写入" in note.text()

        start.click()
        qt_app.processEvents()
        assert panel.property("status") == "ready"
        assert panel.property("serverMode") == "auth_required"
        assert panel.property("authRequired") is True
        assert panel.property("writeEnabled") is False
        assert panel.property("syncEnabled") is False

        create_pairing.click()
        qt_app.processEvents()
        pairing_code = pairing_label.property("pairingCode")
        assert isinstance(pairing_code, str)
        assert len(pairing_code) == 8
        assert pairing_label.property("pairingActive") is True

        host_status = labtools_runtime.get_labtools_lan_host_status(store_root)
        paired = labtools_runtime.claim_labtools_lan_pairing(
            host_status.server_url,
            pairing_code,
            client_label="UIShell manual LAN client",
        )
        assert paired.success is True
        refresh.click()
        qt_app.processEvents()
        assert clients.count() == 1
        assert "active" in clients.item(0).text()
        assert "token" not in clients.item(0).text().lower()

        clients.setCurrentRow(0)
        revoke.click()
        qt_app.processEvents()
        assert clients.count() == 1
        assert "revoked" in clients.item(0).text()
    finally:
        labtools_runtime.stop_labtools_lan_host(store_root)
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_labtools_home_host_management_keeps_compatibility_mode_explicit(qt_app, tmp_path: Path) -> None:
    labtools_runtime._ensure_labtools_importable()

    store_root = tmp_path / "store"
    _seed_lan_store(store_root)
    window = MainWindow()
    window.set_labtools_project_root(store_root)
    window._welcome_page.enter_workspace()
    window.show_labtools()
    window._show_labtools_home()
    try:
        panel = window.findChild(QLabel, "labtoolsLanHostModeText")
        compat_radio = window.findChild(QRadioButton, "labtoolsLanHostCompatibilityRadio")
        start = window.findChild(QPushButton, "labtoolsLanHostStartButton")
        create_pairing = window.findChild(QPushButton, "labtoolsLanHostCreatePairingButton")
        pairing_label = window.findChild(QLabel, "labtoolsLanHostPairingCodeText")

        assert panel is not None
        assert compat_radio is not None
        assert start is not None
        assert create_pairing is not None
        assert pairing_label is not None
        compat_radio.setChecked(True)
        start.click()
        qt_app.processEvents()

        assert panel.property("serverMode") == "compatibility"
        assert panel.property("authRequired") is False
        assert panel.property("compatibilityMode") is True
        create_pairing.click()
        qt_app.processEvents()
        assert pairing_label.property("pairingActive") is False
    finally:
        labtools_runtime.stop_labtools_lan_host(store_root)
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_labtools_shell_does_not_import_lan_client_or_store_directly() -> None:
    source = Path("app/shell/main_window.py").read_text(encoding="utf-8")

    assert "labtools.lan_client" not in source
    assert "labtools.lan_server" not in source
    assert "LocalLabToolsDataStore" not in source
    assert "labtools.local_data" not in source
