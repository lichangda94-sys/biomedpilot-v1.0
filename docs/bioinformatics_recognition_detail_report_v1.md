# Bioinformatics Recognition Detail Report V1

## 功能目标

Stage 2.7 为数据识别页增加只读识别详情和用户友好的 Markdown 导出。它用于解释单个 recognition run 或单个识别文件中识别到了哪些数据资产，而不是让用户直接阅读 `recognition_report.json`。

详情视图只读取已有识别产物：

- `recognized_data/current.json`
- `recognized_data/runs/<run_id>/recognition_report.json`
- `recognized_data/runs/<run_id>/recognized_files.json`
- 旧版导入的 `recognition_report.json`

查看详情不会修改 `current.json`，不会把历史记录写入“本次识别结果”。

## 详情页信息结构

详情页使用同一套 formatter 展示本次识别文件、历史 run 和旧版导入记录：

1. 顶部摘要：识别类型、当前状态、物种、gene ID 类型、数据内容、生成时间。
2. 输入文件信息：文件名、短路径、格式、大小、行列数、run id、识别时间。
3. 内容块识别结果：count、FPKM/TPM、已有 DEG、gene annotation、gene identifier metadata。
4. 样本列与分组推断：只显示表达矩阵样本列，过滤 DEG/stat/annotation 字段。
5. DEG comparison 识别：比较名、log2FC/pvalue/padj 原始列名、完整性状态。
6. Gene annotation 识别：已识别注释字段及用途。
7. 物种与 gene ID 判断依据：例如 `ENSMUSG -> Mus musculus`，或 GEO organism evidence。
8. Warning 与风险提示：按信息、注意、需要用户确认、阻塞分级。
9. 后续建议：标准化、结果浏览、富集输入、重新 DEG 前的分组确认、mouse 数据限制。
10. 技术详情折叠区：保留 machine-readable 摘要。

## 用户可见字段

综合 RNA-seq 表的主详情应显示：

- `RNA-seq 综合表达结果表`
- `Mus musculus`
- `Ensembl mouse gene ID`
- count 矩阵样本列数量和推断分组
- FPKM 矩阵样本列数量和用途
- DEG comparison 数量和每个 comparison 的列映射
- gene annotation 字段
- `差异结果来源：导入表格中的已有结果`

样本列展示必须排除：

- `gene_start`
- `gene_end`
- `gene_length`
- `gene_chr`
- `gene_strand`
- `gene_biotype`
- `gene_description`
- `*_log2FoldChange`
- `*_pvalue`
- `*_padj`
- `P.Value`
- `adj.P.Val`

## 技术详情字段

技术详情默认折叠，可包含：

- `file_kind`
- `semantic_type`
- `recognized_type`
- `species_group`
- `gene_id_type`
- `content_blocks` 摘要
- 过滤后的 `sample_columns`
- `recognition_report.json` 路径
- `recognized_files.json` 路径
- `current.json` 指向状态

技术详情是审计辅助信息，不作为主 UI 文案。

## Markdown 报告结构

导出按钮将报告写入：

```text
recognized_data/runs/<run_id>/recognition_report_user.md
```

报告包含：

- 项目与 run 摘要
- 输入文件信息
- 内容块摘要
- 样本列与分组推断预览
- DEG comparison 表
- gene annotation 字段
- species / gene ID 判断依据
- warnings
- 后续建议
- 技术附录摘要

报告不复制完整表达矩阵，不写入大体积原始数据行，只保留列名预览和结构摘要。

## Run / Current / History 关系

- “本次识别结果”只显示当前用户刚刚点击“开始识别”产生的结果。
- 历史识别记录始终在历史区域展示。
- 点击历史记录“查看”只打开详情，不修改 `current.json`。
- 点击“设为当前结果”才会更新 `recognized_data/current.json`。
- 如果记录为旧版导入，详情显示“由旧版项目结构导入”。

## 当前限制

- 详情页当前是识别页内嵌只读面板，不是独立路由。
- Markdown 导出是摘要报告，不包含可交互表格。
- DEG 数量统计、火山图和富集分析真实结果仍由后续结果模块处理。
- 物种判断依据依赖 recognition report 中已有字段，不在 Stage 2.7 新增识别算法。

## 后续计划

- 在 Stage 3 将详情页与标准化资产详情联动。
- 为 DEG comparison 增加已筛选基因数量和阈值记录。
- 支持从详情页跳转到对应标准化资产、任务中心 capability 和结果浏览 comparison。
