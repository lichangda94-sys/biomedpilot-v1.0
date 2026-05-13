# LabTools Stage L0 + L1A Report

日期：2026-05-13

## 范围

- 当前 worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- 权威总手册：`/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- 本阶段以 LabTools 模块骨架、统一 Shell 最小入口、实验计算器 MVP 为范围。
- LabTools worktree 内缺少 `docs/handoff/Global_Development_Manual.md` 本地 handoff 手册副本；本阶段按用户授权不作为阻塞项。建议后续由 MainLine / ProjectControl 统一同步策略处理。

## 已实现

- 新增 `app/labtools` 模块边界与 `LabToolsWorkspaceWidget`。
- 新增 LabTools 首页四个入口：
  - 实验计算器：测试级可用。
  - 试剂与配方：开发中。
  - 图像定量：开发中。
  - 实验模板：开发中。
- 实验计算器 MVP：
  - 浓度单位换算。
  - 由质量、体积、分子量计算摩尔浓度。
  - 由摩尔浓度、体积、分子量计算称量质量。
  - C1V1 = C2V2 稀释计算。
- 支持单位：
  - 质量：g, mg, µg, ng
  - 体积：L, mL, µL
  - 物质的量浓度：M, mM, µM, nM
  - 质量浓度：mg/mL, µg/mL, ng/µL
- 结果显示输入摘要、计算公式、结果和“请人工复核计算结果后再用于实验”提示。
- 非法输入、空输入、负数、零体积、缺失分子量、未知单位均返回中文友好错误。
- 统一 Shell 最小接入：
  - Dashboard 模型加入 LabTools features。
  - 模块选择页加入 LabTools 入口卡片。
  - 侧边栏加入“实验工具”入口。
  - 主窗口加入 LabTools 工作台页面。
  - app smoke-test 输出 `workspace_entries=3` 和 `labtools_features=4`。

## 未实现

- 试剂与配方未实现，仅显示“开发中”。
- 图像定量未实现；未接入 ImageJ/Fiji，未生成任何图像分析结果。
- 实验模板未实现，仅显示“开发中”。
- 未接入外部网络。
- 未修改包装发布逻辑。

## 测试记录

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`
  - 结果：17 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q -k 'not main_window'`
  - 结果：15 passed, 3 deselected
- `python3 -m app.main --smoke-test`
  - 结果：通过，输出包含 `workspace_entries=3`、`labtools_features=4`
- `git diff --check`
  - 结果：通过

## 已知基线问题

完整运行 `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q` 时，3 个 MainWindow 用例失败。失败原因是当前 LabTools worktree 的既有 Bioinformatics UI 导入链依赖缺失的 `app.bioinformatics.deg_executor_preflight`，导致 `BioinformaticsWorkspaceWidget` 降级为 fallback 类并无法按主窗口期望初始化。该问题不属于 LabTools Stage L0 + L1A 范围，本阶段未修改 Bioinformatics 业务逻辑。

## 边界影响

- Bioinformatics：未修改业务逻辑。
- Meta Analysis：未修改业务逻辑。
- Shared Vocabulary：未修改。
- AI Gateway：未修改。
- MainLine：未修改；本阶段仅在 LabTools worktree 内开发。
