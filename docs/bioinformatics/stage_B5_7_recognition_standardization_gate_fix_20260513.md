# Stage B5.7 Recognition to Standardization Readiness Gate Fix

## 问题原因

数据识别已经能在文件级结果中识别表达矩阵、原始 count 矩阵、FPKM / normalized expression 矩阵，以及 RNA-seq 综合表达结果表中的多个可用资产。但上层 UI gate 仍混用了“能否进入标准化”和“能否直接做 DEG”的语义。

当表达矩阵存在但分组信息缺失时，DEG 确实不能运行；但这不应阻止用户进入数据准备与标准化阶段。错误文案“未识别到表达矩阵或原始计数矩阵”只应在真正没有表达矩阵类输入时出现。

## 修复的 readiness 字段或 gate 逻辑

- `project_readiness.run_project_readiness()` 明确以表达矩阵类输入计算 `standardization_ready`。
- `overall_status` 不再因为缺少 DEG 分组而退回为不可进入标准化；存在表达矩阵类输入但有 warning 时为 `ready_with_warnings`。
- recognition 页继续按钮 gate 调用 readiness 逻辑，并以 `standardization_ready` 判断是否可继续。
- readiness 页继续按钮 gate 也以 `standardization_ready` 为准，而不是把 DEG 缺失项当作标准化阻断。
- mixed processed expression table 中的 `raw_count_matrix`、`normalized_expression_matrix` 只要 `input_eligible=true`，就纳入标准化 gate；`differential_result_table` 仍不作为表达矩阵输入。

## standardization_ready 与 deg_ready 的新语义

- `standardization_ready=true`：已识别到 `expression_matrix`、`normalized_expression_matrix` 或 `raw_count_matrix`，包括综合表达表中检测出的 count / FPKM 资产。
- `deg_ready=true`：在标准化可用表达矩阵基础上，还需要确认比较分组，并且 case/control 或 comparison design 与表达矩阵样本可用。
- 缺少分组信息时：`standardization_ready=true`，`deg_ready=false`。
- 只有 imported DEG result 时：`standardization_ready=false`，`deg_ready=false`；该结果可用于 imported result 浏览语义，但不作为重新标准化或重新 DEG 的表达矩阵输入。

## UI 文案变化

- recognition 页识别摘要与继续状态统一显示：
  `可以继续进入数据准备与标准化；需在标准化阶段确认分组后才能进行 DEG 分析。`
- readiness 概览在缺少分组但已有表达矩阵时，不再显示“关键输入还不完整”式阻断文案，而显示可继续标准化并提示 DEG 分组要求。
- `未识别到表达矩阵或原始计数矩阵` 只在真正没有表达矩阵、count matrix 或 normalized expression matrix 时显示。

## 测试结果

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`：233 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：149 passed
- `python3 -m app.main --smoke-test`：passed
- `git diff --check`：passed

## 是否建议继续桌面手动测试

建议继续做一次桌面手动测试：导入并识别 `GSE236866_Processed_data_tau_with_inhibitors.xlsx`，确认文件详情、识别摘要、readiness 概览和继续按钮一致显示可进入数据准备与标准化，同时 DEG 仍提示需要在标准化阶段确认分组。
