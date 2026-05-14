# LabTools Current Development Handoff

日期：2026-05-14

## 1. 当前基线

- 当前 worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- 当前分支：`dev/labtools`
- 当前最近完成阶段：LabTools ImageJ/Fiji status consumer，commit 以当前 git log 为准
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
| LabTools Stage L6D | 最终交接记录 | 新增 LabTools schema index，扩展 ROI export / recipe draft / experiment record draft persistence UI 回归测试，并完成写盘安全审计；不新增 persistence 功能或算法。 |
| LabTools Stage L6A.2 | 当前 git log | 优化 ROI export 用户反馈和目录选择回归测试：成功提示显示导出目录与四类输出，取消/失败均保留当前分析结果，同目录连续导出不覆盖；不新增图像算法。 |
| LabTools Stage L6E | 当前 git log | 审计并校准 LabTools 用户可见状态语义：已实现功能显示为本地辅助/草稿/manual-review MVP，placeholder 功能继续显示占位或未开放；不新增功能。 |
| LabTools Stage L7A | 当前 git log | 优化实验计算器结果复制体验：三个 v1 计算器提供 copyable formatter，UI 每个结果区新增“复制结果”按钮；不新增公式、导出、自动保存或历史记录。 |
| LabTools Stage L7B | 当前 git log | 优化 recipe draft/template 安全边界和导入冲突提示：新增用户可见 safety category，强化 SOP/SDS/pH/储存/有效期/危险性核对提示，确认冲突导入不覆盖。 |
| LabTools Tool Logic Audit 1 | 当前 git log | 暂停新增功能，为当前 calculators、manual ROI image assistance、ROI export、recipe draft、experiment record draft 和 planned placeholders 建立 Tool Logic Cards；新增审计文档和文档覆盖测试，不新增工具、算法、公式、schema、导出格式或 UI 功能。 |
| LabTools Module Architecture Alignment 1 | 当前 git log | 将 LabTools 首页从四个工具集合入口调整为六个一级模块入口：通用计算器、试剂与实验记录、细胞实验、Western Blot、PCR / qPCR、ELISA / 吸光度与标准曲线；仅调整入口、占位语义、文档和测试，不新增算法、schema、persistence 或导出格式。 |
| LabTools Western Blot Module Scaffold 1 | 当前 git log | 建立 Western Blot 模块占位框架，页面包含蛋白样品准备、蛋白浓度测定、上样与胶、电泳 / 转膜 / 抗体孵育流程、结果与灰度分析五个分区；仅新增模块分区、文案、文档和测试，不新增 SDS-PAGE 配胶计算、WB 灰度算法、自动配方推荐、胶浓度推导或持久化。 |
| LabTools SDS-PAGE Gel Template Tool 1 | 当前 git log | 在 Western Blot 模块实现基于用户录入模板的 SDS-PAGE 配胶模板与批量换算工具；支持分离胶/浓缩胶 section、组分备注、默认 3% overage、模板 JSON 导入/导出、冲突跳过/副本导入和本次计算 XLSX 导出；不内置通用配方、不自动推荐胶浓度、不生成配置步骤或 WB 灰度分析。 |
| Western Blot Protein Loading + BCA Assay v1 | 当前 git log | 在 Western Blot 模块实现蛋白上样体系计算器和 BCA 蛋白浓度测定辅助计算 v1；支持多样本上样体积换算、还原剂人工确认提示、BCA 96 孔 OD 矩阵粘贴、Blank/Standard/Sample/Unused 标注、blank 可选扣除、线性拟合、CV/R²/范围警告和复制结果；不做 WB 灰度、Bradford、NanoDrop、ELISA 标准曲线、4PL、plate layout 保存、xlsx 导出、数据库或联网。 |
| LabTools Current Status + ImageJ/Fiji Bridge Planning | 当前 git log | 只更新文档和阶段报告，明确当前已完成工具清单与后续图像路线：现有 Python/Pillow manual ROI MVP 保持 legacy/testing 辅助状态，下一阶段图像分析后端转为 Fiji/ImageJ macro bridge v1；本阶段不新增代码、不新增算法、不接入 Fiji/ImageJ。 |
| LabTools ImageJ/Fiji Bridge v1 | 当前 git log | 实现外部 Fiji/ImageJ executable + LabTools bridge + ImageJ macro 自动化基础设施；支持用户路径配置、本地 JSON 配置、常见路径探测、版本检测、macro smoke test、状态显示和设置页；不新增 WB/gel grayscale、自动 ROI、细胞计数、wound/fluorescence 自动分析、OpenCV/scikit-image、PyImageJ、下载或打包 Fiji/ImageJ。 |
| LabTools ImageJ/Fiji status consumer | 当前 git log | 对齐 Integration `5cda2bc` 的共享 `app.shared.local_engines` 架构，LabTools 不再维护独立 ImageJ/Fiji detection/config 框架；图像相关入口只消费共享状态并显示 contextual setup prompt，非图像 LabTools 功能不受 ImageJ/Fiji 配置影响。 |

