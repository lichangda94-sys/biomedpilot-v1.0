from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence, TypeVar

from labtools.local_data.locking import write_lock
from labtools.local_data.migration import ensure_supported_store_schema
from labtools.local_data.models import (
    CellProfileRecord,
    FreezeBatchRecord,
    FreezeVialRecord,
    LabToolsAuditLogEntry,
    LabToolsDataStoreManifest,
    LabToolsLocalDataError,
    LabToolsRecordIndexEntry,
    ReagentRecord,
    SampleRecord,
    utc_now,
)
from labtools.local_data.paths import LabToolsLocalDataPaths, resolve_labtools_local_data_paths
from labtools.local_data.schema_version import (
    LABTOOLS_AUDIT_LOG_SCHEMA_VERSION,
    LABTOOLS_LOCAL_DATA_STORE_SCHEMA_VERSION,
    LABTOOLS_RECORD_INDEX_SCHEMA_VERSION,
)


T = TypeVar("T")


class LabToolsLocalDataVersionConflict(LabToolsLocalDataError):
    pass


class LabToolsLocalDataNotFound(LabToolsLocalDataError):
    pass


@dataclass(frozen=True)
class LocalStoreStatus:
    status: str
    message: str
    paths: LabToolsLocalDataPaths
    initialized: bool
    readable: bool
    writable: bool
    reagent_count: int = 0
    sample_count: int = 0
    cell_count: int = 0
    record_count: int = 0


@dataclass(frozen=True)
class LocalDataSnapshot:
    manifest: LabToolsDataStoreManifest
    reagents: tuple[ReagentRecord, ...]
    samples: tuple[SampleRecord, ...]
    cells: tuple[CellProfileRecord, ...]
    freeze_batches: tuple[FreezeBatchRecord, ...]
    freeze_vials: tuple[FreezeVialRecord, ...]
    records: tuple[LabToolsRecordIndexEntry, ...]
    audit_log: tuple[LabToolsAuditLogEntry, ...]


