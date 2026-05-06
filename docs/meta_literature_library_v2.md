# Meta Literature Library v2

Status: Developer Preview / testing.

## Scope

The normalized literature library is the active Meta Analysis data layer for imported references. It supports current PubMed candidate handoff plus NBIB, RIS, and CSV import bridges. It is designed to accept future WOS, Zotero, EndNote, Embase, CNKI, Wanfang, and VIP adapters without changing downstream workflow contracts.

This stage does not add new online database execution, screening, automatic dedup merge, or PRISMA advancement.

## Files

- `literature/literature_records.json`
- `literature/import_batches.json`
- `literature/library_manifest.json`
- `audit/literature_record_audit.jsonl`

## Schema Versions

- Library: `meta_literature_library.v2`
- Record: `meta_normalized_literature_record.v2`
- Import batch: `meta_literature_import_batch.v2`
- Manifest: `meta_literature_library_manifest.v1`
- Record audit: `meta_literature_record_audit.v1`

## Normalized Record Fields

Each normalized record includes:

- `record_id`
- `title`
- `abstract`
- `authors`
- `first_author`
- `corresponding_author`
- `journal`
- `year`
- `publication_date`
- `doi`
- `pmid`
- `pmcid`
- `clinical_trial_id`
- `database_source`
- `source_type`
- `source_file`
- `source_query`
- `search_execution_id`
- `import_batch_id`
- `provenance`
- `raw_extra`
- `dedup_status`
- `screening_status`
- `full_text_status`
- `extraction_status`
- `quality_status`
- `record_status`
- `created_at`
- `updated_at`
- `audit_refs`

Defaults are conservative: `screening_status=not_started`, `dedup_status=pending_review`, `full_text_status=not_checked`, `extraction_status=not_started`, `quality_status=not_started`.

## Import Batch Fields

Each import batch includes:

- `import_batch_id`
- `source_type`
- `source_name`
- `source_file`
- `source_query`
- `search_execution_id`
- `created_at`
- `imported_count`
- `skipped_count`
- `duplicate_candidate_count`
- `diagnostics`
- `governance_refs`
- `audit_refs`

## Manifest

`literature/library_manifest.json` records:

- `schema_version`
- `records_path`
- `import_batches_path`
- `dedup_queue_path`
- `total_records`
- `total_batches`
- `source_counts`
- `last_updated`

## Diagnostics

The library records Chinese-friendly diagnostics without failing import when metadata is sparse:

- 缺少 DOI
- 缺少 PMID
- 缺少摘要
- 缺少年份
- 作者字段不完整
- 来源信息不完整

## Current Sources

- PubMed confirmed candidates: selected candidates only, with search execution and reviewer decision provenance.
- NBIB: bridged through the existing active import service and normalized into the v2 library.
- RIS: bridged through the existing active import service and normalized into the v2 library.
- CSV: bridged through the existing active import service and normalized into the v2 library.

The NBIB/RIS/CSV bridge still uses the existing transitional parser adapter. This is recorded as technical debt and should not be expanded into a broader active legacy dependency.

## Guardrails

- Rejected or pending PubMed candidates are not imported.
- Import does not create title/abstract screening artifacts.
- Import does not confirm study inclusion.
- Import does not automatically merge duplicates.
- Import does not update PRISMA artifacts.
- No Bioinformatics, GEO, GSE, TCGA, or GTEx code is used.
