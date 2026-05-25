from __future__ import annotations

import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from labtools.lan_server import (
    LAN_API_SCHEMA_VERSION,
    LAN_READONLY_RUNTIME_MODE,
    LOOPBACK_HEALTH_RUNTIME_MODE,
    LOOPBACK_READONLY_RUNTIME_MODE,
    LabToolsLanHealthServerConfig,
    build_lan_health_server,
)
from labtools.local_data.datasource_adapter import LocalLabToolsDataSourceAdapter


def _request_json(url: str, *, method: str = "GET", payload: bytes | None = None) -> tuple[int, dict[str, object]]:
    request = Request(url, data=payload, method=method)
    try:
        with urlopen(request, timeout=5) as response:  # noqa: S310 - loopback-only test server
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def test_lan_health_server_config_rejects_public_bind_hosts() -> None:
    with pytest.raises(ValueError, match="loopback"):
        LabToolsLanHealthServerConfig(host="0.0.0.0", port=8787).normalized()
    with pytest.raises(ValueError, match="private LAN"):
        LabToolsLanHealthServerConfig(host="8.8.8.8", port=8787, allow_lan_bind=True).normalized()

    config = LabToolsLanHealthServerConfig(host="localhost", port=0, data_source_mode="local", health_only=False).normalized()
    lan_config = LabToolsLanHealthServerConfig(host="0.0.0.0", port=8787, health_only=False, allow_lan_bind=True).normalized()

    assert config.host == "127.0.0.1"
    assert config.port == 0
    assert config.data_source_mode == "future_lan"
    assert config.health_only is False
    assert lan_config.host == "0.0.0.0"
    assert lan_config.allow_lan_bind is True


def test_lan_readonly_server_status_reports_lan_bind_mode() -> None:
    server = build_lan_health_server(LabToolsLanHealthServerConfig(host="0.0.0.0", port=0, health_only=False, allow_lan_bind=True))

    status = server.status()

    assert status.lan_runtime_mode == LAN_READONLY_RUNTIME_MODE
    assert status.data_access_enabled is True
    assert status.auth_enabled is False
    assert "pairing" in status.reason


def test_lan_health_server_does_not_bind_until_started() -> None:
    server = build_lan_health_server(LabToolsLanHealthServerConfig(port=0))

    status = server.status()

    assert status.status == "created"
    assert status.listening is False
    assert status.network_enabled is False
    assert status.host == "127.0.0.1"
    assert status.port == 0


def test_lan_health_server_serves_health_and_status_without_data_access() -> None:
    with build_lan_health_server(LabToolsLanHealthServerConfig(host="127.0.0.1", port=0)) as server:
        runtime_status = server.status()

        assert runtime_status.status == "ready"
        assert runtime_status.listening is True
        assert runtime_status.network_enabled is True
        assert runtime_status.host == "127.0.0.1"
        assert runtime_status.port > 0
        assert runtime_status.data_access_enabled is False
        assert runtime_status.sync_enabled is False

        health_code, health = _request_json(server.url("/health"))
        status_code, status = _request_json(server.url("/status"))

    assert health_code == 200
    assert health["ok"] is True
    assert health["status"] == "ready"
    assert health["data_source_mode"] == "future_lan"
    assert health["schema_version"] == LAN_API_SCHEMA_VERSION
    assert health["data"] == {
        "auth_enabled": False,
        "data_access_enabled": False,
        "lan_runtime_mode": LOOPBACK_HEALTH_RUNTIME_MODE,
        "sync_enabled": False,
        "write_enabled": False,
    }

    assert status_code == 200
    assert status["ok"] is True
    assert status["status"] == "ready"
    assert status["data_source_mode"] == "future_lan"
    assert status["schema_version"] == LAN_API_SCHEMA_VERSION
    assert status["data"]["data_access_enabled"] is False
    assert status["data"]["sync_enabled"] is False
    assert status["data"]["write_enabled"] is False
    assert status["data"]["runtime"]["data_source_mode"] == "future_lan"
    assert status["data"]["runtime"]["listening"] is True


def test_lan_health_server_blocks_data_endpoints_and_writes() -> None:
    with build_lan_health_server() as server:
        read_code, read_body = _request_json(server.url("/reagents"))
        write_code, write_body = _request_json(server.url("/reagents"), method="POST", payload=b"{}")

    assert read_code == 404
    assert read_body["ok"] is False
    assert read_body["status"] == "disabled_or_not_implemented"
    assert read_body["data"] is None
    assert write_code == 405
    assert write_body["ok"] is False
    assert write_body["status"] == "blocked_write_disabled"
    assert write_body["data"] is None


def test_lan_health_server_does_not_create_or_mutate_local_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    with build_lan_health_server() as server:
        _request_json(server.url("/health"))
        _request_json(server.url("/status"))

    assert list(tmp_path.iterdir()) == []


def test_lan_health_runtime_does_not_import_local_data_store() -> None:
    source = (Path("labtools") / "lan_server" / "runtime.py").read_text(encoding="utf-8")

    assert "LocalLabToolsDataStore" not in source
    assert "labtools.local_data.store" not in source


