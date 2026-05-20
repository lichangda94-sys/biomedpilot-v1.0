# Meta Scoped Mirror From Shared Core

Date: 2026-05-20

## Scope

This is Phase S3 of the shared core cleanup plan.

Implemented artifacts:

- `data/medical_terms/meta_analysis/meta_migrated_from_shared_terms.json`
- `data/medical_terms/meta_analysis/legacy_meta_compatibility_map.json`
- `data/medical_terms/review_reports/meta_scoped_mirror_conflicts.jsonl`
- `tests/shared/test_meta_scoped_mirror_from_shared.py`

Runtime boundaries:

- `mini_medical_terms_index.json` was not edited.
- `zh_term_overrides.json` was not edited.
- Existing Meta seed files were not edited.
- Bioinformatics vocabularies were not edited.
- Loader routing was not changed.
- No PubMed retrieval, PDF extraction, or business workflow was added.

## Mirror Result

Mirrored terms:

- 48 canonical Meta-scoped concepts.
- 49 legacy shared concept IDs represented, because two `overall survival` legacy IDs are consolidated into one canonical target.

Excluded from Meta mirror:

- `gene expression profiling`

Reason:

- It is an omics/data-modality term and should route to Bioinformatics scoped vocabulary or remain a manual routing item.

Conflict/manual routing output:

`data/medical_terms/review_reports/meta_scoped_mirror_conflicts.jsonl`

## Duplicate Handling

`overall survival` existed as:

- `mini:meta_outcomes_core`
- `mini:meta_analysis_overall_survival`

Both are mapped to:

`meta_outcome:overall_survival`

The mirror intentionally does not copy broad synonyms from `mini:meta_outcomes_core` such as `risk`, `odds ratio`, `hazard ratio`, `sensitivity`, or `diagnostic accuracy`, because those are separate Meta concepts.

## Special Context Terms

`survival data` is mirrored as:

`meta_data_context:survival_data`

Guard behavior:

- `query_expansion_allowed=false`
- `standalone_search_allowed=false`
- `requires_qualified_term=true`

It is a data/extraction context term only. It is not an `overall survival` synonym.

## Generic Non-Expanding Terms

The following are mirrored but remain non-expanding and non-standalone:

- `risk`
- `control`
- `patient`
- `population`
- `review`
- `setting`

These support classification, profile hints, PICO labeling, or filtering, but not PubMed topic expansion.

## Compatibility Map

`legacy_meta_compatibility_map.json` is data-only in this phase.

Each mapping keeps:

- `legacy_concept_ids`
- `new_concept_id`
- `scope=meta_analysis`
- `status=mirrored_to_meta_scoped`
- `shared_core_active=true`
- `planned_shared_status=deprecated_in_shared_after_loader_routing`

S4 will decide loader routing. S3 does not make the compatibility map active.

## Validation

Validation completed:

```bash
git diff --check
# pass
python3 -m pytest tests/shared/test_meta_scoped_mirror_from_shared.py -q
# 6 passed
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

## Next Step

Do not proceed to shared cleanup or deletion. The next phase should be S4 loader routing / compatibility, after reviewing whether the S3 compatibility map should become active for Meta scope only.
