# LabTools UI Integration Contract

日期：2026-05-22

范围：当前 `LabTools` Python package 的桌面 UI 调用契约。本文只固化 public API、数据模型、状态边界和 UI 接入规则；不新增复杂业务功能，不处理打包或 LaunchServices，不声明 LabTools 已完整产品化。

## 1. Contract 边界

当前 LabTools 是 BioMedPilot 桌面 UI 可调用的后端能力包，主要提供：

- 计算函数
- dataclass 输入 / 输出模型
- 公式展示元数据
- 试剂模板与记录模型
- 本地 JSON store
- 部分 Markdown / CSV / XLSX / JSON 导出

当前 LabTools 不提供：

- 桌面页面、导航、modal、side panel
- Qt / PySide view model
- BioMedPilot storage root adapter
- 用户级导出文件选择器
- ImageJ/Fiji 外部引擎调用
- ELISA 完整标准曲线 UI 后端
- packaged desktop validation

## 2. API 状态标签

| 标签 | 含义 |
|---|---|
| `stable_for_ui` | 可以作为桌面 UI 的后端契约接入；仍需 UI adapter 做表单、错误展示和保存动作。 |
| `testing_only` | 单元测试覆盖并可用于 mockup 或内部验证，但还不建议直接作为正式 UI 主入口。 |
| `internal_only` | 低层实现或持久化细节，UI 不应直接依赖；应经 adapter 包装。 |
| `planned_shell_only` | 目前只适合做页面壳、入口、空状态或外部引擎状态展示。 |
| `deprecated_or_not_for_ui` | 仍可保留兼容或测试，但桌面 UI 应使用更明确的新契约。 |

## 3. Public API Inventory

### 3.1 Root package: `labtools`

| API | 状态 | UI 用法 |
|---|---|---|
| `__version__` | `stable_for_ui` | About / diagnostics 显示版本。 |
| `smoke_test()` | `testing_only` | 集成 smoke/diagnostics，不作为业务页面入口。 |
| `CalculationError` | `stable_for_ui` | adapter 捕获并显示用户级错误。 |
| `CalculationResult` | `stable_for_ui` | 动态公式求解结果容器，可生成记录。 |
| `CalculationRecord` | `stable_for_ui` | 通用计算历史的基础记录模型；当前缺少统一 record store。 |
| `CALCULATION_REVIEW_NOTICE` | `stable_for_ui` | 通用计算复核提示。 |
| `LOW_MASS_WARNING`, `LOW_VOLUME_WARNING`, `TINY_VALUE_WARNING` | `stable_for_ui` | UI warning 文案来源。 |

### 3.2 Formula display contract: `labtools.calculators.formula_specs`

| API | 状态 | UI 用法 |
|---|---|---|
| `FormulaSpec` | `stable_for_ui` | 高级公式求解页面的公式元数据。 |
| `FormulaFieldSpec` | `stable_for_ui` | 自动渲染字段、默认单位、helper text。 |
| `FormulaSolveTargetSpec` | `stable_for_ui` | 渲染“求解目标” segmented control。 |
| `FormulaExampleSpec` | `stable_for_ui` | 示例卡片。 |
| `QuickCalculatorTaskSpec` | `stable_for_ui` | 快速计算任务卡片元数据。 |
| `FORMULA_SPECS` | `stable_for_ui` | 公式注册表，只读使用。 |
| `QUICK_CALCULATOR_TASKS` | `stable_for_ui` | 快速计算任务注册表，只读使用。 |
| `FORMULA_RESULT_SECTIONS` | `stable_for_ui` | 公式结果区布局约定。 |
| `QUICK_TASK_RESULT_SECTIONS` | `stable_for_ui` | 快速计算结果区布局约定。 |
| `list_formula_specs()` | `stable_for_ui` | 生成公式列表。 |
| `get_formula_spec(spec_id)` | `stable_for_ui` | 加载单个公式页面配置。 |
| `list_quick_calculator_tasks()` | `stable_for_ui` | 生成快速计算首页任务卡。 |
| `get_quick_calculator_task(task_id)` | `stable_for_ui` | 加载单个快速计算表单配置。 |
| `supported_units_for_formula_field(field)` | `stable_for_ui` | 字段级单位下拉。 |

### 3.3 General calculators: `labtools.calculators`

