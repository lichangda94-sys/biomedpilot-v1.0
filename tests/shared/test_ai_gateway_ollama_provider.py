from __future__ import annotations

import json
from pathlib import Path
from urllib.error import URLError

from app.shared.ai_gateway import AIGateway, AIGatewayConfig, AIGatewayRequest, AIProviderRegistry, load_ai_gateway_config
from app.shared.ai_gateway.models import AIProviderStatus
from app.shared.ai_gateway.providers.disabled_provider import DisabledProvider
from app.shared.ai_gateway.providers.ollama_provider import OllamaProvider, OllamaProviderConfig


def test_default_config_does_not_enable_ollama(tmp_path) -> None:
    config = load_ai_gateway_config(tmp_path / "missing_ai_gateway_config.json")

    registry = AIProviderRegistry(config)

    assert "ollama" not in registry.names()
    assert isinstance(registry.get("ollama"), DisabledProvider)


def test_ollama_disabled_does_not_call_network() -> None:
    calls: list[object] = []
    provider = OllamaProvider(OllamaProviderConfig(enabled=False), urlopen_func=_recording_urlopen(calls))
    request = AIGatewayRequest(module="bioinformatics", task_type="bio_query_help", prompt="Do not send.")

    status = provider.detect_ollama_status()
    response = provider.generate(request)

    assert status == AIProviderStatus.DISABLED
    assert response.status == "fallback_used"
    assert response.fallback_used is True
    assert calls == []


def test_provider_registry_selects_enabled_ollama_provider() -> None:
    config = AIGatewayConfig(
        default_provider="ollama",
        provider_configs={"ollama": {"enabled": True, "default_model": "local-test-model"}},
    )

    registry = AIProviderRegistry(config)
    provider = registry.get("ollama")

    assert isinstance(provider, OllamaProvider)
    assert provider.model_name == "local-test-model"


def test_detect_ollama_status_available_when_tags_endpoint_responds() -> None:
    provider = OllamaProvider(
        OllamaProviderConfig(enabled=True),
        urlopen_func=_urlopen_sequence([_FakeResponse({"models": [{"name": "medgemma:4b"}]})]),
    )

    assert provider.detect_ollama_status() == AIProviderStatus.AVAILABLE


def test_detect_ollama_status_unavailable_on_connection_failure() -> None:
    provider = OllamaProvider(OllamaProviderConfig(enabled=True), urlopen_func=_raising_urlopen(URLError("refused")))

    assert provider.detect_ollama_status() == AIProviderStatus.UNAVAILABLE


def test_generate_success_returns_normalized_response() -> None:
    calls: list[object] = []
    provider = OllamaProvider(
        OllamaProviderConfig(enabled=True, default_model="local-test-model"),
        urlopen_func=_recording_urlopen(calls, _FakeResponse({"response": "Generated local answer."})),
    )
    request = AIGatewayRequest(module="bioinformatics", task_type="bio_query_help", prompt="Draft a query.")

    response = provider.generate(request)

    assert response.status == "success"
    assert response.content == "Generated local answer."
    assert response.provider_name == "ollama"
    assert response.model_name == "local-test-model"
    assert response.fallback_used is False
    assert len(calls) == 1


def test_generate_non_json_output_warning_does_not_crash() -> None:
    provider = OllamaProvider(
        OllamaProviderConfig(enabled=True),
        urlopen_func=_urlopen_sequence([_FakeResponse({"response": "not json"})]),
    )
    request = AIGatewayRequest(
        module="meta_analysis",
        task_type="meta_query_help",
        prompt="Return structured data.",
        metadata={"output_format": "json"},
    )

    response = provider.generate(request)

    assert response.status == "success"
    assert response.content == "not json"
    assert response.fallback_used is False
    assert response.metadata["warnings"] == ["ollama generated content was not valid JSON"]


