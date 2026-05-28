# B86 Enrichment Plot and Section Report Gate

## Scope

B86 adds formal enrichment plot artifacts and a section-only enrichment report package gate for controlled ORA/GSEA results.

## Implemented

Added `app/bioinformatics/enrichment_plot_report.py`:

- `build_enrichment_plot_gate(...)`
- `create_enrichment_plot_artifact(...)`
- `evaluate_enrichment_section_report_ready_gate(...)`
- `create_enrichment_section_report_package(...)`

Plot activation:

- accepts only `formal_computed_result` ORA/GSEA results;
- blocks imported/testing/exploratory/preflight sources;
- writes controlled SVG plot artifacts;
- registers artifacts into result index v2;
- inherits source result semantics;
- keeps `report_ready_eligible=False`.

Section report gate:

- requires formal enrichment result index completeness;
- requires passed dependency snapshot;
- requires output table;
- requires formal enrichment plot artifact or explicit table-only mode;
- creates a section-only package under `report_package/enrichment/`;
- records limitations, provenance, dependency snapshot, result index snapshot, plot artifacts and logs;
- sets report artifact scope to `formal_enrichment_only`.

## Boundaries

- This is not a full integrated report.
- No clinical interpretation, diagnosis, prognosis, or treatment recommendation.
- No ReactomePA/msigdbr bypass.
- No imported/testing/exploratory/preflight promotion.
- No survival/clinical activation.

## Validation

Focused tests cover:

- plot gate blocking imported sources;
- SVG artifact registration from formal ORA result;
- report gate requiring plot artifact or explicit table-only mode;
- section-only report package creation from formal GSEA result.
