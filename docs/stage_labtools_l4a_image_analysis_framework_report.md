# LabTools Stage L4A Image Analysis Framework Report

日期：2026-05-13

## 范围

- 当前 worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- 权威总手册：`/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- 本阶段范围：图像分析基础框架。

## 已实现

- 新增 `app/labtools/image_analysis` 基础模块：
  - `image_models.py`
  - `image_io.py`
  - `analysis_task.py`
  - `roi_models.py`
  - `result_models.py`
  - `audit_models.py`
- 新增数据模型：
  - `LabImageRecord`
  - `ImageAnalysisTask`
  - `ROIRecord`
  - `ImageAnalysisResult`
  - `ImageAnalysisAuditRecord`
- 支持本地图片路径校验：
  - 检查空路径、路径存在性、文件类型、文件大小提示。
  - 支持 `.png`、`.jpg`、`.jpeg`、`.tif`、`.tiff`、`.bmp`、`.gif`。
  - 仅引用本地路径，不复制、不上传、不联网。
- 支持创建图像分析任务草稿：
  - `wound_healing`
  - `cell_counting`
  - `fluorescence_intensity`
  - `densitometry`
- 默认任务状态为 `draft` 或 `pending_configuration`。
- 默认结果状态为 `algorithm_not_available`，不包含定量 metrics。
- LabTools 首页“图像定量”入口改为可进入。
- 新增图像定量 UI：
  - 图片选择 / 路径输入区
  - 图片记录摘要
  - 四类分析任务卡片
  - 任务草稿区
  - 参数、ROI、结果和人工复核提示占位结构

## 安全与边界

- 未实现划痕面积自动计算。
- 未实现细胞计数算法。
- 未实现荧光强度计算。
- 未实现 WB/凝胶灰度分析。
- 未生成 fake 图像分析结果。
- 未接入 ImageJ/Fiji。
- 未调用 OpenCV、scikit-image 或其他新增大型图像依赖。
- 未上传图片。
- 未访问外部网络。
- 未调用 AI Gateway 或本地模型。
- 未自动写盘或创建复杂项目系统。
- 未把图片路径传给 Bioinformatics、Meta 或其他模块。

## 未实现

- 未实现任何真实图像定量算法。
- 未实现 ROI 绘制器或图像预览器。
- 未实现项目级图片管理。
- 未实现图像文件复制、导入目录或持久化数据库。
- 未实现 ImageJ/Fiji/OpenCV/scikit-image 接入。

## 测试记录

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`
  - 结果：68 passed
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

## 边界影响

- 实验计算器：不修改核心计算逻辑。
- 本地配方库和来源草稿：不修改业务逻辑。
- Bioinformatics：不修改业务逻辑。
- Meta Analysis：不修改业务逻辑。
- Shared Vocabulary：不修改业务逻辑。
- AI Gateway：不修改业务逻辑。
- MainLine：不修改；本阶段仅在 LabTools worktree 内开发。
