# Stage Bio GEO Random Recognition Audit

## 测试配置

- seed: `202605`
- queries: `thyroid cancer, breast cancer, lung cancer, colorectal cancer, melanoma`
- per-query: `2`
- max-total: `8`
- download-mode: `metadata_only`
- max-file-mb: `50`
- max-total-mb: `300`
- keep-files: `False`
- workdir: cleaned after run

## 总体统计

- 测试 GSE 数: 8
- profile 成功数: 8
- 下载成功数: 8
- expression matrix 识别成功数: 2
- sample metadata 识别成功数: 8
- candidate comparisons 成功数: 5
- group preview 成功数: 8
- readiness 可继续数: 2

## 每个 GSE 结果表

| GSE | query | 推荐等级 | 样本数 | 候选分组 | 表达矩阵 | 样本注释 | 基因/平台注释 | 是否可继续 | 主要失败原因 |
|---|---|---|---:|---|---|---|---|---|---|
| GSE217851 | thyroid cancer | 中 | 4 | control:1, tumor:1 | 否 | 是 | 是 | 否 | 缺表达矩阵 |
| GSE221088 | thyroid cancer | 不建议 | 160 | follicular thyroid carcinoma:84, follicular thyroid adenoma:76 | 否 | 是 | 是 | 否 | 缺表达矩阵 |
| GSE231733 | breast cancer | 中 | 2 | ad5 transduction:1, ad5 transduction and expression of sars-cov-2 nucleocapsid:1 | 否 | 是 | 是 | 否 | 缺表达矩阵 |
| GSE173882 | breast cancer | 不建议 | 6 | t47d sielf5:3, t47d sinc:3 | 否 | 是 | 是 | 否 | 缺表达矩阵 |
| GSE236879 | lung cancer | 高 | 6 | nsclc brain metastatic tumor tissue:3, nsclc primary tumor tissue:3 | 是 | 是 | 是 | 是 | 无 |
| GSE287799 | lung cancer | 不建议 | 6 | jq1:3, mock:3 | 否 | 是 | 是 | 否 | 缺表达矩阵 |
| GSE315960 | melanoma | 中 | 27 | 1 um vemurafenib:9, 20 nm trametinib:9, dmso:9 | 否 | 是 | 是 | 否 | 缺表达矩阵 |
| GSE238207 | melanoma | 中 | 26 | normal:10, melanoma pt:6, comonnevus:5, dysplasticnevus:5 | 是 | 是 | 是 | 是 | 无 |

## 错误类型归纳

- 缺表达矩阵或表达矩阵未识别: 6
- 未生成候选分组: 3
- 数据类型不支持或不建议: 3

## 人工复核摘要

### GSE217851

- query: thyroid cancer
- title: RNA-seq analysis in thyroid cancer cells knocking down METTL3
- overall design: We knocked down METTL3 in BCPAP cells and performed the RNA-seq analysis in order to exam the transcriptome after METTL3 knockdown
- sample title examples: Contral replication 1；Contral replication 2；replication 1 of colony 1 knocking down METTL3 in cells；replication 1 of colony 3 knocking down METTL3 in cells
- characteristics examples: 无
- software candidate groups: tumor vs control {'control': 1, 'tumor': 1}
- downloaded files: GSE217851_family.soft.gz, GSE217851_series_matrix.txt.gz
- recognized file types: geo_soft_container, geo_series_matrix_container
- warnings: 无
- improvement suggestions: project_recognition: improve expression matrix detection or supplementary prioritization

### GSE221088

- query: thyroid cancer
- title: Circulating small extracellular vesicle-based miRNA classifier for follicular thyroid carcinoma: a multicenter diagnostics study
- overall design: 21 FTC plasma samples and 20 FTA plasma samples were collected. EV long RNAs, cell-free long RNAs, EV miRNAs, and cell-free miRNAs were pairwise detected. Cell-free small and long RNA libraries were not prepared for two ...
- sample title examples: FTC-1-EV-Small-RNA；FTC-2-EV-Small-RNA；FTC-3-EV-Small-RNA；FTC-4-EV-Small-RNA；FTC-5-EV-Small-RNA
- characteristics examples: 无
- software candidate groups: 无
- downloaded files: GSE221088_family.soft.gz, GSE221088_series_matrix.txt.gz
- recognized file types: geo_soft_container, geo_series_matrix_container
- warnings: 无
- improvement suggestions: project_recognition: improve expression matrix detection or supplementary prioritization; geo_metadata_profile: improve sample-level group evidence extraction

### GSE231733

- query: breast cancer
- title: Bulk RNA-sequencing of A549 cells transduced with Ad5 empty vector (GFP) or Ad5 expressing SARS-CcV-2 nucleocapsid (AdN)
- overall design: To mimic the abundant expression of human-infecting coronaviruse nucleocapsid protein in infected cells, replication-deficient recombinant human adenovirus type‐5 was used as the vector. Recombinant adenovirus type‐5 exp...
- sample title examples: A549 transduced with Ad5 empty vector；A549 transduced with Ad5 expressing SARS-CcV-2 nucleocapsid
- characteristics examples: 无
- software candidate groups: 无
- downloaded files: GSE231733_family.soft.gz, GSE231733_series_matrix.txt.gz
- recognized file types: geo_soft_container, geo_series_matrix_container
- warnings: 无
- improvement suggestions: project_recognition: improve expression matrix detection or supplementary prioritization; geo_metadata_profile: improve sample-level group evidence extraction

