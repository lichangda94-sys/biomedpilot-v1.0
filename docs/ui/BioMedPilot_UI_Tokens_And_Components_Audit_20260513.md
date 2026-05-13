# BioMedPilot UI Stage 0.2：Shared UI Tokens / Common Components 审计与轻量抽取方案

日期：2026-05-13
范围：MainLine `app/shell`、`app/bioinformatics`、`app/meta_analysis`、`app/shared`、现有 UI token 入口与 UI 测试
阶段定位：承接 UI Stage 0.1，只建立轻量 shared UI 基础层，不重写业务页面，不开发 LabTools 业务代码。

## 1. 当前 UI Tokens 分散情况

当前主线已有一个集中样式入口：`app/ui_style_tokens.py`。它被 Shell 登录页、模块选择页、Bioinformatics 项目首页与 workflow 页面使用，包含 `COLORS`、`SPACING`、`CONTROL_HEIGHT`、`RADIUS`、`FONT_SIZE` 以及登录、模块选择、生信项目页的 QSS。

但该入口存在三类治理问题：

1. 位置不在 `app/shared` 下，权威性更像局部工具文件，不足以约束 Bioinformatics、Meta Analysis、未来 LabTools。
2. 颜色、字号、半径和控件高度与具体 QSS 混在同一文件中，后续很容易继续扩张成“样式大文件”。
3. 仍存在大量页面级内联 `setStyleSheet`，包括 Shell card、Sidebar、StatusPanel、Bioinformatics 子页面、Meta mainline workspace。

Stage 0.2 已建立新的 shared UI token 基础层：

- `app/shared/ui/theme.py`
- `app/shared/ui/__init__.py`

并让 `app/ui_style_tokens.py` 继续作为兼容入口，从 shared theme 导出旧字典，避免一次性改动既有页面。

## 2. 当前颜色硬编码情况

### 主色与基础色

UI 总规范要求主色板为：

- 深海军蓝：`#12324A`
- 青绿色：`#1BAE9F`
- 浅灰背景：`#F5F7F9`
- 白色：`#FFFFFF`

现状：

- `app/ui_style_tokens.py` 已集中使用上述主色中的 `#12324A`、`#1BAE9F`、`#F5F7F9`、`#FFFFFF`。
- Shell 的 `sidebar.py`、`status_panel.py`、`main_window.py` 仍直接硬编码 `#F8FAFC`、`#D8DEE9`、`#FFFFFF`、`#EAF0F7`、`#64748B` 等。
- Bioinformatics 多个 `app/bioinformatics/pages/*_page.py` 直接硬编码 summary card、错误色、警告色，例如 `#D8DEE9`、`#FFFFFF`、`#B42318`、`#92400E`。
- Bioinformatics legacy 工具仍保留大量历史硬编码蓝灰色系和旧按钮蓝色，例如 `#315f9e`、`#294f84`。这些属于 legacy 范围，Stage 0.2 只记录，不迁移。
- Meta mainline `app/meta_analysis/workspace.py` 目前以内联字号为主，颜色硬编码较少，但缺少 shared QSS 接入。

### 当前结论

颜色 token 应进入 shared UI。Stage 0.2 已抽取：

- `BioMedPilotColors.PRIMARY_NAVY`
- `BioMedPilotColors.ACCENT_TEAL`
- `BioMedPilotColors.BACKGROUND_LIGHT`
- `BioMedPilotColors.SURFACE_WHITE`
- `BioMedPilotColors.TEXT_PRIMARY`
- `BioMedPilotColors.TEXT_SECONDARY`
- `BioMedPilotColors.BORDER_SUBTLE`
- `BioMedPilotColors.STATUS_READY`
- `BioMedPilotColors.STATUS_WARNING`
- `BioMedPilotColors.STATUS_ERROR`
- `BioMedPilotColors.STATUS_DRAFT`
- `BioMedPilotColors.STATUS_CONFIRMED`

