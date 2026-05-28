from __future__ import annotations

from pathlib import Path

from labtools.local_data.store import LocalLabToolsDataStore


def test_record_index_create_query_update_and_audit(tmp_path: Path) -> None:
    store = LocalLabToolsDataStore(tmp_path)
    store.initialize_store()
    reagent = store.create_reagent({"name": "Laemmli buffer"})
    sample = store.create_sample({"sample_name": "S1", "sample_type": "protein_lysate"})
    cell = store.create_cell({"cell_name": "TPC-1"})

    record = store.create_record_index_entry(
        {
            "record_type": "wb_loading",
            "title": "WB loading 2026-05-24",
            "linked_reagents": [reagent.id],
            "linked_samples": [sample.id],
            "linked_cells": [cell.id],
            "record_summary": "Draft WB loading calculation.",
        }
    )
    completed = store.update_record_index_status(record.id, "available", expected_version=1)

    assert store.list_record_index(record_type="wb_loading") == (completed,)
    assert store.list_records_by_reagent(reagent.id) == (completed,)
    assert store.list_records_by_sample(sample.id) == (completed,)
    assert store.list_records_by_cell(cell.id) == (completed,)
    assert store.load_store().audit_log[-1].entity_type == "record"
