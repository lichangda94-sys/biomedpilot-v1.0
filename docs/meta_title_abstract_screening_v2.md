# Meta Title / Abstract Screening v2

Stage M8 adds the engineering foundation for title / abstract screening, while preserving the research-governance rule that final inclusion and exclusion decisions must be made by a reviewer.

## Active Service

- Service: `app/meta_analysis/services/title_abstract_screening_v2_service.py`
- Queue artifact: `screening/title_abstract_queue_v2.json`
- Reviewer decisions: `screening/title_abstract_decisions_v2.json`
- Compatibility decisions for downstream testing services: `screening/screening_decisions.json`
- AI suggestion queue: `screening/title_abstract_ai_suggestions_v2.json`

## Source Priority

1. `deduplication/deduplicated_literature_v2.json`
2. `literature/literature_records.json`

If the deduplicated set is missing, the service falls back to the normalized literature library and records a warning.

## Governance Rules

- Queue creation is preview-only. It writes no final include / exclude decision.
- AI/model output is stored as suggestion only and cannot overwrite final screening decisions.
- Reviewer decisions support `include`, `exclude`, `uncertain`, and `needs_review`.
- `exclude` requires a structured exclusion reason.
- Reviewer decisions write Meta audit and research-governance events.
- PRISMA screened / excluded / included numbers should be based on saved reviewer decision records, not on queue creation.

## Current Limitations

- Multi-reviewer adjudication is not implemented.
- Keyboard workflow and batch marking remain UI skeleton work.
- Exclusion Criteria Library v1 is planned next; M8 carries only a default reason list.
- No automatic screening, no automatic full-text handoff, and no automatic PRISMA advancement from suggestions or queue creation.
