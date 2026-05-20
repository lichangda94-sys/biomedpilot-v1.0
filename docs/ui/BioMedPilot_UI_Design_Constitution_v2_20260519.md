# BioMedPilot / 萤火虫 UI 设计宪法 v2

日期：2026-05-19
适用范围：BioMedPilot / 医研智析 / 萤火虫 全局 UI、Figma 设计、Codex UI 开发、UIShell 收敛、模块 UI 重构
文件性质：上位 UI 设计原则与 UI 治理规范，不是具体页面实现任务

---

## 0. 文件目的

本文件用于统一 BioMedPilot / 萤火虫 后续所有界面设计、Figma 原型、Codex UI 开发、UIShell 收敛和模块重构原则。

它的作用不是规定某一个按钮的具体位置，而是规定：

- 这个软件应该被设计成什么类型的软件；
- 所有模块 UI 应遵循什么基本逻辑；
- 当前阶段为什么需要 UI Freeze / UI Consolidation；
- 如何处理历史 UI 设计资产；
- 如何判断一个 UI 页面是否真实可运行；
- 哪些能力不能被误画、误写或误导性展示；
- Figma 设计和 Codex 开发应如何保持一致；
- LabTools、Bioinformatics、Meta Analysis、UIShell 等复杂模块应如何避免界面继续扩张和混乱。

后续所有 UI 相关任务，包括 Figma 设计、Codex 页面重构、模块首页设计、计算器页面设计、实验记录页面设计、报告页面设计、UIShell 清理、历史页面合并，都应优先遵守本文件。

---

## 1. 软件类型定义

BioMedPilot / 萤火虫 不是普通工具箱软件，不是网页 SaaS 后台，不是 AI 聊天软件，也不是医疗诊断软件。

它应被定义为：

> 面向生物医学科研人员的本地桌面端科研工作流软件。

它具有以下属性：

1. **科研工作流软件**
   用户需要经历导入、配置、检查、确认、分析、记录、导出等连续步骤。

2. **专业生产力软件**
   用户是医学科研人员、PhD、实验人员、转化医学研究者、生信分析用户和 Meta 分析用户。
   用户可以接受一定复杂度，但不能接受状态混乱、边界不清、结果不可复核。

3. **本地桌面软件**
   软件运行在本地桌面环境中。UI 不应被设计成网页后台、营销落地页或云 SaaS 控制台。

4. **多模块科研平台**
   Bioinformatics、Meta Analysis、LabTools、Settings、External Engines、Testing Mode 属于同一套科研工作台，不是几个互不相关的小工具。

5. **Developer Preview / Internal Beta 阶段产品**
   当前 UI 必须持续区分 stable、MVP、testing、developer preview、placeholder、planned、out-of-v1.0、runtime blocked、shell-only、historical UI asset。
   不能把测试级功能、历史页面或不可运行页面画成正式科研结论能力。

---

## 2. 当前阶段的核心判断

当前项目已经积累了较多历史 UI 设计、阶段报告、页面代码和图标资源。
这说明 UI 设计有沉淀，但也带来了新风险：

- 历史 UI 页面与当前真实运行时状态可能不一致；
- 旧阶段报告中的通过状态不等于当前 HEAD 可运行；
- 页面代码存在不等于当前 workspace 能挂载；
- 测试被 skip 不等于测试通过；
- shell-only 模块不能被表现为完整 runtime；
- placeholder / planned 功能不能继续抢占主流程；
- LabTools 等模块如果继续快速叠加入口，会造成界面失控；
- Figma 高保真和图标资源如果早于真实页面结构完成，会制造虚假成熟感。

因此，当前阶段不适合继续进行大范围 UI 扩张。
更合理的策略是进入：

> UI Freeze / UI Consolidation / UI Baseline Reset
> UI 结构冻结、清理合并与新基线阶段

这不是停止所有开发，而是暂停结构性 UI 扩张，先整理出一个简洁、真实、可运行、可继续开发的新 UI 基线。

---

## 3. 总体设计目标

BioMedPilot / 萤火虫 的 UI 设计目标不是“炫酷”，而是：

> 让复杂科研流程变得可理解、可操作、可复核、可继续。

所有界面设计应服务于以下目标：

1. **降低科研重复劳动**
   - 减少重复填写；
   - 支持从历史记录继续；
   - 支持模板、记录、导出；
   - 支持结构化管理数据和实验过程。

2. **让用户知道下一步**
   - 每个流程页面必须显示当前状态；
   - 明确下一步操作；
   - 明确阻塞项；
   - 明确哪些项目需要人工确认。

3. **让结果可追溯**
   - 显示结果来源；
   - 显示输入条件；
   - 显示人工复核状态；
   - 显示导出内容；
   - 保留必要技术详情，但不干扰主界面。

4. **保护用户预期**
   - 明确哪些功能可用；
   - 明确哪些功能只是 testing；
   - 明确哪些功能 runtime blocked；
   - 明确哪些功能只是 historical asset；
   - 明确哪些功能 planned；
   - 不制造自动化幻觉；
   - 不把辅助结果包装成正式结论。

5. **保持长期扩展能力**
   - 新模块必须能纳入统一导航；
   - 新页面必须遵守统一状态系统；
   - 新工具必须归入明确任务类别；
   - 不允许无限堆叠卡片导致界面失控。

---

## 4. 全局 UI 设计原则

### 4.1 先信息架构，后视觉风格

任何新页面、新模块、新功能进入 UI 前，必须先回答：

1. 它属于什么任务类型？
2. 它是入口页、流程页、工具页、模板页、记录页、结果页，还是设置页？
3. 用户进入这个页面想完成什么？
4. 它是否属于 v1.0 主流程？
5. 它是 stable、MVP、testing、developer preview、placeholder、planned、out-of-v1.0、runtime blocked、shell-only，还是 historical UI asset？
6. 它是否需要人工复核？
7. 它会不会误导用户以为软件已经自动完成科研判断？
8. 它在当前 HEAD 下是否真实可运行？

