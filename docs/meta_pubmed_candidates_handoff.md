# Meta PubMed Candidates Handoff v1

Status: Developer Preview / testing.

## Scope

PubMed confirmed execution now produces a candidate preview that can be reviewed before import. This stage does not implement Web of Science, Embase, or CNKI online execution.

## Flow

1. Reviewer confirms and executes the PubMed query.
2. The execution report is written to `protocol/search_execution_report.json`.
3. Candidate preview is written to `protocol/pubmed_candidates/*_candidates_preview.json`.
4. Candidates remain `pending` by default and are not imported.
5. Reviewer explicitly selects candidates.
6. Selected candidates are converted through `LiteratureLibraryService` into `meta_normalized_literature_record.v2` records in `literature/literature_records.json`.
7. Import batch metadata is appended as `meta_literature_import_batch.v2` in `literature/import_batches.json`.
8. Dedup preparation is written to `deduplication/pubmed_candidate_duplicate_groups.json`.
9. No title/abstract screening artifact is created.
10. PRISMA included, screened, and full-text counts are not advanced by the handoff.

## Candidate Fields

Each candidate carries:

- `candidate_id`
- `pmid`
- `doi`
- `title`
- `authors`
- `journal`
- `year`
- `abstract`
- `source_query`
- `search_execution_id`
- `selected`
- `rejected`
- `user_decision`
- `decision_time`

## Provenance

Imported literature records keep:

- PubMed execution report path
- search strategy snapshot path
- candidate preview id
- candidate id
- PubMed execution id
- user decision event reference

## Governance

Automatic preview creation records `draft_created` governance events for `literature_inclusion` targets. Reviewer selection records `accept` or `reject`. Import handoff records a final `confirm` event for the import batch.

The handoff does not mark a study as included in the review. Inclusion still requires downstream screening and full-text decisions.

## Guardrails

- No automatic import from PubMed execution.
- No import for rejected or pending candidates.
- No automatic screening.
- No automatic PRISMA included/screened/full-text updates.
- No automatic dedup merge.
- No Bioinformatics, GEO, GSE, TCGA, or GTEx dependency.
