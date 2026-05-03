# Medical Term Index Contract

## Stage 2 / 2.2 Goal

Stage 2 establishes a small but extensible shared medical term index for BioMedPilot. The immediate goal is to stop fixing one disease at a time and instead route Chinese disease terms through a stable lookup layer that can be consumed by both Bioinformatics and Meta Analysis with context-specific filtering.

Stage 2.2 expands the default built-in mini coverage systematically by medical category, Meta retrieval category, and Bioinformatics data-source mapping category so common topics still resolve when the optional full sqlite index is absent.

## Planned Vocabulary Sources

- MONDO: primary disease vocabulary, CC BY 4.0.
- DOID: disease fallback vocabulary, CC0.
- NCIt: oncology terminology, CC BY 4.0.
- MeSH: biomedical subject heading layer used for controlled medical terminology.
- EFO: bioinformatics experiment variables and data resource annotations.

Development builds may download or read local MONDO/DOID/NCIt/MeSH/EFO source files. Runtime builds must not parse full OWL/OBO/XML files during application startup. Full ontology processing is performed by `scripts/update_medical_term_index.py`, which writes an optional preprocessed `data/medical_terms/medical_terms_index.sqlite`.

## Current Built-In Assets

- `data/medical_terms/zh_term_overrides.json`: curated Chinese entry-point overrides for common oncology diseases, common non-oncology diseases, clinical/pathology modifiers, outcomes, and bioinformatics data modalities.
- `data/medical_terms/mini_medical_terms_index.json`: built-in JSON concept index that keeps the application runnable without external files.
- `data/medical_terms/source_metadata.json`: source and license planning metadata.
- `data/medical_terms/license_attribution.md`: attribution and license notes.
- `data/package_manifest.json`: package manifest entry that identifies `medical_terms_index` as a BioMedPilot shared medical vocabulary, not a Bioinformatics-specific asset.

The mini coverage includes:

- Oncology: glioma/GBM/LGG, meningioma, pituitary adenoma, thyroid cancer/PTC/PDTC/ATC, esophageal cancer/ESCC, head and neck tumors, lung cancer/NSCLC/SCLC/LUAD/LUSC, gastric/colon/rectal/colorectal cancers, HCC, cholangiocarcinoma, pancreatic cancer/PDAC, breast cancer/TNBC, prostate/ovarian/cervical/endometrial cancers, kidney cancer/KIRC/KIRP, bladder cancer, melanoma, leukemia/AML, lymphoma, and multiple myeloma.
- Common non-oncology diseases: type 1 and type 2 diabetes, insulin resistance, metabolic syndrome, obesity/overweight, hyperlipidemia, hypercholesterolemia, hypertension, coronary artery disease, heart failure, atherosclerosis, chronic kidney disease, glomerulonephritis, Alzheimer disease, Parkinson disease, stroke, multiple sclerosis, rheumatoid arthritis, systemic lupus erythematosus, inflammatory bowel disease, Crohn disease, ulcerative colitis, fatty liver disease/NAFLD, COPD, and asthma.
- Tissues and organs: brain, thyroid, esophagus, lung, stomach, colon, rectum, liver, pancreas, breast, prostate, ovary, cervix, endometrium, kidney, bladder, skin, blood, bone marrow, lymph node, adipose tissue, muscle, and heart.
- Modifiers and outcomes: differentiation grade, metastasis, recurrence, prognosis, survival, disease risk, OS/PFS/DFS/RFS, mortality, incidence, prevalence, OR/RR/HR, sensitivity, specificity, diagnostic accuracy, and AUC.
- Study designs and publication filters: RCT, cohort, case-control, cross-sectional, diagnostic accuracy, prognostic, observational, review, meta-analysis, editorial, letter, comment, case report, conference abstract, animal study, and cell experiment.
- Data modalities: gene expression profiling, transcriptome, RNA-seq, single-cell RNA-seq/scRNA-seq, spatial transcriptomics, microarray, methylation profiling, miRNA, lncRNA, circRNA, proteomics, metabolomics, ATAC-seq, ChIP-seq, WGS, and WES.

