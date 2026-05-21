# Bioinformatics 第一阶段 - 旧版本能力审计与当前链路定界

日期：2026-05-14

范围：只读审计为主；本阶段未迁移旧代码、未改 runtime、未联网下载数据、未运行桌面打包。唯一产物是本审计报告。

## 0. 审计范围与源码现实

当前工作区：

- 路径：`/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`
- 分支：`dev/bioinformatics`
- HEAD：`c5b2f4a`
- 当前存在未跟踪文件：
  - `docs/bioinformatics/Bioinformatics_handoff_report_20260513.md`
  - `docs/bioinformatics/.stage_B5_12_legacy_acquisition_standardization_audit_20260514.md.swp`
- 本报告未修改上述未跟踪文件。

并列 worktree：

- `../MainLine`：`stable/mainline`，HEAD `83749d1`
- `../Integration`：`dev/integration`，HEAD `59ee32b`
- `../ReleaseBuild`：`dev/release-internal-test`，HEAD `f3f9f45`

路径差异：

- 用户指定的 `ReleaseBuild/archive/legacy_sources/model9/**` 在当前 Bioinformatics 工作区内部不存在。
- 实际可审计路径是并列 worktree：`../ReleaseBuild/archive/legacy_sources/model9/**`。
- 当前工作区内存在 `app/bioinformatics/legacy/**`。

当前与 Integration 的 Bioinformatics 差异：

- 当前 `dev/bioinformatics` 比 Integration 多：`app/bioinformatics/gse_file_download_candidates.py`。
- 当前 `dev/bioinformatics` 比 Integration 少：
  - `app/bioinformatics/analysis_task_runs.py`
  - `app/bioinformatics/deg_executor_preflight.py`
  - `app/bioinformatics/group_comparison_design.py`
  - `app/bioinformatics/recognition_detail_report.py`
  - `app/bioinformatics/recognition_next_steps.py`
  - `app/bioinformatics/retrieval/geo_detail_enrichment.py`
  - `app/bioinformatics/services/organism_display.py`
  - `app/bioinformatics/standardized_asset_selection.py`

结论：当前 `dev/bioinformatics` 不能直接等同于 Integration Preview。后续进入 Integration 时，需要 scoped carry-over 或明确舍弃差异文件。

## 1. 当前能力矩阵

| 能力域 | 当前 runtime 状态 | 证据文件 | 真实边界 |
| --- | --- | --- | --- |
| 项目入口与主线页面 | 已有项目首页、数据导入与检索、中文主题检索、数据识别、Ready 检查、标准化、任务中心、结果浏览、项目报告、设置页 | `app/bioinformatics/workflow_pages.py`, `app/bioinformatics/workspace.py` | 主线可测，但 Ready 检查和工作流总控仍偏开发者视角 |
| Acquisition 记录 | 已有 `register_acquisition()`，写 plan / record / handoff，支持 copy / reference / plan_only | `app/bioinformatics/project_workspace_binding.py` | 能登记本地文件、GSE plan、下载后文件；不是后台下载队列 |
| GSE 编号入口 | 已有 plan-only 登记、GEO 详情、family SOFT 下载、asset manifest、补充文件下载入口 | `workflow_pages.py`, `download/dataset_download_service.py` | family SOFT 可下载；Series Matrix / supplementary 依赖 manifest 与用户选择 |
| 中文主题检索 | 已有 GEO / TCGA-GDC / GTEx 三源草稿与 router | `search_center/**`, `retrieval/bio_query_adapter.py` | PubMed 被排除；TCGA/GTEx 多为候选或下载清单，不是完整表达矩阵下载 |
| GEO 文件发现 | 已有 NCBI HTTPS directory listing manifest，发现 family SOFT / Series Matrix / supplementary | `download/dataset_download_service.py`, `services/geo_metadata_profile_service.py` | 未在本阶段 live 网络验证；目录 size 不总是完整 |
| GSE 下载候选选择 | 当前分支已新增候选选择 manifest，默认选择 Series Matrix 与高优先级 processed expression；排除 RAW 和 imported DEG 默认下载 | `gse_file_download_candidates.py` | Integration 尚未有此文件，需 carry-over |
| 下载 receipt/cache/handoff | 已写 download_request / receipt / asset_manifest，下载成功后 reference 注册 source_files | `download/dataset_download_service.py` | 没有取消、后台队列、正式 retry policy |
| 文件识别 | 已识别 Series Matrix、family.soft、CSV/TSV/XLSX expression/metadata/clinical/annotation/imported DEG | `project_recognition.py`, `geo_series_matrix_parser.py`, `geo_family_soft_parser.py` | 识别输出是候选与证据，不是正式标准化矩阵 |
| Series Matrix parser | 已解析 metadata、sample fields、matrix block preview、ID_REF、sample columns、species evidence | `geo_series_matrix_parser.py` | 不物化完整大矩阵，不自动平台映射，不自动确认分组 |
| family SOFT parser | 当前已有 native parser 识别 series/sample/platform blocks、sample metadata、phenotype、platform annotation、sample table expression 候选 | `geo_family_soft_parser.py`, `project_recognition.py` | 不再只是 container-only，但仍不是旧 GEOparse 的完整处理器 |
| 标准化确认 | 已有 expression/sample/group/species/gene ID/platform/imported DEG candidates 与 `standardization_confirmation.json` | `standardization_confirmation.py` | 用户确认层，不做 normalization、sample 对齐或 ID 映射 |
| 标准化资产注册 | 已生成 registry、analysis-ready manifest、data processing task plan | `project_standardization.py` | 只是资产注册和轻量校验，不等于 biological normalization |
| Readiness | 分离 `standardization_ready`、`standardization_confirmed`、`deg_preflight_ready`、`imported_result_ready` | `project_readiness.py` | DEG readiness 不是正式 DEG executor 通过 |
| 分析任务中心 | 可创建 preview/testing 任务记录 | `project_analysis_tasks.py`, `workflow_pages.py` | 当前创建任务记录，不等于正式统计执行 |
| 真实分析服务 | 存在 differential expression、enrichment、correlation、survival、TCGA import 等服务和测试 | `services/**`, `tcga/**`, `tests/bioinformatics/**` | 当前 acquisition -> recognition -> standardization 主线尚未证明这些服务可作为 Preview 承诺面 |
| 报告 | 可生成 Markdown 项目报告草稿 | `reports/project_report_builder.py`, `results/project_results.py` | 报告只能基于已有结果索引；不能伪造成真实分析结果 |

