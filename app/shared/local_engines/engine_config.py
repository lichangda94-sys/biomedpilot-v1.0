from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.shared.local_engines.engine_status import EngineStatus, engine_status_from_dict
from app.shared.storage import default_storage_root


LOCAL_ENGINE_CONFIG_SCHEMA_VERSION = "biomedpilot_local_engine_config.v1"


@dataclass(frozen=True)
class LocalEngineConfig:
    engine_id: str
    configured_path_or_endpoint: str = ""
    last_status: EngineStatus | None = None
    schema_version: str = LOCAL_ENGINE_CONFIG_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "configured_path_or_endpoint": self.configured_path_or_endpoint,
            "last_status": self.last_status.to_dict() if self.last_status is not None else None,
        }


def local_engine_config_from_dict(payload: Any) -> LocalEngineConfig:
    if not isinstance(payload, dict):
        raise ValueError("Local engine config payload must be a JSON object")
    if payload.get("schema_version") != LOCAL_ENGINE_CONFIG_SCHEMA_VERSION:
        raise ValueError("Unsupported local engine config schema")
    last_status_payload = payload.get("last_status")
    return LocalEngineConfig(
        schema_version=LOCAL_ENGINE_CONFIG_SCHEMA_VERSION,
        engine_id=str(payload.get("engine_id", "")),
        configured_path_or_endpoint=str(payload.get("configured_path_or_endpoint", "")),
        last_status=engine_status_from_dict(last_status_payload) if isinstance(last_status_payload, dict) else None,
    )


@dataclass(frozen=True)
class LocalEngineConfigStore:
    engine_id: str
    config_path: Path | None = None

    def resolved_path(self) -> Path:
        if self.config_path is not None:
            return self.config_path
        return default_storage_root() / "local_engines" / f"{self.engine_id}.json"

    def load(self) -> LocalEngineConfig:
        path = self.resolved_path()
        if not path.exists():
            return LocalEngineConfig(engine_id=self.engine_id)
        try:
            config = local_engine_config_from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise ValueError("本地工具配置 JSON 无效，无法载入") from exc
        if config.engine_id != self.engine_id:
            raise ValueError("本地工具配置 engine_id 不匹配")
        return config

    def save(self, config: LocalEngineConfig) -> Path:
        if config.engine_id != self.engine_id:
            raise ValueError("本地工具配置 engine_id 不匹配")
        path = self.resolved_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(config.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        try:
            path.write_text(payload, encoding="utf-8")
        except OSError as exc:
            raise ValueError("无法写入本地工具配置，请检查路径权限") from exc
        return path

    def clear(self) -> LocalEngineConfig:
        path = self.resolved_path()
        if path.exists():
            try:
                path.unlink()
            except OSError as exc:
                raise ValueError("无法清除本地工具配置，请检查路径权限") from exc
        return LocalEngineConfig(engine_id=self.engine_id)
