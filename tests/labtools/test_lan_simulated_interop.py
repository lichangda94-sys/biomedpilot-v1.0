from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from labtools.lan_client import (
    LAN_CLIENT_READONLY_DISABLED_REASON,
    LabToolsLanReadonlyClientConfig,
    build_lan_readonly_client_adapter,
)
from labtools.lan_server import LabToolsLanHealthServerConfig, build_lan_health_server
from labtools.local_data.datasource_adapter import LocalLabToolsDataSourceAdapter


def _request_json(
    url: str,
    *,
    method: str = "GET",
    payload: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any]]:
    request = Request(url, data=payload, method=method)
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    try:
        with urlopen(request, timeout=5) as response:  # noqa: S310 - loopback simulation server.
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def _seed_store(root: Path) -> LocalLabToolsDataSourceAdapter:
    adapter = LocalLabToolsDataSourceAdapter(root)
    adapter.initialize()
    reagent = adapter.create_reagent(
        {
            "name": "Tris-HCl",
            "category": "buffer",
            "concentration": "1",
            "unit": "M",
            "volume": "100",
            "volume_unit": "mL",
        }
    )
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
    cell = adapter.store.create_cell({"cell_name": "TPC-1", "species": "human", "passage": 12})
    batch = adapter.store.create_freeze_batch({"cell_id": cell.id, "batch_name": "TPC-1_P12"})
    adapter.store.create_freeze_vial({"freeze_batch_id": batch.id, "vial_label": "TPC-1 P12 #01", "status": "available"})
    adapter.create_record_index_entry(
        {
            "record_type": "wb_loading",
            "title": "WB loading",
            "record_summary": "Read-only loading summary.",
            "linked_reagents": [reagent.id],
            "linked_samples": [sample.id],
            "linked_cells": [cell.id],
            "artifact_refs": ["summary-only"],
        }
    )
    return adapter


