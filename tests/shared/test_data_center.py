from __future__ import annotations

from app.shared.data_center.service import DataCenter


def test_data_center_registers_literature_asset(tmp_path) -> None:
    center = DataCenter(tmp_path / "data_assets.json")
    asset = center.register_asset(
        project_id="meta-test",
        module="meta_analysis",
        data_type="literature_records",
        source_path="/tmp/sample.nbib",
        output_path="/tmp/records.json",
    )
    records = center.list_assets("meta-test")
    assert records == [asset]
    assert records[0].status == "available"
