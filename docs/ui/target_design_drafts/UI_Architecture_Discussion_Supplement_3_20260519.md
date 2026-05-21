# UI 架构讨论记录补充 3：Bioinformatics 结果、报告、设置与日志收束

日期：2026-05-19
适用范围：UIShell / Bioinformatics / Result & Report / Report Export / Bioinformatics Settings / Project Logs / 后续 Codex UI 开发
文件性质：阶段性 UI 设计决策与 Codex 实现输入，不是完整 Figma 设计稿

---

## 1. 文件背景

本文件是在上一份 `UI_Architecture_Discussion_Supplement_2_20260519.md` 之后继续补充形成的 Bioinformatics UI 架构决策。

上一份补充文件已经确认：

- 数据检查与准备页以文件级识别为核心；
- 不设置数据集级摘要；
- 根据文件级识别结果给出整体检查结论；
- 分组与分析设计页服务后续所有分析任务；
- 支持多个 comparison design；
- 支持原始分组字段到分析分组的映射；
- 分析任务页按分析类型分区；
- 富集分析第一版只支持 GO / KEGG；
- Settings 中新增“分析资源与工具”；
- 分析任务页保留就地资源准备入口。

本文件继续记录后续新增确认内容，主要包括：

1. Result & Report / 结果与报告页；
2. Report Export / 报告导出页；
3. Bioinformatics Settings / 生信设置；
4. Bioinformatics Settings 与其他页面行为映射；
5. Project Logs & Technical Details / 项目日志与技术详情；
6. Bioinformatics 完整目标 IA 树；
7. Bioinformatics 后续 Codex 实现原则。

---

## 2. Bioinformatics UI 讨论当前状态判断

Bioinformatics 这部分的核心 UI 架构已经可以阶段性收束。

已完成讨论并确认的主页面包括：

```text
1. Project Home / 项目首页
2. Data Source / 数据来源
3. Data Check & Preparation / 数据检查与准备
4. Group & Design / 分组与分析设计
5. Analysis Tasks / 分析任务
6. Result & Report / 结果与报告
7. Report Export / 报告导出
8. Bioinformatics Settings / 生信设置
```

已完成讨论并确认的辅助机制包括：

```text
Project Logs & Technical Details / 项目日志与技术详情
```

当前暂无必须继续讨论的大结构问题。
后续如果继续细化，应进入具体页面低保真、控件布局、Codex 实现任务拆分，而不是继续调整大 IA。

---

## 3. Result & Report / 结果与报告页

### 3.1 页面定位

“结果与报告 / Result & Report” 不是全局结果中心，也不是自动展示所有历史结果的页面。

它由上一页“分析任务 / Analysis Tasks”触发：

```text
Analysis Tasks
→ 用户选择某一种分析
→ 点击开始分析
→ 软件运行对应分析
→ 进入该分析对应的 Result & Report 页面
```

该页面只展示当前这一次分析任务生成的结果、图表和可导出内容。

用户可以：

- 保存结果；
- 导出结果数据；
- 导出结果图；
- 加入报告草稿；
- 返回分析任务页，继续选择其他分析。

### 3.2 页面不做什么

该页面不应：

- 自动展示所有历史分析结果；
- 自动混合 DEG、富集、生存、相关性结果；
- 把不同任务的图表放在同一个默认页面；
- 把历史结果列表作为主视图；
- 生成自动科研结论；
- 把统计结果解释成核心发现或关键发现。

历史结果可以作为辅助入口，但不是主视图。

---

## 4. Result & Report 页面顶部区域

### 4.1 顶部保留信息

顶部只保留用户识别当前结果所必需的信息：

```text
当前分析任务名称
分析类型
使用的 comparison design
```

示例：

```text
DEG_Tumor_vs_Normal

分析类型：差异表达分析
比较设计：Tumor vs Normal
```

### 4.2 顶部不重点展示的信息

顶部不重点展示：