### GSE173882

- query: breast cancer
- title: ELF5 regulates epithelial integrity independently of EHF [RNA-seq]
- overall design: Three ChIP-seq replicates
- sample title examples: T47D siNC rep1；T47D siNC rep2；T47D siNC rep3；T47D siELF5 rep1；T47D siELF5 rep2
- characteristics examples: 无
- software candidate groups: 无
- downloaded files: GSE173882_family.soft.gz, GSE173882_series_matrix.txt.gz
- recognized file types: geo_soft_container, geo_series_matrix_container
- warnings: 无
- improvement suggestions: project_recognition: improve expression matrix detection or supplementary prioritization; geo_metadata_profile: improve sample-level group evidence extraction

### GSE236879

- query: lung cancer
- title: CircRNAs differentially expressed in brain metastases and primary lung cancer tissues of three pairs of non-small cell lung cancer patients with brain metastases
- overall design: In the First Affiliated Hospital of Nanjing Medical University, we searched three patients with brain metastasis of non-small cell lung cancer, and obtained the primary lung cancer tissue and brain metastasis cancer tiss...
- sample title examples: RNAs_NSCLCBM_PT1；RNAs_NSCLCBM_PT2；RNAs_NSCLCBM_PT3；RNAs_NSCLCBM_BM1；RNAs_NSCLCBM_BM2
- characteristics examples: 无
- software candidate groups: metastatic vs primary {'metastatic': 3, 'primary': 3}
- downloaded files: GSE236879_family.soft.gz, GSE236879_series_matrix.txt.gz
- recognized file types: geo_soft_container, geo_series_matrix_container
- warnings: 无
- improvement suggestions: 无

### GSE287799

- query: lung cancer
- title: Epigenetic modulation of polyamine biosynthetic pathways rectifies T cell dysfunction to enhance anti-tumor immunity in lung cancer [RNA-seq]
- overall design: CD3+ T cells were isolated from malignant pleural effusions (MPE) of three lung cancer patients and treated with mock and JQ1 (500nM) for three consecutive days. At day 7, total cellular RNA was extracted for RNA-seq.
- sample title examples: L197-JQ1；L197-MOCK；L204-JQ1；L204-Mock；L210-JQ1
- characteristics examples: 无
- software candidate groups: tumor vs primary {'primary': 1, 'treated': 1, 'tumor': 1}
- downloaded files: GSE287799_family.soft.gz, GSE287799_series_matrix.txt.gz
- recognized file types: geo_soft_container, geo_series_matrix_container
- warnings: 无
- improvement suggestions: project_recognition: improve expression matrix detection or supplementary prioritization

### GSE315960

- query: melanoma
- title: Epigenetic regulation of melanoma phenotypic plasticity and therapeutic resistance
- overall design: RNA-seq profiling was performed on A375 control cells or TADA2BKO cells treated with DMSO, 1 μM vemurafenib, or 20 nM trametinib for 24 hours.
- sample title examples: A375_GFPsg_DMSO_rep1；A375_GFPsg_DMSO_rep2；A375_GFPsg_DMSO_rep3；A375_GFPsg_Tram_rep1；A375_GFPsg_Tram_rep2
- characteristics examples: 无
- software candidate groups: tumor vs control {'control': 375, 'treated': 1, 'tumor': 1}
- downloaded files: GSE315960_family.soft.gz, GSE315960_series_matrix.txt.gz
- recognized file types: geo_soft_container, geo_series_matrix_container
- warnings: 无
- improvement suggestions: project_recognition: improve expression matrix detection or supplementary prioritization

### GSE238207

- query: melanoma
- title: Laser Capture Microdissection Provides a Novel Molecular Profile of Human Primary Cutaneous Melanoma
- overall design: We performed laser capture microdissection (LCM) and gene expression profiling of patient-derived frozen sections of pigmented lesions and primary cutaneous melanoma.
- sample title examples: Normal.DER-1；Normal.DER-2；Normal.DER-3；Normal.DER-4；Normal.DER-5
- characteristics examples: 无
- software candidate groups: tumor vs primary {'primary': 1, 'tumor': 1}
- downloaded files: GSE238207_family.soft.gz, GSE238207_series_matrix.txt.gz
- recognized file types: geo_soft_container, geo_series_matrix_container
- warnings: 无
- improvement suggestions: 无


## 下一步改进建议

- project_recognition: improve expression matrix detection or supplementary prioritization: 6
- geo_metadata_profile: improve sample-level group evidence extraction: 3

## Skipped GSE

