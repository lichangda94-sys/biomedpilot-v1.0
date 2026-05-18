from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class QueryIntelligenceInput:
    original_question: str
    language_hint: str = "auto"
    target_context: str = "bioinformatics"
    optional_review_type: str = ""
    optional_domain: str = ""


@dataclass(frozen=True)
class LocalModelConfig:
    enabled: bool = False
    provider: str = "ollama"
    base_url: str = ""
    translator_model: str = "translategemma"
    medical_model: str = "medgemma:4b"
    timeout_seconds: int = 20
    max_retries: int = 1
    require_json: bool = True
    fallback_to_registry: bool = True


@dataclass(frozen=True)
class LocalModelCallResult:
    status: str
    model_name: str
    ai_role: str = ""
    raw_output: str = ""
    parsed_json: dict[str, Any] | None = None
    error_message: str | None = None
    elapsed_seconds: float | None = None


@dataclass(frozen=True)
class LocalModelSearchTranslation:
    original_question: str
    model_name: str
    status: str
    raw_output: str
    parsed_json: dict[str, Any]
    candidate_zh_terms: list[str]
    candidate_en_terms: list[str]
    candidate_synonyms: list[str]
    candidate_pubmed_queries: list[str]
    candidate_geo_queries: list[str]
    rejected_terms: list[str]
    warnings: list[str]
    provider_name: str = ""
    ai_role: str = ""
    gateway_status: str = ""
    fallback_used: bool = False
    output_char_count: int = 0
    output_sha256: str = ""


@dataclass(frozen=True)
class SearchTranslationDraft:
    original_question: str
    detected_language: str
    target_context: str
    target_database: str
    normalized_question: str
    review_or_analysis_intent: str
    main_concepts_zh: list[str]
    main_concepts_en: list[str]
    disease_terms_zh: list[str]
    disease_terms_en: list[str]
    exposure_terms_zh: list[str]
    exposure_terms_en: list[str]
    outcome_terms_zh: list[str]
    outcome_terms_en: list[str]
    modifier_terms_zh: list[str]
    modifier_terms_en: list[str]
    data_type_terms_en: list[str]
    mesh_terms: list[str]
    database_terms: list[str]
    pubmed_query_candidates: list[str]
    geo_query_candidates: list[str]
    rejected_terms: list[str]
    warnings: list[str]
    confidence: float
    local_model_status: str
    local_model_used: bool
    search_execution_status: str
    audit: dict[str, Any]
    candidate_terms: list[str] = field(default_factory=list)
    pico_terms: list[str] = field(default_factory=list)
    effect_measures: list[str] = field(default_factory=list)
    diagnostic_accuracy_terms: list[str] = field(default_factory=list)
    exclusion_type_terms: list[str] = field(default_factory=list)
    quality_assessment_terms: list[str] = field(default_factory=list)
    pubmed_query_terms: list[str] = field(default_factory=list)
    source: str = "rule_based"
    ai_provider: str = "disabled"
    ai_role: str = ""
    model_name: str = ""
    generated_at: str = ""
    user_confirmation_required: bool = True
    accepted_by_user: bool = False


@dataclass(frozen=True)
class MedicalConcept:
    concept_id: str
    label_zh: str
    zh_terms: tuple[str, ...] = ()
    en_terms: tuple[str, ...] = ()
    synonyms: tuple[str, ...] = ()
    mesh_terms: tuple[str, ...] = ()
    database_terms: tuple[str, ...] = ()
    semantic_group: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "concept_id": self.concept_id,
            "label_zh": self.label_zh,
            "zh_terms": list(self.zh_terms),
            "en_terms": list(self.en_terms),
            "synonyms": list(self.synonyms),
            "mesh_terms": list(self.mesh_terms),
            "database_terms": list(self.database_terms),
            "semantic_group": self.semantic_group,
        }


@dataclass(frozen=True)
class QueryIntelligenceResult:
    original_question: str
    detected_language: str
    normalized_question: str
    detected_domain: str
    detected_intent: str
    detected_review_or_analysis_type: str
    concepts: tuple[MedicalConcept, ...] = ()
    warnings: tuple[str, ...] = ()
    confidence: float = 0.0
    local_model_status: str = "fallback_registry_only"
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def zh_terms(self) -> tuple[str, ...]:
        return _unique(term for concept in self.concepts for term in concept.zh_terms)

    @property
    def en_terms(self) -> tuple[str, ...]:
        return _unique(term for concept in self.concepts for term in concept.en_terms)

    @property
    def synonyms(self) -> tuple[str, ...]:
        return _unique(term for concept in self.concepts for term in concept.synonyms)

    @property
    def mesh_terms(self) -> tuple[str, ...]:
        return _unique(term for concept in self.concepts for term in concept.mesh_terms)

    @property
    def database_terms(self) -> tuple[str, ...]:
        return _unique(term for concept in self.concepts for term in concept.database_terms)

    def to_dict(self) -> dict[str, object]:
        return {
            "original_question": self.original_question,
            "detected_language": self.detected_language,
            "normalized_question": self.normalized_question,
            "detected_domain": self.detected_domain,
            "detected_intent": self.detected_intent,
            "detected_review_or_analysis_type": self.detected_review_or_analysis_type,
            "concepts": [concept.to_dict() for concept in self.concepts],
            "zh_terms": list(self.zh_terms),
            "en_terms": list(self.en_terms),
            "synonyms": list(self.synonyms),
            "mesh_terms": list(self.mesh_terms),
            "database_terms": list(self.database_terms),
            "warnings": list(self.warnings),
            "confidence": self.confidence,
            "local_model_status": self.local_model_status,
            "metadata": self.metadata,
        }


def _unique(values: object) -> tuple[str, ...]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:  # type: ignore[union-attr]
        text = str(value).strip()
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            items.append(text)
    return tuple(items)
