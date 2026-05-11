# Shared Medical Vocabulary Cardiovascular Core v1

## Scope

Cardiovascular Core v1 adds a curated cardiovascular vocabulary layer for Bioinformatics topic search and Meta Analysis question parsing. It focuses on high-frequency cardiovascular diseases, phenotypes, risk factors, and biomarkers used in translational research, GEO/GTEx/SRA query drafting, and PubMed/MeSH query drafting.

This stage does not import a full cardiovascular ontology. It keeps the project-local curated vocabulary strategy used by the oncology, endocrine/metabolic, anatomy/tissue, bioinformatics modality, and meta-analysis term cores.

## Covered Areas

The checklist covers 80 cardiovascular concepts across:

- Hypertension and blood pressure abnormalities: hypertension, essential hypertension, secondary hypertension, pulmonary hypertension, isolated systolic hypertension, prehypertension, hypotension.
- Coronary and ischemic heart disease: coronary artery disease, coronary heart disease, ischemic heart disease, myocardial infarction, acute myocardial infarction, acute coronary syndrome, and angina subtypes.
- Heart failure and cardiomyopathy: heart failure, HFrEF, HFpEF, cardiomyopathy, and common cardiomyopathy subtypes.
- Arrhythmia: arrhythmia, atrial fibrillation, atrial flutter, ventricular tachycardia, ventricular fibrillation, bradycardia, tachycardia, and long QT syndrome.
- Atherosclerosis and vascular disease: atherosclerosis, arteriosclerosis, peripheral artery disease, carotid artery disease, aneurysm concepts, vascular calcification, and endothelial dysfunction.
- Cerebrovascular disease: stroke, ischemic stroke, hemorrhagic stroke, TIA, cerebral infarction, intracerebral hemorrhage, and subarachnoid hemorrhage.
- Thrombosis and embolism: thrombosis, VTE, DVT, pulmonary embolism, and arterial thrombosis.
- Valvular and structural heart disease: valvular heart disease, aortic stenosis, mitral regurgitation, mitral stenosis, congenital heart disease.
- Cardiovascular risk factors and phenotypes: dyslipidemia, hypercholesterolemia, obesity, diabetes, smoking, inflammation, vascular stiffness, arterial stiffness, LVH, and ejection fraction.
- Cardiovascular biomarkers: troponin, cTnI, cTnT, BNP, NT-proBNP, CRP, LDL cholesterol, HDL cholesterol, triglycerides, total cholesterol, lipoprotein(a), and homocysteine.

## Cross-Core Boundaries

Diabetes, obesity, dyslipidemia, hypercholesterolemia, HDL, and LDL overlap with Endocrine & Metabolic Core v1. This stage does not create conflicting duplicate concepts for those established endocrine/metabolic entries. Cardiovascular checklist rows point to existing concept IDs where appropriate, while new cardiovascular biomarker concepts are kept as biomarker or phenotype records rather than disease concepts.

Heart, artery, whole blood, lung, liver, and brain mappings rely on Anatomy / Tissue Core v1 and GTEx tissue candidates. Tissue terms are search auxiliaries only: `heart` or `artery` must not imply cardiovascular disease by themselves.

## Context Boundaries

Bioinformatics context may output disease terms, abbreviations, MeSH terms, tissue terms, GTEx tissue candidates, data modality terms, and GEO/GTEx/SRA helper terms. It must not expose PICO, effect measure, publication type, or PubMed-only outputs as primary results.

Meta Analysis context may output cardiovascular disease terms, MeSH/PubMed query terms, exposure and risk-factor terms, outcome terms, and auxiliary study design or effect-measure terms. It must not expose TCGA/GEO/GTEx dataset candidates as primary results.

## Short Token Handling

High-risk cardiovascular tokens include `CAD`, `CHD`, `MI`, `PH`, `AF`, `VT`, `VF`, `PE`, `LDL`, `HDL`, `CRP`, `BNP`, and `EF`. These are matched as exact short tokens and carry ambiguity notes where relevant. Biomarker tokens such as `LDL`, `HDL`, `CRP`, and `BNP` are not disease concepts. `EF` is a phenotype token and should not be confused with Meta Analysis effect measures.

## Negative Expansion Rules

The vocabulary intentionally avoids these automatic expansions:

- Hypertension is not the same as pulmonary hypertension.
- Pulmonary hypertension is not essential hypertension.
- Myocardial infarction is not stroke or cerebral infarction.
- Heart failure is not cardiomyopathy.
- Atrial fibrillation is not all arrhythmia.
- Atherosclerosis is not coronary artery disease.
- Troponin, BNP, CRP, LDL, HDL, triglycerides, and homocysteine are biomarkers, not disease concepts.
- Heart and artery tissue terms do not imply cardiovascular disease.

## Coverage Audit

`data/medical_terms/reference_checklists/cardiovascular_core_checklist.json` is audited by `scripts/audit_medical_vocabulary_coverage.py`. The audit report includes cardiovascular total count, covered count, missing count, coverage percentage, subcategory coverage, high-risk ambiguity terms, and quality gate status. Consolidation summary fields continue to include all core checklist coverage, total runtime concepts, total zh overrides, and total high-risk ambiguity terms.

## Remaining Gaps

The stage intentionally does not cover rare inherited arrhythmia syndromes, detailed congenital heart disease anatomy, full lipid disorder ontology, pharmacology classes, procedures, devices, ECG waveform terminology, or complete vascular bed-specific disease terminology.

## Next Stage

The recommended next vocabulary package is Immune & Inflammatory Core v1. A later External Ontology Subset Import v1 can selectively import authoritative cardiovascular subsets once the curated schemas and context isolation behavior remain stable.
