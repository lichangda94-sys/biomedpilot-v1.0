# LabTools 整改后报告

日期：2026-05-17

依据文档：

- `docs/labtools/L3_quick_calculator_formula_audit_20260517.md`
- `/Users/changdali/Desktop/LabTools_Actual_Use_Issue_List_for_Codex_20260516.md`

## 1. 本次整改目标

本次整改聚焦当前 `LabTools` Python package 在仓库内可以直接落地的后端层能力，不涉及桌面 UI 仓库中的页面结构、卡片布局、modal 或导航重构。

整改目标分为三组：

1. L3 快速计算器后端补齐
2. L3 模板与配置试剂数据结构补齐
3. 配套测试与整改验证

## 2. 已完成整改项

### 2.1 新增 L3 公式驱动动态求解器

新增文件：

- `labtools/calculators/formula_solver.py`

已新增接口：

- `solve_concentration_bridge`
- `solve_dilution_equation`
- `solve_solution_preparation_formula`

已实现能力：

- 支持“只保留一个未知项”的动态求解规则
- 自动识别唯一空字段作为未知项
- 多未知项时报错
- 全字段已填时报错
- 稀释公式支持 `C1V1 = C2V2` 的动态求解
- 浓度桥接支持质量浓度、摩尔浓度、分子量三者间反向求解
- 溶液配制支持质量、浓度、体积，以及摩尔模式下 MW 的动态求解

### 2.2 扩展单位系统

整改文件：

- `labtools/calculators/unit_conversion.py`

新增支持：

- 体积：`nL`
- 摩尔浓度：`pM`
- 质量浓度：`g/L`
- 比例浓度：`%`、`X`、`fold`
- 物质的量：`mol`、`mmol`、`µmol`、`nmol`、`pmol`

新增能力：

- 比例浓度基准换算
- 物质的量单位换算
- 更多单位别名归一化

### 2.3 新增统一显示与 warning policy

新增文件：

- `labtools/calculators/result_formatting.py`

已实现能力：

- 默认更接近产品要求的结果显示
- 极小值不再退化为 `0.00`
- 大数支持千分位显示
- 对极小质量/体积结果优先给出更可读展示
- 新增低称量 warning
- 新增低体积 warning
- 新增当前单位过小 warning

整改效果示例：

- `0.00282 µg（约 2.82 ng）`
- 对低移液体积给出“不建议直接移取”的 warning
- 对低称量质量给出“建议先配 stock 再稀释”的 warning

### 2.4 旧计算接口已补结构化记录

整改文件：

- `labtools/calculators/concentration_calculator.py`
- `labtools/calculators/dilution_calculator.py`
- `labtools/calculators/solution_preparation_calculator.py`

已补齐：

- `record_inputs`
- `record_outputs`
- warning 透传

这次整改后，旧 API 即使不切到动态求解器，也能输出更完整的结构化记录。

### 2.5 模板系统新增 addition_order / stage_label

整改文件：

- `labtools/reagent_templates/models.py`
- `labtools/reagent_templates/calculator.py`

已实现能力：

- `ReagentComponent` 新增 `addition_order`
- `ReagentComponent` 新增 `stage_label`
- `PreparationComponentResult` 保留阶段字段
- `PreparationTreeNode` 新增结构化 `stage_groups`
- `PreparationResult` 新增 `direct_stage_groups`
- `as_text()` 输出中新增按阶段分组展示
- 通用步骤中新增阶段执行提示

整改后效果：

- 同一阶段组分会按 `addition_order` 聚合
- 主模板结果和子模板展开都能保留阶段分组信息

### 2.6 配置试剂支持固定损耗量

整改文件：

- `labtools/reagent_templates/models.py`
- `labtools/reagent_templates/calculator.py`

已新增请求字段：

- `loss_mode`
- `loss_percent`
- `loss_fixed_amount`
- `loss_fixed_unit`
- `operator_name`
- `notes`

已实现逻辑：

- 兼容旧的 `overage_percent`
- 新增 `fixed_amount` 固定损耗量模式
- 内部自动折算为建议配制体积

### 2.7 新增配置试剂历史记录模型与 store

新增文件：

- `labtools/reagent_templates/preparation_record.py`
- `labtools/reagent_templates/preparation_record_store.py`

已实现能力：

- `PreparationRecord`
- `PreparationRecordStore`
- 本地 JSON 持久化
- `template_snapshot`
- `request_snapshot`
- `primary_components`
- `expanded_subtemplates`
- `ph_records`
- `staged_steps`
- `warnings`
- `review_notice`
- `summary_status`

这使 L3 “配置试剂”模块在后端层面已经具备“生成后保存历史记录”的基础能力。

## 3. 已补测试

新增测试：

- `tests/test_formula_solver.py`

扩展测试：

- `tests/test_unit_conversion.py`
- `tests/test_calculation_record.py`
- `tests/test_reagent_templates.py`

本次新增覆盖点：

- 动态求解器单未知项求解
- 多未知项报错
- 极小值显示与 warning
- 新单位换算
- `addition_order / stage_label` 阶段分组
- 固定损耗量模式
- `PreparationRecordStore` 读写与坏 JSON 处理

## 4. 当前仍未在本仓库落地的项

这些项属于上层产品或桌面 UI 仓库范围，本次未在当前 Python package 内直接实现：

- “快速计算 / 我的试剂模板 / 配置试剂” 三个一级模块的桌面导航重构
- 模板列表页 / 详情页 / 编辑页 UI
- 添加组分 modal / side panel
- 配置试剂页面的 Step 1-4 交互流
- Western Blot 历史记录列表页面与按钮入口

说明：

当前仓库已经为上述 UI 工作补齐了所需的主要后端契约层，但 UI 入口本身仍需在上层仓库接入。

## 5. 验证结果

本次整改完成后，已执行：

```bash
./.venv/bin/python -m pytest -q
./.venv/bin/python -m labtools --smoke-test
```

结果：

- `pytest`: `133 passed`
- `smoke-test`: `passed`

## 6. 整改结论

本次整改已经把文档中最关键、且当前仓库能够独立落地的后端缺口补齐：

- L3 动态求解器已具备
- 统一显示/warning policy 已具备
- 模板阶段字段已具备
- 配置试剂历史记录已具备
- 固定损耗量模式已具备

当前 `LabTools` 包已经从“若干独立计算函数 + 模板换算”提升为“可被上层 UI 直接接入的 L3 后端能力层”。
