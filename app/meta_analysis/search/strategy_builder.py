from __future__ import annotations

from app.meta_analysis.search.pubmed_query_builder import build_pubmed_query_draft
from app.meta_analysis.search.search_strategy_models import (
    META_SEARCH_DATABASES,
    MetaConceptGroupDraft,
    MetaSearchStrategyDraft,
    QueryDraft,
)
from app.shared.query_intelligence import SearchTranslationDraft, build_search_translation_draft
from app.shared.search_context import META_ANALYSIS_SEARCH_CONTEXT, filter_search_translation_draft_by_context


_FORBIDDEN_META_OUTPUT_TOKENS = ("geo", "gse", "tcga", "gtex")
_PUBLICATION_EXCLUSION_MESH = {"Animals", "Case Reports", "Editorial", "Letter", "Review"}


def build_meta_search_strategy_draft(
    question: str,
    *,
    population: str = "",
    intervention_or_exposure: str = "",
    comparator: str = "",
    outcome: str = "",
    study_design: str = "",
) -> MetaSearchStrategyDraft:
    shared_draft = _shared_meta_translation(question)
    framework = _review_framework(shared_draft)
    concept_groups = _build_concept_groups(
        shared_draft,
        framework=framework,
        population=population,
        intervention_or_exposure=intervention_or_exposure,
        comparator=comparator,
        outcome=outcome,
        study_design=study_design,
    )
    query_drafts = _build_query_drafts(concept_groups)

    return MetaSearchStrategyDraft(
        original_question=shared_draft.original_question,
        target_context="meta_analysis",
        review_framework=framework,
        review_or_analysis_intent=shared_draft.review_or_analysis_intent,
        concept_groups=concept_groups,
        query_drafts=query_drafts,
        local_model_status=shared_draft.local_model_status,
        search_execution_status=shared_draft.search_execution_status,
        warnings=tuple(shared_draft.warnings),
        audit={
            "shared_target_context": shared_draft.target_context,
            "shared_target_database": shared_draft.target_database,
            "shared_search_execution_status": shared_draft.search_execution_status,
            "shared_local_model_status": shared_draft.local_model_status,
            "shared_term_sources": tuple(shared_draft.audit.get("term_sources", ())),
            "context_filter": shared_draft.audit.get("filtered_for_context"),
            "search_execution": "not_implemented_draft_only",
            "database_scope": META_SEARCH_DATABASES,
        },
    )


def _shared_meta_translation(question: str) -> SearchTranslationDraft:
    draft = build_search_translation_draft(
        question,
        target_context="meta_analysis",
        target_database="pubmed",
        use_local_model=False,
        allow_network=False,
    )
    return filter_search_translation_draft_by_context(draft, META_ANALYSIS_SEARCH_CONTEXT)


def _review_framework(draft: SearchTranslationDraft) -> str:
    if draft.exposure_terms_en or "exposure" in draft.review_or_analysis_intent:
        return "PECO"
    return "PICO"


