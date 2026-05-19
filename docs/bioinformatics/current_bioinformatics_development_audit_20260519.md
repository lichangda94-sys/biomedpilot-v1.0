# Bioinformatics 当前开发审计报告

日期：2026-05-19

范围：审计当前 `dev/bioinformatics` 工作树的已实现能力、仍未实现或未接入能力、旧版本中是否已有可复用实现，以及下一阶段推进建议。本报告只写审计结论，不修改 runtime 代码，不覆盖既有 handoff 文档。

## 0. 当前状态

- 工作区：`/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`
- 分支：`dev/bioinformatics`
- 当前 HEAD：`70c3419 docs(bio): hand off gene set resources to asset repository work`
- 并列 Integration 工作树：`/Users/changdali/Developer/biomedpilot v1.0/Integration`，分支 `dev/integration`，HEAD `49c855f`
- 当前工作树审计前已有未跟踪文件：`docs/bioinformatics/Bioinformatics_handoff_report_20260513.md`。本报告未覆盖该文件。

阶段判断：

- 当前生信模块已经不再是早期旧 GEO 工具的简单搬运，而是形成了 BioMedPilot 桌面主线中的项目、数据来源、识别、Ready、标准化、任务中心、结果和报告框架。
- 当前最稳定的可承诺主链路是：`acquisition record / source manifest / receipt` -> `pending dataset` -> `recognition_report.v2` -> `standardization_confirmation` -> `standardized_data/repositories` -> `analysis_input_repository` -> `preflight / preview / report draft`。
- 当前还不能承诺完整科研分析链。正式 DEG、富集、GSEA、相关性、生存分析、图表和可发表报告仍需继续接入、校验和产品化。

## 1. 已实现功能

### 1.1 桌面工作流与页面骨架

已实现：

- Bioinformatics 项目首页、数据导入/检索、中文主题检索、数据识别、Ready 检查、标准化、分析任务中心、结果浏览、项目报告、设置页已接入 `workflow_pages.py`。
- `project_workflow_orchestrator.py` 定义了 10 步项目工作流：工作区验证、数据获取、数据识别、初始 Ready 判断、标准化、Ready 刷新、任务中心、结果、报告、最终验证。
- UI 语义已经开始区分“可进入标准化”“仅供参考/注释”“不能用于分析”“testing / preview”。

边界：

- 工作流可以生成状态文件和阶段报告，但结果、报告阶段仍以读取现有 artifact 为主。
- 任务中心当前主要创建任务记录和 capability rows，不等于正式统计任务执行平台。

### 1.2 数据获取与 acquisition 记录

已实现：

- 本地文件 copy/reference 登记，GSE plan-only 登记，acquisition plan/record/handoff 输出。
- GEO family SOFT 通过 NCBI HTTPS 下载，支持本地 cache hit。
- GEO asset manifest 可发现 family SOFT、Series Matrix、supplementary、RAW/heavy 等远端资产。
- GSE 文件下载候选选择已实现，默认偏向 Series Matrix 和高优先级 processed expression，避免 RAW/heavy 和 imported DEG 默认进入表达输入。
- 选中 GEO 远端资产可下载到项目缓存，并通过 acquisition record 把真实文件路径交给 pending dataset 和 recognition。
- GDC public file downloader 类已存在，TCGA/GDC 和 GTEx 搜索可生成项目/组织候选和下载计划语义。

边界：

- 没有后台下载队列、取消、正式 retry policy、细粒度进度恢复。
- TCGA/GDC 与 GTEx 还没有完整“在线选择文件 -> 下载 -> 标准化 expression matrix -> 分析输入”的用户闭环。
- RAW/SRA/CEL/BAM/CRAM 等重型原始数据默认仍应阻断，不进入普通用户流程。

### 1.3 检索与候选数据源

已实现：

- `BioinformaticsSourceRouter` 路由 GEO、TCGA/GDC、GTEx。
- query understanding 层可从中文主题生成结构化数据源查询草稿。
- TCGA/GDC adapter 在 online 模式下可检查 project、file、case 级 metadata；offline 模式下生成 draft mapping。
- GTEx adapter 可生成正常组织参考候选，并显式提示 TCGA-GTEx joint analysis 前需要处理 batch effect。
- PubMed 不属于当前 Bioinformatics 数据获取边界。

