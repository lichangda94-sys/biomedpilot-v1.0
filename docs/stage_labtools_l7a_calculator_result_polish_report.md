# LabTools L7A Calculator Result Copy UX Report

日期：2026-05-13

## Stage

LabTools L7A - Calculator result copy UX / 实验计算器结果展示与复制体验。

## Worktree

- Worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- Branch：`dev/labtools`
- Starting commit：`ead51bb Audit LabTools user-facing status semantics`
- Ending commit：committed as this report's containing commit; see `git log --oneline -5` for the exact hash.

## Scope

- 为 LabTools 实验计算器结果增加可复制文本和“复制结果”按钮。
- 仅复用已有公式和已有计算结果，不新增计算公式、导出、自动保存、历史记录、CSV、manifest、网络或 AI。

## Files Changed

- `app/labtools/calculators/__init__.py`
- `app/labtools/calculators/experiment_calculator_center.py`
- `app/labtools/ui/calculator_widgets.py`
- `tests/labtools/test_experiment_calculator_center.py`
- `tests/ui/test_labtools_calculator_copy_ui.py`
- `docs/labtools_current_handoff.md`
- `docs/stage_labtools_l7a_calculator_result_polish_report.md`

## Implemented

- 新增三个用户可复制 formatter：
  - `format_dilution_copy_text()`
  - `format_mass_molarity_copy_text()`
  - `format_cell_seeding_copy_text()`
- copyable text 包含：
  - 工具名称；
  - 输入摘要；
  - 计算结果；
  - 单位；
  - 人工核对提示；
  - “实验辅助计算草稿，不替代实验 SOP”语义。
- `ResultPanel` 统一管理 copyable text：
  - 初始无结果时复制按钮禁用；
  - 成功计算后复制按钮启用；
  - invalid 输入或异常提示时复制按钮禁用；
  - 点击复制写入 clipboard，并显示“已复制计算结果，请使用前人工核对”。
- qPCR、WB、传统浓度/溶液配制等既有 calculator 结果区也获得相同复制按钮；无效结果不启用复制。

## Explicit Non-Goals

- 不新增公式。
- 不新增导出。
- 不自动保存。
- 不写 CSV / manifest。
- 不创建项目文件夹。
- 不写历史记录。
- 不联网，不调用 AI。
- 不把计算结果描述为正式 SOP、临床诊断或 production-grade 输出。

## Validation

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools/test_experiment_calculator_center.py -q`：13 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_labtools_calculator_copy_ui.py -q`：5 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`：158 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：168 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q`：18 passed
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`：passed
- `python3 -m compileall app/labtools`：passed
- `git diff --check`：passed
- `git diff --cached --check`：pending before commit

## Known Limitations

- L7A does not add clipboard history or persistence.
- Copy text is intentionally plain text for local clipboard use, not a formal report format.
- Tests mock clipboard behavior and do not depend on the host clipboard.

## Next Recommended Stage

Continue with L7B：Recipe template safety polish, focusing on local recipe draft safety wording, import conflict transparency, and manual review reminders.

## Git Status After Commit

Pending before commit.
