# LabTools L6A.2 ROI Export UX Regression Report

日期：2026-05-13

## Stage

LabTools L6A.2 - ROI export user experience regression / 图像 ROI 导出体验与目录选择回归。

## Worktree

- Worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- Branch：`dev/labtools`
- Starting commit：`ee7afca Add LabTools schema index and persistence audit`
- Ending commit：committed as this report's containing commit; see `git log --oneline -5` for the exact hash.

## Scope

- 只优化 LabTools 图像 ROI 导出成功、取消、失败和同目录重复导出的用户反馈与回归测试。
- 保持 L6A / L6A.1 已有 export package schema、文件命名和 no-overwrite 语义。
- 不新增图像算法、不新增自动 ROI、不新增自动细胞计数、不新增 grayscale / ink-value、WB / gel 灰度分析、批量导出、数据库、自动保存、历史记录、正式报告系统、网络、AI、OpenCV、scikit-image 或 ImageJ/Fiji。

## Files Changed

- `app/labtools/ui/image_analysis_widgets.py`
- `tests/ui/test_labtools_image_export_ui.py`
- `docs/labtools_current_handoff.md`
- `docs/labtools_schema_index.md`
- `docs/stage_labtools_l6a2_roi_export_ux_regression_report.md`

## UX Hardening

- ROI 导出成功提示明确显示：
  - 导出成功；
  - 导出目录；
  - JSON manifest；
  - CSV summary；
  - Markdown fragment；
  - ROI overlay PNG；
  - Developer Preview / testing；
  - 人工复核提示。
- 用户取消目录选择时：
  - 不写盘；
  - 不显示成功；
  - 当前分析结果仍保留；
  - 导出按钮保持可用。
- 导出失败时：
  - 显示可读错误；
  - 不显示成功；
  - 不暴露 traceback；
  - 当前分析结果仍保留；
  - 导出按钮保持可用。
- 同一目录连续导出继续依赖 L6A.1 no-overwrite 策略，生成不同文件名并保留第一次导出文件。

## Safety And Semantics

- UI 继续使用 manual ROI / auxiliary analysis / manual-review / semi-quantitative / Developer Preview testing 语义。
- Markdown fragment 和 manifest 仍不被描述为正式报告、临床诊断、自动算法结论、完整 ELN 或 production-grade 输出。
- 普通 UI 成功提示可显示用户选择的导出目录；schema index 明确该路径是本地 UI 反馈，不是公开报告正文。

## Validation

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_labtools_image_export_ui.py -q`：6 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`：154 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：157 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q`：18 passed
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`：passed
- `python3 -m compileall app/labtools`：passed
- `git diff --check`：passed
- `git diff --cached --check`：passed

## Known Limitations

- L6A.2 不改变导出包内容 schema，仅增强 UI 状态和回归覆盖。
- ROI overlay PNG 仍是静态导出图，不是交互式 ROI 编辑器。
- 仍不支持批量导出、自动保存、数据库历史记录或正式报告生成。

## Next Recommended Stage

继续执行 L6E：LabTools user-facing status and placeholder audit，审计所有 LabTools 用户可见状态文案，确保 implemented / draft / manual-review / placeholder 边界一致。

## Git Status After Commit

Clean after commit and metadata amend.