边界：

- GEO/TCGA/GTEx 候选还不是统一的“可分析数据集包”。
- TCGA/GDC controlled access 不支持；GTEx 主要是正常组织参考候选。
- 中文主题检索仍需要保守处理歧义，不能自动承诺找到可分析矩阵。

### 1.4 文件识别与 parser

已实现：

- `recognition_report.json` / `recognized_files.json` 使用 v2 语义，包含 recognition run、engine version、fingerprint、stale status、evidence、matrix/profile/risk 信息。
- Series Matrix parser 可解析 metadata、sample fields、matrix block preview、ID_REF、sample columns、species/value type evidence。
- family SOFT native parser 已识别 series/sample/platform blocks、sample metadata、phenotype、platform annotation、sample expression table 候选。
- CSV/TSV/XLSX 可以识别 expression/count/FPKM/TPM、sample metadata、clinical/survival、annotation、imported DEG 等。
- imported DEG 与 recompute DEG 输入已经分开，导入差异结果不会被误用为表达矩阵。
- RAW/heavy 文件进入风险/阻断语义，不默认进入 analysis input。

边界：

- recognition 输出是候选和证据，不是标准化完成证明。
- Series Matrix 不物化完整大矩阵，不自动平台映射，不自动确认分组。
- family SOFT 当前 parser 已强于 container-only，但尚未达到旧 GEOparse pipeline 的完整深度。

### 1.5 Readiness、标准化确认和标准化仓库

已实现：

- Ready 检查生成 `readiness_report.json` 和 `analysis_capability_matrix.json`。
- Ready 语义区分 `standardization_ready`、`standardization_confirmed`、`deg_preflight_ready`、`imported_result_ready`。
- 标准化确认收集 expression、sample metadata、group、species、gene ID、platform、imported DEG 候选，写入 `standardization_confirmation.json`。
- `project_standardization.py` 已生成 repository v2：
  - `expression_repository`
  - `sample_metadata_repository`
  - `group_design_repository`
  - `feature_annotation_repository`
  - `clinical_repository`
  - `imported_result_repository`
  - `analysis_input_repository`
- 已写入 `repository_manifest.json`、`validation_report.json`、`asset_lineage.jsonl`、`standardized_assets_registry.json`、`analysis_ready_manifest.json`。
- DEG preflight 优先读取 `analysis_input_repository` 的 `deg_recompute` package。

边界：

- 标准化仓库当前是资产整理、轻量格式转换和校验，不等于 biological normalization。
- 不做 sample name 最终对齐后的可发表矩阵，不做 ID_REF -> gene symbol/gene ID 自动映射。
- 多候选资产 selection/resolver 尚未完全收口到一个跨模块 truth。

### 1.6 GSEA 基因集资源管理

已实现：

- 本地 GMT import、GMT validation、registry 管理、单选 selected resource。
- Reactome、GO BP/CC/MF、KEGG human pathways 下载和本地 cache。
- registry 写入 `user_data/bioinformatics/gene_sets/gene_set_registry.json`，包含 source、URL、license note、version/download date、local path、status、validation、gene set count、checksum、file size。
- 未选择或失效的 gene set 只阻断 GSEA preflight/execution，不阻断数据检查、标准化准备或 DEG preflight。

边界：

- 资源管理器不是 GSEA 分析执行器。
- MSigDB 等受限资源没有自动下载或捆绑。
- 下一步应把 selected GMT 接入真正的 GSEA preflight manifest，再决定是否实现 execution。

### 1.7 分析服务、结果和报告

已实现：

- 存在最小本地 runner：
  - GEO differential expression runner：Welch t-test / fallback 近似，写 DEG CSV 和 summary。
  - TCGA tumor-vs-normal DEG runner：基于 prepared package 运行最小 DEG。
  - over-representation enrichment runner：读取确认 DEG 和 GMT，执行本地 ORA。
  - expression correlation runner：按目标基因计算 Pearson correlation。
- 存在服务层 preflight：
  - differential expression preflight
  - survival preflight
  - cleaning/grouping/import/report 等服务和页面
- imported DEG 浏览和项目报告草稿已实现。
- 报告 builder 明确写入语义声明：preflight-only、imported result、testing-level、dry-run/configured-not-run、real computed result 未开放。