为兼容现有页面，`app/ui_style_tokens.py` 的旧键名仍保留，例如 `bio`、`bio_accent`、`meta`、`warning_soft`、`danger`。其中 `meta`、`meta_soft` 仅作为迁移期 legacy alias，不应成为未来 Meta 独立主色依据。

## 3. 当前按钮样式分散情况

现状：

- Shell 登录页和模块选择页主要通过 `app/ui_style_tokens.py` 的 QSS 管理按钮。
- Bioinformatics workflow 使用 `primaryButton`、`secondaryButton`、`ghostButton`、`dangerButton`、`projectActionButton` 等 objectName 或属性组合，视觉语言相对接近，但主按钮与确认/保存/加入队列等语义尚未完全统一。
- Bioinformatics 子页面仍有默认 QPushButton 或局部 QSS，缺少统一 action role。
- Meta mainline workspace 的按钮主要是默认 QPushButton，仅有 `metaBackButton` objectName，尚未接入统一按钮层级。
- 当前尚无 shared button helper 或 shared button component。

建议统一的按钮角色：

- `primary action`：当前页面最推荐的主动作。
- `secondary action`：并列但非主路径动作。
- `quiet / text action`：低强调查看、取消、折叠。
- `destructive action`：删除、清空、不可逆操作。
- `navigation action`：下一步、返回。
- `detail action`：查看详情、展开诊断。
- `confirm action`：确认、保存。

Stage 0.2 已在 shared theme 中记录 `BioMedPilotButtonRoles`，但暂不创建 QPushButton 子类，也不替换现有业务页面按钮。

## 4. 当前状态标签分散情况

现状：

- Bioinformatics 项目首页已有 `bioProjectStatusLabel`、`bioValidationAlert`、`bioStepBadge` 等视觉对象，状态色主要在 `app/ui_style_tokens.py` 内定义。
- Bioinformatics workflow 中存在 Ready / Not Ready / Warning / Error / Draft / Confirmed / Running / Completed 等状态语义，但标签文字、显示位置、背景和边框没有完全组件化。
- Shell 的功能可用性、图标状态、测试模式状态使用各自的文本展示。
- Meta mainline workspace 中 `Mainline shell`、`测试中`、项目 manifest 状态等信息仍以普通 QLabel 文本呈现，容易把开发边界文案与用户状态混在一起。

Stage 0.2 已抽取 `BioMedPilotStatusStyle` 和 `BioMedPilotStatusColors`，覆盖：

- `ready` / 已就绪
- `not_ready` / 未就绪
- `warning` / 需注意
- `error` / 错误
- `draft` / 草稿
- `confirmed` / 已确认
- `running` / 运行中
- `completed` / 已完成
- `testing` / 测试中
- `blocked` / 受阻

当前只提供 token 与样式结构，不创建 status badge QWidget。后续 Stage 0.3 可在 shared components 中建立 `StatusBadge` 或 QSS helper。

## 5. 当前卡片 / 页面布局分散情况

现状：

- `app/ui_style_tokens.py` 中 `RADIUS` 为 `sm=8`、`md=14`、`lg=20`，Shell 页面又直接写入 `border-radius: 8px`。
- Shell entry card、list card、recent projects card 直接写入相同边框与背景。
- Bioinformatics 项目首页和 workflow 卡片多数通过 `bioinformatics_project_home_stylesheet()` 管理，但普通子页面仍直接写 summary card QSS。
- Meta mainline workspace 的页面结构是左侧流程列表 + 右侧 page stack，但还没有统一 page header、content card、boundary notice 样式。
- `app/shared/ui_components` 当前只有占位性质，未形成可复用组件。

建议后续统一：

- `PageContainer`
- `PageHeader`
- `SectionCard`
- `SummaryCard`
- `WarningCard`
- `DiagnosticCard`
- `RightSideDetailPanel`
- `EmptyStatePanel`

Stage 0.2 仅抽取 `BioMedPilotSpacing`、`BioMedPilotRadii`、`BioMedPilotControlHeights`，不重构卡片组件。

