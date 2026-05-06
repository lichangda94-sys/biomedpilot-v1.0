# Meta Analysis Legacy Migration Plan

## Scope

This plan turns the high-priority legacy migration candidates into active Meta-owned implementation stages. It does not authorize copying legacy directories or importing legacy modules into new active code.

## Stage 1: Active Meta Foundations

Implement small Meta-owned service foundations that preserve the useful legacy ideas without moving legacy code:

- Artifact preview and result detail lookup for report, result, and audit pages.
- Task lifecycle audit logging for future long-running Meta jobs.
- Analysis profile configuration snapshots for PICO/PECO, extraction schema, and analysis-plan reuse.

Stage 1 should not add UI controls, automatic execution, schedulers, or literature database clients.

Implemented Stage 1 foundations:

- `app/meta_analysis/services/artifact_review_service.py`
- `app/meta_analysis/services/task_lifecycle_audit_service.py`
- `app/meta_analysis/services/analysis_profile_config_service.py`
- `app/meta_analysis/services/literature_edge_case_audit_service.py`

## Stage 2: Literature Import / Dedup Edge Replacement

The current active import and duplicate review path still uses a transitional bridge to legacy `literature` parser and dedup components. That bridge should be retired only after active Meta tests identify a concrete missing behavior and an active replacement is implemented.

Candidate edge cases for future test-driven replacement:

- CSV header aliases.
- DOI and PMID cleanup.
- Publication type and clinical trial id extraction.
- Similar-title duplicate detection with year, journal, and first-author evidence.
- Completeness-based master record suggestion.
- Field-source tracing for merge preview and final merge.

Each future replacement should:

- Add a failing active Meta test first.
- Implement the smallest active Meta helper or service behavior needed.
- Avoid importing `app/meta_analysis/legacy/`.
- Remove one bridge dependency only after active parity is covered.

`LiteratureEdgeCaseAuditService` records the current candidate edge cases and proposed active tests. It is an audit aid, not a parser or dedup replacement.

## Stage 3: Workflow Integration

After Stage 1 foundations are stable:

- Surface artifact preview and result detail in Reporting / Audit / Analysis pages.
- Use task lifecycle audit summaries in future batch import, PubMed search execution, and analysis-run panels.
- Let protocol, extraction, and analysis pages save/reuse analysis profile config snapshots.

No scheduler or automatic task scanning should be added until a separate long-task design is approved.

## Stage 4: Legacy Retirement

Retire legacy bridge usage incrementally:

- Replace active literature import parser dependency.
- Replace active duplicate detection dependency.
- Keep `legacy/geo_readiness/` quarantined throughout.
- Add architecture tests only when the transitional bridge can pass them.
