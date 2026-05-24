from __future__ import annotations

from typing import Mapping

from labtools.local_data.models import (
    CellProfileRecord,
    FreezeBatchRecord,
    FreezeVialRecord,
    LabToolsAuditLogEntry,
    LabToolsRecordIndexEntry,
    ReagentRecord,
    SampleRecord,
)


def validate_reagent(payload: Mapping[str, object]) -> ReagentRecord:
    return ReagentRecord.from_dict(payload)


def validate_sample(payload: Mapping[str, object]) -> SampleRecord:
    return SampleRecord.from_dict(payload)


def validate_cell_profile(payload: Mapping[str, object]) -> CellProfileRecord:
    return CellProfileRecord.from_dict(payload)


def validate_freeze_batch(payload: Mapping[str, object]) -> FreezeBatchRecord:
    return FreezeBatchRecord.from_dict(payload)


def validate_freeze_vial(payload: Mapping[str, object]) -> FreezeVialRecord:
    return FreezeVialRecord.from_dict(payload)


def validate_record_index_entry(payload: Mapping[str, object]) -> LabToolsRecordIndexEntry:
    return LabToolsRecordIndexEntry.from_dict(payload)


def validate_audit_log_entry(payload: Mapping[str, object]) -> LabToolsAuditLogEntry:
    return LabToolsAuditLogEntry.from_dict(payload)
