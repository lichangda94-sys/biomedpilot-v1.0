from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from labtools.local_data import FutureLanDataSourceAdapter, LabToolsDataSourceAdapterStatus
from labtools.local_data.models import CellProfileRecord, FreezeVialRecord, LabToolsRecordIndexEntry, ReagentRecord, SampleRecord


LAN_CLIENT_DISABLED_REASON = "LAN client adapter skeleton only; network I/O not implemented."


@dataclass(frozen=True)
class LabToolsLanClientConfig:
    server_label: str = "future-lan-server"
    workspace_id: str = ""
    data_source_mode: str = "future_lan"
    enabled: bool = False

    def normalized(self) -> "LabToolsLanClientConfig":
        return LabToolsLanClientConfig(
            server_label=str(self.server_label or "future-lan-server").strip(),
            workspace_id=str(self.workspace_id or "").strip(),
            data_source_mode="future_lan",
            enabled=False,
        )


@dataclass(frozen=True)
class LabToolsLanClientStatus:
    status: str
    data_source_mode: str
    enabled: bool
    network_enabled: bool
    connected: bool
    server_label: str
    workspace_id: str
    reason: str
    adapter_status: LabToolsDataSourceAdapterStatus


class LabToolsLanClientDataSourceAdapter:
    """Contract-only LAN client data source adapter placeholder.

    The class intentionally does not open network connections or translate
    payloads. It fixes the adapter-facing disabled status for the future LAN
    line while preserving the current local-first runtime.
    """

    data_source_mode = "future_lan"

    def __init__(self, config: LabToolsLanClientConfig | None = None) -> None:
        self.config = (config or LabToolsLanClientConfig()).normalized()
        self.placeholder_adapter = FutureLanDataSourceAdapter()

    def client_status(self) -> LabToolsLanClientStatus:
        adapter_status = self.placeholder_adapter.status()
        return LabToolsLanClientStatus(
            status="disabled_skeleton",
            data_source_mode=adapter_status.data_source_mode,
            enabled=False,
            network_enabled=False,
            connected=False,
            server_label=self.config.server_label,
            workspace_id=self.config.workspace_id,
            reason=LAN_CLIENT_DISABLED_REASON,
            adapter_status=adapter_status,
        )

    def status(self) -> LabToolsDataSourceAdapterStatus:
        return self.placeholder_adapter.status()

    def list_reagents(self) -> tuple[ReagentRecord, ...]:
        return ()

    def list_samples(self) -> tuple[SampleRecord, ...]:
        return ()

    def list_cells(self) -> tuple[CellProfileRecord, ...]:
        return ()

    def list_freeze_vials(self) -> tuple[FreezeVialRecord, ...]:
        return ()

    def list_record_index(self, record_type: str | None = None) -> tuple[LabToolsRecordIndexEntry, ...]:
        return ()

    def create_reagent(self, payload: Mapping[str, object]) -> ReagentRecord:
        raise PermissionError(LAN_CLIENT_DISABLED_REASON)

    def update_reagent(self, reagent_id: str, payload: Mapping[str, object], *, expected_version: int) -> ReagentRecord:
        raise PermissionError(LAN_CLIENT_DISABLED_REASON)

    def archive_reagent(self, reagent_id: str, *, expected_version: int) -> ReagentRecord:
        raise PermissionError(LAN_CLIENT_DISABLED_REASON)

    def create_sample(self, payload: Mapping[str, object]) -> SampleRecord:
        raise PermissionError(LAN_CLIENT_DISABLED_REASON)

    def update_sample(self, sample_id: str, payload: Mapping[str, object], *, expected_version: int) -> SampleRecord:
        raise PermissionError(LAN_CLIENT_DISABLED_REASON)

    def archive_sample(self, sample_id: str, *, expected_version: int) -> SampleRecord:
        raise PermissionError(LAN_CLIENT_DISABLED_REASON)

    def create_record_index_entry(self, payload: Mapping[str, object]) -> LabToolsRecordIndexEntry:
        raise PermissionError(LAN_CLIENT_DISABLED_REASON)

    def update_record_index_status(self, record_id: str, status: str, *, expected_version: int) -> LabToolsRecordIndexEntry:
        raise PermissionError(LAN_CLIENT_DISABLED_REASON)


def build_lan_client_adapter_skeleton(config: LabToolsLanClientConfig | None = None) -> LabToolsLanClientDataSourceAdapter:
    return LabToolsLanClientDataSourceAdapter(config)
