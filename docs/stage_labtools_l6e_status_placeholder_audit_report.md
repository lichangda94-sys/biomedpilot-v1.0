# LabTools L6E Status Placeholder Audit Report

日期：2026-05-13

## Stage

LabTools L6E - user-facing status and placeholder audit / 用户可见状态与 placeholder 语义审计。

## Worktree

- Worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- Branch：`dev/labtools`
- Starting commit：`d2dff19 Polish LabTools ROI export UX`
- Ending commit：committed as this report's containing commit; see `git log --oneline -5` for the exact hash.

## Scope

- 审计并修正 LabTools 首页、feature status 和关键 UI 页面中的用户可见状态文案。
- 新增 UI 语义回归测试，固定 implemented / draft / manual-review / placeholder 边界。
- 不新增计算公式、图像算法、persistence、导出、网络、AI、OpenCV、scikit-image、ImageJ/Fiji、数据库、自动保存、历史记录、正式报告或完整 ELN。

## Files Changed

- `app/labtools/labtools_home.py`
- `app/labtools/workspace.py`
- `tests/ui/test_labtools_status_semantics.py`
- `docs/labtools_current_handoff.md`
- `docs/labtools_schema_index.md`
- `docs/stage_labtools_l6e_status_placeholder_audit_report.md`

## Audit Results

- 实验计算器：用户可见状态改为“本地辅助”，描述为实验辅助计算草稿，使用前需人工核对。
- 试剂与配方：用户可见状态改为“本地草稿”，描述为本地配方草稿、JSON 草稿持久化和 SOP/SDS 人工核对。
- ROI image analysis：用户可见状态改为 manual-review MVP，继续限定为 fluorescence manual ROI 与 wound manual ROI + threshold。
- ROI export package：UI 成功文本仍为 manual ROI auxiliary analysis / manual-review / semi-quantitative 辅助结果，不是正式报告或临床诊断。
- Recipe draft store/import：UI 继续显示本地草稿、不自动写盘、人工核对、SOP/SDS 边界。
- Experiment record draft JSON：UI 继续显示结构化记录草稿、不自动保存、不生成正式 ELN。
- Image placeholders：cell counting、grayscale / ink-value、WB / gel grayscale、automatic ROI、batch image processing 仍未被描述为已完成能力。

## Explicit Non-Goals

- 不新增功能。
- 不修改图像分析计算逻辑。
- 不修改 recipe 或 experiment draft persistence schema。
- 不新增 WB / gel grayscale quantification、automatic cell counting、automatic ROI、formal report system、full ELN、cloud sync、AI interpretation 或 batch image processing。

## Validation

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_labtools_status_semantics.py -q`：6 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools/test_labtools_imports.py -q`：2 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`：154 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：163 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q`：18 passed
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`：passed
- `python3 -m compileall app/labtools`：passed
- `git diff --check`：passed
- `git diff --cached --check`：pending before commit

## Known Limitations

- L6E audits visible wording and tests current UI surfaces; it does not introduce a global copy registry.
- Schema index remains a developer-facing document and may include technical schema names not shown in normal UI.

## Next Recommended Stage

Continue with L7A：Calculator result copy UX, adding copyable calculator result text without adding formulas, exports, autosave, or history.

## Git Status After Commit

Pending before commit.