| API | 状态 | UI 用法 |
|---|---|---|
| `DilutionInput`, `DilutionResult`, `calculate_dilution_v1()` | `stable_for_ui` | 快速稀释卡片。 |
| `MassMolarityInput`, `MassMolarityResult`, `calculate_mass_molarity_v1()` | `stable_for_ui` | 摩尔浓度称量卡片。 |
| `CellSeedingInput`, `CellSeedingResult`, `calculate_cell_seeding_v1()` | `stable_for_ui` | 细胞铺板快速计算。 |
| `QpcrMixInput`, `QpcrMixResult`, `calculate_qpcr_mix_v1()` | `stable_for_ui` | qPCR mix 快速计算。 |
| `WesternBlotLoadingInput`, `WesternBlotLoadingResult`, `calculate_western_blot_loading_v1()` | `stable_for_ui` | 简化 WB 上样快速计算；完整 WB 应优先用 `calculate_wb_loading()`。 |
| `format_dilution_copy_text()` | `stable_for_ui` | 复制稀释结果。 |
| `format_mass_molarity_copy_text()` | `stable_for_ui` | 复制称量结果。 |
| `format_cell_seeding_copy_text()` | `stable_for_ui` | 复制细胞铺板结果。 |
| `solve_concentration_bridge()` | `stable_for_ui` | 高级公式求解。 |
| `solve_dilution_equation()` | `stable_for_ui` | 高级公式求解。 |
| `solve_stock_working_solution()` | `stable_for_ui` | 高级公式求解 / 快速配 working solution。 |
| `solve_solution_preparation_formula()` | `stable_for_ui` | 高级溶液配制。 |
| `solve_percent_solution()` | `stable_for_ui` | 百分比溶液。 |
| `calculate_serial_dilution()` | `stable_for_ui` | 梯度稀释表。 |
| `supported_quick_calculator_units()` | `stable_for_ui` | 快速计算字段单位选择。 |
| `supported_concentration_units()` | `stable_for_ui` | adapter 构造单位菜单。 |
| `supported_mass_units()` | `stable_for_ui` | adapter 构造单位菜单。 |
| `supported_volume_units()` | `stable_for_ui` | adapter 构造单位菜单。 |
| `supported_amount_units()` | `stable_for_ui` | adapter 构造单位菜单。 |
| `supported_molecular_weight_units()` | `stable_for_ui` | adapter 构造单位菜单。 |
| `convert_mass_concentration_unit()` | `stable_for_ui` | 质量浓度单位换算。 |
| `convert_concentration()` | `deprecated_or_not_for_ui` | 老式直接换算；新 UI 优先用公式求解或 task spec。 |
| `calculate_dilution()` | `deprecated_or_not_for_ui` | 老式固定方向稀释；新 UI 优先 `calculate_dilution_v1()` 或 `solve_dilution_equation()`。 |
| `calculate_solution_preparation()` | `deprecated_or_not_for_ui` | 老式固定方向配制；新 UI 优先 `solve_solution_preparation_formula()`。 |
| `calculate_molar_concentration()` | `testing_only` | 可用于内部校验；不建议直接暴露为单独页面。 |
| `calculate_mass_for_molar_solution()` | `testing_only` | 可用于内部校验；快速 UI 优先 `calculate_mass_molarity_v1()`。 |
| `calculate_cell_seeding()` | `deprecated_or_not_for_ui` | 老式 cell seeding helper；新 UI 用 `calculate_cell_seeding_v1()`。 |
| `calculate_qpcr_mix()` | `deprecated_or_not_for_ui` | 老式 qPCR helper；新 UI 用 `calculate_qpcr_mix_v1()`。 |

### 3.4 Reagent templates: `labtools.reagent_templates`

| API | 状态 | UI 用法 |
|---|---|---|
| `ReagentTemplate`, `ReagentComponent`, `CommercialReagentInfo`, `PHRecord` | `stable_for_ui` | 模板编辑和详情展示。 |
| `PreparationRequest` | `stable_for_ui` | 本次试剂配制输入模型。 |
| `PreparationResult`, `PreparationTreeNode`, `PreparationComponentResult`, `PreparationStageGroup` | `stable_for_ui` | 配制结果、子模板展开、阶段分组。 |
| `PreparationRecord`, `PreparationRecordStore` | `stable_for_ui` | 配制历史保存、读取、删除。 |
| `ReagentTemplateStore` | `stable_for_ui` | 模板列表、保存、复制、删除；建议经 BioMedPilot storage adapter 传入 path。 |
| `calculate_preparation()` | `stable_for_ui` | 本次试剂配制计算。 |
| `detect_template_cycles()` | `internal_only` | store / adapter 层校验，不直接给终端用户按钮调用。 |
| `normalize_component_type()` | `stable_for_ui` | UI 类型 alias 转后端类型。 |
| `UI_COMPONENT_TYPES`, `COMPONENT_TYPE_DESCRIPTIONS` | `stable_for_ui` | 模板编辑组件类型选项。 |
| `COMPONENT_TYPES`, `COMPONENT_TYPE_ALIASES` | `testing_only` | adapter 可读，页面不直接显示。 |
| schema constants | `stable_for_ui` | migration / diagnostics。 |

