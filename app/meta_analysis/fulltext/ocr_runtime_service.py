from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.fulltext.paddleocr_subprocess_runner import (
    PADDLEOCR_WORKER_MODULE,
    PaddleOcrRuntimeConfig,
    PaddleOcrSubprocessRunner,
)
from app.shared.local_engines.engine_status import ENGINE_STATUS_AVAILABLE
from app.shared.local_engines.paddleocr_detector import detect_paddleocr_runtime_status
from app.shared.local_engines.paddleocr_runtime import (
    PADDLEOCR_ENGINE_ID,
    PADDLEOCR_RUNTIME_MANIFEST_SCHEMA_VERSION,
    default_paddleocr_runtime_root,
    load_paddleocr_runtime_manifest,
    paddleocr_runtime_manifest_path,
)


OCR_RUNTIME_MANIFEST_SCHEMA_VERSION = PADDLEOCR_RUNTIME_MANIFEST_SCHEMA_VERSION
OCR_RUNTIME_ENGINE_ID = PADDLEOCR_ENGINE_ID


@dataclass(frozen=True)
class OcrRuntimeStatus:
    available: bool
    runtime_root: str
    python_executable: str = ""
    engine_id: str = OCR_RUNTIME_ENGINE_ID
    engine_version: str = ""
    manifest_path: str = ""
    runtime_manifest_id: str = ""
    status: str = "not_configured"
    message: str = ""


class MetaOcrRuntimeService:
    """Resolves a user-installed OCR runtime without storing model assets in the repo."""

    def __init__(self, runtime_root: str | Path | None = None) -> None:
        self._runtime_root = Path(runtime_root).expanduser() if runtime_root is not None else self.default_runtime_root()

    @staticmethod
    def default_runtime_root() -> Path:
        override = os.environ.get("BIOMEDPILOT_OCR_RUNTIME_ROOT", "").strip()
        if override:
            return Path(override).expanduser()
        return default_paddleocr_runtime_root()

    def manifest_path(self) -> Path:
        return paddleocr_runtime_manifest_path(self._runtime_root)

    def status(self) -> OcrRuntimeStatus:
        root = self._runtime_root.expanduser()
        manifest_path = self.manifest_path()
        engine_status = detect_paddleocr_runtime_status(root)
        try:
            manifest = load_paddleocr_runtime_manifest(root)
        except ValueError as exc:
            return OcrRuntimeStatus(
                available=False,
                runtime_root=str(root),
                manifest_path=str(manifest_path),
                status=engine_status.status,
                message=engine_status.last_error or str(exc),
            )

        python_path = Path(manifest.python_executable).expanduser()
        if engine_status.status != ENGINE_STATUS_AVAILABLE:
            return OcrRuntimeStatus(
                available=False,
                runtime_root=str(root),
                python_executable=str(python_path),
                engine_id=manifest.engine_id,
                engine_version=manifest.engine_version,
                manifest_path=str(manifest_path),
                runtime_manifest_id=manifest.runtime_id,
                status=engine_status.status,
                message=engine_status.last_error or "OCR runtime is configured but not verified.",
            )
        return OcrRuntimeStatus(
            available=True,
            runtime_root=str(root),
            python_executable=str(python_path),
            engine_id=manifest.engine_id,
            engine_version=manifest.engine_version,
            manifest_path=str(manifest_path),
            runtime_manifest_id=manifest.runtime_id,
            status="available",
            message="OCR runtime is available.",
        )

    def runner(self) -> PaddleOcrSubprocessRunner | None:
        status = self.status()
        if not status.available:
            return None
        return PaddleOcrSubprocessRunner(
            PaddleOcrRuntimeConfig(
                python_executable=status.python_executable,
                worker_module=PADDLEOCR_WORKER_MODULE,
                pythonpath_entries=(str(_repo_root()),),
            )
        )

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]
