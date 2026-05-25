from __future__ import annotations

from pathlib import Path

import pytest

from labtools.lan_client import (
    LAN_CLIENT_DISABLED_REASON,
    LabToolsLanClientConfig,
    LabToolsLanClientDataSourceAdapter,
    build_lan_client_adapter_skeleton,
)


def test_lan_client_adapter_skeleton_reports_disabled_status() -> None:
    adapter = build_lan_client_adapter_skeleton(LabToolsLanClientConfig(server_label="bench-a", workspace_id="lab-1", enabled=True))

    client_status = adapter.client_status()
    adapter_status = adapter.status()

    assert client_status.status == "disabled_skeleton"
    assert client_status.data_source_mode == "future_lan"
    assert client_status.enabled is False
    assert client_status.network_enabled is False
    assert client_status.connected is False
    assert client_status.server_label == "bench-a"
    assert client_status.workspace_id == "lab-1"
    assert client_status.reason == LAN_CLIENT_DISABLED_REASON
    assert adapter_status.status == "disabled_future_option"
    assert adapter_status.read_enabled is False
    assert adapter_status.write_enabled is False


def test_lan_client_adapter_skeleton_reads_empty_and_blocks_writes() -> None:
    adapter = LabToolsLanClientDataSourceAdapter()

    assert adapter.list_reagents() == ()
    assert adapter.list_samples() == ()
    assert adapter.list_cells() == ()
    assert adapter.list_freeze_vials() == ()
    assert adapter.list_record_index() == ()
    with pytest.raises(PermissionError, match="network I/O not implemented"):
        adapter.create_reagent({"name": "Blocked"})
    with pytest.raises(PermissionError, match="network I/O not implemented"):
        adapter.create_sample({"sample_name": "Blocked"})
    with pytest.raises(PermissionError, match="network I/O not implemented"):
        adapter.create_record_index_entry({"record_type": "quick_calculation", "title": "Blocked"})


def test_lan_client_config_normalizes_without_enabling_network() -> None:
    config = LabToolsLanClientConfig(server_label="", workspace_id=" lab ", data_source_mode="local", enabled=True).normalized()

    assert config.server_label == "future-lan-server"
    assert config.workspace_id == "lab"
    assert config.data_source_mode == "future_lan"
    assert config.enabled is False


def test_lan_client_adapter_skeleton_contains_no_network_client_code() -> None:
    source = (Path("labtools") / "lan_client" / "skeleton.py").read_text(encoding="utf-8")

    assert "import socket" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "httpx" not in source
    assert "aiohttp" not in source
    assert ".connect(" not in source
    assert ".request(" not in source
