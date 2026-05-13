# LabTools Handoff Report - 2026-05-13

## 1. Branch / Worktree Summary

- 当前 worktree 路径：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- 当前 git branch：`dev/labtools`
- 当前 HEAD commit：`ab262cb3166140055bb328c6e07eb2a59c0673a5`
- HEAD 摘要：`ab262cb feat(labtools): add wound healing threshold analysis mvp`
- L5A 状态：本报告已追加状态文案校准说明。
- L5A 前本报告文件处于未跟踪状态；本阶段将其作为 scoped handoff 产物纳入提交。
- 本地 upstream/tracking：`git branch -vv` 未显示 `dev/labtools` 跟踪远程分支；未执行 `git fetch`，未确认远程最新状态。
- 与 MainLine / upstream 明显分叉：
  - 本地 `stable/mainline` 存在，HEAD 为 `73d4cc7`。
  - `git merge-base --is-ancestor stable/mainline dev/labtools` 退出码为 `1`。
  - `git merge-base --is-ancestor dev/labtools stable/mainline` 退出码为 `1`。
  - `git rev-list --left-right --count stable/mainline...dev/labtools` 输出 `29 11`。
  - 结论：基于本地 refs，`dev/labtools` 与 `stable/mainline` 已明显分叉，后续进入 MainLine 前需要 Integration 或等价验证。
- 当前分支职责边界：LabTools / 医研智析实验工具模块，包含实验计算器、试剂与配方、来源草稿框架、图像定量辅助；不得污染 Bioinformatics / Meta / Vocabulary / AI Gateway / MainLine，不得把测试级或阈值估算结果写成正式科研结论。

实际执行的状态命令：

```bash
pwd
git status --short
git branch --show-current
git rev-parse --short HEAD
git rev-parse HEAD
git log --oneline -5
git status -sb
git branch -vv
git remote -v
git merge-base --is-ancestor stable/mainline dev/labtools
git merge-base --is-ancestor dev/labtools stable/mainline
git rev-list --left-right --count stable/mainline...dev/labtools
```

最近 5 个提交：

```text
ab262cb feat(labtools): add wound healing threshold analysis mvp
01e94fb feat(labtools): enhance fluorescence result review export
7e64dfc feat(labtools): add fluorescence roi analysis mvp
d1e7f71 docs(labtools): add current development handoff
be8e5e8 feat(labtools): add image analysis framework
```

## 2. Current Functional Scope

### 已实现并可运行的功能

- LabTools 统一 Shell 工作区入口：
  - `app/labtools/workspace.py`
  - `app/labtools/labtools_home.py`
  - 页面 key：`home`, `calculators`, `recipes`, `image_analysis`, `pending`
- 实验计算器：
  - 浓度 / 分子量 / 摩尔浓度换算。
  - C1V1 = C2V2 稀释计算。
  - 溶液配制、细胞接种、qPCR 配液计算。
  - `CalculationResult` 和 `CalculationRecord` 支持结构化记录和 JSON-compatible dict。
- 本地试剂与配方：
  - 内置常用科研参考配方。
  - 配方体积缩放。
  - stock-to-working dilution。
  - 用户配方草稿确认，确认后进入内存态 `UserRecipeStore`。
- 来源草稿框架：
  - 支持手动来源卡片、摘录草稿、摘录草稿转用户配方草稿。
  - `network_enabled` 默认关闭；当前 importer 不访问外部网络。
- 图像定量框架与当前 MVP：
  - 图片路径校验、本地图片记录、任务草稿、ROI 占位、结果占位、审计记录。
  - 仅引用本地图片路径，不复制、不上传、不自动写盘。
  - 荧光 manual ROI grayscale 指标和 scratch/wound manual ROI + threshold 面积估算为 testing-level MVP 可用。
  - 细胞计数、灰度 / 墨值仍为 `algorithm_not_available` 占位。
- 荧光强度 ROI 分析 MVP：
  - 单张本地图片。
  - Pillow 读取并转换 grayscale。
  - 手动 signal ROI / background ROI。
  - mean intensity、integrated density、background mean、corrected total fluorescence、min/max。
  - 质量 warnings、JSON-compatible dict、CSV rows/text、Markdown 报告片段。
  - UI 中显示结果摘要、指标表、参数摘要、warning、复核提示和简洁导出预览。
