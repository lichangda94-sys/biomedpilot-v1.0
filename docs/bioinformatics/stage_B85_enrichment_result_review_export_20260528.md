# B85 Enrichment Result Review and Export

## Scope

B85 adds a review/export layer for controlled formal ORA and preranked GSEA results. It does not generate plots, report-ready packages, full integrated reports, or clinical interpretation.

## Implemented

Added `app/bioinformatics/enrichment_result_review.py`:

- `build_enrichment_result_review(...)`
- `export_enrichment_review_table(...)`

The review layer:

- only includes `formal_computed_result` entries with task type `ora` or `gsea_preranked`;
- excludes imported/testing/exploratory/preflight entries;
- reads ORA and GSEA TSV output artifacts;
- normalizes term id, description, p-value, adjusted p-value and significance label;
- supports sorting by adjusted p-value, p-value, term id, NES/ES/count/size and input order;
- supports filtering significant, not significant, positive enrichment and negative enrichment;
- exposes provenance, parameter manifest, dependency snapshot and log artifacts;
- keeps guard copy stating this is statistical research only.

Exports:

- TSV;
- CSV;
- no report-ready state change;
- no plot/report artifact registration.

## Boundaries

- No enrichment plot activation.
- No enrichment report-ready package.
- No clinical conclusion, diagnosis, prognosis, or treatment recommendation.
- No imported/testing/exploratory/preflight result promotion.

## Validation

Focused tests cover:

- formal ORA review and imported result exclusion;
- GSEA filtering/sorting;
- TSV/CSV export without report-ready promotion;
- missing formal result blocking.