边界：

- 这些 runner/service 还没有统一接入当前桌面任务中心的正式执行、result index、图表和报告闭环。
- 当前任务中心默认记录 `execution=not_run`，不应被描述为真实分析完成。
- limma、DESeq2、edgeR、正式 GSEA、正式火山图/热图/富集图/生存曲线仍未作为产品承诺面开放。

## 2. 未实现或未完成内容

| 功能域 | 当前缺口 | 旧版本是否开发过 | 处理建议 |
| --- | --- | --- | --- |
| 标准化资产 extraction router / resolver | repository 已有，但跨模块只读 resolver、默认资产选择、下游统一消费口仍未完全收口 | 旧版 Module 3 有 `module3_assets.py` 和标准资产 contract；Integration 分支还有 `standardized_asset_selection.py` | 下一阶段 P0/P1，建立当前 repository manifest 为唯一 truth，不直接复用旧 manifest |
| 多候选资产选择 | 当前 registry 有 selection state，但 UI/服务 resolver 不完整 | Integration 分支有相关 helper；旧版有 standard asset planning | 合并 Integration helper 前先改为读取 v2 repository 字段 |
| 正式 DEG 执行 | 有最小 runner 和 preflight，但未成为桌面正式任务闭环；无 limma/DESeq2/edgeR | 旧版有 readiness/preflight 和最小可测路径，但不是生产级 DEG | 先接 preflight -> executor -> result index 的受控链路，再评估 R/容器化方法 |
| 平台注释和 probe mapping | 当前只识别/登记 platform annotation，不自动完成 ID_REF 映射 | 旧版有 platform/feature annotation 规则和 GEOparse pipeline 思路 | 做 mapping quality report 和人工确认 gate，不自动宣称映射成功 |
| biological normalization | 当前标准化仓库明确 `biological_normalization_performed=false` | 旧版只冻结 contract / 有 normalizer 思路，不是可直接承诺能力 | 先补 matrix value semantic、log-scale、batch/normalization provenance |
| sample alignment / design validation | DEG preflight 做轻量样本名检查，但未完成统计设计校验 | 旧版 local_data validation 和 group detection 可参考 | 作为 B5.19/B5.20 的 blocker gate，输出 validation report |
| TCGA/GDC 在线闭环 | 可搜索/检查/下载 public file，但没有完整用户文件选择、package、标准化和分析闭环 | 旧版 Module 4 是 optional runtime path，不是生产级 downloader | 只支持 open/public，先做 file selection UI 和 prepared package handoff |
| GTEx 在线闭环 | 可生成组织候选和 reference 语义，未完成表达矩阵下载标准化闭环 | 旧版有 facade / bundle 最小 runtime | 与 TCGA joint 分开推进，batch effect 处理前只能作为 reference candidate |
| TCGA + GTEx joint analysis | readiness 中明确 warning，无正式 batch correction | 旧版没有生产级 joint analysis | 保持 preview/testing；batch correction 未完成前禁止正式结论 |
| GSEA execution | gene set 管理完成，execution 未实现 | 旧版没有可直接迁移的正式 GSEA | 先做 GSEA preflight manifest，再接本地/外部执行器 |
| 富集/相关性/生存正式产品化 | 有最小 runner 或 preflight，缺 UI 参数、任务记录、结果图、报告语义闭环 | 旧版多为 readiness 或 sandbox | 在 DEG result index 稳定后按结果消费链推进 |
| 图表系统 | 无正式火山图、热图、GSEA plot、生存曲线产品输出 | 旧版未形成当前产品可复用图表链 | 放在 result schema 稳定之后，不先做孤立图 |
| 报告导出 | Markdown 草稿可生成，PDF/DOCX/HTML 不支持 | 旧版 reporting/Meta 相关不属于当前 Bioinformatics runtime | 暂保 Markdown 草稿，正式导出等结果语义稳定后再做 |
| 后台下载队列 | 无取消、retry、恢复、大文件进度 | 旧版脚本有下载能力但不是桌面队列 | 先完成小规模 GEO selected assets，再单独设计 queue |
| RAW preprocessing | 默认阻断 RAW/heavy，未处理 SRA/FASTQ/CEL/BAM/CRAM | 旧版有下载脚本和规则，但不是当前产品边界 | 继续隔离，不进入下一次 Preview |
| PubMed/文献 | 不属于当前 Bioinformatics 数据主线 | 旧版 literature CLI/GUI 存在，但已明确 legacy | 不迁移到 Bioinformatics，保持 Meta/文献边界 |

