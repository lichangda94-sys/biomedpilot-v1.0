# Stage 2.1 Medical Vocabulary Coverage Report

## Scope

Stage 2.1 expands the shared medical vocabulary mini coverage for BioMedPilot. The change is limited to the default local assets and lookup contract so Bioinformatics and Meta Analysis can resolve common Chinese biomedical topics without `data/medical_terms/medical_terms_index.sqlite`.

## Updated Assets

- `data/medical_terms/zh_term_overrides.json` now contains curated Chinese entry points for oncology diseases, common non-oncology diseases, pathology/clinical modifiers, outcomes, and bioinformatics data modalities.
- `data/medical_terms/mini_medical_terms_index.json` now contains the same core concepts as a built-in fallback index, with English labels, synonyms, abbreviations, MeSH terms, and TCGA/GTEx cross references where applicable.
- `data/medical_terms/source_metadata.json` records the Stage 2.1 mini coverage version.

## Acceptance Coverage

- `脑胶质瘤`: glioma, glioblastoma, TCGA-GBM, TCGA-LGG, GTEx Brain.
- `食管鳞癌`: ESCC and esophageal squamous cell carcinoma; no thyroid/PTC leakage.
- `乳头状甲状腺癌`: PTC, papillary thyroid carcinoma, TCGA-THCA; no ESCC leakage.
- `肺腺癌`: lung adenocarcinoma, LUAD, TCGA-LUAD.
- `肝细胞癌`: hepatocellular carcinoma, HCC, TCGA-LIHC.
- `糖尿病`: Diabetes Mellitus, diabetes, diabetic, MeSH Diabetes Mellitus.
- `肥胖`: Obesity, BMI, body mass index, MeSH Obesity.
- Data modality terms enter `data_type_terms_en` through lookup-backed search translation drafts.

## Notes

The optional sqlite index remains preferred when present. The built-in mini index and override files are intentionally curated and package-local; they are not a replacement for a full ontology build.
