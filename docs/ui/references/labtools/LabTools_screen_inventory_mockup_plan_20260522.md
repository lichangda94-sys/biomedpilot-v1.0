# LabTools Screen Inventory and Mockup Plan

日期：2026-05-22

范围：基于当前 LabTools 后端能力，为 BioMedPilot 桌面 UI 固化页面清单、后端绑定、保存/导出/历史需求和 mockup 优先级。本文不包含实际 UI 实现。

## 1. Screen 状态定义

| 状态 | 含义 |
|---|---|
| `active_backend_ready` | 后端计算或数据模型已可接入 UI。 |
| `ui_adapter_needed` | 后端可用，但需要桌面 adapter 处理表单、路径、保存、导出或错误展示。 |
| `mockup_only` | 可先做视觉和交互 mockup，不应接真实业务承诺。 |
| `shell_only` | 只能做入口、空状态、外部依赖状态或占位说明。 |
| `blocked_until_backend` | 需要先补后端模型或 store。 |

## 2. Screen Inventory

| screen_id | screen_name | backend_api | input_model | output_model | warning_policy | save_needed | export_needed | history_needed | empty_state_needed | modal_or_side_panel_needed | priority | UI 状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `labtools_home` | LabTools 首页 | `list_quick_calculator_tasks`, `list_formula_specs` | none | task/spec list | show feature status badges | no | no | no | yes | no | P0 | `ui_adapter_needed` |
| `quick_calculator` | 通用快速计算 | `list_quick_calculator_tasks`, calculator by `calculator_name` | task-specific dataclass or kwargs | task-specific result | show `warnings`, `review_tip`, user errors | yes | copy first; export later | yes | yes | no | P0 | `active_backend_ready` + `ui_adapter_needed` |
| `formula_solver` | 动态公式求解 | `list_formula_specs`, solver by `solver_name`, `supported_units_for_formula_field` | solver kwargs | `CalculationResult` | show equation, substitution, warnings, review tip | yes | copy first; export later | yes | yes | no | P0 | `active_backend_ready` + `ui_adapter_needed` |
| `calculation_history` | 通用计算历史 | `CalculationRecord` | record filters | record list | show status from warnings | yes | planned | yes | yes | optional detail panel | P1 | `blocked_until_backend` |
| `reagent_template_list` | 试剂模板列表 | `ReagentTemplateStore.list_templates` | store path | `tuple[ReagentTemplate]` | template validation errors | yes | JSON planned via adapter | yes | yes | detail side panel | P0 | `active_backend_ready` + `ui_adapter_needed` |
| `reagent_template_editor` | 模板编辑 modal / side panel | `ReagentTemplate`, `ReagentComponent`, `PHRecord`, `ReagentTemplateStore.upsert_template` | template fields | `ReagentTemplate` | show component validation, cycle/reference errors | yes | no | no | yes | yes | P0 | `active_backend_ready` + `ui_adapter_needed` |
| `reagent_component_editor` | 组分编辑 modal / side panel | `UI_COMPONENT_TYPES`, `COMPONENT_TYPE_DESCRIPTIONS`, `normalize_component_type` | component fields | `ReagentComponent` | show unit/type/reference validation | yes | no | no | yes | yes | P1 | `active_backend_ready` + `ui_adapter_needed` |
| `reagent_preparation_run` | 本次试剂配制 | `calculate_preparation`, `PreparationRequest` | `PreparationRequest` + templates | `PreparationResult` | show `warnings`, pH, staged steps, review notice | yes | copy first; export later | yes | yes | optional template picker side panel | P0 | `active_backend_ready` + `ui_adapter_needed` |
| `reagent_preparation_history` | 配制记录历史 | `PreparationRecordStore` | store path, filters | `tuple[PreparationRecord]` | show `summary_status` | yes | planned | yes | yes | detail side panel | P1 | `active_backend_ready` + `ui_adapter_needed` |
| `wb_loading_calculator` | WB loading calculator | `calculate_wb_loading`, `WBLoadingConfig`, `WBSampleInput` | config + sample rows | `WBLoadingResult` | row errors, lane warnings, review notice | yes | Markdown / CSV | yes | yes | sample row editor optional | P0 | `active_backend_ready` + `ui_adapter_needed` |
| `wb_loading_history` | WB 上样历史 | `WBLoadingRecordStore`, `wb_loading_record_markdown`, `wb_loading_record_csv` | store path, filters | `tuple[WBLoadingRecord]` | show `summary_status` | yes | Markdown / CSV | yes | yes | detail side panel | P1 | `active_backend_ready` + `ui_adapter_needed` |
| `sds_page_gel` | SDS-PAGE 配胶 | `calculate_sds_page_gel_batch`, `SdsPageGelTemplate`, `save_sds_page_gel_calculation_xlsx` | `SdsPageGelCalculationInput` | `SdsPageGelCalculationResult` | show safety/review/context notices | template save needed | XLSX, template JSON | template history needed | yes | template editor side panel | P0 | `active_backend_ready` + `ui_adapter_needed` |
| `sds_page_template_import_export` | SDS-PAGE 模板导入导出 | `load_sds_page_gel_template_json`, `save_sds_page_gel_template_json`, `SdsPageGelTemplateStore` | file path, template | import result / path | show conflict and non-overwrite errors | yes | JSON | yes | yes | modal | P1 | `ui_adapter_needed` |
| `bca_od_record` | BCA / OD 记录 | `parse_bca_od_matrix`, `annotate_well`, `annotate_well_range`, `analyze_bca_assay` | OD matrix text + annotations | `BcaAnalysisResult` | low R2, high CV, negative corrected OD, out of range | yes | copy first; CSV later | yes | yes | annotation side panel | P0 | `mockup_only` to `ui_adapter_needed` |
| `qpcr_mix` | qPCR Mix | `calculate_qpcr_mix_v1`, `QpcrMixInput` | `QpcrMixInput` | `QpcrMixResult` | water zero, invalid volume, review notice | yes | copy first | yes | yes | no | P1 | `active_backend_ready` + `ui_adapter_needed` |
| `cell_plating` | 细胞铺板 | `calculate_cell_seeding_v1`, `CellSeedingInput` | `CellSeedingInput` | `CellSeedingResult` | density/volume validation, review notice | yes | copy first | yes | yes | no | P1 | `active_backend_ready` + `ui_adapter_needed` |
| `cell_experiment_records_home` | 细胞实验记录模板首页 | none | none | none | display planned scope, no calculation claims | no | no | yes later | yes | template picker later | P0 | `shell_only` |
| `elisa_absorbance` | ELISA / 吸光度 | none in `labtools.elisa` | none | none | no analytical claims | no | no | yes later | yes | no | P1 | `blocked_until_backend` |
| `imagej_fiji_entry` | ImageJ/Fiji 图像分析入口 | none | external engine status later | status only | no image analysis claims | no | no | no | yes | settings modal later | P1 | `shell_only` |