## 3. 当前已实现功能

### 3.0 当前已完成工具总览

当前已完成并可从 LabTools UI 或服务层使用的工具 / 草稿能力：

- 通用计算器：浓度换算、C1V1 稀释、溶液配制、称量质量 / 摩尔浓度、细胞接种、qPCR 配液。
- 试剂与实验记录：recipe draft store、recipe JSON import/export、recipe safety category、冲突导入不覆盖、experiment template draft、experiment record draft JSON persistence。
- 图像辅助 legacy MVP：fluorescence manual ROI、wound / scratch manual ROI + threshold、ROI export package。
- 图像后端状态：LabTools 消费共享 `app.shared.local_engines` 的 ImageJ/Fiji 状态；当前不包含具体 ImageJ-backed 图像分析 workflow。
- Western Blot：SDS-PAGE 用户录入模板批量换算、Protein Loading v1、BCA Assay v1。

当前未完成且不得写成已开放的能力：

- 自动 ROI、自动细胞计数、WB / gel grayscale、batch image processing、AI interpretation。
- Bradford、NanoDrop、ELISA standard curve、4PL、qPCR Delta Delta Ct。
- 完整 ELN、正式报告、临床诊断、production-grade 输出。

后续图像路线：

- 共享 ImageJ/Fiji local-engine 基础设施来自 Integration commit `5cda2bc` 的 `app/shared/local_engines`；LabTools 只作为 consumer 读取共享状态并在相关图像入口显示上下文提示。
- 后续图像分析后端路线继续为 Fiji/ImageJ macro bridge：LabTools 负责具体 workflow 的参数表单、输入/输出校验、宏模板选择、运行前预览、结果解析、人工复核提示和 no-overwrite 导出策略。
- 不继续扩大自研 Python 图像算法面；现有 Python/Pillow fluorescence / wound manual ROI MVP 仅作为 legacy/testing 辅助能力保留，后续新增或重做图像工具优先走 Fiji/ImageJ macro bridge。
- 不得在 UI 或文档中把 ImageJ/Fiji bridge 基础设施误写成自动 ROI、细胞计数、WB 灰度、fluorescence 自动分析、wound 自动分析或批处理已经完成。

### 3.1 实验计算器

- 浓度 / 分子量 / 摩尔浓度换算。
- C1V1 = C2V2 稀释计算。
- 溶液配制计算器。
- 细胞接种计算器。
- qPCR 配液计算器。
- `CalculationRecord` 计算记录结构，支持 JSON-compatible dict。
- 中文友好错误提示和人工复核提示。
- L6E 首页和 feature status 文案校准为“本地辅助计算草稿”，避免把计算器描述成正式 SOP、临床建议或生产级结论。
- L5B 新增 `experiment_calculator_center` 结构化 v1 服务层：
  - `DilutionInput` / `DilutionResult` / `calculate_dilution_v1()`：支持同维度浓度单位换算，输出 stock 体积、溶剂体积和 dilution factor。
  - `MassMolarityInput` / `MassMolarityResult` / `calculate_mass_molarity_v1()`：根据分子量、目标摩尔浓度和终体积估算称量质量。
  - `CellSeedingInput` / `CellSeedingResult` / `calculate_cell_seeding_v1()`：根据细胞悬液浓度、目标每孔细胞数、孔数、每孔体积和 overage 估算细胞悬液体积、培养基体积和总需求量。
- L5B v1 结果均为结构化辅助计算草稿，使用前需人工核对，不替代实验 SOP、临床建议或安全操作规范。
- L5C 新增：
  - `QpcrMixInput` / `QpcrMixResult` / `calculate_qpcr_mix_v1()`：输出 qPCR 单反应用量、总用量和 overage 后总用量。
  - `WesternBlotLoadingInput` / `WesternBlotLoadingResult` / `calculate_western_blot_loading_v1()`：根据蛋白浓度、目标蛋白量、目标上样体积和 loading buffer 倍数估算样品、buffer 和水体积。
