# Meta Candidate Optimization Report

Generated: 2026-05-18

- raw_candidates_total: 88629
- normalized_candidates_total: 47357
- review_queue_total: 47362
- auto_reject_total: 35

## Rules

High-value batches prioritize mapped disease, exposure, intervention, outcome, effect measure, study design, and research intent terms, then short stable phrases and multi-source terms.

Conflict batches prioritize cross-label terms, known ambiguous review terms, and short broad terms.

Disambiguation and English-mapping batches prioritize terms likely to become runtime candidates after human review.

Auto-reject candidates include single-character non-abbreviations, generic medical words, colloquial terms, long sentence-like strings, Chinese PDF section terms, and out-of-scope TCM terms.

## Top Batch Files

- data/medical_terms/review_batches/meta/meta_priority_review_batch_top_300.jsonl
- data/medical_terms/review_batches/meta/meta_mapping_conflicts_top_200.jsonl
- data/medical_terms/review_batches/meta/meta_disambiguation_top_200.jsonl
- data/medical_terms/review_batches/meta/meta_english_mapping_top_300.jsonl

## Remaining Manual Review Reason

Most external corpus rows still lack reliable English preferred labels, MeSH/Emtree candidates, and unambiguous PICO/PECO roles.