## 6. 当前技术字段暴露情况

Stage 0.1 已确认“主界面不暴露过多技术字段”是 UI 总规范。Stage 0.2 复核后，仍需持续治理以下类别：

- `manifest path`
- `asset id`
- `run id`
- 完整本地路径
- internal schema version
- raw JSON
- diagnostic logs
- developer-only warnings

当前风险点：

- Meta mainline workspace 的状态文本会显示项目根目录和 manifest 相关错误，适合作为开发边界说明，但不应成为最终普通用户主界面文案。
- Shell 设置中心中的图标资源状态包含调用明细，当前作为测试/内部状态可接受，后续应放入诊断详情。
- Bioinformatics 中部分识别、标准化、任务执行页面需要继续检查是否把资产路径、manifest、raw package 信息直接展示在主流程。

Stage 0.2 未修改这些业务页面，只记录迁移原则：普通主界面只展示研究人员能理解的摘要；技术字段进入折叠详情、诊断页、开发者详情或日志文件。

## 7. 建议抽取到 Shared UI 的内容

应进入 shared UI tokens：

- 总色板与语义色：主色、强调色、背景、表面、文字、边框、状态色。
- 字体字号：页面标题、分区标题、卡片标题、正文、辅助说明、状态文本、按钮文本。
- 间距：页面边距、卡片内边距、控件间距、分区间距。
- 半径：普通卡片、面板、输入框、状态标签。
- 控件高度：输入框、普通按钮、主按钮。
- 状态样式：Ready、Not Ready、Warning、Error、Draft、Confirmed、Running、Completed。
- 按钮角色：primary、secondary、quiet、destructive、navigation、detail、confirm。

应进入 shared components 或 helper：

- `StatusBadge`
- `PageHeader`
- `ActionBar`
- `SectionCard`
- `DeveloperDetails`
- `EmptyStatePanel`
- `button_style_for_role`
- `status_badge_style_for_state`

其中 Stage 0.2 只做 tokens 与状态样式结构；组件层留到 Stage 0.3。

## 8. 当前阶段实际抽取了哪些内容

本阶段实际新增：

- `app/shared/ui/theme.py`
  - `BioMedPilotColors`
  - `BioMedPilotTypography`
  - `BioMedPilotSpacing`
  - `BioMedPilotRadii`
  - `BioMedPilotControlHeights`
  - `BioMedPilotButtonRoles`
  - `BioMedPilotStatusStyle`
  - `BioMedPilotStatusColors`
  - `status_style()`
  - `status_styles()`
  - legacy dict adapters
- `app/shared/ui/__init__.py`
  - 统一导出 shared UI tokens。
- `app/ui_style_tokens.py`
  - 保留现有 API，改为从 shared theme 生成 legacy dict，保证既有 Shell / Bioinformatics 页面不需要改导入。
- `tests/ui/test_shared_ui_theme.py`
  - 验证 shared UI tokens 可导入。
  - 验证 UI 总规范四个主色存在。
  - 验证旧 token 入口与 shared theme 值一致。
  - 验证基础状态样式覆盖跨模块状态语言。

本阶段没有修改 Bioinformatics、Meta Analysis、LabTools 的业务逻辑，也没有重写业务页面。

## 9. 哪些内容只记录，不立即修改

本阶段只记录，不立即处理：

- Shell card、Sidebar、StatusPanel 中的内联 QSS。
- Bioinformatics 普通子页面中重复的 summary card、error label、warning label 内联 QSS。
- Bioinformatics legacy UI 的旧蓝色、旧灰色、旧按钮样式。
- Meta mainline workspace 的完整 shared style 接入。
- `app/ui_theme.py` 的全局 Qt palette 颜色与 shared tokens 的对齐。
- shared QWidget 组件，如 `StatusBadge`、`PageHeader`、`SectionCard`。
- UI token 强制检查或 lint 规则。
- 技术字段折叠区和开发者详情组件。

