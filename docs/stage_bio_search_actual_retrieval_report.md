# Stage B1 Bioinformatics Search Actual Retrieval Report

## Scope

This report records Bioinformatics-only data source search checks for GEO/GSE, TCGA/GDC candidates, and GTEx normal references. PubMed, Web of Science, Embase, CNKI, Zotero, EndNote, and Meta Analysis literature retrieval are out of scope.

## Live GEO Checks

Date: 2026-05-03

| Input | Recognized Chinese Disease | English Disease Terms | First GEO Query | Disease In Query | Broad Guard | TCGA | GTEx | Live GEO Result Check | UI Check |
|---|---|---|---|---|---|---|---|---|---|
| 脑胶质瘤 | 脑胶质瘤; 胶质瘤 | glioma; brain glioma; glioblastoma | `glioma AND "expression profiling"` | yes | no | TCGA-GBM; TCGA-LGG | Brain | Relevant glioma/GSE results returned; top results include glioma or glioblastoma in title/summary. | UI shows disease terms, GEO query draft, TCGA table, GTEx table, query_used, result count. |
| 食管鳞癌 | 食管鳞癌; 食道鳞癌; 食管鳞状细胞癌 | esophageal squamous cell carcinoma; ESCC | `"esophageal squamous cell carcinoma" AND "expression profiling"` | yes | no | TCGA-ESCA | Esophagus | Relevant ESCC/GSE results returned; no thyroid leakage observed. | UI avoids PubMed/Meta copy and shows disease-specific queries. |
| 乳头状甲状腺癌 | 甲状腺癌; 乳头状甲状腺癌 | thyroid cancer; papillary thyroid carcinoma; PTC | `"thyroid cancer" AND "expression profiling"` | yes | no | TCGA-THCA | Thyroid | Relevant thyroid cancer/GSE results returned; no ESCC leakage observed. | TCGA appears as specific project row, not generic TCGA label. |
| 肺腺癌 | 肺腺癌 | lung adenocarcinoma; lung cancer | `"lung adenocarcinoma" AND "expression profiling"` | yes | no | TCGA-LUAD | Lung | Relevant lung adenocarcinoma/lung cancer GSE results returned. | GTEx Lung appears as normal reference. |
| 肝细胞癌 | 肝细胞癌 | hepatocellular carcinoma; liver cancer | `"hepatocellular carcinoma" AND "expression profiling"` | yes | no | TCGA-LIHC | Liver | Relevant HCC/liver cancer GSE results returned. | Query_used and relevance reason are available per row. |
| 肥胖与甲状腺癌 | 甲状腺癌; 肥胖 | thyroid cancer; Obesity | `"thyroid cancer" AND "expression profiling"` | yes | no | TCGA-THCA | Thyroid; Adipose | Relevant thyroid cancer GSE results returned. Obesity is recognized but not yet prioritized in the first GEO query. | Record as future ranking/query-composition issue, not a vocabulary expansion task. |
| 糖尿病相关转录组 | 糖尿病 | Diabetes Mellitus; diabetes; diabetic | `"Diabetes Mellitus" AND transcriptome` | yes | no | none | Pancreas | Relevant diabetes transcriptome/GSE results returned. | No TCGA table rows when no oncology project mapping exists. |

## Issues Recorded

- Multi-concept Bioinformatics queries such as `肥胖与甲状腺癌` currently prioritize the oncology disease term first. This is acceptable for Stage B1/B2 disease-aware guard behavior, but a later search-ranking pass may add combined exposure-disease GEO query variants.
- The local Python certificate store initially failed NCBI HTTPS validation. GEO search now uses the installed `certifi` CA bundle when available and keeps certificate verification enabled.

## Boundary Confirmation

- GEO execution uses disease-aware query candidates when disease terms are present.
- Platform-only broad GEO queries are blocked unless supplemental broad search is explicitly requested.
- TCGA/GDC project candidates are displayed separately from GEO query drafts.
- GTEx normal tissue references are displayed separately from GEO query drafts.
- PubMed and other literature databases are not shown in the Bioinformatics data source UI.