- L5C WB/SDS-PAGE 旧通用计算器入口已从“通用计算器”UI 移除；Western Blot 模块内的 Protein Loading v1 是当前用户入口。
- L5C 旧服务层保留为历史测试/兼容结构，不作为当前 UI 入口；不进行 WB/凝胶灰度、条带检测、归一化或图像解释。
- SDS-PAGE Gel Template Tool 1 新增：
  - `labtools_sds_page_gel_template_store.v1` 模板 JSON schema。
  - 用户录入 SDS-PAGE 配胶模板，必须包含分离胶和浓缩胶 section；section 可标记为 `0 / 不使用`。
  - 每个 section 支持用户填写组分名称、每块胶用量、单位和备注。
  - 支持单位：`µL`、`mL`、`mg`、`g`。
  - 胶厚度默认下拉：`0.75 mm`、`1.0 mm`、`1.5 mm`。
  - 孔数默认下拉：`10 wells`、`12 wells`、`15 wells`。
  - 批量换算公式：`total_amount = amount_per_gel × gel_count × (1 + overage_percent / 100)`，默认 overage 为 3%。
  - 支持导出单个模板 JSON、导入模板 JSON，导入冲突只允许跳过或作为副本导入，不覆盖已有模板。
  - 支持导出本次计算 `.xlsx`，包含 `Summary`、`分离胶`、`浓缩胶` 三个 sheet。
  - UI 明确“基于用户录入的试剂盒/实验室模板进行批量换算”和“结果为实验辅助计算草稿，使用前请按试剂盒说明书和实验室 SOP 人工核对”。
- SDS-PAGE Gel Template Tool 1 不内置通用配方、不自动推荐胶浓度、不自动推导胶浓度、不生成配置步骤、不做 WB 灰度分析、不做蛋白浓度分析。
- Western Blot Protein Loading + BCA Assay v1 新增：
  - `app/labtools/western_blot/protein_loading.py`：多样本蛋白上样体系辅助计算，支持 `µg/µL`、`ug/uL`、`mg/mL`、`µg/mL`、`ug/mL` 浓度单位；`µg/µL` 与 `mg/mL` 等价。
  - Loading buffer 体积按 `最终上样体积 × 目标终浓度 ÷ Loading buffer 倍数` 计算；蛋白样品体积按 `目标每孔蛋白量 ÷ 蛋白样品浓度` 计算；补水体积为最终体积扣除样品和 buffer。
  - 默认 overage 为 3%；总量按每个样本单独计算后汇总并乘以 overage。
  - UI 和复制文本包含还原剂提示：需确认 loading buffer 是否已包含 DTT、β-ME 或其他还原剂。
  - `app/labtools/western_blot/bca_assay.py`：BCA 蛋白浓度测定辅助计算 v1，支持 8×12 OD 矩阵解析、96 孔板标注、批量选区标注、blank 可选扣除、线性标准曲线拟合和样本浓度估算。
  - BCA v1 仅做线性拟合，不做 4PL；CV% 警告阈值为 15%，R² 警告阈值为 0.98；异常孔只提示，不自动剔除。
  - Protein loading 和 BCA 结果均支持复制摘要文本，不写盘、不自动保存、不新增 schema。
  - 按用户确认，不保留旧通用计算器 WB 上样入口；上样体系只从 Western Blot 模块进入。
- Western Blot Protein Loading + BCA Assay v1 明确未做：
  - 不做 WB/gel grayscale、条带 ROI、背景扣除、target/loading control ratio。
  - 不做 Bradford、NanoDrop、ELISA 标准曲线、4PL、plate layout 模板保存或 xlsx 导出。
  - 不新增 AI/network、数据库、自动保存或 dist/desktop app 改动。
- L7A 新增结果复制体验：
  - `format_dilution_copy_text()`、`format_mass_molarity_copy_text()`、`format_cell_seeding_copy_text()` 生成用户可复制文本。
  - copyable text 包含工具名称、输入摘要、计算结果、单位和“实验辅助计算草稿，不替代实验 SOP”人工核对提示。
  - 计算器 UI 每个结果区有“复制结果”按钮；无有效结果或 invalid 输入时禁用，成功计算后启用。
  - 点击复制只写系统 clipboard，不写文件、不保存历史、不生成 JSON/CSV/manifest。