## 2. 旧版本可复用能力清单

可直接作为规则或 adapter 参考：

- `app/bioinformatics/legacy/geo_processing/download_validator.py`
  - 文件 scoring、RAW/heavy 风险、Series Matrix / family.soft / supplementary / platform / imported DEG 分类规则值得复用。
  - 建议作为只读分类规则或 dev audit helper，不直接替换当前 recognition truth。
- `app/bioinformatics/legacy/geo_processing/detector/**`
  - `matrix_classifier.py`、`dataset_detector.py`、`strategy_router.py` 对 supplementary expression、metadata、diff-result suppression、strategy 选择有价值。
  - 适合拆成测试用 fixtures 和规则表。
- `app/bioinformatics/legacy/geo_processing/module1_readers.py`
  - 旧 download plan / receipt / handoff normalization 思路可参考。
  - 必须映射到当前 `acquisition_record`、`recognized_files`、`standardization_confirmation` schema。
- `app/bioinformatics/legacy/geo_processing/module3_assets.py`
  - standard asset layout 思路可参考，尤其 expression / sample / feature / dataset manifest 的消费边界。
  - 不建议直接复用输出路径和旧 manifest。
- `app/bioinformatics/legacy/geo_tool/geo_pipeline/process.py`
  - 旧 GEOparse family SOFT 处理深度较强：phenotype、probe expression、GPL annotation、gene-level aggregation。
  - 适合后续做 scoped adapter，但不应直接调用旧 CLI/output flow。
- `app/bioinformatics/legacy/tcga_gtex/lexicon/**`
  - 疾病、组织、TCGA/GTEx 映射词表可补强当前中文主题检索。
  - 建议先合并到 shared vocabulary / query intelligence，避免在 UI 中硬编码。
- `../ReleaseBuild/archive/legacy_sources/model9/geo_readiness/series_matrix_parser.py`
  - 可参考 parser contract、metadata/matrix preview 测试设计。
  - 当前 runtime 已有 Series Matrix MVP，不建议整文件迁移。
- `../ReleaseBuild/archive/legacy_sources/model9/geo_readiness/soft_parser.py`
  - 可参考 SOFT metadata/sample table parser 细节。
  - 当前已有 native SOFT parser，可按缺口补测试。
- `../ReleaseBuild/archive/legacy_sources/model9/geo_readiness/platform_annotation_parser.py`
  - probe -> gene symbol mapping quality report 适合后续平台映射预审。
  - 进入 Preview 前只能作为“可选预审/候选质量检查”，不能承诺自动映射完成。
- `../ReleaseBuild/archive/legacy_sources/model9/local_data/standardizer.py`
  - local standardized dataset copy、sample match、numeric value validation 可复用为标准化确认后的校验规则。
  - 不兼容当前 `standardization_confirmation.json`，需要 adapter。
