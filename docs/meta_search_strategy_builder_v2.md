# Meta Search Strategy Builder v2

Status: Developer Preview / testing.

## Scope

Search Strategy Builder v2 generates versioned multi-database search strategy drafts from the M5 confirmed PICO / PICOS / PECO protocol. It does not read temporary UI inputs directly.

It does not execute database searches, import literature, create screening decisions, or update PRISMA counts.

## Active Service

- `app/meta_analysis/search/search_strategy_builder_service.py`
- Required input: `protocol/pico_workspace_confirmed.json`
- Required input schema: `meta_confirmed_protocol.v2`

## Draft Databases

- PubMed
- Web of Science
- Embase
- Cochrane
- CNKI
- WanFang
- VIP

## Schema Versions

- Draft strategy: `meta_search_strategy_draft.v2`
- Draft set: `meta_search_strategy_draft_set.v2`
- Confirmed strategy: `meta_confirmed_search_strategy.v2`
- Confirmed set: `meta_confirmed_search_strategy_set.v2`
- Manifest: `meta_search_strategy_builder_manifest.v2`

## Artifacts

- `protocol/search_strategy_v2/search_strategy_drafts.json`
- `protocol/search_strategy_v2/search_strategy_draft_versions.json`
- `protocol/search_strategy_v2/search_strategy_confirmed.json`
- `protocol/search_strategy_v2/search_strategy_confirmed_versions.json`
- `protocol/search_strategy_v2/search_strategy_manifest.json`
- `protocol/search_strategy_v2/search_strategy_draft.md`
- `protocol/search_strategy_v2/search_strategy_draft.txt`

## Query Draft Rules

PubMed:

- MeSH terms
- `tiab` terms
- Boolean query
- can be executed only through the existing explicit reviewer-confirmed PubMed execution entry

Web of Science:

- `TS=` query draft
- draft-only

Embase:

- Emtree-style `/exp` terms
- `ti,ab,kw` terms
- draft-only

Cochrane:

- title / abstract / keyword draft
- draft-only

CNKI / WanFang / VIP:

- Chinese keyword combinations
- title / abstract / keyword style fields
- draft-only and file-import oriented

## Governance

The service writes:

- `draft_created` for the search strategy set
- `suggestion_created` for each database query
- `edit` / `user_edited` for reviewer query edits
- `confirm` / `confirmed` for reviewer-confirmed search strategies

Confirmed strategies are separate from drafts. Confirmation does not execute search.

## Guardrails

- Requires confirmed PICO / PICOS / PECO protocol.
- No automatic online execution.
- No automatic literature import.
- No automatic screening artifact.
- No PRISMA updates.
- No Bioinformatics dependency.
- No GEO, GSE, TCGA, or GTEx output in Meta search strategy artifacts.
