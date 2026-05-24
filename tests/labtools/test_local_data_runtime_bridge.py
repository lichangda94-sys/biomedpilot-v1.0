from __future__ import annotations

from pathlib import Path

from app import labtools_runtime


def _seed_local_data(project_root: Path) -> None:
    labtools_runtime._ensure_labtools_importable()
    from labtools.local_data import LocalLabToolsDataStore

    store = LocalLabToolsDataStore(project_root / "project_storage" / "labtools")
    store.initialize_store()
    reagent = store.create_reagent(
        {
            "name": "Tris-HCl",
            "category": "buffer",
            "concentration": "1 M",
            "storage_location": "4C fridge / Box A",
        }
    )
    sample = store.create_sample(
        {
            "sample_name": "Tumor lysate",
            "sample_type": "protein_lysate",
            "concentration": "2.0",
            "concentration_unit": "mg/mL",
            "volume": "25",
            "volume_unit": "µL",
            "storage_location": "-80C / Rack 1",
        }
    )
    cell = store.create_cell({"cell_name": "TPC-1", "passage": 12, "species": "human"})
    batch = store.create_freeze_batch({"cell_id": cell.id, "batch_name": "TPC-1_P12", "vial_count": 1})
    store.create_freeze_vial({"freeze_batch_id": batch.id, "vial_label": "TPC-1 P12 #01", "location": "LN2 A1"})
    store.create_record_index_entry(
        {
            "record_type": "wb_loading",
            "title": "WB loading draft",
            "linked_reagents": [reagent.id],
            "linked_samples": [sample.id],
            "linked_cells": [cell.id],
        }
    )


def _load_store(project_root: Path):
    labtools_runtime._ensure_labtools_importable()
    from labtools.local_data import LocalLabToolsDataStore

    return LocalLabToolsDataStore(project_root / "project_storage" / "labtools")


def test_runtime_bridge_gracefully_blocks_missing_store(tmp_path: Path) -> None:
    status = labtools_runtime.get_labtools_local_data_status(tmp_path)
    model = labtools_runtime.get_labtools_local_data_read_model(tmp_path)

    assert status.status == "blocked"
    assert status.read_enabled is False
    assert "not been initialized" in status.reason
    assert model.reagents == ()
    assert not (tmp_path / "project_storage").exists()


def test_runtime_bridge_reads_initialized_local_data(tmp_path: Path) -> None:
    _seed_local_data(tmp_path)

    model = labtools_runtime.get_labtools_local_data_read_model(tmp_path)

    assert model.status.status == "ready"
    assert model.status.reagent_count == 1
    assert model.status.sample_count == 1
    assert model.status.cell_count == 1
    assert model.status.freeze_vial_count == 1
    assert model.status.record_count == 1
    assert model.reagents[0].name == "Tris-HCl"
    assert model.wb_samples[0].sample_name == "Tumor lysate"
    assert model.cells[0].cell_name == "TPC-1"
    assert model.freeze_vials[0].status == "available"
    assert model.records[0].record_type == "wb_loading"


def test_runtime_bridge_reports_corrupted_store_without_throwing(tmp_path: Path) -> None:
    local_root = tmp_path / "project_storage" / "labtools"
    local_root.mkdir(parents=True)
    (local_root / "labtools_data_store.json").write_text("{bad-json", encoding="utf-8")
    (local_root / "labtools_record_index.json").write_text('{"schema_version": "labtools_record_index.v1", "records": []}', encoding="utf-8")
    (local_root / "labtools_audit_log.json").write_text('{"schema_version": "labtools_audit_log.v1", "audit_log": []}', encoding="utf-8")

    model = labtools_runtime.get_labtools_local_data_read_model(tmp_path)

    assert model.status.status == "blocked"
    assert model.status.read_enabled is False
    assert "not valid JSON" in model.status.reason


def test_runtime_bridge_keeps_future_adapters_disabled(tmp_path: Path) -> None:
    lan = labtools_runtime.get_labtools_local_data_status(tmp_path, data_source_mode="future_lan")
    cloud = labtools_runtime.get_labtools_local_data_status(tmp_path, data_source_mode="future_cloud")

    assert lan.status == "disabled_future_option"
    assert cloud.status == "disabled_future_option"
    assert lan.read_enabled is False
    assert cloud.write_enabled is False
    assert "Future adapter only" in lan.reason


