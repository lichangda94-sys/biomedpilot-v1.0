from __future__ import annotations

from pathlib import Path

import pytest

from labtools.local_data.datasource_adapter import (
    FutureCloudDataSourceAdapter,
    FutureLanDataSourceAdapter,
    LocalLabToolsDataSourceAdapter,
    ReadOnlyLabToolsDataSourceAdapter,
)


def test_local_datasource_adapter_reports_status_and_lists_entities(tmp_path: Path) -> None:
    adapter = LocalLabToolsDataSourceAdapter(tmp_path)
    status = adapter.initialize()
    adapter.store.create_reagent({"name": "Tris-HCl"})
    adapter.store.create_sample({"sample_name": "S1"})
    adapter.store.create_cell({"cell_name": "TPC-1"})
    batch = adapter.store.create_freeze_batch({"cell_id": adapter.list_cells()[0].id, "batch_name": "TPC-1_P12"})
    vial = adapter.store.create_freeze_vial({"freeze_batch_id": batch.id, "vial_label": "TPC-1 P12 #01"})
    record = adapter.create_record_summary({"record_type": "quick_calculation", "title": "Dilution"})

    assert status.data_source_mode == "local"
    assert status.write_enabled is True
    assert len(adapter.list_reagents()) == 1
    assert len(adapter.list_samples()) == 1
    assert len(adapter.list_cells()) == 1
    assert adapter.list_freeze_vials() == (vial,)
    assert adapter.list_records() == (record,)


def test_readonly_datasource_adapter_disables_writes(tmp_path: Path) -> None:
    local = LocalLabToolsDataSourceAdapter(tmp_path)
    local.initialize()
    local.store.create_reagent({"name": "Tris-HCl"})

    readonly = ReadOnlyLabToolsDataSourceAdapter(tmp_path)
    status = readonly.status()

    assert status.data_source_mode == "readonly"
    assert status.read_enabled is True
    assert status.write_enabled is False
    assert len(readonly.list_reagents()) == 1
    with pytest.raises(PermissionError):
        readonly.create_record_summary({"record_type": "quick_calculation", "title": "Dilution"})


def test_future_datasource_placeholders_are_disabled() -> None:
    for adapter in (FutureLanDataSourceAdapter(), FutureCloudDataSourceAdapter()):
        status = adapter.status()
        assert status.status == "disabled_future_option"
        assert status.read_enabled is False
        assert status.write_enabled is False
        assert status.reason == "Future adapter only; LAN/cloud sync not implemented."
