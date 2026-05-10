from __future__ import annotations

from app.shared.ai_gateway.models import AIGatewayConfig
from app.shared.ai_gateway.providers.base import AIProvider
from app.shared.ai_gateway.providers.disabled_provider import DisabledProvider
from app.shared.ai_gateway.providers.ollama_provider import OllamaProvider


class AIProviderRegistry:
    def __init__(self, config: AIGatewayConfig | None = None) -> None:
        self._providers: dict[str, AIProvider] = {}
        self.register(DisabledProvider())
        if config is not None:
            ollama_provider = OllamaProvider.from_provider_config(config.provider_configs.get("ollama", {}))
            if ollama_provider.enabled:
                self.register(ollama_provider)

    def register(self, provider: AIProvider) -> None:
        self._providers[provider.name] = provider

    def get(self, provider_name: str) -> AIProvider:
        provider = self._providers.get(provider_name)
        if provider is not None:
            return provider
        return self._providers["disabled"]

    def names(self) -> list[str]:
        return sorted(self._providers)


def default_provider_registry(config: AIGatewayConfig | None = None) -> AIProviderRegistry:
    return AIProviderRegistry(config)
