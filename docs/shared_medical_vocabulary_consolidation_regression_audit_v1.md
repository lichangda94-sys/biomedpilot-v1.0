# Shared Medical Vocabulary Consolidation & Regression Audit v1

## Status

The shared medical vocabulary currently has five curated core packages:

| Core package | Checklist items | Covered | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| Oncology Core v1 | 68 | 68 | 0 | 100% |
| Endocrine & Metabolic Core v1 | 75 | 75 | 0 | 100% |
| Anatomy / Tissue Core v1 | 68 | 68 | 0 | 100% |
| Bioinformatics Modality Core v1 | 65 | 65 | 0 | 100% |
| Meta Analysis Terms Core v1 | 108 | 108 | 0 | 100% |

Overall core checklist coverage is 384/384. The runtime vocabulary contains 448 concepts and 808 Chinese override mappings. The five core checklists define 49 high-risk ambiguity terms, and the overall quality gate status is pass.

## Runtime Vocabulary Boundary

The runtime vocabulary is still curated rather than an ontology-scale import. It is intended to provide stable, auditable concepts for:

- Disease and tumor topic understanding.
- Organ, tissue, TCGA primary-site, and GTEx tissue mapping.
- Bioinformatics data modality and assay recognition.
- Meta Analysis PICO, outcome, effect measure, diagnostic accuracy, publication type, exclusion type, and quality assessment recognition.

Concept IDs are unique, curated concepts carry confidence and source metadata, and the SQLite index is rebuilt from the JSON runtime vocabulary. Legacy entries can remain less structured, but curated core entries are expected to have stable category, subcategory, context, confidence, source, and synonym fields.

## Bioinformatics Context

Bioinformatics context is allowed to use:

- `disease_terms_en`
- `abbreviations`
- `mesh_terms`
- `tissue_terms`
- `gtex_tissue_candidates`
- `tcga_project_candidates`
- `tcga_primary_site_candidates`
- `data_modality_terms`
- `assay_terms`
- `platform_candidates`
- GEO/TCGA/GTEx/SRA helper terms

It must not expose PICO, effect measure, publication/exclusion type, quality assessment, or PubMed-only query terms as primary output. Short Meta tokens such as `OS`, `HR`, `OR`, `RR`, and `CI` are suppressed as Bioinformatics primary results.

## Meta Analysis Context

Meta Analysis context is allowed to use:

- `disease_terms_en`
- `mesh_terms`
- `pico_terms`
- `study_design_terms`
- `effect_measures`
- `outcome_terms`
- `diagnostic_accuracy_terms`
- `publication_type_terms`
- `exclusion_type_terms`
- `quality_assessment_terms`
- `pubmed_query_terms`

It must not expose TCGA, GTEx, GEO, or SRA candidates as primary results. Omics assay terms may remain auxiliary topic terms, but platform candidates are filtered out of Meta Analysis output.

## Short Token Handling

Short uppercase tokens require exact token boundaries. This protects:

- `OR` from matching lowercase `or`.
- `CI` from matching substrings inside ordinary words.
- `OS`, `HR`, `OR`, `RR`, and `CI` from leaking into Bioinformatics output.
- `PD` from defaulting to Parkinson disease in Meta Analysis context.

Known ambiguous abbreviations such as `SCC`, `RCC`, `PR`, `SD`, and `PD` are retained with context constraints or ambiguity warnings rather than forced expansion to a single disease or endpoint.

## Negative Regression Coverage

The consolidation regression tests cover:

- ESCC vs thyroid/PTC/THCA leakage.
- Thyroid cancer/PTC vs ESCC leakage.
- LUAD vs LUSC leakage.
- HCC vs cholangiocarcinoma leakage.
- Tissue-only terms such as thyroid, liver, lung, bone marrow, lymph node, and adipose tissue not becoming disease concepts.
- NAFLD/MASLD/NASH and thyroid nodule not expanding to oncology concepts.
- scRNA-seq vs bulk RNA-seq, ATAC-seq vs ChIP-seq, WGS vs WES, and proteomics vs metabolomics boundaries.
- Meta terms staying separated from disease, tissue, biomarker, data modality, and Bioinformatics platform outputs.

## Remaining Risks

Some legacy non-core entries predate the curated schema and may not have the same field completeness as the five core packages. The current tests enforce the stricter schema on curated core entries and leave legacy cleanup for a later migration.

The Bioinformatics registry still provides generic dataset helper terms for broad Bioinformatics queries. This is treated as auxiliary query support, not as a disease or assay-specific concept match.

## Next Stage

Recommended next work:

- Cardiovascular & Immune Inflammatory Core v1.
- External Ontology Subset Import v1 for selected MeSH, EFO, OBI, NCIt, or EBM/publication-type subsets.
- Legacy vocabulary normalization to bring older curated entries fully into the newer core schema.
