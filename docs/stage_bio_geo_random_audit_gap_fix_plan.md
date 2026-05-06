# Stage Bio GEO Random Audit Gap Fix Plan

## 输入材料

- 审计报告：`docs/stage_bio_geo_random_recognition_audit.md`
- 机器结果：`logs/validation/geo_random_recognition_audit.jsonl`
- 基线审计 seed：`202605`
- 基线下载模式：`metadata_only`

## 失败类型归纳

### 表达矩阵缺失的 GSE

以下数据集在 metadata-only 审计中成功下载 family SOFT / Series Matrix，但未识别到可直接进入分析的表达矩阵：

- `GSE217851`：RNA-seq analysis in thyroid cancer cells knocking down METTL3
- `GSE221088`：Circulating small extracellular vesicle-based miRNA classifier for follicular thyroid carcinoma
- `GSE231733`：Bulk RNA-sequencing of A549 cells transduced with Ad5 vector
- `GSE173882`：ELF5 regulates epithelial integrity independently of EHF
- `GSE287799`：JQ1/mock treated T cells from lung cancer pleural effusions
- `GSE315960`：Melanoma phenotypic plasticity and therapeutic resistance

### 只有 metadata 的 GSE

本轮 `metadata_only` 只下载 family SOFT 和 Series Matrix，因此以下数据集表现为“只有 metadata，表达矩阵需要 supplementary 再判断”：

- `GSE217851`
- `GSE221088`
- `GSE231733`
- `GSE173882`
- `GSE287799`
- `GSE315960`

`GSE236879` 和 `GSE238207` 在 Series Matrix / SOFT 容器中已经被识别到表达矩阵线索，readiness 可继续。

### 候选分组成功的 GSE

- `GSE236879`：metastatic vs primary，3 vs 3，符合 NSCLC brain metastatic / primary tumor tissue 结构。
- `GSE238207`：normal / melanoma / nevus-like 多组结构，需人工选择正式比较组。
- `GSE221088`：follicular thyroid carcinoma vs follicular thyroid adenoma，样本数充足，但数据类型为 miRNA/sEV 诊断研究，分析潜力不建议。
- `GSE173882`：siELF5 vs siNC 结构可从标题推断，但需要 supplementary 表达矩阵。
- `GSE315960`：DMSO / vemurafenib / trametinib 结构存在，但细胞系和剂量信息混杂，需降置信度并人工确认。

### 候选分组误判的 GSE

- `GSE315960`：`A375_GFPsg_DMSO_rep1` 被错误拆出 `control:375`，原因是 `A375 control cells` 中的细胞系编号 `375` 被当作 control 附近样本数。
- `GSE287799`：`JQ1/mock` 处理结构被报告成 `tumor vs primary`，说明 summary/overall design 的肿瘤语义干扰了逐样本处理分组。
- `GSE217851`：METTL3 knockdown 细胞系实验被概括成 `tumor vs control`，说明 “cancer cells” 被误作肿瘤样本组。
- `GSE231733`：A549/Ad5 转导结构没有形成可用处理分组，说明病毒载体/处理名需要作为低置信候选，而不是直接丢弃或误判。

### A375 / 细胞系误判证据

`GSE315960` 的样本标题示例：

- `A375_GFPsg_DMSO_rep1`
- `A375_GFPsg_Tram_rep1`

基线报告中的错误输出：

- `software candidate groups: tumor vs control {'control': 375, 'treated': 1, 'tumor': 1}`

根因：

- `A375` 中的数字 `375` 被 `_number_near_label()` 识别为 control 附近的样本数。
- `A375` 是细胞系名称，应该作为样本属性，不应作为组标签或组样本数来源。

### supplementary 文件优先级缺口

本轮 metadata-only 暴露的主要缺口是：多数 GSE 需要 supplementary 中的 processed expression/count matrix 才能分析。下一轮应优先识别并推荐：

- `count` / `counts` / `raw_counts` / `readcount`
- `TPM` / `FPKM` / `RPKM`
- `normalized`
- `expression` / `expr` / `matrix`
- `.txt` / `.tsv` / `.csv` / `.xlsx` 及单文件 gzip

不应默认推荐：

- `CEL`
- `RAW.tar`
- `FASTQ`
- `BAM`
- `SRA`
- `CRAM`
- 大型 tar archive
- image / PDF 等非表达矩阵补充文件

## 本阶段修复点

| 修复点 | 代码模块 |
|---|---|
| 细胞系名称不作为主要分组 | `app/bioinformatics/services/geo_metadata_profile_service.py`, `app/bioinformatics/group_preview.py` |
| 数值、剂量、时间点、replicate、batch 不作为高置信分组 | `app/bioinformatics/services/geo_metadata_profile_service.py`, `app/bioinformatics/group_preview.py` |
| sample-level 分组置信度更保守 | `app/bioinformatics/services/geo_metadata_profile_service.py`, `app/bioinformatics/group_preview.py` |
| supplementary expression candidate 优先级字段 | `app/bioinformatics/services/geo_metadata_profile_service.py` |
| 随机审计报告增加误判与 supplementary 统计 | `scripts/bio_geo_random_recognition_audit.py` |
| 回归测试覆盖细胞系、剂量、时间点、raw 文件跳过 | `tests/bioinformatics/` |

## 验证方式

修复后继续运行：

```bash
python3 scripts/bio_geo_random_recognition_audit.py \
  --queries "thyroid cancer,breast cancer,lung cancer,colorectal cancer,melanoma" \
  --per-query 2 \
  --max-total 8 \
  --seed 202605 \
  --download-mode metadata_only \
  --max-file-mb 50 \
  --max-total-mb 300 \
  --output docs/stage_bio_geo_random_recognition_audit.md
```

并补充：

```bash
python3 scripts/bio_geo_random_recognition_audit.py \
  --queries "thyroid cancer,breast cancer,lung cancer" \
  --per-query 2 \
  --max-total 6 \
  --seed 202606 \
  --download-mode metadata_plus_small_supplementary \
  --max-file-mb 30 \
  --max-total-mb 200 \
  --output docs/stage_bio_geo_random_supplementary_audit.md
```
