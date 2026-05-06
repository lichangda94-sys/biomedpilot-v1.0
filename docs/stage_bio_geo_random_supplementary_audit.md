# Stage Bio GEO Random Recognition Audit

## 测试配置

- seed: `202606`
- queries: `thyroid cancer, breast cancer, lung cancer`
- per-query: `2`
- max-total: `6`
- download-mode: `metadata_plus_small_supplementary`
- max-file-mb: `30`
- max-total-mb: `200`
- keep-files: `False`
- workdir: cleaned after run

## 总体统计

- 测试 GSE 数: 6
- profile 成功数: 6
- 下载成功数: 6
- expression matrix 识别成功数: 3
- sample metadata 识别成功数: 6
- candidate comparisons 成功数: 4
- group preview 成功数: 4
- readiness 可继续数: 3
- suspected_group_misclassification_count: 3
- cell_line_as_group_warnings: 0
- numeric_or_timepoint_group_warnings: 0
- low_confidence_group_count: 3
- high_confidence_group_count: 0
- supplementary_high_priority_count: 4
- expression_candidate_supplementary_count: 10

## 每个 GSE 结果表

| GSE | query | 推荐等级 | 样本数 | 候选分组 | 表达矩阵 | 样本注释 | 基因/平台注释 | 是否可继续 | 主要失败原因 |
|---|---|---|---:|---|---|---|---|---|---|
| GSE307253 | thyroid cancer | 中 | 6 | control:3, gdf15:3 | 是 | 是 | 是 | 是 | 无 |
| GSE284824 | thyroid cancer | 高 | 18 | control:9, knockout:9 | 是 | 是 | 是 | 是 | 无 |
| GSE173882 | breast cancer | 不建议 | 6 | 无 | 否 | 是 | 是 | 否 | 缺表达矩阵 |
| GSE173880 | breast cancer | 不建议 | 4 | 无 | 否 | 是 | 是 | 否 | 缺表达矩阵 |
| GSE314392 | lung cancer | 中 | 12 | control:1, treated:1 | 是 | 是 | 是 | 是 | 无 |
| GSE287930 | lung cancer | 不建议 | 2 | treated:1, tumor:1 | 否 | 是 | 是 | 否 | 缺表达矩阵 |

## 错误类型归纳

- 缺表达矩阵或表达矩阵未识别: 3
- 数据类型不支持或不建议: 3
- 未生成候选分组: 2
- supplementary 文件过大: 1
- raw 数据不可直接分析: 1

## 人工复核摘要

### GSE307253

- query: thyroid cancer
- title: GDF15 contributes to thyroid cancer progression and modulates thyroid cancer cell senescence in a p53-dependent manner.
- overall design: GDF15 expression was knocked down in thyroid cancer cell lines, and the control group was blank control. Set three repetitions for each group.
- sample title examples: NC1；NC2；NC3；Si1；Si2
- characteristics examples: 无
- software candidate groups: tumor vs control {'control': 1, 'tumor': 1, 'wild_type': 1}
- suspected group warnings: low_confidence:tumor vs control
- recommended expression supplementary: GSE307253_1_genes_fpkm_expression.txt.gz
- downloaded files: GSE307253_1_genes_fpkm_expression.txt.gz, GSE307253_family.soft.gz, GSE307253_series_matrix.txt.gz
- recognized file types: geo_soft_container, geo_series_matrix_container, expression_matrix
- warnings: 无
- improvement suggestions: 无

### GSE284824

- query: thyroid cancer
- title: CRISPR/Cas9-mediated deletion of MADD induces cell cycle arrest and apoptosis in anaplastic thyroid cancer cells
- overall design: RNA-seq profiling of 8505C, C643, and HtH7 cell lines and their derivatives based on CRISPR-Cas9 knockdown of the MADD gene.
- sample title examples: 8505C Control, replicate 1；8505C Control, replicate 2；8505C Control, replicate 3；8505C MADD knockout, replicate 1；8505C MADD knockout, replicate 2
- characteristics examples: 无
- software candidate groups: knockout vs control {'control': 9, 'knockout': 9}
- suspected group warnings: 无
- recommended expression supplementary: 无
- downloaded files: GSE284824_genes.txt.gz, GSE284824_family.soft.gz, GSE284824_series_matrix.txt.gz
- recognized file types: geo_soft_container, geo_series_matrix_container, raw_count_matrix
- warnings: 无
- improvement suggestions: 无

