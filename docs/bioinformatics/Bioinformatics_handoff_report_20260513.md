# Bioinformatics Handoff Report - 2026-05-13

## 1. Branch / Worktree Summary

本报告基于当前 Bioinformatics 独立 worktree 的实际文件、提交记录、阶段报告和本轮重新运行的验证命令生成。报告生成前，当前 worktree `git status --short --branch` 为 clean；保存本报告后会出现一个未提交的新报告文件，按用户要求本轮不自动提交。

- 当前 worktree 路径：`/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`
- 当前 git branch：`dev/bioinformatics`
- 当前 HEAD commit：`699312b`
- 最新提交：`699312b feat(bioinformatics): add imported deg result browser`
- 未提交改动：报告生成前无；报告保存后仅新增本报告文件。
- upstream：`git branch -vv --list dev/bioinformatics` 未显示 upstream tracking；remotes 存在 `origin` 和 `old-origin`。
- 与 MainLine / stable 分叉：存在明显分叉。`stable/mainline...dev/bioinformatics` 计数为 `87 10`，即 `stable/mainline` 有 87 个提交未进入当前分支，`dev/bioinformatics` 有 10 个提交未进入 `stable/mainline`；merge-base 为 `59369de`。
- 当前分支职责边界：Bioinformatics 负责 GEO / TCGA / GTEx / local expression data 的生信数据入口、识别、标准化、分析配置、结果浏览和报告草稿辅助。不得执行 PubMed 文献检索作为 Bioinformatics 数据检索，不得把 Meta 文献候选混入生信，不得生成 fake DEG / fake 火山图 / fake 富集结果，不得把 dry-run、preflight、imported、testing-level 写成真实计算结果。

本轮已执行状态命令：

```bash
pwd
git status --short --branch
git branch --show-current
git rev-parse --short HEAD
git log --oneline -5
git --git-dir="/Users/changdali/Developer/biomedpilot v1.0/_repo.git" rev-list --left-right --count stable/mainline...dev/bioinformatics
```

最近 5 个提交：

```text
699312b feat(bioinformatics): add imported deg result browser
0479af3 Add Bioinformatics DEG preflight page
d9275c7 Document bioinformatics B1 closure
f10d4a4 Userize bioinformatics results and reports
16e2877 Userize bioinformatics analysis task center
```

## 2. Current Functional Scope

### 已实现并可运行的功能

- Bioinformatics workspace shell：项目首页、数据选择、中文研究主题检索、数据识别、readiness、数据标准化、分析任务中心、DEG 配置/preflight、imported DEG 浏览、结果浏览、项目报告、设置页均可初始化并通过 UI 测试。
- 项目创建与打开：`project_manifest.json`、`project_config.json`、项目目录结构由 `app/bioinformatics/project_workspace.py` 创建和校验。
- 本地数据导入 / GSE 编号计划：`app/bioinformatics/project_workspace_binding.py` 可写入 acquisition plan / record / handoff。
- 数据识别：`app/bioinformatics/project_recognition.py` 可识别表达矩阵、raw count matrix、sample metadata、clinical/survival metadata、differential result table 等类型，并写 recognition report。
- 分组预览与比较配置：`app/bioinformatics/group_preview.py` 和 `app/bioinformatics/comparison_config.py` 支持候选分组、人工 comparison config 和样本匹配检查。
- 标准化资产注册：`app/bioinformatics/project_standardization.py` 写入 standardized asset registry 和 analysis-ready manifest，但这是资产注册和轻量校验，不等于正式 biological normalization。
- Readiness / capability matrix：`app/bioinformatics/project_readiness.py` 生成 readiness report 和 analysis capability matrix。
- 分析任务中心：`app/bioinformatics/project_analysis_tasks.py` 生成任务中心和 task records；UI 已用户化，能区分可配置、缺输入、导入结果和 testing-level。
- B2 DEG 配置与 preflight：`app/bioinformatics/deg_task_plan.py` 只做输入校验，生成 `analysis/deg/preflight/deg_preflight_manifest.json`，不运行 DEG。
- B3 imported DEG 浏览：`app/bioinformatics/imported_deg_results.py` 可识别导入 DEG 表主要列、预览行、预览上调/下调/不显著计数，并可标记为报告候选，但保持 `result_semantics = imported result`。
- 结果浏览与报告草稿：`app/bioinformatics/results/project_results.py` 和 `app/bioinformatics/reports/project_report_builder.py` 可读取 result index、生成 Markdown 报告草稿和 report manifest。

