# Stage 2.2 Medical Vocabulary Systematic Expansion Report

## Scope

Stage 2.2 expands the shared mini medical vocabulary by category rather than one-off fixes. The change remains in the shared vocabulary layer and keeps the optional full sqlite index as an enhancement, not a runtime dependency.

## Added Term Categories

- Oncology diseases: central nervous system tumors, head and neck tumors, thoracic tumors, gastrointestinal tumors, breast and genitourinary tumors, melanoma, and hematologic malignancies.
- Common non-oncology diseases: metabolic, cardiovascular, kidney, neurologic, autoimmune, gastrointestinal, liver, and respiratory diseases.
- Tissues and organs: 23 Chinese-supported tissue concepts mapped to GTEx-style candidates.
- Bioinformatics data modalities: expression, transcriptomic, single-cell, spatial, methylation, RNA class, proteomic, metabolomic, chromatin, genome, and exome modalities.
- Meta Analysis terms: clinical outcomes, diagnostic metrics, effect measures, study designs, and publication exclusion types.

## Added Disease Coverage

The mini index now contains 71 disease concepts. Stage 2.2 added or strengthened entries for meningioma, pituitary adenoma, nasopharyngeal carcinoma, HNSCC, OSCC, laryngeal cancer, SCLC, gastric adenocarcinoma, colon cancer, rectal cancer, cholangiocarcinoma, PDAC, TNBC, KIRC, KIRP, leukemia, AML, lymphoma, multiple myeloma, type 1 diabetes, insulin resistance, metabolic syndrome, overweight, hyperlipidemia, hypercholesterolemia, heart failure, atherosclerosis, glomerulonephritis, stroke, multiple sclerosis, SLE, Crohn disease, ulcerative colitis, COPD, and asthma.

## TCGA Mapping

The built-in mini index now exposes 24 TCGA project candidates, including TCGA-GBM, TCGA-LGG, TCGA-THCA, TCGA-LUAD, TCGA-LUSC, TCGA-STAD, TCGA-COAD, TCGA-READ, TCGA-LIHC, TCGA-PAAD, TCGA-BRCA, TCGA-PRAD, TCGA-OV, TCGA-CESC, TCGA-UCEC, TCGA-KIRC, TCGA-KIRP, TCGA-BLCA, TCGA-SKCM, TCGA-HNSC, TCGA-ESCA, and TCGA-LAML.

Multi-project diseases remain candidates instead of forced single picks, for example colorectal cancer maps to TCGA-COAD and TCGA-READ.

## GTEx Mapping

The mini index now exposes 23 GTEx-style tissue candidates, including Brain, Thyroid, Esophagus, Lung, Stomach, Colon, Liver, Pancreas, Breast, Prostate, Ovary, Uterus, Kidney, Bladder, Skin, Whole Blood, Adipose Tissue, Muscle, and Heart.

Approximate candidates are marked in concept metadata where the mini vocabulary has no exact GTEx tissue, such as cervix/endometrium to Uterus, rectum to Colon, kidney/bladder where support may depend on the local GTEx source version, and hematologic or marrow terms to Whole Blood.

## Meta Terms

Outcome and metric coverage now includes OS, PFS, DFS, RFS, mortality, recurrence, incidence, prevalence, risk, OR, RR, HR, sensitivity, specificity, diagnostic accuracy, and AUC.

Study design coverage now includes RCT, cohort study, case-control study, cross-sectional study, diagnostic accuracy study, prognostic study, and observational study.

Publication exclusion coverage now includes review, meta-analysis, editorial, letter, comment, case report, conference abstract, animal study, and cell experiment.

## Test Coverage

`tests/shared/test_medical_vocabulary_systematic_coverage.py` adds systematic assertions for tumor TCGA/GTEx mapping, common non-tumor diseases, data modalities, Meta outcomes, study design/publication terms, context filtering, and forbidden disease leakage.

The existing Stage 2.1 coverage tests remain in place for glioma, ESCC, PTC, LUAD, HCC, diabetes, obesity, fatty liver, data modalities, and Meta outcomes.

## Current Gaps

- The mini index is curated and intentionally incomplete; rare diseases, drug names, genes, variants, and procedure terms are still out of scope.
- GTEx approximate candidates are metadata annotations in the mini concept records; downstream UI can expose mapping status later if needed.
- Hematologic malignancies do not have complete TCGA coverage beyond AML/LAML in this mini layer.
- The mini index does not replace ontology-backed normalization for MONDO, DOID, NCIt, MeSH, or EFO identifiers.

## Full Ontology Plan

The full index should continue to be generated offline by `scripts/update_medical_term_index.py` into `data/medical_terms/medical_terms_index.sqlite`. That build can add ontology identifiers, richer synonym ranking, exact GTEx tissue status, and broader coverage while preserving the same runtime contract: full sqlite is optional, mini index plus zh overrides remains the default fallback, and runtime startup must not parse full OWL/OBO/XML inputs.
