# Bioinformatics Project Report Draft v1

## 功能目标

Stage 3.4 为 BioMedPilot / 医研智析生信流程增加项目报告草稿自动组装能力。报告草稿从项目中已经登记的 manifest 与结果索引生成用户可读摘要，帮助用户了解哪些内容可以纳入后续正式报告。

本阶段只做报告组装，不执行真实 DEG、富集分析、绘图或正式 biological normalization。

## 数据来源

报告草稿读取以下项目级文件：

- `recognized_data/current.json`：当前识别批次。
- `manifests/standardized_assets_registry.json`：标准化资产注册表。
- `manifests/standardized_asset_selection.json`：默认资产选择。
- `manifests/group_comparison_design.json`：已确认的分组与比较设计。
- `results/summaries/result_index.json`：导入结果与分析任务记录索引。
- `analysis_runs/`：分析任务 run 记录。

如果某个来源不存在，报告草稿会显示对应章节不可用，而不是自动扫描历史记录替代当前输入。

## 报告结构

默认输出：

- `reports/project_report_draft.md`
- `reports/project_analysis_report.md`
- `reports/project_report_manifest.json`

草稿章节包括：

- 项目概览
- 数据识别摘要
- 标准化资产与默认选择
- 分组与比较设计
- 导入 DEG 结果
- 分析任务记录
- 已完成分析结果
- 限制与待确认事项

## 结果边界

报告草稿会区分三类内容：

- `imported_deg_result`：导入表格中的已有差异分析结果，可作为报告素材，但来源必须标注为导入文件。
- `analysis_task_run`：分析任务记录，可能是 `skipped_dry_run`，不代表真实分析完成。
- `completed_result`：未来真实执行器产生的已完成结果。

`skipped_dry_run` 不会被写成 completed result，也不会生成假的 DEG 表、火山图或富集结果。

## 与报告 Manifest 的关系

`reports/project_report_manifest.json` 保留 Stage 3.3 的 section 索引，并新增草稿相关字段：

- `draft_path`
- `draft_sections`
- `result_items`
- `warning_count`
- `warnings`

下游项目报告页可以用 manifest 判断哪些内容可纳入报告，哪些只是尚未完成的任务记录。

## 当前限制

- 不导出正式 PDF / DOCX / HTML。
- 不复制完整表达矩阵到报告。
- 不生成真实 DEG、富集结果或图表。
- 不把 imported DEG 结果描述为 BioMedPilot 重新计算结果。

## 后续计划

- Stage 3.5：真实 DEG 执行器接入前审计。
- Stage 3.6：DEG 执行器最小实现或外部 R 脚本桥接。
- 后续报告版本可纳入真实执行结果、图表、富集结果和完整方法学说明。
