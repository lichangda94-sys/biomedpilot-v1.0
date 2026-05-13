# BioMedPilot UI Governance Audit

日期：2026-05-13

范围：MainLine Shell、MainLine Bioinformatics UI、MainLine Meta 最小入口、dev/meta-analysis 当前 UI 延展面，以及未来 LabTools 接入原则。

本审计只记录 UI / Shell / 视觉规范问题，不改业务逻辑，不创建 LabTools 业务代码，不改变数据结构、分析逻辑、AI Gateway 或词库逻辑。

## 1. 当前 UI 治理结论

BioMedPilot / 医研智析 需要建立一个跨模块 UI 权威层。当前 MainLine 已有 `app/ui_style_tokens.py` 和 `docs/biomedpilot_ui_design_standard.md`，但它们仍偏向 UI 阶段说明和局部样式复用，还没有明确成为 Shell、Bioinformatics、Meta Analysis、LabTools 的最高优先级 UI 规范。

当前结论：

- P0：必须把 UI Governance / UI Design Principles 提升为跨模块界面开发权威依据，并写入 Global Development Manual。
- P0：后续 Meta Analysis 和 LabTools 不得绕过 MainLine Shell 自建完整视觉体系。
- P1：需要把颜色、字体、半径、间距、按钮、状态标签和页面骨架进一步沉淀到 shared UI tokens / shared UI components。
- P1：普通主界面必须继续减少 manifest、asset id、run id、raw path、schema、branch、完整 JSON 等技术字段。
- P2：部分页面已使用统一风格但仍存在字号、卡片半径、状态色和按钮语义不一致。
- P3：旧 legacy UI、历史沙盒和归档页面暂只记录，不在本阶段重构。

## 2. 当前一致性现状

### 2.1 MainLine Shell

审计范围：

- `app/shell/login.py`
- `app/shell/module_selection.py`
- `app/shell/main_window.py`
- `app/shell/sidebar.py`
- `app/shell/status_panel.py`
- `app/ui_style_tokens.py`

现状：

- 登录页和模块选择页已使用 `app/ui_style_tokens.py` 中的 `COLORS`、`SPACING`、`RADIUS`、`FONT_SIZE`。
- 主色方向基本符合 deep navy、teal、white、light gray。
- 模块入口页已经形成较清晰的卡片、版本标记、Developer Preview 标记和本地测试信息。
- Sidebar、settings、testing page、status card 仍有硬编码颜色、字号和卡片样式，未完全接入 tokens。
- Shell 仍有普通用户可见的图标资源状态、环境状态和默认路径等内容，需要控制主界面密度。

### 2.2 Bioinformatics UI

审计范围：

- `app/bioinformatics/project_home.py`
- `app/bioinformatics/workspace.py`
- `app/bioinformatics/workflow_pages.py`
- `app/bioinformatics/pages/*_page.py`

现状：

- 项目首页、数据来源、数据识别、Ready 检查、标准化、分析任务、结果浏览、项目报告已经接入 MainLine Shell，并多数使用 `bioinformatics_project_home_stylesheet()`。
- Bioinformatics 已有统一 helper：`_header()`、`_card()`、`_button()`、`_status_label()`，并开始使用 `buttonRole=primary_next/primary_action/back/secondary/danger`。
- 主流程页面基本具备页面标题区、一句话说明、主操作区、状态区、内容卡片区、技术详情折叠区。
- 数据来源、识别、标准化页面对技术详情已有折叠意识。
- 分析任务中心、结果浏览和报告页仍暴露较多技术字段，例如 `task type`、`run id`、`DEG task plan`、参数 JSON、manifest、asset ID、result path、raw JSON 预览。
- 部分页面存在多个 `primaryButton` 并列，容易削弱“下一步”层级。
- `app/bioinformatics/pages/*_page.py` 使用重复的硬编码卡片样式和 error 颜色，尚未完全统一。
- `app/bioinformatics/legacy/*` 中存在大量旧样式和旧主色，但属于 legacy / sandbox，不应本阶段直接重构。

### 2.3 Meta Analysis UI

审计范围：

- MainLine `app/meta_analysis/workspace.py`
- dev/meta-analysis `app/meta_analysis/workspace.py`
- dev/meta-analysis `app/meta_analysis/pages/*.py`
- dev/meta-analysis `app/meta_analysis/workflow_pages.py`

现状：

