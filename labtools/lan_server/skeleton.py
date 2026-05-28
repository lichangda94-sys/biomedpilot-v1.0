from __future__ import annotations

from dataclasses import dataclass

from labtools.local_data import FutureLanDataSourceAdapter, LabToolsDataSourceAdapterStatus


LAN_SERVER_DISABLED_REASON = "LAN server skeleton only; network listening not implemented."


@dataclass(frozen=True)
class LabToolsLanServerConfig:
    host: str = "127.0.0.1"
    port: int = 0
    data_source_mode: str = "future_lan"
    enabled: bool = False

    def normalized(self) -> "LabToolsLanServerConfig":
        host = str(self.host or "127.0.0.1").strip()
        port = int(self.port)
        if port < 0 or port > 65535:
            raise ValueError("LAN server port must be between 0 and 65535.")
        return LabToolsLanServerConfig(
            host=host,
            port=port,
            data_source_mode="future_lan",
            enabled=False,
        )


@dataclass(frozen=True)
class LabToolsLanServerStatus:
    status: str
    data_source_mode: str
    enabled: bool
    network_enabled: bool
    listening: bool
    host: str
    port: int
    reason: str
    adapter_status: LabToolsDataSourceAdapterStatus


class LabToolsLanServerSkeleton:
    """Contract-only LAN server placeholder.

    This class intentionally does not bind a port, open a socket, run a loop,
    or synchronize LabTools data. It provides a stable status surface for later
    LAN adapter planning while keeping the current runtime local-first.
    """

    def __init__(self, config: LabToolsLanServerConfig | None = None) -> None:
        self.config = (config or LabToolsLanServerConfig()).normalized()
        self.adapter = FutureLanDataSourceAdapter()

    def status(self) -> LabToolsLanServerStatus:
        adapter_status = self.adapter.status()
        return LabToolsLanServerStatus(
            status="disabled_skeleton",
            data_source_mode=adapter_status.data_source_mode,
            enabled=False,
            network_enabled=False,
            listening=False,
            host=self.config.host,
            port=self.config.port,
            reason=LAN_SERVER_DISABLED_REASON,
            adapter_status=adapter_status,
        )

    def start(self) -> LabToolsLanServerStatus:
        return self.status()

    def stop(self) -> LabToolsLanServerStatus:
        return self.status()


def build_lan_server_skeleton(config: LabToolsLanServerConfig | None = None) -> LabToolsLanServerSkeleton:
    return LabToolsLanServerSkeleton(config)
