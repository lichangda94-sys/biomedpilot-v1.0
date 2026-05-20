# Loader Routing / Compatibility

Date: 2026-05-20

## Scope

This is Phase S4 of the shared core cleanup plan. It adds a scope-aware vocabulary loading utility and legacy Meta compatibility resolution.

Implemented behavior:

- `load_terms(scope="shared_core")`
- `load_terms(scope="meta_analysis")`
- `load_terms(scope="bioinformatics")`
- `resolve_legacy_concept_id(concept_id, scope=...)`
- `find_terms(query, scope=...)`

Runtime boundaries:

- `mini_medical_terms_index.json` was not edited.
- `zh_term_overrides.json` was not edited.
- Bioinformatics scoped vocabulary files were not edited.
- Existing Meta seed files were not edited.
- Business pages and workflow execution were not changed.
- No retrieval or PDF feature was added.
- S5 cleanup was not performed.

## Routing Model

Meta Analysis scope loads:

- Shared core terms, excluding legacy Meta scoped shared rows and shared data-modality rows.
- Existing Meta seed terms.
- `meta_migrated_from_shared_terms.json`.
- `legacy_meta_compatibility_map.json` for legacy ID resolution.

Bioinformatics scope loads:

- Shared core terms, excluding legacy Meta scoped shared rows.
- Bioinformatics scoped vocabularies.
- It does not load `meta_migrated_from_shared_terms.json`.
- It does not activate `legacy_meta_compatibility_map.json` mappings.

Shared-only scope loads:

- Shared core terms only.
- S5 cleanup is still pending, so this scope does not edit or delete shared core data.

## Compatibility Behavior

Confirmed mappings:

- `mini:meta_outcomes_core` -> `meta_outcome:overall_survival`
- `mini:meta_analysis_overall_survival` -> `meta_outcome:overall_survival`
- `mini:study_design_core` -> `meta_study_design:randomized_controlled_trial`
- `mini:meta_analysis_quadas_2` -> `meta_quality_tool:quadas_2`

Meta term resolution:

- `overall survival` resolves to `meta_outcome:overall_survival`.
- `hazard ratio` resolves from existing Meta seed terms as `meta_effect:hazard_ratio`.
- `randomized controlled trial` resolves to `meta_study_design:randomized_controlled_trial`.
- `QUADAS-2` resolves to `meta_quality_tool:quadas_2`.

Bioinformatics isolation:

- Bioinformatics does not activate Meta migrated terms or legacy Meta compatibility mappings.
- Bioinformatics still loads scoped terms such as `TPM`, `FPKM`, `raw counts`, `count matrix`, GTEx terms, GEO scoped stop terms, and platform annotation terms.

## Special Cases

`survival data`

- Resolves in Meta as `meta_data_context:survival_data`.
- Does not resolve as `overall survival`.
- Remains non-query-expanding and non-standalone.

`gene expression profiling`

- Does not enter Meta migrated compatibility.
- Does not appear as a Meta active scoped term.
- Remains available through Bioinformatics/shared data-modality routing.

## Validation

Validation completed:

```bash
git diff --check
# pass
python3 -m pytest tests/shared/test_medical_terms_scope_routing.py -q
# 6 passed
python3 -m pytest tests/shared/test_meta_scoped_mirror_from_shared.py -q
# 6 passed
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

## Next Step

Do not delete or mark inactive shared core rows yet. S5 should be a separate cleanup decision stage after this routing layer is reviewed.
