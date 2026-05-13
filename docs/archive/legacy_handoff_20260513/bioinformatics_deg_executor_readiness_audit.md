# Bioinformatics DEG Executor Readiness Audit

审计范围：BioMedPilot / 医研智析 Bioinformatics 流程在接入真实 DEG 执行器前的准备度。重点检查 count matrix materialization、group design、asset selection、analysis task run、result index、report draft、日志和错误处理。

审计结论：当前主线不具备直接接入真实 DEG 执行器的条件。它已经具备比较完整的执行前工作流外壳，包括识别、标准化资产注册、默认资产选择、分组与比较设计、DEG task plan、dry-run task run、result index 和项目报告草稿。但核心输入仍停留在“引用原始综合表内容块”的注册层，尚未生成执行器可直接读取的 count-only 矩阵、样本设计表和比较设计包。因此下一阶段应先做执行器输入物化与校验，而不是直接调用 DESeq2 / edgeR / limma。

## 当前已具备的能力

| 环节 | 当前状态 | 主要代码 | 结论 |
|---|---|---|---|
| 识别 content blocks | 已能识别 count / FPKM / DEG / annotation / gene id metadata | `app/bioinformatics/project_recognition.py` | 可作为 DEG 输入发现来源 |
| 标准化资产注册 | 已生成 `count_matrix`、`normalized_expression_matrix`、`deg_result_table` 等 assets | `app/bioinformatics/project_standardization.py` | 是资产注册，不是正式 normalization |
| 默认资产选择 | 已支持同类多资产阻断、单资产推荐默认、selection manifest | `app/bioinformatics/standardized_asset_selection.py` | 能避免下游误选第一个资产 |
| 分组与比较设计 | 已保存 confirmed group/comparison design | `app/bioinformatics/group_comparison_design.py` | 可表达用户确认的组名、角色、比较 |
| DEG task plan | 已能从默认 count matrix 和 confirmed design 保存 DEG 配置 | `app/bioinformatics/deg_task_plan.py` | 只保存配置，不执行 DEG |
| Analysis task run | 已创建 dry-run run directory 和 manifest | `app/bioinformatics/analysis_task_runs.py` | 可追踪任务记录，但没有执行器 |
| Result index | 已区分 imported DEG、analysis task run、completed result | `app/bioinformatics/results/project_results.py` | 没有把 dry-run 写成真实结果 |
| Report draft | 已汇总 recognition/assets/design/imported DEG/task run | `app/bioinformatics/reports/project_report_builder.py` | 明确不生成假结果 |

## Count Matrix Materialization

当前 `count_matrix` asset 来自 `content_blocks`，其字段包括：

- `asset_type=count_matrix`
- `source_file`
- `source_block_type=count_expression_matrix`
- `sample_columns`
- `inferred_sample_ids`
- `inferred_groups`
- `materialize_strategy=content_block_reference`

这说明系统知道原始表中哪些列是 count，但没有生成执行器可直接消费的独立 count matrix 文件。

缺口：

- 没有 `materialized_count_matrix_path`。
- 没有 count-only TSV/CSV 输出，例如 `standardized_data/matrices/count_matrix_001.tsv`。
- 没有 sample design TSV，例如 `standardized_data/design/sample_design_001.tsv`。
- 没有 comparison design TSV，例如 `standardized_data/design/comparisons_001.tsv`。
- 没有验证 count 是否为非负整数。
- 没有处理 gene_id 缺失、重复 gene_id、重复 sample column、空值、NA、Excel 数字格式等执行器输入问题。
- 没有记录原始列到物化列的映射 manifest。

结论：真实 DEG 执行器不能直接依赖当前 `count_matrix` asset。下一阶段必须先增加 count matrix materializer。

## Group Design Readiness

当前 `manifests/group_comparison_design.json` 可保存：

- `sample_groups`
- `comparisons`
- `source_recognition_run_id`
- `source_standardized_asset_ids`
- `species`
- `gene_id_type`
- `imported_deg_references`

已具备：

- 用户确认组名和角色。
- comparison 基础校验：case/control 非空、不能相同、组名存在、样本数不少于 2。
- imported DEG comparison 只作为参考，不自动等同 confirmed design。

缺口：

