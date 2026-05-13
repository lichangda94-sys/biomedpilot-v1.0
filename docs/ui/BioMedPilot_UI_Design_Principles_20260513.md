# BioMedPilot UI Design Principles

日期：2026-05-13

本文件是 BioMedPilot / 医研智析 v1.0 跨模块 UI 总规范。后续 Shell、Bioinformatics、Meta Analysis、LabTools 或其他模块的 UI 开发，如与本文件冲突，应优先遵守本文件；业务模块可以根据自身流程适配，但不得自行引入冲突的颜色、字体、按钮体系、页面结构或视觉风格。

## 1. 总体 UI 定位

BioMedPilot / 医研智析 的 UI 定位是：

Apple-like macOS premium biomedical research desktop software.

它是专业医学科研桌面软件，不是网页后台、脚本控制台、技术日志浏览器或营销页。界面应保持克制、清晰、低噪音、中文友好，让研究人员知道当前步骤、当前状态、下一步动作和需要人工确认的边界。

## 2. 总色板

总色板固定为：

| 角色 | 色值 |
| --- | --- |
| 深海军蓝 | `#12324A` |
| 青绿色 | `#1BAE9F` |
| 浅灰背景 | `#F5F7F9` |
| 白色 | `#FFFFFF` |

使用原则：

- `#12324A` 用于品牌、模块标题、主要流程按钮、重要文本强调。
- `#1BAE9F` 用于确认、焦点、进度强调和少量高价值操作。
- `#F5F7F9` 用于全局页面背景。
- `#FFFFFF` 用于卡片、输入区域、表格容器和弹层。
- 模块不得把其他颜色定义为主色。业务模块可使用弱识别色，但不得覆盖总色板。
- Warning、Error、Ready、Draft、Confirmed 等状态色必须进入 shared UI tokens，不得在页面内随意硬编码。

## 3. 中文友好原则

- 主界面优先中文表达。
- 英文缩写只在研究语境必要时保留，例如 PICO、PICOS、PECO、DEG、PRISMA、GSEA。
- 每个页面只保留一句简短说明，避免长段落解释。
- 表格列名、按钮、状态标签应短而稳定。
- 技术英文只进入技术详情、开发者诊断或导出文档。
- 不把 draft、dry-run、testing-level、imported result 描述成正式结果。

## 4. 模块一致性原则

Bioinformatics、Meta Analysis、LabTools 必须共享同一视觉语言：

- 同一 Shell 入口。
- 同一背景、卡片、边框、按钮和状态标签规则。
- 同一字体层级和间距节奏。
- 同一 Developer Preview / 本地测试版表达方式。
- 同一“普通主界面简洁，技术详情折叠”的信息层级。

模块可以根据业务流程有不同页面内容，但不能形成独立主题、独立主色、独立按钮系统或独立全局导航。

## 5. 主线 Shell 权威原则

MainLine Shell 是 BioMedPilot 的全局入口和界面权威层。

Shell 负责：

- 登录页。
- 模块选择。
- 全局导航。
- 模块入口。
- 全局状态和 Developer Preview 标记。
- 主题、色板、字体、间距、按钮语义和状态标签。

业务模块负责：

- 自己的流程内容。
- 自己的输入、状态摘要、结果摘要和报告摘要。
- 自己的业务确认与下一步动作。

业务模块不得重建与 Shell 冲突的全局侧栏、主窗口结构、品牌区、主色或页面视觉体系。

## 6. UI 总规范优先原则

UI Governance / UI Design Principles 是 BioMedPilot 跨模块界面开发的权威依据。

Bioinformatics、Meta Analysis、LabTools 或任何后续模块的 UI 开发，如果与总 UI 规范冲突，应优先遵循总 UI 规范；模块可以做业务适配，但不得自行引入冲突的颜色、字体、按钮体系、页面结构或视觉风格。

## 7. 技术字段暴露原则

普通主界面不暴露过多技术字段。

不得直接放在普通主界面的内容包括：

- manifest。
- schema。
- asset id。
- run id。
- branch。
- raw path / 完整本地路径。
- internal contract。
- raw JSON。
- backend / legacy / adapter 细节。
- queue_path、decisions_path、report_manifest_path 等内部路径。

允许出现的位置：

- 折叠的“技术详情”。
- 折叠的“开发者诊断”。
- 设置页中的开发者诊断区。
- 日志审计文件。
- manifest / handoff / stage report 等文档。

主界面需要展示路径时，应显示压缩后的用户友好路径，并把完整路径放入 tooltip 或技术详情。

## 8. 页面布局基本模板

流程型页面模板：

1. 页面标题区：模块、步骤、Developer Preview / 本地测试版标记。
2. 一句话说明：说明当前页目的。
3. 状态摘要区：Ready、Not Ready、Warning、Draft、Confirmed 等短状态。
4. 主操作区：最多一个当前主要动作。
5. 内容卡片区：表单、表格、列表或报告摘要。
6. 辅助详情区：可折叠，用于解释、日志或诊断。
7. 底部流程区：返回与下一步。

工具型页面模板：

