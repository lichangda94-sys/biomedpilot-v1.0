from __future__ import annotations

from app.shared.ai_gateway.models import AIGatewayRequest, AIGatewayResponse, AIProviderStatus
from app.shared.ai_gateway.providers.base import AIProvider


class DisabledProvider(AIProvider):
    name = "disabled"
    model_name = "none"
    status = AIProviderStatus.DISABLED
    uses_network = False
    external_model = False

    def generate(self, request: AIGatewayRequest) -> AIGatewayResponse:
        return AIGatewayResponse(
            request_id=request.request_id,
            module=request.module,
            task_type=request.task_type,
            status="fallback_used",
            content="AI Gateway is disabled. No model call was performed.",
            provider_name=self.name,
            model_name=self.model_name,
            fallback_used=True,
            metadata={"reason": "disabled_provider"},
        )