- L6D 新增 `docs/labtools_schema_index.md`，统一记录 LabTools 当前 schema / JSON-compatible 结构、用途、字段、用户语义、公开分享风险、本地路径风险和 draft / auxiliary / local persistence 边界。
- Tool Logic Audit 1 新增 `docs/labtools_tool_logic_audit.md`，为 dilution、mass/molarity、cell seeding、qPCR、WB loading、fluorescence manual ROI、wound manual ROI、ROI export、recipe draft、experiment record draft 和 planned placeholder 工具建立 Tool Logic Cards；不新增公式、schema 或导出格式。

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
- L6E 首页和 feature status 文案校准为“本地草稿 / 用户配方草稿”，继续强调 SOP/SDS 人工核对和非正式 SOP 边界。
- L7B 安全边界 polish：
  - recipe draft store payload 增加 `safety_category`：`routine_buffer_draft` / `user_verified_only` / `requires_lab_sop_review`。
  - UI 明确本地草稿使用前需按实验室 SOP、SDS、试剂说明书人工核对浓度、pH、储存条件、有效期和危险性。
  - UI 明确不构成安全操作规范、不自动适配所有实验。
  - 导入冲突继续显示冲突数量，冲突项作为 imported copy 导入，不覆盖现有用户配方。
  - failed import 不清空现有用户配方。

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
- 当前 fluorescence / wound 的 Python/Pillow 实现是 legacy/testing manual ROI MVP，不作为后续图像后端扩展方向。
- 后续图像分析后端路线改为 Fiji/ImageJ macro bridge；新增图像能力应优先通过宏桥接调用可审计的 Fiji/ImageJ macro，而不是继续扩展 LabTools 内部自研图像算法。
- 细胞计数和灰度 / 墨值任务仍为 `algorithm_not_available` 占位状态，不生成 fake 定量结果。
- L6E 回归测试固定图像分析 UI 语义：
  - fluorescence 和 wound 仅显示 manual ROI / threshold MVP 与人工复核。
  - cell counting、grayscale / ink-value 继续显示 `algorithm_not_available` 占位。
  - 不把 automatic ROI、automatic cell counting、WB / gel grayscale 或 batch image processing 描述为已完成。

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
- L6A.2 UI 回归硬化：
  - 导出成功后 UI 明确显示“导出成功”、用户选择的导出目录、JSON manifest、CSV summary、Markdown fragment、ROI overlay PNG、Developer Preview / testing 和人工复核提示。
  - 用户取消目录选择时不写盘、不显示成功，当前分析结果仍保留，导出按钮保持可用。
  - 导出失败时显示可读错误，不暴露 traceback，不清空当前分析结果，导出按钮状态保持可用。
  - 同一目录连续导出会继续使用 no-overwrite 文件命名策略，第一次导出文件仍保留。
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
- L6A.2 UI 回归硬化：
  - 导出成功后 UI 明确显示导出目录和 JSON manifest / CSV summary / Markdown fragment / ROI overlay PNG 四类输出。
  - 取消目录选择或导出失败均不清空当前 wound 结果，不写成成功状态。
  - 同目录重复导出保持非覆盖策略，使用 suffix / token 文件名避免 silent overwrite。
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
- L6E 首页和 feature status 文案校准为“草稿中心 / 不是完整 ELN”，并用 UI 回归测试固定 non-ELN 语义。

## 4. 当前未实现功能

