# LabTools Current Development Handoff

日期：2026-05-13

## 1. 当前基线

- 当前 worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- 当前分支：`dev/labtools`
- 当前最近完成阶段：LabTools Stage L6B.1，commit 以最终交接为准
- 当前进行阶段：下一阶段待定。
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
| LabTools Stage L4B.1 | `01e94fb09fb9e3c0c2925eb20a92f8dc07fd271e` | 增强荧光 ROI 分析复核、质量提示、JSON-compatible dict、CSV-compatible rows/text、Markdown 报告片段和 UI 导出预览；不新增图像算法。 |
| LabTools Stage L4C | `ab262cb3166140055bb328c6e07eb2a59c0673a5` | 新增单张本地图片、手动 ROI、用户阈值、亮/暗模式的划痕实验面积估算 MVP；结果为基于阈值的 measurement assistance，不自动判断迁移效果。 |
| LabTools Stage L5A | `32cb27c` | 校准 LabTools UI、feature status、handoff 和测试中的用户可见能力边界；不新增算法、不新增持久化、不启用网络/AI/外部图像依赖。 |
| LabTools Stage L5B | 最终交接记录 | 新增实验计算器中心 v1 结构化服务层和 UI 对齐，覆盖稀释、摩尔浓度/称量质量、细胞接种密度三类本地辅助计算；不做历史记录、导出或持久化。 |
| LabTools Stage L5C | 最终交接记录 | 新增 qPCR 配液 v1 和 WB/SDS-PAGE 上样计算 v1 结构化结果与 UI tab；不做 WB/凝胶灰度、条带分析、历史记录或导出。 |
| LabTools Stage L6A | 最终交接记录 | 新增 fluorescence manual ROI 与 wound manual ROI threshold 结果的用户确认导出包：JSON manifest、CSV summary、Markdown 片段和 ROI overlay PNG；默认仍不自动写盘。 |
| LabTools Stage L6A.1 | 最终交接记录 | 硬化 ROI export package schema、文件命名、no-overwrite、CSV header、Markdown manual-review 语义和 UI 导出取消/失败/成功反馈；不新增图像算法。 |
| LabTools Stage L6B | 最终交接记录 | 新增用户配方草稿本地 JSON 持久化和安全范围检查；保存/载入均需用户选择路径，不自动保存、不联网、不调用 AI、不新增 recipe 算法。 |
| LabTools Stage L6B.1 | 最终交接记录 | 补充 recipe draft store schema 文档，载入时显示 recipe_id 冲突 summary，冲突导入不会覆盖现有用户配方，并在 UI 显示用户草稿 version。 |
| LabTools Stage L6C | 最终交接记录 | 新增轻量实验模板和结构化记录草稿中心，覆盖 qPCR、WB、细胞接种、scratch assay、免疫荧光图像记录；不做完整 ELN、签名、权限或合规审计。 |
| LabTools Stage L6C.1 | 最终交接记录 | 新增实验记录草稿本地 JSON 持久化 schema、no-overwrite 保存、载入校验和 UI 保存/载入反馈；仍不做完整 ELN、数据库、自动保存、签名或合规审计。 |

## 3. 当前已实现功能

### 3.1 实验计算器

- 浓度 / 分子量 / 摩尔浓度换算。
- C1V1 = C2V2 稀释计算。
- 溶液配制计算器。
- 细胞接种计算器。
- qPCR 配液计算器。
- WB / SDS-PAGE 上样计算器。
- `CalculationRecord` 计算记录结构，支持 JSON-compatible dict。
- 中文友好错误提示和人工复核提示。
- L5B 新增 `experiment_calculator_center` 结构化 v1 服务层：
  - `DilutionInput` / `DilutionResult` / `calculate_dilution_v1()`：支持同维度浓度单位换算，输出 stock 体积、溶剂体积和 dilution factor。
  - `MassMolarityInput` / `MassMolarityResult` / `calculate_mass_molarity_v1()`：根据分子量、目标摩尔浓度和终体积估算称量质量。
  - `CellSeedingInput` / `CellSeedingResult` / `calculate_cell_seeding_v1()`：根据细胞悬液浓度、目标每孔细胞数、孔数、每孔体积和 overage 估算细胞悬液体积、培养基体积和总需求量。
