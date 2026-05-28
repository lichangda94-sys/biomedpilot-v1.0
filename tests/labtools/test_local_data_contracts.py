from __future__ import annotations

import pytest

from labtools.local_data.models import (
    CellProfileRecord,
    FreezeBatchRecord,
    FreezeVialRecord,
    LabToolsAuditLogEntry,
    LabToolsLocalDataError,
    LabToolsRecordIndexEntry,
    ReagentRecord,
    SampleRecord,
)
from labtools.local_data.schema_version import LABTOOLS_LOCAL_DATA_SCHEMA_VERSION


def test_local_data_contract_defaults_and_json_roundtrip() -> None:
    reagent = ReagentRecord.from_dict({"name": "Tris-HCl", "category": "buffer"})
    assert reagent.id.startswith("reagent_")
    assert reagent.version == 1
    assert reagent.status == "available"
    assert reagent.source_mode == "local"
    assert reagent.created_by == "local_user"

    reloaded = ReagentRecord.from_dict(reagent.to_dict())
    assert reloaded == reagent


def test_local_data_contract_required_fields_and_enums() -> None:
    with pytest.raises(LabToolsLocalDataError):
        ReagentRecord.from_dict({"name": ""})

    with pytest.raises(LabToolsLocalDataError):
        SampleRecord.from_dict({"sample_name": "S1", "source_mode": "lan"})

    with pytest.raises(LabToolsLocalDataError):
        CellProfileRecord.from_dict({"cell_name": "TPC-1", "version": 0})


def test_all_core_contracts_roundtrip() -> None:
    cell = CellProfileRecord.from_dict({"cell_name": "TPC-1", "passage": 12})
    batch = FreezeBatchRecord.from_dict({"cell_id": cell.id, "batch_name": "TPC-1_P12", "passage": 12})
    vial = FreezeVialRecord.from_dict({"freeze_batch_id": batch.id, "vial_label": "TPC-1 P12 #01"})
    sample = SampleRecord.from_dict({"sample_name": "S1", "sample_type": "protein_lysate"})
    record = LabToolsRecordIndexEntry.from_dict(
        {
            "record_type": "wb_loading",
            "title": "WB loading",
            "linked_samples": [sample.id],
            "linked_cells": [cell.id],
        }
    )
    audit = LabToolsAuditLogEntry.from_dict(
        {
            "entity_type": "sample",
            "entity_id": sample.id,
            "action": "create",
            "after_version": 1,
            "summary": "Created sample record",
        }
    )

    assert FreezeBatchRecord.from_dict(batch.to_dict()) == batch
    assert FreezeVialRecord.from_dict(vial.to_dict()) == vial
    assert SampleRecord.from_dict(sample.to_dict()) == sample
    assert CellProfileRecord.from_dict(cell.to_dict()) == cell
    assert LabToolsRecordIndexEntry.from_dict(record.to_dict()) == record
    assert LabToolsAuditLogEntry.from_dict(audit.to_dict()) == audit


def test_schema_version_constant_is_explicit() -> None:
    assert LABTOOLS_LOCAL_DATA_SCHEMA_VERSION == "labtools_local_data_contract.v1"