Key built-in mappings include `脑胶质瘤 -> glioma / glioblastoma / TCGA-GBM / TCGA-LGG / GTEx Brain`, `食管鳞癌 -> ESCC / esophageal squamous cell carcinoma`, `乳头状甲状腺癌 -> PTC / TCGA-THCA`, `肺腺癌 -> LUAD / TCGA-LUAD`, and `肝细胞癌 -> HCC / TCGA-LIHC`.

`medical_terms_index.sqlite` is optional. If present, it is preferred over the mini index. If it is absent, the runtime falls back to the mini index. If both full and mini indexes are absent, the legacy `biomedical_term_registry` remains the final fallback.

## Lookup Contract

`lookup_medical_terms(query, target_context="bioinformatics")` returns a `TermLookupResult` with:

- matched Chinese terms
- English disease terms and synonyms
- abbreviations and MeSH terms
- tissue terms
- TCGA project candidates
- GTEx tissue candidates
- data modality terms
- modifier terms
- Meta-oriented terms such as exposure, intervention, outcome, study design, and publication type terms when available
- concept ids, term sources, confidence, and warnings

Matching priority is:

1. Longest Chinese match first.
2. Disease concept before tissue concept.
3. `zh_term_overrides`.
4. Optional full `medical_terms_index.sqlite` when present.
5. Built-in mini index.
6. Legacy biomedical registry.

If both disease and tissue are identified, both are retained. If only tissue is identified, lookup emits a warning so the Bioinformatics broad GEO guard can block default wide expression-profile searches.

## Fallback Order

`build_search_translation_draft()` merges term sources in this order:

1. Chinese overrides and term lookup.
2. Optional preprocessed full sqlite index.
3. Mini medical terms index.
4. Existing `biomedical_term_registry`.
5. Legacy MeSH query builder where still used by the Bioinformatics preview path.
6. Optional local model candidates, only when explicitly enabled.

Local model output must not override curated term lookup results, and disease guard filtering remains active after all candidate terms are merged.

## Bioinformatics Routing

Bioinformatics consumes lookup output through `SearchTranslationDraft.audit`:

- `disease_terms_en`
- `tcga_project_candidates`
- `gtex_tissue_candidates`
- `tissue_terms`
- `data_modality_terms`
- `term_lookup`
- `term_sources`

The Bioinformatics adapter uses these fields so `脑胶质瘤` produces glioma GEO query terms, TCGA `TCGA-GBM / TCGA-LGG`, and GTEx `Brain` normal tissue reference. TCGA/GDC results are project assets, and GTEx results are normal references, not disease datasets.

Bioinformatics does not consume PubMed, Web of Science, Embase, or CNKI query candidates.

## Meta Analysis Routing

Meta Analysis consumes disease terms, synonyms, abbreviations, MeSH terms, exposure terms, intervention terms, outcome terms, study design terms, and publication type terms. It does not consume TCGA project candidates, GTEx tissue candidates, or GEO/GSE query candidates.

For `target_context="meta_analysis"`, MeSH terms are prioritized when building PubMed query drafts. For `target_context="bioinformatics"`, PubMed candidates are removed and TCGA/GTEx mappings remain available only as Bioinformatics dataset-source metadata.

## UMLS And SNOMED CT

UMLS and SNOMED CT are not default inputs in this stage because their licensing, account access, and redistribution constraints are more restrictive than the open vocabulary set above. They can be evaluated later behind an explicit local-user import flow.

## Audit Rules

Every lookup-backed translation writes term source metadata into `SearchTranslationDraft.audit`. Downstream modules should use this audit trail for diagnostics but must not expose raw Python exceptions or unrelated literature-search wording in the Bioinformatics UI.
