from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any, ClassVar, Mapping
from uuid import uuid4

from labtools.local_data.schema_version import LABTOOLS_LOCAL_DATA_SCHEMA_VERSION


SOURCE_MODES = frozenset({"local", "imported", "future_lan", "future_cloud"})
COMMON_STATUSES = frozenset({"available", "draft", "active", "archived", "used", "discarded", "revived", "inactive", "unknown"})
RECORD_TYPES = frozenset(
    {
        "reagent_preparation",
        "formula_solver",
        "quick_calculation",
        "wb_loading",
        "bca_od",
        "cell_passage",
        "cell_thawing",
        "cell_plating",
        "sds_page",
        "image_processing_boundary",
    }
)
AUDIT_ACTIONS = frozenset({"create", "update", "archive", "status_update", "restore", "import", "export"})


class LabToolsLocalDataError(ValueError):
    """Raised when local LabTools data cannot be validated or persisted."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def _as_str(value: Any) -> str:
    return str(value or "").strip()


def _as_str_list(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise LabToolsLocalDataError("linked fields must be lists.")
    return tuple(_as_str(item) for item in value if _as_str(item))


def _as_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    return int(value)


def _validate_common(*, entity_id: str, version: int, status: str, source_mode: str) -> None:
    if not entity_id:
        raise LabToolsLocalDataError("id is required.")
    if not isinstance(version, int) or version < 1:
        raise LabToolsLocalDataError("version must be a positive integer.")
    if status not in COMMON_STATUSES:
        raise LabToolsLocalDataError(f"Unsupported status: {status}.")
    if source_mode not in SOURCE_MODES:
        raise LabToolsLocalDataError(f"Unsupported source_mode: {source_mode}.")


@dataclass(frozen=True)
class TraceableRecord:
    id: str
    status: str = "available"
    version: int = 1
    source_mode: str = "local"
    created_at: str = ""
    updated_at: str = ""
    created_by: str = "local_user"
    updated_by: str = "local_user"

    ID_PREFIX: ClassVar[str] = "entity"

    def normalized(self) -> "TraceableRecord":
        now = utc_now()
        entity_id = self.id or new_id(self.ID_PREFIX)
        created_at = self.created_at or now
        updated_at = self.updated_at or created_at
        normalized = replace(self, id=entity_id, created_at=created_at, updated_at=updated_at)
        _validate_common(
            entity_id=normalized.id,
            version=normalized.version,
            status=normalized.status,
            source_mode=normalized.source_mode,
        )
        return normalized

    def with_update(self, fields: Mapping[str, Any], *, updated_by: str = "local_user") -> "TraceableRecord":
        blocked = {"id", "created_at", "created_by", "version"}
        clean_fields = {key: value for key, value in fields.items() if key not in blocked}
        updated = replace(self, **clean_fields, version=self.version + 1, updated_at=utc_now(), updated_by=updated_by)
        return updated.normalized()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "version": self.version,
            "source_mode": self.source_mode,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
        }


@dataclass(frozen=True)
class ReagentRecord(TraceableRecord):
    ID_PREFIX: ClassVar[str] = "reagent"

    name: str = ""
    category: str = ""
    concentration: str = ""
    unit: str = ""
    vendor: str = ""
    catalog_number: str = ""
    lot_number: str = ""
    storage_location: str = ""
    expiry_date: str = ""
    notes: str = ""

    def normalized(self) -> "ReagentRecord":
        normalized = super().normalized()
        if not normalized.name:
            raise LabToolsLocalDataError("reagent name is required.")
        return normalized  # type: ignore[return-value]

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload.update(
            {
                "name": self.name,
                "category": self.category,
                "concentration": self.concentration,
                "unit": self.unit,
                "vendor": self.vendor,
                "catalog_number": self.catalog_number,
                "lot_number": self.lot_number,
                "storage_location": self.storage_location,
                "expiry_date": self.expiry_date,
                "notes": self.notes,
            }
        )
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ReagentRecord":
        return cls(
            id=_as_str(payload.get("id")),
            name=_as_str(payload.get("name")),
            category=_as_str(payload.get("category")),
            concentration=_as_str(payload.get("concentration")),
            unit=_as_str(payload.get("unit")),
            vendor=_as_str(payload.get("vendor")),
            catalog_number=_as_str(payload.get("catalog_number")),
            lot_number=_as_str(payload.get("lot_number")),
            storage_location=_as_str(payload.get("storage_location")),
            expiry_date=_as_str(payload.get("expiry_date")),
            status=_as_str(payload.get("status")) or "available",
            notes=_as_str(payload.get("notes")),
            version=_as_int(payload.get("version"), 1),
            source_mode=_as_str(payload.get("source_mode")) or "local",
            created_at=_as_str(payload.get("created_at")),
            updated_at=_as_str(payload.get("updated_at")),
            created_by=_as_str(payload.get("created_by")) or "local_user",
            updated_by=_as_str(payload.get("updated_by")) or "local_user",
        ).normalized()


@dataclass(frozen=True)
class SampleRecord(TraceableRecord):
    ID_PREFIX: ClassVar[str] = "sample"

    sample_name: str = ""
    sample_type: str = ""
    linked_experiment: str = ""
    project: str = ""
    concentration: str = ""
    concentration_unit: str = ""
    volume: str = ""
    volume_unit: str = ""
    storage_location: str = ""
    notes: str = ""

    def normalized(self) -> "SampleRecord":
        normalized = super().normalized()
        if not normalized.sample_name:
            raise LabToolsLocalDataError("sample_name is required.")
        return normalized  # type: ignore[return-value]

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload.update(
            {
                "sample_name": self.sample_name,
                "sample_type": self.sample_type,
                "linked_experiment": self.linked_experiment,
                "project": self.project,
                "concentration": self.concentration,
                "concentration_unit": self.concentration_unit,
                "volume": self.volume,
                "volume_unit": self.volume_unit,
                "storage_location": self.storage_location,
                "notes": self.notes,
            }
        )
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SampleRecord":
        return cls(
            id=_as_str(payload.get("id")),
            sample_name=_as_str(payload.get("sample_name")),
            sample_type=_as_str(payload.get("sample_type")),
            linked_experiment=_as_str(payload.get("linked_experiment")),
            project=_as_str(payload.get("project")),
            concentration=_as_str(payload.get("concentration")),
            concentration_unit=_as_str(payload.get("concentration_unit")),
            volume=_as_str(payload.get("volume")),
            volume_unit=_as_str(payload.get("volume_unit")),
            storage_location=_as_str(payload.get("storage_location")),
            status=_as_str(payload.get("status")) or "available",
            notes=_as_str(payload.get("notes")),
            version=_as_int(payload.get("version"), 1),
            source_mode=_as_str(payload.get("source_mode")) or "local",
            created_at=_as_str(payload.get("created_at")),
            updated_at=_as_str(payload.get("updated_at")),
            created_by=_as_str(payload.get("created_by")) or "local_user",
            updated_by=_as_str(payload.get("updated_by")) or "local_user",
        ).normalized()


@dataclass(frozen=True)
class CellProfileRecord(TraceableRecord):
    ID_PREFIX: ClassVar[str] = "cell"

    cell_name: str = ""
    species: str = ""
    disease: str = ""
    source: str = ""
    passage: int = 0
    culture_medium: str = ""
    mycoplasma_status: str = "unknown"
    storage_status: str = "active"
    notes: str = ""

    def normalized(self) -> "CellProfileRecord":
        normalized = super().normalized()
        if not normalized.cell_name:
            raise LabToolsLocalDataError("cell_name is required.")
        if normalized.passage < 0:
            raise LabToolsLocalDataError("passage cannot be negative.")
        return normalized  # type: ignore[return-value]

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload.update(
            {
                "cell_name": self.cell_name,
                "species": self.species,
                "disease": self.disease,
                "source": self.source,
                "passage": self.passage,
                "culture_medium": self.culture_medium,
                "mycoplasma_status": self.mycoplasma_status,
                "storage_status": self.storage_status,
                "notes": self.notes,
            }
        )
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CellProfileRecord":
        return cls(
            id=_as_str(payload.get("id")),
            cell_name=_as_str(payload.get("cell_name")),
            species=_as_str(payload.get("species")),
            disease=_as_str(payload.get("disease")),
            source=_as_str(payload.get("source")),
            passage=_as_int(payload.get("passage"), 0),
            culture_medium=_as_str(payload.get("culture_medium")),
            mycoplasma_status=_as_str(payload.get("mycoplasma_status")) or "unknown",
            storage_status=_as_str(payload.get("storage_status")) or "active",
            status=_as_str(payload.get("status")) or "active",
            notes=_as_str(payload.get("notes")),
            version=_as_int(payload.get("version"), 1),
            source_mode=_as_str(payload.get("source_mode")) or "local",
            created_at=_as_str(payload.get("created_at")),
            updated_at=_as_str(payload.get("updated_at")),
            created_by=_as_str(payload.get("created_by")) or "local_user",
            updated_by=_as_str(payload.get("updated_by")) or "local_user",
        ).normalized()


@dataclass(frozen=True)
class FreezeBatchRecord(TraceableRecord):
    ID_PREFIX: ClassVar[str] = "freeze_batch"

    cell_id: str = ""
    batch_name: str = ""
    passage: int = 0
    freeze_date: str = ""
    vial_count: int = 0
    storage_location: str = ""

    def normalized(self) -> "FreezeBatchRecord":
        normalized = super().normalized()
        if not normalized.cell_id:
            raise LabToolsLocalDataError("cell_id is required.")
        if not normalized.batch_name:
            raise LabToolsLocalDataError("batch_name is required.")
        return normalized  # type: ignore[return-value]

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload.update(
            {
                "cell_id": self.cell_id,
                "batch_name": self.batch_name,
                "passage": self.passage,
                "freeze_date": self.freeze_date,
                "vial_count": self.vial_count,
                "storage_location": self.storage_location,
            }
        )
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "FreezeBatchRecord":
        return cls(
            id=_as_str(payload.get("id")),
            cell_id=_as_str(payload.get("cell_id")),
            batch_name=_as_str(payload.get("batch_name")),
            passage=_as_int(payload.get("passage"), 0),
            freeze_date=_as_str(payload.get("freeze_date")),
            vial_count=_as_int(payload.get("vial_count"), 0),
            storage_location=_as_str(payload.get("storage_location")),
            status=_as_str(payload.get("status")) or "available",
            version=_as_int(payload.get("version"), 1),
            source_mode=_as_str(payload.get("source_mode")) or "local",
            created_at=_as_str(payload.get("created_at")),
            updated_at=_as_str(payload.get("updated_at")),
            created_by=_as_str(payload.get("created_by")) or "local_user",
            updated_by=_as_str(payload.get("updated_by")) or "local_user",
        ).normalized()


@dataclass(frozen=True)
class FreezeVialRecord(TraceableRecord):
    ID_PREFIX: ClassVar[str] = "vial"

    freeze_batch_id: str = ""
    vial_label: str = ""
    location: str = ""

    def normalized(self) -> "FreezeVialRecord":
        normalized = super().normalized()
        if not normalized.freeze_batch_id:
            raise LabToolsLocalDataError("freeze_batch_id is required.")
        if not normalized.vial_label:
            raise LabToolsLocalDataError("vial_label is required.")
        return normalized  # type: ignore[return-value]

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload.update(
            {
                "freeze_batch_id": self.freeze_batch_id,
                "vial_label": self.vial_label,
                "location": self.location,
            }
        )
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "FreezeVialRecord":
        return cls(
            id=_as_str(payload.get("id")),
            freeze_batch_id=_as_str(payload.get("freeze_batch_id")),
            vial_label=_as_str(payload.get("vial_label")),
            location=_as_str(payload.get("location")),
            status=_as_str(payload.get("status")) or "available",
            version=_as_int(payload.get("version"), 1),
            source_mode=_as_str(payload.get("source_mode")) or "local",
            created_at=_as_str(payload.get("created_at")),
            updated_at=_as_str(payload.get("updated_at")),
            created_by=_as_str(payload.get("created_by")) or "local_user",
            updated_by=_as_str(payload.get("updated_by")) or "local_user",
        ).normalized()


@dataclass(frozen=True)
class LabToolsRecordIndexEntry(TraceableRecord):
    ID_PREFIX: ClassVar[str] = "record"

    record_type: str = ""
    title: str = ""
    linked_reagents: tuple[str, ...] = ()
    linked_samples: tuple[str, ...] = ()
    linked_cells: tuple[str, ...] = ()
    record_summary: str = ""
    artifact_refs: tuple[str, ...] = ()

    def normalized(self) -> "LabToolsRecordIndexEntry":
        normalized = super().normalized()
        if normalized.record_type not in RECORD_TYPES:
            raise LabToolsLocalDataError(f"Unsupported record_type: {normalized.record_type}.")
        if not normalized.title:
            raise LabToolsLocalDataError("record title is required.")
        return normalized  # type: ignore[return-value]

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload.update(
            {
                "record_type": self.record_type,
                "title": self.title,
                "linked_reagents": list(self.linked_reagents),
                "linked_samples": list(self.linked_samples),
                "linked_cells": list(self.linked_cells),
                "record_summary": self.record_summary,
                "artifact_refs": list(self.artifact_refs),
            }
        )
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LabToolsRecordIndexEntry":
        return cls(
            id=_as_str(payload.get("id")),
            record_type=_as_str(payload.get("record_type")),
            title=_as_str(payload.get("title")),
            linked_reagents=_as_str_list(payload.get("linked_reagents")),
            linked_samples=_as_str_list(payload.get("linked_samples")),
            linked_cells=_as_str_list(payload.get("linked_cells")),
            status=_as_str(payload.get("status")) or "draft",
            record_summary=_as_str(payload.get("record_summary")),
            artifact_refs=_as_str_list(payload.get("artifact_refs")),
            version=_as_int(payload.get("version"), 1),
            source_mode=_as_str(payload.get("source_mode")) or "local",
            created_at=_as_str(payload.get("created_at")),
            updated_at=_as_str(payload.get("updated_at")),
            created_by=_as_str(payload.get("created_by")) or "local_user",
            updated_by=_as_str(payload.get("updated_by")) or "local_user",
        ).normalized()


@dataclass(frozen=True)
class LabToolsAuditLogEntry:
    id: str
    entity_type: str
    entity_id: str
    action: str
    user_id: str = "local_user"
    timestamp: str = ""
    before_version: int | None = None
    after_version: int | None = None
    summary: str = ""
    source_mode: str = "local"

    def normalized(self) -> "LabToolsAuditLogEntry":
        if not self.id:
            normalized = replace(self, id=new_id("audit"))
        else:
            normalized = self
        if not normalized.entity_type or not normalized.entity_id:
            raise LabToolsLocalDataError("audit entity_type and entity_id are required.")
        if normalized.action not in AUDIT_ACTIONS:
            raise LabToolsLocalDataError(f"Unsupported audit action: {normalized.action}.")
        if normalized.source_mode not in SOURCE_MODES:
            raise LabToolsLocalDataError(f"Unsupported source_mode: {normalized.source_mode}.")
        if not normalized.timestamp:
            normalized = replace(normalized, timestamp=utc_now())
        return normalized

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action": self.action,
            "user_id": self.user_id,
            "timestamp": self.timestamp,
            "before_version": self.before_version,
            "after_version": self.after_version,
            "summary": self.summary,
            "source_mode": self.source_mode,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LabToolsAuditLogEntry":
        before_version = payload.get("before_version")
        after_version = payload.get("after_version")
        return cls(
            id=_as_str(payload.get("id")),
            entity_type=_as_str(payload.get("entity_type")),
            entity_id=_as_str(payload.get("entity_id")),
            action=_as_str(payload.get("action")),
            user_id=_as_str(payload.get("user_id")) or "local_user",
            timestamp=_as_str(payload.get("timestamp")),
            before_version=int(before_version) if before_version is not None else None,
            after_version=int(after_version) if after_version is not None else None,
            summary=_as_str(payload.get("summary")),
            source_mode=_as_str(payload.get("source_mode")) or "local",
        ).normalized()


@dataclass(frozen=True)
class LabToolsDataStoreManifest:
    schema_version: str = LABTOOLS_LOCAL_DATA_SCHEMA_VERSION
    created_at: str = ""
    updated_at: str = ""
    reagent_count: int = 0
    sample_count: int = 0
    cell_count: int = 0
    record_count: int = 0
    source_mode: str = "local"

    def normalized(self) -> "LabToolsDataStoreManifest":
        now = utc_now()
        normalized = replace(
            self,
            created_at=self.created_at or now,
            updated_at=self.updated_at or now,
        )
        if normalized.schema_version != LABTOOLS_LOCAL_DATA_SCHEMA_VERSION:
            raise LabToolsLocalDataError("local data contract schema_version mismatch.")
        if normalized.source_mode not in SOURCE_MODES:
            raise LabToolsLocalDataError(f"Unsupported source_mode: {normalized.source_mode}.")
        return normalized

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "reagent_count": self.reagent_count,
            "sample_count": self.sample_count,
            "cell_count": self.cell_count,
            "record_count": self.record_count,
            "source_mode": self.source_mode,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LabToolsDataStoreManifest":
        return cls(
            schema_version=_as_str(payload.get("schema_version")) or LABTOOLS_LOCAL_DATA_SCHEMA_VERSION,
            created_at=_as_str(payload.get("created_at")),
            updated_at=_as_str(payload.get("updated_at")),
            reagent_count=int(payload.get("reagent_count") or 0),
            sample_count=int(payload.get("sample_count") or 0),
            cell_count=int(payload.get("cell_count") or 0),
            record_count=int(payload.get("record_count") or 0),
            source_mode=_as_str(payload.get("source_mode")) or "local",
        ).normalized()
