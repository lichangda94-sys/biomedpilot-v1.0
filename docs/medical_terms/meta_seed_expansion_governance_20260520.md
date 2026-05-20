# Meta Seed Expansion Governance

Date: 2026-05-20

## Policy

Future Meta seed expansion must remain manually curated. Batch size should be 50-100 terms and must not auto-promote external Chinese corpus candidates or review-batch candidates into runtime seed files.

## Required Fields

Every seed must include `concept_id`, `preferred_label_en`, `zh_terms`, `concept_type`, `pico_roles`, query guard fields, extraction flags, and review status.

## Guard Rules

- Outcomes default to `query_expansion_allowed=conditional` and require population/disease pairing.
- Effect/statistical terms do not enter topic expansion.
- Study-design terms are `filter_only=true`.
- Research-intent terms do not enter query expansion.

## Required Batch Outputs

- `seed_diff_report`
- mapping diff report
- query guard test result
- scope isolation test result

## Prohibited Promotion

Do not auto-promote rows from external Chinese corpus candidates, candidate-only pools, TCM future-scope pools, condition/symptom long-tail queues, or unresolved English mapping queues.
