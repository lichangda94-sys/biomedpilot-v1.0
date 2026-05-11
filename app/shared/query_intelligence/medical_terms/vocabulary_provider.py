from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.shared.query_intelligence.biomedical_term_registry import match_registry_concepts
from app.shared.query_intelligence.query_intelligence_models import MedicalConcept

from .term_index_loader import load_full_term_index, load_mini_term_index
from .term_index_models import ChineseTermOverride, TermConcept
from .term_normalizer import normalize_en_term, normalize_zh_term
from .zh_overrides_loader import load_zh_overrides


@dataclass(frozen=True)
class VocabularyProviderMatch:
    source: str
    provider_kind: str
    overrides: tuple[ChineseTermOverride, ...] = ()
    index_concepts: tuple[TermConcept, ...] = ()
    registry_concepts: tuple[MedicalConcept, ...] = ()

    @property
    def matched(self) -> bool:
        return bool(self.overrides or self.index_concepts or self.registry_concepts)


class MedicalVocabularyProvider(Protocol):
    provider_id: str
    provider_kind: str

    def lookup(self, query: str, normalized_query: str, target_context: str) -> VocabularyProviderMatch:
        """Return vocabulary matches for a normalized medical query."""


def default_vocabulary_providers() -> tuple[MedicalVocabularyProvider, ...]:
    return (
        ChineseOverrideVocabularyProvider(),
        RuntimeIndexVocabularyProvider(),
        RegistryFallbackVocabularyProvider(),
    )


@dataclass(frozen=True)
class ChineseOverrideVocabularyProvider:
    provider_id: str = "zh_term_overrides"
    provider_kind: str = "external_asset"

    def lookup(self, query: str, normalized_query: str, target_context: str) -> VocabularyProviderMatch:
        return VocabularyProviderMatch(
            source=self.provider_id,
            provider_kind=self.provider_kind,
            overrides=tuple(_rank_override_matches(_matched_overrides(normalized_query))),
        )


@dataclass(frozen=True)
class RuntimeIndexVocabularyProvider:
    provider_id: str = "runtime_medical_terms_index"
    provider_kind: str = "external_asset"

    def lookup(self, query: str, normalized_query: str, target_context: str) -> VocabularyProviderMatch:
        concepts, source = _matched_runtime_index_concepts(normalized_query)
        return VocabularyProviderMatch(
            source=source or self.provider_id,
            provider_kind=self.provider_kind,
            index_concepts=tuple(concepts),
        )


@dataclass(frozen=True)
class RegistryFallbackVocabularyProvider:
    provider_id: str = "biomedical_term_registry"
    provider_kind: str = "mainline_fallback"

    def lookup(self, query: str, normalized_query: str, target_context: str) -> VocabularyProviderMatch:
        return VocabularyProviderMatch(
            source=self.provider_id,
            provider_kind=self.provider_kind,
            registry_concepts=match_registry_concepts(query, target_context=target_context),
        )


def _matched_overrides(normalized_query: str) -> list[ChineseTermOverride]:
    candidates: list[ChineseTermOverride] = []
    for override in load_zh_overrides():
        if not override.normalized_zh:
            continue
        if override.normalized_zh == normalized_query or override.normalized_zh in normalized_query:
            candidates.append(override)
    return candidates


def _matched_runtime_index_concepts(normalized_query: str) -> tuple[list[TermConcept], str]:
    full_matches = _matched_index_concepts(normalized_query, load_full_term_index())
    if full_matches:
        return full_matches, "medical_terms_index.sqlite"
    mini_matches = _matched_index_concepts(normalized_query, load_mini_term_index())
    if mini_matches:
        return mini_matches, "mini_medical_terms_index"
    return [], ""


def _matched_index_concepts(normalized_query: str, concepts: tuple[TermConcept, ...]) -> list[TermConcept]:
    candidates: list[TermConcept] = []
    for concept in concepts:
        terms = [concept.preferred_label_en, *concept.normalized_terms, *concept.synonyms_en, *concept.exact_synonyms_en]
        for term in terms:
            normalized = normalize_zh_term(term) if not term.isascii() else normalize_en_term(term)
            if normalized and (normalized == normalized_query or normalized in normalized_query):
                candidates.append(concept)
                break
    return _rank_concept_matches(candidates)


def _rank_override_matches(candidates: list[ChineseTermOverride]) -> list[ChineseTermOverride]:
    priority = {"disease": 0, "modifier": 1, "tissue": 2, "data_modality": 3}
    candidates.sort(key=lambda item: (priority.get(item.concept_type, 9), -len(item.normalized_zh), -item.confidence))
    disease_spans = [item.normalized_zh for item in candidates if item.concept_type == "disease"]
    result: list[ChineseTermOverride] = []
    for item in candidates:
        if item.concept_type in {"tissue", "data_modality"} and any(item.normalized_zh != span and item.normalized_zh in span for span in disease_spans):
            continue
        result.append(item)
    return result


def _rank_concept_matches(candidates: list[TermConcept]) -> list[TermConcept]:
    priority = {"disease": 0, "modifier": 1, "tissue": 2, "data_modality": 3}
    unique: dict[str, TermConcept] = {candidate.concept_id: candidate for candidate in candidates}
    items = list(unique.values())
    items.sort(key=lambda item: (priority.get(item.concept_type, 9), -max((len(term) for term in item.normalized_terms), default=0)))
    return items
