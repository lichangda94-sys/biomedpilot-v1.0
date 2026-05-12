# Bioinformatics Analysis Task Runs v1

## 功能目标

Stage 3.2 增加统一的 analysis task run 记录层，用来保存分析任务的一次运行意图、输入资产、比较设计、参数、状态和输出索引。当前阶段只支持从 DEG task plan 生成 dry-run 任务记录，不执行真实 DEG，不生成 DEG 表、火山图或富集结果。

## 为什么需要 task run

DEG task plan 只描述“准备怎么跑”。task run 描述“某一次任务记录”。后续真实执行器接入后，每次运行都应有独立 run 目录，避免旧结果被覆盖，并能追溯结果来自哪个 count matrix、哪个 group comparison design 和哪些阈值参数。

## 目录结构

当前使用项目内目录：

```text
analysis_runs/
  deg/
    deg_run_YYYYMMDD_HHMMSS_<shortid>/
      task_run.json
      inputs.json
      parameters.json
      outputs_manifest.json
      warnings.json
      logs/
        task.log
```

所有 manifest 写入使用 atomic write。run id 会过滤路径穿越字符，run 目录必须位于项目 `analysis_runs/` 下，并且不会覆盖已有 run。

## task_run.json schema

```json
{
  "schema_version": "bioinformatics_analysis_task_run.v1",
  "run_id": "deg_run_20260512_103012_ab12cd",
  "task_type": "differential_expression_recompute",
  "task_family": "deg",
  "status": "skipped_dry_run",
  "execution_mode": "dry_run",
  "source_task_plan": "manifests/analysis_tasks/deg_task_plan.json",
  "source_assets": [
    {
      "asset_id": "count_matrix_001",
      "asset_type": "count_matrix",
      "role": "primary_count_matrix"
    }
  ],
  "source_group_design": "manifests/group_comparison_design.json",
  "comparisons": [
    {
      "comparison_name": "PFF_vs_PBS",
      "case_group": "PFF",
      "control_group": "PBS"
    }
  ],
  "parameters": {
    "method": "DESeq2",
    "method_status": "planned_placeholder",
    "padj_threshold": 0.05,
    "abs_log2fc_threshold": 1.0
  },
  "outputs": [],
  "warnings": [],
  "created_at": "...",
  "updated_at": "...",
  "started_at": null,
  "finished_at": null,
  "error": null
}
```

## 状态枚举

支持状态：

- `configured_not_run`
- `queued`
- `running`
- `completed`
- `failed`
- `cancelled`
- `skipped_dry_run`

Stage 3.2 主要使用 `skipped_dry_run`，表示只生成任务记录，当前版本尚未执行真实差异分析。不得把 dry-run 标记为 `completed`。

## 与 DEG task plan 的关系

创建 DEG task run 前必须存在：

- `manifests/analysis_tasks/deg_task_plan.json`
- 默认 `count_matrix` 标准化资产
- `manifests/group_comparison_design.json`
- 至少一个 confirmed comparison

如果默认 count matrix 失效、分组设计缺失或 plan 中没有 comparison，系统不会创建 run，而是提示用户先补齐前置步骤。

## 与 imported DEG result 的区别

Imported DEG result 来自导入表格中已有的差异分析结果，资产类型是 `deg_result_table`，可用于结果浏览、筛选、火山图输入和富集输入。

Recompute DEG task run 来自用户配置的重新差异分析任务，输入是 `count_matrix` 和 confirmed group design。Stage 3.2 只生成任务记录，不产生重新计算的 DEG 结果。

UI 和 manifest 中必须区分这两条路径，不能把 imported DEG 写成 BioMedPilot 重新计算完成，也不能把 dry-run 写成已完成分析结果。

## 与 result manager 的关系

当前阶段不向 `results/summaries/result_index.json` 写入假的 DEG 结果。后续真实执行器生成可审计输出后，可以登记为正式 result entry，并通过 `source_task_run_id` 追溯到对应 task run。

## 当前限制

- 不执行 DESeq2、edgeR、limma 或其他真实 DEG 算法。
- 不生成 DEG 表。
- 不生成火山图。
- 不执行富集分析。
- 不把 dry-run 输出登记为 completed result。

## 后续计划

下一阶段可以在 task run 层之上接入真实执行器：

1. 将 run 状态从 `queued` 更新为 `running`。
2. 执行真实 DEG。
3. 写入结果表和 QC 日志。
4. 更新 `outputs_manifest.json`。
5. 只在输出真实存在且校验通过后标记 `completed`。
6. 将正式结果登记到 result manager，并保留 `source_task_run_id`。