只有这些问题回答清楚后，才进入视觉设计。

### 4.2 以用户任务组织界面，不以代码模块组织界面

UI 不应暴露代码结构。

用户不关心：

- manifest；
- registry；
- service；
- backend；
- artifact；
- source_files；
- diagnostics；
- JSON storage；
- engine consumer；
- handoff；
- internal id；
- cache path。

这些可以进入“技术详情”“开发者诊断”“调试信息”折叠区，但不能成为普通用户主界面的核心。

UI 应围绕用户任务组织：

- 我要导入一个 GEO 数据集；
- 我要检查数据是否可分析；
- 我要确认分组；
- 我要整理一篇 Meta 分析文献；
- 我要配制一个试剂；
- 我要计算 Western Blot 上样体系；
- 我要记录今天的细胞传代；
- 我要配置 ImageJ/Fiji 外部引擎；
- 我要导出一份测试报告。

### 4.3 每个页面必须回答五个问题

用户进入任何页面，应该立即知道：

1. **我在哪里？**
2. **这个页面是干什么的？**
3. **我现在已经完成了什么？**
4. **我下一步应该做什么？**
5. **有什么限制、风险或需要人工确认的地方？**

如果一个页面不能回答这五个问题，就需要重新设计。

### 4.4 主操作必须唯一，次操作必须克制

每个页面最多只能有一个最突出的主操作。

例如：

- 运行数据检查；
- 保存模板；
- 生成本次配制单；
- 保存实验记录；
- 导出报告；
- 进入下一步。

其他操作应作为次级按钮、文本按钮、更多菜单或折叠操作出现。

不要在同一区域放置多个同等视觉权重的按钮。

### 4.5 状态比装饰更重要

科研软件的 UI 重点不是插画、动画、渐变，而是状态表达。

必须优先设计：

- 当前步骤；
- 完成状态；
- 阻塞状态；
- warning；
- error；
- manual review；
- testing；
- runtime blocked；
- shell-only；
- placeholder；
- planned；
- external engine required；
- local only；
- result source。

状态不清楚的界面，即使视觉漂亮，也不合格。

---

## 5. 运行时真实性原则

### 5.1 当前运行时状态高于历史设计沉淀

后续所有 UI 评估必须遵守：

> 当前运行时真实状态，高于历史设计沉淀。

以下材料不能单独证明页面当前可用：

- 历史阶段报告；
- 旧代码存在；
- Figma 草图存在；
- 图标资源存在；
- 曾经通过的测试；
- 旧文档中标记为完成；
- 页面类存在但当前未被 workspace 挂载。

### 5.2 当前可用 UI 的最低标准

一个页面只有同时满足以下条件，才能被标记为当前可用 UI：

1. 当前 HEAD 下能正常 import；
2. 能被真实 workspace 挂载；
3. 不走 fallback / unavailable 占位页；
4. 对应 UI 测试不是整体 skip；
5. smoke test 或目标测试能证明该页面进入真实运行路径；
6. 页面能力与当前后端能力一致；
7. 页面文案与当前功能状态一致；
8. 不把 historical asset 表现为 current runtime UI。

否则只能标记为：

- reference only；
- historical UI asset；
- runtime blocked；
- shell-only；
- fallback UI；
- placeholder；
- developer diagnostic；
- planned。

### 5.3 Skip 不等于通过

UI 验证报告必须分别写明：

- passed；
- skipped；
- failed；
- skip 原因；
- failed 原因；
- 当前 HEAD；
- 执行命令；
- 是否进入真实运行路径。

因以下原因导致的 skip，必须标记为 blocker 或待修复项：

- import error；
- dependency missing；
- runtime unavailable；
- backend module missing；
- PySide6 runtime unavailable；
- workspace fallback；
- 测试条件被跳过。

禁止把“大量 skipped + 少量 passed”描述为 UI 流程通过。

---

## 6. UI Freeze、Consolidation 与新基线治理

### 6.1 触发条件

当出现以下情况时，项目必须进入 UI Freeze / UI Consolidation 阶段：

1. 历史 UI 页面、阶段报告和当前运行时状态不一致；
2. 当前 HEAD 下存在大量 UI 测试 skip；
3. 页面代码存在，但真实 workspace 进入 fallback；
4. 一个模块内出现多个功能入口堆叠，用户任务路径不清；
5. 同一功能存在多个历史页面或重复入口；
6. 新设计规范与旧页面代码冲突；
7. planned / placeholder / testing 功能在主界面中权重过高；
8. 图标、Figma、高保真视觉资源先于真实页面结构完成；
9. 开发者诊断页被混入普通用户流程；
10. 模块扩张速度超过信息架构整理速度。

### 6.2 UI Freeze 的含义

UI Freeze 不是停止所有开发。

允许继续：

- 后端功能修复；
- 运行时 blocker 修复；
- 测试修复；
- 小范围 bug 修复；
- 现有页面的文案和状态修正；
- 技术术语清理；
- 文档审计；
- 页面合并和降级；
- 已确认基线内的最小 UI 修复；
- 模块内部非结构性开发。

暂停以下工作：

- 新增主导航；
- 新增主流程页面；
- 新增大模块入口；
- 大范围重做首页；
- 扩展 planned 功能视觉；
- 生成大批图标；
- 高保真 Figma 全量设计；
- 将历史页面直接声明为当前可用；
- 在未修复运行时 blocker 前继续美化 blocked 页面；
- 继续按旧阶段报告推进 UI 验收。

### 6.3 UI Consolidation 的目标

UI Consolidation 的目标是生成一个简洁、真实、可继续开发的新 UI 基线。

必须输出：

