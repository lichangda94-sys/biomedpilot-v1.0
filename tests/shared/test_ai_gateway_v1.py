from __future__ import annotations

import json

from app.shared.ai_gateway import AIGateway, AIGatewayConfig, AIGatewayRequest, AIProviderRegistry, load_ai_gateway_config
from app.shared.ai_gateway.models import AIGatewayResponse, AIProviderStatus
from app.shared.ai_gateway.providers.base import AIProvider
from app.shared.ai_gateway.providers.disabled_provider import DisabledProvider


def test_default_config_is_safe(tmp_path) -> None:
    config = load_ai_gateway_config(tmp_path / "missing_ai_gateway_config.json")

    assert config.allow_network is False
    assert config.allow_external_model is False
    assert config.allow_sensitive_upload is False
    assert config.store_raw_prompts is False
    assert config.store_raw_responses is False
    assert config.default_provider == "disabled"
    assert config.allowed_task_prefixes["bioinformatics"] == ["bio_"]
    assert config.allowed_task_prefixes["meta_analysis"] == ["meta_"]


def test_disabled_provider_returns_fallback_response() -> None:
    request = AIGatewayRequest(module="bioinformatics", task_type="bio_report_draft", prompt="Summarize this.")

    response = DisabledProvider().generate(request)

    assert response.status == "fallback_used"
    assert response.fallback_used is True
    assert response.provider_name == "disabled"
    assert response.model_name == "none"
    assert "No model call" in response.content


def test_bioinformatics_cannot_call_meta_task(tmp_path) -> None:
    gateway = _gateway(tmp_path)

    response = gateway.generate(
        AIGatewayRequest(module="bioinformatics", task_type="meta_extraction_assist", prompt="Do meta work.")
    )

    assert response.status == "error"
    assert response.fallback_used is True
    assert "Module policy blocked" in response.error_message


def test_meta_analysis_cannot_call_bio_task(tmp_path) -> None:
    gateway = _gateway(tmp_path)

    response = gateway.generate(AIGatewayRequest(module="meta_analysis", task_type="bio_report_draft", prompt="Do bio work."))

    assert response.status == "error"
    assert response.fallback_used is True
    assert "Module policy blocked" in response.error_message


def test_unknown_module_blocked(tmp_path) -> None:
    gateway = _gateway(tmp_path)

    response = gateway.generate(AIGatewayRequest(module="other_module", task_type="other_task", prompt="Try gateway."))

    assert response.status == "error"
    assert response.fallback_used is True
    assert "not allowed" in response.error_message


def test_audit_log_is_written(tmp_path) -> None:
    log_path = tmp_path / "ai_gateway_audit.jsonl"
    gateway = _gateway(tmp_path, log_path=log_path)

    response = gateway.generate(AIGatewayRequest(module="bioinformatics", task_type="bio_query_help", prompt="Help with query."))

    assert response.status == "fallback_used"
    assert log_path.exists()
    entries = _read_jsonl(log_path)
    assert len(entries) == 1
    assert entries[0]["module"] == "bioinformatics"
    assert entries[0]["task_type"] == "bio_query_help"
    assert entries[0]["fallback_used"] is True
    assert "request_summary" in entries[0]
    assert "response_summary" in entries[0]


def test_raw_prompt_and_response_not_stored_by_default(tmp_path) -> None:
    log_path = tmp_path / "ai_gateway_audit.jsonl"
    gateway = _gateway(tmp_path, log_path=log_path)

    gateway.generate(
        AIGatewayRequest(
            module="bioinformatics",
            task_type="bio_query_help",
            prompt="VERY_SECRET_PROMPT_SHOULD_NOT_BE_STORED",
            context={"raw_note": "VERY_SECRET_CONTEXT_SHOULD_NOT_BE_STORED"},
        )
    )

    raw_log = log_path.read_text(encoding="utf-8")
    entry = _read_jsonl(log_path)[0]
    assert "VERY_SECRET_PROMPT_SHOULD_NOT_BE_STORED" not in raw_log
    assert "VERY_SECRET_CONTEXT_SHOULD_NOT_BE_STORED" not in raw_log
    assert "raw_prompt" not in entry
    assert "raw_context" not in entry
    assert "raw_response" not in entry


def test_provider_failure_returns_safe_response(tmp_path) -> None:
    registry = AIProviderRegistry()
    registry.register(FailingProvider())
    log_path = tmp_path / "ai_gateway_audit.jsonl"
    config = AIGatewayConfig(default_provider="failing", audit_log_path=str(log_path))
    gateway = AIGateway(config=config, provider_registry=registry)

    response = gateway.generate(AIGatewayRequest(module="bioinformatics", task_type="bio_query_help", prompt="Trigger failure."))

    assert response.status == "error"
    assert response.fallback_used is True
    assert response.provider_name == "disabled"
    assert "RuntimeError" in response.error_message
    assert log_path.exists()


def test_sensitive_upload_blocked_by_default(tmp_path) -> None:
    gateway = _gateway(tmp_path)

    response = gateway.generate(
        AIGatewayRequest(
            module="meta_analysis",
            task_type="meta_extraction_assist",
            prompt="Contains sensitive text",
            contains_sensitive_content=True,
        )
    )

    assert response.status == "error"
    assert response.fallback_used is True
    assert "sensitive content upload is disabled" in response.error_message


class FailingProvider(AIProvider):
    name = "failing"
    model_name = "failing-model"
    status = AIProviderStatus.ERROR
    uses_network = False
    external_model = False

    def generate(self, request: AIGatewayRequest) -> AIGatewayResponse:
        raise RuntimeError("simulated provider failure")


def _gateway(tmp_path, *, log_path=None) -> AIGateway:
    audit_log_path = log_path or tmp_path / "ai_gateway_audit.jsonl"
    return AIGateway(config=AIGatewayConfig(audit_log_path=str(audit_log_path)))


def _read_jsonl(path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
