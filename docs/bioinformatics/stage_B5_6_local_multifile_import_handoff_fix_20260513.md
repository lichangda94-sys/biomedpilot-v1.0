# Stage B5.6 Local Multi-file Import Batch Display and Recognition Handoff Fix

## 问题原因

本地数据导入登记层原本会保存多个 `registered_files`、`copied_files` 或 `referenced_paths`，数据识别路径也会从登记记录中读取这些列表。但数据选择 UI 在生成本地导入显示名时，只取列表中的第一个文件名作为 `source_label` / `display_name`。因此用户一次选择 4 个文件后，待处理数据集表格只显示第一个文件名，容易误判为只导入了一个文件。

同时，进入数据识别前的 pending selection 只记录数据集 key 和 acquisition id，没有把可审计的完整文件列表写入交接清单。识别阶段当前通过 acquisition id 仍可回读列表，但 handoff 语义不够清楚。

## 修复的数据结构

- `AcquisitionSummary` 新增 `source_files`，并在 acquisition record 与 acquisition handoff 中持久化原始选择文件列表。
- 本地导入 UI 汇总对象保留 `display_name`、`source_files`、`copied_files` 和 `referenced_paths`，不再把显示名当作真实文件列表。
- 待识别 pending selection 新增 `selected_sources`，包含 `display_name`、`source_files` 和 `source_file_count`。
- recognition 路径解析改为按保存策略选择真实输入：
  - `copy` 使用 `copied_files`，缺失时回退到声明的 `source_files`。
  - `reference` 使用 `referenced_paths`，不复制文件。
  - 其他情况按 copied / referenced / declared source files 顺序回退。

## UI 显示变化

- 多文件本地导入在待处理数据集表格中显示为 `本地导入批次：N 个文件`。
- `可用内容` 显示为 `待识别：N 个文件`。
- 默认备注显示为 `包含 <第一个文件名> 等 N 个文件`。
- 主表格不再把第一个文件名呈现为唯一数据集信息，也不在可见单元格暴露 raw absolute path。
- 单文件导入仍显示原文件名。
- “查看导入详情”显示文件总数、文件来源状态、保存方式，以及完整文件名/路径列表。

## 识别 handoff 确认

点击“进入数据识别”后，pending recognition selection 会写入完整导入批次信息。识别页根据 acquisition id 读取完整真实文件列表，并把 4 个文件全部传给 `run_project_recognition_for_paths()`。

新增 UI 回归测试已验证：4 文件 reference 导入不会复制到项目 raw_data，pending handoff 保留 4 个 `source_files`，识别报告的 `selected_input_count` 为 4，`selected_inputs` 与原始 4 个文件一致。

## 测试结果

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`：231 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：148 passed
- `python3 -m app.main --smoke-test`：passed
- `git diff --check`：passed

## 是否建议继续桌面手动测试

建议继续做一次桌面手动测试：在“本地数据导入”选择 4 个真实文件，确认待处理数据集主表、查看导入详情、进入数据识别后的待识别数据源和识别 summary 都显示并处理完整文件列表。