- MainLine 只保留 Meta 最小入口和项目壳，明确提示完整流程在 `dev/meta-analysis` 开发。
- dev/meta-analysis 已经有 PICO/PICOS/PECO、检索策略、PubMed candidates、文献库诊断、去重 Review、筛选、全文、提取、质量评价、统计和报告导出等页面雏形。
- dev/meta-analysis 的 workspace 自带 `_meta_workspace_stylesheet()`，使用 `#0F766E`、`#111827`、`#D8DEE9`、`#F5F7F9` 等硬编码颜色，虽然接近 BioMedPilot 气质，但已经形成独立样式体系。
- Meta 页面按钮命名、状态文案和技术字段暴露多于 Bioinformatics，例如 `Draft ID`、`preview_id`、`queue_path`、`decisions_path`、`manifest`、`run_count`、`figure_id`、`path`、`schema`。
- Meta 当前 UI 很多页面通过 `_developer_details()` 折叠技术信息，这是正确方向，但仍有部分技术字段进入标题、列表或主摘要。
- Meta 后续筛选、全文、提取、质量评价页面风险较高：流程长、按钮多、状态多，若不统一 token 和页面骨架，容易形成另一套视觉语言。

### 2.4 LabTools 未来模块

MainLine 当前不存在 `app/labtools/`、`app/lab_tools/` 或 `app/lab/`。本阶段不得创建 LabTools 业务代码。

未来 LabTools 应作为 Shell 内的工具型模块接入，而不是独立桌面应用或独立主题。实验工具可采用更紧凑的工具布局，但必须遵守总色板、字体、按钮层级、状态标签、主界面不暴露技术字段和 Developer Preview 标记规则。

## 3. 已发现的不一致问题

### P0

- UI 总规范尚未写入 Global Development Manual，后续模块可能把局部 UI 设计置于 Shell 之上。
- dev/meta-analysis 已有独立 `_meta_workspace_stylesheet()` 和多级侧栏，若直接合入 MainLine，可能与 Shell 权威、Bioinformatics 流程导航和总色板冲突。
- LabTools 未来如果按工具集合自建导航和主题，会破坏跨模块一致性；需要先明确“接入 Shell，不自建视觉体系”。

### P1

- `app/ui_style_tokens.py` 中已有 `meta="#6B4FD8"` 和 `meta_soft="#F0EDFF"`，与用户指定总色板不一致。Meta 可以有业务识别色，但不得作为主色替代 deep navy / teal。
- Shell `sidebar.py`、`main_window.py`、`status_panel.py` 仍有分散硬编码样式。
- Bioinformatics `workflow_pages.py` 分析任务中心同时提供多个主按钮：配置 DEG、生成任务记录、校验输入、创建任务、运行 GEO 差异分析，主操作层级不清。
- Bioinformatics 结果浏览页直接显示“打开参数 JSON”、结果路径、warning、DEG 技术列；应改为主界面摘要，技术详情折叠。
- Meta PICO、检索、文献库、去重页面仍可见 `Draft ID`、`preview_id`、`queue_path`、`decisions_path` 等技术字段。
- Meta 多个页面使用英文或混合技术短语作为主界面文案，例如 `testing-level`、`Merge preview`、`active record`、`study unit`、`effect row`、`run_count`。

### P2

- 卡片半径存在 8px、14px、18px、20px 混用。桌面工具面建议普通卡片统一 8px，登录品牌大卡可作为例外记录。
- 字号存在 18px、20px、22px、24px、26px、28px、30px、44px 混用。应明确 Shell 标题、页面标题、卡片标题、正文、辅助说明、表格字号。
- 状态标签颜色分散：warning、danger、success、preview badge 在不同页面使用不同色值。
- Bioinformatics 和 Meta 的“下一步”按钮有时使用 primary，有时使用 secondary，语义不稳定。
- “返回模块首页”“返回首页”“返回模块选择首页”“返回数据导入与检索”等用语需要统一规则。

### P3

- legacy UI 目录中存在旧蓝色、旧紫色、旧按钮体系和旧卡片样式，当前不应直接重构；只要求不得作为新 UI 参考。
- 旧 `docs/biomedpilot_ui_design_standard.md` 可保留，但后续应逐步与本次 UI Design Principles 合并或标记为阶段性标准。

## 4. 颜色审计

总色板应固定为：

- 深海军蓝 `#12324A`
- 青绿色 `#1BAE9F`
- 浅灰背景 `#F5F7F9`
- 白色 `#FFFFFF`

