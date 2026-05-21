# B8.1 Standardized Analysis Input Resolver

## 旧实现审计与迁入判断

| 范围 | 判断 | 可复用内容 | 不直接迁入原因 | 本阶段处理 | 测试 |
| --- | --- | --- | --- | --- | --- |
| `project_standardization.py` / `project_readiness.py` | 最小迁入 | repository manifest、asset registry、analysis_input_repository 文件形态 | 旧 package type 不完整，状态不足以表达 formal/preflight/exploratory | resolver 只读取其产物并规范化为 v2 package | `test_analysis_input_resolver.py` |
| `project_analysis_tasks.py` / `deg_task_plan.py` | 直接保留 | 既有配置草稿和 preflight 文案边界 | 仍是配置/预检，不是统一 task-run contract | 新增独立 `analysis_task_runs.py` contract | `test_analysis_task_run_contract.py` |
| `results/project_results.py` / `workflow_pages.py` | 最小迁入 | 结果浏览和 UI diagnostics 入口 | 旧 result schema 字段不足 | UI 增加 resolver diagnostics，结果 schema 在 B8.4 收口 | UI 既有测试 + resolver 单测 |
| Integration `standardized_asset_selection.py` / `analysis_task_runs.py` / `deg_executor_preflight.py` | 不迁入，仅记录 | contract 命名和 preflight 思路 | 路径、schema 与当前分支不一致 | 只保留“从标准化资产选择输入”的设计原则 | 文档记录 |
| `legacy/geo_processing/*`、`legacy/geo_pipeline/process.py`、ReleaseBuild model9 analysis/local_data | 不迁入，仅记录 | GEO/probe/value type 识别思路 | runner/legacy 输出不能直接成为正式输入 | 仅转化为阻断规则和审计边界 | blocker 单测 |

## 新 Resolver 模型

新增 `app/bioinformatics/analysis_inputs/*`，统一输出：

- `deg_recompute`
- `deg_imported_result`
- `enrichment_from_deg`
- `gsea_preranked`
- `correlation_expression`
- `immune_score_linkage`
- `tcga_clinical_survival_preflight`

Resolver 只读取 standardized repository / registry / analysis_input_repository，不读取 `recognition_report.json` 或 runner 临时文件。

## Task-run Contract

新增 `analysis_task_runs.py`，字段包括 `task_run_id`、`task_type`、`input_package_id`、`task_semantics`、`parameters`、`dependency_snapshot`、`status`、`blockers`、`warnings`、`output_artifacts`、`result_index_entry`、`logs`、`failure_reason`。默认状态限制在 `not_run`、`config_only`、`preflight_only`、`blocked`。

## Blockers / Warnings

实现 multiple candidate matrix、GEO ID_REF/probe mapping、TPM/FPKM count-model DEG、GTEx auto control、imported DEG external semantics、immune/TME exploratory 等规则。

## UI Diagnostics

`BioinformaticsAnalysisTaskCenterWidget` 新增 resolver summary，显示 input package 数量、类型和 formal DEG/GSEA/Survival/Plot/Report-ready 仍受 gate 控制。

## 未实现边界

未执行 DEG/GSEA/survival，未生成 plot artifact，未生成 report-ready package，未新增 scipy/statsmodels/R/lifelines 依赖。

## B8.2 建议

从 `deg_recompute` package 构建 DEG-ready matrix，并把 sample alignment、gene mapping、value type policy 独立为可测试 contract。
