from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.shared.ai_gateway.models import AIGatewayRequest, AIGatewayResponse, AIProviderStatus
from app.shared.ai_gateway.providers.base import AIProvider


DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "medgemma:4b"
DEFAULT_OLLAMA_TIMEOUT_SECONDS = 20


@dataclass(frozen=True)
class OllamaProviderConfig:
    enabled: bool = False
    base_url: str = DEFAULT_OLLAMA_BASE_URL
    default_model: str = DEFAULT_OLLAMA_MODEL
    timeout_seconds: int = DEFAULT_OLLAMA_TIMEOUT_SECONDS


class OllamaProvider(AIProvider):
    name = "ollama"
    status = AIProviderStatus.UNAVAILABLE
    uses_network = True
    external_model = False

    def __init__(
        self,
        config: OllamaProviderConfig | None = None,
        *,
        urlopen_func: Callable[..., object] | None = None,
    ) -> None:
        self.config = config or OllamaProviderConfig()
        self.model_name = self.config.default_model
        self._urlopen = urlopen_func or urlopen
        self.status = AIProviderStatus.DISABLED if not self.config.enabled else AIProviderStatus.UNAVAILABLE

    @classmethod
    def from_provider_config(cls, payload: dict[str, object] | None) -> "OllamaProvider":
        return cls(_ollama_config_from_mapping(payload or {}))

    @property
    def enabled(self) -> bool:
        return self.config.enabled

    def detect_ollama_status(self) -> AIProviderStatus:
        if not self.config.enabled:
            self.status = AIProviderStatus.DISABLED
            return self.status

        try:
            request = Request(_join_url(self.config.base_url, "/api/tags"), method="GET")
            with self._urlopen(request, timeout=min(self.config.timeout_seconds, 5)) as response:
                status_code = int(getattr(response, "status", 200))
                self.status = AIProviderStatus.AVAILABLE if 200 <= status_code < 300 else AIProviderStatus.UNAVAILABLE
                return self.status
        except (TimeoutError, HTTPError, URLError, OSError):
            self.status = AIProviderStatus.UNAVAILABLE
            return self.status
        except Exception:
            self.status = AIProviderStatus.ERROR
            return self.status

    def generate(self, request: AIGatewayRequest) -> AIGatewayResponse:
        model = self._model_for_request(request)
        output_format = self._output_format_for_request(request)
        if not self.config.enabled:
            return self._fallback_response(request, model, "ollama provider is disabled", status="fallback_used")

        payload: dict[str, object] = {
            "model": model,
            "prompt": request.prompt,
            "stream": False,
        }
        if output_format == "json":
            payload["format"] = "json"

        http_request = Request(
            _join_url(self.config.base_url, "/api/generate"),
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with self._urlopen(http_request, timeout=self.config.timeout_seconds) as response:
                status_code = int(getattr(response, "status", 200))
                if not 200 <= status_code < 300:
                    return self._fallback_response(request, model, f"ollama returned HTTP {status_code}")
                body = response.read()
        except HTTPError as exc:
            return self._fallback_response(request, model, f"ollama returned HTTP {exc.code}")
        except (TimeoutError, URLError, OSError) as exc:
            return self._fallback_response(request, model, f"ollama connection failed: {exc.__class__.__name__}")
        except Exception as exc:
            return self._fallback_response(request, model, f"ollama provider error: {exc.__class__.__name__}")

        if not body:
            return self._fallback_response(request, model, "ollama returned an empty HTTP response")

        try:
            ollama_payload = json.loads(body.decode("utf-8"))
        except Exception:
            return self._fallback_response(request, model, "ollama returned invalid response JSON")
        if not isinstance(ollama_payload, dict):
            return self._fallback_response(request, model, "ollama response JSON was not an object")

        content = _response_content(ollama_payload)
        if not content.strip():
            return self._fallback_response(request, model, "ollama returned empty generated content")

        warnings: list[str] = []
        if output_format == "json":
            try:
                json.loads(content)
            except Exception:
                warnings.append("ollama generated content was not valid JSON")

        metadata: dict[str, object] = {"warnings": warnings}
        if output_format:
            metadata["output_format"] = output_format
        return AIGatewayResponse(
            request_id=request.request_id,
            module=request.module,
            task_type=request.task_type,
            status="success",
            content=content,
            provider_name=self.name,
            model_name=model,
            fallback_used=False,
            metadata=metadata,
        )

    def _model_for_request(self, request: AIGatewayRequest) -> str:
        for source in (request.metadata, request.context):
            value = source.get("model")
            if isinstance(value, str) and value.strip():
                return value.strip()
        return self.config.default_model

    def _output_format_for_request(self, request: AIGatewayRequest) -> str:
        for source in (request.metadata, request.context):
            value = source.get("output_format")
            if isinstance(value, str) and value.strip():
                return value.strip().lower()
        return ""

    def _fallback_response(
        self,
        request: AIGatewayRequest,
        model: str,
        warning: str,
        *,
        status: str = "error",
    ) -> AIGatewayResponse:
        return AIGatewayResponse(
            request_id=request.request_id,
            module=request.module,
            task_type=request.task_type,
            status=status,
            content="AI Gateway could not complete this Ollama request. No model output was used.",
            provider_name=self.name,
            model_name=model,
            fallback_used=True,
            error_message=warning,
            metadata={"warnings": [warning]},
        )


def _ollama_config_from_mapping(payload: dict[str, object]) -> OllamaProviderConfig:
    defaults = OllamaProviderConfig()
    return OllamaProviderConfig(
        enabled=_bool_value(payload, "enabled", defaults.enabled),
        base_url=_str_value(payload, "base_url", defaults.base_url).rstrip("/"),
        default_model=_str_value(payload, "default_model", defaults.default_model),
        timeout_seconds=_int_value(payload, "timeout_seconds", defaults.timeout_seconds),
    )


def _join_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _bool_value(payload: dict[str, object], key: str, default: bool) -> bool:
    value = payload.get(key)
    return value if isinstance(value, bool) else default


def _str_value(payload: dict[str, object], key: str, default: str) -> str:
    value = payload.get(key)
    return value.strip() if isinstance(value, str) and value.strip() else default


def _int_value(payload: dict[str, object], key: str, default: int) -> int:
    value = payload.get(key)
    if isinstance(value, bool):
        return default
    if isinstance(value, int) and value > 0:
        return value
    return default


def _response_content(payload: dict[str, object]) -> str:
    response = payload.get("response")
    if isinstance(response, str):
        return response
    message = payload.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
            return content
    return ""