- GSE291054 / thyroid cancer: not_profiled_by_seed_budget
- GSE296099 / thyroid cancer: not_profiled_by_seed_budget
- GSE307253 / thyroid cancer: not_profiled_by_seed_budget
- GSE310793 / thyroid cancer: not_profiled_by_seed_budget
- GSE315375 / thyroid cancer: not_profiled_by_seed_budget
- GSE103254 / thyroid cancer: not_profiled_by_seed_budget
- GSE104005 / thyroid cancer: not_profiled_by_seed_budget
- GSE104006 / thyroid cancer: not_profiled_by_seed_budget
- GSE106306 / thyroid cancer: not_profiled_by_seed_budget
- GSE129878 / thyroid cancer: not_profiled_by_seed_budget
- GSE129879 / thyroid cancer: not_profiled_by_seed_budget
- GSE138198 / thyroid cancer: not_profiled_by_seed_budget
- GSE151179 / thyroid cancer: not_profiled_by_seed_budget
- GSE151180 / thyroid cancer: not_profiled_by_seed_budget
- GSE215328 / breast cancer: not_profiled_by_seed_budget
- GSE215331 / breast cancer: not_profiled_by_seed_budget
- GSE231911 / breast cancer: not_profiled_by_seed_budget
- GSE241872 / breast cancer: not_profiled_by_seed_budget
- GSE243273 / breast cancer: not_profiled_by_seed_budget
- GSE253691 / breast cancer: not_profiled_by_seed_budget
- GSE253692 / breast cancer: not_profiled_by_seed_budget
- GSE253693 / breast cancer: not_profiled_by_seed_budget
- GSE253694 / breast cancer: not_profiled_by_seed_budget
- GSE253695 / breast cancer: not_profiled_by_seed_budget
- GSE253697 / breast cancer: not_profiled_by_seed_budget
- GSE264572 / breast cancer: not_profiled_by_seed_budget
- GSE264576 / breast cancer: not_profiled_by_seed_budget
- GSE264577 / breast cancer: not_profiled_by_seed_budget
- GSE316905 / lung cancer: not_profiled_by_seed_budget
- GSE317309 / lung cancer: not_profiled_by_seed_budget
- GSE329204 / lung cancer: not_profiled_by_seed_budget
- GSE329205 / lung cancer: not_profiled_by_seed_budget
- GSE329206 / lung cancer: not_profiled_by_seed_budget
- GSE232282 / lung cancer: not_profiled_by_seed_budget
- GSE242413 / lung cancer: not_profiled_by_seed_budget
- GSE244427 / lung cancer: not_profiled_by_seed_budget
- GSE261469 / lung cancer: not_profiled_by_seed_budget
- GSE269696 / lung cancer: not_profiled_by_seed_budget
- GSE278453 / lung cancer: not_profiled_by_seed_budget
- GSE283535 / lung cancer: not_profiled_by_seed_budget
- GSE287025 / lung cancer: not_profiled_by_seed_budget
- GSE316110 / melanoma: not_profiled_by_seed_budget
- GSE316474 / melanoma: not_profiled_by_seed_budget
- GSE316620 / melanoma: not_profiled_by_seed_budget
- GSE316898 / melanoma: not_profiled_by_seed_budget
- GSE319305 / melanoma: not_profiled_by_seed_budget
- GSE319443 / melanoma: not_profiled_by_seed_budget
- GSE319449 / melanoma: not_profiled_by_seed_budget
- GSE329231 / melanoma: not_profiled_by_seed_budget
- GSE119540 / melanoma: not_profiled_by_seed_budget
- GSE12391 / melanoma: not_profiled_by_seed_budget
- GSE130244 / melanoma: not_profiled_by_seed_budget
- GSE255263 / melanoma: not_profiled_by_seed_budget
- GSE266234 / melanoma: not_profiled_by_seed_budget
- GSE268319 / melanoma: not_profiled_by_seed_budget
- GSE213940 / thyroid cancer: not_selected_by_seed_or_strata
- GSE284824 / thyroid cancer: not_selected_by_seed_or_strata
- GSE103996 / thyroid cancer: not_selected_by_seed_or_strata
- GSE113629 / thyroid cancer: not_selected_by_seed_or_strata
- GSE151088 / breast cancer: not_selected_by_seed_or_strata
- GSE173880 / breast cancer: not_selected_by_seed_or_strata
- GSE215326 / breast cancer: not_selected_by_seed_or_strata
- GSE262036 / breast cancer: not_selected_by_seed_or_strata
- GSE287798 / lung cancer: not_selected_by_seed_or_strata
- GSE287930 / lung cancer: not_selected_by_seed_or_strata
- GSE314392 / lung cancer: not_selected_by_seed_or_strata
- GSE241236 / lung cancer: not_selected_by_seed_or_strata
- GSE183445 / melanoma: not_selected_by_seed_or_strata
- GSE304149 / melanoma: not_selected_by_seed_or_strata
- GSE305296 / melanoma: not_selected_by_seed_or_strata
- GSE329586 / melanoma: not_selected_by_seed_or_strata