1. 当前可运行 UI 清单；
2. 历史 UI 资产清单；
3. runtime blocked 页面清单；
4. shell-only 页面清单；
5. fallback 页面清单；
6. 需要合并的页面清单；
7. 需要降级为开发者诊断的页面清单；
8. 需要移出普通用户路径的页面清单；
9. 需要保留但弱化的 planned / placeholder 功能清单；
10. 新的主导航结构；
11. 新的模块首页结构；
12. 新的测试与验收命令；
13. 新的 UI 基线文档。

### 6.4 新 UI 基线的定义

新 UI 基线必须满足：

1. 当前 HEAD 可运行；
2. 关键页面能 import；
3. workspace 能真实挂载页面；
4. 关键 UI 测试不是整体 skip；
5. smoke test 通过；
6. 页面状态与真实功能一致；
7. 普通用户路径不暴露开发者诊断术语；
8. planned 功能不抢占主流程；
9. shell-only 模块明确标记；
10. testing 功能明确标记；
11. 页面数量被压缩到当前版本真正需要的范围；
12. 历史 UI 资产被归档、合并或降级，不再混入当前可用 UI。

### 6.5 历史 UI 资产处理规则

历史 UI 页面、旧阶段报告、旧 Figma、旧图标不能直接作为当前可用 UI。

它们只能被归为以下几类：

- 保留并接入新基线；
- 合并到新页面；
- 降级为技术详情；
- 降级为开发者诊断；
- 标记为 historical reference；
- 移出普通用户路径；
- 删除或归档。

任何历史页面如果与当前 UI 宪法冲突，应服从当前 UI 宪法。

### 6.6 合并优先原则

当多个页面表达同一任务链时，应优先合并，而不是继续分裂。

典型合并规则：

- 技术状态页并入主任务页的“状态摘要 + 技术详情”；
- 获取状态并入数据来源页；
- 诊断信息进入折叠区；
- planned 功能进入“未来功能”区域；
- shell-only 模块只保留入口说明，不画完整 workflow；
- 重复按钮合并为一个主操作和少数次操作。

### 6.7 UI Reset 后再进入 Figma

Figma 高保真设计必须发生在 UI Consolidation 之后。

顺序必须是：

```text
UI 审计
→ UI Freeze
→ UI Consolidation
→ 新 UI 基线
→ 低保真 Figma
→ 组件系统
→ 高保真 Figma
→ Codex UI 实现
```

不得在 runtime blocked、页面重复、信息架构未收敛时直接做全量高保真设计。

---

## 7. 历史 UI 资产状态标签

除原有 stable、MVP、testing、developer preview、placeholder、planned、out-of-v1.0 外，当前阶段必须新增以下 UI 治理状态。

| 标签 | 含义 | 后续处理 |
| --- | --- | --- |
| Current runtime UI | 当前运行路径真实可进入 | 可继续迭代 |
| Historical UI asset | 历史设计/代码存在，但当前运行状态未确认 | 只能参考，不能验收 |
| Runtime blocked | 当前导入、挂载或测试被阻断 | 先修 blocker |
| Shell-only | 只有入口壳，没有完整功能 runtime | 只能画入口，不画完整流程 |
| Fallback UI | 因运行失败进入占位页 | 必须显式标记 unavailable |
| Developer diagnostic | 技术诊断页 | 不进入普通用户主流程 |
| Reference only | 可作为设计参考 | 不计入当前可交付 UI |

### 7.1 旧页面与新规范冲突时的优先级

当旧代码、旧阶段报告、旧 Figma 设计与当前 UI 设计宪法或最新设计标准冲突时，优先级为：

1. 当前 UI 设计宪法；
2. 最新 UI design standard；
3. 当前真实运行状态；
4. 当前测试结果；
5. 历史代码与历史阶段报告。

---

## 8. 全局信息架构原则

### 8.1 三层结构

全局 UI 应采用三层结构：

```text
第一层：全局工作台
第二层：模块工作区
第三层：具体任务页面
```

### 8.2 第一层：全局工作台

全局工作台用于回答：

- 用户可以进入哪些模块；
- 最近项目是什么；
- 本地环境是否正常；
- 当前版本和测试状态是什么；
- 是否有外部引擎或本地模型状态提醒；
- 用户可以从哪里继续上次任务。

建议一级入口保持克制：

```text
工作台
生信分析
Meta 分析
实验工具
报告 / 导出
设置
测试反馈
```

不应在第一层暴露过多内部中心，例如完整 Data Center、Task Center、Report Center，除非这些中心已经形成真实用户工作流。

### 8.3 第二层：模块工作区

每个主模块都必须有自己的模块首页。

模块首页用于说明：

- 这个模块能做什么；
- 当前项目状态是什么；
- 推荐下一步是什么；
- 哪些功能可用；
- 哪些功能测试中；
- 哪些功能未开放；
- 最近任务或最近记录是什么。

### 8.4 第三层：具体任务页面

具体任务页面用于执行实际操作，例如：

- GEO 检索；
- 数据检查；
- 文献导入；
- 文献筛选；
- WB 上样计算；
- 试剂模板详情；
- 细胞传代记录；
- ImageJ/Fiji 配置。

任务页面必须显示输入、状态、输出、风险和下一步。

---

## 9. 页面类型规范

### 9.1 首页 / Dashboard 页面

适用于：

- 全局工作台；
- Bioinformatics 首页；
- Meta Analysis 首页；
- LabTools 首页；
- Settings 首页。

页面目标：

- 建立方向感；
- 显示模块入口；
- 显示当前状态；
- 提供继续操作；
- 不承载复杂输入。

设计原则：

- 卡片可以使用，但不能堆叠过多；
- 每张卡片必须显示状态；
- planned 功能弱化展示；
- 当前可用功能优先；
- 不做营销 hero section；
- 不做数据大屏。

