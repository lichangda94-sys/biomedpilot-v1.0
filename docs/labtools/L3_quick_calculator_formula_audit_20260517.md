# LabTools L3 Quick Calculator Formula Audit

日期：2026-05-17

用途：审计当前 `LabTools` 开源包中已经具备的 L3 相关快速计算能力、公式、单位、warning 与记录结构，为后续 L3.3 公式驱动动态求解器开发提供边界。

结论先行：

- 当前仓库已经具备 L3 快速计算的核心后端原子能力：浓度换算、稀释计算、溶液配制、单位换算、结果记录模型、试剂模板与本次配制树。
- 当前仓库尚未具备你在问题清单中要求的“公式驱动动态求解器”后端接口，也没有桌面 UI 中的三级导航结构。
- 当前仓库对 L3.3 的最大缺口不在基础公式本身，而在“任意未知项求解、字段级单位约束、统一显示策略、warning policy、完整输入快照”。
- 当前仓库已经部分覆盖 L4.2：Western Blot 上样记录保存、本地 store、Markdown/CSV 导出已存在，剩余缺口主要是 UI 入口、历史列表呈现和桌面工作流接入。

## 1. 审计范围与仓库边界

本仓库是独立 Python package，不是桌面端 UI 工程。当前可以直接审计和实现的是：

- 计算公式与求解接口
- 单位系统与字段约束
- warning policy
- 结果显示格式化逻辑
- calculation record / preparation record 数据结构
- reagent template / preparation workflow 的后端模型
- Western Blot 记录保存与导出

当前无法仅在本仓库内完成的问题：

- “快速计算 / 我的试剂模板 / 配置试剂” 三一级模块的桌面界面重构
- modal / side panel 等前端交互
- 页面级历史列表、按钮层级、卡片布局

这意味着后续任务 B/C 需要上层产品仓库配合；本仓库更适合作为 B/C/D/E 的计算与数据契约层。

## 2. 当前 L3 快速计算能力盘点

### 2.1 已有模块

`labtools/calculators/concentration_calculator.py`

- `convert_concentration`
- `calculate_molar_concentration`
- `calculate_mass_for_molar_solution`

已覆盖公式：

- `mass concentration = molar concentration x molecular weight`
- `moles = mass / molecular weight`
- `molarity = moles / volume`
- `mass = molarity x volume x molecular weight`

当前特点：

- 支持质量浓度与摩尔浓度之间换算
- 支持由质量 + 体积 + MW 求摩尔浓度
- 支持由摩尔浓度 + 体积 + MW 求称量质量

当前限制：

- 不是动态求解器，方向是固定的
- 不能反向求 MW
- 不能在一个统一公式界面里求任意未知项

`labtools/calculators/dilution_calculator.py`

- `calculate_dilution`

已覆盖公式：

- `C1V1 = C2V2`

当前特点：

- 可以把 stock 浓度换算到目标浓度单位后再计算
- 输出所需原液体积与溶剂体积

当前限制：

- 本质上只支持“已知 C1/C2/V2，求 V1”
- 不能求 `C1`、`C2`、`V2`
- 没有“只允许一个未知项”的通用求解接口

`labtools/calculators/solution_preparation_calculator.py`

- `calculate_solution_preparation`

已覆盖公式：

- 质量浓度配制：`mass = C_mass x V`
- 摩尔浓度配制：`mass = C_molar x V x MW`

当前特点：

- 能根据质量浓度或摩尔浓度计算称量质量
- 已有基本 `record_inputs` / `record_outputs`

当前限制：

- 仍是单向计算
- 不能反向求浓度、体积、MW
- 尚未把“溶液配制 / 称量质量”抽象成统一动态公式模块

### 2.2 现有相关但不属于 L3 的模块

以下模块已存在，但根据问题清单不应继续塞进 L3 快速计算器：

- `labtools/calculators/qpcr_mix_calculator.py`
- `labtools/calculators/cell_seeding_calculator.py`
- `labtools/western_blot/*`

这个边界与问题清单第 8 节一致。

## 3. 当前单位系统审计

当前统一单位逻辑在 `labtools/calculators/unit_conversion.py`。

### 3.1 已支持单位

质量：

- `g`
- `mg`
- `µg`
- `ng`

体积：

- `L`
- `mL`
- `µL`

摩尔浓度：

- `M`
- `mM`
- `µM`
- `nM`

质量浓度：

- `mg/mL`
- `µg/µL`
- `µg/mL`
- `ng/mL`
- `ng/µL`

别名兼容：

- `ug` -> `µg`
- `uL` -> `µL`
- `uM` -> `µM`
- `ug/mL` -> `µg/mL`
- `ug/uL` -> `µg/µL`

### 3.2 与需求清单相比的缺口

