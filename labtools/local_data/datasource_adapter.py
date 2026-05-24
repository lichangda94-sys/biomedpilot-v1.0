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

    def create_reagent(self, payload: Mapping[str, object]) -> ReagentRecord:
        return self.store.create_reagent(payload)

    def update_reagent(self, reagent_id: str, payload: Mapping[str, object], *, expected_version: int) -> ReagentRecord:
        return self.store.update_reagent(reagent_id, payload, expected_version=expected_version)

    def archive_reagent(self, reagent_id: str, *, expected_version: int) -> ReagentRecord:
        return self.store.archive_reagent(reagent_id, expected_version=expected_version)

    def list_samples(self) -> tuple[SampleRecord, ...]:
        return self.store.list_samples()

    def create_sample(self, payload: Mapping[str, object]) -> SampleRecord:
        return self.store.create_sample(payload)

    def update_sample(self, sample_id: str, payload: Mapping[str, object], *, expected_version: int) -> SampleRecord:
        return self.store.update_sample(sample_id, payload, expected_version=expected_version)

    def archive_sample(self, sample_id: str, *, expected_version: int) -> SampleRecord:
        return self.store.archive_sample(sample_id, expected_version=expected_version)

    def list_cells(self) -> tuple[CellProfileRecord, ...]:
        return self.store.list_cells()

    def list_freeze_vials(self) -> tuple[FreezeVialRecord, ...]:
        return self.store.list_freeze_vials()

    def list_record_index(self, record_type: str | None = None) -> tuple[LabToolsRecordIndexEntry, ...]:
        return self.store.list_record_index(record_type=record_type)

    def list_records(self) -> tuple[LabToolsRecordIndexEntry, ...]:
        return self.list_record_index()

    def create_record_index_entry(self, payload: Mapping[str, object]) -> LabToolsRecordIndexEntry:
        return self.store.create_record_index_entry(payload)

    def create_record_summary(self, payload: Mapping[str, object]) -> LabToolsRecordIndexEntry:
        return self.create_record_index_entry(payload)

    def get_record_index(self, record_id: str) -> LabToolsRecordIndexEntry:
        return self.store.get_record_index(record_id)

    def update_record_index_status(self, record_id: str, status: str, *, expected_version: int) -> LabToolsRecordIndexEntry:
        return self.store.update_record_index_status(record_id, status, expected_version=expected_version)

    def list_records_by_reagent(self, reagent_id: str) -> tuple[LabToolsRecordIndexEntry, ...]:
        return self.store.list_records_by_reagent(reagent_id)

    def list_records_by_sample(self, sample_id: str) -> tuple[LabToolsRecordIndexEntry, ...]:
        return self.store.list_records_by_sample(sample_id)

    def list_records_by_cell(self, cell_id: str) -> tuple[LabToolsRecordIndexEntry, ...]:
        return self.store.list_records_by_cell(cell_id)


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

    def create_record_index_entry(self, payload: Mapping[str, object]) -> LabToolsRecordIndexEntry:
        raise PermissionError("Read-only LabTools data source does not allow writes.")

    def create_record_summary(self, payload: Mapping[str, object]) -> LabToolsRecordIndexEntry:
        raise PermissionError("Read-only LabTools data source does not allow writes.")

    def update_record_index_status(self, record_id: str, status: str, *, expected_version: int) -> LabToolsRecordIndexEntry:
        raise PermissionError("Read-only LabTools data source does not allow writes.")

    def create_reagent(self, payload: Mapping[str, object]) -> ReagentRecord:
        raise PermissionError("Read-only LabTools data source does not allow writes.")

    def update_reagent(self, reagent_id: str, payload: Mapping[str, object], *, expected_version: int) -> ReagentRecord:
        raise PermissionError("Read-only LabTools data source does not allow writes.")

    def archive_reagent(self, reagent_id: str, *, expected_version: int) -> ReagentRecord:
        raise PermissionError("Read-only LabTools data source does not allow writes.")

    def create_sample(self, payload: Mapping[str, object]) -> SampleRecord:
        raise PermissionError("Read-only LabTools data source does not allow writes.")

    def update_sample(self, sample_id: str, payload: Mapping[str, object], *, expected_version: int) -> SampleRecord:
        raise PermissionError("Read-only LabTools data source does not allow writes.")

    def archive_sample(self, sample_id: str, *, expected_version: int) -> SampleRecord:
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