- L5B v1 结果均为结构化辅助计算草稿，使用前需人工核对，不替代实验 SOP、临床建议或安全操作规范。
- L5C 新增：
  - `QpcrMixInput` / `QpcrMixResult` / `calculate_qpcr_mix_v1()`：输出 qPCR 单反应用量、总用量和 overage 后总用量。
  - `WesternBlotLoadingInput` / `WesternBlotLoadingResult` / `calculate_western_blot_loading_v1()`：根据蛋白浓度、目标蛋白量、目标上样体积和 loading buffer 倍数估算样品、buffer 和水体积。
- L5C WB/SDS-PAGE 仅为上样体积计算，不进行 WB/凝胶灰度、条带检测、归一化或图像解释。

### 3.2 本地试剂与配方库

- 内置本地科研参考配方。
- 配方按目标体积线性缩放。
- stock-to-working dilution 计算。
- 用户配方草稿确认。
- 用户配方保存在内存结构中，支持 JSON-compatible dict 导出。
- L6B 新增用户确认配方的本地 JSON 持久化：
  - schema 固定为 `labtools_recipe_draft_store.v1`。
  - 仅保存用户确认配方，不保存内置参考配方、网络内容或自动建议。
  - 保存和载入均由用户选择本地 JSON 路径触发；默认不自动写盘。
  - 保存文件采用 no-overwrite 策略，同名文件自动使用 `_001` 等 suffix。
  - 保存/载入前进行基础安全范围检查，阻断高风险化学品、毒物、高风险合成、动物/人体实验或病毒相关草稿。
  - UI 明确“本地草稿，使用前需人工核对 SOP、SDS 和试剂说明书”。
- L6B.1 硬化：
  - 新增 `docs/labtools_recipe_draft_store_schema.md`，记录 `labtools_recipe_draft_store.v1` 顶层字段、recipe 字段、component 字段、导入冲突规则和安全边界。
  - 用户配方列表和 summary 显示草稿 `version`。
  - 载入 JSON 时如果 `recipe_id` 已存在，会 clone 为 `user_recipe_imported_<token>`，保留原有配方不覆盖。
  - UI 显示实际写入数量、`recipe_id` 冲突数和“未覆盖现有用户配方”提示。

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
  - `wound_healing`：划痕实验面积分析，手动 ROI + 用户阈值面积估算 MVP 可用。
  - `cell_counting`：细胞计数，占位，`algorithm_not_available`。
  - `fluorescence_intensity`：荧光强度分析，手动 ROI grayscale 指标 MVP 可用。
  - `densitometry`：灰度 / 墨值分析，占位，`algorithm_not_available`。
- 细胞计数和灰度 / 墨值任务仍为 `algorithm_not_available` 占位状态，不生成 fake 定量结果。

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
- L6A 提供用户确认后的本地导出包：
  - JSON manifest：记录 schema、算法名/版本、manual-review 语义、原图摘要、ROI、指标、warnings、review_notice 和 derived files。
  - CSV summary：写出当前 metrics rows。
  - Markdown 报告片段：写出当前 review fragment。
  - ROI overlay PNG：在原图副本上标出 signal ROI 和 background ROI，不覆盖原图。
- L6A.1 硬化：
  - JSON manifest schema 固定为 `labtools_roi_export_manifest.v1`。
  - manifest 固定包含 `export_type`、`tool_slug`、`tool_label`、`analysis_mode`、`created_at`、`software_channel`、`source_image`、`output_files`、`parameters`、`result_summary`、`review_status`、`safety_note` 和 `generated_files_count`。
  - 导出文件使用 `fluorescence_manual_roi_<timestamp>_<token>` basename，并在同名冲突时自动追加 `_001`、`_002` 等 suffix，避免 silent overwrite。
  - CSV summary 使用稳定 header，包含 schema version、tool slug、review status、measurement id、ROI id、measurement name、value、unit 和 note。
  - Markdown fragment 使用 LabTools manual ROI 辅助分析标题，不包含原图绝对路径，保持人工复核和 testing 语义。
- UI 展示指标表、参数摘要、warning、复核提示和简洁导出预览；只有用户点击“导出当前 ROI 结果”并选择目录后才写盘。
- 默认不自动写盘，不上传图片，不访问网络，不调用 AI Gateway。

### 3.6 划痕实验面积分析

