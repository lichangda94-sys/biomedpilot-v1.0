# LabTools Stage L4B Fluorescence ROI MVP Report

日期：2026-05-13

## 范围

- 当前 worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- 权威总手册：`/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- LabTools handoff：`/Users/changdali/Developer/biomedpilot v1.0/LabTools/docs/labtools_current_handoff.md`
- 本阶段范围：荧光强度手动 ROI 分析 MVP。

## Pillow 依赖接入

- 接入位置：
  - `pyproject.toml`
  - `requirements.txt`
- 依赖声明：`Pillow>=11.0,<13`
- 原因：
  - `pyproject.toml` 是当前项目运行时依赖声明入口。
  - `requirements.txt` 是当前本地安装和打包说明使用的依赖入口。
  - 两个文件此前已共同声明 `PySide6`，因此 Pillow 作为运行时轻量图像读取依赖同步加入这两个现有入口。
- 未新增 OpenCV、scikit-image、ImageJ/Fiji、imageio、napari、cellpose、stardist 等大型依赖。

## 修改文件

- `pyproject.toml`
- `requirements.txt`
- `app/labtools/image_analysis/__init__.py`
- `app/labtools/image_analysis/fluorescence/__init__.py`
- `app/labtools/image_analysis/fluorescence/fluorescence_models.py`
- `app/labtools/image_analysis/fluorescence/fluorescence_analyzer.py`
- `app/labtools/image_analysis/fluorescence/fluorescence_report.py`
- `app/labtools/ui/image_analysis_widgets.py`
- `tests/labtools/test_fluorescence_models.py`
- `tests/labtools/test_fluorescence_analyzer.py`
- `tests/labtools/test_fluorescence_result_export.py`
- `docs/stage_labtools_l4b_fluorescence_roi_mvp_report.md`

## 已实现

- 使用 Pillow 读取单张本地图片，并转换为 grayscale。
- 支持用户手动定义 signal ROI。
- 支持用户手动定义 background ROI。
- ROI 坐标必须在图片边界内。
- ROI width / height 必须大于 0。
- 计算结构化荧光指标：
  - ROI area pixels
  - mean intensity
  - integrated density
  - background mean intensity
  - corrected total fluorescence
  - min intensity
  - max intensity
- 如果 corrected total fluorescence 为负，保留负值并生成 warning。
- 新增结构化模型：
  - `FluorescenceROI`
  - `FluorescenceAnalysisParameters`
  - `FluorescenceAnalysisMetrics`
  - `FluorescenceAnalysisResult`
- 新增审计记录生成：
  - 算法名：`manual_roi_grayscale_fluorescence_v1`
  - 算法版本：`L4B-MVP`
  - 记录手动 ROI、背景校正和输入路径。
- 图像定量 UI 中“荧光强度分析”显示 MVP 可用。
- UI 新增 signal/background ROI 输入、运行按钮、结果摘要、公式、warning 和人工复核提示。
- 结果支持 JSON-compatible dict 导出。
- 不自动写盘。

## 未实现

- 未实现自动细胞识别。
- 未实现自动 ROI 检测。
- 未实现批量分析。
- 未实现划痕面积分析。
- 未实现细胞计数。
- 未实现 WB / 凝胶灰度分析。
- 未实现 ROI 绘制器或 overlay 复核。
- 未实现图像文件复制、上传或项目级持久化。

## 算法公式

- `integrated_density = signal ROI 像素强度总和`
- `mean_intensity = signal ROI 像素平均值`
- `background_mean_intensity = background ROI 像素平均值`
- `corrected_total_fluorescence = integrated_density - roi_area_pixels x background_mean_intensity`

结果必须显示人工复核提示：

```text
请人工复核 ROI、背景区域和图像曝光条件后再用于实验结论。
```

## 测试记录

- `python3 - <<'PY' ... from PIL import Image ... PY`
  - 结果：通过，Pillow import OK
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`
  - 结果：78 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - 结果：135 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q`
  - 结果：18 passed
- `python3 -m app.main --smoke-test`
  - 结果：通过，输出包含 `workspace_entries=3`、`labtools_features=4`
- `python3 -m compileall app/labtools`
  - 结果：通过
- `git diff --check`
  - 结果：通过

## 边界状态

- 是否接入 ImageJ/Fiji：否。
- 是否访问外部网络：否。
- 是否调用 AI Gateway：否。
- 是否自动写盘：否。
- 是否影响 LabTools 计算器：否。
- 是否影响本地配方库：否。
- 是否影响来源草稿：否。
- 是否影响 Bioinformatics：否。
- 是否影响 Meta Analysis：否。
- 是否影响 Shared Vocabulary：否。
- 是否影响 AI Gateway：否。
- 是否影响 MainLine：否。

## 提交状态

- Commit hash：提交完成后以最终报告为准。
- Git status：提交完成后以最终报告为准。
