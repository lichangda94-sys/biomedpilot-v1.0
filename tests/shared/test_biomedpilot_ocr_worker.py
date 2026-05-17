from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from biomedpilot_ocr_worker.__main__ import _paddle_lang


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
