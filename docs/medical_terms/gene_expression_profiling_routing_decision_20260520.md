# Gene Expression Profiling Routing Decision

Date: 2026-05-20

## Decision

`gene expression profiling` should route to Bioinformatics scoped vocabulary as `expression_profiling_assay` or `omics_assay` vocabulary.

Implemented target file: `data/medical_terms/bioinformatics/bioinformatics_data_type_terms.json`.

Implemented concept id: `bio_data_modality:gene_expression_profiling`.

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

## Implementation Status

- Bioinformatics scoped vocabulary updated: yes.
- Shared core modified: no.
- Meta seed modified: no.
- Loader modified: no.
- Online retrieval or PDF extraction enabled: no.

The legacy shared-core mini entries for this wording remain a separate shared-core cleanup concern. The new scoped Bioinformatics concept is not added to shared core and is not loaded as a Meta PICO term.
