# LabTools Stage L1B Report

日期：2026-05-13

## 范围

- 当前 worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- 权威总手册：`/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- 本阶段范围：实验计算器增强与计算记录基础。

## 已实现

- 新增计算记录基础模型 `CalculationRecord`：
  - `record_id`
  - `calculator_type`
  - `created_at`
  - `inputs`
  - `outputs`
  - `formula`
  - `warnings`
  - `review_notice`
  - 支持导出 JSON-compatible dict。
- 扩展 `CalculationResult`，支持 warnings、结构化记录输入输出，并可生成 `CalculationRecord`。
- 新增细胞接种计算器：
  - 输入当前细胞悬液浓度、目标每孔细胞数、孔数、额外损耗比例。
  - 输出总细胞数、所需细胞悬液体积、建议补足总体积、每孔加样体积、公式和复核提示。
- 新增 qPCR 配液计算器：
  - 支持 master mix 体积模式和比例模式。
  - 输出每个组分单反应用量、总用量、加损耗后的总用量和 nuclease-free water 补足体积。
  - 当组分体积超过单反应总体积时报中文错误。
- 新增溶液配制计算器：
  - 支持质量浓度 + 目标体积。
  - 支持摩尔浓度 + 分子量 + 目标体积。
  - 输出称量质量、溶剂补足体积和单位换算过程。
- 扩展实验计算器 UI 标签页：
  - 浓度换算
  - 稀释计算
  - 溶液配制
  - 细胞接种
  - qPCR 配液
- UI 展示最近一次计算摘要；不做数据库持久化，不自动写盘。

## 未实现

- 未开发试剂与配方检索。
- 未接入外部网络。
- 未接入 ImageJ/Fiji。
- 未开发图像分析算法。
- 未生成 fake 图像分析结果。
- 未做复杂项目系统或数据库持久化。
- 未修改包装发布逻辑。

## 测试记录

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`
  - 结果：33 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q -k 'not main_window'`
  - 结果：15 passed, 3 deselected
- `python3 -m app.main --smoke-test`
  - 结果：通过，输出包含 `workspace_entries=3`、`labtools_features=4`
- `python3 -m compileall app/labtools`
  - 结果：通过
- `git diff --check`
  - 结果：通过

## 已知基线问题

完整运行 `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q` 时，3 个 MainWindow 用例失败。失败原因仍是当前 LabTools worktree 的既有 Bioinformatics UI 导入链依赖缺失的 `app.bioinformatics.deg_executor_preflight`，导致 `BioinformaticsWorkspaceWidget` 降级为 fallback 类并无法按主窗口期望初始化。该问题不属于 LabTools Stage L1B 范围，本阶段未修改 Bioinformatics 业务逻辑。

## 边界影响

- Bioinformatics：未修改业务逻辑。
- Meta Analysis：未修改业务逻辑。
- Shared Vocabulary：未修改。
- AI Gateway：未修改。
- MainLine：未修改；本阶段仅在 LabTools worktree 内开发。
