from __future__ import annotations

from pathlib import Path

import pytest

from labtools.local_data.store import LabToolsLocalDataVersionConflict, LocalLabToolsDataStore


def test_sample_store_update_concentration_archive_and_filters(tmp_path: Path) -> None:
    store = LocalLabToolsDataStore(tmp_path)
    store.initialize_store()

    sample = store.create_sample({"sample_name": "S1", "sample_type": "protein_lysate"})
    updated = store.update_sample(sample.id, {"concentration": "2.5", "concentration_unit": "mg/mL"}, expected_version=1)
    archived = store.archive_sample(sample.id, expected_version=2)

    assert updated.version == 2
    assert archived.status == "archived"
    assert store.list_wb_compatible_samples() == ()
    assert store.list_bca_compatible_samples() == ()
    assert [entry.entity_type for entry in store.load_store().audit_log] == ["sample", "sample", "sample"]


def test_sample_store_wb_and_bca_compatible_filters(tmp_path: Path) -> None:
    store = LocalLabToolsDataStore(tmp_path)
    store.initialize_store()
    protein = store.create_sample({"sample_name": "P1", "sample_type": "protein_lysate"})
    store.create_sample({"sample_name": "DNA1", "sample_type": "dna"})

    assert tuple(sample.id for sample in store.list_wb_compatible_samples()) == (protein.id,)
    assert tuple(sample.id for sample in store.list_bca_compatible_samples()) == (protein.id,)


def test_sample_store_blocks_version_conflict(tmp_path: Path) -> None:
    store = LocalLabToolsDataStore(tmp_path)
    store.initialize_store()
    sample = store.create_sample({"sample_name": "S1"})

    with pytest.raises(LabToolsLocalDataVersionConflict):
        store.update_sample(sample.id, {"volume": "10"}, expected_version=2)