- 使用 Pillow 读取单张本地图片，并转换为 grayscale。
- 用户手动输入 analysis ROI。
- 用户手动输入阈值，范围 0-255。
- 支持 bright / dark 两种划痕候选模式：
  - bright：`pixel >= threshold` 视为 scratch candidate。
  - dark：`pixel <= threshold` 视为 scratch candidate。
- 计算：
  - ROI area pixels
  - scratch area pixels
  - scratch area fraction
  - non-scratch area pixels
  - non-scratch area fraction
  - threshold
  - scratch_mode
- `non_scratch_area_fraction` 可作为 covered / migrated fraction 的计算型指标，但必须标注为“基于阈值的估算”。
- 记录图像文件名、图像尺寸、ROI、threshold、scratch_mode、公式、warnings、review_notice。
- 提供 JSON-compatible dict、CSV-compatible rows/text、Markdown 报告片段字符串。
- L6A 提供用户确认后的本地导出包：
  - JSON manifest：记录 schema、算法名/版本、manual-review / semi-quantitative 语义、原图摘要、ROI、threshold、scratch_mode、指标、warnings、review_notice 和 derived files。
  - CSV summary：写出当前 metrics rows。
  - Markdown 报告片段：写出当前 review fragment。
  - ROI overlay PNG：在原图副本上标出 analysis ROI，不覆盖原图。
- L6A.1 硬化：
  - JSON manifest schema 固定为 `labtools_roi_export_manifest.v1`。
  - `tool_slug` 固定为 `wound_manual_roi_threshold`，`analysis_mode` 固定为 `manual_roi_threshold_area_estimation`。
  - manifest 记录 threshold value / mode、manual ROI 参数、result summary、output file roles 和 manual-review required。
  - 导出文件使用 `wound_manual_roi_threshold_<timestamp>_<token>` basename，并在同名冲突时自动追加 suffix，避免 silent overwrite。
  - CSV summary 使用稳定 header，并记录 threshold value / mode。
  - Markdown fragment 保持 manual-review / semi-quantitative 辅助输出语义，不写成正式实验结论。
- UI 展示图片路径、ROI 输入、阈值输入、亮/暗模式、结果摘要、公式、warning、复核提示和简洁导出预览；只有用户点击“导出当前 ROI 结果”并选择目录后才写盘。
- 默认不自动写盘，不上传图片，不访问网络，不调用 AI Gateway。

### 3.7 实验模板和记录草稿

- L6C 新增 `experiment_templates` 服务层：
  - `ExperimentTemplate`。
  - `ExperimentRecordDraft`。
  - `ExperimentTemplateLibrary`。
  - `create_record_draft()`。
  - `draft_markdown_preview()`。
- 当前内置 5 类轻量结构化模板：
  - qPCR 实验计划模板。
  - Western blot 实验计划模板。
  - 细胞实验接种计划模板。
  - Scratch assay 记录模板。
  - 免疫荧光图像记录模板。
- 每个记录草稿包含：
  - 实验目的。
  - 样本分组。
  - 试剂/材料。
  - 关键参数。
  - 输出文件/记录。
  - 备注。
  - 人工复核提示。
- 草稿 schema：`labtools_experiment_template_draft.v1`。
- 草稿状态：`draft_manual_review_required`。
- UI 提供“实验模板”页面，可选择模板并生成本地 Markdown 预览。
- L6C.1 新增实验记录草稿本地 JSON 持久化：
  - schema 固定为 `labtools_experiment_record_draft_store.v1`。
  - 仅保存用户在当前 UI 中生成的结构化记录草稿。
  - 保存和载入均由用户选择本地 JSON 路径触发；默认不自动写盘。
  - 保存文件采用 no-overwrite 策略，同名文件自动使用 `_001` 等 suffix。
  - 保存/载入前校验草稿 schema、`draft_manual_review_required` 状态、核心字段和人工复核提示。
  - 基础范围检查会阻断人体/动物实验、病毒包装、临床诊断、治疗建议或高风险合成相关草稿。
  - UI 明确“本地结构化草稿，使用前需人工核对 SOP、伦理/安全要求、试剂说明书和实验设计”。
- 当前不自动保存、不写数据库、不生成正式报告、不跨模块传递。
- 当前不做完整 ELN、权限、签名、审计合规或团队协作。

## 4. 当前未实现功能