### 已接入 UI 但仍是占位 / 测试级 / draft 的功能

- 中文研究主题检索：query draft 和 GEO / TCGA / GTEx 分区工作台可用于内部测试；不得描述为正式联网检索或正式 AI 完成结果。
- DEG 配置/preflight：仅配置、仅校验、未运行真实差异分析。
- imported DEG 浏览：只浏览用户导入 / 外部分析结果，不代表 BioMedPilot 重新计算。
- 结果浏览和报告草稿：能展示 imported / testing-level / dry-run / configured-not-run / future real computed result 语义，但当前不能作为正式科研结论。
- DOCX / HTML / PDF 导出：UI 中仍为 testing placeholder 或未正式支持。
- 设置页本地 AI：AI 默认关闭；只可经 AI Gateway；本分支不应绕过 AI Gateway 或保存 raw prompt / raw response。
- 开发者诊断：大量 raw JSON、manifest path、schema、raw path 保留在折叠区用于排查，不应进入普通主界面。

### 只有后端或服务层，还没有稳定用户主流程的功能

- `app/bioinformatics/services/*` 中的 correlation / enrichment / survival / differential_expression / geo_* 服务与 adapter 有测试覆盖，但多数仍是服务层或 preview/testing-level，不应写成生产分析能力。
- `app/bioinformatics/tcga/*` 有 TCGA barcode、expression、clinical、prepared package、deg runner 相关测试和工具，但当前 B1-B3 用户主线没有将其包装成正式用户可运行的真实 DEG 流程。
- `app/bioinformatics/legacy/**` 保留历史 GEO / TCGA / GTEx / legacy tooling；它不是当前 UI 主线的证明，后续不得无差别迁入。

### 仅有设计、文档或预留接口的功能

- 真实 DESeq2 / edgeR / limma executor 接入仍未完成。
- 真实火山图、热图、富集、GSEA 结果生成未完成。
- TCGA / GTEx 完整真实文件下载和批次校正未完成。
- 报告模板深度用户化、正式报告导出和 Integration 合并验证仍未完成。

## 3. Completed Work Since Last Handoff

- 完成：B1F 用户可测试闭环总验收
  - 涉及文件：`docs/bioinformatics/stage_B1_user_test_closure_report_20260513.md`
  - 行为变化：无运行时代码变化；形成 B1 总结论和后续 B2-B6 建议。
  - UI 变化：无。
  - 数据/manifest：无 schema 变更。
  - 测试：阶段报告记录 `smoke-test`、`tests/bioinformatics`、`tests/ui`、`git diff --check` 通过；当时结果分别为 215 / 143 passed。

- 完成：B2 独立 DEG 配置页与 preflight 输入校验
  - 涉及文件：`app/bioinformatics/deg_task_plan.py`、`app/bioinformatics/workflow_pages.py`、`app/bioinformatics/workspace.py`、`tests/bioinformatics/test_deg_task_plan.py`、`tests/ui/test_bioinformatics_workflow_pages.py`、`docs/bioinformatics/stage_B2_deg_config_preflight_20260513.md`
  - 行为变化：新增 DEG preflight 服务，只校验表达矩阵、样本列、sample metadata、group design、comparison design、case/control、样本名匹配、数值矩阵预览和 imported DEG 排除。
  - UI 变化：新增“DEG 配置与 preflight 输入校验”页；分析任务中心进入 DEG 配置页而不是直接创建易误解的结果。
  - 数据/manifest：允许生成 `analysis/deg/preflight/deg_preflight_manifest.json`；语义为 `input_preflight_only_not_deg_result`、`execution = not_run`、`not_a_result = true`。不写 result index。
  - 测试：新增 service 和 UI 测试覆盖缺分组 blocker、passed/blocked 语义、imported DEG 不作为重新计算输入、不生成结果文件。

