from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from app.shared.query_intelligence.query_intelligence_models import MedicalConcept

from .term_index_models import ChineseTermOverride, TermConcept, TermLookupResult


@dataclass(frozen=True)
class VocabularyProviderMatch:
    source: str
    provider_kind: str
    result: TermLookupResult | None = None
    overrides: tuple[ChineseTermOverride, ...] = ()
    index_concepts: tuple[TermConcept, ...] = ()
    registry_concepts: tuple[MedicalConcept, ...] = ()

    @property
    def matched(self) -> bool:
        return bool(
            (self.result and self.result.matched)
            or self.overrides
            or self.index_concepts
            or self.registry_concepts
        )


@runtime_checkable
class MedicalVocabularyProvider(Protocol):
    provider_id: str
    provider_kind: str

    def lookup(self, query: str, normalized_query: str, target_context: str) -> VocabularyProviderMatch:
        """Return vocabulary matches for a normalized medical query."""


@dataclass(frozen=True)
class ChineseOverrideVocabularyProvider:
    provider_id: str = "zh_term_overrides"
    provider_kind: str = "external_asset"

    def lookup(self, query: str, normalized_query: str, target_context: str) -> VocabularyProviderMatch:
        return VocabularyProviderMatch(source=self.provider_id, provider_kind=self.provider_kind)


@dataclass(frozen=True)
class RuntimeIndexVocabularyProvider:
    provider_id: str = "runtime_medical_terms_index"
    provider_kind: str = "external_asset"

    def lookup(self, query: str, normalized_query: str, target_context: str) -> VocabularyProviderMatch:
        return VocabularyProviderMatch(source=self.provider_id, provider_kind=self.provider_kind)


@dataclass(frozen=True)
class RegistryFallbackVocabularyProvider:
    provider_id: str = "biomedical_term_registry"
    provider_kind: str = "mainline_fallback"

    def lookup(self, query: str, normalized_query: str, target_context: str) -> VocabularyProviderMatch:
        return VocabularyProviderMatch(source=self.provider_id, provider_kind=self.provider_kind)


def default_vocabulary_providers() -> tuple[MedicalVocabularyProvider, ...]:
    return (
        ChineseOverrideVocabularyProvider(),
        RuntimeIndexVocabularyProvider(),
        RegistryFallbackVocabularyProvider(),
    )
