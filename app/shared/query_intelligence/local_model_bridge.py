from __future__ import annotations

import hashlib
import json
import time

from app.shared.ai_gateway import AIGateway, AIGatewayConfig, AIGatewayRequest, resolve_task_role_model
from app.shared.query_intelligence.query_intelligence_models import (
    LocalModelCallResult,
    LocalModelConfig,
    LocalModelSearchTranslation,
)


SEARCH_TRANSLATION_PROMPT_TEMPLATE = """You are a biomedical search translation assistant.

Task:
Translate the Chinese biomedical search question into English biomedical search terms and database query candidates.

Rules:
1. Output JSON only.
2. Do not invent unrelated diseases.
3. Do not include thyroid cancer terms unless the original question mentions thyroid, 甲状腺, PTC, or THCA.
4. Do not include esophageal cancer terms unless the original question mentions 食管, 食道, ESCC, esophageal, or oesophageal.
5. Do not execute search.
6. Do not decide final query.
7. Generate editable query candidates only.
8. If the local vocabulary has no match, output candidate English terms only as suggestions.
9. Do not decide TCGA, GTEx, GEO, or final database mappings.

Return JSON with fields:
{{
  "main_concepts_zh": [],
  "main_concepts_en": [],
  "modifier_terms_zh": [],
  "modifier_terms_en": [],
  "data_type_terms_en": [],
  "pubmed_query_candidates": [],
  "geo_query_candidates": [],
  "candidate_terms": [],
  "uncertainty": [],
  "notes": []
}}

Original question:
{original_question}

Target context:
{target_context}

Target database:
{target_database}
"""


def detect_local_model_status() -> str:
    return "fallback_registry_only"


def describe_local_model_components() -> dict[str, str]:
    status = detect_local_model_status()
    if status == "available_not_called":
        return {
            "ollama": "available_not_called",
            "translator": "optional_not_called",
            "medical": "optional_not_called",
            "status": "available_not_called",
        }
    return {
        "ollama": "unavailable",
        "translator": "unavailable",
        "medical": "unavailable",
        "status": "fallback_registry_only",
    }


def detect_ollama_status() -> dict[str, str]:
    return {"status": "gateway_managed", "command_path": ""}


def call_ai_gateway_json(
    prompt: str,
    model: str,
    timeout_seconds: int,
    *,
    module: str,
    task_type: str,
    config: LocalModelConfig,
    target_context: str,
    target_database: str,
    ai_gateway: AIGateway | None = None,
) -> LocalModelCallResult:
    started = time.monotonic()
    try:
        gateway = ai_gateway or _gateway_from_local_model_config(config)
        gateway_config = getattr(gateway, "config", AIGatewayConfig(default_provider=config.provider))
        routing = resolve_task_role_model(gateway_config, task_type, fallback_model=model)
        if not routing.available:
            return LocalModelCallResult(
                status="role_mapping_missing_fallback_registry",
                model_name=model,
                ai_role=routing.role_id,
                error_message=routing.warning or "AI Gateway role mapping is missing.",
                elapsed_seconds=time.monotonic() - started,
            )
        response = gateway.generate(
            AIGatewayRequest(
                module=module,
                task_type=task_type,
                prompt=prompt,
                context={
                    "target_context": target_context,
                    "target_database": target_database,
                    "timeout_seconds": timeout_seconds,
                    "ai_role": routing.role_id,
                },
                requires_network=config.provider == "ollama",
                metadata={"model": routing.model_name, "ai_role": routing.role_id, "output_format": "json"},
            )
        )
    except Exception as exc:
        return LocalModelCallResult(
            status="called_failed_fallback_registry",
            model_name=model,
            error_message=f"AI Gateway call failed: {exc.__class__.__name__}.",
            elapsed_seconds=time.monotonic() - started,
        )

    content = response.content.strip()
    if response.status != "success" or response.fallback_used:
        return LocalModelCallResult(
            status="called_failed_fallback_registry",
            model_name=response.model_name or routing.model_name,
            ai_role=routing.role_id,
            raw_output="",
            error_message=response.error_message or f"AI Gateway returned {response.status}.",
            elapsed_seconds=time.monotonic() - started,
        )
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        return LocalModelCallResult(
            status="invalid_model_output_fallback_registry",
            model_name=response.model_name or routing.model_name,
            ai_role=routing.role_id,
            raw_output="",
            error_message=str(exc),
            elapsed_seconds=time.monotonic() - started,
        )
    if not isinstance(parsed, dict):
        return LocalModelCallResult(
            status="invalid_model_output_fallback_registry",
            model_name=response.model_name or routing.model_name,
            ai_role=routing.role_id,
            raw_output="",
            error_message="Ollama returned JSON, but the root value is not an object.",
            elapsed_seconds=time.monotonic() - started,
        )
    return LocalModelCallResult(
        status="called_success",
        model_name=response.model_name or routing.model_name,
        ai_role=routing.role_id,
        raw_output="",
        parsed_json=parsed,
        elapsed_seconds=time.monotonic() - started,
    )


