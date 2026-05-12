# Bioinformatics Group Comparison Design v1

## 功能目标

分组与比较设计页用于把识别阶段的“推断分组”转成用户确认的实验设计。识别模块可以从 `A1_count`、`A2_count`、`B1_count` 等列名推断 A/B 组，但不能知道 A 是 PBS、B 是 PFF，也不能自动决定对照组或需要重新计算的比较关系。

本阶段只保存设计 manifest，不运行真实 DEG 算法。

## 为什么需要用户确认

- 推断分组只来自样本列命名规则，不等于实验设计。
- imported DEG comparison 是导入文件中已有结果，只能作为参考。
- 重新差异表达分析需要明确 case/control 和样本归属。
- 如果只有 FPKM/TPM，没有 count matrix，不应默认进入 DESeq2/edgeR 式重新差异分析。

## 数据来源

页面只读取当前项目的当前输入：

- `recognized_data/current.json`
- `manifests/standardized_assets_registry.json`
- 当前 recognition run 的 `recognition_report.json` / `recognized_files.json`，仅在标准化资产信息不足时作为补充

页面不扫描历史 recognition runs，也不会把历史记录自动作为当前分组设计来源。

## 页面结构

- 当前数据来源摘要
- 样本分组确认
- 组名语义映射
- 比较设计
- 已有导入差异结果
- 保存与后续任务状态

## Sample Group Schema

保存路径：

`manifests/group_comparison_design.json`

核心字段：

```json
{
  "inferred_group_id": "A",
  "user_group_name": "PBS",
  "group_role": "control",
  "sample_ids": ["A1", "A2", "A3"],
  "source_columns": ["A1_count", "A2_count", "A3_count"],
  "note": ""
}
```

UI 主界面显示样本 ID，例如 `A1`，不显示 `A1_count` 作为样本名。`source_columns` 保留在技术字段中。

## Comparison Schema

```json
{
  "comparison_name": "PFF_vs_PBS",
  "case_group": "PFF",
  "control_group": "PBS",
  "case_inferred_group_id": "B",
  "control_inferred_group_id": "A",
  "status": "confirmed",
  "source": "user_confirmed"
}
```

校验规则：

- `comparison_name` 非空且唯一。
- `case_group` 和 `control_group` 必须存在。
- `case_group != control_group`。
- 两组样本数至少 2，建议 3 个或以上。
- 不能在全部 group role 为 `unknown` 时把重新 DEG 标记为 ready。

## Imported DEG 与 Confirmed Design 的区别

imported DEG comparisons 来自导入表格中的已有差异分析结果，例如 `PFFvsPBS_log2FoldChange`、`PFFvsPBS_pvalue`、`PFFvsPBS_padj`。

它们可以直接用于：

- DEG 浏览
- 阈值筛选
- 火山图输入
- 富集分析输入

但它们不是 BioMedPilot 重新计算出的结果，也不会自动成为 confirmed design。用户需要在分组设计页确认组名、组角色和比较关系后，系统才会把“重新差异表达分析”从“需要确认分组”更新为可配置/可运行。

## 与后续模块的关系

- 标准化页面显示分组设计状态：未确认 / 已确认。
- 分析任务中心读取 `group_comparison_design.json`，确认后将 count matrix 的重新 DEG capability 标记为 available。
- 结果浏览继续独立读取 imported DEG assets，不被 confirmed design 覆盖。
- 识别详情和下一步建议在未确认分组时提示：重新差异分析前请先确认分组。

## 当前限制

- 仅保存设计，不执行真实 DESeq2/edgeR/limma。
- imported DEG comparison 名称只作为参考，不自动映射到用户组名。
- 批次、配对设计、多因素设计尚未建模。
- FPKM/TPM 只推荐用于表达展示、热图、相关性和表达浏览。

## 后续计划

- 增加批次和配对设计字段。
- 支持从 sample metadata 自动预填用户组名。
- 支持从 comparison config 自动生成 comparison 草稿。
- 将 confirmed design 接入真实 DEG runner 的参数准备阶段。
