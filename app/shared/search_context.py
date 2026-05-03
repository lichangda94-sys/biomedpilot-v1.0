from __future__ import annotations

from dataclasses import dataclass, replace

from app.shared.query_intelligence.query_intelligence_models import SearchTranslationDraft


@dataclass(frozen=True)
class SearchContext:
    module: str
    target_context: str
    allowed_databases: tuple[str, ...]
    forbidden_databases: tuple[str, ...]
    default_database: str
    allow_network: bool = False
    search_execution_mode: str = "draft_only"


BIOINFORMATICS_SEARCH_CONTEXT = SearchContext(
    module="bioinformatics",
    target_context="bioinformatics",
    allowed_databases=("geo", "gse", "tcga", "gtex", "local"),
    forbidden_databases=("pubmed", "web_of_science", "wos", "embase", "cnki", "zotero", "endnote"),
    default_database="geo",
)


META_ANALYSIS_SEARCH_CONTEXT = SearchContext(
    module="meta_analysis",
    target_context="meta_analysis",
    allowed_databases=("pubmed", "web_of_science", "wos", "embase", "cnki", "zotero", "endnote", "ris", "nbib", "csv"),
    forbidden_databases=("geo", "gse", "tcga", "gtex"),
    default_database="pubmed",
)


def filter_search_translation_draft_by_context(
    draft: SearchTranslationDraft,
    context: SearchContext,
) -> SearchTranslationDraft:
    allowed = {value.lower() for value in context.allowed_databases}
    audit = dict(draft.audit)
    audit["filtered_for_context"] = context.module
    audit["allowed_databases"] = list(context.allowed_databases)
    audit["forbidden_databases"] = list(context.forbidden_databases)

    pubmed_candidates = list(draft.pubmed_query_candidates)
    geo_candidates = list(draft.geo_query_candidates)
    database_terms = [
        term
        for term in draft.database_terms
        if _database_token_allowed(term, allowed)
    ]

    if context.module == "bioinformatics":
        pubmed_candidates = []
    elif context.module == "meta_analysis":
        geo_candidates = []

    return replace(
        draft,
        target_context=context.target_context,
        target_database=context.default_database,
        pubmed_query_candidates=pubmed_candidates,
        geo_query_candidates=geo_candidates,
        database_terms=database_terms,
        audit=audit,
    )


_KNOWN_DATABASE_TOKENS = {
    "geo",
    "gse",
    "tcga",
    "tcga-thca",
    "gtex",
    "pubmed",
    "web_of_science",
    "wos",
    "embase",
    "cnki",
    "zotero",
    "endnote",
}


def _database_token(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def _database_token_allowed(value: str, allowed: set[str]) -> bool:
    token = _database_token(value)
    if token in allowed:
        return True
    if any(token == allowed_token or token.startswith(f"{allowed_token}-") for allowed_token in allowed):
        return True
    return token not in _KNOWN_DATABASE_TOKENS