### GSE173882

- query: breast cancer
- title: ELF5 regulates epithelial integrity independently of EHF [RNA-seq]
- overall design: Three ChIP-seq replicates
- sample title examples: T47D siNC rep1；T47D siNC rep2；T47D siNC rep3；T47D siELF5 rep1；T47D siELF5 rep2
- characteristics examples: 无
- software candidate groups: 无
- suspected group warnings: 无
- recommended expression supplementary: 无
- downloaded files: GSE173882_family.soft.gz, GSE173882_series_matrix.txt.gz
- recognized file types: geo_soft_container, geo_series_matrix_container
- warnings: 无
- improvement suggestions: project_recognition: improve expression matrix detection or supplementary prioritization; geo_metadata_profile: improve sample-level group evidence extraction

### GSE173880

- query: breast cancer
- title: ELF5 regulates epithelial integrity independently of EHF [ChIP-seq]
- overall design: Three ChIP-seq replicates
- sample title examples: T47D ELF5 ChIP-seq rep1；T47D ELF5 ChIP-seq rep2；T47D ELF5 ChIP-seq rep3；T47D_input
- characteristics examples: 无
- software candidate groups: 无
- suspected group warnings: 无
- recommended expression supplementary: 无
- downloaded files: GSE173880_family.soft.gz, GSE173880_series_matrix.txt.gz
- recognized file types: geo_soft_container, geo_series_matrix_container
- warnings: 无
- improvement suggestions: project_recognition: improve expression matrix detection or supplementary prioritization; geo_metadata_profile: improve sample-level group evidence extraction

### GSE314392

- query: lung cancer
- title: The gene regulations by AGR2 in the lung cancer cell line PC9 under Gefitinib treatment.
- overall design: RNA-seq profile of PC9 cells with AGR2 knockdown (24 hr gefitinib), AGR2 overexpression (72 hr gefitinib), and their corresponding time-matched controls.
- sample title examples: PC9 control_24hrGef_rep1；PC9 control_24hrGef_rep2；PC9 control_24hrGef_rep3；PC9 shAGR2_24hrGef_rep1；PC9 shAGR2_24hrGef_rep2
- characteristics examples: 无
- software candidate groups: treated vs control {'control': 1, 'treated': 1}
- suspected group warnings: low_confidence:treated vs control
- recommended expression supplementary: GSE314392_TPM_Normalized_counts.xlsx
- downloaded files: GSE314392_TPM_Normalized_counts.xlsx, GSE314392_family.soft.gz, GSE314392_series_matrix.txt.gz
- recognized file types: geo_soft_container, geo_series_matrix_container, raw_count_matrix
- warnings: 无
- improvement suggestions: 无

### GSE287930

- query: lung cancer
- title: Epigenetic modulation of polyamine biosynthetic pathways rectifies T cell dysfunction to enhance anti-tumor immunity in lung cancer
- overall design: MPE CD3+ T cells were treated with or without 500 nM JQ1 for 3 days (D3R3, n=3). Multiplex single-cell sequencing analysis was performed using TotalSeq™-B antibodies (394645, 394647, 394635, and 394637, BioLegend) as per...
- sample title examples: Gene expression of JQ1, scRNAseq；Gene expression of MOCK, scRNAseq
- characteristics examples: 无
- software candidate groups: tumor vs treated {'treated': 1, 'tumor': 1}
- suspected group warnings: low_confidence:tumor vs treated
- recommended expression supplementary: 无
- downloaded files: GSE287930_family.soft.gz, GSE287930_series_matrix.txt.gz
- recognized file types: geo_soft_container, geo_series_matrix_container
- warnings: 无
- improvement suggestions: project_recognition: improve expression matrix detection or supplementary prioritization; geo_download: keep raw files opt-in and show safer processed alternatives


## 下一步改进建议

