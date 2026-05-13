# LabTools L6A.1 Image ROI Export Hardening Report

日期：2026-05-13

## 1. Stage

- Stage name：LabTools L6A.1 - Image ROI export schema and UI hardening
- Worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- Branch：`dev/labtools`
- Starting commit：`89b082f Add LabTools image ROI export packages`
- Ending commit：最终交接记录

## 2. Scope

本阶段只硬化 L6A 已实现的 ROI export package 写盘机制：

- 固化 JSON manifest schema。
- 固化导出文件命名和 no-overwrite 策略。
- 强化 output_dir 校验和写盘失败提示。
- 固化 CSV summary header。
- 固化 Markdown fragment 的 manual-review / auxiliary output 语义。
- 增加 UI 导出取消、失败和成功行为测试。

本阶段不新增任何图像算法，也不改变 fluorescence / wound 计算逻辑。

## 3. Files Changed

- `app/labtools/image_analysis/export_package.py`
- `app/labtools/ui/image_analysis_widgets.py`
- `tests/labtools/test_fluorescence_export.py`
- `tests/labtools/test_wound_export.py`
- `tests/labtools/test_roi_export_package_schema.py`
- `tests/ui/test_labtools_image_export_ui.py`
- `docs/labtools_current_handoff.md`
- `docs/stage_labtools_l6a1_image_roi_export_hardening_report.md`

## 4. Implemented Hardening Items

- 固定 schema version：`labtools_roi_export_manifest.v1`。
- 固定 export type：`labtools_image_roi_export_package`。
- 固定 tool slug：
  - `fluorescence_manual_roi`
  - `wound_manual_roi_threshold`
- 固定 analysis mode：
  - `manual_roi_auxiliary_analysis`
  - `manual_roi_threshold_area_estimation`
- Manifest 固定记录：
  - tool label。
  - created_at。
  - app/software channel。
  - algorithm name/version。
  - source image filename/reference/dimensions。
  - output files。
  - parameters。
  - result summary。
  - review_status。
  - safety_note。
  - generated_files_count。
- CSV summary 使用稳定 header，包含 schema version、tool slug、review status、measurement id、ROI id、measurement name、value、unit 和 note。
- Markdown fragment 使用 LabTools manual ROI 辅助分析标题，不包含原图绝对路径，不写成正式结论。
- UI 增加可测试 helper：
  - `has_exportable_result()`。
  - `set_export_result_for_testing()`。
  - `_select_export_directory()`。
  - `_perform_export_to_directory()`。

## 5. Manifest Schema

当前 ROI export manifest schema：

```text
labtools_roi_export_manifest.v1
```

关键字段：

- `schema_version`
- `export_type`
- `tool_slug`
- `tool_label`
- `analysis_mode`
- `created_at`
- `app_channel`
- `software_channel`
- `algorithm`
- `manual_review_required`
- `review_status`
- `semi_quantitative`
- `interpretation_note`
- `safety_note`
- `source_image`
- `parameters`
- `result_summary`
- `result`
- `output_files`
- `generated_files_count`
- `persistence_note`

## 6. File Naming And No-overwrite Strategy

导出 basename：

```text
<tool_slug>_<YYYYMMDDTHHMMSSZ>_<short_token>
```

输出文件：

```text
<basename>_manifest.json
<basename>_summary.csv
<basename>_fragment.md
<basename>_overlay.png
```

如果同名文件已存在，自动追加 `_001`、`_002` 等 suffix。测试覆盖同一目录连续导出不会覆盖第一次导出文件。

## 7. UI Export Behavior

- 没有分析结果时，“导出当前 ROI 结果”按钮保持禁用。
- 有 fluorescence 或 wound 结果后按钮启用。
- 用户取消目录选择时，不写盘，不显示成功。
- 导出成功时显示 manifest / CSV / Markdown / overlay 四类文件路径摘要。
- 导出失败时显示用户可读错误，不暴露 traceback，并保留当前分析结果文本。
- UI 文案继续保持 manual-review / semi-quantitative 辅助输出语义。

## 8. Safety And Semantics Boundaries

- 荧光结果仍为 manual ROI grayscale measurement assistance。
- 划痕结果仍为 manual ROI + user threshold semi-quantitative area estimation。
- Markdown fragment 不包含原图绝对路径，不写正式结论或自动识别证明。
- Manifest 是本地审计文件；如包含 source image reference，不应直接作为公开报告分享。
- 导出包不构成自动图像算法结论、医疗用途解释或正式实验 SOP。

## 9. Explicit Non-goals

- 未新增图像算法。
- 未实现自动 ROI。
- 未实现自动细胞计数。
- 未实现 grayscale / ink-value。
- 未实现 WB / gel 灰度分析。
- 未实现批量导出。
- 未实现数据库、自动保存或历史记录系统。
- 未实现正式报告系统。
- 未实现 reagent recipe center。
- 未新增 qPCR / WB 计算器。
- 未启用网络、AI Gateway、本地模型、Ollama。
- 未引入 OpenCV、scikit-image、ImageJ/Fiji。
- 未修改 Bioinformatics、Meta Analysis、ReleaseBuild、Integration、MainLine。

## 10. Dependency Changes

- 未新增第三方依赖。
- 继续使用 L4B 已接入的 Pillow。

## 11. Persistence And Export Status

- 默认图像结果预览仍不写盘。
- 只有用户选择目录后才写入 ROI export package。
- 不覆盖已有导出文件。
- 不写数据库。
- 不写历史记录。
- 不创建项目级存储。
- 不复制、移动或覆盖原图。

## 12. Image Algorithm Status

- `fluorescence_intensity`：仍为 manual ROI grayscale MVP。
- `wound_healing`：仍为 manual ROI + user threshold area estimation MVP。
- `cell_counting`：仍为 `algorithm_not_available` 占位。
- `densitometry` / 灰度墨值：仍为 `algorithm_not_available` 占位。

## 13. Validation

已运行：

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q
```

结果：通过，`130 passed in 0.49s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

结果：通过，`139 passed in 8.96s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q
```

结果：通过，`18 passed in 2.33s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
```

结果：通过，输出包含 `workspace_entries=3`、`labtools_features=4`。

```bash
python3 -m compileall app/labtools
```

结果：通过。

```bash
git diff --check
```

结果：通过。

提交前还需运行：

- `git diff --cached --check`

## 14. Known Limitations

- Overlay PNG 仍为静态 ROI 框预览，不是交互式复核器。
- 当前不做批量导出。
- 当前不复制原图；导出包依赖用户保留原始图片。
- Manifest schema 是 LabTools internal preview schema，不是正式提交级报告规范。

## 15. Next Recommended Stage

- L6B：本地 reagent recipe draft persistence and safety review。
- 或 L6A.2：导出 schema 文档化、更多 UI 回归测试和目录选择体验微调。

## 16. Git Status After Commit

- 待提交后回填最终状态。