## 3. 旧版本能力复用判断

### 可复用为规则或 adapter

- `app/bioinformatics/legacy/geo_processing/download_validator.py`：文件 scoring、RAW/heavy 风险、Series Matrix / family.soft / supplementary / platform / imported DEG 分类规则有价值。
- `app/bioinformatics/legacy/geo_processing/detector/**`：matrix classifier、dataset detector、strategy router 可拆成规则表和 regression fixtures。
- `app/bioinformatics/legacy/geo_processing/module1_readers.py`：download plan、receipt、handoff normalization 思路可映射到当前 acquisition record。
- `app/bioinformatics/legacy/geo_processing/module3_assets.py`：standard asset layout、expression/sample/feature/dataset manifest 消费边界可作为 B5.19 resolver 参考。
- `app/bioinformatics/legacy/geo_tool/geo_pipeline/process.py`：旧 GEOparse family SOFT 处理更深，可作为 scoped parser adapter 参考。
- `app/bioinformatics/legacy/tcga_gtex/lexicon/**`：疾病、组织、TCGA/GTEx 映射词表可补强当前 query intelligence / vocabulary。
- `app/bioinformatics/legacy/tcga_gtex/facade.py`：TCGA/GTEx search/resolve/download/bundle/summary 的 minimal facade 说明了旧版边界，可参考但不能直接宣称生产级。

### 不建议迁移到当前 runtime

- 旧 `literature_cli.py` / `literature_gui.py`：属于文献/Meta 线，不属于当前 Bioinformatics 数据获取主线。
- 旧 GEO GUI / sandbox UI：交互模型与当前 PySide `workflow_pages.py` 不兼容，不建议大规模迁移。
- 旧 GEOparse pipeline 的直接输出流：目录和 manifest 假设不同，必须 adapter 化。
- 旧 RAW/SRA 下载脚本：风险高，不应进入普通 Preview。
- 旧 Meta/reporting/bias/extraction/fulltext 相关代码：不是 Bioinformatics runtime evidence。

## 4. 与 Integration 的当前差异

从 `dev/integration...dev/bioinformatics` 看，当前生信分支相对 Integration 增加或重写了大量 B5 文档、acquisition/recognition/standardization/GSEA 资源代码和测试。

需要下一阶段特别 reconcile 的 Integration 侧文件包括：

- `app/bioinformatics/analysis_task_runs.py`
- `app/bioinformatics/deg_executor_preflight.py`
- `app/bioinformatics/group_comparison_design.py`
- `app/bioinformatics/recognition_detail_report.py`
- `app/bioinformatics/recognition_next_steps.py`
- `app/bioinformatics/retrieval/geo_detail_enrichment.py`
- `app/bioinformatics/services/organism_display.py`
- `app/bioinformatics/standardized_asset_selection.py`

处理原则：

- 以当前 `recognition_report.v2`、`repository_manifest.v1`、`analysis_input_repository` 为 truth。
- Integration helper 若保留，必须改为读取当前 v2/v1 schema，不应回退到旧 recognition 或旧 analysis-ready manifest。
- `deg_executor_preflight.py` 若回收，必须消费 `analysis_input_repository` package，不应直接扫描 recognition report。

## 5. 下一阶段推进建议

### P0 - B5.19 标准化资产仓库和 extraction router

目标：把“识别到了什么”与“下游可消费什么”彻底分开。

建议任务：

1. 新建或收口 asset resolver，只读取 `standardized_data/repositories/repository_manifest.json` 和 `analysis_input_repository`。
2. 定义 stable API：获取默认 expression、sample metadata、group design、feature annotation、clinical、imported result、GMT gene set。
3. 把 DEG preflight、GSEA preflight、correlation/enrichment/survival 的输入选择统一走 resolver。
4. 合并或替代 Integration 的 `standardized_asset_selection.py`，避免双 truth。
5. 增加 fixtures：单表达矩阵、多表达候选、Series Matrix probe ID、imported DEG、缺 sample metadata、样本 mismatch。

