from __future__ import annotations

import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from labtools.lan_server import (
    LAN_API_SCHEMA_VERSION,
    LOOPBACK_HEALTH_RUNTIME_MODE,
    LabToolsLanHealthServerConfig,
    build_lan_health_server,
)


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

    config = LabToolsLanHealthServerConfig(host="localhost", port=0, data_source_mode="local", health_only=False).normalized()

    assert config.host == "127.0.0.1"
    assert config.port == 0
    assert config.data_source_mode == "future_lan"
    assert config.health_only is True


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
