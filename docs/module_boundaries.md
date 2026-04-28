# Module Boundaries

## Bioinformatics Analysis

Allowed domain terms and flows:

- GEO, TCGA, GTEx, user sequencing data.
- Data retrieval, download, asset identification, expression matrix cleaning,
  sample grouping, DEG readiness, enrichment, correlation, survival, plots,
  and reports.

Current preserved source:

- `app/bioinformatics/legacy/geo_tool/`
- `app/bioinformatics/legacy/geo_pipeline/`
- `app/bioinformatics/legacy/geo_processing/`
- `app/bioinformatics/legacy/tcga_gtex/`
- `app/bioinformatics/legacy/ui/`

## Meta Analysis

Allowed domain terms and flows:

- PICO, search strategy, literature import, deduplication, title/abstract
  screening, full-text screening, extraction, risk of bias, analysis plan,
  Meta statistics, forest/funnel plots, and reports.

Current preserved source:

- `app/meta_analysis/legacy/literature/`
- `app/meta_analysis/legacy/extraction/`
- `app/meta_analysis/legacy/analysis/`
- `app/meta_analysis/legacy/analysis_profiles/`
- `app/meta_analysis/legacy/reporting/`
- `app/meta_analysis/legacy/fulltext/`
- `app/meta_analysis/legacy/bias/`

## Shared Layer

Shared code must not contain business-specific execution logic for GEO/TCGA/GTEx
or Meta statistics. It may contain common project, data, task, report, settings,
storage, logging, environment, and reusable UI services.