- 运行时间；
- 状态。

原因：

- 运行时间对普通用户判断结果没有太大意义；
- 如果已经进入正常结果页，通常默认分析已完成；
- 如果分析失败，不应进入正常结果页，而应显示失败提示或进入日志；
- 运行时间和状态如需保留，应进入“项目日志与技术详情”。

---

## 5. Result & Report 不设置“分析摘要”主区块

结果页不设置独立的“分析摘要”主区块。

以下内容不作为结果页主视图区块展示：

- 分析方法；
- 参数；
- 样本数；
- 阈值设置；
- 运行时间；
- 软件版本；
- 资源版本。

这些信息属于分析任务配置和复现信息，应在 Analysis Tasks 中完成选择，并在 Project Logs & Technical Details 中记录。

---

## 6. 统计结果预览 / 结果预览

### 6.1 命名

原先“结果摘要”统一改为：

```text
统计结果预览 / 结果预览
```

### 6.2 页面职责

该区域展示软件完成对应统计分析后生成的结果表格前几行。

推荐显示：

```text
前 5 行或前 10 行
```

具体行数由 Bioinformatics Settings 中“结果预览默认行数”决定。

### 6.3 示例

DEG：

```text
显示差异表达结果表前 5–10 行
```

富集分析：

```text
显示 GO / KEGG 富集结果表前 5–10 行
```

相关性分析：

```text
显示相关性结果表前 5–10 行
```

生存分析 / 临床关联：

```text
显示统计结果表或模型结果表前 5–10 行
```

### 6.4 不展示内容

该区域不展示：

- 核心发现；
- 关键发现；
- 结论；
- 自动解释；
- warning 作为主要内容。

Warning 如存在，应作为状态提示或日志记录，不作为“统计结果预览”主体。

---

## 7. 图表区域

图表区域展示当前分析任务产生的图。

示例：

DEG：

- 火山图；
- 热图；
- PCA；
- MA plot，按实际实现。

富集分析：

- dot plot；
- bar plot；
- enrichment plot，按实际实现。

相关性分析：

- scatter plot；
- correlation heatmap。

临床关联 / 生存分析：

- KM curve；
- forest plot，按实际实现。

图表区域应提供导出操作。

---

## 8. 云端 AI 结果分析

### 8.1 当前状态

原先设想的：

- 一句话解释；
- 详细解释；
- 人工复核提示；

统一改为：

```text
云端 AI 结果分析，待开发
```

当前版本不生成自动解释，不生成一句话结论，不生成详细结果解释。

### 8.2 未来开放后

未来如开发该功能，可加入：

- AI 生成结果解释；
- AI 生成报告段落草稿；
- AI 辅助润色；
- 人工核实提示；
- 不作为正式科研依据；
- 不构成临床或发表级结论。

---

## 9. Result & Report 操作区

操作区包含：

```text
保存结果
导出结果数据
导出结果图
加入报告草稿
返回分析任务
```

说明：

- “保存结果”保存当前分析任务输出；
- “导出结果数据”导出当前分析表格；
- “导出结果图”导出当前图表；
- “加入报告草稿”将当前结果加入 Report Export 的可用条目；
- “返回分析任务”回到 Analysis Tasks，用户可以选择其他分析类型继续分析。

---

## 10. Result & Report 页面最终结构

```text
结果与报告 / Result & Report

顶部：
- 当前分析任务名称
- 分析类型
- 使用的 comparison design

统计结果预览 / 结果预览：
- 显示结果表格前 5–10 行
- 查看完整结果表
- 导出结果数据

图表区域：
- 展示当前分析产生的图
- 导出图表

云端 AI 结果分析：
- 待开发

操作区：
- 保存结果
- 导出结果数据
- 导出结果图
- 加入报告草稿
- 返回分析任务

项目日志与技术详情入口：
- 查看当前分析日志
```

---

## 11. Report Export / 报告导出页

