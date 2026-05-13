# Stage Bio GEO Page Sample Structure Audit

## Scope

本审计覆盖 Bioinformatics GEO 检索、下载、中文检索详情、group preview、recognition 和 readiness 当前链路。目标是确认在下载和识别前，软件是否已经能读取 GEO/GSE 页面级信息，并说明哪些字段可以用于样本结构预览。

## Current Field Coverage

| GEO 字段 | 当前能力 | 主要来源 |
| --- | --- | --- |
| GSE title | 已读取 | `GeoSearchAdapter` 将 `GeoDatasetSearchItem.title` 写入 `UnifiedDatasetCandidate.display_title` 和 `source_specific_metadata.title_en` |
| GSE summary | 已读取 | GEO search result `summary` 写入 `source_specific_metadata.summary_en` |
| overall design | 不稳定 | metadata 字段存在 `overall_design_en`，但 search adapter 当前默认写空；family SOFT / legacy helper 可解析该字段 |
| sample count | 已读取 | search item `sample_count`；下载后 recognition/group preview 可从 sample records 或矩阵列名重新估计 |
| sample title | 下载后可读取 | `group_preview.py` 可从 family SOFT / Series Matrix 解析 `!Sample_title` |
| sample source_name_ch1 | 下载后可读取 | `group_preview.py` 解析 `!Sample_source_name_ch1` |
| sample characteristics_ch1 | 下载后可读取 | `group_preview.py` 解析 `!Sample_characteristics_ch1` 并提取明确分组字段 |
| platform GPL | 已读取 / 下载后可增强 | search adapter 保存 `platform_accessions`；recognition 对 Series Matrix 生成 `platform_reference_hint` |
| supplementary file list | 元数据下载后可读取 | `DatasetDownloadService` 生成 `GSE*_asset_manifest.json`，区分 family SOFT、Series Matrix、supplementary files |
| SRA / raw data link | 不稳定 | 主线 download service 目前没有结构化 SRA/raw link 字段；legacy downloader 有相关探索逻辑但不属于主线 |

## Current Group Inference Sources

当前正式的分组预览来自 `app/bioinformatics/group_preview.py`，主要依赖下载后的文件内容：

- GEO family SOFT：`!Sample_geo_accession`、`!Sample_title`、`!Sample_source_name_ch1`、`!Sample_characteristics_ch1`。
- GEO Series Matrix：sample metadata 行与 `ID_REF` 表头中的 GSM 列。
- sample / clinical metadata 表格：`group`、`condition`、`treatment`、`disease_state`、`phenotype`、`source_name_ch1`、`characteristics_ch1` 等字段。
- 表达矩阵列名：仅作为低置信度预览。

这些结果只写入 `group_preview`，不会自动写入正式 `comparison_config`。

## Missing Page-Level Structure

当前缺口是“下载前”的 GEO 页面理解：

1. `overall design` 未稳定进入主线 candidate metadata。
2. sample title / source / characteristics 只有下载 family SOFT 或 Series Matrix 后才可用。
3. supplementary file list 只有元数据下载后才可结构化显示。
4. 当前详情页显示资产状态，但需要把 title / summary / overall design / sample records / supplementary manifest 聚合成统一的 metadata profile。
5. profile 层必须只给出下载前“分析潜力”，不能承诺“可运行”；真正可运行性需要下载后 recognition 和样本匹配确认。

## Fields Suitable For Sample Structure Preview

可用于保守预览：

- `Sample_title`、`Sample_source_name_ch1`、`Sample_characteristics_ch1`、`Sample_description` 中明确重复出现的组别字段。
- `overall design` 和 `summary` 中明确出现的 tumor/normal、treated/control、resistant/sensitive 等比较语句只能作为辅助证据；没有 sample-level 证据时只能生成低置信提示。
- asset manifest 中的 Series Matrix / supplementary expression 文件名，用于判断是否值得下载分析。
- platform GPL 和 data modality，用于判断数据类型是否适合 bulk expression 分析。

不应直接作为正式分组：

- GSM / sample accession、文件名、barcode、batch、platform、replicate、run accession、library strategy。
- sex / age 等临床变量，除非未来用户明确选择临床变量分组。
- summary / 中文提炼中的自然语言推断结果，只能辅助用户判断，不能自动生成正式比较组。

## Implementation Recommendation

新增 `app/bioinformatics/services/geo_metadata_profile_service.py`，作为 UI 和下载前决策的轻量聚合层：

- 读取 candidate metadata、已下载 family SOFT / Series Matrix、asset manifest、中文 summary payload。
- 输出 `GeoMetadataProfile`，包含 title、summary、overall design、sample_records、分层样本数、supplementary_file_preview、sample_structure_preview、candidate_comparisons、analysis_potential_level、analysis_availability_status 和 warnings。
- candidate comparisons 的 sample assignments 必须包含 sample accession、assigned group、evidence field、evidence text 和 confidence。
- supplementary 文件下载前只按文件名、扩展名、大小和描述做轻量预测；大文件提示“建议确认后下载”。
- UI 详情页默认显示 profile 摘要；原始下载/recognition 状态继续保留在技术或资产状态区域。
- profile 的 candidate comparisons 必须标记 `requires_user_confirmation=true`，不得自动写入 `comparison_config`。

## Live GEO Smoke Observation

本阶段用临时目录对 `GSE33630` 做了一次轻量 live smoke，下载后删除临时文件：

- metadata source：family SOFT。
- geo / metadata sample count：105 / 105。
- sample-level 字段可识别多个候选比较组；例如 pathological diagnostic 字段支持 tumor vs control。
- 第一个样本证据示例：`GSM831749 -> tumor`，证据字段 `pathological_diagnostic`，证据文本 `pathological diagnostic: anaplastic thyroid carcinoma (ATC)`。
- supplementary 预览共 111 个条目；建议下载文件收敛为 Series Matrix 和 clinical annotation，不再把 family SOFT 或大量 CEL 原始文件默认列为优先下载。

结论：真实 GEO 元数据可以支持下载前样本结构预览，但同一数据集可能存在多个病理/组织/处理维度，必须保持候选分组待确认，不能静默写入正式比较组。
