from __future__ import annotations

import json
from pathlib import Path

from app import labtools_runtime


def _seed_lan_store(root: Path):
    labtools_runtime._ensure_labtools_importable()
    from labtools.local_data import LocalLabToolsDataSourceAdapter

    adapter = LocalLabToolsDataSourceAdapter(root)
    adapter.initialize()
    reagent = adapter.create_reagent({"name": "Tris-HCl", "concentration": "1", "unit": "M"})
    sample = adapter.create_sample(
        {
            "sample_name": "Tumor lysate",
            "sample_type": "protein_lysate",
            "concentration": "2.0",
            "concentration_unit": "mg/mL",
            "volume": "25",
            "volume_unit": "uL",
        }
    )
    cell = adapter.store.create_cell({"cell_name": "TPC-1", "passage": 12})
    batch = adapter.store.create_freeze_batch({"cell_id": cell.id, "batch_name": "TPC-1_P12"})
    adapter.store.create_freeze_vial({"freeze_batch_id": batch.id, "vial_label": "TPC-1 P12 #01"})
    adapter.create_record_index_entry(
        {
            "record_type": "wb_loading",
            "title": "WB loading",
            "record_summary": "Read-only loading summary.",
            "linked_reagents": [reagent.id],
            "linked_samples": [sample.id],
            "linked_cells": [cell.id],
        }
    )
    return adapter


def test_lan_runtime_bridge_requires_manual_connection() -> None:
    model = labtools_runtime.get_labtools_lan_read_model("")

    assert model.status.status == "manual_connection_required"
    assert model.status.data_source_mode == "future_lan"
    assert model.status.read_enabled is False
    assert model.status.write_enabled is False
    assert "不会自动发现" in model.status.reason
    assert "read-only server URL" in model.status.reason


def test_lan_runtime_bridge_reads_loopback_summaries_without_writes(tmp_path: Path) -> None:
    labtools_runtime._ensure_labtools_importable()
    from labtools.lan_server import LabToolsLanHealthServerConfig, build_lan_health_server

    adapter = _seed_lan_store(tmp_path)
    audit_count = len(adapter.store.load_store().audit_log)
    before_sample = adapter.store.load_store().samples[0]

    with build_lan_health_server(LabToolsLanHealthServerConfig(health_only=False, local_data_root=tmp_path)) as server:
        model = labtools_runtime.get_labtools_lan_read_model(server.url(""))

    after_sample = adapter.store.load_store().samples[0]

    assert model.status.status == "ready_readonly"
    assert model.status.data_source_mode == "future_lan"
    assert model.status.read_enabled is True
    assert model.status.write_enabled is False
    assert "pairing" in model.status.reason
    assert model.status.reagent_count == 1
    assert model.status.sample_count == 1
    assert model.status.cell_count == 1
    assert model.status.freeze_vial_count == 1
    assert model.status.record_count == 1
    assert model.reagents[0].name == "Tris-HCl"
    assert model.wb_samples[0].sample_name == "Tumor lysate"
    assert model.wb_samples[0].concentration == "2.0"
    assert model.cells[0].cell_name == "TPC-1"
    assert model.freeze_vials[0].vial_label == "TPC-1 P12 #01"
    assert model.records[0].record_type == "wb_loading"
    assert len(adapter.store.load_store().audit_log) == audit_count
    assert after_sample.volume == before_sample.volume == "25"


def test_lan_runtime_bridge_claims_pairing_and_uses_saved_token(tmp_path: Path, monkeypatch) -> None:
    labtools_runtime._ensure_labtools_importable()
    from labtools.lan_server import LabToolsLanHealthServerConfig, build_lan_health_server

    credentials_path = tmp_path / "settings" / "labtools_lan_credentials.json"
    monkeypatch.setenv("BIOMEDPILOT_LABTOOLS_LAN_CREDENTIALS_PATH", str(credentials_path))
    _seed_lan_store(tmp_path / "store")

    with build_lan_health_server(
        LabToolsLanHealthServerConfig(
            health_only=False,
            local_data_root=tmp_path / "store",
            auth_required=True,
            allow_unauthenticated_readonly=False,
        )
    ) as server:
        blocked = labtools_runtime.get_labtools_lan_read_model(server.url(""))
        pairing = server.create_pairing_session(client_label="UIShell test client")
        paired = labtools_runtime.claim_labtools_lan_pairing(server.url(""), pairing.pairing_code, client_label="UIShell test client")
        credential_status = labtools_runtime.get_labtools_lan_client_credential_status(server.url(""))
        model = labtools_runtime.get_labtools_lan_read_model(server.url(""))
        saved_payload = json.loads(credentials_path.read_text(encoding="utf-8"))
        revoked = server.revoke_paired_client(paired.credential.token_id if paired.credential else "")
        blocked_after_revoke = labtools_runtime.get_labtools_lan_read_model(server.url(""))
        failed_credential_status = labtools_runtime.get_labtools_lan_client_credential_status(server.url(""), read_model=blocked_after_revoke)
        cleared = labtools_runtime.clear_labtools_lan_credential(server.url(""))
        cleared_status = labtools_runtime.get_labtools_lan_client_credential_status(server.url(""))
    assert blocked.status.read_enabled is False
    assert blocked.status.status == "blocked_read_disabled"
    assert paired.success is True
    assert paired.status == "paired"
    assert paired.credential is not None
    assert paired.credential.role == "viewer"
    assert credential_status.has_saved_token is True
    assert credential_status.role == "viewer"
    assert credential_status.expires_at
    assert saved_payload["schema_version"] == labtools_runtime.LAN_CREDENTIAL_SCHEMA_VERSION
    assert saved_payload["credentials"][0]["server_url"].startswith("http://127.0.0.1:")
    assert saved_payload["credentials"][0]["token"]
    assert model.status.status == "ready_readonly"
    assert model.status.read_enabled is True
    assert model.wb_samples[0].concentration == "2.0"
    assert revoked is True
    assert blocked_after_revoke.status.read_enabled is False
    assert failed_credential_status.auth_failed is True
    assert failed_credential_status.status == "auth_failed_repair_required"
    assert cleared.success is True
    assert cleared.status == "cleared"
    assert cleared_status.has_saved_token is False


