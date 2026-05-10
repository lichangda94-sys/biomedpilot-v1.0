from __future__ import annotations

from app.shared.ai_gateway.providers.base import AIProvider
from app.shared.ai_gateway.providers.disabled_provider import DisabledProvider


class AIProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}
        self.register(DisabledProvider())

    def register(self, provider: AIProvider) -> None:
        self._providers[provider.name] = provider

    def get(self, provider_name: str) -> AIProvider:
        provider = self._providers.get(provider_name)
        if provider is not None:
            return provider
        return self._providers["disabled"]

    def names(self) -> list[str]:
        return sorted(self._providers)


def default_provider_registry() -> AIProviderRegistry:
    return AIProviderRegistry()