### 9.2 流程型页面

适用于：

- Bioinformatics；
- Meta Analysis；
- Western Blot workflow；
- 未来复杂实验流程。

页面目标：

- 让用户知道流程走到哪一步；
- 显示每一步的完成状态；
- 显示阻塞项；
- 提供下一步操作；
- 支持返回修改。

流程型页面必须包含：

```text
步骤导航
当前步骤说明
输入摘要
检查结果
warning / error
主操作
下一步
技术详情折叠区
```

### 9.3 工具型页面

适用于：

- 浓度换算；
- 稀释计算；
- 溶液配制；
- WB loading calculator；
- BCA；
- SDS-PAGE 配胶；
- PCR/qPCR mix；
- ELISA/OD 整理。

工具型页面必须采用：

```text
输入 → 检查 → 计算 → 结果 → 复核 → 导出
```

工具型页面应包含：

- 输入参数；
- 单位；
- 公式或计算逻辑说明；
- 结果摘要；
- warning；
- manual review notice；
- 复制 / 导出；
- 清空 / 重置。

### 9.4 模板型页面

适用于：

- 试剂模板；
- 实验记录模板；
- 分析配置模板；
- 未来 SOP-like 模板。

模板型页面的本质是“重复使用结构”，不是“一次性计算”。

模板型页面必须区分：

```text
创建模板
查看模板
编辑模板
复制模板
使用模板生成一次任务
```

原则：

- 查看和编辑分开；
- 使用模板和修改模板分开；
- 本次任务中的临时改动不能默默污染原模板；
- 如果需要修改模板，应复制或进入编辑模式；
- 模板必须显示更新时间、来源、状态和限制。

### 9.5 记录型页面

适用于：

- 细胞实验记录；
- Western Blot 实验记录；
- 试剂配制记录；
- PCR/qPCR 记录；
- ELISA 记录；
- 用户测试反馈记录。

记录型页面的本质是“保存一次发生过的事实”。

记录型页面必须包含：

- 日期；
- 项目 / 实验名称；
- 对象，例如样本、细胞、试剂、文献；
- 关键参数；
- 观察记录；
- 异常情况；
- 附件或路径；
- 保存；
- 从上次记录创建；
- 导出。

记录型页面不能表现为完整 ELN / LIMS / 合规审计系统，除非这些能力真实实现。

### 9.6 结果型页面

适用于：

- Bioinformatics Results Browser；
- Meta Analysis Results；
- Report Viewer；
- 计算器结果；
- 实验记录导出预览。

结果型页面必须显示：

- 结果来源；
- 输入数据；
- 执行等级；
- 是否 testing；
- 是否 manual review required；
- 是否可导出；
- 结果限制；
- 技术详情。

结果型页面禁止只展示漂亮图表而不说明来源和限制。

### 9.7 设置型页面

适用于：

- 外部引擎；
- 本地模型；
- 默认路径；
- 导出格式；
- 缓存；
- 环境配置。

设置型页面必须区分：

- 已配置；
- 未配置；
- 检测失败；
- 可选；
- 必需；
- 仅本地；
- 不联网；
- 手动配置。

外部引擎必须表现为外部依赖，而不是内置能力。

---

## 10. 全局状态标签系统

所有模块必须使用统一状态标签，不允许每个页面自定义一套状态语言。

### 10.1 功能成熟度标签

| 标签 | 含义 | UI 表达 |
| --- | --- | --- |
| Stable | 基础能力稳定可展示，但不等于正式商业版 | 正常入口，可有 internal beta 说明 |
| MVP | 最小可用功能，可完成真实小任务 | 正常入口 + 限制说明 |
| Testing | 测试级功能，结果仅供内部测试 | 必须显示 testing 标签 |
| Developer Preview | 开发者预览，功能边界可能变化 | 页面顶部持续显示 |
| Placeholder | 有入口或说明，无真实能力 | 弱化入口，不显示假结果 |
| Planned | 规划中，当前未开放 | 放入未来功能区域 |
| Out of v1.0 | 不属于当前版本 | 不进入主流程 |
| Runtime blocked | 当前运行路径被阻断 | 不可验收，先修 blocker |
| Shell-only | 只有入口壳层 | 不画完整 workflow |
| Historical UI asset | 历史资产 | 只作参考 |

### 10.2 操作状态标签

| 标签 | 含义 |
| --- | --- |
| Not started | 未开始 |
| In progress | 进行中 |
| Ready | 已准备好 |
| Needs review | 需要人工复核 |
| Blocked | 被阻塞 |
| Warning | 有风险但可继续 |
| Error | 错误，不能继续 |
| Completed | 已完成 |
| Disabled | 当前不可用 |

### 10.3 结果可信度标签

| 标签 | 含义 |
| --- | --- |
| Imported result | 用户导入结果 |
| Testing-level result | 测试级结果 |
| Draft summary | 草稿摘要 |
| Manual review required | 需要人工复核 |
| Not publication-ready | 不可视为发表级结果 |
| Not clinical use | 不可用于临床决策 |
| External engine output | 外部引擎输出 |
| Local-only | 仅本地处理 |

### 10.4 状态标签使用规则

1. testing 页面必须显示 testing。
2. developer preview 页面必须显示 developer preview。
3. placeholder 功能不得显示完整操作链。
4. planned 功能不得以可用按钮形式进入主流程。
5. runtime blocked 页面不得进入普通用户主流程。
6. shell-only 模块不得暗示完整 runtime。
7. 结果页面必须显示结果来源和可信等级。
8. AI 和外部引擎输出必须显示人工复核提示。
9. 不允许用颜色暗示“已正式完成”而文字上写 testing。
10. historical UI asset 不得被计入当前可交付 UI。

---

## 11. AI 与自动化边界

### 11.1 AI 的 UI 定位

