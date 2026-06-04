from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from labtools.cell_culture import (
    build_imagej_run_command,
    get_cell_imagej_experiment,
    list_cell_imagej_experiments,
    render_cell_imagej_macro,
    resolve_imagej_executable,
    run_cell_imagej_macro,
    write_cell_imagej_macro,
)


def test_cell_imagej_experiment_catalog_exposes_requested_workflows() -> None:
    experiment_ids = {spec.experiment_id for spec in list_cell_imagej_experiments()}

    assert experiment_ids == {"wound_scratch", "transwell", "immunohistochemistry"}
    assert get_cell_imagej_experiment("划痕实验").experiment_id == "wound_scratch"
    assert get_cell_imagej_experiment("ihc").experiment_id == "immunohistochemistry"


def test_wound_scratch_macro_contains_batch_csv_and_parameter_overrides(tmp_path: Path) -> None:
    bundle = render_cell_imagej_macro(
        "wound_scratch",
        tmp_path / "images",
        tmp_path / "out",
        parameters={"threshold_method": "Otsu", "min_gap_area_px": 1200},
    )

    assert bundle.output_csv_path == tmp_path / "out" / "wound_scratch_results.csv"
    assert "File.saveString(\"image,gap_area_px,total_area_px,gap_fraction" in bundle.macro_text
    assert "threshold_method = \"Otsu\";" in bundle.macro_text
    assert "min_gap_area_px = 1200;" in bundle.macro_text
    quote_escape_line = '    escaped = replace(value, "\\\"", "\\\"\\\"");'
    assert quote_escape_line in bundle.macro_text
    assert "Analyze Particles..." in bundle.macro_text


def test_transwell_and_ihc_macros_expose_real_imagej_workflows(tmp_path: Path) -> None:
    transwell = render_cell_imagej_macro("transwell", tmp_path / "images", tmp_path / "out")
    ihc = render_cell_imagej_macro("immunohistochemistry", tmp_path / "images", tmp_path / "out")

    assert "particle_count,total_particle_area_px" in transwell.macro_text
    assert "run(\"Watershed\")" in transwell.macro_text
    assert "positive_area_px,total_area_px,positive_fraction" in ihc.macro_text
    assert "mean_gray" in ihc.macro_text


def test_write_cell_imagej_macro_creates_default_macro_path(tmp_path: Path) -> None:
    bundle = write_cell_imagej_macro("transwell", tmp_path / "images", tmp_path / "out")

    assert bundle.macro_path == tmp_path / "out" / "macros" / "transwell_particle_count.ijm"
    assert bundle.macro_path.read_text(encoding="utf-8") == bundle.macro_text


def test_resolve_imagej_executable_accepts_fiji_app_bundle(tmp_path: Path) -> None:
    app_executable = tmp_path / "Fiji.app" / "Contents" / "MacOS" / "ImageJ-macosx"
    app_executable.parent.mkdir(parents=True)
    app_executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    app_executable.chmod(0o755)

    assert resolve_imagej_executable(tmp_path / "Fiji.app") == app_executable


def test_run_cell_imagej_macro_invokes_explicit_executable(tmp_path: Path) -> None:
    executable = tmp_path / "fake-imagej"
    log_path = tmp_path / "imagej.args"
    executable.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$@\" > {log_path}\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)

    result = run_cell_imagej_macro("wound_scratch", tmp_path / "images", tmp_path / "out", imagej_executable=executable)

    assert result.returncode == 0
    assert result.command == build_imagej_run_command(executable, result.macro_path)
    logged_args = log_path.read_text(encoding="utf-8")
    assert "--headless" in logged_args
    assert str(result.macro_path) in logged_args
    assert os.access(result.macro_path, os.R_OK)


def test_cell_imagej_cli_macro_accepts_parameter_overrides(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "labtools",
            "cell-imagej",
            "macro",
            "wound_scratch",
            "--input-dir",
            str(tmp_path / "images"),
            "--output-dir",
            str(tmp_path / "out"),
            "--param",
            "threshold_method=Otsu",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    macro_path = tmp_path / "out" / "macros" / "wound_scratch_analysis.ijm"
    assert completed.returncode == 0
    assert str(macro_path) in completed.stdout
    assert "threshold_method = \"Otsu\";" in macro_path.read_text(encoding="utf-8")