问题清单要求的 L3.3 单位范围比当前明显更大。

缺少的重点单位：

- 浓度：`g/L`、`%`、`X`、`fold`
- 摩尔浓度：`pM`
- 体积：`nL`
- 物质的量：`mol`、`mmol`、`µmol`、`nmol`、`pmol`

还缺少“字段级单位白名单”这一层逻辑：

- 当前 `canonical_unit` 是全局识别
- 但 L3.3 需要按字段类型限制下拉
- 同一个页面中不能把所有单位混进一个通用列表

## 4. 当前结果显示与 warning policy 审计

### 4.1 数值显示

当前统一显示函数：

- `labtools/calculators/unit_conversion.py::format_number`

当前规则：

- 一般范围内显示最多 6 位小数并去掉尾零
- 极大或极小值自动转科学计数法

当前优点：

- 不会把小值一律粗暴显示为 `0.00`
- 对 CLI / 文本输出足够简单

当前问题：

- 不符合“默认保留 2 位小数”的产品要求
- 不支持千分位显示
- 没有 `0.00282 µg（约 2.82 ng）` 这种双展示
- 没有“当前单位过小，已切换更多有效数字/科学计数法”的显式 warning

### 4.2 warning 现状

L3 快速计算模块当前主要只有通用人工复核提示，缺少产品级实验 warning policy。

已存在的情况：

- `CalculationResult.review_tip`
- qPCR / WB 等模块有少量专用 warning

缺失的情况：

- 低称量 warning 分级
- 低体积 warning 分级
- 结果在当前单位下过小的 warning
- 自动建议“先配 stock 再稀释”

结论：

- 当前 warning 能力是“可复核”，但不是“可操作性分级提示”

## 5. 当前 Calculation Record 审计

当前记录模型在：

- `labtools/calculators/calculation_record.py`
- `labtools/calculators/calculator_models.py`

当前优点：

- 已有统一 `CalculationRecord`
- 支持 `inputs`、`outputs`、`formula`、`warnings`、`review_notice`
- `solution_preparation`、`qpcr_mix`、`cell_seeding` 已写入结构化记录字段

当前缺口：

- `concentration_calculator` 与 `dilution_calculator` 还没有完整 `record_inputs` / `record_outputs`
- 当前记录没有显式区分：
  - 输入值
  - 输入单位
  - 目标单位
  - 结果值
  - warning policy 命中项
  - 求解目标字段
- 当前 `CalculationResult.to_record()` 在缺少结构化 payload 时会退化成 `input_1` / `output_1` 这种弱语义字段

这与问题清单第 3.7 节的要求存在明显差距。

## 6. 当前“我的试剂模板 / 配置试剂”后端审计

### 6.1 已有能力

`labtools/reagent_templates/*` 已经具备：

- 模板模型
- 本地 JSON store
- 模板复制 / 删除 / 读取 / 保存
- 配制请求 `PreparationRequest`
- 配制结果树 `PreparationResult` / `PreparationTreeNode`
- 子模板展开
- pH record
- 溶剂补足
- 初始加液模式
- 循环引用检测
- 阶段性自然语言步骤生成

这部分已经明显超出“纯快速计算器”，是 L3 模板系统的有效后端基线。

### 6.2 当前缺口

与问题清单相比，当前还缺少：

- `addition_order`
- `stage_label`
- 按阶段稳定分组的结构化结果，而不仅是文字步骤
- “配置试剂历史记录” store
- `loss_mode = none / percent / fixed_amount` 的显式建模
- `operator_name`、`notes`、`summary_status`
- `template_snapshot` / `request_snapshot` / `staged_steps` 形式的持久化记录

### 6.3 重要边界判断

问题清单中的任务 B/C 并非从零开始。

当前后端已经有：

- template store
- 本次配制树
- 子模板展开
- pH record
- percent overage

因此 B/C 更像是：

- UI 重构
- preparation record schema 扩展
- “固定损耗量”和“阶段字段”补完

而不是重写整个模板系统。

## 7. 当前 L4.2 审计

问题清单把 L4.2 定义为“WB 上样记录保存与导出”。

本仓库中这部分已经部分实现：

- `labtools/western_blot/models.py`
  - `WBLoadingRecord`
- `labtools/western_blot/store.py`
  - `WBLoadingRecordStore`
- `labtools/western_blot/exporter.py`
  - Markdown / CSV 导出

测试也已经覆盖：

- `tests/test_western_blot_loading_records.py`

结论：

- L4.2 在后端层面不是“待开始”，而是“已具备基础数据能力”
- 剩余工作主要在桌面 UI 接入、列表入口、复制按钮、历史浏览和产品文案

## 8. 当前测试覆盖审计

与 L3 直接相关的现有测试包括：

