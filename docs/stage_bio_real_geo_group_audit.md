# Stage Bio Real GEO Group Recognition Audit

## Scope

This audit used the current Bioinformatics GEO search and download services against five tumor topics:

- thyroid cancer
- lung adenocarcinoma
- breast cancer
- hepatocellular carcinoma
- glioma

For each topic, the first five GEO/GSE search results were reviewed. GEO family SOFT metadata and Series Matrix assets were downloaded in a temporary project under `/tmp/biomedpilot_geo_group_audit`. The temporary project was used only for capability testing and should not be treated as project data.

## Download Coverage

- 25 GEO candidates were selected from the five topic searches.
- 24 candidates completed protected family SOFT metadata download and Series Matrix discovery/download.
- `GSE300956` was not downloaded in this pass because its family SOFT file was about 295 MB and stalled the first unprotected run.
- No supplementary archive was bulk-downloaded in this audit. Many current RNA-seq entries expose expression through supplementary/SRA assets rather than populated Series Matrix tables, so supplementary download selection still needs user confirmation.

## Recognition Findings

After downloading 24 candidates:

- `geo_soft_container`: 24
- `geo_series_matrix_container`: 28
- files with sample metadata role: 52
- files with expression matrix role: 2
- unknown files: 0

Key finding: most recent RNA-seq GEO Series Matrix files contain sample metadata and an `ID_REF/GSM` header but no expression rows. These must not be counted as usable expression matrices. The recognition layer now requires at least one table data row before assigning the `expression_matrix` role to a Series Matrix container.

## Group Preview Findings

The updated group preview recovered useful candidate groups from real GEO metadata:

- `GSE301150`: `benign_malignant`, malignant 20 / benign 18
- `GSE304653`: `treatment`, sedentary 12 / exercise 11
- `GSE325873`: `treatment`, HK2-targeted siRNA 6 / non-targeting control siRNA 6
- `GSE213940`: `treatment`, control 3 / gamma irradiated 3 / valproic acid and gamma irradiated 3 / valproic acid 1
- `GSE319666`: `sample_histology`, AAH 68 / ADC 49 / normal 48 / AIS-MIA 12

Observed gaps and fixes:

- Family SOFT SAMPLE blocks were previously not parsed for group preview. They are now parsed directly.
- `benign/malignant` was not treated as a high-priority grouping field. It is now recognized as `benign_malignant`.
- Protocol text such as `extract_protocol_ch1` could be mistaken for a grouping field. It is now excluded from group candidate selection.
- Candidate group fields now require one value per sample, preventing duplicated title/protocol-derived labels from inflating group counts.
- Group preview now includes `sample_group_assignments`, which provides the explicit sample-to-group mapping needed after user confirmation.

## Downstream Analysis Check

Using real `GSE213940` Series Matrix data:

- Differential expression ran with explicit GSM group assignments: gamma irradiated vs control, 1000 rows tested in the audit run.
- Local over-representation enrichment ran against a user-supplied audit GMT file.
- Local Pearson correlation ran against the Series Matrix table block.

The analysis runners remain offline/local. They do not download GO/KEGG/MSigDB and do not infer formal comparison groups without user confirmation.

## Remaining Product Gaps

- Supplementary/SRA file selection is still the main bottleneck for recent RNA-seq GEO entries.
- UI should present metadata-only Series Matrix files as "样本信息已识别，表达矩阵需下载补充文件" rather than "表达矩阵已下载".
- Formal comparison setup should use `sample_group_assignments` as a confirmation preview, not as an automatic `comparison_config`.
- Enrichment requires a user-provided GMT file or a separately approved gene-set resource bundle.
- Correlation currently runs a local Pearson table; UI still needs a guided target-gene selection step.