### 3.5 Western Blot: `labtools.western_blot`

| API | 状态 | UI 用法 |
|---|---|---|
| `WBLoadingConfig`, `WBSampleInput`, `WBLoadingResult`, `WBLoadingResultRow`, `WBLane` | `stable_for_ui` | 完整 WB loading calculator 页面。 |
| `calculate_wb_loading()` | `stable_for_ui` | 完整 WB 上样计算，包括 lane layout。 |
| `WBLoadingRecord`, `WBLoadingRecordStore` | `stable_for_ui` | WB 上样历史。 |
| `wb_loading_record_markdown()`, `wb_loading_record_csv()` | `stable_for_ui` | 复制 / 预览导出内容。 |
| `export_wb_loading_record_markdown()`, `export_wb_loading_record_csv()` | `stable_for_ui` | 文件导出；需要 UI file picker adapter。 |
| `result_summary_status()` | `stable_for_ui` | 历史列表状态 badge。 |
| `SdsPageGelTemplate`, `GelSection`, `GelComponent` | `stable_for_ui` | SDS-PAGE 配胶模板编辑。 |
| `SdsPageGelCalculationInput`, `SdsPageGelCalculationResult` | `stable_for_ui` | 配胶计算。 |
| `SdsPageGelTemplateStore` | `testing_only` | 目前是内存 store；正式 UI 需要本地持久化 adapter。 |
| `calculate_sds_page_gel_batch()` | `stable_for_ui` | SDS-PAGE 多胶批量计算。 |
| `save_sds_page_gel_template_json()`, `load_sds_page_gel_template_json()` | `stable_for_ui` | 模板导入/导出。 |
| `save_sds_page_gel_calculation_xlsx()` | `stable_for_ui` | 配胶结果 XLSX 导出；需要 file picker adapter。 |
| `BcaPlateMatrix`, `BcaWellAnnotation`, `BcaAnalysisResult` | `testing_only` | BCA / OD mockup 和 MVP 可用；缺少 record store。 |
| `parse_bca_od_matrix()`, `annotate_well()`, `annotate_well_range()`, `analyze_bca_assay()` | `testing_only` | BCA / OD MVP 计算；需要 UI adapter 和 history model。 |
| `calculate_protein_loading()` and protein loading dataclasses | `testing_only` | 可作为 WB 子模块或内部 helper；主 UI 先用 `calculate_wb_loading()`。 |

### 3.6 Domain namespaces

| Namespace | 状态 | UI 用法 |
|---|---|---|
| `labtools.pcr_qpcr` | `stable_for_ui` | 目前只公开 qPCR mix。 |
| `labtools.cell_culture` | `stable_for_ui` | 公开 cell seeding，并开放细胞图片实验 ImageJ/Fiji macro 工作流。 |
| `labtools.elisa` | `planned_shell_only` | 仅预留命名空间，`__all__` 为空。 |
| ImageJ/Fiji APIs | `adapter_ready_for_cell_image_workflows` | 可用于划痕实验、Transwell、迁移 / 划痕 ROI、免疫组化图片处理的 macro 生成和 ImageJ/Fiji 调用；实验记录保存仍未接。 |

## 4. UI 调用规则

1. 桌面 UI 不应 import 下划线函数或未列入模块 `__all__` 的 helper。
2. 快速计算入口优先使用 `list_quick_calculator_tasks()` 生成任务卡，再绑定对应 `calculator_name`。
3. 高级公式求解入口优先使用 `list_formula_specs()` 生成公式列表，并用 `default_solve_target` 和 `solve_targets` 渲染求解目标。
4. 所有用户输入必须在 UI adapter 层先转为对应 dataclass 或 solver keyword arguments，再调用后端。
5. 所有 `CalculationError`、`ReagentTemplateError`、`WBLoadingCalculatorError`、`BcaAssayError`、`SdsPageGelTemplateError` 应作为用户级错误展示。
6. 所有 `warnings`、`review_notice`、`review_tip` 必须在结果区显示，不应隐藏。
7. Store 类应由 BioMedPilot adapter 传入明确 path，避免直接写到默认 `~/.labtools`。
8. 文件导出 API 只负责写文件；UI 负责文件选择、覆盖确认和权限提示。

## 5. 当前验证基线

用户输入中记录的旧基线是：

- `python3 -m pytest`: `217 passed`
- `python3 -m labtools --smoke-test`: passed

当前 checkout 已新增公式展示元数据测试，本阶段验证结果为：

- `python3 -m pytest -q`: `151 passed`
- `python3 -m labtools --smoke-test`: passed
