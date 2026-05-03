from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TermConcept:
    concept_id: str
    source_vocabulary: str
    source_id: str
    preferred_label_en: str
    synonyms_en: list[str] = field(default_factory=list)
    exact_synonyms_en: list[str] = field(default_factory=list)
    related_synonyms_en: list[str] = field(default_factory=list)
    abbreviations: list[str] = field(default_factory=list)
    mesh_terms: list[str] = field(default_factory=list)
    disease_group: str = ""
    concept_type: str = ""
    parent_terms: list[str] = field(default_factory=list)
    cross_refs: dict[str, list[str]] = field(default_factory=dict)
    license: str = ""
    version: str = ""
    normalized_terms: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TermConcept":
        return cls(
            concept_id=str(payload.get("concept_id", "")),
            source_vocabulary=str(payload.get("source_vocabulary", "")),
            source_id=str(payload.get("source_id", "")),
            preferred_label_en=str(payload.get("preferred_label_en", "")),
            synonyms_en=_list(payload.get("synonyms_en")),
            exact_synonyms_en=_list(payload.get("exact_synonyms_en")),
            related_synonyms_en=_list(payload.get("related_synonyms_en")),
            abbreviations=_list(payload.get("abbreviations")),
            mesh_terms=_list(payload.get("mesh_terms")),
            disease_group=str(payload.get("disease_group", "")),
            concept_type=str(payload.get("concept_type", "")),
            parent_terms=_list(payload.get("parent_terms")),
            cross_refs=_cross_refs(payload.get("cross_refs")),
            license=str(payload.get("license", "")),
            version=str(payload.get("version", "")),
            normalized_terms=_list(payload.get("normalized_terms")),
        )


@dataclass(frozen=True)
class ChineseTermOverride:
    zh_term: str
    normalized_zh: str
    preferred_label_en: str
    mapped_concept_ids: list[str] = field(default_factory=list)
    disease_terms_en: list[str] = field(default_factory=list)
    synonyms_en: list[str] = field(default_factory=list)
    abbreviations: list[str] = field(default_factory=list)
    mesh_terms: list[str] = field(default_factory=list)
    tissue_terms: list[str] = field(default_factory=list)
    tcga_project_candidates: list[str] = field(default_factory=list)
    gtex_tissue_candidates: list[str] = field(default_factory=list)
    data_modality_terms: list[str] = field(default_factory=list)
    modifier_terms_en: list[str] = field(default_factory=list)
    exposure_terms: list[str] = field(default_factory=list)
    intervention_terms: list[str] = field(default_factory=list)
    outcome_terms: list[str] = field(default_factory=list)
    study_design_terms: list[str] = field(default_factory=list)
    publication_type_terms: list[str] = field(default_factory=list)
    concept_type: str = ""
    confidence: float = 0.0
    source: str = "zh_override"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ChineseTermOverride":
        from .term_normalizer import normalize_zh_term

        zh_term = str(payload.get("zh_term", ""))
        return cls(
            zh_term=zh_term,
            normalized_zh=str(payload.get("normalized_zh") or normalize_zh_term(zh_term)),
            preferred_label_en=str(payload.get("preferred_label_en", "")),
            mapped_concept_ids=_list(payload.get("mapped_concept_ids")),
            disease_terms_en=_list(payload.get("disease_terms_en")),
            synonyms_en=_list(payload.get("synonyms_en")),
            abbreviations=_list(payload.get("abbreviations")),
            mesh_terms=_list(payload.get("mesh_terms")),
            tissue_terms=_list(payload.get("tissue_terms")),
            tcga_project_candidates=_list(payload.get("tcga_project_candidates")),
            gtex_tissue_candidates=_list(payload.get("gtex_tissue_candidates")),
            data_modality_terms=_list(payload.get("data_modality_terms")),
            modifier_terms_en=_list(payload.get("modifier_terms_en")),
            exposure_terms=_list(payload.get("exposure_terms")),
            intervention_terms=_list(payload.get("intervention_terms")),
            outcome_terms=_list(payload.get("outcome_terms")),
            study_design_terms=_list(payload.get("study_design_terms")),
            publication_type_terms=_list(payload.get("publication_type_terms")),
            concept_type=str(payload.get("concept_type", "")),
            confidence=float(payload.get("confidence", 0.0) or 0.0),
            source=str(payload.get("source", "zh_override")),
        )


@dataclass(frozen=True)
class TermLookupResult:
    original_term: str
    normalized_term: str
    matched: bool
    matched_zh_terms: list[str] = field(default_factory=list)
    disease_terms_en: list[str] = field(default_factory=list)
    synonyms_en: list[str] = field(default_factory=list)
    abbreviations: list[str] = field(default_factory=list)
    mesh_terms: list[str] = field(default_factory=list)
    tissue_terms: list[str] = field(default_factory=list)
    tcga_project_candidates: list[str] = field(default_factory=list)
    gtex_tissue_candidates: list[str] = field(default_factory=list)
    data_modality_terms: list[str] = field(default_factory=list)
    modifier_terms_en: list[str] = field(default_factory=list)
    exposure_terms: list[str] = field(default_factory=list)
    intervention_terms: list[str] = field(default_factory=list)
    outcome_terms: list[str] = field(default_factory=list)
    study_design_terms: list[str] = field(default_factory=list)
    publication_type_terms: list[str] = field(default_factory=list)
    concept_ids: list[str] = field(default_factory=list)
    term_sources: list[str] = field(default_factory=list)
    confidence: float = 0.0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_term": self.original_term,
            "normalized_term": self.normalized_term,
            "matched": self.matched,
            "matched_zh_terms": list(self.matched_zh_terms),
            "disease_terms_en": list(self.disease_terms_en),
            "synonyms_en": list(self.synonyms_en),
            "abbreviations": list(self.abbreviations),
            "mesh_terms": list(self.mesh_terms),
            "tissue_terms": list(self.tissue_terms),
            "tcga_project_candidates": list(self.tcga_project_candidates),
            "gtex_tissue_candidates": list(self.gtex_tissue_candidates),
            "data_modality_terms": list(self.data_modality_terms),
            "modifier_terms_en": list(self.modifier_terms_en),
            "exposure_terms": list(self.exposure_terms),
            "intervention_terms": list(self.intervention_terms),
            "outcome_terms": list(self.outcome_terms),
            "study_design_terms": list(self.study_design_terms),
            "publication_type_terms": list(self.publication_type_terms),
            "concept_ids": list(self.concept_ids),
            "term_sources": list(self.term_sources),
            "confidence": self.confidence,
            "warnings": list(self.warnings),
        }


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _cross_refs(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {}
    return {str(key): _list(items) for key, items in value.items()}