- 未表达 batch、paired design、covariates、blocking factor。
- 未表达设计公式，例如 `~ condition`、`~ batch + condition`。
- 未保存每个 sample_id 到 count matrix 物化列的最终映射校验结果。
- 未校验 comparison 中 case/control 的样本列确实存在于默认 count asset。
- 未区分 biological replicate 与 technical replicate。

结论：可支持最小 one-factor DEG 设计前置配置，但不足以直接承诺通用 DEG 执行。

## Asset Selection Readiness

当前 `standardized_asset_selection.py` 已实现：

- 单候选：`recommended_default`。
- 多候选未选：`needs_selection`。
- 用户确认：`confirmed`。
- selection 指向不存在资产：`invalid`。
- 下游 resolver 可阻断多候选默认取第一个。

结论：资产选择机制已足够作为 DEG 执行器入口前置条件。但真实执行器应要求 `count_matrix` selection 为 `confirmed`，而不是仅使用推荐默认，以避免用户未确认时执行正式统计分析。

## DEG Task Plan Readiness

当前 `manifests/analysis_tasks/deg_task_plan.json` 包含：

- `source_count_asset_id`
- `source_count_asset_file`
- `source_group_design_path`
- `comparisons`
- `method`
- `thresholds`
- `status=configured_not_run`
- note：只保存配置，不执行真实差异表达分析

优点：

- 不会把 imported DEG result 当作重新计算结果。
- 没有 count matrix 或 confirmed group design 时不能创建计划。
- method 使用 `planned_placeholder`，避免误导。

缺口：

- 未保存执行器输入物化文件路径。
- 未保存软件环境需求，例如 R、DESeq2、edgeR、limma 版本。
- 未保存 normalization / size factor / dispersion / contrast 细节。
- 未保存运行资源、线程、随机种子、失败重试策略。
- 未保存 output contract，即真实完成后应产出哪些文件和字段。

结论：DEG task plan 可作为真实执行器配置草稿，但不能直接执行。

## Analysis Task Run Readiness

当前 `analysis_task_runs.py` 已实现：

- `analysis_runs/deg/<run_id>/task_run.json`
- `inputs.json`
- `parameters.json`
- `outputs_manifest.json`
- `warnings.json`
- `logs/task.log`
- 安全 run id、路径限制、atomic JSON write。

当前状态：

- dry-run 使用 `skipped_dry_run`。
- `outputs` 为空。
- `outputs_manifest.json` 明确写明 dry-run 未生成 DEG 表、火山图或富集结果。

缺口：

- 尚无 executor interface，例如 `run_deg_executor(project_root, run_id)`。
- `completed` 状态目前没有强制要求 outputs 非空；真实执行器接入前应增加完成态校验。
- 没有 stdout/stderr、command line、exit code、runtime duration、environment snapshot。
- `logs/task.log` 不是 atomic write，且只写 dry-run 文案。
- 没有失败状态下的 structured error code / recoverability。
- 没有运行锁或并发保护，未来真实执行时可能出现同一 task plan 多 run 并发。

结论：run 机制可承载执行历史，但还不是可运行执行器框架。

## Result Index Readiness

当前 `results/summaries/result_index.json` 由 `project_results.py` 生成并区分：

- `imported_deg_result`
- `analysis_task_run`
- `completed_result`

优点：

- imported DEG 来源明确为导入表格中的已有差异分析结果。
- dry-run task run 不会成为 completed result。
- report draft 可读取 result items。

缺口：

- 尚未定义真实 DEG completed result 的最小 schema。
- 尚未定义 DEG result table 输出列契约：`gene_id`、`gene_name`、`log2FC`、`pvalue`、`padj`、`baseMean`、`stat` 等。
- 尚未定义 volcano input、enrichment input、gene list 输出 manifest。
- `write_result_index()` 仍可写入任意 completed result entry，未来执行器应提供专用登记函数并校验来源 task run。

结论：结果索引能防止当前阶段误报，但真实 DEG 输出登记规则还需要单独设计。

## Report Draft Readiness

当前 `project_report_builder.py` 会生成：

- `reports/project_report_draft.md`
- `reports/project_analysis_report.md`
- `reports/project_report_manifest.json`

优点：

- 能引用 recognition、standardized assets、group design、imported DEG、task runs。
- 明确 dry-run 不代表 DEG 已完成。
- 明确不生成假 DEG 表、假火山图、假富集结果。

