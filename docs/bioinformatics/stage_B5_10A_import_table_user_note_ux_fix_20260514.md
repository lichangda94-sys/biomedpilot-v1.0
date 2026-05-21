# Stage B5.10A - Import Table and User Note UX Fix

## 问题原因

B5.6 为避免多文件本地导入在识别 handoff 中丢失文件，将一次本地选择登记为一个导入批次，并在待处理数据集表格中用一行“本地导入批次：N 个文件”表示。该实现保留了完整 `source_files`，但主表格缺少文件级可见性，用户仍需要进入详情才能确认每个文件。

同时，多文件批次的系统摘要“包含 <第一个文件名> 等 N 个文件”被作为默认备注显示在“备注”列和用户备注框中，造成系统摘要与用户手写备注语义混淆。

## 修复内容

- 待处理数据集表格现在将多文件本地导入展开为文件级行。
- 每个文件行显示独立文件名、数据状态、可用内容、需要补充、用户备注和“查看详情”入口。
- 每个文件行仍保留同一导入批次的完整 `source_files`，进入数据识别时不会退化为单文件 handoff。
- 表格附近新增只读“本地导入批次摘要”，显示文件总数、保存方式、来源状态和包含文件概览。
- 系统摘要只出现在批次摘要或详情摘要中，不再写入用户备注。
- “查看详情”优先显示当前文件，并附带批次完整文件列表、保存方式和来源状态。
- 详情摘要显示区加高，用户备注框缩小。
- 用户备注默认空白，仅显示 placeholder：“可记录筛选理由、疑问或后续处理计划，备注只作为笔记保存”。

## 数据结构与 Handoff

- `DatasetListEntry` 新增 `focused_source_file` 和 `batch_summary`，用于区分文件级 UI 行和批次级系统摘要。
- 多文件本地导入的文件级行使用唯一 UI key，例如 `local:<acquisition_id>:file:<index>`。
- 文件级行的 `source_files` 仍保存完整批次文件列表。
- 保存 `pending_recognition_selection.json` 时按 acquisition 去重；即使用户只勾选一个文件行，也会传递完整批次 `source_files`。
- `display_name` 只作为 UI/manifest 显示字段，不替代真实 `source_files`。

## 测试覆盖

已更新 UI 回归测试，覆盖：

- 多文件导入后表格显示 4 行。
- 每行文件名正确，主表格不暴露 raw absolute path。
- 批次摘要仍可见，并显示“包含 GSE6004_family.soft 等 4 个文件”。
- 用户备注默认空白，系统摘要不写入备注。
- 用户手工输入备注可保存到 `manifests/user_dataset_notes.json`。
- 查看详情显示对应文件信息和完整批次文件列表。
- 进入数据识别时 `pending_recognition_selection.json` 仍传递 4 个 `source_files`。

## 验证结果

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`：242 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：154 passed
- `python3 -m app.main --smoke-test`：通过

## 已知限制

- 本阶段仅修复导入表格和备注 UX，不改变数据识别算法。
- 多文件本地导入仍作为一个 acquisition 批次进入识别；文件级行用于 UI 可见性和详情查看。
- 不运行真实 DEG executor，不修改 DEG preflight、imported DEG、报告 builder 语义。

## 后续建议

继续按 B5.11 桌面手动测试清单验证“本地多文件导入 -> 数据识别 -> 标准化确认 -> readiness -> 报告草稿”主链路，重点观察文件级表格、备注保存、批次 handoff 和报告 path 脱敏。
