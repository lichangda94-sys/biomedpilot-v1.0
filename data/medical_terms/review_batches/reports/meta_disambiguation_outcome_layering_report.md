# Meta Disambiguation Outcome Layering Report

Generated: 2026-05-19

Scope: `data/medical_terms/review_batches/meta/meta_disambiguation_top_200.jsonl`.

This batch is an outcome-layering review queue, not a Meta outcome runtime input. No Meta runtime, shared core, or Bioinformatics runtime files were changed.

## Layering Result

| output file | rows | layer policy |
| --- | ---: | --- |
| `meta_outcome_symptom_feature_candidates.jsonl` | 34 | Patient-reported symptom/sign candidates. Candidate-only; requires population or disease context. |
| `meta_outcome_clinical_feature_candidates.jsonl` | 42 | Clinical feature or phenotype candidates. Candidate-only; requires site, severity, disease, or measurement context. |
| `meta_outcome_condition_candidate_only.jsonl` | 62 | Diagnosis or condition candidates. Do not map directly as Meta outcome runtime. |
| `meta_outcome_adverse_event_candidates.jsonl` | 21 | Event, complication, poisoning, bleeding, injury, or drug-related outcome candidates. Requires intervention or exposure context. |
| `meta_outcome_functional_impairment_candidates.jsonl` | 27 | Functional impairment or neurologic/sensory deficit candidates. Requires scale, outcome definition, or disease context. |
| `meta_outcome_tcm_future_scope_candidates.jsonl` | 13 | Likely TCM syndrome/pattern terms. Deferred out of current Meta runtime scope. |
| `meta_outcome_still_requires_manual_review.jsonl` | 1 | Still ambiguous after layering; requires manual qualification. |

## Guardrails

- Every layered row has `runtime_promotion_allowed=false`.
- Every layered row has `query_expansion_allowed=false`.
- Every layered row has `requires_context_rule=true`.
- These files are review-batch derivatives only; they must not be consumed as Meta runtime seed files.

## Still Manual

`结节` remains in `meta_outcome_still_requires_manual_review.jsonl` because it is a short ambiguous focus term that can mean a finding, lesion, disease component, imaging feature, or endpoint depending on context.

## Next Step

Use the layered outputs to decide which rows need English mapping, PICO role clarification, or future-scope deferral. Do not promote this batch directly into Meta outcome runtime.