### 11.1 页面定位

“报告导出 / Report Export” 用于把用户确认过、加入报告草稿的多个结果组织成可编辑报告。

它不是单次分析结果页面。

### 11.2 报告内容来源

报告导出页只读取用户已加入报告草稿的结果。

规则：

```text
只有用户在 Result & Report 页点击“加入报告草稿”的结果，才进入 Report Export。
```

不自动包含所有分析结果。

原因：

- 用户可能做很多分析，但只希望部分结果进入报告；
- 加入报告草稿代表用户确认该结果值得纳入报告；
- 避免报告自动堆叠大量无关结果。

### 11.3 报告应包含的内容

报告应包含：

- 项目信息；
- 数据来源与数据文件摘要；
- 分组与分析设计；
- 用户选择加入报告的分析结果；
- 每个分析的分析方法与主要参数；
- 每个分析的统计结果预览；
- 每个分析的图表；
- 完整结果文件路径；
- 完整运行日志路径；
- 图表、结果文件与日志索引；
- 报告说明与使用边界。

---

## 12. 报告格式

### 12.1 第一版推荐格式

报告格式应优先支持可编辑、可被后续 AI 读取的格式：

```text
Markdown：第一优先
HTML：可选
DOCX：后续开放
PDF：后续开放
```

Markdown 是第一版核心格式，原因：

- 容易生成；
- 容易编辑；
- 容易版本管理；
- 容易被 AI 读取；
- 容易后续转换成 HTML / DOCX / PDF；
- 适合未来接入云端 AI 润色与解释。

### 12.2 云端 AI 报告润色

报告页可预留：

```text
云端 AI 报告润色，待开发
```

当前不启用自动润色，不自动生成正式报告解释。

---

## 13. 报告中长结果的处理

### 13.1 不完整写入长表

DEG、富集分析等结果可能很长。

报告正文不应完整写入：

- 上千个差异基因；
- 大量 GO term；
- 大量 KEGG pathway；
- 大型相关性表格；
- 大型临床结果表格。

### 13.2 正文只展示结果预览

报告正文只展示 Result & Report 中的统计结果预览，即前 5–10 行。

具体行数由 Bioinformatics Settings 中“结果预览默认行数”决定。

### 13.3 完整结果通过路径索引

完整结果文件以路径形式写入报告，方便用户手动查看。

示例：

```text
完整差异表达结果表已保存至：
project/results/DEG_Tumor_vs_Normal/deg_results_full.tsv

完整火山图已保存至：
project/results/DEG_Tumor_vs_Normal/volcano_plot.png
```

---

## 14. 报告章节结构

推荐 Markdown 报告章节结构如下。