原因：这些改动会触及较多页面，容易超出 Stage 0.2 的低风险轻量抽取范围，应在 Stage 0.3 以后按页面族逐步迁移。

## 10. 后续 UI Stage 0.3 建议

建议 Stage 0.3 目标为“common components 试点迁移”，不要一次性全量替换。

优先级建议：

1. 建立 shared style helper：
   - `status_badge_qss(status)`
   - `button_qss(role)`
   - `card_qss(kind)`
2. 在 Shell 的 `StatusPanel`、`MainWindow` card、`Sidebar` 中试点替换硬编码 QSS。
3. 在 Bioinformatics 普通 `pages/*_page.py` 中抽出 summary card 和 error/warning label helper。
4. 为 Meta mainline workspace 增加统一 page header、boundary notice、status badge，避免 Meta 后续形成独立视觉体系。
5. 将 `app/ui_theme.py` 的 Qt palette 迁移到 shared colors，减少 `#F8FAFC`、`#0F172A`、`#2563EB` 等非规范色的扩散。
6. 增加轻量 UI token 使用检查：新页面不得直接硬编码四个主色和常用状态色，必须引用 shared UI token 或 shared helper。
7. 建立 `DeveloperDetails` 折叠组件，承接 manifest、asset id、run id、完整路径、raw JSON、diagnostic logs。

## 11. 风险分级

### P0：会破坏 UI 总规范权威或导致跨模块视觉分裂

- Meta Analysis 完整功能合入主线时若继续使用独立主色、独立按钮体系或独立 status badge，将与 Shell / Bioinformatics 形成视觉分裂。
- 未来 LabTools 如果以“工具集合”为理由创建独立界面框架、颜色和按钮体系，会削弱主线 Shell 权威。
- 新页面如果继续直接硬编码主色和状态色，会让 Stage 0.1 UI 总规范无法执行。

### P1：明显影响界面一致性，应后续处理

- Shell 多个 card 与 sidebar 仍有重复硬编码边框、背景、半径和字号。
- Bioinformatics 子页面重复 summary card 和 error/warning label 样式，且错误/警告色与 shared status token 尚未统一。
- Meta mainline workspace 缺少统一状态标签、按钮角色和页面卡片样式。
- `app/ui_theme.py` 全局 palette 未使用 shared token，存在与 UI 总色板不完全一致的蓝色高亮。

### P2：可逐步优化

- `app/ui_style_tokens.py` 仍包含较长 QSS，未来可拆为 shared style helper 或业务页面样式 adapter。
- Bioinformatics legacy UI 保留旧视觉语言，但目前属于 legacy 范围，短期不影响主线 Shell。
- 字号体系已有初步 token，但不同页面中 18、20、22、24、28、30 等字号仍需后续统一。
- 半径体系中 `md=14`、`lg=20` 与 UI 总规范“普通卡片 8px 优先”需要在迁移时重新分层定义。

### P3：仅记录

- 当前 `app/shared/ui_components` 为空目录性质，暂不强制迁移。
- Meta mainline workspace 的 dev branch 边界说明在当前阶段可保留，但后续生产化前应收敛文案。
- Shell 设置中心的图标资源状态明细可继续用于测试阶段，后续归入诊断详情。

## 12. Stage 0.2 结论

BioMedPilot 当前具备部分集中样式基础，但 shared UI 权威层不足。Stage 0.2 已在 `app/shared/ui/theme.py` 建立低风险、纯 Python、无 Qt 依赖、无业务模块依赖的 token 基础层，并通过 legacy adapter 保持现有页面兼容。

后续模块 UI 开发应优先引用 `app.shared.ui.theme` 中的 shared tokens。新页面不得自行创建与 UI 总规范冲突的主色、字体、按钮体系、页面结构或状态标签视觉语言。业务模块可以根据流程做适配，但颜色、字号、间距、按钮层级、状态标签和技术字段展示原则必须服从 UI 总规范。
