from __future__ import annotations

from pathlib import Path


PADDLEOCR_WORKER_MODULE = "biomedpilot_ocr_worker"
PADDLEOCR_WORKER_MODE_PDF = "pdf"
PADDLEOCR_WORKER_MODE_IMAGE = "image"
PADDLEOCR_WORKER_MODES = (PADDLEOCR_WORKER_MODE_PDF, PADDLEOCR_WORKER_MODE_IMAGE)


def build_paddleocr_worker_command(
    python_executable: str | Path,
    *,
    input_path: str | Path,
    mode: str,
    record_id: str,
    attachment_id: str = "",
    lang: str = "auto",
    worker_module: str = PADDLEOCR_WORKER_MODULE,
) -> list[str]:
    normalized_mode = mode.strip().lower()
    if normalized_mode not in PADDLEOCR_WORKER_MODES:
        raise ValueError("unsupported_paddleocr_worker_mode")
    command = [
        str(python_executable),
        "-m",
        worker_module,
        "--mode",
        normalized_mode,
        "--input",
        str(input_path),
        "--record-id",
        record_id,
        "--lang",
        lang,
    ]
    if attachment_id:
        command.extend(["--attachment-id", attachment_id])
    return command
