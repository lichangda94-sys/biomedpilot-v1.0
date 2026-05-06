# Meta Statistics Engine v2

## Status

Stage M17 adds a Developer Preview / testing-level statistics engine for Meta Analysis. It is not production-grade statistical software and must not be presented as final medical interpretation.

## Required Entry

The engine refuses to run unless `analysis/analysis_plan_confirmed_v1.json` exists. The confirmed analysis plan is the only formal M17 entrypoint.

The engine does not directly consume extraction rows as an independent trigger. It resolves only the effect rows selected by the reviewer-confirmed analysis plan.

## Supported Testing-Level Effect Types

- Binary: OR / RR / RD
- Continuous: MD / SMD
- Survival: HR
- Prevalence / incidence proportion-style pooling
- Correlation / Fisher z-style inputs
- Diagnostic 2x2: DOR / sensitivity / specificity / PLR / NLR basic testing calculations
- Fixed and random effects
- Heterogeneity: Q / I2 / tau2
- Subgroup descriptive summaries
- Leave-one-out sensitivity output
- Egger and funnel data output

## Artifacts

- `analysis/runs/<analysis_run_id>.json`
- `analysis/results/<analysis_run_id>_result.json`
- `analysis/analysis_manifest.json`
- `logs/analysis/analysis_audit.jsonl`
- `audit/audit_log.jsonl`
- `audit/research_governance_log.jsonl`

## Schema Versions

- Analysis run: `meta_statistics_analysis_run.v2`
- Standardized result: `meta_statistics_standardized_result.v2`
- Manifest: `meta_statistics_analysis_manifest.v2`
- Analysis audit: `meta_statistics_analysis_audit.v2`

## Standardized Result Object

The result object includes:

- pooled effect, CI, p value, z value
- heterogeneity Q / p / I2 / tau2
- study-level results
- subgroup results
- leave-one-out sensitivity results
- publication-bias result placeholders / Egger / funnel data
- diagnostics
- explicit testing-level notice

## Input Validation

M17 validates:

- confirmed analysis plan existence
- included effect rows
- effect-row validation status
- effect measure consistency
- adjusted/unadjusted mixing
- outcome/timepoint consistency
- study count for Egger / funnel guidance
- zero-cell correction need
- diagnostic 2x2 completeness

## Governance

M17 writes research governance and audit events for:

- analysis run requested
- analysis run executed
- analysis result generated

The generated result remains a testing-level result object. It is not automatically marked reviewed, final, or medically interpreted.

## Explicit Boundaries

- No run without confirmed analysis plan.
- No extraction record modification.
- No quality assessment modification.
- No PRISMA update.
- No medical conclusion, discussion, or final interpretation.
- No production-grade statistical claim.
- No Bioinformatics import or GEO/GSE/TCGA/GTEx dependency.

## Tests

- `tests/meta_analysis/test_meta_statistics_engine_v2.py`
- `tests/architecture`
- `tests/ui/test_meta_analysis_workflow_pages.py`