- 划痕实验面积分析 MVP：
  - 单张本地图片。
  - Pillow 读取并转换 grayscale。
  - 手动 analysis ROI。
  - 用户手动阈值 0-255。
  - bright / dark 模式。
  - ROI area、scratch area、scratch area fraction、non-scratch area/fraction。
  - 结果明确标注为“基于用户 ROI 和阈值的划痕区域估算”。
  - 质量 warnings、JSON-compatible dict、CSV rows/text、Markdown 报告片段。
  - UI 中显示 ROI、阈值、模式、结果摘要、公式、warning、复核提示和导出预览。

### 已接入 UI 但只是占位 / 测试级 / draft 的功能

- 图像定量中的细胞计数：任务卡片存在，但仍为 `algorithm_not_available` / draft，占位结果不得当作真实结果。
- 图像定量中的灰度 / 墨值分析：任务卡片存在，但仍为 `algorithm_not_available` / draft。
- 实验模板：LabTools 首页入口存在，进入后为开发中占位页。

### 只有后端或服务层，还没有完整 UI 的功能

- 图像分析 audit record 生成函数在荧光和划痕模块中可用，但当前 UI 仅展示审计条数摘要，没有完整审计日志浏览器。
- 荧光和划痕的 JSON/CSV/Markdown 导出函数返回内存结构或字符串，当前 UI 只预览，不提供保存文件操作。

### 仅有设计、文档或预留接口的功能

- ImageJ/Fiji、OpenCV、scikit-image、imageio、napari、cellpose、stardist 等外部图像工具依赖：未接入，仅作为未来边界在文档中声明。
- LabTools 本地项目存储、数据库持久化、正式报告写盘：未实现。
- 外部配方网络检索：未启用，当前只支持手动来源录入。

## 3. Completed Work Since Last Handoff

- 完成：图像分析基础框架 L4A
  - 涉及文件：`app/labtools/image_analysis/*`, `app/labtools/ui/image_analysis_widgets.py`, `docs/stage_labtools_l4a_image_analysis_framework_report.md`
  - 行为变化：新增本地图片记录、图像任务草稿、ROI 占位、结果占位、审计记录。
  - UI 变化：LabTools 首页“图像定量”入口可进入，显示图片路径输入和四类任务卡片。
  - 数据/manifest：`LabImageRecord`, `ImageAnalysisTask`, `ROIRecord`, `ImageAnalysisResult`, `ImageAnalysisAuditRecord`。
  - 测试：阶段报告记录 `tests/labtools` 68 passed、`tests/ui` 135 passed、指定 UI/entry 18 passed、smoke/compileall/diff 通过。

- 完成：荧光强度 ROI 分析 MVP L4B
  - 涉及文件：`app/labtools/image_analysis/fluorescence/*`, `pyproject.toml`, `requirements.txt`, `app/labtools/ui/image_analysis_widgets.py`, `tests/labtools/test_fluorescence_*`
  - 行为变化：接入 Pillow 最小依赖；支持单张图片、手动 signal/background ROI、grayscale 指标和 CTF。
  - UI 变化：“荧光强度分析”显示 MVP 可用，新增 ROI 输入和运行按钮。
  - 数据/manifest：`FluorescenceROI`, `FluorescenceAnalysisParameters`, `FluorescenceAnalysisMetrics`, `FluorescenceAnalysisResult`。
  - 测试：阶段报告记录 `tests/labtools` 78 passed、`tests/ui` 135 passed、指定 UI/entry 18 passed、smoke/compileall/diff 通过。

- 完成：荧光复核与导出增强 L4B.1
  - 涉及文件：`fluorescence_export.py`, `fluorescence_quality.py`, `fluorescence_report.py`, `fluorescence_models.py`, `image_analysis_widgets.py`, `tests/labtools/test_fluorescence_export.py`, `test_fluorescence_quality.py`, `test_fluorescence_report.py`
  - 行为变化：新增质量提示、JSON-compatible dict、CSV rows/text、Markdown 报告片段。
  - UI 变化：荧光结果面板展示指标表、参数摘要、warning、复核提示和简洁导出预览。
  - 数据/manifest：荧光结果顶层增加 image filename、image dimensions、ROI、formula、warnings、review_notice、generated_at。
  - 测试：阶段报告记录 `tests/labtools` 86 passed、`tests/ui` 135 passed、指定 UI/entry 18 passed、smoke/compileall/diff 通过。

