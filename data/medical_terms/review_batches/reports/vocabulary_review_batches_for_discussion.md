# Vocabulary Review Batches For Discussion

Generated: 2026-05-18

## Purpose

This stage turns the previous 47,000+ Meta candidates and Bioinformatics audits into bounded review batches for human discussion.

## Bioinformatics

- GEO missing: 28 -> data/medical_terms/review_batches/bioinformatics/geo_core_missing_review_batch.jsonl
- GTEx needs_review: 5 -> data/medical_terms/review_batches/bioinformatics/gtex_needs_review_batch.jsonl
- TCGA status: complete

## Meta

- Approved runtime review entries: 11 -> data/medical_terms/review_batches/meta/meta_approved_runtime_review_batch.jsonl
- Shared promotion candidates: 4 -> data/medical_terms/review_batches/meta/meta_shared_promotion_review_batch.jsonl
- Priority review top batch: 300 -> data/medical_terms/review_batches/meta/meta_priority_review_batch_top_300.jsonl
- Mapping conflicts top batch: 200 -> data/medical_terms/review_batches/meta/meta_mapping_conflicts_top_200.jsonl
- Disambiguation top batch: 200 -> data/medical_terms/review_batches/meta/meta_disambiguation_top_200.jsonl
- English mapping top batch: 300 -> data/medical_terms/review_batches/meta/meta_english_mapping_top_300.jsonl
- Auto reject candidates: 35
- Evidence-only optimized candidates: 1385
- Future-scope optimized candidates: 7

## Recommended Discussion Order

1. GEO core missing 28
2. GTEx needs_review 5
3. Meta approved runtime 11
4. Shared promotion candidates 4
5. Meta mapping conflicts top 200
6. Meta disambiguation top 200
7. Meta English mapping top 300
8. Meta priority review top 300

## Scope Guard

This stage does not modify shared core, Bioinformatics runtime, Meta runtime, desktop entry points, packaging, or business workflows.
