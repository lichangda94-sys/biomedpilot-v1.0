# Shared Medical Vocabulary Oncology Core v1

## Scope

This stage upgrades the mini shared medical vocabulary into a curated oncology core vocabulary. The scope is intentionally oncology-first because current BioMedPilot retrieval workflows depend heavily on tumor names, TCGA project candidates, GEO query terms, GTEx tissue hints, and Meta Analysis cancer-topic search terms.

This is not a full medical ontology import. The goal is a high-confidence runtime vocabulary that improves Chinese biomedical topic retrieval without introducing broad, low-context concept expansion.

## Runtime Sources

- `data/medical_terms/mini_medical_terms_index.json`
- `data/medical_terms/zh_term_overrides.json`
- `data/medical_terms/medical_terms_index.sqlite`
- `data/medical_terms/reference_checklists/oncology_core_checklist.json`
- `app/shared/query_intelligence/medical_terms`

New oncology records keep the existing runtime fields and also carry normalized curation fields where useful, including `preferred_zh`, `zh_synonyms`, `preferred_en`, `en_synonyms`, `parent_concepts`, `child_concepts`, `related_organs`, `related_tissues`, `tcga_project_candidates`, `gtex_tissue_candidates`, `contexts`, `avoid_expansion_to`, `ambiguity_notes`, `confidence`, and `sources`.

## Coverage

Oncology core v1 covers the TCGA 33 project disease space as a hard requirement. It also adds high-value solid tumor and hematologic malignancy terms that are common in clinical and translational research, including thyroid cancer subtypes, kidney cancer subtypes, bladder urothelial carcinoma, breast cancer subtypes, gynecologic tumors, lung tumor subtypes, cholangiocarcinoma, colorectal adenocarcinoma, acute and chronic leukemias, lymphomas, multiple myeloma, central nervous system tumors, skin tumors, gastrointestinal stromal tumor, and bone or soft-tissue sarcoma examples.

TCGA mapping coverage is 33/33 in `coverage_audit_report.json`. The checklist keeps parent and subtype relationships explicit, for example lung cancer to LUAD/LUSC/small cell lung cancer, colorectal cancer to colon and rectal cancer, glioma to GBM/LGG, kidney cancer to KIRC/KIRP/KICH, and thyroid cancer to papillary, follicular, medullary, and anaplastic thyroid carcinoma.

GTEx mapping is used as an analysis hint, not as a tumor ontology. Current mappings emphasize practical tissue candidates such as Brain, Lung, Thyroid, Kidney, Liver, Colon, Esophagus, Breast, Prostate, Bladder, Skin, Pancreas, Stomach, Ovary, Uterus, Cervix Uteri, Testis, Whole Blood, and Adrenal Gland.

## Context Boundaries

Bioinformatics context may emit disease terms, abbreviations, MeSH terms, tissue terms, TCGA candidates, GTEx tissue candidates, GEO-oriented query terms, and data modality terms. It should not emit PubMed-only query strings, PICO primary outputs, or effect-measure primary outputs.

Meta Analysis context may emit disease terms, MeSH/PubMed terms, outcome terms, study design terms, and effect measures. It should not emit TCGA, GTEx, or GEO dataset candidates.

## Ambiguity Rules

The vocabulary avoids unconditional cross-subtype expansion for high-risk terms. Examples:

- ESCC does not expand to thyroid cancer, PTC, or THCA.
- PTC and thyroid cancer do not expand to ESCC.
- LUAD and LUSC do not expand to each other unless the parent lung cancer context is explicit.
- HCC does not expand to cholangiocarcinoma.
- Colon cancer is not automatically rectal cancer; colorectal cancer may cover both.
- GBM is not automatically all brain tumor or LGG.
- RCC alone is not expanded to every kidney cancer subtype.
- SCC alone is treated as ambiguous because the anatomical site is missing.

## Non-Goals

This stage does not import all of NCIt, OncoTree, WHO tumor classification, MeSH, UMLS, MONDO, or Disease Ontology. A full import would require version pinning, license review, namespace conflict handling, synonym confidence scoring, hierarchy pruning, and cross-context expansion policies. Those are larger ontology-management tasks and would add risk before the high-value oncology retrieval path is stable.

## Next Stages

Recommended next coverage modules:

- metabolic and endocrine diseases
- cardiovascular diseases
- immune and inflammatory diseases
- tissue and organ vocabulary
- Meta Analysis terms for PICO, outcomes, study design, and effect measures