AI 在 BioMedPilot / 萤火虫 中只能作为辅助能力，而不是主流程主体。

AI 可以表现为：

- 草稿建议；
- 检索词辅助；
- 术语映射辅助；
- 文案草稿；
- 本地模型配置；
- 可接受 / 拒绝 / 编辑的建议队列。

AI 不应表现为：

- 自动完成科研分析；
- 自动给出正式结论；
- 自动替代人工筛选；
- 自动替代数据提取；
- 自动替代质量评价；
- 自动替代统计判断；
- 自动生成投稿级报告。

### 11.2 AI Gateway 表达规则

AI Gateway 默认关闭。

UI 中必须表达：

- 默认 disabled；
- local-only 优先；
- 用户明确开启；
- 不自动上传敏感数据；
- 不把 AI 输出直接写入最终结果；
- 人工确认后才进入记录。

禁止设计：

- 云 AI 默认开启；
- 外部 API Key 管理作为已实现能力；
- 一键 AI 完成分析；
- AI 自动生成正式科研结论。

---

## 12. 外部引擎边界

### 12.1 ImageJ/Fiji

ImageJ/Fiji 必须被设计为外部引擎。

UI 应表达：

- 外部路径配置；
- 检测状态；
- 版本或可执行路径；
- 失败原因；
- 手动配置；
- 可继续 manual workflow；
- 输出需要人工复核。

禁止表达：

- BioMedPilot 内置图像识别；
- 自动 ROI；
- 自动细胞计数；
- 自动条带识别；
- 自动 WB 灰度结论；
- 自动病理识别；
- 自动实验结论。

### 12.2 本地模型和其他引擎

Ollama、本地模型、PaddleOCR 等外部能力应统一放入外部引擎或设置体系。

它们不是主模块，不应抢占科研工作流主界面。

---

## 13. 模块设计原则

## 13.1 UIShell UI 原则

UIShell 是桌面壳层和导航基线，不是所有模块完整 runtime 的替代品。

设计原则：

1. Shell 可展示登录、模块选择、主窗口、侧边栏、设置、测试模式。
2. 模块入口必须真实反映当前接入状态。
3. Shell-only 模块必须明确标记。
4. 侧边栏不应显示未形成真实用户工作流的中心页。
5. 公共导航模型和真实渲染应保持一致。
6. 设置中心中 placeholder 配置不能画成完整设置系统。
7. 本地 launcher、packaged-local-python、signed .app、ReleaseBuild 必须区分。
8. 旧 UI 阶段报告不能作为当前 Shell 可交付证据。

## 13.2 Bioinformatics UI 原则

Bioinformatics 是数据分析流程型模块。

它的 UI 核心不是“展示分析结果”，而是：

```text
数据来源 → 数据识别 → 数据准备 → 人工确认 → 分析配置 → 结果浏览 → 报告导出
```

设计原则：

1. 数据来源必须清楚。
2. 每个文件或数据资产的识别状态必须清楚。
3. 分组、物种、表达矩阵、样本信息必须显示确认状态。
4. DEG、GSEA、enrichment 等未成熟功能不能画成正式执行完成。
5. 报告必须显示 testing summary 或 draft report 语义。
6. 技术详情可以折叠，不放在主视觉中心。
7. 所有分析结果必须显示来源：导入、测试、真实计算、草稿。
8. 当前 workflow import 或 runtime blocked 时，不能宣传 UI-04 到 UI-13 当前可运行。
9. 技术状态页应优先合并进主任务页或降级为开发者诊断。

Bioinformatics 页面应强调：

- readiness；
- missing items；
- next step；
- manual confirmation；
- result semantics；
- report limitations。

## 13.3 Meta Analysis UI 原则

Meta Analysis 是文献研究流程型模块。

它的 UI 核心是：

```text
Protocol → Search → Import → Deduplication → Screening → Full-text → Extraction → Quality → Analysis → Reporting
```

设计原则：

1. 所有关键决定都必须保留人工确认。
2. AI 只能作为建议，不可直接覆盖结论。
3. 筛选、提取、质量评价必须显示人工决策状态。
4. 统计结果必须显示 testing-level。
5. PRISMA、报告、forest/funnel 图不能表现为投稿级正式输出，除非真实实现。
6. 文献导入和去重应强调 diagnostics 和 review。
7. 不设计自动全文下载、自动 OCR、绕过 paywall 或 Zotero 双向同步，除非真实实现。
8. 如果当前工作区只是 shell-only，必须明确标记，不得暗示完整 Meta runtime 已接入。

Meta Analysis 页面应强调：

- workflow progress；
- decision queue；
- manual review；
- evidence traceability；
- testing analysis；
- report draft。

## 13.4 LabTools UI 原则

LabTools 是实验任务工作台，不是工具卡片堆叠区。

它的 UI 应围绕实验室用户任务重新组织。

建议长期结构：

```text
LabTools
├── 快速计算
├── 试剂与溶液
├── 实验记录
├── 实验流程工具
└── 图像分析与外部引擎
```

### 13.4.1 快速计算

用于一次性计算，不承担模板管理和长期记录职责。

适合放置：

- 浓度换算；
- 稀释计算；
- 溶液配制；
- WB 上样计算；
- BCA；
- SDS-PAGE；
- PCR/qPCR mix；
- ELISA / OD 整理。

原则：

- 输入和结果分区；
- 单位选择清晰；
- warning 明显；
- 支持复制和导出；
- 不自动变成实验记录；
- 不自动修改模板。

### 13.4.2 试剂与溶液

用于管理可重复使用的试剂模板和本次配制。

适合放置：

- 我的试剂模板；
- 新建模板；
- 查看模板；
- 编辑模板；
- 复制模板；
- 从模板配置试剂；
- 历史配制记录。

原则：

