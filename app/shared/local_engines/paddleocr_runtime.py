from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


PADDLEOCR_RUNTIME_MANIFEST_SCHEMA_VERSION = "biomedpilot_ocr_runtime.v1"
PADDLEOCR_ENGINE_ID = "paddleocr_local"


@dataclass(frozen=True)
class PaddleOCRModelAsset:
    name: str
    language: str = "auto"
    path: str = ""
    sha256: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "language": self.language, "path": self.path, "sha256": self.sha256}


@dataclass(frozen=True)
class PaddleOCRRuntimeManifest:
    runtime_id: str
    platform: str
    python_executable: str
    python_version: str = ""
    packages: Mapping[str, str] = field(default_factory=dict)
    models: tuple[PaddleOCRModelAsset, ...] = ()
    smoke_test_status: str = "unknown"
    smoke_test_result_path: str = ""
    created_at: str = ""
    schema_version: str = PADDLEOCR_RUNTIME_MANIFEST_SCHEMA_VERSION
    engine_id: str = PADDLEOCR_ENGINE_ID

    @property
    def engine_version(self) -> str:
        return str(self.packages.get("paddleocr", "") or "")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "runtime_id": self.runtime_id,
            "created_at": self.created_at,
            "platform": self.platform,
            "python": {"executable": self.python_executable, "version": self.python_version},
            "packages": dict(self.packages),
            "models": [model.to_dict() for model in self.models],
            "smoke_test": {"status": self.smoke_test_status, "result_path": self.smoke_test_result_path},
        }


def default_paddleocr_runtime_root(*, platform_name: str | None = None, home: str | Path | None = None, env: Mapping[str, str] | None = None) -> Path:
    platform_value = platform_name or sys.platform
    home_path = Path(home).expanduser() if home is not None else Path.home()
    env_values = env or os.environ
    if platform_value == "darwin":
        return home_path / "Library" / "Application Support" / "BioMedPilot" / "engines" / "ocr" / "paddleocr"
    if platform_value.startswith("win"):
        local_app_data = env_values.get("LOCALAPPDATA")
        base = Path(local_app_data) if local_app_data else home_path / "AppData" / "Local"
        return base / "BioMedPilot" / "engines" / "ocr" / "paddleocr"
    return home_path / ".local" / "share" / "BioMedPilot" / "engines" / "ocr" / "paddleocr"


def paddleocr_runtime_manifest_path(runtime_root: str | Path) -> Path:
    return Path(runtime_root).expanduser() / "runtime_manifest.json"


def load_paddleocr_runtime_manifest(runtime_root: str | Path) -> PaddleOCRRuntimeManifest:
    path = paddleocr_runtime_manifest_path(runtime_root)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError("paddleocr_runtime_manifest_missing") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("paddleocr_runtime_manifest_invalid") from exc
    return paddleocr_runtime_manifest_from_dict(payload)


def paddleocr_runtime_manifest_from_dict(payload: Any) -> PaddleOCRRuntimeManifest:
    if not isinstance(payload, dict):
        raise ValueError("paddleocr_runtime_manifest_must_be_object")
    if payload.get("schema_version") != PADDLEOCR_RUNTIME_MANIFEST_SCHEMA_VERSION:
        raise ValueError("unsupported_paddleocr_runtime_manifest_schema")
    if str(payload.get("engine_id") or PADDLEOCR_ENGINE_ID) != PADDLEOCR_ENGINE_ID:
        raise ValueError("paddleocr_runtime_manifest_engine_id_mismatch")
    python_payload = payload.get("python") if isinstance(payload.get("python"), dict) else {}
    smoke_payload = payload.get("smoke_test") if isinstance(payload.get("smoke_test"), dict) else {}
    packages = payload.get("packages") if isinstance(payload.get("packages"), dict) else {}
    models = tuple(_model_from_payload(item) for item in payload.get("models", []) if isinstance(item, dict))
    runtime_id = str(payload.get("runtime_id") or "").strip()
    python_executable = str(python_payload.get("executable") or "").strip()
    if not runtime_id:
        raise ValueError("paddleocr_runtime_manifest_missing_runtime_id")
    if not python_executable:
        raise ValueError("paddleocr_runtime_manifest_missing_python_executable")
    return PaddleOCRRuntimeManifest(
        runtime_id=runtime_id,
        platform=str(payload.get("platform") or ""),
        python_executable=python_executable,
        python_version=str(python_payload.get("version") or ""),
        packages={str(key): str(value) for key, value in packages.items()},
        models=models,
        smoke_test_status=str(smoke_payload.get("status") or "unknown"),
        smoke_test_result_path=str(smoke_payload.get("result_path") or ""),
        created_at=str(payload.get("created_at") or ""),
    )


def _model_from_payload(payload: dict[str, Any]) -> PaddleOCRModelAsset:
    return PaddleOCRModelAsset(
        name=str(payload.get("name") or ""),
        language=str(payload.get("language") or "auto"),
        path=str(payload.get("path") or ""),
        sha256=str(payload.get("sha256") or ""),
    )