```markdown
# Bioinformatics Analysis Report

## 1. 项目信息

- 项目名称
- 创建时间
- 报告生成时间
- 软件版本
- 分析模块：Bioinformatics / 生信分析
- 报告状态：Draft / 草稿

## 2. 数据来源与数据文件摘要

### 2.1 数据来源

- 数据来源类型：本地数据 / GEO / TCGA / GTEx
- 数据集名称或编号
- 数据记录状态：已记录 / 已下载 / 已构建
- 本地引用方式：复制到项目 / 原路径引用，若适用

### 2.2 数据文件摘要

只列出用于分析的关键文件：

| 文件 | 识别类型 | 状态 | 说明 |
|---|---|---|---|
| expression_counts.tsv | 表达矩阵 | 已识别 | 20,531 genes × 58 samples |
| sample_metadata.tsv | 样本信息 | 已识别 | 58 samples |
| gene_annotation.tsv | 基因注释信息 | 已识别 | gene_id / gene_symbol |
| clinical.tsv | 临床信息 | 已识别 | survival / diagnosis fields |

## 3. 分组与分析设计

### 3.1 使用的样本分组

- 使用的原始字段
- 用户定义分组
- 纳入样本数
- 排除样本数

### 3.2 Comparison Design

| 设计名称 | Group A / Control | Group B / Case | 样本数 | Paired | 用途 |
|---|---|---|---|---|---|
| Tumor vs Normal | Normal | Tumor | 10 / 50 | No | DEG / GSEA |

### 3.3 分组说明

用户备注或系统生成的简短说明。

## 4. 分析结果概览

只列出用户加入报告草稿的结果。

| 分析名称 | 分析类型 | Comparison Design | 状态 | 完整结果文件 |
|---|---|---|---|---|
| DEG_Tumor_vs_Normal | DEG | Tumor vs Normal | 已完成 | results/DEG_Tumor_vs_Normal/deg_results_full.tsv |
| GO_BP_enrichment | GO enrichment | Tumor vs Normal | 已完成 | results/GO_BP/go_results_full.tsv |

## 5. 差异表达分析结果，若已加入报告

### 5.1 分析说明

- 分析名称
- 使用的 comparison design
- 输入表达矩阵
- 分析方法
- 主要参数，简要列出
- 完整运行日志：`logs/deg_20260519.log`

### 5.2 统计结果预览

只显示前 5–10 行：

| gene_id | gene_symbol | logFC | p value | adjusted p value | regulation |
|---|---|---:|---:|---:|---|
| ... | ... | ... | ... | ... | ... |

完整结果文件：

```text
results/DEG_Tumor_vs_Normal/deg_results_full.tsv
```

### 5.3 图表

- 火山图：`results/DEG_Tumor_vs_Normal/volcano_plot.png`
- 热图：`results/DEG_Tumor_vs_Normal/heatmap.png`
- 其他图表，若有

## 6. 富集分析结果，若已加入报告

### 6.1 分析说明

- 分析名称
- 输入来源：DEG / ranked gene list
- 使用资源：GO / KEGG
- Gene ID 类型
- 物种
- 完整运行日志：`logs/enrichment_20260519.log`

### 6.2 统计结果预览

只显示前 5–10 行：

| term_id | term_name | gene_count | p value | adjusted p value |
|---|---|---:|---:|---:|
| ... | ... | ... | ... | ... |

完整结果文件：

```text
results/enrichment/go_results_full.tsv
```

### 6.3 图表

- Dot plot：`results/enrichment/dotplot.png`
- Bar plot：`results/enrichment/barplot.png`
- Enrichment plot，若有

## 7. 相关性分析结果，若已加入报告

### 7.1 分析说明

- 分析名称
- 目标基因 / 特征
- 相关变量
- 方法：Pearson / Spearman，按实际分析记录
- 完整运行日志：`logs/correlation_20260519.log`

### 7.2 统计结果预览

| feature | variable | correlation | p value | adjusted p value |
|---|---|---:|---:|---:|
| ... | ... | ... | ... | ... |

完整结果文件：

```text
results/correlation/correlation_results_full.tsv
```

### 7.3 图表

- Scatter plot
- Correlation heatmap

## 8. 临床关联 / 生存分析结果，若已加入报告

### 8.1 分析说明

- 分析名称
- 使用的临床字段
- 分组方式
- 样本数
- 方法，按实际实现记录
- 完整运行日志：`logs/clinical_survival_20260519.log`

### 8.2 统计结果预览

| variable | group | statistic | p value | note |
|---|---|---:|---:|---|
| ... | ... | ... | ... | ... |

完整结果文件：

```text
results/clinical/clinical_results_full.tsv
```

### 8.3 图表

- KM curve，若有
- Forest plot，若有
- Clinical association plot，若有

## 9. 图表、结果文件与日志索引

### 9.1 结果数据文件

| 文件说明 | 路径 |
|---|---|
| DEG 完整结果 | results/DEG_Tumor_vs_Normal/deg_results_full.tsv |
| GO 富集完整结果 | results/enrichment/go_results_full.tsv |

### 9.2 图表文件

| 图表说明 | 路径 |
|---|---|
| 火山图 | results/DEG_Tumor_vs_Normal/volcano_plot.png |
| GO dot plot | results/enrichment/dotplot.png |

### 9.3 日志文件

| 日志说明 | 路径 |
|---|---|
| 数据检查日志 | logs/data_check_20260519.log |
| DEG 分析日志 | logs/deg_20260519.log |
| 富集分析日志 | logs/enrichment_20260519.log |
| 相关性分析日志 | logs/correlation_20260519.log |
| 临床 / 生存分析日志 | logs/clinical_survival_20260519.log |

## 10. 云端 AI 结果分析

云端 AI 结果分析功能待开发。

后续该部分可用于：

- 生成结果解释草稿
- 生成报告段落草稿
- 辅助润色报告
- 生成摘要

当前不生成自动解释。

## 11. 报告说明与使用边界

本次报告仅供科研记录与结果整理参考，所有结论需由用户结合原始数据、分析参数和专业判断进行人工复核。

本报告不构成临床建议、诊断结论或发表级科研结论。
```

