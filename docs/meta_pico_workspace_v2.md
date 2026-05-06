# Meta PICO / PICOS / PECO Workspace v2

Status: Developer Preview / testing.

## Scope

PICO Workspace v2 turns the Chinese research-question entry point into an auditable draft and confirmation workspace. It generates a PICO, PICOS, or PECO draft from the user question, lets reviewer edits create a new draft version, and writes a separate confirmed protocol only after explicit reviewer confirmation.

It does not execute PubMed, create a final search strategy, start screening, or update PRISMA counts.

## Active Service

- `app/meta_analysis/services/pico_workspace_service.py`
- Shared language input: `build_search_translation_draft(target_context="meta_analysis")`
- Shared output is filtered through the Meta search context so GEO, GSE, TCGA, and GTEx terms are not surfaced in Meta protocol artifacts.

## Artifacts

- `protocol/pico_workspace_draft.json`
- `protocol/pico_workspace_draft_versions.json`
- `protocol/pico_workspace_confirmed.json`
- `protocol/pico_workspace_confirmed_versions.json`
- `protocol/pico_workspace_manifest.json`

## Schema Versions

- Draft: `meta_pico_protocol_draft.v2`
- Confirmed protocol: `meta_confirmed_protocol.v2`
- Manifest: `meta_pico_workspace_manifest.v2`

## Draft Fields

Drafts record:

- original research question and detected language
- `pico_mode`: `pico`, `picos`, or `peco`
- population
- intervention
- exposure
- comparator
- outcome
- study design
- context, disease, and synonym terms
- exclusion scope
- meta-type candidates
- warnings
- governance and audit references

Meta-type candidates are suggestions only. `network_meta_coming_soon` remains a candidate marker, not an implemented analysis path.

## Confirmation

Confirmed protocols record:

- source draft id
- reviewer and timestamp
- confirmed PICO/PICOS/PECO fields
- confirmed meta-analysis type
- user notes
- version
- `locked_for_search_strategy`

Confirmed protocols are separate from drafts. A draft is never promoted to final by system action alone.

## Governance

The service writes:

- `draft_created` for PICO/PICOS/PECO drafts
- `suggestion_created` for meta-type candidates
- `edit` / `user_edited` for reviewer draft edits
- `confirm` / `confirmed` for reviewer-confirmed protocols

All governance events also write Meta audit events through the research governance service.

## Guardrails

- No automatic final PICO/PICOS/PECO confirmation.
- No PubMed execution.
- No Web of Science, Embase, or CNKI execution.
- No title/abstract screening artifact.
- No PRISMA updates.
- No Bioinformatics dependency.
- No GEO, GSE, TCGA, or GTEx output in Meta protocol artifacts.
