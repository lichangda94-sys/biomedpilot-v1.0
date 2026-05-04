from __future__ import annotations

from dataclasses import dataclass, field


META_SEARCH_DATABASES = ("pubmed", "web_of_science", "embase", "cnki")
PICO_PECO_SLOTS = ("population", "intervention_or_exposure", "comparator", "outcome", "study_design")


@dataclass(frozen=True)
class MetaConceptGroupDraft:
    slot: str
    label: str
    terms_zh: tuple[str, ...] = ()
    terms_en: tuple[str, ...] = ()
    mesh_terms: tuple[str, ...] = ()
    source: str = "shared_medical_vocabulary"

    @property
    def all_terms(self) -> tuple[str, ...]:
        return _unique([*self.terms_zh, *self.terms_en, *self.mesh_terms])


@dataclass(frozen=True)
class QueryDraft:
    database: str
    query: str
    status: str = "draft_only"
    note: str = "Requires reviewer validation before execution."


@dataclass(frozen=True)
class MetaSearchStrategyDraft:
    original_question: str
    target_context: str
    review_framework: str
    review_or_analysis_intent: str
    concept_groups: tuple[MetaConceptGroupDraft, ...]
    query_drafts: tuple[QueryDraft, ...]
    warnings: tuple[str, ...] = ()
    audit: dict[str, object] = field(default_factory=dict)

    @property
    def population(self) -> MetaConceptGroupDraft:
        return self._group("population")

    @property
    def intervention_or_exposure(self) -> MetaConceptGroupDraft:
        return self._group("intervention_or_exposure")

    @property
    def comparator(self) -> MetaConceptGroupDraft:
        return self._group("comparator")

    @property
    def outcome(self) -> MetaConceptGroupDraft:
        return self._group("outcome")

    @property
    def study_design(self) -> MetaConceptGroupDraft:
        return self._group("study_design")

    @property
    def pubmed_query_draft(self) -> str:
        return self.query_for("pubmed")

    @property
    def web_of_science_query_draft(self) -> str:
        return self.query_for("web_of_science")

    @property
    def embase_query_draft(self) -> str:
        return self.query_for("embase")

    @property
    def cnki_query_draft(self) -> str:
        return self.query_for("cnki")

    def query_for(self, database: str) -> str:
        for draft in self.query_drafts:
            if draft.database == database:
                return draft.query
        return ""

    def _group(self, slot: str) -> MetaConceptGroupDraft:
        for group in self.concept_groups:
            if group.slot == slot:
                return group
        return MetaConceptGroupDraft(slot=slot, label=slot.replace("_", " ").title())


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
