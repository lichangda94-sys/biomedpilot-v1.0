# LabTools L6A Image ROI Export Package Report

日期：2026-05-13

## 1. Stage

- Stage name：LabTools L6A - image ROI result persistence and export package
- Worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- Branch：`dev/labtools`
- Starting commit：`cadb552 Add LabTools qPCR and WB calculators`
- Ending commit：最终交接记录

## 2. Scope

本阶段只增强已有两个图像 MVP 的可审计导出能力：

- 荧光强度 manual ROI grayscale 分析结果导出包。
- 划痕 / wound healing manual ROI + user threshold 面积估算结果导出包。

导出只在用户明确选择目录后发生。默认 UI 仍展示内存预览，不自动保存、不创建项目目录、不上传、不联网。

## 3. Implemented Features

- 新增 `ImageAnalysisExportPackage` 结构化结果。
- 新增 `export_fluorescence_analysis_package()`：
  - 写入 JSON manifest。
  - 写入 CSV summary。
  - 写入 Markdown 报告片段。
  - 生成 signal/background ROI overlay PNG。
- 新增 `export_wound_healing_analysis_package()`：
  - 写入 JSON manifest。
  - 写入 CSV summary。
  - 写入 Markdown 报告片段。
  - 生成 analysis ROI overlay PNG。
- JSON manifest 记录：
  - schema version。
  - algorithm name/version。
  - manual review required。
  - semi-quantitative 语义。
  - source image filename/path summary/image dimensions。
  - ROI、threshold、scratch_mode、metrics、formula、warnings、review_notice。
  - derived file names。
- UI：
  - 新增“导出当前 ROI 结果”按钮。
  - 结果运行前按钮禁用。
  - 用户选择导出目录后才写盘。
  - 导出完成后展示 manifest、CSV、Markdown 和 overlay 文件路径。

## 4. Explicit Non-goals

- 未新增图像分析算法。
- 未实现自动 ROI 检测。
- 未实现自动细胞计数。
- 未实现 grayscale / ink-value、WB/凝胶灰度或条带分析。
- 未实现 batch analysis。
- 未实现交互式 ROI 绘制器或图像预览器。
- 未实现 LabTools 项目数据库、后台自动持久化、历史记录或正式报告系统。
- 未修改实验计算器、recipe center、experiment templates。
- 未启用网络、AI Gateway、本地模型、ImageJ/Fiji、OpenCV、scikit-image。
- 未修改 Bioinformatics、Meta Analysis、ReleaseBuild、Integration、MainLine。

## 5. Safety And Semantics Boundaries

- 荧光导出结果仍是 manual ROI grayscale measurement assistance。
- 划痕导出结果仍是 manual ROI + user threshold semi-quantitative area estimation。
- 导出文件不构成自动算法结论、临床建议、安全操作建议或实验 SOP。
- ROI overlay 是 derived preview，不覆盖原图。
- Manifest 仅记录 source path summary / filename，不把图片复制到项目结构。
- 所有导出均需要用户确认目录；没有自动写盘行为。

## 6. Files Changed

- `app/labtools/image_analysis/export_package.py`
- `app/labtools/image_analysis/__init__.py`
- `app/labtools/ui/image_analysis_widgets.py`
- `tests/labtools/test_fluorescence_export.py`
- `tests/labtools/test_wound_export.py`
- `tests/labtools/test_labtools_imports.py`
- `docs/labtools_current_handoff.md`
- `docs/stage_labtools_l6a_image_roi_export_package_report.md`

## 7. Validation

已运行：

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q
```

结果：通过，`121 passed in 0.49s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

结果：通过，`135 passed in 9.00s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q
```

结果：通过，`18 passed in 2.34s`。

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

## 8. Dependency Changes

- 未新增第三方依赖。
- 继续使用 L4B 已接入的 Pillow。

## 9. Persistence And Export Status

- 默认图像结果预览仍不写盘。
- L6A 新增用户确认目录后的显式导出包。
- 未新增自动保存、数据库、项目目录写入、CSV/manifest 批量导出或历史记录。

## 10. Image Algorithm Status

- `fluorescence_intensity`：仍为 manual ROI grayscale MVP。
- `wound_healing`：仍为 manual ROI + user threshold area estimation MVP。
- `cell_counting`：仍为 `algorithm_not_available` 占位。
- `densitometry` / 灰度墨值：仍为 `algorithm_not_available` 占位。

## 11. Known Limitations

- ROI overlay 仅为静态 PNG 预览，不提供交互式复核。
- 当前导出单次分析结果，不做批量导出。
- Manifest schema 为 LabTools internal preview，不是正式提交级报告规范。
- 不复制原图；导出包依赖用户保留原始图片。

## 12. Next Recommended Stage

- L6B：本地 reagent recipe draft persistence and safety review。
- 或 L6A.1：ROI export package schema hardening、批量结果命名策略和更完整的 UI 导出测试。

## 13. Git Status After Commit

- 待提交后回填最终状态。