---

## 15. 删除数据检查结论章节

报告中删除原先建议的：

```text
2.3 数据检查结论
```

原因：

- 用户已经通过数据检查并进入后续分析；
- 如果用户认为检查有问题，就不会继续进行分析；
- 数据检查结论属于流程日志，不属于报告正文；
- 数据检查过程和结论应进入数据检查日志。

---

## 16. 所有分析结果必须包含完整运行日志路径

所有分析结果章节均必须包含完整运行日志路径。

包括：

- 差异表达分析；
- 富集分析；
- 相关性分析；
- 临床关联 / 生存分析；
- 后续其他分析。

每个分析章节都应包含类似：

```text
完整运行日志：logs/<analysis_name>_<date>.log
```

同时，第 9 节集中列出所有日志文件路径。

---

## 17. Bioinformatics Settings / 生信设置

### 17.1 页面定位

Bioinformatics Settings 是生信模块的行为控制层。
它不是装饰性设置页，也不是全局 Settings 的重复页。

它只管理影响 Bioinformatics 工作流的模块级设置。

### 17.2 页面结构

Bioinformatics Settings 包含：

1. 数据识别偏好；
2. 默认物种与 Gene ID；
3. 分析资源引用；
4. 结果与报告偏好；
5. 项目日志与技术详情入口。

其中“项目日志与技术详情”不是大区块，只是入口。

### 17.3 不放入 Bioinformatics Settings 的内容

不放：

- 账户与订阅；
- 云端 AI 服务账号；
- 本地语言模型路径；
- PDF OCR 引擎；
- 图像分析引擎；
- 全局缓存清理；
- 图标资源状态；
- 打包状态；
- ReleaseBuild 信息；
- LabTools 设置；
- Meta Analysis 设置。

这些应进入全局 Settings 或对应模块。

---

## 18. Bioinformatics Settings 必须驱动实际行为

### 18.1 最高原则

Bioinformatics Settings 不是只显示偏好，它必须真实约束后续页面行为。

不能出现：

- 设置中能选择，但后续页面不生效；
- 设置中关闭了某项识别，但识别流程仍然执行；
- 设置中选择了默认导入方式，但 Data Source 页面不体现；
- 设置中设置结果预览 5 行，但结果页或报告页仍显示 10 行。

### 18.2 设置-页面映射

后续 Codex 开发时必须建立：

```text
设置项 → 影响页面 → 行为要求
```

建议映射：

