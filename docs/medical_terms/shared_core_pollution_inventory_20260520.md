# Shared Core Pollution Inventory

Date: 2026-05-20

## Scope

This is Phase S1 of the shared core cleanup plan. It inventories suspected shared core pollution but does not modify runtime vocabulary files.

Generated artifacts:

- `scripts/inventory_shared_core_pollution.py`
- `data/medical_terms/review_reports/shared_core_pollution_inventory.json`
- `data/medical_terms/review_reports/shared_core_pollution_manual_review.jsonl`
- `docs/medical_terms/shared_core_pollution_inventory_20260520.md`
- `tests/shared/test_shared_core_pollution_inventory.py`

Runtime files not modified:

- `data/medical_terms/mini_medical_terms_index.json`
- `data/medical_terms/zh_term_overrides.json`
- `data/medical_terms/meta_analysis/*`
- `data/medical_terms/bioinformatics/*`

## Method

The inventory script scans `mini_medical_terms_index.json` and classifies suspicious terms into:

- `meta_outcome`
- `meta_effect_measure`
- `meta_statistical_term`
- `meta_study_design`
- `meta_research_intent`
- `meta_quality_assessment_tool`
- `meta_reporting_guideline`
- `meta_database_query_term`
- `bioinformatics_technical_term`
- `ambiguous_or_qualified_term`
- `needs_manual_review`

It also checks whether a suspicious shared concept appears to already exist in Meta seed terms and whether the legacy `mini:*` concept id is referenced by current code/docs/tests.

## Results

Inventory summary:

- Total suspected pollution terms: 177
- Manual review required: 50

Category counts:

- `ambiguous_or_qualified_term`: 1
- `bioinformatics_technical_term`: 65
- `meta_effect_measure`: 27
- `meta_outcome`: 26
- `meta_research_intent`: 1
- `meta_study_design`: 15
- `needs_manual_review`: 42

Representative terms:

- Meta outcome/effect/study-design: `overall survival`, `progression-free survival`, `hazard ratio`, `odds ratio`, `cohort study`, `randomized controlled trial`.
- Bioinformatics technical: `gene expression profiling`, `bulk RNA-seq`, `ATAC-seq`, `cell type annotation`.
- Ambiguous: `survival data`.
- Needs manual review: broad PICO labels such as `population`, `patient`, `intervention`, `comparator`, and `outcome`.

## Manual Review

Manual review file:

`data/medical_terms/review_reports/shared_core_pollution_manual_review.jsonl`

Manual review is required when:

- The term is ambiguous or qualified-only.
- The term has legacy references in code/docs/tests.
- The term is a broad PICO label with unclear target scope.
- Automated migration could break legacy Meta compatibility.

## Decisions

No migration was performed in this phase.

No terms were removed, deprecated, or marked inactive in shared core.

Recommended next step:

Review the 50 manual-review rows before Phase S3. Phase S3 should mirror only confirmed Meta-scoped terms into `meta_migrated_from_shared_terms.json` and build a compatibility map, without deleting shared core rows.

## Validation

Completed validation:

```bash
git diff --check
# pass
python3 -m pytest tests/shared/test_shared_core_pollution_inventory.py -q
# 5 passed
python3 -m pytest tests/shared/test_medical_terms_integration_audit.py -q
# 5 passed
python3 -m pytest tests/shared/test_meta_seed_terms.py -q
# 9 passed
python3 -m pytest tests/shared/test_query_intelligence_service.py -q
# 21 passed
python3 -m pytest tests/meta_analysis -q
# 17 passed
python3 -m pytest tests/bioinformatics -q
# 238 passed
python3 -m app.main --smoke-test
# pass
```