def test_lan_readonly_summary_endpoints_block_missing_store_without_initializing(tmp_path: Path) -> None:
    with build_lan_health_server(LabToolsLanHealthServerConfig(health_only=False, local_data_root=tmp_path)) as server:
        status_code, status = _request_json(server.url("/status"))
        reagents_code, reagents = _request_json(server.url("/reagents"))

    assert status_code == 200
    assert status["data"]["lan_runtime_mode"] == LOOPBACK_READONLY_RUNTIME_MODE
    assert status["data"]["data_access_enabled"] is True
    assert status["data"]["adapter_status"]["status"] == "missing_store"
    assert status["data"]["adapter_status"]["read_enabled"] is False
    assert str(tmp_path) not in json.dumps(status)
    assert reagents_code == 503
    assert reagents["ok"] is False
    assert reagents["status"] == "blocked_store_missing"
    assert reagents["data"]["adapter_status"]["status"] == "missing_store"
    assert not any(tmp_path.iterdir())


def test_lan_readonly_summary_endpoints_list_initialized_store(tmp_path: Path) -> None:
    adapter = LocalLabToolsDataSourceAdapter(tmp_path)
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
    vial = adapter.store.create_freeze_vial({"freeze_batch_id": batch.id, "vial_label": "TPC-1 P12 #01"})
    record = adapter.create_record_index_entry(
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
    adapter.create_record_index_entry({"record_type": "quick_calculation", "title": "Dilution"})

    audit_count = len(adapter.store.load_store().audit_log)
    sample_volume = adapter.store.get_sample(sample.id).volume

    with build_lan_health_server(LabToolsLanHealthServerConfig(health_only=False, local_data_root=tmp_path)) as server:
        status_code, status = _request_json(server.url("/status"))
        reagents_code, reagents = _request_json(server.url("/reagents"))
        samples_code, samples = _request_json(server.url("/samples"))
        cells_code, cells = _request_json(server.url("/cells"))
        vials_code, vials = _request_json(server.url("/freeze-vials"))
        records_code, records = _request_json(server.url("/record-index?record_type=wb_loading"))
        summary_code, summary = _request_json(server.url("/records/summary"))
        write_code, write_body = _request_json(server.url("/samples"), method="POST", payload=b"{}")

    assert status_code == 200
    assert status["data"]["adapter_status"]["status"] == "ready"
    assert status["data"]["adapter_status"]["counts"] == {
        "cells": 1,
        "record_index": 2,
        "reagents": 1,
        "samples": 1,
    }
    assert str(tmp_path) not in json.dumps(status)

    assert reagents_code == 200
    assert reagents["status"] == "ready_readonly"
    assert reagents["data"][0]["id"] == reagent.id
    assert reagents["data"][0]["name"] == "Tris-HCl"
    assert "notes" not in reagents["data"][0]

    assert samples_code == 200
    assert samples["data"][0]["id"] == sample.id
    assert samples["data"][0]["sample_type"] == "protein_lysate"
    assert samples["data"][0]["concentration"] == "2.0"
    assert samples["data"][0]["volume"] == "25"

    assert cells_code == 200
    assert cells["data"][0]["id"] == cell.id
    assert cells["data"][0]["cell_name"] == "TPC-1"
    assert cells["data"][0]["passage"] == 12

    assert vials_code == 200
    assert vials["data"][0]["id"] == vial.id
    assert vials["data"][0]["vial_label"] == "TPC-1 P12 #01"

    assert records_code == 200
    assert len(records["data"]) == 1
    assert records["data"][0]["id"] == record.id
    assert records["data"][0]["record_type"] == "wb_loading"
    assert records["data"][0]["linked_reagents"] == [reagent.id]
    assert records["data"][0]["linked_samples"] == [sample.id]

    assert summary_code == 200
    assert summary["data"]["counts"] == {
        "cells": 1,
        "freeze_vials": 1,
        "record_index": 2,
        "reagents": 1,
        "samples": 1,
    }

    assert write_code == 405
    assert write_body["status"] == "blocked_write_disabled"
    assert len(adapter.store.load_store().audit_log) == audit_count
    assert adapter.store.get_sample(sample.id).volume == sample_volume


def test_lan_readonly_summary_endpoints_block_corrupted_store(tmp_path: Path) -> None:
    adapter = LocalLabToolsDataSourceAdapter(tmp_path)
    adapter.initialize()
    adapter.store.paths.data_store.write_text("{not valid json", encoding="utf-8")

    with build_lan_health_server(LabToolsLanHealthServerConfig(health_only=False, local_data_root=tmp_path)) as server:
        status_code, status = _request_json(server.url("/status"))
        samples_code, samples = _request_json(server.url("/samples"))

    assert status_code == 200
    assert status["data"]["adapter_status"]["status"] == "blocked_invalid_store"
    assert samples_code == 503
    assert samples["ok"] is False
    assert samples["status"] == "blocked_invalid_store"
    assert "not valid JSON" in samples["reason"]
    assert str(tmp_path) not in json.dumps(samples)