- 完成：B3 imported DEG 专门浏览与用户结果详情页
  - 涉及文件：`app/bioinformatics/imported_deg_results.py`、`app/bioinformatics/workflow_pages.py`、`app/bioinformatics/workspace.py`、`tests/bioinformatics/test_imported_deg_results.py`、`tests/ui/test_bioinformatics_workflow_pages.py`、`docs/bioinformatics/stage_B3_imported_deg_result_browser_20260513.md`
  - 行为变化：新增 imported DEG 浏览服务，可从 recognition 或 result index 收集 imported differential result table，识别 gene/logFC/p-value/FDR 列，限制预览行数，计算预览级上调/下调/不显著数量。
  - UI 变化：分析任务中心新增“查看已导入差异分析结果”；结果浏览页新增“导入结果浏览”；新增 imported DEG 专门页，主界面隐藏 raw path、schema、manifest 等技术字段。
  - 数据/manifest：`mark_imported_deg_report_candidates()` 可写 result index entry，但保持 `result_semantics = imported result` 和导入警告；不生成 DEG 表、火山图、富集或 GSEA。
  - 测试：新增 service 和 UI 测试覆盖列识别、报告候选、B2 preflight 边界、无 fake result、UI 文案和开发者诊断。

- 完成：总控 handoff 外部补记
  - 涉及文件：`/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/current_handoff_20260513.md`
  - 行为变化：这不是 Bioinformatics git worktree 内文件；已追加 B2/B3 结果输入边界说明，便于后续全项目 handoff 汇总。
  - UI 变化：无。
  - 数据/manifest：无。
  - 测试：未作为 Bioinformatics commit 管理；本报告只记录其存在，不把它算作当前 worktree 提交。

## 4. Important Files and Entry Points

### 主要 UI 文件

- `app/bioinformatics/workspace.py`：Bioinformatics workspace 的 QStackedWidget 入口，连接项目首页、数据选择、中文主题检索、识别、readiness、标准化、分析任务、DEG 配置、imported DEG 浏览、结果浏览、报告和设置页。
- `app/bioinformatics/workflow_pages.py`：当前主要 UI 页集中实现文件。包含 DataSource、ChineseDatasetSearch、Recognition、Readiness、StandardizedAssets、AnalysisTaskCenter、DegConfig、ImportedDegBrowser、ResultsBrowser、ReportViewer、Settings 等页面。
- `app/bioinformatics/project_home.py`：Bioinformatics 项目首页 UI。

### 主要 service / workflow 文件

- `app/bioinformatics/project_workspace.py`：项目目录、`project_manifest.json`、`project_config.json` 创建和校验。
- `app/bioinformatics/project_workspace_binding.py`：本地导入 / GSE acquisition plan / record / handoff 写入和读取。
- `app/bioinformatics/project_recognition.py`：数据识别、文件类型识别、recognition report 写入。
- `app/bioinformatics/group_preview.py`：候选分组预览和 group preview report。
- `app/bioinformatics/comparison_config.py`：人工 comparison config 解析、保存路径、样本匹配。
- `app/bioinformatics/project_readiness.py`：readiness report 和 analysis capability matrix。
- `app/bioinformatics/project_standardization.py`：标准化资产注册、analysis-ready manifest、data processing task plan。
- `app/bioinformatics/project_analysis_tasks.py`：analysis task center 和 task records。
- `app/bioinformatics/deg_task_plan.py`：B2 preflight 输入校验，只产出 preflight manifest，不运行 DEG。
- `app/bioinformatics/imported_deg_results.py`：B3 imported DEG 浏览和报告候选标记。
- `app/bioinformatics/results/project_results.py`：result index / result manager 读取和写入。
- `app/bioinformatics/reports/project_report_builder.py`：项目 Markdown 报告草稿和 report manifest。
- `app/bioinformatics/search_center/*`：GEO / TCGA / GTEx 搜索中心模型、normalizer、router 和 adapter。
- `app/bioinformatics/download/*`：dataset download service、GEO 页面 profile、文本摘要服务。

### 主要 schema / manifest / generated artifact 文件

