from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


QueryExpansion = bool | Literal["conditional"]
StandaloneSearch = bool | Literal["conditional"]


@dataclass(frozen=True)
class SeedTerm:
    concept_id: str
    preferred_label_en: str
    zh_terms: list[str]
    synonyms_en: list[str]
    concept_type: str
    pico_roles: list[str]
    query_expansion_allowed: QueryExpansion
    standalone_search_allowed: StandaloneSearch
    requires_pairing_with: list[str]
    filter_only: bool
    pdf_extraction_target: bool
    mesh_terms: list[str]
    pubmed_free_text_terms: list[str]
    emtree_terms: list[str]
    emtree_review_status: str
    review_status: str

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "SeedTerm":
        return cls(
            concept_id=str(payload["concept_id"]),
            preferred_label_en=str(payload["preferred_label_en"]),
            zh_terms=_strings(payload.get("zh_terms")),
            synonyms_en=_strings(payload.get("synonyms_en")),
            concept_type=str(payload["concept_type"]),
            pico_roles=_strings(payload.get("pico_roles")),
            query_expansion_allowed=payload["query_expansion_allowed"],  # type: ignore[arg-type]
            standalone_search_allowed=payload["standalone_search_allowed"],  # type: ignore[arg-type]
            requires_pairing_with=_strings(payload.get("requires_pairing_with")),
            filter_only=bool(payload["filter_only"]),
            pdf_extraction_target=bool(payload["pdf_extraction_target"]),
            mesh_terms=_strings(payload.get("mesh_terms")),
            pubmed_free_text_terms=_strings(payload.get("pubmed_free_text_terms")),
            emtree_terms=_strings(payload.get("emtree_terms")),
            emtree_review_status=str(payload["emtree_review_status"]),
            review_status=str(payload["review_status"]),
        )

    def search_terms(self) -> list[str]:
        return _unique([self.preferred_label_en, *self.pubmed_free_text_terms, *self.synonyms_en])


@dataclass(frozen=True)
class PicoDraft:
    population_or_disease: list[SeedTerm] = field(default_factory=list)
    exposure: list[SeedTerm] = field(default_factory=list)
    intervention: list[SeedTerm] = field(default_factory=list)
    outcome: list[SeedTerm] = field(default_factory=list)
    effect: list[SeedTerm] = field(default_factory=list)
    study_design: list[SeedTerm] = field(default_factory=list)
    research_intent: str = ""

    def concept_ids(self) -> list[str]:
        return _unique(
            [
                *(term.concept_id for term in self.population_or_disease),
                *(term.concept_id for term in self.exposure),
                *(term.concept_id for term in self.intervention),
                *(term.concept_id for term in self.outcome),
                *(term.concept_id for term in self.effect),
                *(term.concept_id for term in self.study_design),
            ]
        )


@dataclass(frozen=True)
class EvidenceCandidate:
    evidence_type: str
    value: str
    section: str
    start: int
    end: int
    context: str


@dataclass(frozen=True)
class OutcomeEffectBinding:
    outcome: str
    effect_measure: str
    statistics: list[EvidenceCandidate]
    section: str
    review_status: str = "pending_review"
    final_extraction_allowed: bool = False


def _strings(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.lower()
        if value and key not in seen:
            seen.add(key)
            result.append(value)
    return result
