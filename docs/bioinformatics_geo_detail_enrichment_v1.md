# Bioinformatics GEO Detail Enrichment v1

## 功能目标

GSE 编号详情页不再只展示搜索摘要。用户查看 GEO 数据集详情时，BioMedPilot 会从 NCBI GEO 官方 accession 页面和 SOFT 文本接口补充详情字段，并在 UI 中展示可审计的英文原始信息、样本预览、平台信息和下载文件提示。

## 字段来源

当前 enrichment 使用三类官方 GEO 信息源：

| 来源 | 用途 |
| --- | --- |
| `acc=<GSE>&targ=self&form=text&view=quick` | Series 标题、Summary、Overall design、Status、提交/更新日期、实验类型、平台编号、PMID、SuperSeries、BioProject、补充文件 URL |
| `acc=<GSE>&targ=gsm&form=text&view=quick` | GSM accession、样本标题、sample characteristics 预览 |
| GEO HTML accession 页面 | 平台完整名称、样本数量、补充文件名称、大小、文件类型和下载入口 |

不调用 PubMed 检索，不下载 RAW tar，不生成下载成功状态。

## 缓存策略

项目内缓存路径：

`acquisition/geo_detail_cache/<GSE>_detail.json`

读取顺序：

1. 先读取项目缓存。
2. 如果缓存缺少 `summary`、`overall_design`、`sample_preview` 或 `supplementary_files`，重新抓取 GEO detail。
3. 抓取成功后写回缓存。
4. 网络失败时保留已有基础字段，并在 UI 中显示明确提示，不伪造 metadata。

## UI 展示策略

详情页展示：

- 数据集概览：GSE 编号、中文物种显示、样本数、数据类型、平台、公开日期。
- 英文原始信息：English title、Summary、Overall design、Contributors、Citation、PMID、BioProject、SuperSeries。
- 样本结构与下载建议：前 20 个 GSM 样本、平台、RAW/Series Matrix/SOFT/MINiML 入口和后续分组提醒。
- 中文翻译与提炼：输入基于英文 title、Summary、Overall design 和 sample overview。

如果 Summary 和 Overall design 都缺失，中文提炼不会生成泛化说明，而是提示：

`未抓取到 GEO Summary / Overall design，无法生成可靠中文提炼。`

## 物种中文显示策略

内部 `organism/species` 字段继续保存 GEO 原始英文名。UI 使用新增显示字段：

- `organism_zh`
- `organism_display_name`

初始映射：

| 原始名 | UI 显示 |
| --- | --- |
| Homo sapiens | 人类（Homo sapiens） |
| Mus musculus | 小鼠（Mus musculus） |
| Rattus norvegicus | 大鼠（Rattus norvegicus） |
| Danio rerio | 斑马鱼（Danio rerio） |
| Drosophila melanogaster | 果蝇（Drosophila melanogaster） |
| Caenorhabditis elegans | 秀丽隐杆线虫（Caenorhabditis elegans） |

未映射物种显示为：

`<raw organism>（未映射中文名）`

## GSE60235 回归覆盖

回归测试使用固定 GEO SOFT/HTML fixture，不依赖实时网络。覆盖：

- raw organism 保持 `Homo sapiens`。
- UI display 包含 `人类`。
- Summary 包含 ImmVar / T cell activation 信息。
- Overall design 包含 peripheral blood / anti-CD3/CD28 信息。
- 样本数为 75。
- 平台为 GPL6244 和 Affymetrix Human Gene 1.0 ST Array。
- 样本预览包含 GSM1468447。
- 补充文件包含 GSE60235_RAW.tar、TAR (of CEL)、328.7 Mb。
- PMID 为 25214635。
- BioProject 为 PRJNA257802。
- SuperSeries 为 GSE60236。

## 当前限制

- HTML 解析只抽取详情页中稳定出现的平台、样本、补充文件和 citation 文本摘要。
- 不下载真实数据文件。
- 不进行分组自动确认；GSM title/characteristics 只作为用户确认分组的依据。
- 不进入 DEG、富集或报告分析执行。
