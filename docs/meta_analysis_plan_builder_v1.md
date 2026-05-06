# Meta Analysis Plan Builder v1

## Status

Stage M16 adds a Developer Preview / testing analysis plan builder for Meta Analysis. It creates draft and reviewer-confirmed analysis plan artifacts only. It does not run statistics and does not generate medical conclusions.

## Inputs

- Confirmed PICO / PICOS / PECO protocol: `protocol/pico_workspace_confirmed.json`
- Extraction schema registry defaults from `ExtractionSchemaRegistryV1Service`
- Manual extraction effect rows: `extraction/extraction_effect_rows.json`
- Quality assessment summary: `quality/quality_assessment_summary_v1.json`

## Artifacts

- `analysis/analysis_plan_draft_v1.json`
- `analysis/analysis_plan_draft_versions_v1.json`
- `analysis/analysis_plan_confirmed_v1.json`
- `analysis/analysis_plan_confirmed_versions_v1.json`
- `analysis/analysis_plan_manifest_v1.json`
- `audit/audit_log.jsonl`
- `audit/research_governance_log.jsonl`

## Schema Versions

- Draft: `meta_analysis_plan_draft.v1`
- Confirmed plan: `meta_confirmed_analysis_plan.v1`
- Manifest: `meta_analysis_plan_manifest.v1`

## Default Draft Logic

- Binary comparative Meta: OR / RR / RD with random-effects default and continuity correction.
- Continuous Meta: MD / SMD with random-effects default.
- Survival Meta: HR on log scale.
- Prevalence / incidence Meta: proportion pooling with logit transformation.
- Diagnostic 2x2 Meta: sensitivity / specificity / DOR basic 2x2 placeholder; bivariate / HSROC remains not implemented.
- Correlation Meta: Fisher z transformation.
- Dose-response Meta: placeholder / coming soon when the engine is not ready.

## Warnings

The draft builder can warn on:

- missing effect rows
- missing required fields
- multiple primary effect candidates in one study unit
- mixed effect measures
- adjusted and unadjusted effects mixed together
- inconsistent outcome names or timepoints
- incomplete quality assessment
- fewer than 10 studies for Egger / funnel plot planning

## Governance

- `analysis_plan draft_created`
- `analysis_plan user_edited`
- `analysis_plan confirmed`
- effect-row candidate suggestion events for selected/excluded candidates
- effect-row candidate accept/reject events when a plan is confirmed

## Explicit Boundaries

- No automatic analysis-plan confirmation.
- No analysis-ready dataset creation.
- No statistical analysis run.
- No final analysis result creation.
- No PRISMA update.
- No medical interpretation, discussion, or conclusion generation.
- No Bioinformatics import or GEO/GSE/TCGA/GTEx dependency.

## Tests

- `tests/meta_analysis/test_analysis_plan_builder_v1.py`
- `tests/architecture`
- `tests/ui/test_meta_analysis_workflow_pages.py`