def test_simulated_lan_pairing_revoke_isolates_clients_and_keeps_readonly_side_effect_free(tmp_path: Path) -> None:
    store_adapter = _seed_store(tmp_path)
    before_snapshot = store_adapter.store.load_store()
    before_sample = before_snapshot.samples[0]
    before_reagent = before_snapshot.reagents[0]
    before_audit_count = len(before_snapshot.audit_log)

    config = LabToolsLanHealthServerConfig(
        host="127.0.0.1",
        port=0,
        health_only=False,
        local_data_root=tmp_path,
        auth_required=True,
        allow_unauthenticated_readonly=False,
    )

    with build_lan_health_server(config) as server:
        unauth_client = build_lan_readonly_client_adapter(LabToolsLanReadonlyClientConfig(server.url(""), timeout_seconds=1))
        blocked_status = unauth_client.status()
        blocked_samples = unauth_client.list_samples()

        pairing_a = server.create_pairing_session(client_label="bench-a")
        pairing_b = server.create_pairing_session(client_label="bench-b")
        claim_a = unauth_client.claim_pairing(pairing_code=pairing_a.pairing_code, client_label="bench-a")
        claim_b = unauth_client.claim_pairing(pairing_code=pairing_b.pairing_code, client_label="bench-b")

        client_a = build_lan_readonly_client_adapter(
            LabToolsLanReadonlyClientConfig(server.url(""), timeout_seconds=1, bearer_token=str(claim_a["token"]))
        )
        client_b = build_lan_readonly_client_adapter(
            LabToolsLanReadonlyClientConfig(server.url(""), timeout_seconds=1, bearer_token=str(claim_b["token"]))
        )
        model_a = client_a.read_model()
        model_b = client_b.read_model()
        wb_records = client_a.list_record_index("wb_loading")
        clients_before_revoke = server.list_paired_clients(include_revoked=False)

        with pytest.raises(PermissionError, match=LAN_CLIENT_READONLY_DISABLED_REASON):
            client_a.update_sample(model_a.samples[0]["id"], {"volume": "1"}, expected_version=int(model_a.samples[0]["version"]))
        with pytest.raises(PermissionError, match=LAN_CLIENT_READONLY_DISABLED_REASON):
            client_a.create_record_index_entry({"record_type": "wb_loading", "title": "Blocked"})

        revoked = server.revoke_paired_client(str(claim_a["token_id"]))
        client_a_after_revoke = client_a.status()
        samples_a_after_revoke = client_a.list_samples()
        samples_b_after_revoke = client_b.list_samples()
        revoked_read_code, revoked_read = _request_json(
            server.url("/samples"),
            headers={"Authorization": f"Bearer {claim_a['token']}"},
        )
        remote_revoke_code, remote_revoke = _request_json(server.url("/pairing/revoke"), method="POST", payload=b"{}")

        runtime_status = server.status()
        active_clients_after_revoke = server.list_paired_clients(include_revoked=False)

    after_snapshot = store_adapter.store.load_store()
    after_sample = after_snapshot.samples[0]
    after_reagent = after_snapshot.reagents[0]

    assert blocked_status.read_enabled is False
    assert blocked_status.status == "blocked_read_disabled"
    assert blocked_samples == ()

    assert claim_a["ok"] is True
    assert claim_a["role"] == "viewer"
    assert claim_b["ok"] is True
    assert claim_b["role"] == "viewer"
    assert {client.client_label for client in clients_before_revoke} == {"bench-a", "bench-b"}

    assert model_a.status.read_enabled is True
    assert model_a.counts == {
        "cells": 1,
        "freeze_vials": 1,
        "record_index": 1,
        "reagents": 1,
        "samples": 1,
    }
    assert model_a.samples[0]["concentration"] == "2.0"
    assert model_a.samples[0]["volume"] == "25"
    assert model_a.freeze_vials[0]["status"] == "available"
    assert model_b.samples[0]["sample_name"] == "Tumor lysate"
    assert len(wb_records) == 1
    assert wb_records[0]["linked_reagents"] == [before_reagent.id]
    assert wb_records[0]["linked_samples"] == [before_sample.id]

    assert revoked is True
    assert client_a_after_revoke.read_enabled is False
    assert client_a_after_revoke.status == "blocked_read_disabled"
    assert samples_a_after_revoke == ()
    assert len(samples_b_after_revoke) == 1
    assert revoked_read_code == 401
    assert revoked_read["status"] == "auth_revoked"
    assert remote_revoke_code == 405
    assert remote_revoke["status"] == "blocked_write_disabled"
    assert {client.client_label for client in active_clients_after_revoke} == {"bench-b"}

    assert runtime_status.sync_enabled is False
    assert runtime_status.auth_enabled is True
    assert not hasattr(client_b, "discover_servers")
    assert not hasattr(client_b, "sync")

    assert len(after_snapshot.audit_log) == before_audit_count
    assert after_sample.volume == before_sample.volume == "25"
    assert after_sample.status == before_sample.status == "available"
    assert after_reagent.concentration == before_reagent.concentration == "1"
    assert after_reagent.status == before_reagent.status == "available"
    assert after_reagent.version == before_reagent.version == 1


def test_simulated_lan_compatibility_mode_is_explicit_readonly_and_not_pairing_default(tmp_path: Path) -> None:
    store_adapter = _seed_store(tmp_path)
    before_snapshot = store_adapter.store.load_store()

    config = LabToolsLanHealthServerConfig(
        host="127.0.0.1",
        port=0,
        health_only=False,
        local_data_root=tmp_path,
        auth_required=False,
        allow_unauthenticated_readonly=True,
    )

    with build_lan_health_server(config) as server:
        client = build_lan_readonly_client_adapter(LabToolsLanReadonlyClientConfig(server.url(""), timeout_seconds=1))
        status = client.status()
        samples = client.list_samples()
        write_code, write_body = _request_json(server.url("/samples"), method="POST", payload=b"{}")
        runtime_status = server.status()

        with pytest.raises(RuntimeError, match="auth is required"):
            server.create_pairing_session(client_label="compat-client")

    after_snapshot = store_adapter.store.load_store()

    assert status.read_enabled is True
    assert status.status == "ready_readonly"
    assert samples[0]["sample_name"] == "Tumor lysate"
    assert write_code == 405
    assert write_body["status"] == "blocked_write_disabled"
    assert runtime_status.auth_enabled is False
    assert runtime_status.sync_enabled is False
    assert runtime_status.reason == "Loopback read-only summaries; writes, sync, auth, and public-network access are disabled."
    assert len(after_snapshot.audit_log) == len(before_snapshot.audit_log)
    assert after_snapshot.samples[0].volume == before_snapshot.samples[0].volume
