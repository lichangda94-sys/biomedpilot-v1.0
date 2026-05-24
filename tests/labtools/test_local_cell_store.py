from __future__ import annotations

from pathlib import Path

import pytest

from labtools.local_data.store import LabToolsLocalDataVersionConflict, LocalLabToolsDataStore


def test_cell_store_cell_batch_vial_status_and_audit(tmp_path: Path) -> None:
    store = LocalLabToolsDataStore(tmp_path)
    store.initialize_store()

    cell = store.create_cell({"cell_name": "TPC-1", "passage": 12})
    updated_cell = store.update_cell(cell.id, {"passage": 13}, expected_version=1)
    batch = store.create_freeze_batch({"cell_id": cell.id, "batch_name": "TPC-1_P13", "passage": 13, "vial_count": 1})
    vial = store.create_freeze_vial({"freeze_batch_id": batch.id, "vial_label": "TPC-1 P13 #01"})
    revived = store.update_freeze_vial_status(vial.id, "revived", expected_version=1)

    assert updated_cell.passage == 13
    assert store.list_freeze_batches(cell_id=cell.id) == (batch,)
    assert store.list_freeze_vials(batch_id=batch.id) == (revived,)
    assert revived.status == "revived"
    assert [entry.entity_type for entry in store.load_store().audit_log] == [
        "cell",
        "cell",
        "freeze_batch",
        "freeze_vial",
        "freeze_vial",
    ]


def test_cell_store_blocks_vial_version_conflict(tmp_path: Path) -> None:
    store = LocalLabToolsDataStore(tmp_path)
    store.initialize_store()
    cell = store.create_cell({"cell_name": "TPC-1"})
    batch = store.create_freeze_batch({"cell_id": cell.id, "batch_name": "Batch 1"})
    vial = store.create_freeze_vial({"freeze_batch_id": batch.id, "vial_label": "Vial 1"})

    with pytest.raises(LabToolsLocalDataVersionConflict):
        store.update_freeze_vial_status(vial.id, "used", expected_version=2)