- 未实现自动 ROI 检测。
- 未实现自动细胞识别。
- 未实现批量分析或批量导出。
- 未实现自动划痕边界识别或全自动迁移效果判断。
- 未实现细胞计数。
- 未实现 WB / 凝胶灰度分析；L5C 只提供 WB/SDS-PAGE 上样体积计算，SDS-PAGE Gel Template Tool 1 只提供用户录入模板的批量换算。
- 未实现 SDS-PAGE 通用配方库、自动配方推荐、胶浓度自动推导或配置步骤生成。
- 已实现 ImageJ/Fiji bridge v1 基础设施；未实现任何基于 Fiji/ImageJ 的具体图像分析 workflow。
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
- 不得在未授权阶段扩展具体 ImageJ/Fiji macro workflow 或图像定量算法。
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
  - 当前 SDS-PAGE Gel Template Tool 1 结果：173 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - 当前 SDS-PAGE Gel Template Tool 1 结果：186 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q`
  - 当前 SDS-PAGE Gel Template Tool 1 结果：18 passed
- `python3 -m app.main --smoke-test`
  - 当前 SDS-PAGE Gel Template Tool 1 结果：通过，输出包含 `workspace_entries=3`、`labtools_features=6`
- `python3 -m compileall app/labtools`
  - 当前 SDS-PAGE Gel Template Tool 1 结果：通过
- `git diff --check`
  - 当前 SDS-PAGE Gel Template Tool 1 结果：通过
- `git diff --cached --check`
  - 当前 SDS-PAGE Gel Template Tool 1 结果：通过

## 7. Shell / UI 接入状态

- LabTools 已接入统一 BioMedPilot Shell。
- Module Architecture Alignment 1 后，LabTools 首页当前六个一级入口：
  - 通用计算器：用于浓度、分子量、质量、体积、稀释、称量和后续 pH/酸碱度等通用试剂计算；现有 dilution、mass/molarity 和通用试剂计算归入此入口。
  - 试剂与实验记录：用于本地 recipe 草稿、实验记录草稿、模板保存和 JSON 导入导出；不等同于完整 ELN；现有 recipe draft、recipe import/export、experiment template draft 和 experiment record draft JSON persistence 后续归入此模块。
  - 细胞实验：用于细胞接种、活率、Transwell、wound healing、增殖率、台盼蓝、Alamar Blue 等；当前为规划中 / 待确认使用逻辑 / 暂未开放，cell seeding 和 wound manual ROI 未来归入此模块。
  - Western Blot：用于蛋白样品准备、蛋白浓度测定入口、上样体系、SDS-PAGE 配胶、电泳/转膜参数、抗体孵育流程和后续灰度分析；当前已有模块页面，上样与胶区域包含 SDS-PAGE 配胶模板与批量换算工具。
  - PCR / qPCR：用于 PCR/qPCR 体系计算、运行参数、plate layout、Ct / ΔCt / ΔΔCt 结果分析；当前为规划中 / 待确认使用逻辑 / 暂未开放，qPCR mix 未来归入此模块。
  - ELISA / 吸光度与标准曲线：用于 OD 值、标准曲线、BCA、Bradford、NanoDrop、ELISA 样本浓度反推等；当前为规划中 / 待确认使用逻辑 / 暂未开放。
- fluorescence manual ROI 暂时标记为图像辅助能力，后续归属待单独确认。
- `LabToolsWorkspaceWidget.page_keys()` 当前包含：
  - `home`
  - `general_calculators`
  - `reagent_records`
  - `cell_experiments`
  - `western_blot`
  - `pcr_qpcr`
  - `elisa_absorbance`
- LabTools 不再在 header 提供显著的 ImageJ/Fiji 设置入口；ImageJ/Fiji 状态只在 Western Blot 结果与灰度分析、图像分析 manual ROI / planned image workflow 等相关区域显示。
- 全局 UX 按“架构上统一，体验上按需”对齐：ImageJ/Fiji 由具体图像 workflow 进入或触发时检测，缺失时显示上下文 setup prompt；若未来存在共享 `设置 > 本地工具与模型` 页面，LabTools 可提供导航 hook。
- Module Architecture Alignment 阶段只完成顶层入口结构、模块占位页、文案、文档和测试；未新增算法、未新增实验结果分析、未新增图像处理、未新增 schema、未新增 persistence。
- Western Blot 模块页面包含：
  - 蛋白样品准备。
  - 蛋白浓度测定。
  - 上样与胶，包含 planned 子入口“蛋白上样体系计算”和已实现的“SDS-PAGE 配胶模板与批量配制”工具。
  - 电泳 / 转膜 / 抗体孵育流程。
  - 结果与灰度分析。
- 未开放区域仍标记为待确认使用逻辑 / 规划中 / 暂未开放；SDS-PAGE 工具仅基于用户录入模板进行批量换算。
- 普通用户界面应继续保持中文友好，不暴露 traceback、内部 schema、内部 id 或大量调试细节。
- UI 必须继续使用 BioMedPilot 统一 UI token，不引入 LabTools 独立主题色。

## 8. 外部网络、AI Gateway、ImageJ/Fiji 状态

- 外部网络：未启用。
- 配方外部来源：只支持手动录入来源草稿；不抓取网页，不下载网页内容。
- AI Gateway：未调用。
- 本地模型：未调用；Ollama/local LLM 属于本地环境能力，不等同于云端付费 AI，不应走积分、会员或 cloud API key 权益。
- ImageJ/Fiji：LabTools 消费共享 `app.shared.local_engines` 状态。共享层支持本机路径配置、常见路径探测、版本检测和 macro smoke test；LabTools 当前只显示相关状态和上下文 setup prompt，不拥有全局 local-engine 架构。
- OpenCV / scikit-image：未接入，且不作为当前推荐后端路线。
- Pillow：已作为 L4B 最小图片读取依赖接入。

任何启用网络、AI Gateway、真实本地模型调用、OpenCV 或 scikit-image 的任务，都必须作为单独阶段明确授权，并重新设计安全边界和测试计划。后续基于 ImageJ/Fiji bridge 开发具体图像工具时，仍必须单独确认 Tool Logic Card，不得顺带开发新定量算法。

Local tools/models UX alignment:

- 统一本地工具/模型管理可以在共享架构层实现，但普通用户体验必须按功能触发。
- 不新增 LabTools 主屏大型本地引擎配置中心。
- ImageJ/Fiji 缺失时，由具体图像 workflow 解释所需工具、用途、是否可 fallback，并提供检测、路径选择或安装指南。
- LabTools 不应独立实现与 Bioinformatics/Meta 重复的 local LLM 或 local engine 权益逻辑。

## 9. 图像分析后端路线

- 当前 legacy/testing 图像 MVP：
  - `fluorescence_intensity`：手动 ROI 荧光强度分析。
  - `wound_healing`：手动 ROI + 用户阈值划痕面积估算。
- 现有 legacy 算法名：
  - `manual_roi_grayscale_fluorescence_v1`
  - `manual_roi_threshold_wound_healing_v1`
- 状态：Developer Preview / testing-level measurement assistance；不作为后续图像算法扩展路线。
- 后续后端路线：Fiji/ImageJ macro bridge。全局本地引擎 detection/config/status 由共享 `app.shared.local_engines` 承担；后续具体工具中，LabTools 只负责图像 workflow 的宏桥接消费、参数和文件校验、结果解析、人工复核提示、provenance 记录和导出安全；图像定量逻辑应由明确版本的 Fiji/ImageJ macro 承载。
- ImageJ/Fiji 是本地图像分析后端，不是云端 AI、积分能力或会员权益；不得静默下载、静默安装或在用户未进入/触发 workflow 时静默运行 macro。
- 共享 local-engine 层记录推荐版本、检测版本、可用性、最后验证时间和错误摘要；LabTools 不重复实现该检测逻辑。
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
- SDS-PAGE 配胶模板 JSON：
  - schema 为 `labtools_sds_page_gel_template_store.v1`。
  - 仅保存用户录入模板，不保存通用配方库或自动推荐内容。
  - 保存只在用户选择 JSON 路径后发生；不自动保存、不进数据库、不云同步。
  - 导入前校验 schema；同名或同 `template_id` 冲突时只允许跳过或作为副本导入，不覆盖已有模板。
- SDS-PAGE 本次计算 XLSX：
  - 只导出 `.xlsx`。
  - 仅保存本次批量换算结果，不是模板 schema。
  - workbook 包含 `Summary`、`分离胶`、`浓缩胶` 三个 sheet。
  - 导出只在用户选择 XLSX 路径后发生。
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
- L6D persistence safety audit 覆盖：
  - `export_fluorescence_analysis_package()`。
  - `export_wound_healing_analysis_package()`。
  - `save_user_recipe_store()` / `load_user_recipe_store()`。
  - `save_experiment_draft_store()` / `load_experiment_draft_store()`。
  - 对应 UI handlers。
- L6D 确认现有写盘路径仍保持用户触发、无自动保存、无 silent overwrite、失败可见、schema version 存在和 draft/manual-review/auxiliary 语义。

后续如需保存用户实验数据，必须先设计本地项目存储策略、用户选择位置、隐私边界、审计字段和迁移/清理规则。

## 10.1 Tool Logic Audit 1 结论

当前结论：后续涉及结果生成、实验解释、图像自动分析、正式记录或报告形态的工具，必须先讨论使用逻辑并补 Tool Logic Card，再进入开发。

现有需要用户确认的工具：

- dilution / mass-molarity / cell seeding calculators。
- qPCR mix calculator。
- Western Blot protein loading calculator。
- fluorescence manual ROI。
- wound / scratch manual ROI + threshold。
- ROI export result summary。
- recipe draft fields、safety category 和 import/export 语义。
- experiment template draft fields 和 experiment record draft JSON persistence 语义。

未来开发前必须先做 Tool Logic Card 的工具：

- absorbance / OD calculation。
- protein concentration / BCA / Bradford / NanoDrop。
- wound healing full workflow。
- Transwell assay。
- WB / gel grayscale。
- cell counting。
- qPCR Delta Delta Ct。
- ELISA standard curve。
- automatic ROI。
- AI interpretation。
- formal report-ready result。
- full ELN。
- batch image processing。

Tool Logic Audit 1 未新增算法、未新增功能、未新增 schema、未新增 persistence、未新增导出格式、未修改 Bioinformatics / Meta / ReleaseBuild / MainLine / dist / desktop app。

## 10.2 Module Architecture Alignment 1 结论

LabTools 顶层入口已从“工具合集”调整为“少量大模块入口”。当前 UI 只完成入口结构和占位页语义，不代表细胞实验、Western Blot、PCR/qPCR、ELISA/吸光度等实验特异性算法已经开放。

当前归类结论：

- 通用计算器只长期承载浓度、分子量、质量、体积、稀释、称量和后续 pH/酸碱度等通用试剂计算；不再长期承载全部实验特异性计算。
- 试剂与实验记录承载 recipe draft、recipe import/export、experiment template draft 和 experiment record draft JSON persistence 语义，但仍不是完整 ELN。
- cell seeding、wound manual ROI 未来归入细胞实验。
- qPCR mix 未来归入 PCR / qPCR。
- WB loading、SDS-PAGE 未来归入 Western Blot。
- fluorescence manual ROI 暂保持图像辅助能力，后续归属待确认。
- absorbance / OD、protein concentration、wound healing full workflow、Transwell、WB / gel grayscale、cell counting、qPCR Delta Delta Ct、ELISA standard curve 等仍必须先做 Tool Logic Card，再进入开发。

本阶段未新增算法、未新增实验结果分析、未新增图像处理、未新增 schema、未新增 persistence、未新增导出格式、未修改 Bioinformatics / Meta / ReleaseBuild / MainLine / dist / desktop app。

## 10.3 Western Blot Module Scaffold 1 结论

Western Blot 模块页已建立五个占位分区：

- 蛋白样品准备：用于记录蛋白提取、裂解液/抑制剂草稿、样本分组和实验室自定义流程，当前只是流程模板入口。
- 蛋白浓度测定：提供 BCA、Bradford、NanoDrop 等蛋白浓度测定入口，底层逻辑后续与吸光度/标准曲线能力复用。
- 上样与胶：包含 planned 子入口“蛋白上样体系计算”和“SDS-PAGE 配胶模板与批量配制”。
- 电泳 / 转膜 / 抗体孵育流程：用于记录参数和步骤模板，用户可录入试剂盒说明书或实验室成熟流程。
- 结果与灰度分析：用于后续 WB/gel grayscale、条带 ROI、背景扣除、target/loading control ratio 和结果导出，但开发前必须单独确认图像分析逻辑。

本阶段未新增 WB 灰度分析、未新增 SDS-PAGE 配胶计算逻辑、未新增自动配方推荐、未新增胶浓度自动推导、未新增 SOP、未新增数据库或自动保存。

## 10.4 SDS-PAGE Gel Template Tool 1 结论

SDS-PAGE 配胶模板与批量配制工具已实现，范围限定为用户录入模板的批量换算：

- 模板包含 `template_id`、`template_name`、`template_version`、胶浓度、胶厚度、孔数、胶格式/备注、试剂盒或实验室模板来源、创建/更新时间、review status、safety note、分离胶 section 和浓缩胶 section。
- 分离胶 / 浓缩胶 section 均支持 `0 / 不使用`；至少需要一个有效 section。
- 每个组分包含名称、每块胶用量、单位和备注。
- 支持单位：`µL`、`mL`、`mg`、`g`。
- 默认 overage 为 3%，批量计算公式为 `total_amount = amount_per_gel × gel_count × (1 + overage_percent / 100)`。
- JSON 导出用于模板备份/迁移/共享；JSON 导入会校验 schema，冲突只允许跳过或作为副本导入。
- XLSX 导出只包含本次计算结果，sheet 为 `Summary`、`分离胶`、`浓缩胶`。

本工具不内置通用配方、不自动推荐配方、不自动推导胶浓度、不生成配置步骤、不做 WB 灰度分析、不做蛋白浓度分析、不联网、不调用 AI、不自动保存。

## 11. 跨模块边界

- Bioinformatics：不得修改业务逻辑，不得写入 Bioinformatics 项目结构，不得混入 LabTools 计算器、配方或图像分析任务。
- Meta Analysis：不得修改业务逻辑，不得混入 LabTools 配方、图像分析或实验记录。
- Vocabulary：不得修改业务逻辑；如未来需要共享术语，必须作为独立共享词表阶段设计。
- AI Gateway：不得绕过；任何模型调用必须走 AI Gateway 且默认禁用，需要单独授权。
- MainLine：不得在 LabTools feature 阶段直接修改；后续进入 MainLine 需经 Integration 或等价验证流程。
- 本地工具与模型：LabTools 不得重复实现一套独立 local engine / local model 权益逻辑；当前已复用共享 local engine status/config，并保持按功能触发的 UX。

## 12. 风险点和开发注意事项

- 图像分析是高风险增长点：必须避免把占位结果、草稿状态或后端未接入状态表述成实验结果。
- 荧光 ROI MVP 只适合手动 ROI、单张本地图片、grayscale 统计和背景扣除；后续重做或扩展应走 Fiji/ImageJ macro bridge。
- 划痕实验面积 MVP 只适合手动 ROI、单张本地图片、用户阈值和亮/暗模式下的候选区域估算；后续 wound healing workflow 应走 Fiji/ImageJ macro bridge。
- 任何图像结果都必须记录后端、宏名/版本、参数、ROI、输入 provenance、人工复核提示。
- 图像定量 UI 不得默认显示其它算法的数值结果，除非算法已经实现并通过测试。
- 外部配方来源不得声明为“标准方案”；来源内容必须要求人工核对 SOP、试剂说明书和安全规范。
- 用户数据和图片路径不得自动写盘、上传或跨模块传递。
- 如果测试暴露 Bioinformatics、Meta、Vocabulary、AI Gateway 的业务问题，不要在 LabTools 阶段混入修复，应停止并单独报告。
- 继续开发前应先确认 worktree、分支、`git status --short` 和总开发手册是否有更新。

## 13. 后续推荐路线

1. 为 Priority 1 现有结果语义工具补用户确认版 Tool Logic Cards：dilution / mass-molarity / cell seeding calculators、fluorescence manual ROI、wound manual ROI + threshold、ROI export summary。
2. 为 recipe draft 和 experiment record draft 补字段、安全边界、非 ELN 语义确认。
3. 下一阶段推荐：为第一个具体 ImageJ/Fiji-backed macro workflow 设计 Tool Logic Card，优先讨论按功能触发的依赖检测、输入文件、macro 参数、输出 CSV/JSON 字段、provenance、人工复核语义和 no-overwrite 导出策略。
4. 为 SDS-PAGE 配胶模板工具补更多 UI 导入预览交互 polish，但仍不做自动配方推荐或胶浓度推导。
5. 为 Western Blot 后续工具继续补 Tool Logic Cards：WB/gel grayscale 必须基于 Fiji/ImageJ macro bridge 设计。
6. 后续单独阶段再评估细胞计数、WB/凝胶灰度、批处理、网络检索或 AI Gateway；图像能力优先走 Fiji/ImageJ macro bridge，不优先接 OpenCV/scikit-image。

## 14. Handoff 结论

LabTools 当前已经具备通用计算器、recipe / record draft、来源草稿框架、图像分析框架入口、SDS-PAGE 用户模板批量换算工具、Western Blot Protein Loading v1、BCA Assay v1，并已作为 consumer 连接共享 ImageJ/Fiji local-engine 状态。现有两个 legacy/testing 图像 MVP 仍为手动 ROI 荧光强度分析和手动 ROI + 阈值划痕面积估算。顶层入口现已调整为六个大模块，Western Blot 模块已有五个分区；其中 SDS-PAGE 配胶模板工具只基于用户录入模板计算，不内置通用配方、不推导胶浓度、不推荐配方、不生成配置步骤。后续具体图像分析工具应通过共享 ImageJ/Fiji 状态和 macro bridge 设计；WB 灰度分析、细胞计数、自动 ROI、fluorescence 自动分析、wound 自动分析和批处理仍未实现；划痕结果不得自动解释迁移效果；外部来源尚未访问网络；AI Gateway 未调用；用户数据和结果导出默认不自动写盘。
