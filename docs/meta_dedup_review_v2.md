# Meta Dedup Review v2

Status: Developer Preview / testing.

## Scope

Dedup Review v2 is a reviewer-confirmed duplicate review layer built on `LiteratureLibraryService`. It reads normalized literature records, creates duplicate groups, assigns risk levels, prepares merge previews, records reviewer decisions, and can export a separate deduplicated literature set.

It does not mutate the source literature library, delete records silently, auto-merge records, start title/abstract screening, or advance PRISMA counts.

## Files

- `deduplication/duplicate_groups_v2.json`
- `deduplication/dedup_decisions_v2.json`
- `deduplication/deduplicated_literature_v2.json`

## Schema Versions

- Review queue: `meta_duplicate_review_queue.v2`
- Duplicate group: `meta_duplicate_group.v2`
- Decision: `meta_dedup_decision.v2`
- Decision log: `meta_dedup_decision_log.v2`
- Deduplicated set: `meta_deduplicated_literature_set.v2`

## Risk Levels

- Red: `高度重复`
- Yellow: `疑似重复`
- Gray: `轻度疑似`
- Green: `暂未发现重复`

Green is not written as a duplicate group; it means no duplicate rule matched for that record.

## Matching Rules

Red:

- PMID exact
- DOI exact or DOI string variant
- PMCID cross-check exact
- ClinicalTrials ID exact
- normalized title exact

Yellow:

- title + first author + year

Gray:

- title fuzzy + journal + author

## Reviewer Decisions

Supported decisions:

- `merge`
- `set_master_record`
- `keep_both`
- `mark_not_duplicate`
- `exclude_duplicate`
- `skip`
- `undo`

Every decision is written to audit and research governance as a human confirmation for `dedup_merge`. Merge decisions require a merge preview. The source literature library is not modified by a decision.

## Merge Preview

Merge preview records:

- merged record candidate
- `merged_from_record_ids`
- field source mapping
- provenance sources
- field-difference warnings

The preview is a reviewer aid only. It is not applied unless the reviewer confirms a merge decision.

## Guardrails

- No automatic deletion.
- No automatic merge.
- No automatic screening artifact.
- No automatic PRISMA updates.
- No Bioinformatics, GEO, GSE, TCGA, or GTEx dependency.