class LocalLabToolsDataStore:
    def __init__(self, root: str | Path | None = None) -> None:
        self.paths = resolve_labtools_local_data_paths(root)

    def initialize_store(self) -> LocalStoreStatus:
        self.paths.root.mkdir(parents=True, exist_ok=True)
        self.paths.backups.mkdir(parents=True, exist_ok=True)
        self.paths.exports.mkdir(parents=True, exist_ok=True)
        if not self.paths.data_store.exists():
            self._write_json(self.paths.data_store, self._empty_data_payload())
        if not self.paths.record_index.exists():
            self._write_json(self.paths.record_index, self._empty_record_index_payload())
        if not self.paths.audit_log.exists():
            self._write_json(self.paths.audit_log, self._empty_audit_log_payload())
        return self.get_store_status()

    def get_store_status(self) -> LocalStoreStatus:
        initialized = self.paths.data_store.exists() and self.paths.record_index.exists() and self.paths.audit_log.exists()
        if not initialized:
            return LocalStoreStatus(
                status="missing_store",
                message="LabTools local data store has not been initialized.",
                paths=self.paths,
                initialized=False,
                readable=False,
                writable=False,
            )
        try:
            snapshot = self.load_store()
        except LabToolsLocalDataError as exc:
            return LocalStoreStatus(
                status="blocked_invalid_store",
                message=str(exc),
                paths=self.paths,
                initialized=True,
                readable=False,
                writable=False,
            )
        return LocalStoreStatus(
            status="ready",
            message="LabTools local data store is ready.",
            paths=self.paths,
            initialized=True,
            readable=True,
            writable=True,
            reagent_count=len(snapshot.reagents),
            sample_count=len(snapshot.samples),
            cell_count=len(snapshot.cells),
            record_count=len(snapshot.records),
        )

    def validate_store(self) -> LocalDataSnapshot:
        return self.load_store()

    def load_store(self) -> LocalDataSnapshot:
        data_payload = self._read_json(self.paths.data_store, LABTOOLS_LOCAL_DATA_STORE_SCHEMA_VERSION)
        record_payload = self._read_json(self.paths.record_index, LABTOOLS_RECORD_INDEX_SCHEMA_VERSION)
        audit_payload = self._read_json(self.paths.audit_log, LABTOOLS_AUDIT_LOG_SCHEMA_VERSION)
        return LocalDataSnapshot(
            manifest=LabToolsDataStoreManifest.from_dict(data_payload.get("manifest") or {}),
            reagents=tuple(ReagentRecord.from_dict(item) for item in _list_payload(data_payload, "reagents")),
            samples=tuple(SampleRecord.from_dict(item) for item in _list_payload(data_payload, "samples")),
            cells=tuple(CellProfileRecord.from_dict(item) for item in _list_payload(data_payload, "cell_profiles")),
            freeze_batches=tuple(FreezeBatchRecord.from_dict(item) for item in _list_payload(data_payload, "freeze_batches")),
            freeze_vials=tuple(FreezeVialRecord.from_dict(item) for item in _list_payload(data_payload, "freeze_vials")),
            records=tuple(LabToolsRecordIndexEntry.from_dict(item) for item in _list_payload(record_payload, "records")),
            audit_log=tuple(LabToolsAuditLogEntry.from_dict(item) for item in _list_payload(audit_payload, "audit_log")),
        )

    def save_store(self, snapshot: LocalDataSnapshot) -> None:
        self.paths.root.mkdir(parents=True, exist_ok=True)
        self._write_json(self.paths.data_store, self._data_payload(snapshot))
        self._write_json(self.paths.record_index, self._record_index_payload(snapshot.records))
        self._write_json(self.paths.audit_log, self._audit_log_payload(snapshot.audit_log))

    def list_reagents(self, *, include_archived: bool = False) -> tuple[ReagentRecord, ...]:
        reagents = self.load_store().reagents
        return reagents if include_archived else tuple(item for item in reagents if item.status != "archived")

    def get_reagent(self, reagent_id: str) -> ReagentRecord:
        return _get_by_id(self.load_store().reagents, reagent_id, "reagent")

    def create_reagent(self, payload: Mapping[str, Any]) -> ReagentRecord:
        reagent = ReagentRecord.from_dict({"source_mode": "local", **dict(payload), "version": 1})
        return self._upsert_entity("reagent", reagent, "create", lambda snapshot: snapshot.reagents)

    def update_reagent(self, reagent_id: str, payload: Mapping[str, Any], *, expected_version: int) -> ReagentRecord:
        return self._update_entity("reagent", reagent_id, payload, expected_version, lambda snapshot: snapshot.reagents)

    def archive_reagent(self, reagent_id: str, *, expected_version: int) -> ReagentRecord:
        return self.update_reagent(reagent_id, {"status": "archived"}, expected_version=expected_version)

    def list_samples(self, *, include_archived: bool = False) -> tuple[SampleRecord, ...]:
        samples = self.load_store().samples
        return samples if include_archived else tuple(item for item in samples if item.status != "archived")

    def list_wb_compatible_samples(self) -> tuple[SampleRecord, ...]:
        return tuple(sample for sample in self.list_samples() if sample.sample_type in {"protein_lysate", "protein", "lysate"})

    def list_bca_compatible_samples(self) -> tuple[SampleRecord, ...]:
        return tuple(sample for sample in self.list_samples() if sample.sample_type in {"protein_lysate", "protein", "lysate", "unknown", ""})

    def get_sample(self, sample_id: str) -> SampleRecord:
        return _get_by_id(self.load_store().samples, sample_id, "sample")

    def create_sample(self, payload: Mapping[str, Any]) -> SampleRecord:
        sample = SampleRecord.from_dict({"source_mode": "local", **dict(payload), "version": 1})
        return self._upsert_entity("sample", sample, "create", lambda snapshot: snapshot.samples)

    def update_sample(self, sample_id: str, payload: Mapping[str, Any], *, expected_version: int) -> SampleRecord:
        return self._update_entity("sample", sample_id, payload, expected_version, lambda snapshot: snapshot.samples)

    def archive_sample(self, sample_id: str, *, expected_version: int) -> SampleRecord:
        return self.update_sample(sample_id, {"status": "archived"}, expected_version=expected_version)

    def list_cells(self, *, include_archived: bool = False) -> tuple[CellProfileRecord, ...]:
        cells = self.load_store().cells
        return cells if include_archived else tuple(item for item in cells if item.status != "archived")

    def get_cell(self, cell_id: str) -> CellProfileRecord:
        return _get_by_id(self.load_store().cells, cell_id, "cell")

    def create_cell(self, payload: Mapping[str, Any]) -> CellProfileRecord:
        cell = CellProfileRecord.from_dict({"source_mode": "local", **dict(payload), "version": 1})
        return self._upsert_entity("cell", cell, "create", lambda snapshot: snapshot.cells)

    def update_cell(self, cell_id: str, payload: Mapping[str, Any], *, expected_version: int) -> CellProfileRecord:
        return self._update_entity("cell", cell_id, payload, expected_version, lambda snapshot: snapshot.cells)

    def create_freeze_batch(self, payload: Mapping[str, Any]) -> FreezeBatchRecord:
        batch = FreezeBatchRecord.from_dict({"source_mode": "local", **dict(payload), "version": 1})
        return self._upsert_entity("freeze_batch", batch, "create", lambda snapshot: snapshot.freeze_batches)

    def list_freeze_batches(self, *, cell_id: str | None = None) -> tuple[FreezeBatchRecord, ...]:
        batches = self.load_store().freeze_batches
        if cell_id is None:
            return batches
        return tuple(batch for batch in batches if batch.cell_id == cell_id)

    def create_freeze_vial(self, payload: Mapping[str, Any]) -> FreezeVialRecord:
        vial = FreezeVialRecord.from_dict({"source_mode": "local", **dict(payload), "version": 1})
        return self._upsert_entity("freeze_vial", vial, "create", lambda snapshot: snapshot.freeze_vials)

    def update_freeze_vial_status(self, vial_id: str, status: str, *, expected_version: int) -> FreezeVialRecord:
        return self._update_entity("freeze_vial", vial_id, {"status": status}, expected_version, lambda snapshot: snapshot.freeze_vials)

    def list_freeze_vials(self, *, batch_id: str | None = None) -> tuple[FreezeVialRecord, ...]:
        vials = self.load_store().freeze_vials
        if batch_id is None:
            return vials
        return tuple(vial for vial in vials if vial.freeze_batch_id == batch_id)

    def create_record_index_entry(self, payload: Mapping[str, Any]) -> LabToolsRecordIndexEntry:
        record = LabToolsRecordIndexEntry.from_dict({"source_mode": "local", **dict(payload), "version": 1})
        return self._upsert_entity("record", record, "create", lambda snapshot: snapshot.records)

    def list_record_index(self, *, record_type: str | None = None) -> tuple[LabToolsRecordIndexEntry, ...]:
        records = self.load_store().records
        if record_type is None:
            return records
        return tuple(record for record in records if record.record_type == record_type)

    def get_record_index(self, record_id: str) -> LabToolsRecordIndexEntry:
        return _get_by_id(self.load_store().records, record_id, "record")

    def update_record_index_status(self, record_id: str, status: str, *, expected_version: int) -> LabToolsRecordIndexEntry:
        return self._update_entity("record", record_id, {"status": status}, expected_version, lambda snapshot: snapshot.records)

    def list_records_by_reagent(self, reagent_id: str) -> tuple[LabToolsRecordIndexEntry, ...]:
        return tuple(record for record in self.load_store().records if reagent_id in record.linked_reagents)

    def list_records_by_sample(self, sample_id: str) -> tuple[LabToolsRecordIndexEntry, ...]:
        return tuple(record for record in self.load_store().records if sample_id in record.linked_samples)

    def list_records_by_cell(self, cell_id: str) -> tuple[LabToolsRecordIndexEntry, ...]:
        return tuple(record for record in self.load_store().records if cell_id in record.linked_cells)

    def _upsert_entity(
        self,
        entity_type: str,
        entity: T,
        action: str,
        collection_getter: Callable[[LocalDataSnapshot], Sequence[T]],
    ) -> T:
        snapshot = self._ensure_snapshot()
        collection = tuple(collection_getter(snapshot))
        if any(getattr(item, "id") == getattr(entity, "id") for item in collection):
            raise LabToolsLocalDataError(f"{entity_type} id already exists: {getattr(entity, 'id')}")
        updated_collection = (*collection, entity)
        updated_snapshot = self._with_collection(snapshot, entity_type, updated_collection)
        updated_snapshot = self._append_audit(
            updated_snapshot,
            LabToolsAuditLogEntry(
                id="",
                entity_type=entity_type,
                entity_id=getattr(entity, "id"),
                action=action,
                before_version=None,
                after_version=getattr(entity, "version"),
                summary=f"{action} {entity_type}",
            ),
        )
        self.save_store(updated_snapshot)
        return entity

    def _update_entity(
        self,
        entity_type: str,
        entity_id: str,
        payload: Mapping[str, Any],
        expected_version: int,
        collection_getter: Callable[[LocalDataSnapshot], Sequence[T]],
    ) -> T:
        snapshot = self._ensure_snapshot()
        collection = list(collection_getter(snapshot))
        for index, existing in enumerate(collection):
            if getattr(existing, "id") != entity_id:
                continue
            if getattr(existing, "version") != expected_version:
                raise LabToolsLocalDataVersionConflict(
                    f"{entity_type} version conflict: expected {expected_version}, found {getattr(existing, 'version')}."
                )
            updated = existing.with_update(payload)  # type: ignore[attr-defined]
            collection[index] = updated
            updated_snapshot = self._with_collection(snapshot, entity_type, tuple(collection))
            action = "archive" if payload.get("status") == "archived" else "update"
            updated_snapshot = self._append_audit(
                updated_snapshot,
                LabToolsAuditLogEntry(
                    id="",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    action=action,
                    before_version=getattr(existing, "version"),
                    after_version=getattr(updated, "version"),
                    summary=f"{action} {entity_type}",
                ),
            )
            self.save_store(updated_snapshot)
            return updated
        raise LabToolsLocalDataNotFound(f"{entity_type} not found: {entity_id}")

    def _ensure_snapshot(self) -> LocalDataSnapshot:
        if not self.paths.data_store.exists():
            self.initialize_store()
        return self.load_store()

    def _append_audit(self, snapshot: LocalDataSnapshot, entry: LabToolsAuditLogEntry) -> LocalDataSnapshot:
        return LocalDataSnapshot(
            manifest=snapshot.manifest,
            reagents=snapshot.reagents,
            samples=snapshot.samples,
            cells=snapshot.cells,
            freeze_batches=snapshot.freeze_batches,
            freeze_vials=snapshot.freeze_vials,
            records=snapshot.records,
            audit_log=(*snapshot.audit_log, entry.normalized()),
        )

    def _with_collection(self, snapshot: LocalDataSnapshot, entity_type: str, collection: Sequence[Any]) -> LocalDataSnapshot:
        kwargs = {
            "manifest": snapshot.manifest,
            "reagents": snapshot.reagents,
            "samples": snapshot.samples,
            "cells": snapshot.cells,
            "freeze_batches": snapshot.freeze_batches,
            "freeze_vials": snapshot.freeze_vials,
            "records": snapshot.records,
            "audit_log": snapshot.audit_log,
        }
        field_by_entity = {
            "reagent": "reagents",
            "sample": "samples",
            "cell": "cells",
            "freeze_batch": "freeze_batches",
            "freeze_vial": "freeze_vials",
            "record": "records",
        }
        kwargs[field_by_entity[entity_type]] = tuple(collection)
        return LocalDataSnapshot(**kwargs)

    def _data_payload(self, snapshot: LocalDataSnapshot) -> dict[str, Any]:
        manifest = LabToolsDataStoreManifest(
            created_at=snapshot.manifest.created_at,
            updated_at=utc_now(),
            reagent_count=len(snapshot.reagents),
            sample_count=len(snapshot.samples),
            cell_count=len(snapshot.cells),
            record_count=len(snapshot.records),
        ).normalized()
        return {
            "schema_version": LABTOOLS_LOCAL_DATA_STORE_SCHEMA_VERSION,
            "updated_at": manifest.updated_at,
            "manifest": manifest.to_dict(),
            "reagents": [item.to_dict() for item in snapshot.reagents],
            "samples": [item.to_dict() for item in snapshot.samples],
            "cell_profiles": [item.to_dict() for item in snapshot.cells],
            "freeze_batches": [item.to_dict() for item in snapshot.freeze_batches],
            "freeze_vials": [item.to_dict() for item in snapshot.freeze_vials],
        }

    def _record_index_payload(self, records: Sequence[LabToolsRecordIndexEntry]) -> dict[str, Any]:
        return {
            "schema_version": LABTOOLS_RECORD_INDEX_SCHEMA_VERSION,
            "updated_at": utc_now(),
            "records": [item.to_dict() for item in records],
        }

    def _audit_log_payload(self, audit_log: Sequence[LabToolsAuditLogEntry]) -> dict[str, Any]:
        return {
            "schema_version": LABTOOLS_AUDIT_LOG_SCHEMA_VERSION,
            "updated_at": utc_now(),
            "audit_log": [item.to_dict() for item in audit_log],
        }

    def _empty_data_payload(self) -> dict[str, Any]:
        snapshot = LocalDataSnapshot(
            manifest=LabToolsDataStoreManifest().normalized(),
            reagents=(),
            samples=(),
            cells=(),
            freeze_batches=(),
            freeze_vials=(),
            records=(),
            audit_log=(),
        )
        return self._data_payload(snapshot)

    def _empty_record_index_payload(self) -> dict[str, Any]:
        return self._record_index_payload(())

    def _empty_audit_log_payload(self) -> dict[str, Any]:
        return self._audit_log_payload(())

    def _read_json(self, path: Path, expected_schema_version: str) -> dict[str, Any]:
        if not path.exists():
            raise LabToolsLocalDataError(f"Missing LabTools local data file: {path}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise LabToolsLocalDataError(f"LabTools local data file is not valid JSON: {path}") from exc
        except OSError as exc:
            raise LabToolsLocalDataError(f"Unable to read LabTools local data file: {path}") from exc
        if not isinstance(payload, dict):
            raise LabToolsLocalDataError(f"LabTools local data file must contain a JSON object: {path}")
        ensure_supported_store_schema(payload, expected_schema_version)
        return payload

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_name(f".{path.name}.tmp")
        with write_lock(path):
            tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            tmp_path.replace(path)


def _list_payload(payload: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise LabToolsLocalDataError(f"LabTools local data payload missing list: {key}")
    return value


def _get_by_id(collection: Sequence[T], entity_id: str, entity_type: str) -> T:
    for item in collection:
        if getattr(item, "id") == entity_id:
            return item
    raise LabToolsLocalDataNotFound(f"{entity_type} not found: {entity_id}")


def initialize_store(root: str | Path | None = None) -> LocalStoreStatus:
    return LocalLabToolsDataStore(root).initialize_store()


def get_store_status(root: str | Path | None = None) -> LocalStoreStatus:
    return LocalLabToolsDataStore(root).get_store_status()


def load_store(root: str | Path | None = None) -> LocalDataSnapshot:
    return LocalLabToolsDataStore(root).load_store()


def save_store(snapshot: LocalDataSnapshot, root: str | Path | None = None) -> None:
    LocalLabToolsDataStore(root).save_store(snapshot)


def validate_store(root: str | Path | None = None) -> LocalDataSnapshot:
    return LocalLabToolsDataStore(root).validate_store()
