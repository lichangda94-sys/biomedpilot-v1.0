from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.meta_analysis.fulltext.ocr_models import OcrDocumentResult, ocr_document_from_dict


PADDLEOCR_WORKER_MODULE = "biomedpilot_ocr_worker"
PADDLEOCR_WORKER_MODE_PDF = "pdf"
PADDLEOCR_WORKER_MODE_IMAGE = "image"
PADDLEOCR_WORKER_MODES = (PADDLEOCR_WORKER_MODE_PDF, PADDLEOCR_WORKER_MODE_IMAGE)

Runner = Callable[..., subprocess.CompletedProcess[str]]


class PaddleOcrSubprocessError(RuntimeError):
    pass


@dataclass(frozen=True)
class PaddleOcrRuntimeConfig:
    python_executable: str
    worker_module: str = PADDLEOCR_WORKER_MODULE
    timeout_seconds: int = 300


class PaddleOcrSubprocessRunner:
    def __init__(self, config: PaddleOcrRuntimeConfig, *, runner: Runner = subprocess.run) -> None:
        self._config = config
        self._runner = runner

    def run_pdf_ocr(self, pdf_path: Path, *, record_id: str, attachment_id: str = "", lang: str = "auto") -> OcrDocumentResult:
        return self._run_ocr(pdf_path, mode=PADDLEOCR_WORKER_MODE_PDF, record_id=record_id, attachment_id=attachment_id, lang=lang)

    def run_image_ocr(self, image_path: Path, *, record_id: str, attachment_id: str = "", lang: str = "auto") -> OcrDocumentResult:
        return self._run_ocr(image_path, mode=PADDLEOCR_WORKER_MODE_IMAGE, record_id=record_id, attachment_id=attachment_id, lang=lang)

    def build_command(self, input_path: str | Path, *, mode: str, record_id: str, attachment_id: str = "", lang: str = "auto") -> list[str]:
        return build_paddleocr_worker_command(
            self._config.python_executable,
            input_path=input_path,
            mode=mode,
            record_id=record_id,
            attachment_id=attachment_id,
            lang=lang,
            worker_module=self._config.worker_module,
        )

    def _run_ocr(self, input_path: Path, *, mode: str, record_id: str, attachment_id: str, lang: str) -> OcrDocumentResult:
        python_path = Path(self._config.python_executable).expanduser()
        if not python_path.exists() or not python_path.is_file():
            raise PaddleOcrSubprocessError("paddleocr_runtime_python_missing")
        command = self.build_command(input_path, mode=mode, record_id=record_id, attachment_id=attachment_id, lang=lang)
        try:
            completed = self._runner(command, capture_output=True, text=True, timeout=self._config.timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            raise PaddleOcrSubprocessError("paddleocr_worker_timeout") from exc
        except OSError as exc:
            raise PaddleOcrSubprocessError(f"paddleocr_worker_launch_failed:{type(exc).__name__}") from exc
        if completed.returncode != 0:
            raise PaddleOcrSubprocessError(f"paddleocr_worker_failed:{_summarize_process_error(completed)}")
        try:
            payload = _json_payload_from_stdout(completed.stdout)
            return ocr_document_from_dict(payload)
        except (json.JSONDecodeError, ValueError) as exc:
            raise PaddleOcrSubprocessError("paddleocr_worker_invalid_json") from exc


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


def _json_payload_from_stdout(stdout: str) -> Any:
    text = stdout.strip()
    if not text:
        raise json.JSONDecodeError("empty stdout", stdout, 0)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        for line in reversed([part.strip() for part in stdout.splitlines() if part.strip()]):
            if line.startswith("{") and line.endswith("}"):
                return json.loads(line)
        raise


def _summarize_process_error(completed: subprocess.CompletedProcess[str]) -> str:
    text = "\n".join(part.strip() for part in (completed.stderr, completed.stdout) if part and part.strip())
    if not text:
        text = f"exit code {completed.returncode}"
    return text[:500]
