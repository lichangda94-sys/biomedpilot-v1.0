from __future__ import annotations

from pathlib import Path

from app.bioinformatics.deg_engine import run_controlled_deg


def test_controlled_deg_backend_does_not_emit_p_values_when_dependencies_missing(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.tsv"
    matrix.write_text("gene\tcase1\tctrl1\nTP53\t10\t5\n", encoding="utf-8")

    bundle = run_controlled_deg(
        {
            "deg_ready_package_id": "ready",
            "source_input_package_id": "pkg",
            "matrix_asset": {"path": str(matrix)},
            "value_type": "count",
            "gene_mapping_status": {"status": "passed"},
            "blockers": [],
        },
        case_samples=["case1"],
        control_samples=["ctrl1"],
        dependency_snapshot={"status": "blocked", "blockers": ["missing_python_package:scipy"]},
    )

    assert bundle["status"] == "blocked"
    assert bundle["rows"] == []
    assert "deg_dependencies_missing_no_p_values_computed" in bundle["blockers"]
