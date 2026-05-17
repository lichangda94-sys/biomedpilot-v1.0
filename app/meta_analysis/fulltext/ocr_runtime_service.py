from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.meta_analysis.fulltext.paddleocr_subprocess_runner import (
    PADDLEOCR_WORKER_MODULE,
    PaddleOcrRuntimeConfig,
    PaddleOcrSubprocessRunner,
)


OCR_RUNTIME_MANIFEST_SCHEMA_VERSION = "biomedpilot_ocr_runtime.v1"
OCR_RUNTIME_ENGINE_ID = "paddleocr_local"


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
        if sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / "BioMedPilot" / "engines" / "ocr" / "paddleocr"
        if os.name == "nt":
            return Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "BioMedPilot" / "engines" / "ocr" / "paddleocr"
        return Path.home() / ".local" / "share" / "BioMedPilot" / "engines" / "ocr" / "paddleocr"

    def manifest_path(self) -> Path:
        return self._runtime_root / "runtime_manifest.json"

    def status(self) -> OcrRuntimeStatus:
        root = self._runtime_root.expanduser()
        manifest_path = self.manifest_path()
        if not manifest_path.exists():
            return OcrRuntimeStatus(
                available=False,
                runtime_root=str(root),
                manifest_path=str(manifest_path),
                status="manifest_missing",
                message="OCR runtime manifest is missing.",
            )
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return OcrRuntimeStatus(
                available=False,
                runtime_root=str(root),
                manifest_path=str(manifest_path),
                status="manifest_invalid",
                message=f"OCR runtime manifest is not readable: {type(exc).__name__}.",
            )
        if not isinstance(payload, dict):
            return OcrRuntimeStatus(
                available=False,
                runtime_root=str(root),
                manifest_path=str(manifest_path),
                status="manifest_invalid",
                message="OCR runtime manifest must be a JSON object.",
            )
        schema_version = str(payload.get("schema_version") or "")
        engine_id = str(payload.get("engine_id") or OCR_RUNTIME_ENGINE_ID)
        python_payload = payload.get("python")
        python_executable = str(payload.get("python_executable") or "")
        if not python_executable and isinstance(python_payload, dict):
            python_executable = str(python_payload.get("executable") or "")
        python_path = Path(python_executable).expanduser() if python_executable else Path()
        if schema_version != OCR_RUNTIME_MANIFEST_SCHEMA_VERSION:
            return self._unavailable(root, manifest_path, payload, "schema_unsupported", "OCR runtime manifest schema is unsupported.")
        if engine_id != OCR_RUNTIME_ENGINE_ID:
            return self._unavailable(root, manifest_path, payload, "engine_unsupported", "OCR runtime engine is unsupported.")
        if not python_executable or not python_path.exists() or not python_path.is_file():
            return self._unavailable(root, manifest_path, payload, "python_missing", "OCR runtime Python executable is missing.")
        return OcrRuntimeStatus(
            available=True,
            runtime_root=str(root),
            python_executable=str(python_path),
            engine_id=engine_id,
            engine_version=_engine_version(payload),
            manifest_path=str(manifest_path),
            runtime_manifest_id=str(payload.get("runtime_manifest_id") or payload.get("manifest_id") or payload.get("runtime_id") or ""),
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

    def _unavailable(
        self,
        root: Path,
        manifest_path: Path,
        payload: dict[str, Any],
        status: str,
        message: str,
    ) -> OcrRuntimeStatus:
        return OcrRuntimeStatus(
            available=False,
            runtime_root=str(root),
            python_executable=_python_executable(payload),
            engine_id=str(payload.get("engine_id") or OCR_RUNTIME_ENGINE_ID),
            engine_version=_engine_version(payload),
            manifest_path=str(manifest_path),
            runtime_manifest_id=str(payload.get("runtime_manifest_id") or payload.get("manifest_id") or payload.get("runtime_id") or ""),
            status=status,
            message=message,
        )


def _python_executable(payload: dict[str, Any]) -> str:
    value = str(payload.get("python_executable") or "")
    python_payload = payload.get("python")
    if not value and isinstance(python_payload, dict):
        value = str(python_payload.get("executable") or "")
    return value


def _engine_version(payload: dict[str, Any]) -> str:
    value = str(payload.get("engine_version") or "")
    packages = payload.get("packages")
    if not value and isinstance(packages, dict):
        value = str(packages.get("paddleocr") or "")
    return value


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]