- 完成：划痕实验面积分析 MVP L4C
  - 涉及文件：`app/labtools/image_analysis/wound_healing/*`, `app/labtools/ui/image_analysis_widgets.py`, `tests/labtools/test_wound_*`, `docs/stage_labtools_l4c_wound_healing_mvp_report.md`
  - 行为变化：新增单张图片、手动 ROI、用户阈值、bright/dark 模式的 scratch candidate 面积估算。
  - UI 变化：“划痕实验面积分析”卡片进入 MVP 可用状态，新增 ROI、阈值、模式输入和运行按钮。
  - 数据/manifest：`WoundHealingROI`, `WoundHealingParameters`, `WoundHealingMetrics`, `WoundHealingResult`，导出字段包括 image filename、dimensions、ROI、threshold、scratch_mode、metrics、formula、warnings、review_notice。
  - 测试：本次复跑 `tests/labtools` 104 passed、`tests/ui` 135 passed、指定 UI/entry 18 passed、smoke/compileall/diff 通过。

## 4. Important Files and Entry Points

### 主要 UI 文件

- `app/labtools/workspace.py`：LabTools 工作区主容器；连接首页、实验计算器、试剂与配方、图像定量、实验模板占位页；提供 `labtools_features()`。
- `app/labtools/labtools_home.py`：LabTools 首页四个入口卡片。
- `app/labtools/ui/calculator_widgets.py`：实验计算器 UI。
- `app/labtools/ui/recipe_widgets.py`：试剂与配方 UI，包含本地库、配方缩放、用户配方草稿和来源草稿相关界面。
- `app/labtools/ui/image_analysis_widgets.py`：图像定量 UI；当前承载图片路径输入、任务卡片、荧光 ROI 分析、划痕阈值分析和结果预览。

### 主要 service / workflow 文件

- `app/labtools/calculators/*.py`：浓度、稀释、溶液配制、细胞接种、qPCR 配液等计算逻辑。
- `app/labtools/recipes/recipe_library.py`：本地配方库入口。
- `app/labtools/recipes/recipe_scaling.py`：配方缩放与 stock-to-working dilution。
- `app/labtools/recipes/recipe_source_importer.py`：来源草稿 importer；当前不访问网络，只支持手动来源。
- `app/labtools/image_analysis/image_io.py`：图片路径校验和 `LabImageRecord` 创建。
- `app/labtools/image_analysis/analysis_task.py`：图像分析任务类型、状态和任务草稿创建。
- `app/labtools/image_analysis/fluorescence/fluorescence_analyzer.py`：荧光 ROI 分析核心。
- `app/labtools/image_analysis/wound_healing/wound_analyzer.py`：划痕 ROI 阈值面积估算核心。

### 主要 schema / manifest / contract 文件

- `app/labtools/calculators/calculator_models.py`：`CalculationResult` 和用户复核提示。
- `app/labtools/calculators/calculation_record.py`：`CalculationRecord` JSON-compatible dict。
- `app/labtools/recipes/recipe_models.py`：`Recipe`, `RecipeDraft`, `RecipeScalingResult` 等结构。
- `app/labtools/recipes/recipe_source_models.py`：`RecipeSourceRequest`, `RecipeSourceCard`, `RecipeExtractionDraft`。
- `app/labtools/image_analysis/image_models.py`：`LabImageRecord`, `ImageAnalysisError`, supported image extensions。
- `app/labtools/image_analysis/result_models.py`：非真实算法占位结果结构。
- `app/labtools/image_analysis/fluorescence/fluorescence_models.py`：荧光参数、指标、结果结构。
- `app/labtools/image_analysis/wound_healing/wound_models.py`：划痕参数、指标、结果结构。

### 主要测试文件

