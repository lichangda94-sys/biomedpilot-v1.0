from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from labtools.local_data.models import CellProfileRecord, FreezeVialRecord, LabToolsRecordIndexEntry, ReagentRecord, SampleRecord
from labtools.local_data.store import LocalLabToolsDataStore, LocalStoreStatus


@dataclass(frozen=True)
class LabToolsDataSourceAdapterStatus:
    status: str
    data_source_mode: str
    read_enabled: bool
    write_enabled: bool
    history_enabled: bool
    export_enabled: bool
    reason: str = ""
    local_store_status: LocalStoreStatus | None = None


class LocalLabToolsDataSourceAdapter:
    data_source_mode = "local"

    def __init__(self, root: str | Path | None = None) -> None:
        self.store = LocalLabToolsDataStore(root)

    def status(self) -> LabToolsDataSourceAdapterStatus:
        store_status = self.store.get_store_status()
        return LabToolsDataSourceAdapterStatus(
            status="ready" if store_status.readable else "blocked",
            data_source_mode=self.data_source_mode,
            read_enabled=store_status.readable,
            write_enabled=store_status.writable,
            history_enabled=store_status.readable,
            export_enabled=store_status.writable,
            reason=store_status.message,
            local_store_status=store_status,
        )

    def initialize(self) -> LabToolsDataSourceAdapterStatus:
        self.store.initialize_store()
        return self.status()

    def list_reagents(self) -> tuple[ReagentRecord, ...]:
        return self.store.list_reagents()

    def list_samples(self) -> tuple[SampleRecord, ...]:
        return self.store.list_samples()

    def list_cells(self) -> tuple[CellProfileRecord, ...]:
        return self.store.list_cells()

    def list_freeze_vials(self) -> tuple[FreezeVialRecord, ...]:
        return self.store.list_freeze_vials()

    def list_records(self) -> tuple[LabToolsRecordIndexEntry, ...]:
        return self.store.list_record_index()

    def create_record_summary(self, payload: Mapping[str, object]) -> LabToolsRecordIndexEntry:
        return self.store.create_record_index_entry(payload)


class ReadOnlyLabToolsDataSourceAdapter(LocalLabToolsDataSourceAdapter):
    data_source_mode = "readonly"

    def status(self) -> LabToolsDataSourceAdapterStatus:
        store_status = self.store.get_store_status()
        return LabToolsDataSourceAdapterStatus(
            status="ready_readonly" if store_status.readable else "blocked",
            data_source_mode=self.data_source_mode,
            read_enabled=store_status.readable,
            write_enabled=False,
            history_enabled=store_status.readable,
            export_enabled=False,
            reason="Read-only adapter; local write actions are disabled.",
            local_store_status=store_status,
        )

    def create_record_summary(self, payload: Mapping[str, object]) -> LabToolsRecordIndexEntry:
        raise PermissionError("Read-only LabTools data source does not allow writes.")


@dataclass(frozen=True)
class FutureAdapterPlaceholder:
    data_source_mode: str

    def status(self) -> LabToolsDataSourceAdapterStatus:
        return LabToolsDataSourceAdapterStatus(
            status="disabled_future_option",
            data_source_mode=self.data_source_mode,
            read_enabled=False,
            write_enabled=False,
            history_enabled=False,
            export_enabled=False,
            reason="Future adapter only; LAN/cloud sync not implemented.",
        )


class FutureLanDataSourceAdapter(FutureAdapterPlaceholder):
    def __init__(self) -> None:
        super().__init__(data_source_mode="future_lan")


class FutureCloudDataSourceAdapter(FutureAdapterPlaceholder):
    def __init__(self) -> None:
        super().__init__(data_source_mode="future_cloud")