审计结果：

- Shell / Bioinformatics 主体基本遵守 deep navy、teal、white、light gray。
- `COLORS["meta"] = "#6B4FD8"` 存在潜在冲突。后续应避免把紫色作为 Meta 主色；如保留，只能作为次级图表或局部标签色。
- dev/meta-analysis 使用 `#0F766E` 作为 primary，与 `#1BAE9F` 接近但不一致，应合并到统一 token。
- Error、Warning、Success 色值目前分散，应抽取为统一状态 tokens。
- 所有新增 UI 不得直接硬编码主色，应通过 shared UI tokens 使用。

建议进入 shared UI tokens：

- `color.background.default = #F5F7F9`
- `color.surface.default = #FFFFFF`
- `color.brand.navy = #12324A`
- `color.brand.teal = #1BAE9F`
- `color.text.primary`
- `color.text.secondary`
- `color.border.default`
- `color.status.ready/warning/error/draft/confirmed/not_ready`

## 5. 字体与字号审计

当前问题：

- 标题层级跨模块不稳定。
- Meta 页面和部分旧页面的 18px / 20px / 22px 标题与 Shell 28px 模块标题、Bioinformatics 26px 页面标题之间缺少规则。
- 辅助说明、状态文本、表格内容有时过密；中文阅读体验需要更克制的行长和分区。

建议规则：

- App / 模块入口标题：26-28px。
- 页面标题：22-24px。
- 卡片标题：16-18px。
- 正文：13-14px。
- 辅助说明：12-13px。
- 表格正文：12-13px。
- 状态标签：12-13px，短文案。

## 6. 布局与间距审计

当前 Shell 和 Bioinformatics 已接近 Apple-like macOS premium desktop 风格：浅灰背景、白色卡片、轻边框、克制按钮。

需要统一的页面结构：

1. 页面标题区：模块名 / 当前步骤 / Developer Preview 标记。
2. 一句话说明：只说明当前页目的，不写长背景。
3. 主操作区：最多一个当前主按钮；其他动作降为次要或进入更多操作。
4. 状态摘要区：展示 Ready、Warning、Draft、Confirmed 等短状态。
5. 内容卡片区：主表、列表、输入表单。
6. 右侧详情或下方折叠区：技术详情、路径、manifest、raw JSON。
7. 底部流程按钮：返回、下一步。

当前风险：

- Bioinformatics 分析任务中心和 Meta 长流程页按钮过多，主操作区容易变成命令面板。
- Meta 三栏结构可能与 MainLine Shell 的左侧 Sidebar 叠加，形成双重导航。
- LabTools 工具型页面未来可能倾向小工具堆叠，需要规定工具卡密度和状态展示。

## 7. 按钮与操作层级审计

建议统一按钮语义：

- 主要按钮：当前页面最重要动作，例如“继续：数据识别”“确认研究问题”“生成标准化资产”。
- 下一步按钮：统一“下一步：{目标步骤}”。
- 返回按钮：统一“返回：{上一步或模块首页}”。
- 次要按钮：刷新、查看详情、导出、选择文件、复制。
- 危险按钮：删除、清理、移除，并使用统一 danger token。
- 文本按钮：只用于低风险轻量动作，不作为主要流程入口。

当前问题：

- Bioinformatics 多个页面存在多个 primary 并列。
- Meta 多个页面把生成、保存、确认、下一步都放在同一按钮行，层级需要收敛。
- “添加到项目”“选择加入文献库”“导入选中文献”“确认全部检索式”等动词体系需要统一成“选择 / 导入 / 确认 / 继续”的有限集合。

## 8. 导航与流程结构审计

结论：

- MainLine Shell 应作为模块入口和全局导航的统一框架。
- Bioinformatics 和 Meta Analysis 都应采用“流程型页面”结构，保留步骤导航和下一步引导。
- LabTools 属于“工具型页面”，可采用工具列表 + 单工具工作区，但仍必须挂在同一 Shell 内。

流程型页面适用于：

- Bioinformatics 数据导入、识别、标准化、分析任务、结果、报告。
- Meta PICO、检索、导入、去重、筛选、全文、提取、质评、分析、报告。

工具型页面适用于：

- LabTools 稀释、浓度、qPCR、Western blot、ELISA、细胞计数等单点计算或记录。

