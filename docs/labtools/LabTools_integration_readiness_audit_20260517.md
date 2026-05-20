# LabTools Integration Readiness Audit

日期：2026-05-17

范围：当前 `LabTools` Python package，不包含 BioMedPilot 私有桌面壳、页面导航、modal、按钮入口或 `.app` 打包产物。

## 1. 审计结论

当前 `LabTools` package 的后端能力可以提交给 integration 作为计算与数据契约层使用。

但它不能单独宣称“完整产品已集成完成”，因为以下内容仍在上层桌面 UI / integration 仓库范围内：

- 通用试剂计算器三一级模块导航：快速计算 / 我的试剂模板 / 配置试剂
- 快速计算公式等式 UI、未知项选择、高亮、结果回填
- 模板列表 / 详情 / 编辑页
- 添加组分 modal 或 side panel
- 配置试剂 Step 1-4 页面流程与历史记录入口
- Western Blot 上样历史列表、复制 Markdown、导出按钮入口
- 桌面 app packaging、LaunchServices/Finder-style launch gate

## 2. 已具备的 integration 后端契约

### 2.1 L3 快速计算

已具备：

- `solve_concentration_bridge`
- `solve_dilution_equation`
- `solve_solution_preparation_formula`
- 单未知项自动识别
- 显式 `unknown_field`
- 多未知项 / 无未知项用户级报错
- 质量浓度、摩尔浓度、分子量、稀释、溶液配制反向求解
- 结构化 `record_inputs` / `record_outputs`

新增给 UI 使用的单位契约：

- `supported_quick_calculator_units(field_type, use_molar_calculation=False)`
- `supported_concentration_units(include_molar=True)`
- `supported_molecular_weight_units()`
- `QUICK_CALCULATOR_FIELD_TYPES`

integration 规则：

- `use_molar_calculation = false` 时，不展示摩尔浓度单位，也不展示 MW 单位。
- `use_molar_calculation = true` 时，允许 M / mM / µM / nM / pM 和 `g/mol`。

### 2.2 L3 我的试剂模板

已具备：

- 模板模型
- 本地 JSON store
- pH 记录
- 自动补足溶剂
- 子模板引用
- 子模板递归展开
- 循环引用检测
- `addition_order`
- `stage_label`
- 阶段分组结果

新增给 UI 使用的组分类型契约：

- `UI_COMPONENT_TYPES`
- `COMPONENT_TYPE_DESCRIPTIONS`
- `normalize_component_type`

兼容 alias：

- `commercial_or_existing_reagent` -> `commercial_reagent`
- `auto_fill_solvent` -> `solvent`

integration 规则：

- UI 可以显示用户友好的 `commercial_or_existing_reagent` 和 `auto_fill_solvent`。
- 进入 store / calculator 前会归一化为当前后端兼容类型。
- `self_prepared_template` 仍是唯一会保留并使用 `referenced_template_id` 的引用类型。

### 2.3 L3 配置试剂

已具备：

- `PreparationRequest.loss_mode`
- `loss_mode = none / percent / fixed_amount`
- `operator_name`
- `notes`
- `PreparationRecord`
- `PreparationRecordStore`
- `template_snapshot`
- `request_snapshot`
- `primary_components`
- `expanded_subtemplates`
- `ph_records`
- `staged_steps`
- `warnings`
- `summary_status`

integration 规则：

- UI 应明确区分 `target_volume` 和 `suggested_volume`。
- 默认 `expand_subtemplates = false`。
- 配置试剂页面不应临时编辑模板组分；需要修改配方时应跳转模板编辑或复制模板。

### 2.4 L4 Western Blot

已具备：

- WB loading record model
- 本地 record store
- Markdown 导出
- CSV 导出

integration 规则：

- 剩余工作是 UI 列表、保存按钮、复制按钮和导出按钮接入。
- 不应把图像分析、条带识别、灰度定量或自动 ROI 放入 L4.2。

## 3. 验证结果

已在当前 checkout 执行：

```bash
./.venv/bin/python -m pytest -q
./.venv/bin/python -m labtools --smoke-test
```

结果：

- `pytest`: `141 passed`
- `smoke-test`: `passed`

## 4. Integration 判定

判定：可以提交给 integration，用作 LabTools 后端包接入。

前提：

- integration 侧把本包视为计算与数据 contract，不把它当作已经完成的桌面 UI。
- integration 侧必须补齐页面导航、表单、modal、历史列表、复制/导出按钮和桌面打包验证。
- 如果 integration 目标是 packaged desktop build，还需要按 BioMedPilot 打包规则执行 LaunchServices/Finder-style launch gate，而不是只跑 Python smoke test。
