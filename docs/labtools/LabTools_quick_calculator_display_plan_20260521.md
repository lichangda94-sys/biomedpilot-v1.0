# LabTools 快速计算与动态公式求解展示方案

日期：2026-05-21

范围：当前 `LabTools` Python package 的通用计算器后端契约与未来桌面 UI 展示方案。本文不声明桌面 UI 已完成。

## 1. 设计结论

通用计算器建议拆成两种入口：

1. 快速计算：面向明确实验任务，默认给用户最短路径。
2. 公式求解：面向需要反推变量的高级模式，明确选择“求解目标”。

后端新增 `labtools.calculators.formula_specs` 作为展示元数据层。现有 solver 继续负责计算，新元数据层负责告诉 UI：

- 展示哪些计算任务
- 每个任务需要哪些字段
- 每个字段属于哪类单位
- 哪些字段可以作为求解目标
- 结果区应该如何分块
- 示例和说明如何呈现

## 2. 快速计算模式

快速计算不应该先展示公式大表单，而应该先展示任务卡片。

建议一级任务：

- 稀释配液
- 摩尔浓度称量
- 溶液配制
- qPCR Mix
- 细胞铺板
- WB 上样

后端契约：

- `list_quick_calculator_tasks()`
- `get_quick_calculator_task(task_id)`
- `QUICK_CALCULATOR_TASKS`

每个任务返回：

- `task_id`
- `title`
- `category`
- `calculator_name`
- `description`
- `primary_result_label`
- `input_field_ids`
- `result_sections`

UI 建议：

1. 用户先选任务卡片。
2. 页面只展示当前任务需要的字段。
3. 主结果突出显示，次要结果放在下面。
4. 固定显示 warning 和人工复核提示。
5. 结果动作只放“复制”和“保存记录”，不要在快速计算里塞高级公式编辑。

## 3. 动态公式求解模式

动态公式求解不建议依赖“留空哪个字段就算哪个字段”作为主要交互。更清晰的方式是让用户显式选择求解目标。

示例：稀释方程

```text
公式：C1 x V1 = C2 x V2

求解目标：
[原液体积 V1] [原液浓度 C1] [目标浓度 C2] [终体积 V2]

已知条件：
原液浓度 C1: 100 mM
目标浓度 C2: 10 mM
终体积 V2: 1 mL

结果：
原液体积 V1 = 100 µL
补足溶剂 = 900 µL
稀释倍数 = 10x
```

后端契约：

- `list_formula_specs()`
- `get_formula_spec(spec_id)`
- `supported_units_for_formula_field(field)`
- `FORMULA_SPECS`

首批公式：

- `concentration_bridge`
- `dilution_c1v1`
- `stock_working_solution`
- `solution_preparation`
- `percent_solution`
- `serial_dilution`

## 4. 推荐页面结构

通用计算器建议结构：

```text
通用计算器
  快速计算
    任务卡片
    简化表单
    主结果
    复制 / 保存

  公式求解
    公式列表
    求解目标 segmented control
    已知条件表单
    公式与代入过程
    主结果与 warning

  历史记录
    计算记录列表
    复制 / 删除 / 导出
```

## 5. 结果展示规范

快速计算结果区：

- `input_summary`
- `primary_result`
- `secondary_results`
- `warnings`
- `copy_or_save`
- `review_notice`

公式求解结果区：

- `input_summary`
- `equation`
- `substitution`
- `primary_result`
- `warnings`
- `review_notice`

展示原则：

- 主结果必须比公式和输入更醒目。
- 公式和代入过程用于复核，不应该遮住主结果。
- warning 不要和错误混在一起；错误阻止生成结果，warning 提醒人工复核。
- 对低体积、低称量、极小值显示、目标浓度高于 stock 等场景保留后端 warning。

## 6. Integration 注意事项

- 当前仓库只提供后端契约，不包含桌面 UI。
- UI 可以直接读取 `FormulaSpec.to_dict()` 和 `QuickCalculatorTaskSpec.to_dict()` 生成页面配置。
- `calculator_name` 是 integration 层绑定现有计算函数的桥，不是让终端用户看到的文字。
- 快速计算和高级公式求解应共享同一套 solver，不要在 UI 里重复实现公式。
- 后续如果新增计算器，优先新增 solver 测试，再把展示元数据注册到 `FORMULA_SPECS` 或 `QUICK_CALCULATOR_TASKS`。