def test_runtime_bridge_creates_updates_and_archives_local_reagent(tmp_path: Path) -> None:
    created = labtools_runtime.create_local_reagent(
        tmp_path,
        {"name": "Tris-HCl", "category": "buffer", "concentration": "1 M", "storage_location": "4C fridge"},
    )
    updated = labtools_runtime.update_local_reagent(
        tmp_path,
        created.entity_id,
        {"name": "Tris-HCl", "category": "buffer", "concentration": "2 M", "storage_location": "4C fridge"},
        expected_version=1,
    )
    archived = labtools_runtime.archive_local_reagent(tmp_path, created.entity_id, expected_version=2)
    model = labtools_runtime.get_labtools_local_data_read_model(tmp_path)
    snapshot = _load_store(tmp_path).load_store()

    assert created.success is True
    assert created.new_version == 1
    assert updated.success is True
    assert updated.new_version == 2
    assert archived.success is True
    assert archived.new_version == 3
    assert model.reagents == ()
    assert snapshot.reagents[0].status == "archived"
    assert [entry.action for entry in snapshot.audit_log] == ["create", "update", "archive"]


def test_runtime_bridge_blocks_reagent_version_conflict(tmp_path: Path) -> None:
    created = labtools_runtime.create_local_reagent(tmp_path, {"name": "Tris-HCl"})

    conflict = labtools_runtime.update_local_reagent(tmp_path, created.entity_id, {"name": "Tris-HCl 2"}, expected_version=2)

    assert conflict.success is False
    assert conflict.status == "blocked_version_conflict"
    assert conflict.blocker == "version_conflict"
    assert _load_store(tmp_path).load_store().reagents[0].version == 1


def test_runtime_bridge_creates_updates_and_archives_local_sample(tmp_path: Path) -> None:
    created = labtools_runtime.create_local_sample(
        tmp_path,
        {
            "sample_name": "Tumor lysate",
            "sample_type": "protein_lysate",
            "concentration": "2.0",
            "concentration_unit": "mg/mL",
            "volume": "25",
            "volume_unit": "µL",
        },
    )
    updated = labtools_runtime.update_local_sample(
        tmp_path,
        created.entity_id,
        {"sample_name": "Tumor lysate", "sample_type": "protein_lysate", "concentration": "2.5"},
        expected_version=1,
    )
    archived = labtools_runtime.archive_local_sample(tmp_path, created.entity_id, expected_version=2)
    model = labtools_runtime.get_labtools_local_data_read_model(tmp_path)
    snapshot = _load_store(tmp_path).load_store()

    assert created.success is True
    assert created.new_version == 1
    assert updated.success is True
    assert updated.new_version == 2
    assert archived.success is True
    assert archived.new_version == 3
    assert model.samples == ()
    assert snapshot.samples[0].status == "archived"
    assert snapshot.samples[0].volume == "25"
    assert [(entry.entity_type, entry.action) for entry in snapshot.audit_log] == [
        ("sample", "create"),
        ("sample", "update"),
        ("sample", "archive"),
    ]


def test_runtime_bridge_blocks_sample_version_conflict(tmp_path: Path) -> None:
    created = labtools_runtime.create_local_sample(tmp_path, {"sample_name": "Tumor lysate"})

    conflict = labtools_runtime.update_local_sample(
        tmp_path,
        created.entity_id,
        {"sample_name": "Tumor lysate 2"},
        expected_version=2,
    )

    assert conflict.success is False
    assert conflict.status == "blocked_version_conflict"
    assert conflict.blocker == "version_conflict"
    assert _load_store(tmp_path).load_store().samples[0].version == 1


def test_wb_preview_uses_local_samples_without_inventory_deduction(tmp_path: Path) -> None:
    _seed_local_data(tmp_path)
    samples = labtools_runtime.list_local_wb_sample_summaries(tmp_path)
    before = _load_store(tmp_path).load_store().samples[0]

    result = labtools_runtime.calculate_wb_loading_preview(local_samples=samples)
    model = labtools_runtime.get_labtools_local_data_read_model(tmp_path)
    after = _load_store(tmp_path).load_store().samples[0]

    assert result.samples[0].sample_id == "Tumor lysate"
    assert "no sample volume deduction" in result.samples[0].note
    assert model.wb_samples[0].version == 1
    assert after.volume == before.volume == "25"
    assert after.status == before.status == "available"


def test_bca_sample_concentration_proposal_does_not_write_until_confirmed(tmp_path: Path) -> None:
    _seed_local_data(tmp_path)
    sample = labtools_runtime.list_local_sample_summaries(tmp_path)[0]

    proposal = labtools_runtime.create_sample_concentration_update_proposal(tmp_path, sample.sample_id, "2.5", "mg/mL")
    after_proposal = _load_store(tmp_path).load_store().samples[0]
    confirmed = labtools_runtime.confirm_sample_concentration_update(tmp_path, proposal)
    after_confirm = _load_store(tmp_path).load_store().samples[0]

    assert proposal.success is True
    assert proposal.status == "proposal_ready"
    assert after_proposal.concentration == "2.0"
    assert after_proposal.version == 1
    assert confirmed.success is True
    assert confirmed.new_version == 2
    assert after_confirm.concentration == "2.5"
    assert after_confirm.concentration_unit == "mg/mL"
    assert after_confirm.volume == "25"
