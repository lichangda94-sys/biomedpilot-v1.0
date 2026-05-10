from __future__ import annotations

from dataclasses import dataclass

from app.shared.ai_gateway.models import AIGatewayConfig, AIGatewayRequest
from app.shared.ai_gateway.providers.base import AIProvider


@dataclass(frozen=True)
class PrivacyPolicyDecision:
    allowed: bool
    reason: str = ""


def check_request_privacy(request: AIGatewayRequest, config: AIGatewayConfig) -> PrivacyPolicyDecision:
    if request.requires_network and not config.allow_network:
        return PrivacyPolicyDecision(False, "network access is disabled by AI Gateway config")
    if request.requests_external_model and not config.allow_external_model:
        return PrivacyPolicyDecision(False, "external model access is disabled by AI Gateway config")
    if request.contains_sensitive_content and not config.allow_sensitive_upload:
        return PrivacyPolicyDecision(False, "sensitive content upload is disabled by AI Gateway config")
    return PrivacyPolicyDecision(True)


def check_provider_privacy(provider: AIProvider, config: AIGatewayConfig) -> PrivacyPolicyDecision:
    if provider.uses_network and not config.allow_network:
        return PrivacyPolicyDecision(False, f"provider {provider.name} requires network access")
    if provider.external_model and not config.allow_external_model:
        return PrivacyPolicyDecision(False, f"provider {provider.name} uses an external model")
    return PrivacyPolicyDecision(True)