def generate_search_translation_candidates(
    original_question: str,
    target_context: str,
    target_database: str,
    config: LocalModelConfig,
    *,
    gateway_module: str = "",
    gateway_task_type: str = "",
    ai_gateway: AIGateway | None = None,
) -> LocalModelSearchTranslation:
    if not config.enabled:
        return _empty_translation(original_question, config.medical_model, "disabled_by_config", "Local model call disabled by config.")
    if not gateway_module.strip() or not gateway_task_type.strip():
        return _empty_translation(
            original_question,
            config.medical_model,
            "missing_gateway_context_fallback_registry",
            "Local model call requires explicit AI Gateway module and task_type.",
        )
    prompt = SEARCH_TRANSLATION_PROMPT_TEMPLATE.format(
        original_question=original_question,
        target_context=target_context,
        target_database=target_database,
    )
    call_result = call_ai_gateway_json(
        prompt,
        config.medical_model,
        config.timeout_seconds,
        module=gateway_module,
        task_type=gateway_task_type,
        config=config,
        target_context=target_context,
        target_database=target_database,
        ai_gateway=ai_gateway,
    )
    if call_result.status != "called_success" or call_result.parsed_json is None:
        return _empty_translation(
            original_question,
            call_result.model_name or config.medical_model,
            call_result.status,
            call_result.error_message or "Ollama call failed.",
            ai_role=call_result.ai_role,
        )
    schema_error = _validate_translation_schema(call_result.parsed_json)
    if schema_error:
        return _empty_translation(
            original_question,
            call_result.model_name or config.medical_model,
            "invalid_model_output_fallback_registry",
            schema_error,
            ai_role=call_result.ai_role,
        )
    parsed = call_result.parsed_json
    output_summary = _json_output_summary(parsed)
    return LocalModelSearchTranslation(
        original_question=original_question,
        model_name=call_result.model_name or config.medical_model,
        status="called_success",
        raw_output="",
        parsed_json=parsed,
        candidate_zh_terms=[*parsed["main_concepts_zh"], *parsed["modifier_terms_zh"]],
        candidate_en_terms=[
            *parsed["main_concepts_en"],
            *parsed["modifier_terms_en"],
            *parsed["data_type_terms_en"],
            *parsed.get("candidate_terms", []),
        ],
        candidate_synonyms=[],
        candidate_pubmed_queries=list(parsed["pubmed_query_candidates"]),
        candidate_geo_queries=list(parsed["geo_query_candidates"]),
        rejected_terms=[],
        warnings=[str(item) for item in [*parsed.get("uncertainty", []), *parsed.get("notes", [])] if str(item).strip()],
        provider_name=config.provider,
        ai_role=call_result.ai_role,
        gateway_status="success",
        fallback_used=False,
        output_char_count=output_summary["char_count"],
        output_sha256=output_summary["sha256"],
    )


def _validate_translation_schema(payload: dict[str, object]) -> str:
    required = (
        "main_concepts_zh",
        "main_concepts_en",
        "modifier_terms_zh",
        "modifier_terms_en",
        "data_type_terms_en",
        "pubmed_query_candidates",
        "geo_query_candidates",
    )
    for key in required:
        value = payload.get(key)
        if not isinstance(value, list):
            return f"Model JSON field {key} must be a list."
        if any(not isinstance(item, str) for item in value):
            return f"Model JSON field {key} must contain strings only."
    for key in ("uncertainty", "notes"):
        value = payload.get(key, [])
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            return f"Model JSON field {key} must be a list of strings when present."
    value = payload.get("candidate_terms", [])
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        return "Model JSON field candidate_terms must be a list of strings when present."
    return ""


def _empty_translation(
    original_question: str,
    model_name: str,
    status: str,
    warning: str,
    *,
    raw_output: str = "",
    ai_role: str = "",
) -> LocalModelSearchTranslation:
    return LocalModelSearchTranslation(
        original_question=original_question,
        model_name=model_name,
        status=status,
        raw_output=raw_output,
        parsed_json={},
        candidate_zh_terms=[],
        candidate_en_terms=[],
        candidate_synonyms=[],
        candidate_pubmed_queries=[],
        candidate_geo_queries=[],
        rejected_terms=[],
        warnings=[warning] if warning else [],
        provider_name="",
        ai_role=ai_role,
        gateway_status=status,
        fallback_used=True,
        output_char_count=0,
        output_sha256="",
    )


def _gateway_from_local_model_config(config: LocalModelConfig) -> AIGateway:
    ollama_config: dict[str, object] = {
        "enabled": config.enabled,
        "default_model": config.medical_model,
        "timeout_seconds": config.timeout_seconds,
    }
    if config.base_url.strip():
        ollama_config["base_url"] = config.base_url
    return AIGateway(
        config=AIGatewayConfig(
            allow_network=config.provider == "ollama",
            default_provider=config.provider,
            provider_configs={"ollama": ollama_config},
        )
    )


def _json_output_summary(payload: dict[str, object]) -> dict[str, object]:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return {
        "char_count": len(text),
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }
