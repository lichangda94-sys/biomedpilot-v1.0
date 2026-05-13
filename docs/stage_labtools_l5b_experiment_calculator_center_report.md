# LabTools L5B Experiment Calculator Center v1 Report

日期：2026-05-13

## 1. Stage

- Stage name：LabTools L5B - Experiment Calculator Center v1 / 实验计算器中心 v1
- Worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- Branch：`dev/labtools`
- Starting commit：`32cb27c docs(labtools): align status wording`
- Ending commit：最终交接记录

## 2. Scope

本阶段实现纯本地、低风险、可测试的实验计算器中心 v1。范围限定为三个 wet-lab 常用辅助计算：

- 溶液稀释 C1V1=C2V2。
- 摩尔浓度 / 称量质量 / 体积换算。
- 细胞接种密度计算。

本阶段没有开发图像算法、自动细胞计数、实验模板、recipe 持久化、历史记录、CSV/manifest 导出、网络请求、AI Gateway、本地模型、ImageJ/Fiji、OpenCV 或 scikit-image。

## 3. Files Changed

- `app/labtools/calculators/experiment_calculator_center.py`
- `app/labtools/calculators/unit_conversion.py`
- `app/labtools/calculators/__init__.py`
- `app/labtools/ui/calculator_widgets.py`
- `tests/labtools/test_experiment_calculator_center.py`
- `tests/labtools/test_unit_conversion.py`
- `tests/labtools/test_labtools_imports.py`
- `docs/labtools_current_handoff.md`
- `docs/stage_labtools_l5b_experiment_calculator_center_report.md`

## 4. Implemented Features

- 新增 Qt-free 结构化服务层，使用 dataclass 输入/输出，不依赖网络、不依赖 pandas/numpy、不新增第三方依赖。
- `calculate_dilution_v1()`：
  - 支持 M、mM、uM/µM、nM 和 mg/mL、ug/µg/mL、ng/mL 的同维度稀释。
  - 支持 L、mL、uL/µL。
  - 返回 stock volume、solvent volume、final volume、dilution factor、summary、warnings、errors。
  - 不混合摩尔浓度和质量浓度，避免在未提供分子量时误导。
- `calculate_mass_molarity_v1()`：
  - 根据 MW、目标摩尔浓度和终体积估算称量质量。
  - 支持输出 g、mg、ug/µg、ng。
  - summary 明确提示试剂纯度、盐型/水合物、有效含量和 SOP 需人工核对。
- `calculate_cell_seeding_v1()`：
  - 支持 cells/mL 和 cells/uL/µL。
  - 根据当前细胞浓度、目标每孔细胞数、孔数、每孔体积和 overage 估算细胞悬液体积、培养基体积、总终体积和总细胞需求量。
  - 当细胞悬液浓度不足以在目标终体积内达到目标接种密度时返回 invalid。
- UI 更新：
  - LabTools 计算器页显示“实验计算器中心”。
  - 增加本地辅助计算、人工核对、不替代实验 SOP 的全局提示。
  - 三个目标计算器接入结构化 v1 结果；输入错误时显示清晰错误，不输出误导性数值。

## 5. Explicit Non-goals

- 不做图像算法、自动 ROI、自动细胞计数、fluorescence 自动分析、grayscale / ink-value 算法。
- 不做实验模板系统。
- 不做 recipe 持久化或新 recipe workflow。
- 不做历史记录、CSV、JSON、manifest、报告或项目文件夹写入。
- 不做网络请求、AI Gateway、本地模型、Ollama。
- 不引入 ImageJ/Fiji、OpenCV、scikit-image。
- 不修改 Bioinformatics、Meta Analysis、ReleaseBuild、Integration、MainLine 业务逻辑。
- 不修改桌面 app、dist 或 release bundle。

## 6. Safety And Semantics

- 所有结果均为实验辅助计算草稿。
- UI 和 result summary 均保留人工核对提示。
- 输出不构成临床、诊断或安全操作建议。
- 结果不替代实验 SOP、试剂说明书、细胞活率判断、计数误差评估或实验设计复核。

## 7. Validation

已运行：

```bash
python3 -m pytest tests/labtools -q
```

结果：通过，`113 passed in 0.45s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

结果：通过，`135 passed in 9.50s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q
```

结果：通过，`18 passed in 2.58s`。

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

## 8. Dependency Changes

- 未新增第三方依赖。
- 未启用网络、AI、ImageJ/Fiji、OpenCV、scikit-image、pandas 或 numpy。

## 9. Persistence And Export Status

- 不自动保存计算结果。
- 不写 CSV、JSON、manifest、报告或项目目录。
- 不新增计算历史记录。
- 仅在 UI 中显示本次计算结果；结构化 result 可供测试读取。

## 10. Image Algorithm Status

L5B 未修改图像算法能力边界。

- 已可用 MVP 仍为 fluorescence manual ROI grayscale analysis 和 scratch/wound manual ROI + threshold area estimation。
- cell counting、grayscale/ink-value、experiment templates 仍为 placeholder / in-development。
- 未接入 OpenCV、scikit-image、ImageJ/Fiji、AI 或自动图像解释。

## 11. Known Limitations

- 当前 UI 仍保留既有溶液配制和 qPCR 配液标签；L5B 只结构化强化三个目标 v1 计算器。
- 本阶段不提供历史记录、导出、项目级保存或批量计算。
- 计算器只做基础单位换算和公式计算，不处理试剂纯度自动校正、盐型/水合物自动换算、细胞活率校正或复杂孔板布局。

## 12. Next Recommended Stage

- L5C：qPCR / WB-SDS-PAGE loading calculator 的结构化 v1 化和测试补齐。
- L6A：图像 ROI 结果持久化、CSV/manifest/overlay preview 导出，保持 manual-review / semi-quantitative。
- L6B：本地 reagent recipe draft center 持久化和安全边界硬化。

## 13. Git Status

提交后工作树应为 clean；最终交接以 `git status --short --branch` 为准。
