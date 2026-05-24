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


def test_wb_preview_uses_local_samples_without_inventory_deduction(tmp_path: Path) -> None:
    _seed_local_data(tmp_path)
    samples = labtools_runtime.list_local_wb_sample_summaries(tmp_path)

    result = labtools_runtime.calculate_wb_loading_preview(local_samples=samples)
    model = labtools_runtime.get_labtools_local_data_read_model(tmp_path)

    assert result.samples[0].sample_id == "Tumor lysate"
    assert "no sample volume deduction" in result.samples[0].note
    assert model.wb_samples[0].version == 1
