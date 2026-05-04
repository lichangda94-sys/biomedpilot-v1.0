# Stage Meta-Search-Scaffold Report

## Scope

This stage adds a Meta Analysis owned search scaffold for literature query
drafts. It does not execute PubMed, Web of Science, Embase, or CNKI searches.

## Added Structure

- `app/meta_analysis/search/search_strategy_models.py`
- `app/meta_analysis/search/strategy_builder.py`
- `app/meta_analysis/search/pubmed_query_builder.py`
- `tests/meta_analysis/test_meta_search_strategy_builder.py`

## Boundary Notes

- The builder reuses shared `build_search_translation_draft()` with
  `target_context="meta_analysis"`.
- The scaffold keeps Meta outputs scoped to PubMed, Web of Science, Embase, and
  CNKI draft queries.
- GEO, GSE, TCGA, and GTEx tokens are filtered from concept blocks and query
  drafts.
- `app/shared/literature_search/` was not added.
- Bioinformatics files and Bioinformatics UI were not modified.

## Current Behavior

- Builds PECO when shared vocabulary detects exposure terms.
- Preserves PICO/PECO concept group structure for later protocol integration.
- Builds PubMed draft queries using MeSH and tiab terms.
- Builds placeholder drafts for Web of Science, Embase, and CNKI.
- Marks all query drafts as `draft_only`.

## Deferred Work

- Real literature retrieval clients.
- Reviewer editable strategy UI.
- Database-specific syntax validation beyond the current draft format.
- Cross-module shared literature clients, pending actual reuse need.
