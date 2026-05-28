from __future__ import annotations

from pathlib import Path

import pytest

from labtools.lan_server import (
    LAN_SERVER_DISABLED_REASON,
    LabToolsLanServerConfig,
    LabToolsLanServerSkeleton,
    build_lan_server_skeleton,
)


def test_lan_server_skeleton_reports_disabled_non_listening_status() -> None:
    server = build_lan_server_skeleton(LabToolsLanServerConfig(host="0.0.0.0", port=8787, enabled=True))

    status = server.status()

    assert status.status == "disabled_skeleton"
    assert status.data_source_mode == "future_lan"
    assert status.enabled is False
    assert status.network_enabled is False
    assert status.listening is False
    assert status.host == "0.0.0.0"
    assert status.port == 8787
    assert status.reason == LAN_SERVER_DISABLED_REASON
    assert status.adapter_status.status == "disabled_future_option"
    assert status.adapter_status.read_enabled is False
    assert status.adapter_status.write_enabled is False


def test_lan_server_skeleton_start_and_stop_do_not_enable_network() -> None:
    server = LabToolsLanServerSkeleton()

    started = server.start()
    stopped = server.stop()

    assert started.listening is False
    assert started.network_enabled is False
    assert stopped.listening is False
    assert stopped.network_enabled is False
    assert started.reason == "LAN server skeleton only; network listening not implemented."


def test_lan_server_config_normalizes_mode_and_rejects_invalid_port() -> None:
    config = LabToolsLanServerConfig(host="", port=0, data_source_mode="local", enabled=True).normalized()

    assert config.host == "127.0.0.1"
    assert config.port == 0
    assert config.data_source_mode == "future_lan"
    assert config.enabled is False
    with pytest.raises(ValueError):
        LabToolsLanServerConfig(port=70000).normalized()


def test_lan_server_skeleton_contains_no_network_listener_code() -> None:
    source = (Path("labtools") / "lan_server" / "skeleton.py").read_text(encoding="utf-8")

    assert "import socket" not in source
    assert "HTTPServer" not in source
    assert "serve_forever" not in source
    assert "listen(" not in source
    assert "bind(" not in source
    assert "FastAPI" not in source
