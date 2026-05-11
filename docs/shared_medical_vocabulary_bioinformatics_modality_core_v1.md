# Shared Medical Vocabulary: Bioinformatics Modality Core v1

## Scope

Bioinformatics Modality Core v1 adds curated data type, assay, platform, and omics-analysis terms to the shared medical vocabulary. The goal is to improve Chinese research-topic retrieval, GEO/TCGA/GTEx/SRA query draft generation, dataset candidate filtering, and Meta Analysis omics topic understanding.

This stage is intentionally curated. It does not import a full assay ontology and it does not handle uploaded-file structure recognition.

## Coverage

The runtime vocabulary now covers core terms across:

- Transcriptomics: RNA-seq, bulk RNA-seq, expression profiling, microarray, scRNA-seq, snRNA-seq, spatial transcriptomics, long-read RNA-seq, total RNA-seq, ribo-depleted RNA-seq, polyA RNA-seq.
- Non-coding RNA: miRNA-seq, microRNA profiling, lncRNA profiling, circRNA profiling, small RNA-seq.
- Epigenomics: methylation profiling, DNA methylation array, bisulfite sequencing, WGBS, RRBS, ATAC-seq, ChIP-seq, CUT&RUN, CUT&Tag, chromatin accessibility, histone modification profiling.
- Genomics: WGS, WES, targeted sequencing, panel sequencing, SNP array, CNV, mutation profiling, somatic mutation, germline variant.
- Single-cell and multi-omics: single-cell multiomics, scATAC-seq, CITE-seq, single-cell proteogenomics, multiome ATAC plus gene expression, cell type annotation, cell clustering.
- Proteomics and metabolomics: proteomics, mass spectrometry proteomics, phosphoproteomics, metabolomics, lipidomics, glycomics.
- Functional genomics: CRISPR screen, RNAi screen, shRNA screen, Perturb-seq, drug screen.
- Clinical and phenotypic omics: survival data, clinical metadata, phenotype data, immune infiltration, tumor microenvironment, pathway activity, gene signature.

Chinese aliases include high-frequency user inputs such as `单细胞`, `空间转录组`, `甲基化`, `蛋白组`, `代谢组`, `全外显子`, `全基因组`, `芯片`, `表达谱`, and `测序`.

## Runtime Boundaries

These entries use `concept_type=data_modality`, not `disease`. A query that only matches RNA-seq, microarray, scRNA-seq, or another assay should be treated as data-type recognition, not disease recognition.

`Bioinformatics` context may consume `data_modality_terms`, `assay_terms`, `platform_candidates`, GEO/TCGA/GTEx/SRA helper terms, and ordinary disease/tissue terms when they are independently matched.

`Meta Analysis` context may consume omics exposure or assay terms, MeSH/disease terms, and study concepts, but should not expose TCGA, GTEx, GEO, or SRA platform candidates as primary output.

## Negative Expansion Rules

The curated entries encode boundary notes for common high-risk terms:

- `scRNA-seq` does not expand to bulk RNA-seq.
- `ATAC-seq` does not expand to ChIP-seq.
- `WGS` does not expand to WES.
- `proteomics` does not expand to metabolomics.
- `表达谱` remains a broad expression-profiling concept.
- `芯片` remains broad unless expression, SNP, or methylation context is explicit.
- `测序` is broad and ambiguous; it should not strongly infer RNA-seq, WGS, or WES by itself.

## Relationship To Existing Vocabulary

This core sits alongside Oncology Core v1, Endocrine & Metabolic Core v1, and Anatomy / Tissue Core v1. It does not create disease or tissue concepts and should not cause organ or disease expansion. Disease and tissue mapping remain owned by the existing disease and anatomy vocabularies.

## Not Covered

This stage does not attempt full coverage of OBI, EFO assay ontology, EDAM, Sequence Ontology, platform-specific probe annotations, instrument models, single-cell preprocessing methods, or uploaded matrix/table structure recognition.

## Next Steps

Recommended follow-up cores:

- Meta Analysis Terms Core v1: outcome, exposure, comparator, design, effect measure, and risk-of-bias terms.
- Cardio-Immune Core v1: high-frequency cardiovascular, immune, inflammatory, and infection concepts.
- Bioinformatics analysis method terms: normalization, differential expression, enrichment, batch correction, trajectory, deconvolution, and survival modeling.