| 设置项 | 影响页面 | 行为要求 |
|---|---|---|
| 本地文件默认处理方式 | Data Source / 本地导入 | 默认选择复制到项目或原路径引用；用户可在本次导入中覆盖 |
| 自动识别表达矩阵 | Data Check & Preparation | 勾选时才自动尝试识别表达矩阵 |
| 自动识别样本信息 | Data Check & Preparation | 勾选时才自动尝试识别样本信息 |
| 自动识别基因注释信息 | Data Check & Preparation | 勾选时才自动尝试识别基因注释文件 |
| 自动识别临床信息 | Data Check & Preparation | 勾选时才自动尝试识别临床信息 |
| 默认物种 | Data Check / Analysis Tasks | 作为缺少明确物种信息时的默认候选，不覆盖已识别物种 |
| 默认 Gene ID 类型 | Data Check / Analysis Tasks | 作为缺少明确 ID 类型时的默认候选，不覆盖已识别 ID 类型 |
| 结果预览默认行数 | Result & Report / Report Export | 结果页和报告页显示对应行数 |
| 报告显示完整结果文件路径 | Report Export | 开启时报告列出完整结果文件路径 |
| 报告显示日志文件路径 | Report Export | 开启时报告列出分析日志路径 |
| 图表默认导出格式 | Result & Report / Report Export | 导出图表时默认使用该格式 |

### 18.3 设置类型

设置分为两类：

#### 默认偏好

提供默认选择，用户可在具体页面本次覆盖，本次选择应记录到项目中。

例如：

- 本地文件默认处理方式；
- 图表导出格式；
- 结果预览行数。

#### 行为控制

直接限制系统自动执行范围，页面和后端必须遵守。

例如：

- 自动识别表达矩阵；
- 自动识别样本信息；
- 自动识别基因注释信息；
- 自动识别临床信息。

### 18.4 作用范围显示

Bioinformatics Settings 中每个设置项应标注作用范围，例如：

- 作用范围：数据来源；
- 作用范围：数据检查与准备；
- 作用范围：结果与报告；
- 作用范围：报告导出。

---

## 19. Project Logs & Technical Details / 项目日志与技术详情

### 19.1 收敛决策

Bioinformatics 不在每个页面单独设置完整“技术详情”区块。

统一建立：

```text
项目日志与技术详情 / Project Logs & Technical Details
```

它是 Bioinformatics 模块的辅助入口，不是主流程页面，不进入普通用户主导航。

### 19.2 页面定位

项目日志与技术详情用于统一承载 Bioinformatics 项目中的技术记录、运行日志、检查日志、分析日志和导出记录。

它不参与普通用户主流程，但可从多个页面进入或导出。

### 19.3 承载内容

项目日志与技术详情包含：

1. 项目基本技术信息
   - 项目路径
   - 项目配置文件
   - 项目创建时间
   - 最近更新时间

2. 数据来源日志
   - 数据来源记录
   - 本地导入记录
   - 下载记录
   - 已记录 / 已下载状态变化

3. 数据检查日志
   - 文件级识别结果
   - 用户确认 / 修改记录
   - warning / error
   - 重新检查记录

4. 分组与设计日志
   - comparison design 创建记录
   - 分组修改记录
   - 样本纳入 / 排除记录

5. 分析任务日志
   - 分析任务名称
   - 输入文件
   - comparison design
   - 分析方法
   - 参数
   - 阈值
   - 运行时间
   - 软件版本
   - 资源版本
   - 运行状态

6. 结果与报告日志
   - 保存结果记录
   - 导出图表记录
   - 导出结果表记录
   - 加入报告草稿记录
   - 报告导出记录

### 19.4 各页面入口规则

Project Home：

- 不再设置完整技术详情区块；
- 只保留轻量入口：查看项目日志。

Data Check & Preparation：

- 保留“导出检查日志”；
- 可打开项目日志并定位到数据检查部分。

Result & Report：

- 保留“查看分析日志”；
- 可打开项目日志并定位到当前分析任务。

Report Export：

- 报告中保留图表、结果文件与日志索引；
- 不作为 UI 里的技术详情页面。

Bioinformatics Settings：

- 不再放“生信技术详情”大区块；
- 只保留“打开项目日志与技术详情”入口。