1. 工具标题区。
2. 输入参数区。
3. 即时结果区。
4. 保存 / 导出 / 复制等次要操作。
5. 技术详情折叠区。

LabTools 默认使用工具型页面模板；Bioinformatics 和 Meta Analysis 默认使用流程型页面模板。

## 9. 按钮层级规则

按钮语义必须统一：

| 层级 | 用途 | 文案示例 |
| --- | --- | --- |
| Primary Next | 流程推进 | 下一步：数据识别 |
| Primary Action | 当前页核心动作 | 生成标准化资产 |
| Secondary | 辅助操作 | 刷新状态、查看详情、选择文件 |
| Back | 返回上一步 | 返回：数据来源 |
| Danger | 删除、清理、移除 | 删除记录、清理旧结果 |
| Text | 轻量辅助 | 复制、展开 |

规则：

- 同一页面最多一个 Primary Next。
- 同一操作区最多一个 Primary Action；如确有多个核心动作，应拆分为步骤或分组。
- “下一步”“返回”“确认”“刷新”“导出”“查看详情”等用语必须稳定。
- 不使用“登记”“加入队列”“创建任务记录”等技术动作作为普通用户主按钮，除非该页面面向开发者诊断。

## 10. 状态标签规则

统一状态标签：

| 英文状态 | 中文文案 | 含义 |
| --- | --- | --- |
| Ready | 已就绪 | 可继续 |
| Not Ready | 未就绪 | 缺少必要输入 |
| Warning | 需注意 | 可继续但需复核 |
| Error | 错误 | 当前动作失败或阻塞 |
| Draft | 草稿 | 生成但未确认 |
| Confirmed | 已确认 | 用户已确认 |
| Testing | 测试级 | 内部测试能力 |
| Blocked | 阻塞 | 无法继续 |

规则：

- 状态标签应短，不写长句。
- 状态说明放在辅助文本或详情区。
- 状态颜色来自 shared UI tokens。
- Draft / Testing 不得伪装成 Confirmed / Ready。

## 11. 文案长度规则

- 页面说明：一行或一短句。
- 状态标签：不超过 8 个中文字符为宜。
- 按钮：优先 2-8 个中文字符；流程按钮可使用“下一步：目标步骤”。
- 卡片标题：不超过 12 个中文字符为宜。
- 表格列名：短词优先。
- 长说明放入折叠说明、tooltip、帮助文档或开发者详情。

## 12. 卡片、半径与间距规则

- 页面背景使用 `#F5F7F9`。
- 内容卡片使用 `#FFFFFF`。
- 普通卡片半径默认 8px。
- 普通边框使用浅灰 token。
- 页面外边距建议 24-32px。
- 卡片内边距建议 16-24px。
- 分区间距建议 12-16px。
- 不使用大面积装饰图、不使用营销式 hero、不使用与科研桌面软件无关的装饰。

## 13. Bioinformatics 适配边界

Bioinformatics 可以保留表达数据、生信任务、标准化资产和分析结果的业务结构，但必须遵守：

- 主界面显示数据状态、分析准备状态、任务状态和报告状态。
- manifest、asset id、run id、完整路径、raw JSON 进入技术详情。
- 分析任务中心不得成为技术命令面板；应突出“当前能做什么”和“下一步是什么”。
- dry-run、preflight、testing-level、imported result、real computed result 必须明确区分。

## 14. Meta Analysis 适配边界

Meta Analysis 可以保留 PICO/PICOS/PECO、检索策略、文献导入、去重、筛选、全文、提取、质评、统计和报告流程，但必须遵守：

- 接入 MainLine Shell，不自建冲突的全局导航。
- 页面状态和按钮层级与 Bioinformatics 保持一致。
- PubMed testing-level、AI suggestion、draft、confirmed 必须明确标记。
- Draft ID、preview_id、queue_path、decisions_path、manifest、schema、raw JSON 进入开发者详情。
- PICO、检索、文献库和去重页面优先展示研究人员可理解的信息。

## 15. LabTools 适配边界

LabTools 当前未在 MainLine 中接入业务代码。未来接入时必须遵守：

- 作为 Shell 内模块出现。
- 使用同一总色板和 shared UI tokens。
- 默认采用工具型页面模板。
- 工具结果必须标记为计算辅助或记录辅助，不伪装成生信分析、Meta 分析或临床结论。
- 不污染 Bioinformatics 或 Meta project manifest。
- 不创建独立品牌、独立主题或独立全局导航。

## 16. 后续落地顺序

1. 将本文件和 UI Governance Audit 作为跨模块 UI 权威依据写入 Global Development Manual。
2. 扩展 `app/ui_style_tokens.py`，移除冲突主色，补充状态 tokens、按钮 tokens、卡片 tokens。
3. 建立 shared UI components：PageHeader、StatusBadge、ActionBar、DeveloperDetails、ContentCard。
4. 先统一 MainLine Shell 和 Bioinformatics 新页面。
5. Meta 合入 MainLine 前先做 UI 对齐，不直接合入独立主题。
6. LabTools 进入 MainLine 前先按工具型页面模板设计和测试。