- project_recognition: improve expression matrix detection or supplementary prioritization: 3
- geo_metadata_profile: improve sample-level group evidence extraction: 2
- geo_download: keep raw files opt-in and show safer processed alternatives: 1

## Skipped GSE

- GSE291054 / thyroid cancer: not_profiled_by_seed_budget
- GSE296099 / thyroid cancer: not_profiled_by_seed_budget
- GSE310793 / thyroid cancer: not_profiled_by_seed_budget
- GSE315375 / thyroid cancer: not_profiled_by_seed_budget
- GSE103254 / thyroid cancer: not_profiled_by_seed_budget
- GSE103996 / thyroid cancer: not_profiled_by_seed_budget
- GSE104005 / thyroid cancer: not_profiled_by_seed_budget
- GSE104006 / thyroid cancer: not_profiled_by_seed_budget
- GSE113629 / thyroid cancer: not_profiled_by_seed_budget
- GSE129878 / thyroid cancer: not_profiled_by_seed_budget
- GSE129879 / thyroid cancer: not_profiled_by_seed_budget
- GSE138198 / thyroid cancer: not_profiled_by_seed_budget
- GSE151179 / thyroid cancer: not_profiled_by_seed_budget
- GSE151180 / thyroid cancer: not_profiled_by_seed_budget
- GSE215328 / breast cancer: not_profiled_by_seed_budget
- GSE215331 / breast cancer: not_profiled_by_seed_budget
- GSE231733 / breast cancer: not_profiled_by_seed_budget
- GSE231911 / breast cancer: not_profiled_by_seed_budget
- GSE241872 / breast cancer: not_profiled_by_seed_budget
- GSE243273 / breast cancer: not_profiled_by_seed_budget
- GSE253691 / breast cancer: not_profiled_by_seed_budget
- GSE253692 / breast cancer: not_profiled_by_seed_budget
- GSE253693 / breast cancer: not_profiled_by_seed_budget
- GSE253695 / breast cancer: not_profiled_by_seed_budget
- GSE253697 / breast cancer: not_profiled_by_seed_budget
- GSE262036 / breast cancer: not_profiled_by_seed_budget
- GSE264572 / breast cancer: not_profiled_by_seed_budget
- GSE264576 / breast cancer: not_profiled_by_seed_budget
- GSE316905 / lung cancer: not_profiled_by_seed_budget
- GSE317309 / lung cancer: not_profiled_by_seed_budget
- GSE329204 / lung cancer: not_profiled_by_seed_budget
- GSE329205 / lung cancer: not_profiled_by_seed_budget
- GSE232282 / lung cancer: not_profiled_by_seed_budget
- GSE236879 / lung cancer: not_profiled_by_seed_budget
- GSE242413 / lung cancer: not_profiled_by_seed_budget
- GSE244427 / lung cancer: not_profiled_by_seed_budget
- GSE261469 / lung cancer: not_profiled_by_seed_budget
- GSE269696 / lung cancer: not_profiled_by_seed_budget
- GSE278453 / lung cancer: not_profiled_by_seed_budget
- GSE283535 / lung cancer: not_profiled_by_seed_budget
- GSE287025 / lung cancer: not_profiled_by_seed_budget
- GSE213940 / thyroid cancer: not_selected_by_seed_or_strata
- GSE217851 / thyroid cancer: not_selected_by_seed_or_strata
- GSE221088 / thyroid cancer: not_selected_by_seed_or_strata
- GSE106306 / thyroid cancer: not_selected_by_seed_or_strata
- GSE151088 / breast cancer: not_selected_by_seed_or_strata
- GSE215326 / breast cancer: not_selected_by_seed_or_strata
- GSE264577 / breast cancer: not_selected_by_seed_or_strata
- GSE253694 / breast cancer: not_selected_by_seed_or_strata
- GSE287798 / lung cancer: not_selected_by_seed_or_strata
- GSE287799 / lung cancer: not_selected_by_seed_or_strata
- GSE241236 / lung cancer: not_selected_by_seed_or_strata
- GSE329206 / lung cancer: not_selected_by_seed_or_strata