- `tests/labtools/test_*calculator*.py`, `test_unit_conversion.py`, `test_calculation_record.py`：实验计算器。
- `tests/labtools/test_recipe_*.py`, `test_user_recipe_store.py`：配方库、缩放、来源草稿、用户配方。
- `tests/labtools/test_image_*.py`：图像分析基础模型和路径校验。
- `tests/labtools/test_fluorescence_*.py`：荧光 ROI 分析、质量提示、导出、报告片段。
- `tests/labtools/test_wound_*.py`：划痕 bright/dark 阈值计算、质量提示、导出、报告片段。
- `tests/ui/test_module_selection.py`, `tests/ui/test_sidebar.py`, `tests/test_unified_entry.py`：Shell / LabTools 入口接入。
- `tests/ui/*`：统一 UI、模块选择、Bioinformatics 相关 UI 回归；当前 LabTools 验证也会跑全量 `tests/ui`。

### 当前报告、审计、handoff 文件

- `docs/labtools_current_handoff.md`：当前 LabTools handoff。注意：其中 L4C 行仍写“提交后以最终交接为准”，但当前 HEAD 已是 L4C commit `ab262cb`；本报告记录当前真实状态。
- `docs/stage_labtools_l4a_image_analysis_framework_report.md`
- `docs/stage_labtools_l4b_fluorescence_roi_mvp_report.md`
- `docs/stage_labtools_l4b_1_fluorescence_review_export_report.md`
- `docs/stage_labtools_l4c_wound_healing_mvp_report.md`
- `reports/LabTools_handoff_report_20260513.md`：本报告。

## 5. Runtime / User Flow

当前 LabTools 用户流程：

1. BioMedPilot 统一入口 / Shell。
2. 模块选择或侧边栏进入 `LabTools / 实验工具`。
3. LabTools 首页显示四个入口：
   - 实验计算器
   - 试剂与配方
   - 图像定量
   - 实验模板
4. 实验计算器流程：
   - 选择计算器页面。
   - 输入数值和单位。
   - 运行计算。
   - UI 显示输入摘要、公式、结果、warning、人工复核提示。
   - 计算记录为内存结构 / JSON-compatible dict。
5. 试剂与配方流程：
   - 浏览本地配方库。
   - 执行配方缩放或 stock-to-working dilution。
   - 可手动录入来源卡片和摘录草稿。
   - 摘录草稿必须转为用户配方草稿，再由用户确认保存到内存态 store。
6. 图像定量流程：
   - 输入或选择本地图片路径。
   - 创建图片记录；只引用本地路径，不复制、不上传、不联网。
   - 可创建四类任务草稿。
   - 对荧光强度分析：输入 signal/background ROI，运行手动 ROI grayscale 指标计算。
   - 对划痕实验面积分析：输入 ROI、阈值和 bright/dark 模式，运行基于阈值的面积估算。
   - UI 显示结果摘要、公式、warnings、复核提示、JSON/CSV/Markdown 预览。
   - 细胞计数和灰度/墨值仍停在算法开发中。

当前流程断点：

- 没有 ROI 绘制器、图像预览器或 overlay 复核。
- 没有批量分析、多时间点曲线、细胞计数、WB/凝胶灰度真实算法。
- 没有项目级持久化、数据库、正式报告文件保存或桌面 app 打包同步。
- 没有外部网络检索或 AI Gateway 调用。

## 6. Data Contracts / Manifest Contracts

- `CalculationRecord`
  - 文件位置：`app/labtools/calculators/calculation_record.py`
  - 由谁生成：`CalculationResult.to_record()` 或调用方。
  - 由谁读取：当前 UI/测试可读取 summary 和 dict；未见跨模块读取。
  - 当前状态：测试级 / JSON-compatible。
  - 是否允许后续模块依赖：仅 LabTools 内部可依赖；跨模块依赖需单独设计。

- `Recipe` / `RecipeDraft` / `RecipeScalingResult`
  - 文件位置：`app/labtools/recipes/recipe_models.py`
  - 由谁生成：内置配方库、用户草稿确认、配方缩放逻辑。
  - 由谁读取：LabTools recipe UI、tests。
  - 当前状态：测试级 / 本地内存结构。
  - 是否允许后续模块依赖：不建议跨模块依赖；不要混入 Bioinformatics / Meta manifest。

- `RecipeSourceRequest` / `RecipeSourceCard` / `RecipeExtractionDraft`
  - 文件位置：`app/labtools/recipes/recipe_source_models.py`
  - 由谁生成：`RecipeSourceImporter` 手动来源流程。
  - 由谁读取：recipe UI、用户配方草稿转换逻辑、tests。
  - 当前状态：draft / 手动录入；网络检索禁用。
  - 是否允许后续模块依赖：仅 LabTools 内部 draft；不得当作标准 SOP 或已验证来源。

