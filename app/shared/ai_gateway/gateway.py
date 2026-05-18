from __future__ import annotations

import time
from dataclasses import replace

from app.shared.ai_gateway.config import load_ai_gateway_config
from app.shared.ai_gateway.logging.ai_audit_logger import AIAuditLogger
from app.shared.ai_gateway.models import AIGatewayConfig, AIGatewayRequest, AIGatewayResponse
from app.shared.ai_gateway.policies.module_policy import check_module_policy
from app.shared.ai_gateway.policies.privacy_policy import check_provider_privacy, check_request_privacy
from app.shared.ai_gateway.provider_registry import AIProviderRegistry, default_provider_registry


SAFE_FALLBACK_CONTENT = "AI Gateway could not complete this request. No model output was used."


class AIGateway:
    def __init__(
        self,
        config: AIGatewayConfig | None = None,
        *,
        config_path: str | None = None,
        provider_registry: AIProviderRegistry | None = None,
        audit_logger: AIAuditLogger | None = None,
    ) -> None:
        self.config = config if config is not None else load_ai_gateway_config(config_path)
        self.provider_registry = provider_registry or default_provider_registry(self.config)
        self.audit_logger = audit_logger or AIAuditLogger.from_config(self.config)

    def generate(self, request: AIGatewayRequest) -> AIGatewayResponse:
        response: AIGatewayResponse | None = None
        started = time.monotonic()
        try:
            validation_error = self._validate_request(request)
            if validation_error:
                response = self._safe_response(request, "error", validation_error)
                return response

            module_decision = check_module_policy(request, self.config)
            if not module_decision.allowed:
                response = self._safe_response(request, "error", f"Module policy blocked request: {module_decision.reason}")
                return response

            request_privacy = check_request_privacy(request, self.config)
            if not request_privacy.allowed:
                response = self._safe_response(request, "error", f"Privacy policy blocked request: {request_privacy.reason}")
                return response

            provider = self.provider_registry.get(self.config.default_provider)
            provider_privacy = check_provider_privacy(provider, self.config)
            if not provider_privacy.allowed:
                response = self._safe_response(request, "error", f"Privacy policy blocked provider: {provider_privacy.reason}")
                return response

            provider_response = provider.generate(request)
            response = self._normalize_response(request, provider_response)
            return response
        except Exception as exc:
            response = self._safe_response(request, "error", f"{exc.__class__.__name__}: provider call failed")
            return response
        finally:
            if response is not None:
                response = _response_with_duration(response, time.monotonic() - started)
                try:
                    self.audit_logger.write(request, response, self.config)
                except Exception:
                    pass

    def _validate_request(self, request: AIGatewayRequest) -> str:
        if not isinstance(request, AIGatewayRequest):
            return "request must be an AIGatewayRequest"
        if not request.module.strip():
            return "module is required"
        if not request.task_type.strip():
            return "task_type is required"
        if not isinstance(request.prompt, str):
            return "prompt must be a string"
        if not isinstance(request.context, dict):
            return "context must be a dictionary"
        return ""

    def _normalize_response(self, request: AIGatewayRequest, response: AIGatewayResponse) -> AIGatewayResponse:
        if not isinstance(response, AIGatewayResponse):
            return self._safe_response(request, "error", "provider returned an invalid response")
        if response.request_id != request.request_id:
            return AIGatewayResponse(
                request_id=request.request_id,
                module=request.module,
                task_type=request.task_type,
                status=response.status or "fallback_used",
                content=response.content or SAFE_FALLBACK_CONTENT,
                provider_name=response.provider_name,
                model_name=response.model_name,
                fallback_used=True,
                error_message=response.error_message or "provider response request_id was normalized",
                metadata=dict(response.metadata),
            )
        return response

    def _safe_response(self, request: AIGatewayRequest, status: str, error_message: str) -> AIGatewayResponse:
        return AIGatewayResponse(
            request_id=getattr(request, "request_id", ""),
            module=getattr(request, "module", ""),
            task_type=getattr(request, "task_type", ""),
            status=status,
            content=SAFE_FALLBACK_CONTENT,
            provider_name="disabled",
            model_name="none",
            fallback_used=True,
            error_message=error_message,
            metadata={"reason": "safe_fallback"},
        )


def _response_with_duration(response: AIGatewayResponse, duration_seconds: float) -> AIGatewayResponse:
    metadata = dict(response.metadata)
    metadata.setdefault("duration_seconds", round(max(duration_seconds, 0.0), 6))
    return replace(response, metadata=metadata)