缺口：

- 报告 manifest 写入不是 atomic write。
- 真实 DEG 输出接入后，需要区分 imported DEG、recomputed DEG completed result、failed task run。
- 需要在报告中记录执行器版本、参数、输入矩阵 checksum、输出文件 checksum。

结论：报告草稿可作为审计视图；接入真实 DEG 后需扩展方法学和 provenance。

## 日志与错误处理

已具备：

- 多数关键 manifest 使用 atomic JSON write。
- DEG task run 路径受项目根目录限制。
- 缺少 plan / count matrix / group design 时会给出明确 warning。

不足：

- 真实执行所需日志字段尚未建立：command、stdout、stderr、exit code、duration、resource usage。
- 缺少 executor dependency preflight：R 是否可用、DESeq2/edgeR/limma 是否安装、版本是否记录。
- 缺少输入文件 checksum 和输出文件 checksum。
- 缺少失败可恢复策略，例如用户修改资产选择或 group design 后如何标记旧 run stale。
- 缺少 completed 状态校验，不能保证 completed run 一定有真实 output manifest。

## 是否已具备真实 DEG 执行条件

未具备。

可以安全进入的下一阶段是“执行器输入物化与 preflight”，不是直接运行 DESeq2 / edgeR。

最低可执行条件应包括：

1. 生成 count-only matrix 文件。
2. 生成 sample design 文件。
3. 生成 comparison design 文件。
4. 校验 count matrix 为非负整数矩阵。
5. 校验 sample design 与 count matrix 列完全匹配。
6. 校验 comparison 中 case/control 组存在且样本数达标。
7. 确认默认 count asset 已由用户保存为 confirmed selection。
8. 记录 species / gene_id_type / source_recognition_run_id / source_asset_id。
9. 生成 executor input manifest，包含 checksum。
10. 运行 dependency preflight，但不执行 DEG。

## 建议下一阶段：Stage 3.5b / 3.6 前置

建议先实现 `deg_executor_preflight.py`，只做输入物化和校验：

- `materialize_count_matrix(project_root, count_asset_id) -> count_matrix.tsv`
- `materialize_sample_design(project_root, group_design) -> sample_design.tsv`
- `materialize_comparison_design(project_root, group_design) -> comparisons.tsv`
- `validate_deg_inputs(...) -> preflight_manifest.json`
- 输出路径建议：
  - `standardized_data/deg_inputs/<run_id>/count_matrix.tsv`
  - `standardized_data/deg_inputs/<run_id>/sample_design.tsv`
  - `standardized_data/deg_inputs/<run_id>/comparisons.tsv`
  - `analysis_runs/deg/<run_id>/executor_preflight.json`

真实执行器接入前，不应：

- 调用 DESeq2 / edgeR / limma。
- 生成 DEG result table。
- 生成火山图。
- 生成富集结果。
- 把 `skipped_dry_run` 或 `configured_not_run` 标记为 completed。

## 风险清单

| 风险 | 严重度 | 说明 | 建议 |
|---|---:|---|---|
| count matrix 未物化 | 高 | 当前资产只引用原始综合表列，执行器无法直接读取 | 先实现 count matrix materializer |
| count 值未验证 | 高 | DESeq2/edgeR 需要 raw integer counts | 增加非负整数、缺失值、重复基因校验 |
| completed 状态缺少 output guard | 中 | 未来误标 completed 可能污染报告 | completed 必须要求 outputs manifest 非空且文件存在 |
| group design 仅支持简单比较 | 中 | 没有 batch/covariate/paired design | v1 限定 one-factor design，UI 明示限制 |
| dependency preflight 缺失 | 中 | 无法知道 R/包版本 | 增加环境检查和版本记录 |
| report manifest 非 atomic write | 低 | 写入中断可能留下半写入报告 manifest | 后续统一 report atomic write |

## 审计结论

主线当前已经完成真实 DEG 执行器所需的业务外壳，但缺少最关键的执行输入物化和强校验层。真实 DEG 之前应先完成“输入物化 + executor preflight + completed output contract”。在这些补齐前，系统应继续保持当前行为：只允许生成 DEG task plan 和 dry-run task run，不执行真实 DEG，不生成假结果。
