# Shared Core Pollution Manual Review Required

Date: 2026-05-20

Manual review file:

`data/medical_terms/review_reports/shared_core_pollution_manual_review.jsonl`

## Summary

Phase S1 generated 50 manual-review rows.

Primary reasons:

- Legacy `mini:*` concept ids are referenced by current code/docs/tests.
- Broad Meta PICO labels need target-scope decisions before migration.
- Ambiguous terms such as `survival data` may affect both Bioinformatics data assets and Meta outcome workflows.

## Decision

No automatic migration, deprecation, or deletion was performed for these rows.

Phase S3 should not proceed until these rows are reviewed or explicitly accepted for staged mirror-only migration.