- 未实现自动 ROI 检测。
- 未实现自动细胞识别。
- 未实现批量分析或批量导出。
- 未实现自动划痕边界识别或全自动迁移效果判断。
- 未实现细胞计数。
- 未实现 WB / 凝胶灰度分析；L5C 只提供 WB/SDS-PAGE 上样体积计算。
- 未实现 ImageJ/Fiji 接入。
- 未实现 OpenCV / scikit-image / imageio / napari / cellpose / stardist 等依赖接入。
- 未实现交互式 ROI 绘制器、在线 overlay 复核或图像预览器；L6A 仅生成用户确认导出的静态 ROI overlay PNG。
- 未启用外部配方网络检索。
- 未实现网页抓取、网页下载、远程来源同步。
- 未调用 AI Gateway 或本地模型进行配方摘录、图像分析或结果解释。
- 未实现 LabTools 本地项目存储、数据库持久化或自动写盘；L6A/L6A.1 仅支持用户确认选择目录后的图像 ROI export package。
- 未实现正式实验报告导出；L6A Markdown 仅为 manual-review 报告片段。
- 未实现完整 ELN、权限、签名、审计合规或团队协作；L6C/L6C.1 只实现轻量实验模板、结构化记录草稿和用户选择路径后的 JSON 草稿持久化。
- 未实现计算器历史记录、CSV/manifest 导出或项目文件写入；L6A CSV/manifest 仅限 fluorescence/wound ROI export package。
- 未实现 recipe center 数据库、自动保存、云同步、网络来源同步或正式 SOP 管理；L6B 仅实现用户选择路径后的本地 JSON 草稿持久化。

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

本 handoff 的测试基线应以最近阶段报告和最终交接为准。L5B 实验计算器中心 v1 后至少运行：

- `python3 - <<'PY' ... from PIL import Image ... PY`
  - 当前 L4C 结果：通过，输出 `Pillow import OK ...`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`
  - 当前 L6B.1 结果：152 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - 当前 L6B.1 结果：153 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q`
  - 当前 L6B.1 结果：18 passed
- `python3 -m app.main --smoke-test`
  - 当前 L6B.1 结果：通过，输出包含 `workspace_entries=3`、`labtools_features=4`
- `python3 -m compileall app/labtools`
  - 当前 L6B.1 结果：通过
- `git diff --check`
  - 当前 L6B.1 结果：通过
- `git diff --cached --check`
  - 当前 L6B.1 提交前运行。

## 7. Shell / UI 接入状态

- LabTools 已接入统一 BioMedPilot Shell。
- LabTools 首页当前四个入口：
  - 实验计算器：可进入；L5B 页面显示“实验计算器中心”，并明确本地辅助计算、人工核对和不替代实验 SOP。
  - 试剂与配方：可进入。
  - 图像定量：可进入；荧光强度分析和划痕实验面积分析为手动 MVP 可用，细胞计数和灰度 / 墨值分析仍为 `algorithm_not_available` 占位。
  - 实验模板：可进入；当前为 qPCR、WB、细胞接种、scratch assay、免疫荧光图像记录的轻量结构化草稿中心。
- `LabToolsWorkspaceWidget.page_keys()` 当前包含：
  - `home`
  - `calculators`
  - `recipes`
  - `image_analysis`
  - `templates`
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

- 当前真实图像算法：
  - `fluorescence_intensity`：手动 ROI 荧光强度分析。
  - `wound_healing`：手动 ROI + 用户阈值划痕面积估算。
- 算法名：
  - `manual_roi_grayscale_fluorescence_v1`
  - `manual_roi_threshold_wound_healing_v1`
- 算法状态：Developer Preview / testing-level measurement assistance。
- 细胞计数和灰度 / 墨值任务必须保持 `algorithm_not_available` 或 draft 占位，不得生成细胞数或 WB/凝胶灰度 fake 数值。
- 荧光分析结果必须显示人工复核提示，不得作为无需复核的实验结论。
- 划痕面积结果必须显示“基于用户 ROI 和阈值的估算”，不得自动判断迁移效果或作为正式实验结论。

## 10. 数据持久化状态

- 计算记录：内存结构 / JSON-compatible dict。
- L5B/L5C 实验计算器 v1 结果：结构化 dataclass 结果和 UI 文本展示；不自动保存、不写 CSV、不写 manifest、不创建项目目录。
- L6C 实验模板记录草稿：结构化 dataclass 结果和 Markdown 预览；不生成正式 ELN。
- L6C.1 实验记录草稿本地 JSON：
  - schema 为 `labtools_experiment_record_draft_store.v1`。
  - 保存只在用户选择 JSON 路径后发生。
  - 载入只在用户选择 JSON 文件后发生。
  - 保存使用 no-overwrite 策略，避免 silent overwrite。
  - 不自动保存、不写数据库、不写历史记录系统、不联网、不调用 AI、不跨模块传递。