- `UserRecipeStore.export_dict()`
  - 文件位置：`app/labtools/recipes/user_recipe_store.py`
  - 由谁生成：用户确认配方草稿后进入内存 store。
  - 由谁读取：LabTools recipe UI/测试。
  - 当前状态：测试级内存结构；不自动写盘。
  - 是否允许后续模块依赖：不允许跨模块直接依赖。

- `LabImageRecord`
  - 文件位置：`app/labtools/image_analysis/image_models.py`
  - 由谁生成：`create_image_record()`。
  - 由谁读取：`ImageAnalysisTask`、图像 UI、测试。
  - 当前状态：测试级；只引用本地 path。
  - 是否允许后续模块依赖：仅 LabTools 内部；图片路径不得写入 Bioinformatics / Meta 项目结构。

- `ImageAnalysisTask` / placeholder `ImageAnalysisResult`
  - 文件位置：`app/labtools/image_analysis/analysis_task.py`, `result_models.py`
  - 由谁生成：`create_analysis_task()`。
  - 由谁读取：图像 UI、tests。
  - 当前状态：draft / placeholder；对未实现算法使用 `algorithm_not_available`。
  - 是否允许后续模块依赖：仅 LabTools 内部；不能当作真实定量结果。

- `ImageAnalysisAuditRecord`
  - 文件位置：`app/labtools/image_analysis/audit_models.py`
  - 由谁生成：图像任务创建、荧光/划痕分析完成函数。
  - 由谁读取：当前 UI 只显示审计条数摘要；测试读取 dict。
  - 当前状态：测试级审计结构；无持久化。
  - 是否允许后续模块依赖：仅 LabTools 内部。

- `FluorescenceAnalysisResult`
  - 文件位置：`app/labtools/image_analysis/fluorescence/fluorescence_models.py`
  - 由谁生成：`analyze_fluorescence_roi()`。
  - 由谁读取：荧光导出、报告片段、UI、tests。
  - 当前状态：测试级 measurement assistance；真实计算来自 Pillow grayscale 手动 ROI。
  - 是否允许后续模块依赖：仅 LabTools 内部；外部报告系统如需使用，必须保留 review_notice 和 warnings。

- `WoundHealingResult`
  - 文件位置：`app/labtools/image_analysis/wound_healing/wound_models.py`
  - 由谁生成：`analyze_wound_healing_area()`。
  - 由谁读取：划痕导出、报告片段、UI、tests。
  - 当前状态：测试级 threshold-based estimation；不得表述为自动迁移效果判断。
  - 是否允许后续模块依赖：仅 LabTools 内部；后续报告系统必须保留“基于用户 ROI 和阈值的估算”语义。

- 导出字符串 / rows / Markdown 片段
  - 文件位置：
    - `app/labtools/image_analysis/fluorescence/fluorescence_export.py`
    - `app/labtools/image_analysis/fluorescence/fluorescence_report.py`
    - `app/labtools/image_analysis/wound_healing/wound_export.py`
    - `app/labtools/image_analysis/wound_healing/wound_report.py`
  - 由谁生成：调用方或 UI。
  - 由谁读取：当前 UI 预览和测试。
  - 当前状态：测试级内存结构；默认不写文件。
  - 是否允许后续模块依赖：可作为 LabTools 后续报告系统输入，但不能删除 warnings/review_notice。

## 7. Tests and Validation

本次报告生成过程中实际运行：

```bash
python3 - <<'PY'
from PIL import Image
print("Pillow import OK", Image)
PY
```

结果：通过，输出包含 `Pillow import OK <module 'PIL.Image' ...>`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q
```

结果：通过，`104 passed in 0.45s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

结果：通过，`135 passed in 9.30s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q
```

结果：通过，`18 passed in 2.34s`。

```bash
python3 -m app.main --smoke-test
```

结果：通过，输出包含：

```text
app_version=0.1.0-internal-beta
app_channel=Developer Preview / testing
launch_mode=source
app_root=/Users/changdali/Developer/biomedpilot v1.0/LabTools
git_head=ab262cb
workspace_entries=3
bioinformatics_features=5
meta_analysis_features=9
labtools_features=4
pyside6_available=True
```