- 模板和本次配制分开；
- 查看和编辑分开；
- 使用模板不等于修改模板；
- 临时改动不能污染原模板；
- 子模板、pH、溶剂补足、添加顺序必须清楚；
- 必须保留人工核对 SOP、pH、纯度、温度、安全要求的提示。

### 13.4.3 实验记录

用于保存一次实验事实，不是完整 ELN/LIMS。

适合放置：

- 细胞实验记录；
- Western Blot 实验记录；
- 试剂配制记录；
- PCR/qPCR 记录；
- ELISA 记录；
- 从上次记录创建；
- 导出记录。

原则：

- 记录发生了什么；
- 不替代正式实验记录本；
- 不提供合规电子签名；
- 不做权限审批；
- 不声称 GLP/GMP/LIMS 合规；
- 支持本地保存和导出。

### 13.4.4 实验流程工具

用于复杂实验流程的多步骤工作台。

适合放置：

- Western Blot workflow；
- 未来 qPCR workflow；
- 未来 ELISA workflow；
- 未来细胞实验 workflow。

原则：

- 按实验流程组织，而不是按孤立工具组织；
- 每一步显示完成状态；
- 计算、记录、导出可以在流程中连接；
- 图像分析必须连接到外部引擎边界；
- 不把未来步骤画成已完成能力。

### 13.4.5 图像分析与外部引擎

用于管理 ImageJ/Fiji 和 manual ROI 辅助流程。

原则：

- 外部引擎优先；
- 人工复核优先；
- 不承诺自动识别；
- 不承诺自动结论；
- 导出结果仅作为辅助材料；
- 图像分析能力必须与当前真实实现一致。

---

## 14. 技术术语泄漏治理

普通用户界面禁止直接暴露以下技术术语，除非位于折叠技术详情 / 开发者诊断区：

- manifest；
- source_files；
- source_type；
- acquisition；
- plan_only；
- artifact；
- backend；
- registry；
- handoff；
- diagnostics；
- raw JSON；
- cache path；
- internal id；
- engine consumer；
- runner；
- dry-run；
- preview task。

推荐转译：

| 技术术语 | 用户界面表达 |
| --- | --- |
| manifest | 项目记录 / 技术清单 |
| source_files | 数据文件 |
| source_type | 数据来源类型 |
| acquisition | 数据获取状态 |
| plan_only | 仅生成计划，尚未下载 |
| artifact | 数据资产 / 结果文件 |
| diagnostics | 技术详情 |
| backend | 后台处理状态 |
| dry-run | 测试运行 / 预检 |
| preview task | 预览任务 |

---

## 15. 视觉资源从属原则

图标、插画、Figma 高保真稿、模块宣传图不得早于真实页面结构稳定。

当页面处于以下状态时：

- runtime blocked；
- shell-only；
- placeholder；
- planned；
- historical UI asset；
- fallback UI；

只允许设计：

- 低保真结构；
- 占位状态；
- future/planned 说明；
- reference-only 说明。

不应生成完整视觉资源并声明功能完成。
不应把图标接入作为功能完成证据。
不应在页面不可运行时先做高保真视觉包装。

---

## 16. 交付状态表达原则

UI 和文档不得混淆以下状态：

1. source smoke 可运行；
2. local launcher 可启动；
3. packaged-local-python 可启动；
4. signed .app；
5. standalone installer；
6. ReleaseBuild 可交付版本；
7. Integration Preview；
8. Public release。

只要未签名、非 standalone、未通过 ReleaseBuild 验证，就不能在 UI 或文档中表达为“可发布版本”。

---

## 17. 视觉风格原则

### 17.1 总体气质

UI 应保持：

- 专业；
- 克制；
- 清晰；
- 安静；
- 低噪音；
- 高可读性；
- 中文友好；
- 桌面软件感；
- 科研工作台感。

不应追求：

- 炫酷动画；
- 过度渐变；
- 高饱和色块；
- 数据大屏风；
- 医疗宣传风；
- 游戏化；
- 过度 AI 化；
- 营销落地页风格。

### 17.2 品牌与工作界面的关系

“萤火虫”的品牌理念可以用于：

- Logo；
- App icon；
- 启动页；
- 空状态插画；
- onboarding；
- 官网；
- PPT；
- 海报；
- 品牌物料。

但主工作界面应保持专业、理性、克制。

品牌层可以有温度，工作层必须有秩序。

### 17.3 色彩原则

推荐基础色彩方向：

- deep navy；
- teal；
- white；
- light gray；
- muted blue-gray；
- restrained status colors。

原则：

- 主色用于导航和强调；
- 状态色用于状态，不用于装饰；
- warning/error/success 必须一致；
- 不同模块可以有轻微色彩区分，但不能变成三个不同软件；
- 表格和表单优先保证可读性；
- token 化优先，减少 inline stylesheet。

### 17.4 字体与层级

中文界面必须保证阅读舒适。

建议层级：

- 页面标题；
- 区块标题；
- 说明文字；
- 表格字段；
- 状态标签；
- 技术详情；
- 警告说明。

原则：

- 不用过多字号；
- 不用过多字重；
- 表格内信息密度可以高，但必须分组；
- 长说明进入折叠或侧栏，不堆在主区域。

---

## 18. 组件系统原则

Figma 和 Codex 后续应优先统一以下基础组件：

1. 全局侧边栏；
2. 模块首页卡片；
3. 状态 badge；
4. 步骤导航；
5. 普通表格；
6. 可编辑表格；
7. 候选列表；
8. 结果摘要卡；
9. warning panel；
10. error panel；
11. empty state；
12. placeholder state；
13. planned feature block；
14. runtime blocked block；
15. shell-only notice；
16. input group；
17. unit selector；
18. formula block；
19. result block；
20. export block；
21. technical details accordion；
22. manual review notice。

组件必须跨模块复用。

