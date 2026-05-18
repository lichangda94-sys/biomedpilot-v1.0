from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.shared.local_engines.ollama_llm_registry import OLLAMA_LLM_ENGINE_FAMILY, OLLAMA_LLM_ENGINE_ID
from app.shared.storage import default_storage_root


OLLAMA_LLM_RUNTIME_MANIFEST_SCHEMA_VERSION = "biomedpilot_ollama_llm_runtime.v1"
OLLAMA_LLM_RUNTIME_MANIFEST_FILENAME = "ollama_llm_runtime_manifest.json"


@dataclass(frozen=True)
class OllamaInstalledModel:
    name: str
    size: int | None = None
    modified_at: str = ""
    digest: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "size": self.size,
            "modified_at": self.modified_at,
            "digest": self.digest,
            "details": dict(self.details),
        }


@dataclass(frozen=True)
class OllamaSmokeResult:
    role_id: str
    model_name: str
    status: str
    error_summary: str = ""
    response_summary: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "role_id": self.role_id,
            "model_name": self.model_name,
            "status": self.status,
            "error_summary": self.error_summary,
            "response_summary": self.response_summary,
        }


@dataclass(frozen=True)
class OllamaLLMRuntimeManifest:
    detected_at: str
    ollama_command_path: str
    ollama_version: str
    http_endpoint: str
    service_available: bool
    model_roles: tuple[dict[str, Any], ...]
    installed_models: tuple[OllamaInstalledModel, ...] = ()
    missing_models: tuple[str, ...] = ()
    smoke_results: tuple[OllamaSmokeResult, ...] = ()
    privacy_mode: str = "local_only"
    notes: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    schema_version: str = OLLAMA_LLM_RUNTIME_MANIFEST_SCHEMA_VERSION
    engine_family: str = OLLAMA_LLM_ENGINE_FAMILY
    engine_id: str = OLLAMA_LLM_ENGINE_ID

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_family": self.engine_family,
            "engine_id": self.engine_id,
            "detected_at": self.detected_at,
            "ollama_command_path": self.ollama_command_path,
            "ollama_version": self.ollama_version,
            "http_endpoint": self.http_endpoint,
            "service_available": self.service_available,
            "model_roles": [dict(role) for role in self.model_roles],
            "installed_models": [model.to_dict() for model in self.installed_models],
            "missing_models": list(self.missing_models),
            "smoke_results": [result.to_dict() for result in self.smoke_results],
            "privacy_mode": self.privacy_mode,
            "notes": list(self.notes),
            "warnings": list(self.warnings),
        }


def default_ollama_llm_runtime_manifest_path() -> Path:
    return default_storage_root() / "local_engines" / OLLAMA_LLM_RUNTIME_MANIFEST_FILENAME


def write_ollama_llm_runtime_manifest(
    manifest: OllamaLLMRuntimeManifest,
    path: str | Path | None = None,
) -> Path:
    resolved = Path(path) if path is not None else default_ollama_llm_runtime_manifest_path()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return resolved


def load_ollama_llm_runtime_manifest(path: str | Path | None = None) -> OllamaLLMRuntimeManifest:
    resolved = Path(path) if path is not None else default_ollama_llm_runtime_manifest_path()
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError("ollama_llm_runtime_manifest_missing") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("ollama_llm_runtime_manifest_invalid") from exc
    return ollama_llm_runtime_manifest_from_dict(payload)


def ollama_llm_runtime_manifest_from_dict(payload: Any) -> OllamaLLMRuntimeManifest:
    if not isinstance(payload, dict):
        raise ValueError("ollama_llm_runtime_manifest_must_be_object")
    if payload.get("schema_version") != OLLAMA_LLM_RUNTIME_MANIFEST_SCHEMA_VERSION:
        raise ValueError("unsupported_ollama_llm_runtime_manifest_schema")
    if str(payload.get("engine_family") or OLLAMA_LLM_ENGINE_FAMILY) != OLLAMA_LLM_ENGINE_FAMILY:
        raise ValueError("ollama_llm_runtime_manifest_engine_family_mismatch")
    installed = tuple(_installed_model_from_dict(item) for item in payload.get("installed_models", []) if isinstance(item, dict))
    smoke = tuple(_smoke_result_from_dict(item) for item in payload.get("smoke_results", []) if isinstance(item, dict))
    roles = tuple(dict(item) for item in payload.get("model_roles", []) if isinstance(item, dict))
    return OllamaLLMRuntimeManifest(
        detected_at=str(payload.get("detected_at") or ""),
        ollama_command_path=str(payload.get("ollama_command_path") or ""),
        ollama_version=str(payload.get("ollama_version") or ""),
        http_endpoint=str(payload.get("http_endpoint") or ""),
        service_available=bool(payload.get("service_available")),
        model_roles=roles,
        installed_models=installed,
        missing_models=tuple(str(item) for item in payload.get("missing_models", []) if str(item).strip()),
        smoke_results=smoke,
        privacy_mode=str(payload.get("privacy_mode") or "local_only"),
        notes=tuple(str(item) for item in payload.get("notes", []) if str(item).strip()),
        warnings=tuple(str(item) for item in payload.get("warnings", []) if str(item).strip()),
    )


def _installed_model_from_dict(payload: dict[str, Any]) -> OllamaInstalledModel:
    size_value = payload.get("size")
    return OllamaInstalledModel(
        name=str(payload.get("name") or ""),
        size=size_value if isinstance(size_value, int) and not isinstance(size_value, bool) else None,
        modified_at=str(payload.get("modified_at") or ""),
        digest=str(payload.get("digest") or ""),
        details=dict(payload.get("details") or {}) if isinstance(payload.get("details"), dict) else {},
    )


def _smoke_result_from_dict(payload: dict[str, Any]) -> OllamaSmokeResult:
    return OllamaSmokeResult(
        role_id=str(payload.get("role_id") or ""),
        model_name=str(payload.get("model_name") or ""),
        status=str(payload.get("status") or "skipped"),
        error_summary=str(payload.get("error_summary") or ""),
        response_summary=str(payload.get("response_summary") or ""),
    )

