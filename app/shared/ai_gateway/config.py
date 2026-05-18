from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from app.shared.ai_gateway.models import AIGatewayConfig


DEFAULT_CONFIG_PATH = Path("config") / "ai_gateway_config.json"
DEFAULT_LOCAL_OLLAMA_ROLE_MODEL_MAPPING = {
    "general_3b": "qwen2.5:3b",
    "translator": "translategemma:latest",
    "medical": "medgemma:4b",
}


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


def save_ai_gateway_config(config: AIGatewayConfig, config_path: str | Path | None = None) -> Path:
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _safe_config_payload(config)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path


def desktop_local_ollama_config(
    *,
    enabled: bool,
    base_url: str,
    default_model: str,
    timeout_seconds: int = 20,
    audit_log_path: str | None = None,
    role_model_mapping: dict[str, str] | None = None,
) -> AIGatewayConfig:
    defaults = AIGatewayConfig()
    clean_base_url = base_url.strip()
    clean_model = default_model.strip()
    provider_config: dict[str, object] = {
        "enabled": bool(enabled),
        "timeout_seconds": timeout_seconds if timeout_seconds > 0 else 20,
    }
    if clean_base_url:
        provider_config["base_url"] = clean_base_url
    if clean_model:
        provider_config["default_model"] = clean_model
    return AIGatewayConfig(
        allow_network=bool(enabled),
        allow_external_model=False,
        allow_sensitive_upload=False,
        store_raw_prompts=False,
        store_raw_responses=False,
        default_provider="ollama" if enabled else "disabled",
        audit_log_path=audit_log_path or defaults.audit_log_path,
        allowed_task_prefixes=defaults.allowed_task_prefixes,
        role_model_mapping=_safe_role_model_mapping(role_model_mapping) if enabled else {},
        provider_configs={"ollama": provider_config},
    )


def _safe_config_payload(config: AIGatewayConfig) -> dict[str, object]:
    payload = asdict(config)
    payload["allow_external_model"] = False
    payload["allow_sensitive_upload"] = False
    payload["store_raw_prompts"] = False
    payload["store_raw_responses"] = False
    provider_configs = payload.get("provider_configs")
    if isinstance(provider_configs, dict):
        for provider_config in provider_configs.values():
            if isinstance(provider_config, dict):
                for secret_key in ("api_key", "token", "secret", "password"):
                    provider_config.pop(secret_key, None)
    return payload


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
        role_model_mapping=_parse_role_model_mapping(payload.get("role_model_mapping")),
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


def _safe_role_model_mapping(value: dict[str, str] | None) -> dict[str, str]:
    source = value or DEFAULT_LOCAL_OLLAMA_ROLE_MODEL_MAPPING
    return {str(role): str(model).strip() for role, model in source.items() if str(role).strip() and str(model).strip()}


def _parse_role_model_mapping(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(role): str(model).strip() for role, model in value.items() if str(role).strip() and str(model).strip()}
