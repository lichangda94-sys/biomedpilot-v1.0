# Meta Analysis Research Governance

Status: Developer Preview / testing governance baseline.

## Principle

Meta Analysis development follows a two-track rule:

- Codex may build engineering substrate: schema, service, adapter, manifest, audit, UI skeleton, preview, validation, report draft, figure output, reproducibility package, and boundary tests.
- Research judgment remains human-confirmed: final PICO/PICOS/PECO, final search strategy, literature inclusion, dedup merge, title/abstract screening, full-text screening, final extraction values, quality scores, analysis plan, medical interpretation, and final discussion/conclusion text.

AI/model/service output is always a draft or suggestion until a reviewer accepts, rejects, edits, or confirms it. PRISMA counts must come from real workflow records, not from model text or PubMed candidate previews.

## Status Vocabulary

- `draft`: system-generated draft, not confirmed.
- `suggested`: AI/model/service suggestion, not final data.
- `user_accepted`: reviewer accepted a suggestion.
- `user_rejected`: reviewer rejected a suggestion.
- `user_edited`: reviewer edited a suggestion or draft.
- `confirmed`: reviewer explicitly confirmed the artifact for downstream consumption.

Only `confirmed` artifacts may be consumed as final research decisions. `user_accepted` and `user_edited` are review events and can still require an explicit confirmation step when the target is a final research artifact.

## Audit Contract

Research-governance events are written to:

- `audit/research_governance_log.jsonl`
- `audit/audit_log.jsonl` as `research_governance_event`

Each event records:

- `actor`
- `action`
- `target_type`
- `target_id`
- `before`
- `after`
- `source_suggestion_id`
- `created_at`

Automatic generation is recorded only as `draft_created` or `suggestion_created`. It must not be recorded as a final judgment.

## Current Guardrails

- Protocol draft saves record `final_pico` as `draft`.
- Confirmed protocol saves record `final_pico` as `confirmed`.
- Search strategy draft saves record `final_search_strategy` as `draft`.
- PubMed confirmed execution records `final_search_strategy` as `confirmed`, but the execution report remains candidate preview only.
- PubMed candidate preview records `literature_inclusion` candidates as `draft`; selected and rejected candidates record reviewer `accept` / `reject`, and the selected-candidate import batch records handoff `confirm`.
- AI suggestions record `suggestion_created`; reviewer accept/reject/edit actions create separate governance events.
- Accepted AI suggestions still write only to the AI application log and do not overwrite formal screening, extraction, analysis, quality, or report artifacts.
- PubMed search execution reports are excluded from PRISMA evidence collection so candidate previews do not advance PRISMA.

## Stage Constraints

M2/M3:

- PubMed confirmed execution results generate literature candidates preview only.
- Unselected PubMed candidates cannot enter the normalized literature library.
- Selected candidates must keep provenance and handoff audit.
- Imported candidates may enter the dedup queue, but must not enter screening automatically.
- PubMed handoff must not create screening artifacts or PRISMA included/excluded counts.

M4-M25:

- Dedup merge, screening, full-text decisions, extraction, quality assessment, and analysis plan require reviewer confirmation tables or review queues.
- AI/model output can only become final after accept/reject/edit plus the required confirmation for that target.
- Report discussion/conclusion text is draft-only unless a reviewer explicitly confirms final wording.