- `../ReleaseBuild/archive/legacy_sources/model9/analysis/*readiness*` 与 `group_detection.py`
  - 可参考 real dataset readiness、group detection、preflight diagnostics。
  - 适合下一阶段 DEG executor pre-audit，不适合直接作为当前用户承诺面。

## 3. 不可迁移或不应迁移能力清单

不建议迁移到当前 Bioinformatics runtime：

- 旧 `literature_cli.py` / `literature_gui.py` / model9 `literature/**`
  - 属于文献/Meta 线，不应混入 Bioinformatics 数据获取主线。
  - 当前 Bioinformatics search center 明确只允许 `geo`、`tcga_gdc`、`gtex`。
- 旧 Meta UI、app_meta、bias、extraction、fulltext、reporting 等 model9 Meta 相关模块
  - 与当前 Bioinformatics acquisition -> recognition -> standardization 链路无直接关系。
  - 只能作为历史参考，不作为生信 runtime evidence。
- 旧 GEO workflow UI / sandbox
  - 旧交互和当前 `workflow_pages.py` 页面栈不兼容。
  - 不应大规模迁移旧 UI。
- 旧 GEOparse pipeline 的直接 output flow
  - 会写自己的 CSV/JSON 输出，假设旧目录结构。
  - 不符合当前 recognition/standardization schema，必须 adapter 化。
- RAW FASTQ/SRA/CEL/BAM/CRAM preprocessing
  - 当前只有风险识别和不默认下载策略。
  - 不应进入下一次 Integration Preview。
- 正式 DEG executor、limma、DESeq2、edgeR、正式火山图/热图/富集/生存分析
  - 当前主线 readiness 尚未完成标准化物化、sample 对齐、平台映射和统计执行验证。
  - 可以进入后续 pre-audit，不应作为当前 Preview 承诺。
- PubMed 检索
  - 当前 Bioinformatics 数据获取主线不包含 PubMed。
  - GEO metadata 中出现 PMID 只属于 dataset metadata。
- 自动确认分组、物种、表达值类型、gene ID 类型、平台映射
  - 当前设计要求用户确认。
  - 自动化只能作为候选建议，不可写成事实。

## 4. 当前 acquisition -> recognition -> standardization 真实状态

### 4.1 Acquisition

已具备：

- 本地文件 copy/reference 登记。
- GSE plan-only 登记。
- GEO family SOFT HTTPS 下载。
- GEO asset manifest 发现 Series Matrix / supplementary / RAW/heavy。
- 当前分支已有 GSE 文件候选选择 manifest。
- `download_geo_manifest_assets()` 可按 selection manifest 下载选中文件。
- 下载完成后通过 `register_acquisition(strategy="reference")` 把真实文件路径写入 `source_files`。
- TCGA/GDC 和 GTEx 可写下载清单，但不伪造本地表达矩阵。

真实限制：

- 没有后台队列、取消、正式 retry、细粒度进度。
- TCGA/GDC、GTEx 还不是完整在线下载到 expression matrix 的闭环。
- live 网络没有在本阶段验证。
- 当前 GSE 候选选择能力在 `dev/bioinformatics`，尚未进入 Integration。

### 4.2 Recognition

已具备：

- 从 acquisition `source_files` 进入识别。
- Series Matrix：metadata、sample fields、matrix block preview、ID_REF、value type candidate、species evidence。
- family.soft：series/sample/platform blocks、sample metadata、phenotype candidate、platform annotation、sample expression table candidate。
- CSV/TSV/XLSX：expression/count/FPKM/TPM、sample metadata、clinical/survival、annotation、imported DEG。
- imported DEG 与 expression matrix 区分，不作为重新计算输入。

真实限制：

- 识别仍是候选和 evidence，不代表标准化完成。
- Series Matrix 不物化完整大矩阵。
- family.soft 当前 native parser 已强于早期 container-only，但未达到旧 GEOparse 完整处理深度。
- RAW/heavy 只做风险或不支持提示。

### 4.3 Standardization

已具备：

- 从 recognized files 收集 expression、sample metadata、group、species、gene ID、platform、imported DEG candidates。
- 写 `manifests/standardization_confirmation.json`。
- 写 `manifests/standardized_assets_registry.json`。
- 写 `standardized_data/analysis_ready_assets/analysis_ready_manifest.json`。
- 写 `manifests/data_processing_task_plan.json`。
- readiness 区分标准化发现、标准化确认、DEG preflight、imported result browse。

真实限制：

- 不做正式 normalization。
- 不做 sample name 对齐的最终 materialized matrix。
- 不做 ID_REF -> gene symbol/gene ID 自动映射。
- 不运行正式 DEG。
- `analysis_ready_manifest` 是 registry/readiness 层，不是可发表或正式统计输入证明。

## 5. 后续阶段优先级