- `project_manifest.json`：Bioinformatics 项目 manifest，由 `project_workspace.py` 创建。
- `project_config.json`：项目 UI/config 草稿，由 `project_workspace.py` 创建。
- `acquisition/plans/latest_acquisition_plan.json`：数据获取计划，由 `project_workspace_binding.py` 写入。
- `acquisition/records/latest_acquisition_record.json`：数据获取记录，由 `project_workspace_binding.py` 写入。
- `acquisition/handoffs/latest_acquisition_handoff.json`：数据获取到识别阶段 handoff，由 `project_workspace_binding.py` 写入。
- `logs/recognition/recognition_report.json`：数据识别报告，由 `project_recognition.py` 写入。
- `logs/recognition/group_preview_report.json`：分组预览报告，由 `group_preview.py` / `project_recognition.py` 写入。
- `raw_data/local_import/manual_supplements/comparison_config_manual.tsv`：人工比较分组配置，由 UI 或 comparison config flow 写入。
- `logs/readiness/readiness_report.json`：readiness report，由 `project_readiness.py` 写入。
- `manifests/analysis_capability_matrix.json`：分析能力矩阵，由 `project_readiness.py` 写入。
- `manifests/standardized_assets_registry.json`：标准化资产 registry，由 `project_standardization.py` 写入。
- `standardized_data/analysis_ready_assets/analysis_ready_manifest.json`：analysis-ready manifest，由 `project_standardization.py` 写入。
- `manifests/data_processing_task_plan.json`：数据处理任务计划，由 `project_standardization.py` 写入。
- `manifests/analysis_task_center.json`：分析任务中心，由 `project_analysis_tasks.py` 写入。
- `analysis/task_records/*.json`：任务配置记录，由 `project_analysis_tasks.py` 写入。
- `analysis/deg/preflight/deg_preflight_manifest.json`：B2 DEG preflight 输入校验记录，由 `deg_task_plan.py` 写入；不是结果。
- `results/summaries/result_index.json`：结果索引，由 `results/project_results.py` 写入。
- `manifests/result_manager.json`：结果管理摘要，由 `results/project_results.py` 写入。
- `reports/project_analysis_report.md`：项目报告草稿，由 `project_report_builder.py` 写入。
- `reports/project_report_manifest.json`：报告 manifest，由 `project_report_builder.py` 写入。
- `logs/reports/project_report_builder_report.json`：报告生成日志，由 `project_report_builder.py` 写入。

### 主要测试文件

- `tests/bioinformatics/test_workflow_adapters.py`：项目识别、readiness、标准化、workflow adapters 的核心覆盖。
- `tests/bioinformatics/test_deg_task_plan.py`：B2 DEG preflight 边界。
- `tests/bioinformatics/test_imported_deg_results.py`：B3 imported DEG 浏览与报告候选边界。
- `tests/bioinformatics/test_comparison_config.py`：comparison config 和样本匹配。
- `tests/bioinformatics/test_geo_page_profile_service.py`、`test_dataset_download_service.py`、`test_search_center_router.py`：GEO / dataset / search center 相关服务覆盖。
- `tests/bioinformatics/test_tcga_*`：TCGA 数据工具和 prepared package 覆盖。
- `tests/ui/test_bioinformatics_workflow_pages.py`：Bioinformatics workflow UI 的主要集成测试。
- `tests/ui/test_bioinformatics_project_home.py`：项目首页 UI 测试。

### 当前报告、审计、handoff 文件

- `docs/bioinformatics/stage_B1_user_test_entry_audit_20260513.md`
- `docs/bioinformatics/stage_B1_user_test_closure_report_20260513.md`
- `docs/bioinformatics/stage_B2_deg_config_preflight_20260513.md`
- `docs/bioinformatics/stage_B3_imported_deg_result_browser_20260513.md`
- `docs/bioinformatics/Bioinformatics_handoff_report_20260513.md`（本报告）
- `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/current_handoff_20260513.md`：总控 handoff，当前不属于 Bioinformatics git worktree。

## 5. Runtime / User Flow

当前用户主流程：

```text
项目首页
-> 数据选择
-> 本地数据导入 / GSE 编号检索 / 中文研究主题检索
-> 数据识别
-> Readiness / 输入检查
-> 数据标准化
-> 分析任务中心
-> DEG 配置 / preflight
-> imported DEG 浏览
-> 结果浏览
-> 项目报告草稿
```

当前流程可用于 Bioinformatics 模块内部用户测试，但仍不是 Integration / ReleaseBuild 级闭环。主要断点和边界：

- 真实 DEG executor 未接入；B2 只做到 preflight 输入校验。
- imported DEG 浏览只展示用户导入 / 外部分析结果，不代表软件重新计算。
- testing-level GEO 差异入口仍是开发者诊断/内部测试能力，不应放大为正式分析。
- 结果浏览和报告草稿已经能区分 imported、testing-level、dry-run、configured-not-run、future real computed result，但 report builder 模板仍需 B4 继续治理。
- TCGA / GTEx 完整下载、批次校正和正式联合分析仍未形成用户可运行闭环。