- 用户自定义配方：
  - 确认后进入 `UserRecipeStore` 内存结构。
  - L6B 可由用户手动保存为本地 JSON 文件，schema 为 `labtools_recipe_draft_store.v1`。
  - L6B 可由用户手动载入同 schema JSON，并合并到当前 `UserRecipeStore`。
  - L6B.1 显示导入冲突 summary；重复 `recipe_id` 会作为 imported copy 保存，不覆盖现有用户配方。
  - 保存/载入不会自动发生，不写数据库，不联网，不调用 AI。
  - 保存使用 no-overwrite 策略，避免 silent overwrite。
- 来源草稿：手动来源和摘录草稿在 UI / 模型层流转，确认后才进入用户配方 store。
- 图片记录：引用本地路径并生成 `LabImageRecord`，不复制、不上传、不自动写盘。
- 荧光结果导出：
  - 默认只返回 dict、rows/text 或 Markdown 字符串，不自动写盘。
  - L6A 新增 `export_fluorescence_analysis_package()`，仅在调用方传入用户确认的目录后写入 JSON manifest、CSV summary、Markdown 片段和 ROI overlay PNG。
  - L6A.1 固化 schema 为 `labtools_roi_export_manifest.v1`；导出文件 no-overwrite；output_dir 为空或为文件时返回受控错误；UI 取消导出不写盘，失败会显示错误且保留当前分析结果。
- 划痕结果导出：
  - 默认只返回 dict、rows/text 或 Markdown 字符串，不自动写盘。
  - L6A 新增 `export_wound_healing_analysis_package()`，仅在调用方传入用户确认的目录后写入 JSON manifest、CSV summary、Markdown 片段和 ROI overlay PNG。
  - L6A.1 固化 schema 为 `labtools_roi_export_manifest.v1`；导出文件 no-overwrite；CSV summary 稳定记录 threshold value/mode；Markdown fragment 保持 manual-review / semi-quantitative 辅助语义。
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
- 划痕实验面积 MVP 只适合手动 ROI、单张本地图片、用户阈值和亮/暗模式下的候选区域估算。
- 任何真实图像算法都必须记录算法名、版本、参数、ROI、输入 provenance、人工复核提示。
- 图像定量 UI 不得默认显示其它算法的数值结果，除非算法已经实现并通过测试。
- 外部配方来源不得声明为“标准方案”；来源内容必须要求人工核对 SOP、试剂说明书和安全规范。
- 用户数据和图片路径不得自动写盘、上传或跨模块传递。
- 如果测试暴露 Bioinformatics、Meta、Vocabulary、AI Gateway 的业务问题，不要在 LabTools 阶段混入修复，应停止并单独报告。
- 继续开发前应先确认 worktree、分支、`git status --short` 和总开发手册是否有更新。

## 13. 后续推荐路线

1. L6A.2：图像导出 schema 文档化、更多 UI 回归测试和用户选择目录体验微调，但仍不得新增算法。
2. L6C.2：实验记录草稿 Markdown 片段导出体验和导入冲突提示，但仍不做完整 ELN、签名、权限或合规审计。
3. L6B.2：recipe JSON 导入预览/选择性导入，但仍不做数据库、云同步或正式 SOP 管理。
4. 后续单独阶段再评估细胞计数、WB/凝胶灰度、ImageJ/Fiji、OpenCV/scikit-image、网络检索或 AI Gateway。

## 14. Handoff 结论

LabTools 当前已经具备实验计算器、本地配方库、来源草稿框架、图像分析框架入口，以及两个边界清晰的真实图像 MVP：手动 ROI 荧光强度分析、手动 ROI + 阈值划痕面积估算。当前最重要的边界是：细胞计数和 WB/凝胶灰度仍未实现；划痕结果不得自动解释迁移效果；外部来源尚未访问网络；AI Gateway 未调用；用户数据和结果导出默认不自动写盘。后续开发应继续小步阶段化，并在每个真实算法、真实网络能力、AI 能力或持久化能力启用前单独确认授权、测试计划和安全提示。