Testing Feedback：

- 可附加项目日志或生成反馈包。

### 19.5 功能要求

项目日志与技术详情应支持：

- 查看；
- 筛选；
- 导出；
- 打包为测试反馈包。

---

## 20. Bioinformatics 完整目标 IA 树

### 20.1 主流程

```text
Bioinformatics / 生信分析
├── Project Home / 项目首页
├── Data Source / 数据来源
├── Data Check & Preparation / 数据检查与准备
├── Group & Design / 分组与分析设计
├── Analysis Tasks / 分析任务
├── Result & Report / 结果与报告
└── Report Export / 报告导出
```

### 20.2 辅助页面

```text
Bioinformatics Settings / 生信设置
Project Logs & Technical Details / 项目日志与技术详情
```

### 20.3 完整 IA 树

```text
Bioinformatics / 生信分析
├── Project Home / 项目首页
│   ├── 当前项目状态
│   ├── 推荐下一步
│   ├── 最近数据 / 任务 / 结果
│   └── 查看项目日志，轻量入口
│
├── Data Source / 数据来源
│   ├── 本地数据导入
│   ├── GEO 数据库
│   ├── TCGA 数据库
│   ├── GTEx 数据库
│   ├── 中文研究问题检索
│   └── 当前项目数据来源，详情默认折叠
│
├── Data Check & Preparation / 数据检查与准备
│   ├── 文件级识别结果表
│   ├── 选中文件摘要
│   ├── 整体检查结论
│   ├── 重新运行数据检查
│   ├── 导出检查日志
│   └── 进入分组与分析设计
│
├── Group & Design / 分组与分析设计
│   ├── 当前输入数据
│   ├── 样本表
│   ├── 原始分组字段与取值
│   ├── 创建分析分组
│   ├── Comparison Design 列表
│   └── 设计检查
│
├── Analysis Tasks / 分析任务
│   ├── DEG / 差异表达分析
│   ├── GSEA / ORA / 富集分析
│   ├── 相关性分析
│   ├── 临床关联 / 生存分析
│   ├── 可视化与报告辅助
│   └── 最近任务记录
│
├── Result & Report / 结果与报告
│   ├── 当前分析任务名称
│   ├── 分析类型
│   ├── 使用的 comparison design
│   ├── 统计结果预览
│   ├── 图表区域
│   ├── 云端 AI 结果分析，待开发
│   ├── 保存 / 导出 / 加入报告草稿
│   └── 查看分析日志，轻量入口
│
├── Report Export / 报告导出
│   ├── 报告草稿条目
│   ├── 报告章节预览
│   ├── 图表、结果文件与日志索引
│   ├── Markdown 导出
│   ├── HTML 导出，可选
│   └── DOCX / PDF / AI 润色，后续开放
│
├── Bioinformatics Settings / 生信设置
│   ├── 数据识别偏好
│   ├── 默认物种与 Gene ID
│   ├── 分析资源引用
│   ├── 结果与报告偏好
│   └── 打开项目日志与技术详情，轻量入口
│
└── Project Logs & Technical Details / 项目日志与技术详情
    ├── 项目基本技术信息
    ├── 数据来源日志
    ├── 数据检查日志
    ├── 分组与设计日志
    ├── 分析任务日志
    ├── 结果与报告日志
    └── 导出 / 反馈包
```

---

## 21. 主流程与辅助流程区分

主流程页面：

```text
Project Home
Data Source
Data Check & Preparation
Group & Design
Analysis Tasks
Result & Report
Report Export
```

辅助页面：

```text
Bioinformatics Settings
Project Logs & Technical Details
```

不再作为普通用户独立主流程页面：

```text
Acquisition Status
Recognition
Readiness Dashboard
Standardized Assets
Workflow Status
Manifest Viewer
Raw JSON Viewer
Developer Diagnostics
```

这些能力已分别合并或降级到：

