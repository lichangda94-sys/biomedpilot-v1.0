# LabTools Current Development Handoff

日期：2026-05-13

## 1. 当前基线

- 当前 worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- 当前分支：`dev/labtools`
- 当前最近完成阶段：LabTools L4B-0 + Stage L4B，commit `7e64dfc3ed3d83dbb8e5a20ae1a3101544b65cd0`
- 当前进行阶段：LabTools Stage L4B.1，荧光 ROI 分析复核与导出增强。
- 权威总开发手册：`/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- 模块定位：LabTools / 医研智析实验工具模块，处于 Developer Preview / internal beta / local testing 状态。

本 handoff 用于上下文清理后继续 LabTools 开发。它是当前开发基线说明，不代表生产级、临床级或提交级能力。

## 2. 阶段摘要

| 阶段 | Commit | 摘要 |
| --- | --- | --- |
| LabTools Stage L0 + L1A | `c2416e142568377663ded0162e97f745429345a5` | 建立 `app/labtools` 模块骨架、`LabToolsWorkspaceWidget`、LabTools 首页四个入口；实现浓度换算和 C1V1 = C2V2 稀释计算。 |
| LabTools Stage L1B | `a305e25ef7acf514daafd2a8f319f9e40131b595` | 增加细胞接种、qPCR 配液、溶液配制计算器；新增 `CalculationRecord` 记录结构。 |
| LabTools L0.1 Baseline Sync | `6a3679f0b70c440e63148b0e6d25c84fc4daa0f8` | 对齐 MainLine 已有 `app.bioinformatics.deg_executor_preflight` 基线修复，修复 LabTools worktree 中 Shell/MainWindow 测试的 Bioinformatics 导入链缺口；不执行真实 DEG，不生成 fake DEG 结果。 |
| LabTools Stage L2 | `44eabf7173b7366127b224473b4556de82989e7b` | 实现本地试剂与配方库、配方缩放、stock-to-working dilution、用户配方草稿确认；不接外部网络，不调用 AI。 |
| LabTools Stage L3A | `3ce03b9fdd51ffd807cbccb007b247f8195a295e` | 建立外部来源草稿框架：来源请求模型、来源卡片、手动来源录入、摘录草稿、转用户配方草稿；`network_enabled` 默认关闭；不访问外部网络，不调用 AI。 |
| LabTools Stage L4A | `be8e5e8ef96c7c5ca39e646dc66ca7b5d04f0741` | 建立图像分析基础框架：图片记录、分析任务、ROI、占位结果、审计记录和图像定量 UI 入口；四类任务草稿已存在。 |
| LabTools Stage L4B | `7e64dfc3ed3d83dbb8e5a20ae1a3101544b65cd0` | 接入 Pillow 最小依赖，实现单张本地图片、手动 signal/background ROI、grayscale 荧光强度基础统计、背景扣除 CTF、负 CTF warning、审计记录和 UI MVP。 |
| LabTools Stage L4B.1 | 提交后以最终交接为准 | 增强荧光 ROI 分析复核、质量提示、JSON-compatible dict、CSV-compatible rows/text、Markdown 报告片段和 UI 导出预览；不新增图像算法。 |

## 3. 当前已实现功能

### 3.1 实验计算器

- 浓度 / 分子量 / 摩尔浓度换算。
- C1V1 = C2V2 稀释计算。
- 溶液配制计算器。
- 细胞接种计算器。
- qPCR 配液计算器。
- `CalculationRecord` 计算记录结构，支持 JSON-compatible dict。
- 中文友好错误提示和人工复核提示。

### 3.2 本地试剂与配方库

- 内置本地科研参考配方。
- 配方按目标体积线性缩放。
- stock-to-working dilution 计算。
- 用户配方草稿确认。
- 用户配方保存在内存结构中，支持 JSON-compatible dict 导出，不自动写盘。

### 3.3 来源草稿框架

- `RecipeSourceRequest` 外部来源请求模型。
- `RecipeSourceCard` 来源卡片模型。
- 手动来源 URL / 标题 / 摘要 / 摘录内容录入。
- `RecipeExtractionDraft` 摘录草稿模型。
- 摘录草稿转用户配方草稿。
- 用户确认后保存为 confirmed user recipe。
- `network_enabled` 默认关闭。
- 当前只支持手动录入来源，不访问外部网络。

### 3.4 图像分析框架

- `LabImageRecord` 图片记录模型。
- `ImageAnalysisTask` 图像分析任务模型。
- `ROIRecord` ROI 占位模型。
- `ImageAnalysisResult` 结果占位模型。
- `ImageAnalysisAuditRecord` 审计记录模型。
- 四类任务草稿：
  - `wound_healing`：划痕实验面积分析，占位，算法开发中。
  - `cell_counting`：细胞计数，占位，算法开发中。
  - `fluorescence_intensity`：荧光强度分析，当前唯一真实图像算法。
  - `densitometry`：灰度 / 墨值分析，占位，算法开发中。
- 非荧光任务仍为 `algorithm_not_available` 占位状态，不生成 fake 定量结果。

### 3.5 荧光强度 ROI 分析

- 使用 Pillow 读取单张本地图片，并转换为 grayscale。
- 用户手动输入 signal ROI 和 background ROI。
- ROI 坐标必须位于图片边界内。
- 计算：
  - ROI area pixels
  - mean intensity
  - integrated density
  - background mean intensity
  - corrected total fluorescence
  - min intensity
  - max intensity
- 公式：`CTF = Integrated Density - ROI Area x Background Mean`
- 负 CTF 保留数值并生成中文 warning。
- 记录图像文件名、图像尺寸、ROI 坐标、公式、warnings、review_notice。
- 提供 JSON-compatible dict、CSV-compatible rows/text、Markdown 报告片段字符串。
- UI 展示指标表、参数摘要、warning、复核提示和简洁导出预览。
- 默认不自动写盘，不上传图片，不访问网络，不调用 AI Gateway。

## 4. 当前未实现功能

- 未实现自动 ROI 检测。
- 未实现自动细胞识别。
- 未实现批量分析。
- 未实现划痕面积分析。
- 未实现细胞计数。
- 未实现 WB / 凝胶灰度分析。
- 未实现 ImageJ/Fiji 接入。
- 未实现 OpenCV / scikit-image / imageio / napari / cellpose / stardist 等依赖接入。
- 未实现 ROI 绘制器、overlay 复核、图像预览器。
- 未启用外部配方网络检索。
- 未实现网页抓取、网页下载、远程来源同步。
- 未调用 AI Gateway 或本地模型进行配方摘录、图像分析或结果解释。
- 未实现 LabTools 本地项目存储、数据库持久化或自动写盘。
- 未实现正式实验报告导出。
- 未实现实验模板功能。

## 5. 明确禁止事项

- 不得生成 fake 实验结果。
- 不得生成 fake 图像定量结果。
- 不得把图像框架占位状态作为真实实验结果。
- 不得在未授权阶段启用外部网络检索。
- 不得在未授权阶段调用 AI Gateway 或本地模型。
- 不得在未授权阶段接入 ImageJ/Fiji。
- 不得跨模块污染 Bioinformatics、Meta、Vocabulary、AI Gateway。
- 不得修改 MainLine。
- 不得 push remote。
- 不得自动写盘保存用户实验数据，除非后续任务明确授权并设计项目存储策略。
- 不得把图片路径写入 Bioinformatics 或 Meta 项目结构。
- 不得把 LabTools 配方、计算器或图像分析任务混入 Bioinformatics / Meta manifest。

## 6. 当前测试基线

本 handoff 的测试基线应以最近阶段报告和最终交接为准。L4B.1 代码/UI/测试变更后至少运行：

- `python3 - <<'PY' ... from PIL import Image ... PY`
  - 当前 L4B.1 结果：通过，输出 `Pillow import OK ...`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`
  - 当前 L4B.1 结果：86 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - 当前 L4B.1 结果：135 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q`
  - 当前 L4B.1 结果：18 passed
- `python3 -m app.main --smoke-test`
  - 当前 L4B.1 结果：通过，输出包含 `workspace_entries=3`、`labtools_features=4`
- `python3 -m compileall app/labtools`
  - 当前 L4B.1 结果：通过
- `git diff --check`
  - 当前 L4B.1 结果：通过
- `git diff --cached --check`
  - 当前 L4B.1 结果：通过

## 7. Shell / UI 接入状态

- LabTools 已接入统一 BioMedPilot Shell。
- LabTools 首页当前四个入口：
  - 实验计算器：可进入。
  - 试剂与配方：可进入。
  - 图像定量：可进入；荧光强度分析为手动 ROI MVP 可用，其它图像任务仍为算法开发中。
  - 实验模板：仍为开发中。
- `LabToolsWorkspaceWidget.page_keys()` 当前包含：
  - `home`
  - `calculators`
  - `recipes`
  - `image_analysis`
  - `pending`
- 普通用户界面应继续保持中文友好，不暴露 traceback、内部 schema、内部 id 或大量调试细节。
- UI 必须继续使用 BioMedPilot 统一 UI token，不引入 LabTools 独立主题色。

## 8. 外部网络、AI Gateway、ImageJ/Fiji 状态

- 外部网络：未启用。
- 配方外部来源：只支持手动录入来源草稿；不抓取网页，不下载网页内容。
- AI Gateway：未调用。
- 本地模型：未调用。
- ImageJ/Fiji：未接入。
- OpenCV / scikit-image：未接入，未新增大型图像依赖。
- Pillow：已作为 L4B 最小图片读取依赖接入。

任何启用网络、AI Gateway、本地模型、ImageJ/Fiji、OpenCV 或 scikit-image 的任务，都必须作为单独阶段明确授权，并重新设计安全边界和测试计划。

## 9. 图像分析真实算法状态

- 当前唯一真实图像算法：`fluorescence_intensity` 手动 ROI 荧光强度分析。
- 算法名：`manual_roi_grayscale_fluorescence_v1`。
- 算法状态：Developer Preview / testing-level measurement assistance。
- 其它图像任务必须保持 `algorithm_not_available` 或 draft 占位，不得生成面积、细胞数、划痕或 WB/凝胶灰度 fake 数值。
- 荧光分析结果必须显示人工复核提示，不得作为无需复核的实验结论。

## 10. 数据持久化状态

- 计算记录：内存结构 / JSON-compatible dict。
- 用户自定义配方：确认后进入 `UserRecipeStore` 内存结构。
- 来源草稿：手动来源和摘录草稿在 UI / 模型层流转，确认后才进入用户配方 store。
- 图片记录：引用本地路径并生成 `LabImageRecord`，不复制、不上传、不自动写盘。
- 荧光结果导出：默认只返回 dict、rows/text 或 Markdown 字符串，不自动写盘。
- 当前没有 LabTools 数据库、项目目录自动写入或后台持久化机制。

后续如需保存用户实验数据，必须先设计本地项目存储策略、用户选择位置、隐私边界、审计字段和迁移/清理规则。

## 11. 跨模块边界

- Bioinformatics：不得修改业务逻辑，不得写入 Bioinformatics 项目结构，不得混入 LabTools 计算器、配方或图像分析任务。
- Meta Analysis：不得修改业务逻辑，不得混入 LabTools 配方、图像分析或实验记录。
- Vocabulary：不得修改业务逻辑；如未来需要共享术语，必须作为独立共享词表阶段设计。
- AI Gateway：不得绕过；任何模型调用必须走 AI Gateway 且默认禁用，需要单独授权。
- MainLine：不得在 LabTools feature 阶段直接修改；后续进入 MainLine 需经 Integration 或等价验证流程。

## 12. 风险点和开发注意事项

- 图像分析是高风险增长点：必须避免把占位结果、草稿状态或算法未启用状态表述成实验结果。
- 荧光 ROI MVP 只适合手动 ROI、单张本地图片、grayscale 统计和背景扣除。
- 任何真实图像算法都必须记录算法名、版本、参数、ROI、输入 provenance、人工复核提示。
- 图像定量 UI 不得默认显示其它算法的数值结果，除非算法已经实现并通过测试。
- 外部配方来源不得声明为“标准方案”；来源内容必须要求人工核对 SOP、试剂说明书和安全规范。
- 用户数据和图片路径不得自动写盘、上传或跨模块传递。
- 如果测试暴露 Bioinformatics、Meta、Vocabulary、AI Gateway 的业务问题，不要在 LabTools 阶段混入修复，应停止并单独报告。
- 继续开发前应先确认 worktree、分支、`git status --short` 和总开发手册是否有更新。

## 13. 后续推荐路线

1. L4B.2：荧光结果复核 UI 细化或手动 ROI 可视化设计预研，但不得自动检测 ROI。
2. L4C：划痕实验面积分析 MVP，需要手动 ROI / 阈值确认，避免全自动误判。
3. L4D：细胞计数 MVP，需要参数化阈值、面积过滤、圆度过滤和 overlay 复核。
4. L4E：灰度 / 墨值分析 MVP，适合 WB / 凝胶条带，但必须保留背景扣除和人工复核。
5. L3B：受控外部配方检索，必须单独授权网络访问。
6. L5：LabTools 本地项目存储和报告导出。

## 14. Handoff 结论

LabTools 当前已经具备实验计算器、本地配方库、来源草稿框架、图像分析框架入口，以及第一个边界清晰的真实图像算法：手动 ROI 荧光强度分析。当前最重要的边界是：除荧光手动 ROI MVP 外，其它图像算法仍未实现；外部来源尚未访问网络；AI Gateway 未调用；用户数据和结果导出默认不自动写盘。后续开发应继续小步阶段化，并在每个真实算法、真实网络能力、AI 能力或持久化能力启用前单独确认授权、测试计划和安全提示。
