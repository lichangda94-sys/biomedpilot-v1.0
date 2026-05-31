from __future__ import annotations

import pytest

from app.labtools.cell_experiments import (
    CellExperimentError,
    CellExperimentRecord,
    CellExperimentRecordStore,
    CellProfile,
    CellProfileStore,
    FreezingBatch,
    FreezingInventoryStore,
    calculate_seeding_preparation,
)


def _stores(tmp_path):
    profile_store = CellProfileStore(tmp_path / "cell_profiles.json")
    inventory_store = FreezingInventoryStore(tmp_path / "freezing_inventory.json")
    record_store = CellExperimentRecordStore(tmp_path / "cell_records.json", profile_store=profile_store, inventory_store=inventory_store)
    return profile_store, inventory_store, record_store


def test_cell_profile_serializes_saves_and_loads(tmp_path) -> None:
    profile_store, _, _ = _stores(tmp_path)
    profile = profile_store.save_profile(
        CellProfile(
            cell_name="A549",
            alias="lung model",
            current_passage="P8",
            basal_medium="DMEM",
            mycoplasma_status="阴性",
        )
    )

    loaded = profile_store.get(profile.cell_profile_id)

    assert loaded.cell_name == "A549"
    assert loaded.snapshot()["current_passage"] == "P8"
    assert loaded.snapshot()["culture_medium"] == "DMEM"
    assert profile_store.search("lung")[0].cell_profile_id == profile.cell_profile_id


def test_freezing_batch_generates_cryovials_and_updates_status(tmp_path) -> None:
    profile_store, inventory_store, _ = _stores(tmp_path)
    profile = profile_store.save_profile(CellProfile(cell_name="HeLa", current_passage="P12"))
    batch = FreezingBatch(cell_profile_id=profile.cell_profile_id, cell_name=profile.cell_name, batch_code="HL-001", passage="P12", cryovial_count=3)

    _, cryovials = inventory_store.save_batch_with_generated_cryovials(batch, liquid_nitrogen_tank="T1", rack="R2", box="B3", start_box_position="5")
    updated = inventory_store.mark_cryovial_status(cryovials[0].cryovial_id, "已转移")

    assert [vial.cryovial_code for vial in cryovials] == ["HL-001-01", "HL-001-02", "HL-001-03"]
    assert cryovials[0].location == "T1 / R2 / B3 / 5"
    assert updated.status == "已转移"
    assert len(inventory_store.list_cryovials(cell_profile_id=profile.cell_profile_id, query="P12")) == 3


def test_thaw_record_updates_selected_cryovial_to_thawed(tmp_path) -> None:
    profile_store, inventory_store, record_store = _stores(tmp_path)
    profile = profile_store.save_profile(CellProfile(cell_name="293T", current_passage="P4"))
    _, cryovials = inventory_store.save_batch_with_generated_cryovials(
        FreezingBatch(cell_profile_id=profile.cell_profile_id, cell_name=profile.cell_name, batch_code="293T-A", passage="P4", cryovial_count=1)
    )
    record = CellExperimentRecord(
        record_type="thaw",
        cell_profile_id=profile.cell_profile_id,
        cell_profile_snapshot=profile.snapshot(),
        experiment_name="293T thaw",
        fields={"cryovial_id": cryovials[0].cryovial_id, "passage_after_thaw": "P5"},
        operator="tester",
    )

    saved = record_store.save_record(record)
    vial = inventory_store.list_cryovials(cell_profile_id=profile.cell_profile_id)[0]

    assert vial.status == "已复苏"
    assert vial.thaw_record_id == saved.record_id
    assert inventory_store.list_available_cryovials(profile.cell_profile_id) == ()


def test_passage_record_can_update_profile_current_passage(tmp_path) -> None:
    profile_store, _, record_store = _stores(tmp_path)
    profile = profile_store.save_profile(CellProfile(cell_name="MCF7", current_passage="P2"))

    record_store.save_record(
        CellExperimentRecord(
            record_type="passage",
            cell_profile_id=profile.cell_profile_id,
            cell_profile_snapshot=profile.snapshot(),
            experiment_name="routine passage",
            fields={"passage_before": "P2", "passage_after": "P3"},
        )
    )

    assert profile_store.get(profile.cell_profile_id).current_passage == "P3"


def test_seeding_calculation_returns_volumes_and_warnings() -> None:
    result = calculate_seeding_preparation(1_000_000, "cells/mL", 10_000, 24, 0.5, 10)

    assert result.total_target_cells == pytest.approx(264_000)
    assert result.suggested_total_volume == pytest.approx(13.2)
    assert result.cell_suspension_volume == pytest.approx(0.264)
    assert result.medium_volume == pytest.approx(12.936)
    assert result.unit == "mL"

    warned = calculate_seeding_preparation(100, "cells/mL", 10_000, 2, 0.1)
    assert warned.warnings == ("当前细胞浓度不足，需要浓缩细胞悬液或调整接种条件。",)


def test_seeding_calculation_rejects_zero_density() -> None:
    with pytest.raises(CellExperimentError, match="当前细胞浓度不能为 0"):
        calculate_seeding_preparation(0, "cells/mL", 10_000, 24, 0.5)


def test_treatment_and_transfection_records_do_not_calculate_systems(tmp_path) -> None:
    profile_store, _, record_store = _stores(tmp_path)
    profile = profile_store.save_profile(CellProfile(cell_name="HUVEC"))

    treatment = record_store.save_record(
        CellExperimentRecord(
            record_type="treatment",
            cell_profile_id=profile.cell_profile_id,
            cell_profile_snapshot=profile.snapshot(),
            experiment_name="drug only record",
            fields={"working_concentration": "10 nM", "added_volume": "manual note"},
        )
    )
    transfection = record_store.save_record(
        CellExperimentRecord(
            record_type="transfection",
            cell_profile_id=profile.cell_profile_id,
            cell_profile_snapshot=profile.snapshot(),
            experiment_name="transfection only record",
            fields={"reagent_volume": "manual note"},
        )
    )

    assert "calculated" not in treatment.fields
    assert "calculated" not in transfection.fields


def test_from_last_record_and_text_export(tmp_path) -> None:
    profile_store, _, record_store = _stores(tmp_path)
    profile = profile_store.save_profile(CellProfile(cell_name="U2OS", current_passage="P10"))
    saved = record_store.save_record(
        CellExperimentRecord(
            record_type="seeding",
            cell_profile_id=profile.cell_profile_id,
            cell_profile_snapshot=profile.snapshot(),
            experiment_name="plate cells",
            fields={"well_count": "24"},
            free_text_sop="seed gently",
        )
    )

    copied = record_store.create_from_last("seeding")
    export_path = record_store.export_record_text(saved.record_id, tmp_path / "exports")

    assert copied is not None
    assert copied.record_id != saved.record_id
    assert copied.fields["well_count"] == "24"
    assert export_path.exists()
    assert "细胞档案快照" in export_path.read_text(encoding="utf-8")
