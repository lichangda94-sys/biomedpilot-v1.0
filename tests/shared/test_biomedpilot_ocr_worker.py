from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from biomedpilot_ocr_worker.__main__ import _paddle_lang
from biomedpilot_ocr_worker.paddleocr_engine import blocks_from_result_payload


def test_worker_missing_runtime_dependency_returns_structured_json(tmp_path: Path) -> None:
    image = tmp_path / "ocr.png"
    image.write_bytes(b"not-a-real-image")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "biomedpilot_ocr_worker",
            "--mode",
            "image",
            "--input",
            str(image),
            "--record-id",
            "rec-1",
        ],
        capture_output=True,
        text=True,
        cwd=str(Path.cwd()),
    )
    payload = json.loads(completed.stdout)

    assert completed.returncode in {3, 4}
    assert payload["schema_version"] == "biomedpilot_ocr_result.v1"
    assert payload["status"] == "failed"
    assert payload["source"]["record_id"] == "rec-1"
    assert payload["pages"] == []
    assert payload["errors"]
    assert "final Meta extraction" in payload["safety_note"]


def test_worker_missing_input_returns_exit_code_2(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "biomedpilot_ocr_worker",
            "--mode",
            "pdf",
            "--input",
            str(tmp_path / "missing.pdf"),
            "--record-id",
            "rec-2",
        ],
        capture_output=True,
        text=True,
        cwd=str(Path.cwd()),
    )
    payload = json.loads(completed.stdout)

    assert completed.returncode == 2
    assert payload["source"]["media_type"] == "application/pdf"
    assert payload["errors"] == ["input_file_missing"]


def test_worker_language_mapping_supports_chinese_english_and_traditional() -> None:
    assert _paddle_lang("auto") == "ch"
    assert _paddle_lang("en") == "en"
    assert _paddle_lang("zh-tw") == "chinese_cht"


def test_worker_can_use_local_paddleocr_source_root_override(tmp_path: Path) -> None:
    source_root = tmp_path / "PaddleOCR-main"
    package = source_root / "paddleocr"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        "\n".join(
            [
                "__version__ = 'source-test'",
                "class _Result:",
                "    def to_dict(self):",
                "        return {'res': {'rec_texts': ['BioMedPilot source OCR'], 'rec_scores': [0.98], 'rec_polys': [[[1, 2], [20, 2], [20, 12], [1, 12]]]}}",
                "class PaddleOCR:",
                "    def __init__(self, **kwargs):",
                "        self.kwargs = kwargs",
                "    def predict(self, path):",
                "        return [_Result()]",
            ]
        ),
        encoding="utf-8",
    )
    image = tmp_path / "ocr.png"
    image.write_bytes(b"not-a-real-image")
    env = os.environ.copy()
    env["BIOMEDPILOT_PADDLEOCR_SOURCE_ROOT"] = str(source_root)

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "biomedpilot_ocr_worker",
            "--mode",
            "image",
            "--input",
            str(image),
            "--record-id",
            "rec-source",
        ],
        capture_output=True,
        text=True,
        cwd=str(Path.cwd()),
        env=env,
    )
    payload = json.loads(completed.stdout)

    assert completed.returncode == 0
    assert payload["status"] == "completed"
    assert payload["engine"]["engine_version"] == "source-test"
    assert payload["pages"][0]["text"] == "BioMedPilot source OCR"
    assert payload["pages"][0]["blocks"][0]["confidence"] == 0.98


def test_worker_source_root_override_fails_closed_when_invalid(tmp_path: Path) -> None:
    image = tmp_path / "ocr.png"
    image.write_bytes(b"not-a-real-image")
    env = os.environ.copy()
    env["BIOMEDPILOT_PADDLEOCR_SOURCE_ROOT"] = str(tmp_path / "missing-source")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "biomedpilot_ocr_worker",
            "--mode",
            "image",
            "--input",
            str(image),
            "--record-id",
            "rec-invalid-source",
        ],
        capture_output=True,
        text=True,
        cwd=str(Path.cwd()),
        env=env,
    )
    payload = json.loads(completed.stdout)

    assert completed.returncode == 4
    assert payload["status"] == "failed"
    assert payload["errors"] == ["paddleocr_source_root_invalid"]


def test_paddleocr_payload_blocks_are_normalized_and_sorted() -> None:
    blocks = blocks_from_result_payload(
        {
            "rec_texts": ["right", "left", "lower"],
            "rec_scores": [0.9, 0.8, 0.7],
            "rec_polys": [
                [[40, 10], [60, 10], [60, 20], [40, 20]],
                [[5, 12], [20, 12], [20, 22], [5, 22]],
                [[4, 40], [20, 40], [20, 50], [4, 50]],
            ],
        }
    )

    assert [block.text for block in blocks] == ["left", "right", "lower"]
    assert blocks[0].bbox == (5.0, 12.0, 20.0, 22.0)
    assert blocks[0].order == 0