不要让 Bioinformatics、Meta Analysis、LabTools、UIShell 分别发展出四套视觉语言。

---

## 19. 禁止设计模式

以下设计模式禁止用于当前阶段：

1. 把软件首页设计成营销 landing page。
2. 把未实现功能画成可点击完整流程。
3. 把 testing 结果画成正式科研结论。
4. 把 AI 画成自动科研分析中心。
5. 把 ImageJ/Fiji 画成内置图像识别。
6. 把 planned 功能放在主操作位置。
7. 把技术字段直接堆在普通用户主界面。
8. 把所有工具以同等权重卡片平铺。
9. 把 LabTools 继续设计成无分类工具集合。
10. 把实验记录设计成完整合规 ELN/LIMS。
11. 把 Meta 报告画成正式投稿级报告。
12. 把 Bioinformatics 分析画成正式生产 pipeline。
13. 用数据大屏风格代替科研工作流。
14. 用过度插画、过度渐变、过度动画降低专业感。
15. 在没有输入和状态说明的情况下只展示“结果图”。
16. 把历史 UI 页面当作当前可运行页面。
17. 把 skip 测试当作通过。
18. 在 runtime blocked 页面上继续做高保真美化。
19. 把 shell-only 模块宣传成完整功能线。
20. 继续在 UI Freeze 阶段新增大页面或主导航。

---

## 20. Figma 设计执行原则

### 20.1 当前阶段不直接进入高保真全量设计

当前阶段应先完成 UI Consolidation 和新基线。

不得在以下情况直接进入全量高保真 Figma：

- runtime blocked 未修复；
- 历史页面和当前运行状态不一致；
- 模块入口仍混乱；
- planned 功能过多抢占主界面；
- shell-only 模块未明确；
- 技术状态页未降级；
- 测试 skip 原因未解释。

### 20.2 第一轮 Figma 目标

第一轮 Figma 不追求全量页面高保真。

第一轮目标是：

- 建立全局信息架构；
- 确定导航；
- 确定模块首页；
- 确定状态标签；
- 确定表格/表单/结果基础组件；
- 确定 LabTools 分类逻辑；
- 确定流程型页面模式；
- 确定工具型页面模式；
- 确定 runtime blocked / shell-only / planned 状态表现。

### 20.3 第一轮优先页面

建议在新 UI 基线形成后，优先设计：

1. 全局工作台；
2. Bioinformatics 模块首页；
3. Bioinformatics 数据来源 / Readiness 页面；
4. Meta Analysis shell-only 或完整 runtime 状态页，视当前工作区而定；
5. Meta 文献导入 / 文献库页面，仅在完整 runtime 接入后；
6. LabTools 首页；
7. 快速计算中心；
8. 试剂模板管理；
9. 实验记录模板中心；
10. Settings / External Engine 页面。

### 20.4 低保真优先

在全局结构稳定前，不应直接进入完整高保真视觉稿。

推荐顺序：

```text
UI 审计
→ UI Freeze
→ UI Consolidation
→ 新 UI 基线
→ 信息架构
→ 低保真线框图
→ 核心组件系统
→ 中保真原型
→ 高保真视觉
→ Codex UI 实现
→ 测试与回填设计规范
```

### 20.5 Figma 输出要求

Figma 输出应至少包含：

- 页面结构；
- 状态 badge；
- 主要交互；
- 主操作和次操作；
- 空状态；
- warning 状态；
- runtime blocked 状态；
- shell-only 状态；
- placeholder 状态；
- planned 状态；
- technical details 折叠；
- manual review notice；
- 可复用组件。

---

## 21. Codex UI 开发约束

后续 Codex 执行 UI 开发任务时，必须遵守以下约束：

1. 不因 UI 重构破坏现有业务逻辑。
2. 不把 placeholder 改成假实现。
3. 不引入未验证的自动算法。
4. 不把 testing 功能包装成 stable。
5. 不删除必要的限制提示。
6. 不把技术详情放到普通用户主界面。
7. 不修改全局功能边界，除非任务明确要求。
8. 每次 UI 重构必须更新对应测试。
9. 每次 UI 重构必须保证 smoke test 通过。
10. 复杂模块应分阶段改造，不一次性大重构。
11. LabTools 新工具必须先归类，再进入 UI。
12. Bioinformatics 和 Meta 结果页必须显示结果来源和 testing 语义。
13. 外部引擎页面必须强调外部依赖和人工复核。
14. 任何 AI 相关 UI 必须保留 disabled/local/manual-review 语义。
15. 修改后应更新 UI 文档或阶段报告。
16. 不得把历史 UI asset 标记为当前可运行。
17. 不得把 skip 测试写成通过。
18. 不得在 UI Freeze 阶段新增主导航或大页面。
19. 不得在 runtime blocked 修复前继续美化 blocked 页面。
20. 每份阶段报告必须写明当前 HEAD、测试命令、passed/skipped/failed 和 skip 原因。

---

## 22. LabTools 特别约束

LabTools 是当前最容易变得混乱的模块，因此需要额外约束。

### 22.1 LabTools 不再允许无分类堆卡片

新增工具前必须先归类：

```text
快速计算
试剂与溶液
实验记录
实验流程工具
图像分析与外部引擎
```

### 22.2 计算器、模板、记录必须分开

- 计算器：解决一次性计算；
- 模板：解决重复使用结构；
- 记录：保存一次实验事实；
- 流程：组织复杂实验步骤；
- 外部引擎：调用和配置外部工具。

这五类可以互相连接，但不能混在同一入口层级中。

### 22.3 实验安全和人工复核必须可见

LabTools 所有结果页面都必须有人工复核提示。

典型提示语：

```text
请根据实验室 SOP、试剂纯度、pH、温度、仪器条件和安全要求人工核对。本工具仅用于本地计算和记录辅助，不构成实验安全建议或正式 SOP。
```

