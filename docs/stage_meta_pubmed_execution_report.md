# Stage Meta-Search-2 Report

## Scope

Added Meta-internal PubMed execution for reviewer-confirmed query drafts. This
stage only executes PubMed through E-utilities; Web of Science, Embase, and
CNKI remain draft-only.

## Outputs

- `protocol/search_strategy_user_confirmed.json`
- `protocol/search_execution_report.json`

The execution report records `database=PubMed`, `query_used`, `executed_at`,
`result_count`, `returned_count`, returned PMIDs, deduplication summary,
structured errors, and warnings.

## Candidate Boundary

Returned PubMed records are literature candidates only. The execution step does
not auto-import records into the literature library, does not run deduplication,
and does not start title/abstract screening.

## Failure Handling

Empty queries and network/API failures return structured error payloads instead
of raising into the UI. The protocol page can still keep the confirmed query and
report path for audit.

## Boundary Notes

- PubMed execution lives in `app/meta_analysis/search/pubmed_search_service.py`.
- Bioinformatics code and GEO/TCGA/GTEx retrieval code were not changed.
- `app/shared/literature_search/` was not added because no cross-module client
  is required yet.
