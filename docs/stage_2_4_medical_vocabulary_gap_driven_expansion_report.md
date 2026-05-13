# Stage 2.4 Medical Vocabulary Gap-Driven Expansion

## Scope

Stage 2.4 expands the shared mini medical vocabulary only where the reference
coverage audit exposed practical gaps. It does not change Bioinformatics UI,
Meta Analysis UI, retrieval execution logic, or module boundaries.

Updated runtime inputs:

- `data/medical_terms/mini_medical_terms_index.json`
- `data/medical_terms/zh_term_overrides.json`
- `data/medical_terms/source_metadata.json`

## Gap Inputs

The expansion targets checklist gaps from:

- NCI GDC TCGA Study Abbreviations for TCGA project coverage.
- GTEx Portal tissue groups and tissue site identifiers for normal tissue
  candidate coverage.
- Common Meta-analysis retrieval terminology for effect sizes and publication
  exclusion filters.

## Added TCGA Project Coverage

| Project | Added vocabulary anchor | Chinese triggers |
| --- | --- | --- |
| TCGA-ACC | adrenocortical carcinoma | 肾上腺皮质癌, 肾上腺皮质肿瘤 |
| TCGA-DLBC | diffuse large B-cell lymphoma | 弥漫大B细胞淋巴瘤, 弥漫大B细胞性淋巴瘤 |
| TCGA-MESO | mesothelioma | 间皮瘤, 恶性间皮瘤 |
| TCGA-PCPG | pheochromocytoma and paraganglioma | 嗜铬细胞瘤, 副神经节瘤 |
| TCGA-SARC | sarcoma | 肉瘤, 软组织肉瘤 |
| TCGA-TGCT | testicular germ cell tumor | 睾丸生殖细胞肿瘤, 睾丸癌 |
| TCGA-THYM | thymoma | 胸腺瘤, 胸腺肿瘤 |
| TCGA-UCS | uterine carcinosarcoma | 子宫癌肉瘤 |
| TCGA-UVM | uveal melanoma | 葡萄膜黑色素瘤, 眼黑色素瘤 |

These terms are intended for Bioinformatics dataset candidate generation. In
`meta_analysis` context, TCGA candidates are still filtered out by shared
context logic.

## Added GTEx Tissue Coverage

| GTEx tissue candidate | Chinese triggers |
| --- | --- |
| Spleen | 脾脏, 脾 |
| Pituitary | 垂体 |
| Adrenal Gland | 肾上腺 |
| Testis | 睾丸 |

Some tumor entries also received approximate GTEx normal tissue candidates when
there is a clear practical match, such as adrenal gland for ACC/PCPG and testis
for TGCT. Tumors without an appropriate GTEx tissue group, such as thymoma and
uveal melanoma, keep disease and TCGA coverage without inventing a misleading
GTEx candidate.

## Added Meta Analysis Term Coverage

Effect-size and interval terms added:

- effect size
- standardized mean difference / SMD
- mean difference / MD
- weighted mean difference / WMD
- confidence interval / CI

Publication exclusion/filter terms added:

- preprint
- study protocol
- duplicate publication
- non-human study
- in vitro study

These terms populate `outcome_terms`, `abbreviations`, or
`publication_type_terms` only. They do not produce GEO, TCGA, or GTEx retrieval
candidates in Meta Analysis context.

## Tests

Coverage is locked by
`tests/shared/test_medical_vocabulary_systematic_coverage.py`:

- `test_stage_2_4_gap_driven_tcga_project_mapping`
- `test_stage_2_4_gap_driven_gtex_tissue_mapping`
- `test_stage_2_4_gap_driven_meta_effect_size_terms`
- `test_stage_2_4_gap_driven_publication_exclusion_terms`

## Remaining P2 Gaps

This stage does not attempt full ontology parity for all rare cancers,
histologic subtypes, immune diseases, exposures, interventions, or every GTEx
sub-tissue label. Those remain better suited to the optional full ontology
index backed by MONDO, DOID, NCIt, MeSH, and EFO.
