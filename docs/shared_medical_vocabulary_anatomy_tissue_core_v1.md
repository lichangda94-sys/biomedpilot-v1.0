# Shared Medical Vocabulary Anatomy / Tissue Core v1

## Scope

Anatomy / Tissue Core v1 adds curated organ, tissue, tissue-site, blood-tissue, and brain-region terms to the shared medical vocabulary. The goal is to improve Bioinformatics Chinese research-topic retrieval, GTEx tissue candidate generation, TCGA primary-site hints, and Meta Analysis disease-organ semantic understanding.

This stage does not import full UBERON, MeSH Anatomy, or NCIt anatomy. It adds a high-confidence operational subset that is useful for BioMedPilot retrieval.

## Why Tissue First

Bioinformatics queries often start from a disease plus tissue, or from a tissue alone. A tissue-only query must not become a cancer query. Explicit tissue vocabulary lets the lookup layer return `tissue_terms`, `gtex_tissue_candidates`, and `tcga_primary_site_candidates` without inventing disease concepts.

## GTEx Coverage

The checklist covers 59 GTEx tissue or tissue-site candidates, including adipose subcutaneous and visceral sites, adrenal gland, arteries, brain regions, breast mammary tissue, colon sites, esophagus sites, heart sites, kidney cortex, liver, lung, skeletal muscle, tibial nerve, ovary, pancreas, pituitary, prostate, skin sites, terminal ileum, spleen, stomach, testis, thyroid, uterus, vagina, whole blood, cultured fibroblasts, and EBV-transformed lymphocytes.

Coverage audit reports 59/59 GTEx candidates covered.

## TCGA Primary Site Coverage

The checklist includes 35 TCGA primary-site candidates, including breast, lung, liver, thyroid, colon, rectum, stomach, esophagus, pancreas, prostate, ovary, cervix, uterus, endometrium, kidney, bladder, brain, skin, head and neck, bile duct, adrenal gland, blood, bone marrow, lymph node, soft tissue, testis, and related sites.

Coverage audit reports 35/35 TCGA primary-site candidates covered.

## Chinese Coverage

Common Chinese organ and tissue inputs are mapped, including 甲状腺, 乳腺, 肺, 肝脏, 胰腺, 胃, 食管, 结肠, 直肠, 结直肠, 前列腺, 卵巢, 宫颈, 子宫, 子宫内膜, 肾脏, 膀胱, 脑, 皮肤, 血液, 骨髓, 淋巴结, 脂肪组织, 皮下脂肪, 内脏脂肪, 骨骼肌, 心脏, 动脉, 垂体, 肾上腺, 脾脏, and 小肠.

## Boundaries

Organ terms describe anatomy. Tissue terms describe biological sample material. Tissue-site terms identify a more specific sampled location such as Colon - Sigmoid or Esophagus - Mucosa. Blood-tissue terms cover whole blood, bone marrow, and lymphoid tissues. Brain-region terms preserve GTEx region specificity.

Tissue-only terms do not imply disease. Examples:

- thyroid does not imply thyroid cancer, PTC, or TCGA-THCA
- liver does not imply HCC or TCGA-LIHC
- lung does not imply LUAD or LUSC
- colon and rectum stay separate unless colorectal is explicit
- blood, bone marrow, and lymph node do not collapse into each other
- adipose tissue does not imply obesity

## Context Boundary

Bioinformatics context may consume tissue terms, GTEx tissue candidates, TCGA primary-site candidates, related disease categories, and retrieval helper terms.

Meta Analysis context may consume anatomy/tissue terms and disease-organ semantic hints. TCGA, GTEx, and GEO candidates are not emitted as primary Meta Analysis outputs.

## Remaining Gaps

This stage does not cover all UBERON anatomy, complete MeSH Anatomy, developmental anatomy, cell ontology, histologic microanatomy, or every GTEx metadata synonym.

## Next Stage

Recommended next step: Bioinformatics Modality Core v1 for data type and assay terms, or Meta Analysis Terms Core v1 for PICO, outcomes, designs, and effect-measure vocabulary.