## 6. Data Contracts / Manifest Contracts

| Contract / artifact | 文件位置 | 生成者 | 读取者 | 当前状态 | 后续模块可否依赖 |
|---|---|---|---|---|---|
| Project manifest | `project_manifest.json` | `project_workspace.py` | project home / workspace validation | 基础正式 contract | 可依赖，但不应擅自改 schema |
| Project config | `project_config.json` | `project_workspace.py` | workspace / UI | draft / UI config | 可读取，不宜作为跨模块正式 contract |
| Acquisition plan | `acquisition/plans/latest_acquisition_plan.json` | `project_workspace_binding.py` | data source / recognition | draft / testing-level | Bioinformatics 内可依赖 |
| Acquisition record | `acquisition/records/latest_acquisition_record.json` | `project_workspace_binding.py` | recognition / reports | draft / testing-level | Bioinformatics 内可依赖 |
| Acquisition handoff | `acquisition/handoffs/latest_acquisition_handoff.json` | `project_workspace_binding.py` | recognition / user handoff | draft / testing-level | Bioinformatics 内可依赖 |
| Recognition report | `logs/recognition/recognition_report.json` | `project_recognition.py` | readiness / standardization / results / imported DEG discovery | 内部 contract，Developer Preview | 可依赖，但字段仍需防止进入主 UI |
| Group preview report | `logs/recognition/group_preview_report.json` | `group_preview.py` / `project_recognition.py` | readiness / comparison UI | draft / preview | 可用于 UI 提示，不等于用户确认分组 |
| Manual comparison config | `raw_data/local_import/manual_supplements/comparison_config_manual.tsv` | comparison UI / helper | readiness / B2 preflight | 用户确认输入 | Bioinformatics 内可依赖 |
| Readiness report | `logs/readiness/readiness_report.json` | `project_readiness.py` | standardization / task center / reports | Developer Preview | 可依赖作输入状态，不是正式统计结果 |
| Capability matrix | `manifests/analysis_capability_matrix.json` | `project_readiness.py` | analysis task center | Developer Preview | 仅用于任务可配置性，不代表可真实运行 |
| Standardized assets registry | `manifests/standardized_assets_registry.json` | `project_standardization.py` | standardization page / B2 preflight | 轻量资产注册 | 可依赖，但不是正式 normalization |
| Analysis-ready manifest | `standardized_data/analysis_ready_assets/analysis_ready_manifest.json` | `project_standardization.py` | standardization / report | testing-level | 可用于 UI 状态，不代表正式分析准备完成 |
| Data processing task plan | `manifests/data_processing_task_plan.json` | `project_standardization.py` | developer diagnostics | draft | 不建议跨模块依赖 |
| Analysis task center | `manifests/analysis_task_center.json` | `project_analysis_tasks.py` | task center UI | draft / preview | 可用于 UI，不代表真实任务执行 |
| Task records | `analysis/task_records/*.json` | `project_analysis_tasks.py` | results / report | configured-not-run / draft | 不能作为分析结果 |
| DEG preflight manifest | `analysis/deg/preflight/deg_preflight_manifest.json` | `deg_task_plan.py` | DEG config page / diagnostics | preflight-only | 不可作为结果；可作为未来 executor 输入准备参考 |
| Result index | `results/summaries/result_index.json` | `results/project_results.py` / imported DEG candidate marking / testing-level generator | results / report | 混合语义索引 | 可依赖但必须保留 result semantics |
| Result manager | `manifests/result_manager.json` | `results/project_results.py` | developer diagnostics | draft | 不建议跨模块依赖 |
| Project report Markdown | `reports/project_analysis_report.md` | `project_report_builder.py` | report viewer / user | 草稿 | 不可作为正式科研结论 |
| Project report manifest | `reports/project_report_manifest.json` | `project_report_builder.py` | report viewer / diagnostics | draft / testing-level | 可用于 report flow，需继续 B4 用户化 |
| Builder report | `logs/reports/project_report_builder_report.json` | `project_report_builder.py` | diagnostics | draft | 不建议跨模块依赖 |

结果语义规则必须保持：

- `preflight-only`：输入校验，不是结果。
- `imported result`：外部导入结果，不是 BioMedPilot 重新计算。
- `testing-level`：内部测试级，不是正式科研结果。
- `dry-run` / `configured-not-run`：流程记录或配置草稿，未运行。
- `real computed result`：当前 B1-B3 不提供，未来真实 executor 接入并验证后才允许。

