from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from labtools.lan_client import (
    LAN_CLIENT_READONLY_DISABLED_REASON,
    LabToolsLanReadonlyClientConfig,
    build_lan_readonly_client_adapter,
)
from labtools.lan_server import LabToolsLanHealthServerConfig, build_lan_health_server
from labtools.local_data.datasource_adapter import LocalLabToolsDataSourceAdapter


def _seed_store(root: Path) -> LocalLabToolsDataSourceAdapter:
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
    adapter.create_record_index_entry({"record_type": "quick_calculation", "title": "Dilution"})
    return adapter


def test_lan_readonly_client_config_rejects_non_loopback_urls() -> None:
    with pytest.raises(ValueError, match="private LAN"):
        LabToolsLanReadonlyClientConfig("http://8.8.8.8:8787").normalized()
    with pytest.raises(ValueError, match="http"):
        LabToolsLanReadonlyClientConfig("https://127.0.0.1:8787").normalized()
    with pytest.raises(ValueError, match="API path"):
        LabToolsLanReadonlyClientConfig("http://127.0.0.1:8787/reagents").normalized()

    config = LabToolsLanReadonlyClientConfig("http://localhost:8787/", timeout_seconds=1).normalized()
    lan_config = LabToolsLanReadonlyClientConfig("http://192.168.1.20:8787", timeout_seconds=1).normalized()

    assert config.server_url == "http://localhost:8787"
    assert config.data_source_mode == "future_lan"
    assert config.timeout_seconds == 1
    assert lan_config.server_url == "http://192.168.1.20:8787"


def test_lan_readonly_client_reads_summary_endpoints_without_mutating_store(tmp_path: Path) -> None:
    store_adapter = _seed_store(tmp_path)
    audit_count = len(store_adapter.store.load_store().audit_log)
    before_sample = store_adapter.store.load_store().samples[0]

    with build_lan_health_server(LabToolsLanHealthServerConfig(health_only=False, local_data_root=tmp_path)) as server:
        client = build_lan_readonly_client_adapter(LabToolsLanReadonlyClientConfig(server.url(""), timeout_seconds=1))
        status = client.status()
        connection = client.client_status()
        model = client.read_model()
        wb_records = client.list_record_index("wb_loading")
        with pytest.raises(PermissionError, match=LAN_CLIENT_READONLY_DISABLED_REASON):
            client.create_sample({"sample_name": "Blocked"})

    after_sample = store_adapter.store.load_store().samples[0]

    assert status.status == "ready_readonly"
    assert status.data_source_mode == "future_lan"
    assert status.read_enabled is True
    assert status.write_enabled is False
    assert connection.connected is True
    assert connection.network_enabled is True
    assert model.counts == {
        "cells": 1,
        "freeze_vials": 1,
        "record_index": 2,
        "reagents": 1,
        "samples": 1,
    }
    assert model.reagents[0]["name"] == "Tris-HCl"
    assert model.samples[0]["sample_type"] == "protein_lysate"
    assert model.samples[0]["concentration"] == "2.0"
    assert model.cells[0]["cell_name"] == "TPC-1"
    assert model.freeze_vials[0]["vial_label"] == "TPC-1 P12 #01"
    assert len(wb_records) == 1
    assert wb_records[0]["record_type"] == "wb_loading"
    assert len(store_adapter.store.load_store().audit_log) == audit_count
    assert after_sample.volume == before_sample.volume == "25"
    assert after_sample.status == before_sample.status == "available"


def test_lan_readonly_client_blocks_missing_store_gracefully(tmp_path: Path) -> None:
    with build_lan_health_server(LabToolsLanHealthServerConfig(health_only=False, local_data_root=tmp_path)) as server:
        client = build_lan_readonly_client_adapter(LabToolsLanReadonlyClientConfig(server.url(""), timeout_seconds=1))
        status = client.status()
        model = client.read_model()

    assert status.status == "blocked_store_missing"
    assert status.read_enabled is False
    assert "not been initialized" in status.reason
    assert model.reagents == ()
    assert not any(tmp_path.iterdir())


def test_lan_readonly_client_handles_unavailable_and_malformed_servers() -> None:
    unavailable = build_lan_readonly_client_adapter(LabToolsLanReadonlyClientConfig("http://127.0.0.1:1", timeout_seconds=0.1))

    unavailable_status = unavailable.status()

    assert unavailable_status.status == "blocked_server_unavailable"
    assert unavailable_status.read_enabled is False

    malformed_server = _MalformedJsonServer()
    try:
        malformed_server.start()
        client = build_lan_readonly_client_adapter(LabToolsLanReadonlyClientConfig(malformed_server.base_url, timeout_seconds=1))

        malformed_status = client.status()
    finally:
        malformed_server.stop()

    assert malformed_status.status == "blocked_invalid_response"
    assert malformed_status.read_enabled is False
    assert "malformed JSON" in malformed_status.reason


def test_lan_client_skeleton_remains_disabled_after_readonly_client_addition() -> None:
    from labtools.lan_client import build_lan_client_adapter_skeleton

    skeleton = build_lan_client_adapter_skeleton()

    assert skeleton.client_status().status == "disabled_skeleton"
    assert skeleton.status().read_enabled is False
    assert skeleton.list_reagents() == ()


class _MalformedJsonServer:
    def __init__(self) -> None:
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _MalformedJsonHandler)
        self._thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        host, port = self._server.server_address[:2]
        return f"http://{host}:{port}"

    def start(self) -> None:
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        if self._thread is not None:
            self._thread.join(timeout=5)
        self._server.server_close()


class _MalformedJsonHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        body = b"not-json"
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format: str, *_args: Any) -> None:
        return
