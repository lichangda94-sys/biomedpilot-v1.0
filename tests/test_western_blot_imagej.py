from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from labtools.western_blot import (
    get_protein_imagej_workflow,
    list_protein_imagej_workflows,
    render_protein_imagej_macro,
    write_protein_imagej_macro,
)


def test_protein_imagej_catalog_exposes_dot_blot_grid_workflow() -> None:
    workflow_ids = {spec.workflow_id for spec in list_protein_imagej_workflows()}

    assert workflow_ids == {"dot_blot_grid"}
    assert get_protein_imagej_workflow("dot_blot").workflow_id == "dot_blot_grid"
    assert get_protein_imagej_workflow("点杂交").workflow_id == "dot_blot_grid"


def test_dot_blot_grid_macro_is_software_driven_and_parameterized(tmp_path: Path) -> None:
    bundle = render_protein_imagej_macro(
        "dot_blot_grid",
        tmp_path / "images",
        tmp_path / "out",
        parameters={"rows": 2, "columns": 3, "spot_diameter_px": 18, "invert_image": False},
    )

    assert bundle.output_csv_path == tmp_path / "out" / "dot_blot_grid_results.csv"
    assert "getDirectory(" not in bundle.macro_text
    assert "image,row,column,spot_id,center_x_px,center_y_px,area_px,mean_gray,integrated_density" in bundle.macro_text
    assert "run(\"Specify...\", \"width=\" + spot_diameter_px" in bundle.macro_text
    assert "rows = 2;" in bundle.macro_text
    assert "columns = 3;" in bundle.macro_text
    assert "spot_diameter_px = 18;" in bundle.macro_text
    assert "invert_image = \"false\";" in bundle.macro_text


def test_write_protein_imagej_macro_creates_default_macro_path(tmp_path: Path) -> None:
    bundle = write_protein_imagej_macro("dot_blot_grid", tmp_path / "images", tmp_path / "out")

    assert bundle.macro_path == tmp_path / "out" / "macros" / "dot_blot_grid_analysis.ijm"
    assert bundle.macro_path.read_text(encoding="utf-8") == bundle.macro_text


def test_protein_imagej_cli_macro_accepts_parameter_overrides(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "labtools",
            "protein-imagej",
            "macro",
            "dot_blot_grid",
            "--input-dir",
            str(tmp_path / "images"),
            "--output-dir",
            str(tmp_path / "out"),
            "--param",
            "columns=6",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    macro_path = tmp_path / "out" / "macros" / "dot_blot_grid_analysis.ijm"
    assert completed.returncode == 0
    assert str(macro_path) in completed.stdout
    assert "columns = 6;" in macro_path.read_text(encoding="utf-8")
