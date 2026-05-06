# Meta Quality Assessment Framework v1

## Status

Stage M15 adds a Developer Preview / testing quality assessment framework for Meta Analysis. It is an engineering scaffold for reviewer-driven quality assessment, not an automated risk-of-bias or GRADE engine.

## Implemented Scope

- `QualityAssessmentService` now exposes v1 quality assessment records, summaries, JSON/CSV exports, and report-readable summary payloads.
- `app/meta_analysis/quality/tool_registry.py` includes ROB2, ROBINS-I, Newcastle-Ottawa Scale / NOS, QUADAS-2, JBI prevalence checklist, AHRQ cross-sectional checklist, Cochrane RoB generic, and GRADE summary placeholder.
- Tool recommendations can be generated from Meta type and study design, but all recommendations are `suggested` and require reviewer confirmation.
- Study-level quality records support domain ratings, domain notes, reviewer notes, draft save, and `completed_by_user`.
- Draft save and reviewer completion write audit events and research governance events.
- GRADE output is limited to a placeholder payload with `certainty=not_assessed` and `auto_grade_generated=false`.
- The Meta quality page state and desktop workspace panel expose the testing boundary: no automatic scoring, no automatic GRADE conclusion, no analysis-ready dataset, no statistics run, and no PRISMA advancement.

## Data Artifacts

- `quality/quality_assessment_records_v1.json`
- `quality/quality_assessment_summary_v1.json`
- `quality/quality_assessment_v1_export.json`
- `exports/quality_assessment_v1.csv`
- `audit/audit_log.jsonl`
- `audit/research_governance_log.jsonl`

## Governance Rules

- `draft_created` is used when a quality assessment draft is saved.
- `confirm` is used when a reviewer explicitly marks an assessment as `completed_by_user`.
- Tool recommendations and helper summaries must remain suggestions. They must not overwrite reviewer-entered quality ratings.
- GRADE placeholder output must not be presented as a final evidence certainty profile.

## Explicit Non-goals

- No automatic risk-of-bias scoring.
- No automatic GRADE certainty judgement.
- No multi-reviewer adjudication workflow yet.
- No analysis-ready dataset creation.
- No statistical analysis trigger.
- No PRISMA count update.
- No Bioinformatics import or GEO/GSE/TCGA/GTEx dependency.

## Tests

- `tests/meta_analysis/test_quality_assessment_framework_v1.py`
- `tests/meta_analysis/test_stage_ab9_quality_assessment_ui.py`
- `tests/architecture`

These tests cover tool recommendations, manual save/complete, audit/governance, GRADE placeholder behavior, export payloads, report summary access, UI state boundaries, and Meta/Bio boundary protection.
