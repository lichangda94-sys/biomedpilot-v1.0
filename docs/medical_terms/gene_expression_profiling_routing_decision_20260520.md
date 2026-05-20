# Gene Expression Profiling Routing Decision

Date: 2026-05-20

## Decision

`gene expression profiling` should route to Bioinformatics scoped vocabulary as `expression_profiling_assay` or `omics_assay` vocabulary.

Recommended target file for a future approved implementation: `data/medical_terms/bioinformatics/bioinformatics_data_type_terms.json`.

## Usage

- `dataset_search`
- `geo_query_expansion`
- `data_type_detection`
- `analysis_readiness_check`

## Boundaries

- `meta_analysis_allowed=false`
- `shared_core_allowed=false`
- `standalone_search_allowed=conditional`
- It must not become a Meta PICO main term.
- It must not remain active shared core after a future cleanup phase.

## Non-Actions

No Bioinformatics runtime file, shared core file, or Meta scoped vocabulary file was modified in this phase.