```bash
python3 -m compileall app/labtools
```

结果：通过，列出 `app/labtools`、`calculators`、`image_analysis`、`fluorescence`、`wound_healing`、`recipes`、`ui`。

```bash
git diff --check
```

结果：通过，无输出。

未运行的测试：

- 未运行全仓库所有测试。
- 未运行 packaging / ReleaseBuild 测试。
- 未运行 MainLine / Integration 合并验证。
- 未做手动 GUI 点击测试；本报告只复用 PySide offscreen UI tests 和 smoke test。

是否需要用户手动确认：

- 进入 MainLine / Integration 前需要人工确认合并策略。
- 如要保存用户图片、结果文件或报告文件，需要先确认本地项目存储策略。
- 如要启用 ImageJ/Fiji、OpenCV、scikit-image、网络检索或 AI Gateway，需要单独阶段授权。

## 8. Known Issues / Risks

- L5A 已校准 `docs/labtools_current_handoff.md` 的 L4C commit 和当前阶段说明，避免继续误读为 L4C 未提交。
- L5A 已校准 `labtools_features()` 和 LabTools 首页/图像 UI 文案，使“图像定量”明确包含两个 testing-level MVP，同时把细胞计数和灰度/墨值保留为占位。
- 本地 `dev/labtools` 与 `stable/mainline` 明显分叉，且 `dev/labtools` 未显示 upstream tracking；进入 MainLine 前必须走 Integration 或等价验证。
- 图像分析 UI 没有图像预览、ROI 绘制器、overlay 或阈值可视化，用户只能手动输入坐标/阈值；误设 ROI 或阈值的风险由 warning 和 review_notice 缓解但未消除。
- 荧光和划痕结果目前默认只返回内存结构或字符串预览；无正式报告系统、无文件保存、无项目级持久化。
- 划痕 `non_scratch_area_fraction` 只是基于阈值的 covered / migrated fraction 估算，不能解释为真实迁移效果、趋势或结论。
- 细胞计数、WB/凝胶灰度、自动 ROI、批量分析、多时间点迁移曲线均未实现；UI 必须继续防止占位功能被误认为可用。
- 当前没有外部网络、AI Gateway、本地模型、ImageJ/Fiji、OpenCV、scikit-image 接入；任何启用都属于新阶段边界。
- 本报告没有验证桌面 app 包 `/Users/changdali/Desktop/BioMedPilot.app`，也没有覆盖 ReleaseBuild 包。

## 9. Do Not Touch / Boundary Rules

- 不要修改其他 worktree 或跨模块业务逻辑；尤其不要修改 Bioinformatics / Meta / Vocabulary / AI Gateway / MainLine。
- 不要把 LabTools 计算器、配方、图像分析任务或图片路径写入 Bioinformatics / Meta manifest。
- 不要启用外部网络检索、网页抓取、下载、AI Gateway、本地模型、ImageJ/Fiji、OpenCV、scikit-image 等能力，除非有单独阶段明确授权。
- 不要自动保存用户图片、图像结果、导出 CSV/JSON/Markdown 或项目数据；当前导出只应返回内存结构或字符串。
- 不要把荧光、划痕等 testing-level measurement assistance 结果表述为生产级、临床级、提交级或正式科研结论。
- 不要把划痕阈值估算自动解释为细胞迁移效果、愈合速度或多时间点曲线。
- 不要生成 fake 图像结果、fake 实验结果、fake report。
- 不要删除 legacy、测试、阶段报告、handoff 或 release 相关文件。
- 不要覆盖桌面 app、release 包、用户测试入口或人工确认过的入口文件。
- 不要 push remote；当前任务没有远程写授权。

## 10. Recommended Next Tasks

### Immediate Next Step

- L5B：实验计算器硬化与缺口补齐。现有 dilution、浓度/质量、溶液配制、细胞接种、qPCR 已可用，下一步应先补验证用例和 UI 一致性；WB/SDS-PAGE loading calculator 可作为小扩展。
- L6A：图像 ROI 结果持久化设计与 CSV/manifest/overlay preview 导出；继续保持 manual-review / semi-quantitative 表述。
- L6B：常用 reagent recipe draft center 的本地持久化和安全边界硬化；现有本地配方库、用户草稿和手动来源草稿作为基础。