def test_generate_timeout_returns_safe_response() -> None:
    provider = OllamaProvider(OllamaProviderConfig(enabled=True), urlopen_func=_raising_urlopen(TimeoutError("slow")))
    request = AIGatewayRequest(module="bioinformatics", task_type="bio_query_help", prompt="Timeout.")

    response = provider.generate(request)

    assert response.status == "error"
    assert response.fallback_used is True
    assert response.provider_name == "ollama"
    assert "connection failed" in response.error_message


def test_generate_connection_error_returns_safe_response() -> None:
    provider = OllamaProvider(OllamaProviderConfig(enabled=True), urlopen_func=_raising_urlopen(URLError("refused")))
    request = AIGatewayRequest(module="meta_analysis", task_type="meta_query_help", prompt="Connection error.")

    response = provider.generate(request)

    assert response.status == "error"
    assert response.fallback_used is True
    assert response.provider_name == "ollama"
    assert "connection failed" in response.error_message


def test_gateway_audit_log_does_not_store_raw_prompt_or_response(tmp_path) -> None:
    log_path = tmp_path / "ai_gateway_audit.jsonl"
    secret_prompt = "SECRET_PROMPT_SHOULD_NOT_BE_WRITTEN"
    secret_response = "SECRET_RESPONSE_SHOULD_NOT_BE_WRITTEN"
    config = AIGatewayConfig(
        allow_network=True,
        default_provider="ollama",
        audit_log_path=str(log_path),
    )
    registry = AIProviderRegistry()
    registry.register(
        OllamaProvider(
            OllamaProviderConfig(enabled=True),
            urlopen_func=_urlopen_sequence([_FakeResponse({"response": secret_response})]),
        )
    )
    gateway = AIGateway(config=config, provider_registry=registry)

    response = gateway.generate(AIGatewayRequest(module="bioinformatics", task_type="bio_query_help", prompt=secret_prompt))

    assert response.status == "success"
    raw_log = log_path.read_text(encoding="utf-8")
    entry = _read_jsonl(log_path)[0]
    assert secret_prompt not in raw_log
    assert secret_response not in raw_log
    assert entry["provider_name"] == "ollama"
    assert entry["model_name"] == "medgemma:4b"
    assert "raw_prompt" not in entry
    assert "raw_context" not in entry
    assert "raw_response" not in entry


def test_module_policy_still_blocks_ollama_provider_before_network_call(tmp_path) -> None:
    calls: list[object] = []
    config = AIGatewayConfig(
        allow_network=True,
        default_provider="ollama",
        audit_log_path=str(tmp_path / "ai_gateway_audit.jsonl"),
    )
    registry = AIProviderRegistry()
    registry.register(OllamaProvider(OllamaProviderConfig(enabled=True), urlopen_func=_recording_urlopen(calls)))
    gateway = AIGateway(config=config, provider_registry=registry)

    response = gateway.generate(
        AIGatewayRequest(module="bioinformatics", task_type="meta_extraction_assist", prompt="Should be blocked.")
    )

    assert response.status == "error"
    assert response.provider_name == "disabled"
    assert "Module policy blocked" in response.error_message
    assert calls == []


class _FakeResponse:
    def __init__(self, payload: object, *, status: int = 200) -> None:
        self.payload = payload
        self.status = status

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def _urlopen_sequence(responses: list[_FakeResponse]):
    remaining = list(responses)

    def _urlopen(request, timeout=None):
        if not remaining:
            raise AssertionError("unexpected network call")
        return remaining.pop(0)

    return _urlopen


def _recording_urlopen(calls: list[object], response: _FakeResponse | None = None):
    def _urlopen(request, timeout=None):
        calls.append({"url": getattr(request, "full_url", ""), "timeout": timeout})
        if response is None:
            raise AssertionError("network call was not expected")
        return response

    return _urlopen


def _raising_urlopen(exc: Exception):
    def _urlopen(request, timeout=None):
        raise exc

    return _urlopen


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