def _build_concept_groups(
    draft: SearchTranslationDraft,
    *,
    framework: str,
    population: str,
    intervention_or_exposure: str,
    comparator: str,
    outcome: str,
    study_design: str,
) -> tuple[MetaConceptGroupDraft, ...]:
    exposure_terms_en = _safe_terms([intervention_or_exposure, *draft.exposure_terms_en])
    exposure_terms_zh = _safe_terms(draft.exposure_terms_zh)
    exposure_keys = {term.lower() for term in exposure_terms_en}
    disease_terms_en = _safe_terms(
        term for term in [*draft.disease_terms_en, *draft.main_concepts_en] if term.lower() not in exposure_keys
    )
    disease_terms_zh = _safe_terms(draft.disease_terms_zh)
    outcome_terms_en = _safe_terms([outcome, *draft.outcome_terms_en, *disease_terms_en])
    outcome_terms_zh = _safe_terms([*draft.outcome_terms_zh, *disease_terms_zh])
    population_terms_en = _safe_terms([population]) or disease_terms_en
    population_terms_zh = () if population else disease_terms_zh
    mesh_terms = _safe_mesh_terms(draft.mesh_terms)

    return (
        MetaConceptGroupDraft(
            slot="population",
            label="Population",
            terms_zh=population_terms_zh,
            terms_en=population_terms_en,
            mesh_terms=_mesh_for_terms(mesh_terms, [*population_terms_en, *population_terms_zh]),
        ),
        MetaConceptGroupDraft(
            slot="intervention_or_exposure",
            label="Exposure" if framework == "PECO" else "Intervention",
            terms_zh=exposure_terms_zh,
            terms_en=exposure_terms_en,
            mesh_terms=_mesh_for_terms(mesh_terms, [*exposure_terms_en, *exposure_terms_zh]),
        ),
        MetaConceptGroupDraft(
            slot="comparator",
            label="Comparator",
            terms_en=_safe_terms([comparator]),
        ),
        MetaConceptGroupDraft(
            slot="outcome",
            label="Outcome",
            terms_zh=outcome_terms_zh,
            terms_en=outcome_terms_en,
            mesh_terms=_mesh_for_terms(mesh_terms, [*outcome_terms_en, *outcome_terms_zh]),
        ),
        MetaConceptGroupDraft(
            slot="study_design",
            label="Study Design",
            terms_en=_safe_terms([study_design, "systematic review", "meta-analysis"]),
        ),
    )


def _build_query_drafts(concept_groups: tuple[MetaConceptGroupDraft, ...]) -> tuple[QueryDraft, ...]:
    return (
        QueryDraft(database="pubmed", query=build_pubmed_query_draft(concept_groups)),
        QueryDraft(database="web_of_science", query=_web_of_science_query_draft(concept_groups)),
        QueryDraft(database="embase", query=_embase_query_draft(concept_groups)),
        QueryDraft(database="cnki", query=_cnki_query_draft(concept_groups)),
    )


def _web_of_science_query_draft(concept_groups: tuple[MetaConceptGroupDraft, ...]) -> str:
    blocks = [_or_block(_quote(term) for term in group.terms_en) for group in concept_groups]
    return " AND ".join(f"TS={block}" for block in blocks if block)


def _embase_query_draft(concept_groups: tuple[MetaConceptGroupDraft, ...]) -> str:
    blocks: list[str] = []
    for group in concept_groups:
        terms = [*(f"{_quote(term)}/exp" for term in group.mesh_terms), *(f"{_quote(term)}:ti,ab" for term in group.terms_en)]
        block = _or_block(terms)
        if block:
            blocks.append(block)
    return " AND ".join(blocks)


def _cnki_query_draft(concept_groups: tuple[MetaConceptGroupDraft, ...]) -> str:
    blocks = [_or_block(_quote(term) for term in group.terms_zh) for group in concept_groups]
    return " AND ".join(f"主题={block}" for block in blocks if block)


def _safe_mesh_terms(values: list[str]) -> tuple[str, ...]:
    return _safe_terms(term for term in values if term not in _PUBLICATION_EXCLUSION_MESH)


def _mesh_for_terms(mesh_terms: tuple[str, ...], values: object) -> tuple[str, ...]:
    tokens = set()
    for value in values:  # type: ignore[union-attr]
        tokens.update(_tokens(str(value)))
    return _safe_terms(mesh for mesh in mesh_terms if tokens.intersection(_tokens(mesh)))


def _or_block(values: object) -> str:
    terms = _safe_terms(values)
    if not terms:
        return ""
    if len(terms) == 1:
        return terms[0]
    return "(" + " OR ".join(terms) + ")"


def _quote(value: str) -> str:
    text = value.strip().strip('"')
    return f'"{text}"'


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(token for token in value.lower().replace("-", " ").split() if len(token) >= 3)


def _safe_terms(values: object) -> tuple[str, ...]:
    seen: set[str] = set()
    terms: list[str] = []
    for value in values:  # type: ignore[union-attr]
        text = str(value).strip()
        key = text.lower()
        if text and key not in seen and not _has_forbidden_meta_output_token(text):
            seen.add(key)
            terms.append(text)
    return tuple(terms)


def _has_forbidden_meta_output_token(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in _FORBIDDEN_META_OUTPUT_TOKENS)