工具型页面不得自建新的全局导航、全局主色或独立 app 入口。

## 9. 文案风格审计

统一原则：

- 普通主界面中文友好，短句优先。
- 技术诊断、manifest、schema、asset id、run id、raw path、branch、完整 JSON 不进入主界面。
- 技术细节进入折叠区、诊断页、开发者详情或 handoff 文档。
- 区分三类文案：普通用户文案、研究人员文案、开发者诊断文案。

当前问题：

- MainLine Settings / Testing page、Bioinformatics 分析任务中心、Meta 多个页面仍有技术词直接可见。
- Meta 文案中 English label、Draft ID、Merge preview、run_count 等需要中文化或折叠。
- Bioinformatics 项目首页已把 manifest/config 放入技术详情，方向正确。

## 10. 状态展示审计

建议统一状态标签：

| 状态 | 中文主文案 | 使用场景 |
| --- | --- | --- |
| Ready | 已就绪 | 可进入下一步 |
| Not Ready | 未就绪 | 缺少必要输入 |
| Warning | 需注意 | 可继续但有提醒 |
| Error | 错误 | 当前动作失败或阻塞 |
| Draft | 草稿 | AI / 系统生成但未确认 |
| Confirmed | 已确认 | 用户已确认 |
| Testing | 测试级 | 内部测试能力 |
| Blocked | 阻塞 | 需补充输入或依赖 |

当前问题：

- Bioinformatics 同时使用 Ready、warning、error、preview、可运行/不可运行、暂无、未开始。
- Meta 同时使用 Testing / Developer Preview、内部测试、草稿、待确认、M17/testing、preliminary、pending 等。
- 状态标签颜色、位置、文案长度需要统一组件化。

## 11. 跨模块冲突风险

### Bioinformatics

Bioinformatics 已接近 Shell 风格，但后续风险是分析任务中心和结果页继续把技术命令面板暴露给普通用户。应优先拆分“主流程”和“开发者诊断”。

### Meta Analysis

Meta 当前功能面长、状态多、按钮多，已经具备独立视觉体系的趋势。合入 MainLine 前必须先对齐 shared UI tokens、统一 Shell 导航、统一按钮层级和中文文案。

### LabTools

LabTools 未来因为工具属性，容易做成独立工具箱或小工具集合。必须明确：LabTools 是 Shell 内模块，不是独立视觉系统。

### Global Manual

必须加入 UI 总规范优先级条款，防止模块局部设计覆盖总规范。

## 12. 应进入 shared UI tokens 或统一组件的内容

应抽取：

- 颜色 tokens：品牌色、背景、表面、边框、文本、状态色。
- 字号 tokens：模块标题、页面标题、卡片标题、正文、辅助说明、表格。
- 间距 tokens：4/8/12/16/24/32。
- 半径 tokens：4/8，登录品牌区等大半径作为例外。
- 按钮组件：primary、secondary、danger、text、primary_next、primary_action、back。
- 卡片组件：page header、content card、summary card、status card、developer details。
- 状态标签组件：Ready、Not Ready、Warning、Error、Draft、Confirmed、Testing、Blocked。
- 技术详情组件：默认折叠，统一标题“开发者详情”或“技术详情”。
- 流程页模板和工具页模板。

## 13. 暂时只记录、不立即重构

本阶段不重构：

- Bioinformatics 业务页面逻辑。
- Meta Analysis 业务流程页面。
- LabTools 业务代码。
- legacy UI / sandbox 目录。
- 旧 `docs/biomedpilot_ui_design_standard.md`。
- 分散硬编码样式。

这些内容应进入后续 UI Stage，以小范围、可测试的方式逐步替换。

## 14. 后续 UI 开发优先级规则

1. UI Governance / UI Design Principles 是跨模块界面开发最高优先级依据。
2. Global Development Manual、架构文档和模块边界仍优先于任何 UI 美化需求。
3. MainLine Shell 是全局入口和视觉权威；模块不得自建冲突的 Shell、主色、字体、按钮体系或全局导航。
4. 模块可做业务适配，但只能在总色板、共享 tokens、统一组件和页面模板内适配。
5. 普通主界面优先服务研究人员流程；技术字段必须折叠或进入开发者详情。
6. 新增 UI 页面必须说明自己属于流程型页面还是工具型页面。
7. 合入 MainLine 前必须通过对应 UI tests、smoke test，并确认 Developer Preview / testing-level 标记不被删除。
