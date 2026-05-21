# Meta Seed Expansion Batch 2 Audit 20260519

Generated: 2026-05-19

Scope: audit of manually curated Meta seed expansion batch 2. This stage extends the additive Meta seed layer and does not promote external candidate pools automatically.

## Summary

Batch 2 added 120 curated seed terms.

Total seed terms after expansion: 190.

| category | total after batch 2 |
| --- | ---: |
| disease / population | 50 |
| exposure | 35 |
| intervention | 30 |
| outcome | 37 |
| effect / statistical term | 14 |
| study design | 12 |
| research intent | 12 |

Mapping files after regeneration:

- `mesh_mappings.json`: 152 disease/exposure/intervention/outcome entries.
- `pubmed_free_text_mappings.json`: 152 disease/exposure/intervention/outcome entries.
- `emtree_mappings.json`: 190 entries, all retained as `emtree_review_status=needs_review`.

## Curated Expansion Policy

The 120 new entries were manually selected common Meta-analysis seed concepts across clinical diseases, exposures, interventions, outcomes, effect/statistical terms, study designs, and research intents.

No row was auto-promoted from:

- external Chinese corpus candidate pools,
- `meta_priority_*` candidate pools,
- `meta_english_mapping_*` candidate pools,
- `meta_outcome_*` review queues.

## Guard Status

Guard behavior remains unchanged:

- Effect/statistical terms do not enter PubMed topic query expansion.
- Research-intent terms do not enter PubMed topic query expansion.
- Outcomes remain `query_expansion_allowed=conditional` and require population/disease context.
- Study-design terms remain `filter_only=true`.

## Batch 2 Smoke Examples

New batch 2 seeds verified by tests:

- `meta_disease:heart_failure`
- `meta_exposure:mediterranean_diet`
- `meta_intervention:sglt2_inhibitor`
- `meta_outcome:objective_response_rate`

Chinese matching smoke:

```text
SGLT2抑制剂治疗心力衰竭的安全性
```

Expected seed concepts:

- `meta_disease:heart_failure`
- `meta_intervention:sglt2_inhibitor`

Expected intent:

- `safety_outcome_meta`

## Boundaries

No protected runtime/shared files were changed:

- `data/medical_terms/mini_medical_terms_index.json`
- `data/medical_terms/zh_term_overrides.json`
- `data/medical_terms/bioinformatics/`
- `app/bioinformatics/`
- existing Meta runtime JSON files under `data/medical_terms/meta_analysis/meta_en_*`
- `data/medical_terms/meta_analysis/meta_research_intent_terms.json`
- `data/medical_terms/meta_analysis/meta_zh_to_en_concept_terms.json`

The expanded seed layer still does not support:

- Chinese database retrieval.
- Chinese PDF extraction.
- Automatic writes to formal extraction tables.
- Automatic Emtree guessing.

## Verification

```bash
git diff --check
python3 -m pytest tests/shared/test_meta_seed_terms.py -q
```
