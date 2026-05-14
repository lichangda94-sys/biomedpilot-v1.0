# Stage B5.10 Recognition to Standardization Confirmation UI

Date: 2026-05-14

## 候选资产来源

标准化确认阶段读取当前项目的 recognition 输出：

- `logs/recognition/recognized_files.json`
- fallback: `logs/recognition/recognition_report.json`
- group preview: `logs/recognition/group_preview_report.json`

候选资产按来源 parser 保留：

- `geo_series_matrix`
- `geo_family_soft`
- `xlsx`
- `csv` / `tsv`
- `processed_table`
- `group_preview`

候选类型包括：

- expression matrix candidates
- sample metadata candidates
- phenotype/group candidates
- species evidence
- gene ID / probe ID candidates
- platform annotation candidates
- imported DEG candidates

主 UI 只显示来源文件名，不显示 raw absolute path。manifest 内可保存内部候选 ID 和脱敏来源文件名。

## 确认 UI 实现

在现有“数据标准化”页面新增“标准化确认候选”区域：

- 候选资产表格显示候选类型、来源文件、来源 parser、确认状态和说明。
- 显示表达矩阵候选、样本注释候选、分组候选、物种候选、gene ID 候选、平台注释候选和已有 DEG 结果候选。
- 增加确认操作：
  - 确认表达矩阵候选
  - 确认物种候选
  - 确认 gene ID 类型
  - 确认候选分组
  - 刷新候选

UI 文案强调：

- 识别阶段只是发现候选表达矩阵。
- Series Matrix 的 `ID_REF` 可能是平台探针 ID。
- 候选分组确认后才可进入 DEG preflight。
- 当前不会运行真实差异分析。

未新增会误导用户把候选状态理解为已完成计算、已自动确认分组、可直接运行 DEG、已发现差异基因或可用于正式发表结论的文案。

## Confirmation Manifest 字段

新增：

`manifests/standardization_confirmation.json`

主要字段：

- `selected_expression_candidate`
- `expression_value_type_confirmed`
- `selected_sample_metadata_candidate`
- `confirmed_group_design`
- `species_confirmed`
- `gene_id_type_confirmed`
- `platform_annotation_confirmed`
- `warnings`
- `readiness`
  - `standardization_confirmed`
  - `deg_preflight_ready`
  - `imported_result_ready`
- `created_at`
- `updated_at`

表达值类型确认支持：

- `count`
- `count_like_candidate`
- `FPKM`
- `TPM`
- `normalized_or_log_expression`
- `unknown`

gene ID 类型确认支持：

- `ensembl_id`
- `entrez_id`
- `gene_symbol`
- `probe_id`
- `unknown`

`probe_id` / `unknown` 会提示需要平台注释或 ID 映射确认，不会自动当作 gene symbol。

## Readiness 语义

本阶段分离三层状态：

- `standardization_ready`: 识别阶段发现可进入标准化的候选资产。
- `standardization_confirmed`: 用户已经确认表达矩阵、表达值类型、物种和 gene ID 基本信息。
- `deg_preflight_ready`: 仅当表达矩阵已选、表达值类型为 `count` 或已确认的 `count_like_candidate`、分组设计已确认且 case/control 可构建时为 true。
- `imported_result_ready`: 已有外部 DEG 结果候选，可进入 imported DEG 浏览，但不能写成重新计算结果。

不改变真实 DEG executor 语义；本阶段不会运行 limma、DESeq2 或 edgeR。

## 测试结果

新增或调整测试覆盖：

- Series Matrix expression candidate 显示在标准化确认页。
- family.soft metadata-only 不显示为可选表达矩阵。
- family.soft `ID_REF/VALUE` table 显示为 expression candidate 且 requires user confirmation。
- XLSX count / FPKM candidates 可显示且来源正确。
- expression value type `unknown` 时不能 `deg_preflight_ready`。
- `count_like_candidate` 未确认时不能 `deg_preflight_ready`。
- 用户确认 `count_like_candidate` 后，配合分组确认可进入 DEG preflight readiness。
- 分组候选未确认时 `deg_ready=false`。
- 分组确认后写入 manifest。
- species evidence 显示来源字段。
- `probe_id` 不误写成 gene symbol。
- `standardization_confirmation.json` 写入成功。
- 主 UI 不暴露 raw absolute path。
- 禁止文案不出现在新增 UI 文案中。

完整验证结果见本阶段提交记录。

## 已知限制

- 不做真实标准化计算。
- 不运行 limma、DESeq2 或 edgeR。
- 不新增火山图、热图、富集分析。
- 不做平台探针到 gene symbol 的正式映射。
- 不自动确认分组。
- 不修改 imported DEG report loop 语义。
- 当前确认 UI 使用首个候选作为快捷确认默认值；后续应提供更细粒度的候选选择控件。

## 下一阶段建议

- B5.11 — Desktop manual test for import-recognition-standardization loop。
- B6 — Real DEG executor pre-audit after manual UI test passes。
