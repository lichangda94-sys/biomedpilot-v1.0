# LabTools L0.1 Baseline Sync Report

日期：2026-05-13

## 范围

- 当前 worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- 权威总手册：`/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- 本阶段只同步 MainLine 已有 P0 基线修复，恢复 Shell / MainWindow UI 测试。

## 问题原因

LabTools worktree 中缺少 `app.bioinformatics.deg_executor_preflight`，而 `app.bioinformatics.workflow_pages` 已经导入 `run_deg_executor_preflight`。因此 `BioinformaticsWorkspaceWidget` 在导入时降级为 fallback 类，导致 MainWindow 初始化时 `BioinformaticsWorkspaceWidget(on_back=...)` 报错。

## 同步内容

参考 MainLine commit `f295672 fix(mainline): restore bioinformatics workspace initialization`，同步最小必要内容：

- 新增 `app/bioinformatics/deg_executor_preflight.py`
  - 生成 DEG input preflight manifest、warnings、comparisons TSV。
  - 只做输入引用物化和基础校验。
  - 不执行真实 DEG。
  - 不生成 DEG 表、火山图、富集结果或任何 fake 结果。
- 更新 `app/bioinformatics/reports/project_report_builder.py`
  - 读取最新 DEG input preflight manifest。
  - 在报告 section 和草稿中显示 DEG 输入准备状态。
  - 明确标注当前版本尚未执行真实差异分析。

## 未实现

- 未开发新的 Bioinformatics 功能。
- 未修改 Bioinformatics 分析执行器业务逻辑。
- 未接入外部网络。
- 未接入 ImageJ/Fiji。
- 未修改 LabTools 计算器功能。
- 未修改 Meta Analysis、Vocabulary、AI Gateway 或 MainLine。
- 未修改包装发布逻辑。

## 测试记录

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - 结果：135 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`
  - 结果：33 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q`
  - 结果：18 passed
- `python3 -m app.main --smoke-test`
  - 结果：通过，输出包含 `workspace_entries=3`、`labtools_features=4`
- `python3 -m compileall app/labtools`
  - 结果：通过
- `git diff --check`
  - 结果：通过

## 边界影响

- LabTools 计算器功能：未修改。
- Bioinformatics：仅同步 MainLine 既有 preflight 基线缺口和报告读取状态；未执行真实分析，未生成 fake 结果。
- Meta Analysis：未修改。
- Shared Vocabulary：未修改。
- AI Gateway：未修改。
- MainLine：未修改；仅在 LabTools worktree 内同步。
