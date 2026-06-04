from __future__ import annotations

import struct
import zlib
from pathlib import Path

import pytest

from labtools.cell_culture import ImageJNotFoundError, resolve_imagej_executable, run_cell_imagej_macro


def test_cell_skeleton_morphology_runs_on_synthetic_sample_when_fiji_is_available(tmp_path: Path) -> None:
    try:
        imagej_executable = resolve_imagej_executable()
    except ImageJNotFoundError:
        pytest.skip("Fiji/ImageJ executable not available for real skeleton sample validation.")

    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    _write_synthetic_skeleton_png(input_dir / "synthetic_cell_skeleton.png")

    result = run_cell_imagej_macro(
        "cell_skeleton_morphology",
        input_dir,
        output_dir,
        imagej_executable=imagej_executable,
        parameters={
            "foreground_polarity": "dark",
            "threshold_method": "Default",
            "save_skeleton_image": True,
        },
        timeout_seconds=120,
    )

    assert result.returncode == 0, result.stderr
    assert result.output_csv_path.exists()
    csv_text = result.output_csv_path.read_text(encoding="utf-8")
    assert "synthetic_cell_skeleton.png,ok" in csv_text
    assert (output_dir / "synthetic_cell_skeleton_skeleton.tif").exists()
    assert (output_dir / "synthetic_cell_skeleton_skeleton_summary.csv").exists()
    assert (output_dir / "synthetic_cell_skeleton_skeleton_branches.csv").exists()


def _write_synthetic_skeleton_png(path: Path) -> None:
    width = 64
    height = 64
    pixels = bytearray()
    for y in range(height):
        pixels.append(0)
        for x in range(width):
            is_line = x == 32 or y == 32 or (16 <= x <= 48 and y == x)
            pixels.append(0 if is_line else 255)

    def chunk(kind: bytes, data: bytes) -> bytes:
        payload = kind + data
        return struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)

    png = b"".join(
        (
            b"\x89PNG\r\n\x1a\n",
            chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)),
            chunk(b"IDAT", zlib.compress(bytes(pixels))),
            chunk(b"IEND", b""),
        )
    )
    path.write_bytes(png)
