# Stage B5.9 GEO Series Matrix Parser MVP

Date: 2026-05-14

## 实现的 Series Matrix parser 能力

新增 `app/bioinformatics/geo_series_matrix_parser.py`，只处理 GEO Series Matrix `.txt` / `.txt.gz` 文件。

MVP 能力：

- 支持普通文本和 gzip 文本读取。
- 默认 UTF-8 读取；遇到解码失败时使用 latin-1 replacement fallback，并记录 warning。
- 流式扫描文件，不一次性载入完整大矩阵。
- 解析 `!Series_*`、`!Sample_*`、`!Platform_*` metadata。
- 解析 `!series_matrix_table_begin` / `!series_matrix_table_end` 矩阵区域。
- 读取矩阵表头、ID 列、样本列，统计矩阵行数和列数。
- 只保存前 N 行 preview 用于表达值类型和 ID 类型候选判断，不做完整矩阵物化。
- 支持文件名包含 `series_matrix` 的 `.txt` / `.txt.gz`，也支持普通 `.txt` / `.txt.gz` 内容中带 Series Matrix marker 的文件。

## Parser 输出字段

file-level recognition result 新增或填充以下字段：

- `file_format`: `TXT` / `TXT.GZ`
- `container_type`: `geo_series_matrix`
- `parser_depth`: `container_only` / `metadata_parsed` / `matrix_detected` / `matrix_previewed`
- `series_accession`
- `series_title`
- `series_summary`
- `overall_design`
- `platform_accessions`
- `sample_count`
- `sample_accessions`
- `sample_titles`
- `sample_source_name_ch1`
- `sample_characteristics_ch1`
- `sample_metadata_fields`
- `phenotype_candidate_fields`
- `phenotype_candidate_values_preview`
- `expression_matrix_presence`
- `expression_matrix_dimensions`
- `id_column`
- `sample_columns`
- `expression_value_type_candidate`
- `gene_id_type_candidate`
- `species_evidence`
- `warnings`
- `requires_user_confirmation`
- `can_enter_standardization`

`species_evidence` 使用结构化对象，包含：

- `species`
- `source_field`
- `source_file`
- `confidence`

如果多个 `Sample_organism_ch1` 不一致，会记录 conflict warning。不会默认写入 Homo sapiens。

## Readiness 语义

- 解析到矩阵区域、ID 列、样本列和至少一行矩阵数据时：
  - `expression_matrix_presence=true`
  - `can_enter_standardization=true`
  - recognition 中登记 `expression_matrix` candidate
  - `standardization_ready=true`
  - `deg_ready=false`，除非后续由用户确认比较分组

- 只有 metadata、没有矩阵数据行或样本列时：
  - `expression_matrix_presence=false`
  - `can_enter_standardization=false`
  - 可作为 `sample_metadata` / `phenotype_metadata` candidate
  - 不解锁标准化 gate

- `expression_value_type_candidate=unknown` 时：
  - 仍可进入标准化
  - `requires_user_confirmation=true`
  - warning 提示表达值类型需在标准化阶段确认

- `gene_id_type_candidate=probe_id` / `unknown` 时：
  - 仍可进入标准化
  - warning 提示 `ID_REF` 可能为平台探针 ID，需结合平台注释确认 gene ID 映射

## UI 文案变化

数据识别表格对 `geo_series_matrix_container` 增加 Series Matrix 专用展示：

- 显示 parser depth。
- 显示样本数量。
- 显示是否检测到表达矩阵区域。
- tooltip 显示平台 accession、矩阵维度、表达值类型候选、ID 类型候选、样本注释字段数量、候选 phenotype 字段和 warning。
- 候选分组只显示为“需用户确认后才能进行 DEG 分析”。

禁止误导文案仍保持：

- 不写“已完成差异分析”。
- 不写“可直接做 DEG”。
- 不写“表达矩阵已标准化”。
- 不写“已确认分组”。
- 不写“可用于发表”。

## 测试覆盖

新增和调整测试覆盖：

- `.txt.gz` Series Matrix 解压并解析。
- 识别 `!series_matrix_table_begin` / `!series_matrix_table_end`。
- 提取 series accession、summary、overall design。
- 提取 platform accession。
- 提取 sample accession。
- 提取 sample title、source_name、characteristics、treatment protocol。
- 统计 sample_count。
- 识别 expression matrix sample columns。
- 输出 matrix dimensions。
- `ID_REF` 识别为 `probe_id`，不误判 gene symbol。
- `Sample_organism_ch1` 形成 species evidence。
- 多个 organism 冲突时产生 warning。
- 矩阵存在时 `standardization_ready=true` 且 `deg_ready=false`。
- metadata-only Series Matrix 不进入 `standardization_ready`。
- `expression_value_type_candidate=unknown` 时仍可进入标准化，但 `requires_user_confirmation=true`。
- UI 文案不把候选分组写成已确认分组。
- `recognized_files.json` 保存 file-level recognition 输出。

## 已知限制

- 不做完整大矩阵载入和标准化计算。
- 不做平台探针到 gene symbol 的正式映射。
- 不自动确认分组。
- 不做 DEG 计算。
- 不做富集分析。
- 表达值类型判断只基于 preview，属于候选判断。
- `matrix_row_count` 通过流式扫描统计，遇到缺失 `!series_matrix_table_end` 时会提示可能不完整。

## 下一阶段建议

- B5.8B — family.soft GEOparse carry-over，如果尚未完成。
- B5.10 — Series Matrix to standardization confirmation UI。
- B6 — Real DEG executor pre-audit，在桌面手动测试通过后再进入。
