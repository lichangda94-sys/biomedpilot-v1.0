# Stage Meta-Search-UI-1 Report

## Scope

Connected the Meta Analysis search strategy scaffold to the Meta PICO/PICOS
protocol page. The page now displays database query drafts only; no online
literature retrieval is executed.

## UI Output

- PICO/PECO mode
- Concept blocks with `role` values for population, exposure/intervention,
  comparison, outcome, and study type
- PubMed query draft with MeSH and tiab terms
- Web of Science query draft marked draft-only
- Embase query draft marked draft-only with `/exp` and `:ti,ab,kw` terms
- CNKI query draft marked draft-only
- Warnings
- `local_model_status`
- `search_execution_status=draft_only`
- Chinese draft-only status text: 当前仅生成检索式草稿，尚未执行在线检索。

## Artifacts

The page can write:

- `protocol/search_strategy_draft.json`
- `protocol/search_strategy_audit.json`

It does not write `protocol/search_execution_report.json`.

## Boundary Notes

- The builder still uses shared `build_search_translation_draft()` with
  `target_context="meta_analysis"`.
- GEO, GSE, TCGA, and GTEx terms are not rendered in Meta search strategy
  output.
- Bioinformatics, shared medical terms, data medical terms, and online PubMed
  execution logic were not changed.
- `app/shared/literature_search/` was not added.