def test_lan_runtime_bridge_blocks_bad_pairing_without_credentials(tmp_path: Path, monkeypatch) -> None:
    labtools_runtime._ensure_labtools_importable()
    from labtools.lan_server import LabToolsLanHealthServerConfig, build_lan_health_server

    credentials_path = tmp_path / "settings" / "labtools_lan_credentials.json"
    monkeypatch.setenv("BIOMEDPILOT_LABTOOLS_LAN_CREDENTIALS_PATH", str(credentials_path))
    _seed_lan_store(tmp_path / "store")

    with build_lan_health_server(
        LabToolsLanHealthServerConfig(
            health_only=False,
            local_data_root=tmp_path / "store",
            auth_required=True,
            allow_unauthenticated_readonly=False,
        )
    ) as server:
        result = labtools_runtime.claim_labtools_lan_pairing(server.url(""), "00000000", client_label="UIShell test client")

    assert result.success is False
    assert result.status == "pairing_required"
    assert not credentials_path.exists()


def test_lan_runtime_bridge_host_management_creates_pairing_and_revokes_client(tmp_path: Path, monkeypatch) -> None:
    labtools_runtime._ensure_labtools_importable()

    credentials_path = tmp_path / "settings" / "labtools_lan_credentials.json"
    monkeypatch.setenv("BIOMEDPILOT_LABTOOLS_LAN_CREDENTIALS_PATH", str(credentials_path))
    store_root = tmp_path / "store"
    _seed_lan_store(store_root)
    try:
        started = labtools_runtime.start_labtools_lan_host(store_root, compatibility_mode=False)
        pairing = labtools_runtime.create_labtools_lan_host_pairing(store_root, client_label="UIShell test client")
        paired = labtools_runtime.claim_labtools_lan_pairing(
            started.host_status.server_url,
            pairing.pairing_code,
            client_label="UIShell test client",
        )
        model = labtools_runtime.get_labtools_lan_read_model(started.host_status.server_url)
        host_status = labtools_runtime.get_labtools_lan_host_status(store_root)
        revoked = labtools_runtime.revoke_labtools_lan_host_client(store_root, paired.credential.token_id if paired.credential else "")
        blocked = labtools_runtime.get_labtools_lan_read_model(started.host_status.server_url)
    finally:
        labtools_runtime.stop_labtools_lan_host(store_root)

    assert started.success is True
    assert started.host_status.server_mode == "auth_required"
    assert started.host_status.auth_required is True
    assert started.host_status.write_enabled is False
    assert started.host_status.sync_enabled is False
    assert pairing.success is True
    assert len(pairing.pairing_code) == 8
    assert paired.success is True
    assert paired.credential is not None
    assert model.status.read_enabled is True
    assert len(host_status.paired_clients) == 1
    assert host_status.paired_clients[0].state == "active"
    assert not hasattr(host_status.paired_clients[0], "token")
    assert not hasattr(host_status.paired_clients[0], "token_hash")
    assert revoked.success is True
    assert revoked.host_status.paired_clients[0].state == "revoked"
    assert blocked.status.read_enabled is False
    assert blocked.status.status == "blocked_read_disabled"


def test_lan_runtime_bridge_host_compatibility_mode_is_explicit_and_readonly(tmp_path: Path) -> None:
    store_root = tmp_path / "store"
    _seed_lan_store(store_root)
    try:
        started = labtools_runtime.start_labtools_lan_host(store_root, compatibility_mode=True)
        pairing = labtools_runtime.create_labtools_lan_host_pairing(store_root, client_label="UIShell test client")
        model = labtools_runtime.get_labtools_lan_read_model(started.host_status.server_url)
        credential_status = labtools_runtime.get_labtools_lan_client_credential_status(started.host_status.server_url, read_model=model)
    finally:
        labtools_runtime.stop_labtools_lan_host(store_root)

    assert started.success is True
    assert started.host_status.server_mode == "compatibility"
    assert started.host_status.auth_required is False
    assert started.host_status.compatibility_mode is True
    assert started.host_status.write_enabled is False
    assert started.host_status.sync_enabled is False
    assert pairing.success is False
    assert pairing.status == "compatibility_mode"
    assert model.status.read_enabled is True
    assert credential_status.compatibility_mode is True
    assert credential_status.has_saved_token is False


def test_lan_runtime_bridge_blocks_unavailable_server_gracefully() -> None:
    model = labtools_runtime.get_labtools_lan_read_model("http://127.0.0.1:1")

    assert model.status.status == "blocked_server_unavailable"
    assert model.status.read_enabled is False
    assert model.reagents == ()