### 22.4 图像分析能力必须谨慎表达

禁止出现：

- 自动 ROI；
- 自动细胞计数；
- 自动条带识别；
- 自动灰度结论；
- 自动实验解释；
- 自动诊断。

---

## 23. 文案原则

### 23.1 文案应清楚、克制、准确

避免夸张表达：

- 智能完成；
- 一键分析；
- 自动生成结论；
- 精准诊断；
- 发表级；
- 临床级；
- 全自动；
- AI 代替人工。

推荐表达：

- 辅助；
- 草稿；
- 待确认；
- 需要人工复核；
- testing；
- developer preview；
- runtime blocked；
- shell-only；
- historical reference；
- 本地计算；
- 导出记录；
- 预检；
- 候选；
- 建议；
- 未开放。

### 23.2 中文优先，英文作为辅助

软件主要面向中文用户时，中文应作为主语言。

英文可以用于：

- 专业术语；
- 方法名；
- 状态 badge；
- 数据库名；
- 算法名；
- 开发者诊断。

示例：

```text
数据检查与准备 / Data Readiness
人工复核 required
Developer Preview
Testing-level result
Runtime blocked
Shell-only
```

---

## 24. 版本阶段表达规则

当前阶段 UI 应持续表达：

```text
0.1.0-internal-beta
Developer Preview
Testing
Local-only
Manual review required
Runtime blocked
Shell-only
Historical reference
```

不应表达：

```text
正式版
商业发布版
临床级
发表级
生产级
全自动
合规 ELN
云协作
多人审批
完整 runtime，除非当前工作区真实接入并通过测试
```

除非这些能力已经真实实现并通过审计。

---

## 25. 设计评审检查清单

每个新页面进入开发前，必须检查：

1. 页面属于哪种页面类型？
2. 页面主任务是否清楚？
3. 是否有唯一主操作？
4. 是否显示当前位置？
5. 是否显示当前状态？
6. 是否显示下一步？
7. 是否显示 warning / error？
8. 是否显示人工复核提示？
9. 是否错误展示 testing / planned 功能？
10. 是否暴露过多技术字段？
11. 是否有空状态？
12. 是否有失败状态？
13. 是否有导出或保存逻辑？
14. 是否符合全局状态标签？
15. 是否与其他模块组件一致？
16. 是否会让用户误解为正式科研结论？
17. 是否需要折叠技术详情？
18. 是否适合当前 v1.0 范围？
19. 当前 HEAD 下是否能 import？
20. 是否被真实 workspace 挂载？
21. 对应测试是否整体 skip？
22. 是否 shell-only？
23. 是否 runtime blocked？
24. 是否 historical UI asset？
25. 是否应该先合并、降级或归档，而不是继续设计？

任何页面如果不能通过以上检查，不应进入高保真设计或开发实现。

---

## 26. 后续推荐执行顺序

建议后续 UI 工作按以下顺序执行：

```text
1. 固化本 UI 设计宪法 v2
2. 进入 UI Freeze / UI Consolidation
3. 生成 UI_Freeze_Consolidation_Baseline 文档
4. 清点 current runtime UI / historical UI asset / runtime blocked / shell-only / fallback UI
5. 修复 P0 runtime blocker
6. 合并或降级旧页面
7. 收敛侧边栏和模块首页
8. 单独制定 LabTools UI 信息架构重构计划
9. 建立新 UI 基线
10. 新基线通过 smoke 和有效 UI 测试
11. 再进入低保真 Figma
12. 建立统一组件系统
13. 再进入高保真视觉设计
14. 按新基线分阶段交给 Codex 实现
```

---

## 27. 推荐给 Codex 的 UI Consolidation 阶段任务

后续可直接将以下任务交给 Codex：

```text
请进入 UI Freeze / UI Consolidation 阶段。

目标：
基于当前 UIShell 审计、UI 设计宪法 v2 和现有 docs/biomedpilot_ui_design_standard.md，生成一个新的简洁 UI 基线方案。

要求：
1. 不新增主导航。
2. 不新增主流程页面。
3. 不生成新图标。
4. 不做高保真视觉。
5. 不把历史 UI 页面标记为当前可用。
6. 清点当前可运行 UI、历史 UI 资产、runtime blocked 页面、shell-only 页面、fallback 页面。
7. 标出应保留、合并、降级、归档、移出普通用户路径的页面。
8. 重点处理：
   - UI-03 是否按新规范收敛；
   - UI-05 是否并入 UI-04 或降级为开发者诊断；
   - UI-04 到 UI-13 当前 blocked 状态如何标记；
   - Meta 在 UIShell 中 shell-only 如何表达；
   - 侧边栏定义和真实渲染不一致如何收敛；
   - 技术术语泄漏如何巡检。
9. 输出新文件：
   docs/ui/UI_Freeze_Consolidation_Baseline_20260519.md
10. 最后给出下一步最小开发任务清单，不超过 5 项。
11. 不修改业务代码，除非任务被拆分为后续开发任务。
```

---

## 28. 总结原则

BioMedPilot / 萤火虫 的 UI 设计必须坚持：

```text
任务驱动，而不是代码驱动。
流程清楚，而不是功能堆叠。
状态明确，而不是按钮很多。
人工复核可见，而不是自动化幻觉。
当前可用和未来规划严格区分。
当前运行时真实状态，高于历史设计沉淀。
Skip 不等于通过。
Shell-only 不能冒充完整 runtime。
Runtime blocked 页面先修复，再美化。
计算器、模板、记录、流程、外部引擎分层管理。
品牌有温度，工作界面有秩序。
先 UI Freeze / Consolidation，再 Figma 高保真。
```

这份 UI 设计宪法 v2 应作为后续所有 Figma 设计、Codex UI 开发、UIShell 收敛和模块重构任务的上位依据。
