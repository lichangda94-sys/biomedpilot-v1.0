from __future__ import annotations

from pathlib import Path

import pytest

from labtools.local_data.store import LabToolsLocalDataVersionConflict, LocalLabToolsDataStore


def test_reagent_store_create_update_archive_and_audit(tmp_path: Path) -> None:
    store = LocalLabToolsDataStore(tmp_path)
    store.initialize_store()

    reagent = store.create_reagent({"name": "Tris-HCl", "category": "buffer"})
    updated = store.update_reagent(reagent.id, {"storage_location": "4C fridge / Box A"}, expected_version=1)
    archived = store.archive_reagent(reagent.id, expected_version=2)

    assert updated.version == 2
    assert archived.version == 3
    assert archived.status == "archived"
    assert store.list_reagents() == ()
    assert store.list_reagents(include_archived=True)[0].id == reagent.id

    audit = store.load_store().audit_log
    assert [entry.action for entry in audit] == ["create", "update", "archive"]
    assert audit[-1].entity_id == reagent.id


def test_reagent_store_blocks_version_conflict(tmp_path: Path) -> None:
    store = LocalLabToolsDataStore(tmp_path)
    store.initialize_store()
    reagent = store.create_reagent({"name": "Tris-HCl"})

    with pytest.raises(LabToolsLocalDataVersionConflict):
        store.update_reagent(reagent.id, {"unit": "mL"}, expected_version=2)