- `tests/test_concentration_calculator.py`
- `tests/test_dilution_calculator.py`
- `tests/test_solution_preparation_calculator.py`
- `tests/test_unit_conversion.py`
- `tests/test_reagent_templates.py`

当前测试已覆盖：

- 基础公式正确性
- 缺失 MW 报错
- 单位别名
- 零值 / 非法值校验
- 模板 store、pH record、子模板展开、循环引用

当前缺失测试：

- 动态求解器单未知项规则
- 多未知项 / 无未知项报错
- 字段级单位限制
- 低体积 / 低称量 warning 阈值
- 数值显示策略
- calculation record 完整输入快照
- fixed loss amount
- addition_order / stage_label
- preparation history record

## 9. 与问题清单逐项对照

### 9.1 通用试剂计算器三级结构

状态：

- 当前仓库没有 UI 导航层

判断：

- 这是上层产品仓库任务，不是当前包内任务

本仓库应提供的配套：

- 三个一级模块对应的后端服务边界
- 每个模块明确的数据 contract

### 9.2 快速计算模块改为公式驱动动态求解器

状态：

- 公式已大体存在
- 动态求解接口不存在

判断：

- 这是当前仓库最适合直接承接的 L3.3 主任务

### 9.3 摩尔计算开关

状态：

- 当前通过是否传入 MW 间接决定能否做摩尔换算

缺口：

- 没有“mode flag”
- 没有单位白名单切换逻辑

### 9.4 结果显示与 warning policy

状态：

- 有基础格式化
- 无产品级分层 warning

判断：

- 这是 L3.3 的核心配套任务，应该和动态求解器一起做

### 9.5 我的试剂模板

状态：

- 后端模型与 store 已存在
- UI 形态不存在

判断：

- 这是任务 B，后端基础不是阻塞点

### 9.6 添加顺序 / 配制阶段

状态：

- 当前只有初始加液模式和步骤文本
- 没有 `addition_order` / `stage_label`

判断：

- 这是模板系统下一轮模型升级点

### 9.7 配置试剂历史记录

状态：

- 当前没有 preparation record store

判断：

- 这是任务 C 的关键后端缺口

### 9.8 L4.2 保存与导出

状态：

- 后端基础已具备

判断：

- 优先级可低于 L3.3，因为后端不是空白区

## 10. 推荐的仓库内实现拆分

基于当前审计，建议本仓库内按以下顺序推进。

### P0.1 L3.3 求解器核心

建议新增统一求解层，例如：

- `labtools/calculators/formula_solver.py`
- `labtools/calculators/formula_models.py`

第一阶段只做三类公式：

- `mass concentration = molar concentration x MW`
- `C1V1 = C2V2`
- `mass = concentration x volume`
  - 质量浓度模式
  - 摩尔浓度模式

需要具备：

- 单未知项自动求解
- 多未知项报错
- 全部已填时报错
- `unknown_field` 显式指定模式
- 字段级单位约束

### P0.2 统一显示与 warning policy

建议新增一层结果渲染辅助，例如：

- `labtools/calculators/result_formatting.py`

职责：

- 默认 2 位小数
- 极小值保护，不显示为 `0.00`
- 千分位或更可读科学计数法
- 可选自动推荐更小单位
- 低称量 / 低体积 warning 分级

### P0.3 完整 calculation record

建议让所有 L3 快速计算结果都统一写入：

- 输入值
- 输入单位
- 求解目标字段
- 结果值与结果单位
- 公式标识
- warning 命中项
- review_notice

### P1.1 PreparationRequest / PreparationResult 升级

为任务 C 做准备，建议扩展：

- `loss_mode`
- `loss_fixed_amount`
- `loss_fixed_unit`
- `operator_name`
- `notes`

### P1.2 Template component stage fields

为任务 B 做准备，建议在 `ReagentComponent` 中加入：

- `addition_order`
- `stage_label`

并在 preparation result 中保留结构化 stage 分组。

### P1.3 Preparation history store

可参考 WB 记录模型，新增：

- `PreparationRecord`
- `PreparationRecordStore`

## 11. 推荐结论

如果按照问题清单的优先级执行，当前仓库最合理的下一步不是先改 UI，而是先把后端边界补齐。

推荐顺序：

1. 在本仓库完成 L3.3 动态求解器核心、统一显示策略、warning policy、完整 calculation record。
2. 在本仓库完成 `addition_order` / `stage_label` 与 preparation record schema。
3. 再由桌面 UI 仓库接入“三一级模块”结构、模板列表/详情/编辑页和“配置试剂”页面。

一句话总结：

当前 L3 的“公式”问题已经基本具备计算基础，真正缺的是统一求解层与产品化输出层；当前 L4.2 的“保存导出”问题已经具备后端基础，真正缺的是 UI 接入层。
