from __future__ import annotations

import json
from pathlib import Path

from app.shared.ai_gateway.models import AIGatewayConfig


DEFAULT_CONFIG_PATH = Path("config") / "ai_gateway_config.json"


def load_ai_gateway_config(config_path: str | Path | None = None) -> AIGatewayConfig:
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    if not path.exists():
        return AIGatewayConfig()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return AIGatewayConfig()
    if not isinstance(payload, dict):
        return AIGatewayConfig()
    return _config_from_mapping(payload)


def _config_from_mapping(payload: dict[str, object]) -> AIGatewayConfig:
    defaults = AIGatewayConfig()
    allowed_task_prefixes = _parse_allowed_task_prefixes(payload.get("allowed_task_prefixes"))
    provider_configs = _parse_provider_configs(payload.get("provider_configs"))
    return AIGatewayConfig(
        allow_network=_bool_value(payload, "allow_network", defaults.allow_network),
        allow_external_model=_bool_value(payload, "allow_external_model", defaults.allow_external_model),
        allow_sensitive_upload=_bool_value(payload, "allow_sensitive_upload", defaults.allow_sensitive_upload),
        store_raw_prompts=_bool_value(payload, "store_raw_prompts", defaults.store_raw_prompts),
        store_raw_responses=_bool_value(payload, "store_raw_responses", defaults.store_raw_responses),
        default_provider=_str_value(payload, "default_provider", defaults.default_provider),
        audit_log_path=_str_value(payload, "audit_log_path", defaults.audit_log_path),
        allowed_task_prefixes=allowed_task_prefixes or defaults.allowed_task_prefixes,
        provider_configs=provider_configs,
    )


def _bool_value(payload: dict[str, object], key: str, default: bool) -> bool:
    value = payload.get(key)
    if isinstance(value, bool):
        return value
    return default


def _str_value(payload: dict[str, object], key: str, default: str) -> str:
    value = payload.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _parse_allowed_task_prefixes(value: object) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {}
    parsed: dict[str, list[str]] = {}
    for module, prefixes in value.items():
        if not isinstance(module, str) or not isinstance(prefixes, list):
            continue
        clean_prefixes = [prefix for prefix in prefixes if isinstance(prefix, str) and prefix]
        if clean_prefixes:
            parsed[module] = clean_prefixes
    return parsed


def _parse_provider_configs(value: object) -> dict[str, dict[str, object]]:
    if not isinstance(value, dict):
        return {}
    parsed: dict[str, dict[str, object]] = {}
    for provider_name, provider_config in value.items():
        if isinstance(provider_name, str) and isinstance(provider_config, dict):
            parsed[provider_name] = dict(provider_config)
    return parsed
