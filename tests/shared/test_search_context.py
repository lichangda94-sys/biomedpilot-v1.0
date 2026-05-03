from __future__ import annotations

from app.shared.query_intelligence import build_search_translation_draft
from app.shared.search_context import (
    BIOINFORMATICS_SEARCH_CONTEXT,
    META_ANALYSIS_SEARCH_CONTEXT,
    filter_search_translation_draft_by_context,
)


def test_bioinformatics_context_allows_only_dataset_databases() -> None:
    assert BIOINFORMATICS_SEARCH_CONTEXT.allowed_databases == ("geo", "gse", "tcga", "gtex", "local")
    assert "pubmed" in BIOINFORMATICS_SEARCH_CONTEXT.forbidden_databases
    assert "embase" in BIOINFORMATICS_SEARCH_CONTEXT.forbidden_databases
    assert BIOINFORMATICS_SEARCH_CONTEXT.default_database == "geo"


def test_meta_context_allows_only_literature_databases() -> None:
    assert "pubmed" in META_ANALYSIS_SEARCH_CONTEXT.allowed_databases
    assert "web_of_science" in META_ANALYSIS_SEARCH_CONTEXT.allowed_databases
    assert "embase" in META_ANALYSIS_SEARCH_CONTEXT.allowed_databases
    assert "cnki" in META_ANALYSIS_SEARCH_CONTEXT.allowed_databases
    assert "zotero" in META_ANALYSIS_SEARCH_CONTEXT.allowed_databases
    assert "endnote" in META_ANALYSIS_SEARCH_CONTEXT.allowed_databases
    assert "geo" in META_ANALYSIS_SEARCH_CONTEXT.forbidden_databases
    assert "tcga" in META_ANALYSIS_SEARCH_CONTEXT.forbidden_databases
    assert "gtex" in META_ANALYSIS_SEARCH_CONTEXT.forbidden_databases
    assert META_ANALYSIS_SEARCH_CONTEXT.default_database == "pubmed"


def test_bioinformatics_draft_filters_pubmed_candidates() -> None:
    draft = build_search_translation_draft("低分化甲状腺癌相关数据集")

    filtered = filter_search_translation_draft_by_context(draft, BIOINFORMATICS_SEARCH_CONTEXT)

    assert filtered.pubmed_query_candidates == []
    assert filtered.geo_query_candidates
    assert filtered.audit["filtered_for_context"] == "bioinformatics"
    assert "TCGA-THCA" in filtered.database_terms


def test_meta_draft_filters_geo_candidates() -> None:
    draft = build_search_translation_draft(
        "肥胖与甲状腺癌发病风险 Meta 分析",
        target_context="meta_analysis",
        target_database="pubmed",
    )

    filtered = filter_search_translation_draft_by_context(draft, META_ANALYSIS_SEARCH_CONTEXT)

    assert filtered.pubmed_query_candidates
    assert filtered.geo_query_candidates == []
    assert "TCGA-THCA" not in filtered.database_terms
    assert filtered.audit["filtered_for_context"] == "meta_analysis"