## 7. Tests and Validation

本轮实际运行：

```bash
python3 -m app.main --smoke-test
```

结果：通过。

```text
app_version=0.1.0-internal-beta
app_channel=Developer Preview / testing
launch_mode=source
app_root=/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics
git_head=699312b
workspace_entries=2
bioinformatics_features=5
meta_analysis_features=7
pyside6_available=True
```

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q
```

结果：通过，`219 passed in 1.85s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

结果：通过，`146 passed in 9.36s`。

```bash
git diff --check
```

结果：通过，无输出。

手动测试：本轮未进行桌面 GUI 手动点击测试，未打开或覆盖 `/Users/changdali/Desktop/BioMedPilot.app`，未打包 ReleaseBuild。

跳过测试：本轮未运行 `tests/shared`、`tests/meta_analysis`、`tests/labtools`、`scripts/run_tests.py` 或 ReleaseBuild packaging tests，因为本报告只审计 Bioinformatics 当前 worktree。

用户手动确认：如果进入 Integration / ReleaseBuild 或要把 B2/B3 结果语义放入全项目手册，需要人工确认是否采用本报告作为汇总来源。

## 8. Known Issues / Risks

- 本报告保存后会产生未提交文件 `docs/bioinformatics/Bioinformatics_handoff_report_20260513.md`；按用户要求不自动提交。
- 当前 Bioinformatics 与 `stable/mainline` 明显分叉：`stable/mainline` 领先 87 commits，`dev/bioinformatics` 领先 10 commits，不能直接把当前模块工作视为 MainLine 状态。
- B1-B3 已在模块 worktree 内通过测试，但尚未进入 Integration 验证，也未进入 ReleaseBuild 包。
- 真实 DEG executor 未接入；不得把 B2 preflight passed 写成真实 DEG。
- B3 imported DEG 预览计数只基于预览行和启发式列识别，不代表 BioMedPilot 正式统计输出。
- `result_index.json` 可能同时包含 imported、testing-level、dry-run、configured-not-run、future real computed result，后续开发必须保留语义字段，不能只看 `analysis_type=differential_expression`。
- `project_report_builder.py` 仍会从 recognition/result index/report artifacts 汇总内容，B4 前仍有把 raw path、manifest、schema、task record 语义带入用户报告的风险。
- `app/bioinformatics/services/geo_differential_expression_runner.py` 和 `app/bioinformatics/tcga/deg_runner.py` 等已有服务/测试不能被误解为当前用户主线已接真实正式 DEG executor。
- `docs/bioinformatics` 中存在大量历史阶段报告和 `docs/meta_dev_reports`，当前报告只代表 Bioinformatics current worktree，不代表 Meta 或 MainLine 运行状态。
- Bioinformatics 本地 `docs/handoff/Global_Development_Manual.md` 和 `docs/architecture/...` 指定副本仍不存在；当前遵循 `/01_ProjectControl/Global_Development_Manual.md` 和既有阶段报告。
- `legacy/**` 内容仍在仓库内，不应作为当前 runtime 主线的证明，也不应无审计迁入 active UI。
- AI Gateway 相关入口必须保持 disabled/default-safe，不得绕过 AI Gateway，不得保存 raw prompt / raw response。

## 9. Do Not Touch / Boundary Rules

- 不要修改 MainLine、Meta、LabTools、Integration、Vocabulary、UIShell、AI、ReleaseBuild，除非任务明确授权。
- 不要在 `_repo.git` 内编辑代码。
- 不要覆盖桌面 app、ReleaseBuild dist、用户测试入口或桌面快捷方式。
- 不要把 PubMed、PICO、Meta 文献候选或系统综述检索混入 Bioinformatics。
- 不要把 GEO / TCGA / GTEx 表达数据分析混入 Meta。
- 不要让 LabTools 计算器或图像分析工作流污染 Bioinformatics project manifests。
- 不要接入真实 DEG executor，除非新任务要求并完成 executor、输入输出、统计假设、result index 写入和安全审计。
- 不要生成 fake DEG、fake 火山图、fake 热图、fake 富集、fake GSEA 或 fake 报告结论。
- 不要把 `preflight-only`、`imported result`、`testing-level`、`dry-run`、`configured-not-run` 写成 `real computed result`。
- 不要删除 legacy、tests、stage reports、handoff docs 或项目控制文件。
- 不要在普通主 UI 暴露 asset id、manifest path、schema version、raw path、raw JSON、task id 等技术字段；保留在开发者诊断折叠区。
- 不要执行 `git push`、merge、force push、remote branch 操作或 credential handling。