## 3. P0 Mockup 建议

### 3.1 LabTools 首页

目标：实验工具中控台，不做营销页。

布局建议：

- 左侧或顶部模块导航：快速计算、公式求解、试剂模板、本次配制、Western Blot、SDS-PAGE、BCA/OD、细胞实验记录。
- 主区显示最近使用、P0 工具入口、后端状态 badge。
- planned / shell 页面必须标明“后端规划中”或“外部引擎未连接”，避免用户误解为已可用。

### 3.2 通用快速计算

目标：任务优先，低认知负担。

优先任务卡：

- 稀释配液
- 摩尔浓度称量
- 溶液配制
- qPCR Mix
- 细胞铺板
- WB 上样简化版

结果区：

- 主结果
- 次要结果
- warning
- 复制 / 保存
- 人工复核提示

### 3.3 动态公式求解

目标：高级用户反推变量。

交互建议：

- 左侧公式列表来自 `list_formula_specs()`。
- 顶部显示公式，例如 `C1 x V1 = C2 x V2`。
- 求解目标用 segmented control，不依赖“留空字段”作为主要交互。
- 结果显示公式、代入过程、主结果、warnings。

### 3.4 试剂模板列表

目标：管理可复用模板。

必备状态：

- 空状态：暂无模板，提供“新建模板”和“导入示例”入口。
- 列表字段：名称、默认体积、默认强度、组分数、pH、更新时间。
- 行动作：详情、复制、删除。

### 3.5 模板编辑 modal / side panel

目标：编辑模板元数据和组分。

建议使用 side panel：

- 基本信息
- 组分列表
- 添加/编辑组分 modal
- pH 记录
- 阶段和添加顺序
- 保存前运行后端校验

### 3.6 本次试剂配制

目标：从模板生成本次配制结果。

流程：

1. 选择模板。
2. 输入目标体积、目标强度、损耗模式、operator、notes。
3. 运行 `calculate_preparation()`。
4. 展示目标体积和建议制备体积的区别。
5. 保存为 `PreparationRecord`。

### 3.7 WB loading calculator

目标：完整 WB 上样体系和 lane layout。

页面应包含：

- 配置区：目标蛋白量、终体积、loading buffer、还原剂、marker、lane count。
- 样本表：样本名、浓度、备注。
- 结果：纵向样本明细、横向 lane layout、summary status。
- 操作：保存记录、复制 Markdown、导出 CSV/Markdown。

### 3.8 SDS-PAGE 配胶

目标：配胶模板和批量配制。

页面应包含：

- 模板选择 / 编辑
- resolving gel section
- stacking gel section
- gel count 和 overage
- 结果表
- 导出 XLSX
- 模板 JSON 导入/导出

### 3.9 BCA / OD 记录

目标：BCA MVP mockup，先做 OD matrix + annotation + linear fit。

页面应包含：

- 8 x 12 OD 粘贴区
- well annotation side panel
- 标准品 / 样本表
- 线性拟合摘要
- warnings：low R2、high CV、out of range、negative corrected OD

当前缺少 record store，P0 mockup 可以做；正式 UI 保存需要先补历史模型。

### 3.10 细胞实验记录模板首页

目标：仅做记录模板入口和空状态。

当前只有 cell seeding calculator 后端，没有细胞实验记录 store。P0 只能做 shell：

- 细胞铺板计算入口
- 未来记录模板占位
- 空状态说明
- 不提供真实记录保存承诺

## 4. Mockup 优先级

| 优先级 | 页面 |
|---|---|
| P0 | LabTools 首页、通用快速计算、动态公式求解、试剂模板列表、模板编辑 side panel、本次试剂配制、WB loading calculator、SDS-PAGE 配胶、BCA / OD 记录、细胞实验记录模板首页 |
| P1 | 通用计算历史、配制记录历史、WB 上样历史、SDS-PAGE 模板导入导出、qPCR Mix 独立页、细胞铺板独立页、ELISA / 吸光度 shell、ImageJ/Fiji 入口 |
| P2 | qPCR plate setup、cell experiment record store、ELISA MVP、ImageJ/Fiji external engine adapter |

## 5. Screen 级接入原则

- P0 mockup 可以先覆盖视觉和交互框架，但只有 `active_backend_ready` 页面可以接真实计算。
- `shell_only` 页面必须显示空状态，不能显示伪结果。
- 需要保存的页面必须先决定 BioMedPilot storage root adapter。
- 所有导出按钮都必须经过桌面 file picker adapter，不直接让用户输入路径。
- 每个页面都应保留人工复核提示区域。