### Before Integration

- 在 Integration worktree 中合并 `dev/labtools` 后跑至少：
  - `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`
  - `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q`
  - `python3 -m app.main --smoke-test`
  - `python3 -m compileall app/labtools`
  - `git diff --check`
- 检查 Integration / MainLine 中是否已有不同版本的 LabTools handoff 或 UI 状态文案，避免 merge 后低估或高估功能状态。
- 验证 `pyproject.toml` / `requirements.txt` 中 Pillow 依赖在目标集成源中存在，且未引入 OpenCV/scikit-image 等未授权依赖。
- 明确是否需要同步桌面 app entry point；不要直接从单一模块 worktree 生成 release/internal beta 包。

### Later / Optional

- 设计 ROI 可视化和图像预览，但仍保持手动确认，不做自动 ROI 检测。
- 为划痕阈值分析增加阈值预览或候选区域 overlay 的测试级 UI，明确不自动判断迁移效果。
- 设计 LabTools 本地项目存储策略，包括用户选择目录、隐私边界、审计字段、导出文件命名和清理策略。
- 设计正式报告系统接入方式，复用现有 JSON/CSV/Markdown 片段，同时保留 warnings 和 review_notice。
- 后续单独阶段实现细胞计数 MVP 或 WB/凝胶灰度 MVP；需要新的算法边界、复核路径和测试基线。

## 11. Suggested Codex Instruction for Next Stage

```text
你现在继续负责 BioMedPilot / 医研智析 LabTools 模块开发。

开发前必须读取并遵守：
- /Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md
- /Users/changdali/Developer/biomedpilot v1.0/README_总说明.md
- /Users/changdali/Developer/biomedpilot v1.0/LabTools/CODEX.md
- /Users/changdali/Developer/biomedpilot v1.0/LabTools/docs/labtools_current_handoff.md
- /Users/changdali/Developer/biomedpilot v1.0/LabTools/reports/LabTools_handoff_report_20260513.md

当前 worktree 必须是：
/Users/changdali/Developer/biomedpilot v1.0/LabTools

当前分支必须是：
dev/labtools

当前 HEAD 应为：
ab262cb3166140055bb328c6e07eb2a59c0673a5

目标：
进行 LabTools 下一阶段的小范围维护任务：修正 LabTools 当前 handoff 和 feature status 文案，使其准确反映当前 testing-level 状态：实验计算器、试剂与配方可用；图像定量中荧光 ROI 和划痕阈值分析为 MVP 可用；细胞计数、灰度/墨值、实验模板仍开发中。不要开发新图像算法。

允许修改范围：
- docs/labtools_current_handoff.md
- app/labtools/workspace.py
- 必要时新增或更新 tests/labtools 或 tests/ui 中与 LabTools feature status / UI 文案相关的最小测试
- 必要时新增阶段报告 docs/stage_labtools_status_text_sync_report.md

禁止事项：
- 不得修改 Bioinformatics / Meta / Vocabulary / AI Gateway / MainLine 业务逻辑。
- 不得启用外部网络、AI Gateway、本地模型、ImageJ/Fiji、OpenCV、scikit-image、imageio、napari、cellpose、stardist。
- 不得自动写盘保存用户图片或结果。
- 不得把 testing-level 或阈值估算结果表述为正式科研结论。
- 不得删除测试、handoff、阶段报告、legacy 或 release 文件。
- 不得 push remote。

测试命令：
- QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q
- QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
- QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q
- python3 -m app.main --smoke-test
- python3 -m compileall app/labtools
- git diff --check
- git diff --cached --check（如需要提交）

报告要求：
- 记录当前 worktree、branch、HEAD、修改文件、测试结果、边界状态。
- 明确没有接入网络/AI/ImageJ/OpenCV/scikit-image，没有自动写盘，没有影响其他模块。

停止条件：
- 当前路径或分支不符。
- git status 出现与本任务相关但来源不明的未提交改动。
- 需要修改其他 worktree 或跨模块业务逻辑。
- 测试失败且修复方向超出文案/状态同步范围。
- 任务需要启用网络、AI、外部图像依赖、持久化或 remote push。
```