验收口径：

- recognition 改变后，stale repository 必须提示重建。
- 多候选未确认时，正式分析 package blocked。
- imported DEG 只能作为 imported result / enrichment-from-imported-result 输入，不能进入 recompute DEG。
- GSEA gene set 未选择只阻断 GSEA，不阻断数据检查或 DEG preflight。

### P1 - analysis task execution 最小闭环

目标：把已有最小 runner 从“代码存在”推进到“桌面受控任务闭环”。

建议任务：

1. 引入统一 task run record：输入 package、参数、runner version、semantic boundary、result paths、warnings。
2. 先接 GEO DEG controlled runner，但默认标注 testing-level，且要求 preflight passed/warning-with-confirmation。
3. 写入 `results/summaries/result_index.json`，让结果浏览和报告读取真实 task output。
4. 禁止在输入不足时生成假结果、假图和正式结论。

### P2 - platform mapping 和 sample alignment gate

目标：解决 GEO Series Matrix / family SOFT 进入 DEG 前最关键的可信度缺口。

建议任务：

1. 基于旧版 platform annotation parser 思路做 mapping quality report。
2. 对 ID_REF/probe_id 数据输出“需要平台映射”的 blocker 或 warning。
3. 做 sample ID alignment report：表达矩阵列、sample metadata、group design 三方一致性。
4. UI 中给人工确认入口，确认前不解除正式执行 blocker。

### P3 - TCGA/GDC 和 GTEx open/public 闭环

目标：形成受控的数据包，而不是只停留在候选列表。

建议任务：

1. GDC file selection UI：open access、data category/type、workflow type、file size、case/sample availability。
2. GTEx normal reference package selection：组织、版本、样本数、表达矩阵来源。
3. 下载后统一走 acquisition record -> recognition v2 -> repository。
4. TCGA + GTEx joint analysis 继续保持 testing，batch correction 未实现前不开放正式结论。

### P4 - GSEA / enrichment / correlation / survival 产品化

目标：在 resolver 和 result index 稳定后再开放二级分析。

建议顺序：

1. GSEA preflight manifest：selected GMT、gene ID type、expression ranking source、blockers。
2. ORA enrichment：先只消费 confirmed DEG/imported DEG 和 selected GMT。
3. Correlation：只消费 confirmed expression asset 和目标基因。
4. Survival：只消费 confirmed clinical/survival metadata 和 expression/group asset。
5. 图表和报告导出放到 result schema 稳定之后。

## 6. 当前 Preview 口径

可以对内承诺：

- 项目工作流骨架可运行。
- 本地文件、GSE plan、GEO family SOFT、GEO asset manifest、selected assets 下载和 acquisition handoff 已形成闭环。
- recognition v2 可识别 GEO/TCGA/GTEx/local processed/metadata/clinical/annotation/imported DEG/RAW-heavy 等类别。
- 标准化确认和 repository v2 能生成 analysis input package。
- GSEA gene set resource manager 已能 import/validate/download/cache/select。
- 报告草稿能明确区分候选、preflight、imported result、testing-level、not-run。

不能对外承诺：

- 完整正式 DEG / GSEA / enrichment / correlation / survival 分析。
- limma / DESeq2 / edgeR 执行。
- 正式火山图、热图、生存曲线、富集图。
- 自动平台映射、自动分组确认、自动 normalization。
- TCGA/GDC/GTEx 生产级下载与联合分析。
- RAW/SRA/CEL/BAM/CRAM preprocessing。
- PubMed/文献检索属于 Bioinformatics 当前主线。

## 7. 验证记录

本报告生成前已执行：

- `git status --short --branch`
- `git worktree list`
- `git diff --name-status dev/integration...dev/bioinformatics -- app/bioinformatics docs/bioinformatics tests/bioinformatics tests/ui/test_bioinformatics_workflow_pages.py`
- 源码审计：`app/bioinformatics/**`、`tests/bioinformatics/**`、`docs/bioinformatics/**`、`app/bioinformatics/legacy/**`

本报告生成后已执行：

- `python3 -m pytest tests/bioinformatics -q`：267 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q`：95 passed
- `python3 -m app.main --smoke-test`：passed，source launch，`git_head=70c3419`
- `git diff --check`：passed
