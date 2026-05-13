# LabTools L5C qPCR And WB Loading Calculator Report

日期：2026-05-13

## 1. Stage

- Stage name：LabTools L5C - qPCR / WB-SDS-PAGE calculator structured v1
- Worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- Branch：`dev/labtools`
- Starting commit：`d2a97e3 Add LabTools experiment calculator center`
- Ending commit：最终交接记录

## 2. Scope

本阶段在 L5B 实验计算器中心基础上补齐两个本地 wet-lab 计算器：

- qPCR 配液结构化 v1。
- Western blot / SDS-PAGE 上样体积计算 v1。

本阶段只做公式计算和 UI 展示，不做历史记录、持久化、CSV/manifest 导出、recipe 修改、实验模板、网络、AI、ImageJ/Fiji、OpenCV 或 scikit-image。

## 3. Implemented Features

- `QpcrMixInput` / `QpcrMixResult` / `calculate_qpcr_mix_v1()`：
  - 支持 master mix 体积模式和比例模式。
  - 输出每反应用量、总用量和 overage 后总用量。
  - 对组分体积超过单反应总体积、master mix 比例超过 100%、负 overage 返回 invalid。
- `WesternBlotLoadingInput` / `WesternBlotLoadingResult` / `calculate_western_blot_loading_v1()`：
  - 支持 mg/mL 与 µg/µL 蛋白浓度单位。
  - 根据目标蛋白量、终上样体积和 loading buffer 倍数计算样品、buffer、水体积。
  - 当样品 + buffer 超过终体积时返回 invalid。
- UI：
  - qPCR 配液 tab 切换到结构化 v1 结果。
  - 新增 `WB 上样` tab。
  - 页面明确 WB/SDS-PAGE 上样计算不做 WB/凝胶灰度或条带分析。
- 单位：
  - 新增 `µg/µL` 与 `ug/uL` 等蛋白浓度别名。

## 4. Non-goals And Boundaries

- 未实现 WB / 凝胶灰度分析。
- 未实现条带检测、背景扣除、归一化或图像解释。
- 未改变 fluorescence manual ROI 和 wound threshold MVP。
- 未实现自动细胞计数、grayscale/ink-value 或 experiment templates。
- 未保存计算结果，未写 CSV/manifest，未创建项目文件。
- 未新增第三方依赖，未启用网络、AI、ImageJ/Fiji、OpenCV、scikit-image。
- 未修改 Bioinformatics、Meta、ReleaseBuild、Integration、MainLine。

## 5. Safety Semantics

所有 qPCR 和 WB/SDS-PAGE 输出均为实验辅助计算草稿。使用前需人工核对试剂说明书、实验 SOP、样品兼容性、体系体积、重复数、对照设置和移液可行性。输出不构成临床、诊断或安全操作建议。

## 6. Validation

已运行：

```bash
python3 -m pytest tests/labtools -q
```

结果：通过，`119 passed in 0.47s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

结果：通过，`135 passed in 9.02s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q
```

结果：通过，`18 passed in 2.36s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
```

结果：通过，输出包含 `workspace_entries=3` 和 `labtools_features=4`。

```bash
python3 -m compileall app/labtools
```

结果：通过。

```bash
git diff --check
```

结果：通过。

## 7. Known Limitations

- qPCR calculator 不自动设计 primer、plate layout 或对照体系。
- WB/SDS-PAGE calculator 不处理蛋白活性、样品变性/还原条件、抗体条件或条带定量。
- 不做历史记录、批量计算、导出或项目级保存。

## 8. Next Recommended Stage

- L6A：图像 ROI 结果持久化、CSV/manifest/overlay preview 导出，保持 manual-review / semi-quantitative。
- L6B：本地 reagent recipe draft center 持久化和安全边界硬化。
