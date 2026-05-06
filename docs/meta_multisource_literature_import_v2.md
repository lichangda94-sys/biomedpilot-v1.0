# Meta Multi-source Literature Import v2

Status: Developer Preview / testing.

## Scope

Multi-source Literature Import v2 adds a Meta-owned file-import adapter path for common literature database and reference-manager exports. It parses local files and writes normalized records through `LiteratureLibraryService`.

It does not execute online database searches, import unselected PubMed candidates, create screening decisions, silently deduplicate records, or update PRISMA counts.

## Active Service

- `app/meta_analysis/services/multisource_literature_import_service.py`

The service is separate from the older transitional NBIB/RIS/CSV legacy bridge. It does not import `app.meta_analysis.legacy` and does not depend on Bioinformatics.

## Supported File Profiles

- NBIB
- RIS
- CSV
- PubMed XML
- MEDLINE text
- EndNote RIS export
- Zotero RIS export
- Web of Science plain text
- Web of Science tab-delimited
- CNKI-style text export
- Embase RIS
- Cochrane RIS

WanFang and VIP remain planned file-import profiles after representative export fixtures are available.

## Output

All parsed records enter the normalized literature library:

- `literature/literature_records.json`
- `literature/import_batches.json`
- `literature/library_manifest.json`
- `audit/literature_record_audit.jsonl`
- `literature/multisource_import_diagnostics/*_diagnostics.json`

## Diagnostics

The service records Chinese-friendly diagnostics without failing sparse records:

- 缺少 DOI
- 缺少 PMID
- 缺少摘要
- 缺少年份
- 作者字段不完整

Unrecognized source fields are preserved in `raw_extra` whenever possible.

## Guardrails

- File import only.
- No WOS / Embase / CNKI / Cochrane online execution.
- No automatic literature screening.
- No automatic dedup merge.
- No PRISMA updates.
- No Bioinformatics dependency.
- No GEO, GSE, TCGA, or GTEx dependency.