## 10. Recommended Next Tasks

### Immediate Next Step

- B4：报告模板用户化。范围应集中在 `app/bioinformatics/reports/project_report_builder.py`、`BioinformaticsReportViewerWidget` 和对应测试，目标是防止 raw path、manifest、schema、task record、preflight-only 或 imported DEG 语义被写成用户版正式结论。
- 更新结果语义测试，确认 report viewer 对 `preflight-only`、`imported result`、`testing-level`、`configured-not-run`、`dry-run` 和未来 `real computed result` 的文案保持区分。
- 补一个报告级 fixture，覆盖 imported DEG report candidate 进入报告草稿时必须保留“用户导入 / 外部分析结果”标签。

### Before Integration

- 做 Bioinformatics Integration readiness audit：检查 `workspace.py`、`workflow_pages.py`、result index、report manifest 和 MainLine shell 入口是否一致。
- 明确哪些 Bioinformatics generated artifacts 可作为 Integration contract，哪些仍是 module-local draft。
- 在 Integration 前重新跑 Bioinformatics smoke、`tests/bioinformatics`、`tests/ui`，并检查 MainLine 当前工作区是否有 unrelated dirty files。
- 审计 B2/B3 新增页面在 MainLine / ReleaseBuild 是否需要额外 shell wiring 或资源同步。

### Later / Optional

- 真实 DEG executor 接入前审计：选择 DESeq2 / edgeR / limma 前，先写 executor design、R/Bioconductor 环境、输入矩阵类型、样本数、错误处理、result index 写入和报告边界。
- imported DEG 列映射 UI：支持多 contrast、宽表、用户确认列映射、阈值保存和逐项报告候选。
- TCGA / GTEx 完整下载、批次校正和联合分析前置审计。
- 大文件结果预览分页、排序、过滤和只读打开体验。
- 将开发者诊断统一成跨页面一致折叠组件，但不要在 B4 中做大规模 UI 重构。

## 11. Suggested Codex Instruction for Next Stage

```text
请在 /Users/changdali/Developer/biomedpilot v1.0/Bioinformatics 工作区执行 Bioinformatics Stage B4：报告模板用户化与结果语义防混淆。

开始前必须读取：
1. /Users/changdali/Developer/biomedpilot v1.0/README_总说明.md
2. /Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md
3. /Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/CODEX.md
4. /Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
5. /Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/docs/bioinformatics/stage_B2_deg_config_preflight_20260513.md
6. /Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/docs/bioinformatics/stage_B3_imported_deg_result_browser_20260513.md

目标：
将 Bioinformatics 项目报告草稿从偏 manifest / raw record 汇总，收敛为用户可理解、结果语义清楚的报告草稿。重点是防止 preflight-only、imported result、testing-level、dry-run、configured-not-run 被写成 real computed result。

允许修改范围：
- app/bioinformatics/reports/project_report_builder.py
- app/bioinformatics/workflow_pages.py 中 BioinformaticsReportViewerWidget 及其直接 helper
- tests/bioinformatics 与 tests/ui 中报告相关测试
- docs/bioinformatics/stage_B4_report_template_userization_20260513.md

禁止事项：
- 不接入真实 DEG executor。
- 不生成 DEG result table、火山图、热图、富集或 GSEA。
- 不修改 project manifest schema。
- 不修改 MainLine、Meta、LabTools、Integration、Vocabulary、UIShell、AI、ReleaseBuild。
- 不把 imported DEG 或 preflight 写成 BioMedPilot 真实计算结果。
- 不删除 tests、legacy、stage reports 或 handoff docs。
- 不执行 git push。

测试命令：
- python3 -m app.main --smoke-test
- QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q
- QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
- git diff --check
- git status --short --branch

报告要求：
新增 docs/bioinformatics/stage_B4_report_template_userization_20260513.md，记录修改内容、结果语义规则、仍未完成内容、测试结果和风险。

停止条件：
如果任务需要修改其他 worktree、接入真实 executor、改变 manifest schema、删除文件、执行外部网络/下载、或测试失败且修复方向不唯一，必须停止并汇报等待确认。
```
