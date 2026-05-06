from __future__ import annotations

import json
import shutil
import subprocess
import time

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
    if shutil.which("ollama") is None:
        return "fallback_registry_only"
    return "available_not_called"


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
    command_path = shutil.which("ollama")
    if command_path is None:
        return {"status": "unavailable", "command_path": ""}
    return {"status": "available_not_called", "command_path": command_path}


def call_ollama_json(prompt: str, model: str, timeout_seconds: int) -> LocalModelCallResult:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return LocalModelCallResult(
            status="called_failed_fallback_registry",
            model_name=model,
            raw_output=str(exc.output or ""),
            error_message=f"Ollama call timed out after {timeout_seconds} seconds.",
            elapsed_seconds=time.monotonic() - started,
        )
    except Exception as exc:
        return LocalModelCallResult(
            status="called_failed_fallback_registry",
            model_name=model,
            error_message=str(exc),
            elapsed_seconds=time.monotonic() - started,
        )
    raw_output = (completed.stdout or "").strip()
    if completed.returncode != 0:
        return LocalModelCallResult(
            status="called_failed_fallback_registry",
            model_name=model,
            raw_output=raw_output,
            error_message=(completed.stderr or f"ollama exited with code {completed.returncode}").strip(),
            elapsed_seconds=time.monotonic() - started,
        )
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        return LocalModelCallResult(
            status="invalid_model_output_fallback_registry",
            model_name=model,
            raw_output=raw_output,
            error_message=str(exc),
            elapsed_seconds=time.monotonic() - started,
        )
    if not isinstance(parsed, dict):
        return LocalModelCallResult(
            status="invalid_model_output_fallback_registry",
            model_name=model,
            raw_output=raw_output,
            error_message="Ollama returned JSON, but the root value is not an object.",
            elapsed_seconds=time.monotonic() - started,
        )
    return LocalModelCallResult(
        status="called_success",
        model_name=model,
        raw_output=raw_output,
        parsed_json=parsed,
        elapsed_seconds=time.monotonic() - started,
    )


def generate_search_translation_candidates(
    original_question: str,
    target_context: str,
    target_database: str,
    config: LocalModelConfig,
) -> LocalModelSearchTranslation:
    ollama = detect_ollama_status()
    if not config.enabled:
        return _empty_translation(original_question, config.medical_model, "disabled_by_config", "Local model call disabled by config.")
    if ollama["status"] == "unavailable":
        return _empty_translation(original_question, config.medical_model, "unavailable", "ollama command not found.")
    prompt = SEARCH_TRANSLATION_PROMPT_TEMPLATE.format(
        original_question=original_question,
        target_context=target_context,
        target_database=target_database,
    )
    call_result = call_ollama_json(prompt, config.medical_model, config.timeout_seconds)
    if call_result.status != "called_success" or call_result.parsed_json is None:
        return _empty_translation(
            original_question,
            config.medical_model,
            call_result.status,
            call_result.error_message or "Ollama call failed.",
            raw_output=call_result.raw_output,
        )
    schema_error = _validate_translation_schema(call_result.parsed_json)
    if schema_error:
        return _empty_translation(
            original_question,
            config.medical_model,
            "invalid_model_output_fallback_registry",
            schema_error,
            raw_output=call_result.raw_output,
        )
    parsed = call_result.parsed_json
    return LocalModelSearchTranslation(
        original_question=original_question,
        model_name=config.medical_model,
        status="called_success",
        raw_output=call_result.raw_output,
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
    )
