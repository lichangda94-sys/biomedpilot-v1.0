# Shared Medical Vocabulary Governance & Release v1

## Release

- release_name: `shared_medical_vocabulary_core_v1`
- version: `core_v1.0.0`
- runtime source: `data/medical_terms/mini_medical_terms_index.json`
- Chinese override source: `data/medical_terms/zh_term_overrides.json`
- optional SQLite index: `data/medical_terms/medical_terms_index.sqlite`
- coverage audit: `data/medical_terms/coverage_audit_report.json`

Core v1 is a curated, auditable shared vocabulary release. It is designed to support Bioinformatics Chinese topic retrieval, GEO/TCGA/GTEx/SRA query assistance, Meta Analysis question understanding, and PubMed/MeSH query drafting without importing an uncontrolled full ontology.

## Core Packages

- Oncology Core v1: tumor concepts, high-value cancer subtypes, TCGA project candidates, and oncology ambiguity boundaries.
- Endocrine & Metabolic Core v1: metabolic disease, endocrine disease, phenotypes, hormones, and biomarkers.
- Cardiovascular Core v1: cardiovascular diseases, vascular disease, risk factors, phenotypes, and biomarkers.
- Immune & Inflammatory Core v1: immune diseases, inflammatory diseases, immune cells, cytokines, autoantibodies, and immune processes.
- Anatomy / Tissue Core v1: organs, tissues, GTEx tissue candidates, and TCGA primary site support.
- Bioinformatics Modality Core v1: omics data modality and assay terms for search intent, not uploaded-file structure recognition.
- Meta Analysis Terms Core v1: PICO/PICOS/PECO, outcomes, study designs, effect measures, diagnostic accuracy terms, publication types, exclusion types, and quality assessment tools.

## Bioinformatics Context Boundary

Bioinformatics context may output disease terms, abbreviations, MeSH terms, tissue terms, GTEx tissue candidates, TCGA project candidates, TCGA primary site candidates, data modality terms, assay terms, platform candidates, immune cell terms, biomarker terms, and GEO/TCGA/GTEx/SRA query assistance.

Bioinformatics context must not output PICO, effect measure, publication/exclusion type, or PubMed-only query terms as primary results.

## Meta Analysis Context Boundary

Meta Analysis context may output disease terms, MeSH terms, PubMed query terms, PICO terms, study design terms, effect measures, outcome terms, diagnostic accuracy terms, publication type terms, exclusion type terms, quality assessment terms, exposure terms, and biomarker terms.

Meta Analysis context must not output TCGA, GTEx, GEO, or SRA candidates as primary results.

## concept_id Rules

- `concept_id` must be globally unique.
- New curated runtime concepts should use the `mini:<domain>_<slug>` pattern unless an older stable `mini:<slug>` already exists.
- Existing stable concept IDs must be reused when a later core package cross-references the same concept.
- Do not create duplicate concepts for cross-domain terms such as CRP, Hashimoto thyroiditis, Graves disease, obesity, diabetes, dyslipidemia, thyroid nodule, inflammation, adipose tissue, whole blood, heart, or artery.
- When retiring a duplicate legacy concept, keep the surviving primary concept and record the old ID in `deprecated_alias_concept_ids` or `related_concepts` when useful for audit.

## category / subcategory Rules

- `category` describes the owning semantic package, such as `oncology`, `endocrine_metabolic`, `cardiovascular`, `immune_inflammatory`, `anatomy_or_tissue`, `data_modality`, or `meta_analysis_term`.
- `subcategory` should be stable and narrow enough for audit tables, for example `thyroid_disease`, `immune_biomarker`, `rheumatic_arthritis`, `blood_tissue`, `transcriptomics`, or `effect_measure`.
- `concept_type` must distinguish disease, tissue, data modality, immune cell, biomarker, hormone, phenotype, process, outcome, study design, effect measure, publication type, exclusion type, and quality assessment terms.
- Biomarkers, immune cells, tissues, outcomes, and effect measures must not be marked as disease concepts.

## zh_term_overrides Rules

- Chinese overrides are curated aliases, not a second independent ontology.
- Every override must map to at least one runtime `concept_id`.
- Overrides should include practical Chinese clinical/research aliases, not exhaustive rare labels.
- Short English abbreviations may be included as override keys only when exact matching is required and ambiguity is documented.
- Overrides must carry `concept_type`, confidence, source, contexts, and the same major output fields as the mapped concept.

## Cross-Reference Rules

- Use `cross_refs` for structured external candidates such as TCGA projects, TCGA primary sites, and GTEx tissues.
- Use `related_concepts` for semantic relationships that should not trigger automatic expansion.
- Use `parent_concepts` and `child_concepts` for hierarchy documentation, but do not treat them as unconditional query expansion.
- Use `avoid_expansion_to` for high-risk false friends, sibling diseases, broad umbrella terms, and overlapping abbreviations.

## Ambiguity & Short Token Management

High-risk ambiguity terms must remain visible in checklist `ambiguity_terms` and release-level `short_token_risk_terms`. Tokens shorter than four characters, all-caps abbreviations, and common assay abbreviations must use exact or boundary-aware matching.

Release v1 tracks at least:

`PTC`, `SCC`, `RCC`, `CRC`, `HCC`, `GBM`, `LGG`, `RA`, `SLE`, `IBD`, `MS`, `CRP`, `IL-6`, `TNF`, `IFN`, `ANA`, `RF`, `ANCA`, `T3`, `T4`, `TSH`, `PTH`, `BMI`, `HDL`, `LDL`, `OS`, `HR`, `OR`, `RR`, `CI`, `MD`, `SMD`, `PR`, `SD`, `PD`, `WGS`, `WES`, `RNA`, `DNA`, `CNV`, `SNP`.

## Why Not Full Ontology Import

Full NCIt, MONDO, MeSH, EFO, UBERON, OncoTree, or WHO imports would add many terms that are not yet mapped to BioMedPilot output semantics. Direct full import would increase false positives, short token leakage, duplicate concepts, unclear licensing/versioning surfaces, and context contamination between Bioinformatics and Meta Analysis.

The current release keeps a curated runtime vocabulary plus an optional SQLite index. External ontology imports should be staged as reviewed subsets with explicit category mapping, context rules, ambiguity notes, and regression tests.

## External Ontology Subset Route

Recommended import route:

1. Select a bounded subset for one domain, such as cardiovascular diseases, immune inflammatory diseases, anatomy/tissue, or assay/modality.
2. Map external IDs into existing `concept_id` ownership rules.
3. Classify every imported term by `category`, `subcategory`, and `concept_type`.
4. Add short token and ambiguity notes before runtime exposure.
5. Add checklist coverage and negative leakage tests.
6. Keep optional full ontology SQLite data behind a provider boundary until release gates pass.

## Release Gates

A release is acceptable only when:

- all core checklists are covered,
- overall quality gate status is `pass`,
- duplicate `concept_id` count is zero,
- watched cross-core terms have a single primary concept,
- high-risk short token list is present,
- `tests/shared` passes,
- SQLite index concept IDs match runtime JSON concept IDs.
