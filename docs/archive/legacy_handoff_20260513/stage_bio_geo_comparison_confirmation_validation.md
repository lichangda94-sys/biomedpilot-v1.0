# Stage Bio GEO Comparison Confirmation Validation

日期：2026-05-06

范围：本轮只验证 GEO 结构化元数据画像、候选比较组确认、下载建议分类、Ready 联动和差异分析入口。未执行大型 raw/CEL/SRA 下载，也未把候选分组自动写入正式比较组。

## 本轮改动结论

- GEO 候选比较组现在以用户可读中文展示，例如“肿瘤组 vs 正常/对照组”，原始字段如 `pathological_diagnostic` 只作为证据详情。
- 用户确认后，比较组写入当前项目的 `comparison_config_manual.tsv`，包含 comparison 头部和 sample assignment 明细。
- Ready 页面读取已确认比较组，并区分：
  - 候选分组待确认
  - 比较组已确认但缺表达矩阵
  - 比较组已确认但样本 ID 不匹配
  - 比较组已确认且表达矩阵样本匹配
- GEO 差异分析 runner 会优先使用正式 comparison_config 中的样本分配，不再只依赖表达矩阵列名推断。
- GEO 下载建议分为三类：
  - 推荐下载：元数据/样本注释
  - 可能用于分析：表达矩阵或标准化表达文件
  - 不建议默认下载：raw/CEL/大文件/SRA 原始数据

## 真实 GEO 轻量验证方法

验证使用 NCBI GEO 当前在线数据，只流式读取 Series Matrix header 和 GEO quick Series metadata；不下载完整大型 family SOFT、RAW tar、CEL、SRA。临时文件保存在 `/tmp/biomedpilot_geo_validation`，用于生成本报告。

## 真实 GSE 验证结果

| GSE | 复杂度类型 | GEO metadata profile | 候选分组 | 下载建议 | 是否可直接差异分析 |
|---|---|---|---|---|---|
| GSE33630 | 完整注释型，甲状腺癌/正常/ATC/PTC，含 RAW tar 和临床注释 | 成功；Series Matrix header 解析到 105 个样本 | `tumor vs control`，肿瘤 60、对照 45，高置信度，证据来自 pathological diagnostic | 推荐临床注释和 Series Matrix；RAW tar/CEL 不默认下载 | 下载前只能显示分析潜力高；需下载表达矩阵并确认比较组后运行 |
| GSE6004 | 甲状腺癌侵袭相关，RAW tar + Series Matrix | 成功；解析到 18 个样本 | `tumor vs normal`，肿瘤 14、正常 4，高置信度 | Series Matrix 作为可能分析输入；RAW tar 不默认下载 | 需确认比较组并验证表达矩阵样本匹配 |
| GSE15641 | 肾癌进展/转移，多临床状态，RAW tar + MAS5 文件 | 成功；解析到 92 个样本 | `tumor vs normal`，肿瘤 69、正常 23，中置信度；存在进一步拆分进展/转移维度的需求 | Series Matrix 为可能分析输入；MAS5 文件类型仍需更精细识别 | 需人工确认使用哪个临床维度作为正式比较组 |
| GSE62944 | TCGA RNA-seq 编译数据，跨癌种、主要是整理后的大型队列 | 成功但样本结构只从 header 取到很小预览；TCGA compendium 不适合作为普通 GSE 自动分析 | `tumor vs normal` 只有 1 vs 1 的预览证据，分析潜力降为中 | 推荐临床变量和癌种表；不承诺可直接分析 | 不应自动进入差异分析，需要专门 TCGA/GDC 流程 |
| GSE197158 | RNA-seq/FPKM xlsx 补充文件，骨肉瘤 vs 健康骨组织 | 成功；解析到 14 个样本 | 未从 sample-level metadata 中识别到明确分组 | xlsx FPKM 和 Series Matrix 属于可能分析输入 | 需要用户手动查看补充文件并设置比较组 |

## 发现的问题和后续改进点

1. Series Matrix parser 原先使用所有 sample 字段的最大列数作为样本数，GSE33630 的长 description 行导致样本数被高估。本轮已改为优先使用 `Sample_geo_accession` 数量。
2. GSE15641 这类多临床维度数据集只显示前几个候选比较组，后续 UI 应提供“查看全部候选比较维度”。
3. GSE62944 这类 TCGA 编译型 GSE 不应被普通 GEO 流程过度承诺；后续应提示用户优先走 TCGA/GDC 标准项目流程。
4. `GSE15641_mas5_data.txt.gz` 目前轻量预览为 unknown，后续可对 MAS5/normalized expression 命名增加更明确的表达矩阵预测。
5. 下载后验证仍依赖 recognition report 的 sample columns；本轮已为普通表格 profile 增加 `sample_columns`，后续还需要在 UI 中更直观展示 matched/unmatched sample list。

## 验收状态

- 候选分组不会自动写入正式 comparison_config：通过。
- 用户确认后写入正式 comparison_config：通过。
- Ready 页面能显示已确认比较组并校验样本匹配：通过。
- 差异分析 runner 能使用正式样本分配：通过。
- 下载建议不再把 raw/CEL/大文件放入默认推荐：通过。
- 下载前只显示“分析潜力”，下载后才显示“可运行/需要确认/缺表达矩阵/样本不匹配”等可用性状态：通过。
