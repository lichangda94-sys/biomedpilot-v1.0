# LabTools Stage L4C Wound Healing MVP Report

日期：2026-05-13

## 范围

- 当前 worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- 当前分支：`dev/labtools`
- 已读取总开发手册：`/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- 已读取 LabTools handoff：`/Users/changdali/Developer/biomedpilot v1.0/LabTools/docs/labtools_current_handoff.md`
- 当前最近完成阶段：LabTools Stage L4B.1，commit `01e94fb09fb9e3c0c2925eb20a92f8dc07fd271e`
- 本阶段范围：划痕实验 wound healing / scratch assay 面积分析 MVP。

## 修改文件列表

- `app/labtools/image_analysis/__init__.py`
- `app/labtools/image_analysis/wound_healing/__init__.py`
- `app/labtools/image_analysis/wound_healing/wound_models.py`
- `app/labtools/image_analysis/wound_healing/wound_analyzer.py`
- `app/labtools/image_analysis/wound_healing/wound_quality.py`
- `app/labtools/image_analysis/wound_healing/wound_export.py`
- `app/labtools/image_analysis/wound_healing/wound_report.py`
- `app/labtools/ui/image_analysis_widgets.py`
- `tests/labtools/test_wound_models.py`
- `tests/labtools/test_wound_analyzer.py`
- `tests/labtools/test_wound_quality.py`
- `tests/labtools/test_wound_export.py`
- `tests/labtools/test_wound_report.py`
- `docs/labtools_current_handoff.md`
- `docs/stage_labtools_l4c_wound_healing_mvp_report.md`

## 实现内容

- 新增 `wound_healing` 图像分析模块。
- 使用 Pillow 读取单张本地图片并转换为 grayscale。
- 支持用户手动定义矩形分析 ROI。
- 支持用户手动输入 0-255 阈值。
- 支持 bright / dark 两种阈值模式。
- 计算 ROI area、scratch area、scratch fraction、non-scratch area、non-scratch fraction。
- 将 covered / migrated fraction 明确标注为“基于阈值的估算”。
- 新增结构化结果对象、质量提示、审计记录、JSON-compatible dict、CSV rows/text、Markdown 报告片段。
- 图像定量 UI 中“划痕实验面积分析”进入 MVP 可用状态。
- UI 显示图片路径、ROI 输入、阈值输入、亮/暗模式、运行按钮、结果摘要、公式、warning、复核提示和简洁导出预览。

## 未实现内容

- 未实现自动 ROI 检测。
- 未自动识别划痕边界并声称完全准确。
- 未实现多时间点迁移曲线。
- 未实现批量分析。
- 未实现细胞计数。
- 未实现 WB / 凝胶灰度分析。
- 未接入 ImageJ/Fiji。
- 未接入 OpenCV、scikit-image、imageio、napari、cellpose、stardist 等新图像依赖。
- 未访问外部网络。
- 未调用 AI Gateway 或本地模型。
- 未上传图片。
- 未自动写盘保存用户图片或结果。
- 未生成 fake 图像结果。
- 未把阈值估算结果表述为正式实验结论。

## 算法公式

- `roi_area_pixels = ROI width x ROI height`
- `scratch_area_pixels = candidate pixels count`
- `scratch_area_fraction = scratch_area_pixels / roi_area_pixels`
- `non_scratch_area_pixels = roi_area_pixels - scratch_area_pixels`
- `non_scratch_area_fraction = 1 - scratch_area_fraction`

结果必须显示：

```text
该结果为基于用户 ROI 和阈值的划痕区域估算，请人工复核阈值、ROI 和原图质量后再用于实验结论。
```

## 阈值模式说明

- bright 模式：`pixel >= threshold` 视为 scratch candidate。
- dark 模式：`pixel <= threshold` 视为 scratch candidate。
- 阈值范围：0-255。
- 所有计算均在用户手动 ROI 内完成。

## 导出结构

JSON-compatible dict 顶层字段：

- `result_id`
- `task_id`
- `status`
- `image_filename`
- `source_path_summary`
- `image_dimensions`
- `roi`
- `threshold`
- `scratch_mode`
- `metrics`
- `formula`
- `warnings`
- `review_notice`
- `generated_at`

CSV-compatible rows 字段：

- `metric`
- `value`
- `unit`
- `note`

Markdown 报告片段包含：

- 标题
- 图片摘要
- ROI 参数
- 阈值和模式
- 计算公式
- 主要指标表
- warnings
- 人工复核提示

默认只返回字符串或数据结构，不自动保存文件。

## 质量提示规则

- ROI area < 100 pixels：提示 ROI 过小。
- threshold < 5 或 > 250：提示阈值极端。
- scratch_area_pixels == 0：提示 scratch area 为 0。
- scratch_area_fraction > 0.95：提示划痕区域接近 ROI 全部。
- scratch_area_fraction < 0.01：提示图像可能需要人工调整阈值。
- warning 不阻止计算，除非输入非法。

## 测试命令和结果

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools/test_wound_models.py tests/labtools/test_wound_analyzer.py tests/labtools/test_wound_quality.py tests/labtools/test_wound_export.py tests/labtools/test_wound_report.py -q`
  - 结果：18 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`
  - 结果：104 passed
- `python3 - <<'PY' ... from PIL import Image ... PY`
  - 结果：通过，输出 `Pillow import OK <module 'PIL.Image' ...>`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - 结果：135 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q`
  - 结果：18 passed
- `python3 -m app.main --smoke-test`
  - 结果：通过，输出包含 `git_head=01e94fb`、`workspace_entries=3`、`labtools_features=4`
- `python3 -m compileall app/labtools`
  - 结果：通过
- `git diff --check`
  - 结果：通过
- `git diff --cached --check`
  - 结果：通过

## 边界状态

- 是否接入 ImageJ/Fiji：否。
- 是否访问外部网络：否。
- 是否调用 AI Gateway：否。
- 是否自动写盘：否。
- 是否影响 LabTools 计算器：否。
- 是否影响 LabTools 配方：否。
- 是否影响 LabTools 来源草稿：否。
- 是否影响 LabTools 荧光分析：未改变荧光算法；仅共享图像定量 UI 页面。
- 是否影响 Bioinformatics：否。
- 是否影响 Meta：否。
- 是否影响 Vocabulary：否。
- 是否影响 AI Gateway：否。
- 是否影响 MainLine：否。

## 提交状态

- Commit hash：提交完成后由最终交接消息记录；Git commit hash 无法在同一提交内容中预先自包含。
- Git status：提交完成后由最终交接消息记录。