```text
Data Source
Data Check & Preparation
Analysis Tasks
Project Logs & Technical Details
```

---

## 22. 页面流转

主流程：

```text
Project Home
→ Data Source
→ Data Check & Preparation
→ Group & Design
→ Analysis Tasks
→ Result & Report
→ Report Export
```

返回路径：

```text
Data Source
→ 可返回 Project Home

Data Check & Preparation
→ 可返回 Data Source

Group & Design
→ 可返回 Data Check & Preparation

Analysis Tasks
→ 可返回 Group & Design

Result & Report
→ 可返回 Analysis Tasks

Report Export
→ 可返回 Result & Report 或 Analysis Tasks
```

原则：

- 主按钮始终向前；
- 返回按钮始终清楚；
- 同一区域不放多个同权重主按钮；
- 技术日志、设置、资源管理不插入主流程。

---

## 23. Codex 实现原则

后续交给 Codex 实现 Bioinformatics UI 收束时，应遵守：

1. 不进入 Figma；
2. 不做高保真视觉；
3. 不新增无必要主页面；
4. 将历史 UI-03 到 UI-13 收敛到目标 IA；
5. UI-05 Acquisition Status 不再作为普通用户独立页；
6. Recognition / Readiness / Standardized Assets 合并进 Data Check & Preparation；
7. Workflow Status / Analysis Task Center / DEG Config 合并进 Analysis Tasks；
8. Result & Report 只展示当前分析任务结果；
9. Report Export 只读取用户加入报告草稿的结果；
10. Bioinformatics Settings 必须真实驱动对应页面行为；
11. 技术详情与日志统一进入 Project Logs & Technical Details；
12. 不在每个页面重复实现技术详情；
13. 日志必须可导出，支持反馈包；
14. 所有结果预览行数受 Bioinformatics Settings 控制；
15. 所有分析结果章节必须包含完整运行日志路径；
16. 报告默认导出 Markdown，HTML 可选，DOCX/PDF 后续开放；
17. 云端 AI 结果分析与云端 AI 报告润色均标记为待开发；
18. 不把 testing、preflight、dry-run 或 planned 功能表现为正式统计分析。

---

## 24. 当前确认决策摘要

已确认：

```text
1. Result & Report 是单次分析结果页，不是全局结果中心。
2. Result & Report 顶部只显示当前分析任务名称、分析类型、comparison design。
3. Result & Report 不设置分析摘要主区块。
4. 统计结果预览展示前 5–10 行，行数由 Bioinformatics Settings 控制。
5. 云端 AI 结果分析统一标记为待开发。
6. Report Export 只读取用户加入报告草稿的结果。
7. 报告正文只展示统计结果预览，不完整写入长结果表。
8. 完整结果文件和图表通过路径写入报告。
9. 删除报告中的“数据检查结论”章节。
10. 所有分析结果章节必须包含完整运行日志路径。
11. Bioinformatics Settings 是生信模块行为控制层，必须真实影响后续页面行为。
12. Bioinformatics Settings 设置项必须建立设置-页面映射关系。
13. 技术详情与日志统一收敛为 Project Logs & Technical Details。
14. Project Logs & Technical Details 是辅助入口，不进入主流程。
15. Bioinformatics 主流程确定为 Project Home → Data Source → Data Check & Preparation → Group & Design → Analysis Tasks → Result & Report → Report Export。
16. Bioinformatics 辅助页面为 Bioinformatics Settings 和 Project Logs & Technical Details。
```

---

## 25. 后续建议

Bioinformatics 大结构目前已经可以阶段性结束。

后续可进入以下方向之一：

1. 将 Bioinformatics UI 架构整理成 Codex 实施任务；
2. 继续讨论 Meta Analysis 的 shell-only 与目标结构；
3. 继续讨论 LabTools 模块级信息架构重构；
4. 讨论 Settings 各子页面的具体布局；
5. 讨论测试反馈页面内容。
