# LabTools Stage L5A Status Wording And Capability Alignment Report

日期：2026-05-13

## 1. Scope

L5A 是状态校准阶段，不是新功能阶段。本阶段只同步 LabTools 用户可见文案、handoff 和测试断言，使当前能力边界与代码真实状态一致。

当前准确状态：

- 实验计算器：testing-level 可用，已包含浓度/质量换算、C1V1 稀释、溶液配制、细胞接种和 qPCR 配液。
- 试剂与配方：testing-level 可用，已包含本地配方库、用户配方草稿和手动来源草稿。
- 图像定量：testing-level 可用范围仅限荧光 manual ROI grayscale 指标和 scratch/wound manual ROI + user threshold 面积估算。
- 细胞计数、灰度/墨值、实验模板：仍为占位或开发中，不生成真实定量结果。

## 2. Changes

- 更新 `labtools_features()` 中“图像定量”的描述，移除整体性的“算法开发中”表述。
- 更新 LabTools 首页“图像定量”入口描述，突出当前两个 MVP，而不是只说任务草稿框架。
- 更新图像分析页任务卡片：
  - 荧光强度分析显示 manual ROI grayscale 指标 MVP，提示人工复核。
  - 划痕实验面积分析显示 manual ROI + user threshold 面积估算 MVP，提示 semi-quantitative。
  - 细胞计数和灰度/墨值显示 `algorithm_not_available` 占位。
- 更新 `IMAGE_REVIEW_NOTICE`，避免继续暗示图像页只有框架而没有任何可用 MVP。
- 更新 `docs/labtools_current_handoff.md`，固定 L4C commit，并把当前阶段改为 L5A 状态校准。
- 更新 `reports/LabTools_handoff_report_20260513.md`，把已发现的 wording 问题标记为 L5A 已处理，并重排后续路线。

## 3. Boundary

本阶段没有新增或启用：

- 新图像算法。
- 自动 ROI、自动细胞计数、灰度/墨值分析。
- 图像预览、overlay、批量分析或结果持久化。
- 外部网络、网页抓取、AI Gateway、本地模型。
- ImageJ/Fiji、OpenCV、scikit-image、imageio、napari、cellpose、stardist。
- 自动写盘保存用户图片、CSV、JSON、Markdown 或报告文件。
- 跨 Bioinformatics / Meta / Vocabulary / AI Gateway 的业务逻辑改动。

## 4. Tests

新增或更新测试覆盖：

- LabTools feature registry 中“图像定量”必须同时提到 fluorescence manual ROI grayscale 和 scratch/wound manual ROI + threshold MVP。
- LabTools feature registry 中“图像定量”不得继续使用整体性的“算法开发中”或 `algorithm in development` 表述。
- LabTools image workspace 必须显示两个 MVP 状态和两个 `algorithm_not_available` 占位状态。
- Image review notice 必须说明当前两个 manual-review MVP 和未启用的自动/占位算法边界。

本阶段实际运行：

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q
```

结果：通过，`104 passed in 0.45s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

结果：通过，`135 passed in 9.32s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q
```

结果：通过，`18 passed in 2.40s`。

```bash
python3 -m app.main --smoke-test
```

结果：通过，输出包含 `workspace_entries=3` 和 `labtools_features=4`。

```bash
python3 -m compileall app/labtools
```

结果：通过。

## 5. Next

建议后续路线：

1. L5B：实验计算器硬化与缺口补齐，优先补现有计算器验证和 UI 一致性，再评估 WB/SDS-PAGE loading calculator。
2. L6A：图像 ROI 结果持久化、CSV/manifest/overlay preview 导出，继续保持 manual-review / semi-quantitative。
3. L6B：常用 reagent recipe draft center 的本地持久化和安全边界硬化，复用现有配方库、用户草稿和手动来源草稿。
4. L6C：轻量实验模板和记录草稿，不做完整 ELN、权限、签名或合规审计。
