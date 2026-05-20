# Meta Conflict Manual Decision Report

Generated: 2026-05-18

Scope: final manual decisions for the 6 terms that remained in `meta_conflicts_still_require_manual_review.jsonl`.

No Meta runtime, shared core, or Bioinformatics runtime files were changed.

## Final Decisions

| term | decision | guard | notes |
| --- | --- | --- | --- |
| 疱疹 | condition_candidate_only | requires_qualification=true | Broad condition label; keep candidate-only until qualified by subtype, pathogen, anatomical site, or context. |
| 结石 | condition_candidate_only | requires_anatomical_site=true | Requires anatomical site before mapping, such as kidney, gallbladder, urinary tract, or salivary gland. |
| 肥胖 | phenotype_or_risk_factor | Meta exposure; blocked_from_shared_promotion | Keep as Meta exposure/risk-factor candidate. Do not promote to shared core until disease/phenotype and exposure semantics are reconciled. |
| 脚气 | ambiguous_condition | manual_mapping_required; possible_mappings=tinea pedis/beriberi | Ambiguous Chinese term; requires context before mapping. |
| 镇静 | intervention_or_clinical_state_candidate | requires_context=true | Can describe sedation intervention/exposure or clinical state; requires context before PICO role assignment. |
| 风团 | clinical_feature_or_adverse_event_candidate | related_disease=urticaria | Clinical feature/adverse-event candidate related to urticaria; do not map directly as disease without context. |

## Batch Status

`meta_mapping_conflicts_top_200.jsonl` can now be treated as processed for this review pass:

- 194 rows were already routed into symptom, TCM future-scope, event/adverse-outcome, or condition candidate-only buckets.
- The remaining 6 manual-review rows now have explicit final decisions in `meta_conflict_manual_decisions.jsonl`.
- No row from this conflict batch should be promoted directly into Meta runtime or shared core without a later explicit implementation stage.

Next review batch: `data/medical_terms/review_batches/meta/meta_disambiguation_top_200.jsonl`.
