# Shared Medical Vocabulary Endocrine & Metabolic Core v1

## Scope

Endocrine & Metabolic Core v1 adds curated high-frequency endocrine and metabolic disease, phenotype, hormone, and biomarker terms to the shared medical vocabulary. The scope is designed for Bioinformatics Chinese research-topic retrieval, GTEx tissue candidate hints, and Meta Analysis query drafting.

This stage continues the curated vocabulary strategy. It does not import a full ontology, and it does not try to cover every rare endocrine disorder.

## Why This Stage

Metabolic and endocrine topics are common in clinical research, translational omics, and literature synthesis. They also contain many short or ambiguous abbreviations such as T1D, T2D, PCOS, TSH, T3, T4, PTH, BMI, HDL, LDL, NAFLD, NASH, and MASLD. Curating these terms explicitly reduces false expansion and gives downstream retrieval modules safer structured signals.

## Covered Areas

The checklist covers glucose metabolism disorders, obesity and weight-related phenotypes, dyslipidemia, metabolic syndrome and fatty liver disease, thyroid disease, parathyroid and calcium-phosphate metabolism, pituitary disease, adrenal disease, reproductive endocrinology, and endocrine/metabolic biomarkers.

Runtime records include practical Chinese terms, English preferred names, synonyms, abbreviations, MeSH terms where useful, related organs/tissues, GTEx tissue candidates, context flags, ambiguity notes, and negative expansion boundaries.

## Disease, Phenotype, And Biomarker Boundaries

Disease concepts include examples such as diabetes mellitus, type 1 diabetes, type 2 diabetes, gestational diabetes, dyslipidemia, hypothyroidism, Graves disease, Cushing syndrome, and PCOS.

Phenotype concepts include examples such as prediabetes, impaired fasting glucose, impaired glucose tolerance, insulin resistance, hyperglycemia, hypoglycemia, central obesity, low HDL cholesterol, high LDL cholesterol, thyroid nodule, menopause, and hypercalcemia.

Biomarker and hormone concepts include examples such as adiponectin, leptin, insulin, C-peptide, glucagon, HbA1c, fasting glucose, TSH, T3, T4, free T3, free T4, thyroglobulin, TPOAb, TgAb, cortisol, aldosterone, renin, PTH, and vitamin D. These are not marked as disease concepts.

## Oncology Boundary

Thyroid disease terms are kept separate from thyroid cancer, PTC, and TCGA-THCA. Thyroid nodule, Hashimoto thyroiditis, Graves disease, hypothyroidism, hyperthyroidism, goiter, and thyroid hormone disorder do not automatically expand into thyroid cancer.

NAFLD, MASLD, and NASH are kept separate from hepatocellular carcinoma and TCGA-LIHC. They may be clinically related in some research contexts, but the shared vocabulary does not make that expansion without explicit disease wording.

## Context Boundary

Bioinformatics context may consume disease, phenotype, tissue, GTEx tissue, and omics retrieval hints. It should not emit PubMed-only, PICO, or effect-measure primary outputs.

Meta Analysis context may consume disease, phenotype, biomarker, hormone, MeSH, PubMed query, study design, outcome, and effect measure terms. It should not emit TCGA, GTEx, or GEO dataset candidates as primary outputs.

## Remaining Gaps

This stage does not fully cover rare pituitary syndromes, inborn errors of metabolism, monogenic diabetes, detailed steroidogenesis disorders, pediatric endocrine diseases, endocrine pharmacology, or full laboratory reference-range terminology.

## Next Stage

Recommended next step: Anatomy/Tissue Core v1 if Bioinformatics retrieval needs stronger tissue normalization, or Cardio-Immune Core v1 if the priority is broader clinical and Meta Analysis disease coverage.
