from __future__ import annotations

from abc import ABC, abstractmethod

from app.shared.ai_gateway.models import AIGatewayRequest, AIGatewayResponse, AIProviderStatus


class AIProvider(ABC):
    name: str = ""
    model_name: str = ""
    status: AIProviderStatus = AIProviderStatus.UNAVAILABLE
    uses_network: bool = False
    external_model: bool = False

    @abstractmethod
    def generate(self, request: AIGatewayRequest) -> AIGatewayResponse:
        raise NotImplementedError