P0 - Integration 前必须定界：

1. 将当前 `gse_file_download_candidates.py` 及对应测试决定是否 carry-over 到 Integration。
2. 对齐当前 Bioinformatics 与 Integration 缺失/新增文件，特别是 `recognition_detail_report.py`、`recognition_next_steps.py`、`standardized_asset_selection.py`、`deg_executor_preflight.py` 是否进入 Preview。
3. 写一份 Integration merge checklist，明确哪些文件来自 current，哪些文件来自 Integration，哪些旧能力保持 legacy。

P1 - acquisition -> recognition 闭环验证：

1. 桌面手动测试：GSE 编号 -> family SOFT 下载 -> asset manifest -> 候选选择 -> Series Matrix / supplementary 下载 -> 待处理数据集文件级显示 -> recognition。
2. 验证 `source_files` 不丢批次内其他文件。
3. 验证 RAW/heavy、imported DEG、platform annotation 不默认进入 expression input。

P2 - recognition -> standardization confirmation：

1. 用户确认表达矩阵、表达值类型、物种、gene ID 类型、候选分组。
2. 引入或补齐 candidate selection 控件，避免总是默认首个候选。
3. 用 model9/local_data validation 思路补 sample ID 对齐、数值类型、缺失值、负值等校验，但保持为 validation，不写成 normalization。

P3 - platform mapping pre-audit：

1. 参考 model9 `platform_annotation_parser.py` 做平台注释质量检查。
2. 输出 mapping quality report 和 blocking gaps。
3. Preview 中只显示“需要平台映射/映射质量”，不自动承诺 gene symbol 完成。

P4 - DEG executor pre-audit：

1. 只在 standardization confirmation 和 sample alignment 稳定后启动。
2. 先审计 `deg_executor_preflight.py`、`geo_differential_expression_runner.py`、`differential_expression_service.py` 与 Integration 差异。
3. limma / DESeq2 / edgeR 不进入当前第一阶段结论。

## 6. Integration / Preview 边界建议

建议纳入 Integration Preview：

- 项目首页、数据导入与检索、中文主题检索、数据识别、标准化确认、任务中心空态/预览态、结果浏览空态、报告草稿空态。
- 本地多文件导入。
- GSE 编号检索和中文主题检索的 GEO / TCGA-GDC / GTEx 候选。
- GEO family SOFT metadata 下载。
- GEO asset manifest 发现 Series Matrix / supplementary / RAW/heavy。
- 用户选择下载 Series Matrix 和高优先级 processed supplementary candidate。
- 下载后文件级待处理数据集和 recognition handoff。
- Series Matrix / family.soft / processed table / metadata / imported DEG recognition。
- Standardization confirmation 与 readiness 状态。
- 报告中只写候选、导入、未运行正式 DEG。

必须显式标注为 testing / preview：

- 中文 query draft。
- TCGA/GDC 与 GTEx 下载清单。
- analysis task center。
- imported DEG 浏览。
- report draft。

不建议纳入 Integration Preview：

- 正式 DEG、富集、GSEA、相关性、生存分析承诺。
- 火山图、热图等正式结果图。
- 自动平台映射。
- 自动分组确认。
- RAW 数据下载或预处理。
- PubMed 检索。
- 后台大文件下载队列和取消能力。
- 从旧 Module1/Module3/Geo Tool 直接迁移 UI 或旧输出流。

## 7. 阶段结论

当前 runtime 已经继承并重建了 acquisition -> recognition -> standardization 的主链路骨架，且不再只是早期的 container-only 状态。尤其是 Series Matrix、family.soft、processed supplementary、standardization confirmation 和 GSE candidate selection 已形成可测试闭环。

但当前链路的真实产品状态仍是：数据获取候选、文件下载/登记、文件识别、用户确认、轻量 readiness。它还不是完整数据标准化计算链，也不是正式 DEG/富集/可发表报告链。

旧版本最有价值的复用方向不是整体迁移，而是规则和 adapter：下载/文件分类 scoring、SOFT 深解析、平台注释质量检查、local dataset validation、readiness/preflight diagnostics。旧 Meta/文献/RAW/正式统计执行内容应继续隔离，避免污染 Bioinformatics Preview 边界。

## 8. 本阶段验证

- `git status --short --branch`：确认当前分支和未跟踪文件。
- `find` / `rg`：审计当前 `app/bioinformatics/**`、`docs/bioinformatics/**`、`tests/bioinformatics/**`、`tests/ui/**`、并列 `MainLine` / `Integration` / `ReleaseBuild`、`../ReleaseBuild/archive/legacy_sources/model9/**`。
- 本阶段未运行联网下载。
- 本阶段未运行 pytest，因为没有 runtime 代码变化。
