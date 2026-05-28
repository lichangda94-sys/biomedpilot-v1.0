# UI-D6 Runtime Screenshot Issue Remediation Plan

Date: 2026-05-26

Status: discussion draft

## Scope

This document records product-owner review feedback for the 16 UI-D6 source-runtime screenshots and turns that feedback into a scoped remediation checklist.

This is a discussion and planning artifact only. It does not implement UI changes, packaging, App icon changes, Finder icon changes, `Info.plist` changes, LaunchServices validation, executor enablement, report generation, or export enablement.

Screenshot source:

- `docs/ui/runtime_screenshots/20260526_d6_runtime_review/`

Reference documents:

- `docs/ui/UI_D6_runtime_ui_screenshot_re_review_20260526.md`
- `docs/ui/UI_D6_runtime_screenshot_manifest_20260526.csv`
- `docs/ui/UI_B10_app_icon_packaging_scoped_plan_20260526.md`
- `docs/ui/UI_B10_app_icon_packaging_gate_matrix_20260526.csv`

## Review Method

Each screenshot should be reviewed with these fields:

- screenshot_id
- current issue observed
- product-owner remediation opinion
- severity: P0 / P1 / P2
- target behavior
- affected component or page area
- proposed stage
- implementation boundary
- verification needed
- status

Severity guide:

- P0: blocks packaging readiness or could mislead users about unavailable capabilities.
- P1: important visual hierarchy, density, or clarity issue that should be fixed before B10 if feasible.
- P2: polish issue that can be carried after B10.

## Global Boundaries

Remediation must not:

- enable Bioinformatics or Meta executors
- enable DEG, ORA, GSEA, KM, Cox, clinical formal execution, Network Meta, or formal pooled effects
- enable report generation or formal export
- show fake report-ready packages, fake plots, fake formal result tables, or fake export success
- install or configure external engines
- download, upload, update, or configure cloud services
- modify App icon, Finder icon, `.icns`, `Info.plist`, LaunchServices, packaging, `dist/**`, or desktop app bundles unless UI-B10 is explicitly started

## Product-Owner Global Rectification Principles

Source: user-provided plaintext rectification brief, `BioMedPilot_UI_Rectification_All_PlainText.txt`.

The global feedback applies to Dashboard and Settings immediately, and should guide later LabTools, Bioinformatics, and Meta polish:

- The current UI has basic structure but still reads too much like Qt default controls, development placeholders, and internal diagnostic pages.
- The target is not pixel-perfect mockup replication; the target is a modern, calm, low-noise biomedical desktop workbench UI.
- The first screen should communicate BioMedPilot / Firefly, the three core modules, and Developer Preview / local beta status without turning the product into a debug page.
- Internal terms such as `Shell only`, `detect-first`, `Resolver-first`, and `UI-D2 boundary` should not appear in ordinary user first-viewport surfaces.
- Shared UI tokens and reusable components should be the basis for remediation; do not continue page-local color, font, radius, spacing, and QSS drift.
- Chinese titles should carry the main meaning; English labels should support recognition rather than dominate the page.
- Common UI elements should come from shared components: AppShell, Sidebar, SidebarNavItem, BrandBlock, DeveloperPreviewCard, PageHeader, TopActionArea, StatusPill, BaseCard, buttons, ModuleEntryCard, RecentProjectsPanel, SettingsTabBar, SettingsRow, ExternalCapabilityOverviewCard, SystemInfoCard, and QuickActionCard.
- Settings and Dashboard should share the same shell, header, status, card, and button language.

## Screenshot Review Checklist

| # | screenshot_id | module | review status | severity | issue summary | product-owner opinion | proposed stage |
|---|---|---|---|---|---|---|---|
| 1 | dashboard_home | Dashboard | reviewed | P1 | 首页仍有 Qt 默认控件感、工程调试页感，品牌化工作台首页主视觉不足 | 按 BioMedPilot / Firefly 产品级工作台首页整改；先沉淀 token 和共享组件，再重做 Dashboard 结构 | Dashboard polish before UI-B10 |
| 2 | settings_home | Settings | reviewed | P1 | 设置页仍像配置字段表和开发状态说明页，缺少产品级设置中心总览结构 | 改为设置中心总览：产品化 TabBar、设置行、外部能力总览、系统信息卡、快速操作区；内部术语移入开发者诊断 | Settings polish before UI-B10 |
| 3 | labtools_home | LabTools | pending | TBD | TBD | TBD | TBD |
| 4 | labtools_general_calculator | LabTools | reviewed | P1 | 通用计算器仍像开发表单原型，任务库、输入区、结果面板和复核提示不够产品化 | 重构为 LabTools 计算工作台：左侧任务库、中间计算输入与公式求解、右侧结果卡片和提示、底部复核提示 | LabTools calculator polish before UI-B10 |
| 5 | labtools_reagent_preparation | LabTools | reviewed | P1 | 试剂制备仍像数据调试页，内部 adapter/storage 术语和长文本摘要占据主界面 | 重构为试剂制备工作台：模板卡片列表、本次配制输入、复核表格、模板编辑、底部操作与提示 | LabTools reagent polish before UI-B10 |
| 6 | labtools_wb_loading | LabTools | pending | TBD | TBD | TBD | TBD |
| 7 | labtools_experiment_boundaries | LabTools | pending | TBD | TBD | TBD | TBD |
| 8 | bioinformatics_project_home | Bioinformatics | pending | TBD | TBD | TBD | TBD |
| 9 | bioinformatics_data_source | Bioinformatics | pending | TBD | TBD | TBD | TBD |
| 10 | bioinformatics_analysis_tasks | Bioinformatics | pending | TBD | TBD | TBD | TBD |
| 11 | bioinformatics_result_export | Bioinformatics | pending | TBD | TBD | TBD | TBD |
| 12 | meta_project_home | Meta Analysis | pending | TBD | TBD | TBD | TBD |
| 13 | meta_question_type | Meta Analysis | pending | TBD | TBD | TBD | TBD |
| 14 | meta_search_strategy | Meta Analysis | pending | TBD | TBD | TBD | TBD |
| 15 | meta_screening_extraction | Meta Analysis | pending | TBD | TBD | TBD | TBD |
| 16 | meta_result_export | Meta Analysis | pending | TBD | TBD | TBD | TBD |

## Per-Screenshot Notes

### 1. dashboard_home

- Current issue observed:
  - Dashboard 已有基础信息结构，但整体仍偏 Qt 默认控件、工程调试页和线框页面。
  - 首页主视觉被系统信息、开发状态和内部工程文案稀释，没有第一眼形成产品级工作台感。
  - 侧边栏品牌感、导航激活态和底部版本区不够强。
  - Header 像系统信息卡，不像轻量页面标题区。
  - 三个模块入口卡片没有形成主视觉，图标偏小，按钮偏普通，模块色不够清晰。
  - 最近项目区域偏默认表格和工程数据表，空表或路径字段会破坏工作恢复入口定位。
  - 状态标签、按钮、卡片、间距、圆角、字号仍需要统一 token 和组件约束。
- Product-owner remediation opinion:
  - 不逐像素仿图，不新增第三方 UI 依赖，不改业务逻辑和模块路由。
  - 将 Dashboard 整改为 BioMedPilot / Firefly 的统一桌面产品级工作台首页。
  - 首屏需要传达三件事：BioMedPilot / Firefly 是本地生物医学研究工作台；核心模块是 Bioinformatics、Meta Analysis、LabTools；当前版本是 Developer Preview / 本地测试版。
  - Dashboard 不应成为系统信息页、配置页或开发调试页。
  - 当前用户、版本、路径、Shell only、Resolver-first 等内部信息不应占据首页主视觉。
  - 版本信息应放在侧边栏底部、Settings 或 About；内部开发状态弱化为 badge 或 tooltip。
  - 中文为主、英文为辅；功能描述优先，架构描述弱化。
- Severity: P1
- Target behavior:
  - 浅色背景、医学科研工具感、品牌化侧边栏、大模块入口卡片、统一圆角、低对比浅边框、清晰状态标签、舒适留白。
  - 首页第一眼看到品牌、页面标题、三大模块入口和最近项目恢复入口。
  - Dashboard Header 使用轻量标题区：`萤火虫 工作台 / Firefly Workbench`，副标题为本地生物医学研究统一工作台说明，Developer Preview 仅作为小 badge。
  - 三个模块入口卡片高度一致、颜色区分明确、具有大图标或插画、状态使用统一 pill、按钮为宽主入口按钮。
  - 最近项目区表现为工作恢复入口；有数据时是弱网格列表，无数据时是空状态，不展示巨大空表。
- Affected component or page area:
  - design tokens / QSS style helpers
  - AppShell / Sidebar
  - SidebarNavItem
  - DeveloperPreviewCard
  - PageHeader
  - ModuleEntryCard
  - StatusChip / StatusPill
  - ActionButton variants
  - WorkbenchCard / BaseCard
  - RecentProjectsPanel
  - RecentProjectsTable or empty state
- Proposed stage:
  - `UI-D6-P1-dashboard-token-alignment`: align Dashboard to existing `app/ui_style_tokens.py` and shared UI component contracts.
  - `UI-D6-P1-dashboard-shell-polish`: rebuild Dashboard shell composition with shared Sidebar, PageHeader, ModuleEntryCard, StatusChip, ActionButton, WorkbenchCard, and EmptyState.
  - `UI-D6-P1-dashboard-recent-projects-polish`: replace default table feel with productized Recent Projects panel.
  - Complete before UI-B10 if Dashboard visual acceptance is required for packaging readiness.
- Implementation boundary:
  - Reuse and extend existing BioMedPilot-native PySide primitives where possible, especially existing shared component files and `app/ui_style_tokens.py`.
  - Do not introduce React, Tailwind, browser UI code, Google Fonts, or third-party UI libraries.
  - Do not change business logic, module routing, executor availability, report/export gates, installer/download/upload/engine/cloud behavior, or project data semantics.
  - Do not touch App icon, Finder icon, `.icns`, `Info.plist`, LaunchServices, packaging, `dist/**`, or desktop app bundles in this Dashboard remediation.
- Verification needed:
  - Focused UI tests for shared component construction and Dashboard route rendering.
  - Source runtime smoke.
  - Runtime screenshot recapture for `dashboard_home`.
  - Visual review against this issue list.
  - `git diff --check` and `git diff --cached --check` before commit.
- Status: reviewed; planning accepted pending implementation authorization

### 2. settings_home

- Current issue observed:
  - Settings 当前像配置字段表和开发状态说明页，不像面向用户的设置中心。
  - 页面首屏内容偏空，信息架构没有形成设置中心总览。
  - 通用偏好以字段表呈现，不像可操作的设置项。
  - TabBar 像普通按钮组，缺少产品化横向标签结构。
  - 缺少右侧外部能力检测总览。
  - 缺少系统信息卡片。
  - 缺少底部快速操作区。
  - `Shell only`、`detect-first`、`UI-D2 boundary` 等内部词暴露在普通设置首页。
- Product-owner remediation opinion:
  - Settings 应重构为设置中心总览页，而不是配置字段表。
  - 页面标题应为 `设置中心 / Settings`。
  - 页面副标题应为 `管理全局偏好、外部能力、分析资源与系统配置。`
  - 使用统一 PageHeader、TopActionArea、Sidebar、StatusPill、Button、Card 体系。
  - 普通用户设置首页不显示 `Shell only`、`detect-first`、`UI-D2 boundary` 等内部词。
  - `UI-D2 boundary` 迁移到“开发者诊断”Tab 内，默认折叠。
  - Settings 首页只展示检测状态和配置入口，不执行外部能力调用。
- Severity: P1
- Target behavior:
  - Settings 首屏结构为 `PageHeader + SettingsTabBar + ContentGrid + QuickActionsPanel`。
  - SettingsTabBar 是横向浅色容器，包含通用偏好、外部能力、分析资源、模型与引擎、开发者诊断。
  - 通用偏好使用 SettingsRow：界面与语言、数据与存储、行为与启动、隐私与安全。
  - 右侧显示 ExternalCapabilityOverviewCard，包含能力、状态、说明、操作，并使用统一 StatusPill。
  - 左下显示 SystemInfoCard，包含版本、运行模式、操作系统、内存、磁盘等信息；进度条应低干扰。
  - 底部显示 QuickActionsPanel：管理默认路径、检查更新、清理缓存、导出日志。
  - 设置页与 Dashboard 共用同一 Sidebar、PageHeader、TopActionArea、卡片、按钮和状态语言。
- Affected component or page area:
  - SettingsPage composition
  - SettingsTabBar
  - SettingsRow
  - ExternalCapabilityOverviewCard
  - ExternalCapabilityRow
  - SystemInfoCard
  - QuickActionCard / QuickActionsPanel
  - Sidebar
  - PageHeader / TopActionArea
  - StatusChip / StatusPill
  - ActionButton variants
  - WorkbenchCard / BaseCard
- Proposed stage:
  - `UI-D6-P1-settings-shell-polish`: align Settings shell with shared AppShell, Sidebar, PageHeader, and TopActionArea.
  - `UI-D6-P1-settings-tabs-and-rows`: replace button-like tabs and field-table preferences with SettingsTabBar and SettingsRow.
  - `UI-D6-P1-settings-overview-cards`: add productized external capability overview, system info, and quick actions as display/configuration-entry surfaces.
  - Complete before UI-B10 if Settings visual acceptance is required for packaging readiness.
- Implementation boundary:
  - Reuse or extend existing BioMedPilot-native shared PySide components and `app/ui_style_tokens.py`.
  - Do not add third-party UI dependencies or copy third-party UI source.
  - Do not trigger installs, downloads, updates, external engine execution, cloud configuration, executor calls, report generation, or export.
  - Do not make optional or unavailable external capabilities look formally available.
  - Do not touch App icon, Finder icon, `.icns`, `Info.plist`, LaunchServices, packaging, `dist/**`, or desktop app bundles in this Settings remediation.
- Verification needed:
  - Focused UI tests for Settings component construction and tab rendering where practical.
  - Source runtime smoke.
  - Runtime screenshot recapture for `settings_home`.
  - Visual review against this issue list.
  - `git diff --check` and `git diff --cached --check` before commit.
- Status: reviewed; planning accepted pending implementation authorization

### 3. labtools_home

- Current issue observed: TBD
- Product-owner remediation opinion: TBD
- Severity: TBD
- Target behavior: TBD
- Affected component or page area: TBD
- Proposed stage: TBD
- Implementation boundary: TBD
- Verification needed: TBD
- Status: pending

### 4. labtools_general_calculator

- Current issue observed:
  - 页面已有三栏雏形，但整体仍偏开发占位页和默认 Qt 表单。
  - 页面副标题暴露后端接入、保存历史和导出禁用等开发说明。
  - Developer Preview 是横向长条，视觉过重。
  - `backend_ready`、`ui_adapter_needed`、`Draft calculation output`、`草稿`、`保存本地记录摘要` 等内部或开发式状态暴露在普通用户界面。
  - 左侧任务栏只有下拉框和说明，无法体现“计算任务库”。
  - 中间输入区过于简陋，缺少标准变量命名、单位选择层级、公式提示和动态公式求解区域。
  - 右侧结果区像大文本输出框，不像结果卡片和复核面板。
  - 缺少醒目的实验计算复核与安全提示。
  - Sidebar 和 TopActionArea 未统一到产品级全局组件。
- Product-owner remediation opinion:
  - 通用计算器应定位为 LabTools 二级工具页面，用于快速计算和动态公式求解。
  - 页面应强调“计算流程”和“用户复核”，而不是显示 backend、adapter、draft 等内部状态。
  - 标题保留 `通用计算器 / General Calculator`。
  - 副标题改为用户语言：`快速计算与动态公式求解，结果需用户复核。`
  - `Developer Preview` 只保留为小型 `本地测试版` badge。
  - 保存和导出保留禁用状态，但通过禁用按钮和原因表达，不在页面副标题中说明。
- Severity: P1
- Target behavior:
  - 页面结构为 `PageHeader + CalculatorModeTabs + CalculatorWorkspace + SafetyNoticeBar`。
  - CalculatorWorkspace 为三栏：左侧计算任务库，中间计算输入和动态公式求解，右侧计算结果、提示和操作。
  - 左侧 TaskPanel 提供搜索框和任务列表：稀释计算、单位换算、细胞铺板辅助、摩尔浓度/称量质量、百分比溶液、Serial Dilution、C1 * V1 = C2 * V2。
  - 中间 QuickDilutionCard 使用标准字段：原液浓度 (C1)、目标浓度 (C2)、目标总体积 (V2)、溶剂/稀释液、备注，并提供单位下拉。
  - 中间 FormulaSolverCard 展示公式、求解目标、变量输入和示例/清空操作。
  - 右侧 ResultPanel 用结果卡片展示所需原液体积、溶剂体积和公式求解结果，不再使用大文本框。
  - 右侧提示与注意事项使用浅橙 WarningNoticeCard。
  - 操作区包含复制结果主按钮、保存到历史禁用按钮、导出结果禁用按钮。
  - 底部 SafetyNoticeBar 明确提示计算结果不替代实验设计与结果判断。
- Affected component or page area:
  - GeneralCalculatorPage composition
  - PageHeader / TopActionArea
  - Sidebar
  - ModeSegmentedTabs / CalculatorModeTabs
  - CalculatorTaskPanel / CalculatorTaskItem
  - CalculatorInputCard / QuickDilutionCard
  - FormulaSolverCard
  - ResultPanel / ResultValueCard
  - WarningNoticeCard / NoticeBar
  - PrimaryActionButton / SecondaryActionButton / DisabledActionButton
  - StatusChip / StatusPill
- Proposed stage:
  - `UI-D6-P1-labtools-calculator-shell-polish`: align shell, header, sidebar, top actions, preview badge, and breadcrumb.
  - `UI-D6-P1-labtools-calculator-workspace`: productize task library, input/formula cards, result panel, and safety notice.
  - Complete before UI-B10 if LabTools visual acceptance is required for packaging readiness.
- Implementation boundary:
  - Reuse or extend existing BioMedPilot-native shared PySide components and `app/ui_style_tokens.py`.
  - Do not add third-party UI dependencies.
  - Do not change existing calculation logic.
  - Do not enable unfinished save, export, history, report, file writer, installer, download, upload, engine, or cloud behavior.
  - Do not present calculation output as formal report or direct experimental instruction; keep user复核 semantics visible.
  - Do not touch App icon, Finder icon, `.icns`, `Info.plist`, LaunchServices, packaging, `dist/**`, or desktop app bundles in this remediation.
- Verification needed:
  - Focused UI tests for calculator component construction and disabled save/export reasons where practical.
  - Source runtime smoke.
  - Runtime screenshot recapture for `labtools_general_calculator`.
  - Visual review against this issue list.
  - `git diff --check` and `git diff --cached --check` before commit.
- Status: reviewed; planning accepted pending implementation authorization

### 5. labtools_reagent_preparation

- Current issue observed:
  - 页面已有模板、配制、详情三个区域，但整体仍像开发占位页和数据调试页。
  - 页面副标题暴露 project storage、保存历史试点、导出禁用等开发说明。
  - Developer Preview 是横向长条，视觉过重。
  - 普通用户界面暴露 `backend_ready`、`storage_adapter_needed`、`project_storage`、`FilePickerExportAdapter`、`missing_project_context`、`in-memory demo template` 等内部术语。
  - 左侧模板列表不产品化，且本地试剂引用/管理表单占据主流程空间。
  - 中间本次配制输入和结果混杂，长文本摘要占据过多主视觉。
  - 配制结果应以复核表格呈现，而不是主要依赖大文本框。
  - 右侧模板详情像开发诊断，未形成模板编辑面板。
  - 操作按钮分散，保存/导出语义不清。
  - 缺少清晰的 SOP、试剂纯度、pH、温度、安全和用户复核提示。
- Product-owner remediation opinion:
  - 试剂制备应定位为 LabTools 二级工作台，用于模板选择、本次配制、计算组分用量、生成复核清单、复制摘要，以及展示保存/导出后续适配状态。
  - 标题保留 `试剂制备 / Reagent Preparation`。
  - 副标题改为用户语言：`试剂模板、本次配制与复核清单，计算结果需用户复核后用于实验。`
  - 内部 backend/storage/project context/adapter 类名迁移到开发者诊断或 tooltip，不占据普通主界面。
  - 保存和导出必须保持禁用或需适配状态，不可表现为已完成。
- Severity: P1
- Target behavior:
  - 页面结构为 `PageHeader + ReagentPreparationWorkspace + BottomActionBar + NoticeBars`。
  - 主工作区为三栏：左侧 TemplatePanel，中间 PreparationPanel，右侧 TemplateEditorPanel。
  - 左侧 TemplatePanel 展示试剂模板卡片列表，包含搜索、分类筛选、排序、新增按钮和模板卡片；本地试剂库管理不放在主流程首屏。
  - 中间 PreparationPanel 展示本次配制输入：目标体积、操作人、日期、批次备注、pH 目标值、pH 实测值、pH 调整后。
  - 中间下方 PreparationResultTable 展示组分、类型、所需量、单位、用户复核 checkbox；默认不自动勾选。
  - 配制摘要默认不以大文本框占据主界面，可通过“复制配制摘要”生成或折叠预览。
  - 右侧 TemplateEditorPanel 展示模板信息、组分设置、验证与提示、保存模板禁用按钮。
  - 底部 BottomActionBar 包含复制配制摘要、保存配制记录 - 需存储适配、导出记录 - 需文件选择器适配。
  - NoticeBars 包含保存路径提示和实验复核安全提示。
- Affected component or page area:
  - ReagentPreparationPage composition
  - PageHeader / TopActionArea
  - Sidebar
  - TemplatePanel / ReagentTemplateCard
  - PreparationInputCard
  - PreparationResultTable
  - TemplateEditorPanel
  - ComponentTable
  - ValidationChecklist
  - BottomActionBar
  - NoticeBar / WarningNoticeCard
  - PrimaryActionButton / DisabledActionButton
  - StatusChip / StatusPill
- Proposed stage:
  - `UI-D6-P1-labtools-reagent-shell-polish`: align shell, header, sidebar, top actions, preview badge, and breadcrumb.
  - `UI-D6-P1-labtools-reagent-workspace`: productize template list, preparation input, result table, template editor, bottom action bar, and notices.
  - Complete before UI-B10 if LabTools visual acceptance is required for packaging readiness.
- Implementation boundary:
  - Reuse or extend existing BioMedPilot-native shared PySide components and `app/ui_style_tokens.py`.
  - Do not add third-party UI dependencies.
  - Do not change existing reagent calculation logic.
  - Do not default-write to `~/.labtools`.
  - Do not automatically save templates or records.
  - Do not automatically associate inventory or claim reagent availability.
  - Do not call real file export adapters, report builders, installers, downloads, uploads, engines, or cloud services.
  - Do not present calculated preparation output as a formal experiment record; keep user复核 semantics visible.
  - Do not touch App icon, Finder icon, `.icns`, `Info.plist`, LaunchServices, packaging, `dist/**`, or desktop app bundles in this remediation.
- Verification needed:
  - Focused UI tests for reagent component construction, result table rendering, and disabled save/export reasons where practical.
  - Source runtime smoke.
  - Runtime screenshot recapture for `labtools_reagent_preparation`.
  - Visual review against this issue list.
  - `git diff --check` and `git diff --cached --check` before commit.
- Status: reviewed; planning accepted pending implementation authorization

### 6. labtools_wb_loading

- Current issue observed: TBD
- Product-owner remediation opinion: TBD
- Severity: TBD
- Target behavior: TBD
- Affected component or page area: TBD
- Proposed stage: TBD
- Implementation boundary: TBD
- Verification needed: TBD
- Status: pending

### 7. labtools_experiment_boundaries

- Current issue observed: TBD
- Product-owner remediation opinion: TBD
- Severity: TBD
- Target behavior: TBD
- Affected component or page area: TBD
- Proposed stage: TBD
- Implementation boundary: TBD
- Verification needed: TBD
- Status: pending

### 8. bioinformatics_project_home

- Current issue observed: TBD
- Product-owner remediation opinion: TBD
- Severity: TBD
- Target behavior: TBD
- Affected component or page area: TBD
- Proposed stage: TBD
- Implementation boundary: TBD
- Verification needed: TBD
- Status: pending

### 9. bioinformatics_data_source

- Current issue observed: TBD
- Product-owner remediation opinion: TBD
- Severity: TBD
- Target behavior: TBD
- Affected component or page area: TBD
- Proposed stage: TBD
- Implementation boundary: TBD
- Verification needed: TBD
- Status: pending

### 10. bioinformatics_analysis_tasks

- Current issue observed: TBD
- Product-owner remediation opinion: TBD
- Severity: TBD
- Target behavior: TBD
- Affected component or page area: TBD
- Proposed stage: TBD
- Implementation boundary: TBD
- Verification needed: TBD
- Status: pending

### 11. bioinformatics_result_export

- Current issue observed: TBD
- Product-owner remediation opinion: TBD
- Severity: TBD
- Target behavior: TBD
- Affected component or page area: TBD
- Proposed stage: TBD
- Implementation boundary: TBD
- Verification needed: TBD
- Status: pending

### 12. meta_project_home

- Current issue observed: TBD
- Product-owner remediation opinion: TBD
- Severity: TBD
- Target behavior: TBD
- Affected component or page area: TBD
- Proposed stage: TBD
- Implementation boundary: TBD
- Verification needed: TBD
- Status: pending

### 13. meta_question_type

- Current issue observed: TBD
- Product-owner remediation opinion: TBD
- Severity: TBD
- Target behavior: TBD
- Affected component or page area: TBD
- Proposed stage: TBD
- Implementation boundary: TBD
- Verification needed: TBD
- Status: pending

### 14. meta_search_strategy

- Current issue observed: TBD
- Product-owner remediation opinion: TBD
- Severity: TBD
- Target behavior: TBD
- Affected component or page area: TBD
- Proposed stage: TBD
- Implementation boundary: TBD
- Verification needed: TBD
- Status: pending

### 15. meta_screening_extraction

- Current issue observed: TBD
- Product-owner remediation opinion: TBD
- Severity: TBD
- Target behavior: TBD
- Affected component or page area: TBD
- Proposed stage: TBD
- Implementation boundary: TBD
- Verification needed: TBD
- Status: pending

### 16. meta_result_export

- Current issue observed: TBD
- Product-owner remediation opinion: TBD
- Severity: TBD
- Target behavior: TBD
- Affected component or page area: TBD
- Proposed stage: TBD
- Implementation boundary: TBD
- Verification needed: TBD
- Status: pending

## Remediation Backlog

### Global P1 Backlog

1. Consolidate shared UI tokens
   - Problem: page-local colors, fonts, spacing, radii, and QSS drift create an inconsistent product surface.
   - Target: all main pages gradually use a common token layer for background, card, border, text, module color, semantic state, typography, spacing, radius, and common sizes.
   - Boundary: prefer evolving `app/ui_style_tokens.py` and existing shared UI component modules rather than creating a parallel token system.

2. Standardize the global shell
   - Problem: Sidebar, active navigation, brand block, top actions, and preview/version surfaces are not yet strong enough as global product chrome.
   - Target: AppShell with branded Sidebar, active route state, utility navigation, DeveloperPreviewCard, PageHeader, and TopActionArea.
   - Boundary: preserve current route behavior and do not introduce account logic.

3. Remove user-facing internal development terms
   - Problem: terms such as `Shell only`, `detect-first`, `Resolver-first`, and `UI-D2 boundary` make ordinary pages look like implementation diagnostics.
   - Target: move developer-only information to developer diagnostics, tooltips, or weak badges; replace main copy with user-facing Chinese-first descriptions.
   - Boundary: do not hide safety gates or imply unavailable capabilities are available.

4. Standardize shared components
   - Problem: repeated Qt default buttons, QGroupBox-like cards, table grids, and ad hoc status labels create a fragmented UI.
   - Target: shared BaseCard, StatusPill, button variants, ModuleEntryCard, RecentProjectsPanel, SettingsTabBar, SettingsRow, capability overview rows, system info card, and quick action cards.
   - Boundary: components stay service-free and must not call executors, reports, exports, installers, downloads, uploads, engines, or cloud services.

### Dashboard P1 Backlog

1. Establish Dashboard token discipline
   - Problem: colors, typography, spacing, radius, state colors, and dimensions still feel scattered.
   - Target: Dashboard page-level styles should come from existing shared tokens or a small extension to the shared token layer.
   - Boundary: prefer extending `app/ui_style_tokens.py` and existing shared components over creating a parallel token system.

2. Strengthen AppShell and Sidebar
   - Problem: sidebar reads like a plain text navigation list; brand, active state, utility navigation, and preview/version block are weak.
   - Target: fixed global sidebar with BrandBlock, Navigation, UtilityNavigation, and DeveloperPreviewCard.
   - Boundary: preserve current route behavior and active route semantics.

3. Replace Dashboard system-info header with product PageHeader
   - Problem: header currently behaves like a large system information card.
   - Target: lightweight header with title, subtitle, preview badge, and compact right-side actions/user area.
   - Boundary: user area may remain static; no account logic changes.

4. Rebuild module entry cards as primary Dashboard visual surface
   - Problem: cards still resemble QGroupBox/module debug blocks; icons are small, buttons are weak, module colors are unclear.
   - Target: three consistent ModuleEntryCards with large module visual, module-specific color, StatusPill, and full-width primary entry button.
   - Boundary: no module enablement changes; Bioinformatics and Meta gates remain unchanged.

5. Replace developer-facing module copy
   - Problem: copy such as `Resolver-first`, `Systematic review workflow shell`, and `Shell only` is too prominent.
   - Target: Chinese-first user-facing descriptions for Bioinformatics, Meta Analysis, and LabTools; engineering state only as weak badge or tooltip.
   - Boundary: do not hide safety gates where they are required; only reduce their visual dominance.

6. Standardize button hierarchy
   - Problem: buttons look like small default Qt buttons and differ by page area.
   - Target: primary module entry button, secondary lightweight button, and icon button styles with consistent hover/pressed/disabled states.
   - Boundary: disabled actions must still expose a reason where relevant.

7. Standardize status pills
   - Problem: status display is inconsistent across labels, text, and horizontal hints.
   - Target: shared compact status pill vocabulary for testing, available, optional, unavailable, planned, preview, shell-only, and local mode.
   - Boundary: status styling must not make testing/draft/shell-only states look like formal results.

8. Productize Recent Projects
   - Problem: recent projects area can look like a default database/debug table.
   - Target: RecentProjectsPanel with clear header, weak-grid rows, status pills, lightweight actions, and a proper empty state.
   - Boundary: do not introduce mock project data into runtime as real user data.

9. Add large module visuals
   - Problem: module icons are too small to support Dashboard recognition.
   - Target: Bioinformatics DNA visual, Meta document/statistics visual, LabTools flask/tube visual, all using module-specific colors.
   - Boundary: no emoji as formal icons; no new third-party asset dependency.

10. Recapture Dashboard screenshot after remediation
    - Problem: current D6 screenshot is not yet accepted for B10 visual readiness.
    - Target: recaptured `dashboard_home` should read as a polished BioMedPilot / Firefly workbench homepage.
    - Boundary: source-runtime screenshot only unless UI-B10 packaging is separately authorized.

### Settings P1 Backlog

1. Recompose Settings as a product settings center
   - Problem: current Settings surface reads as a field table and status note area.
   - Target: `PageHeader + SettingsTabBar + two-column content + QuickActionsPanel`.
   - Boundary: display/configuration entry only; no external install, download, update, engine, cloud, report, or export calls.

2. Productize SettingsTabBar
   - Problem: tabs look like plain buttons.
   - Target: horizontal rounded tab container with icons, active text/icon color, and subtle active underline or fill.
   - Boundary: preserve existing tab/view semantics.

3. Replace General Preferences field table with SettingsRows
   - Problem: fields such as path, language, chart style, export format, and cache cleanup look like raw configuration data.
   - Target: grouped setting rows for interface/language, data/storage, behavior/startup, and privacy/security.
   - Boundary: do not implement new settings persistence unless already supported.

4. Add External Capability Overview as a safe status surface
   - Problem: Settings lacks a right-side overview of local capabilities and their state.
   - Target: capability rows with ability name, StatusPill, explanation, and configuration action.
   - Boundary: configuration actions remain gated/disabled as appropriate and must not install or run engines.

5. Add SystemInfoCard
   - Problem: system/version/runtime information is either overexposed in the wrong place or not productized.
   - Target: compact system info card with app version, local mode, OS, memory, and disk usage; unavailable values should be clearly marked.
   - Boundary: no intrusive diagnostics or privacy-sensitive details in the ordinary first view.

6. Add QuickActionsPanel
   - Problem: common settings actions lack a productized entry surface.
   - Target: quick action cards for manage default paths, check updates, clear cache, and export logs.
   - Boundary: actions that are not implemented must remain planned/disabled with clear reason.

7. Move developer diagnostics out of ordinary Settings first view
   - Problem: `UI-D2 boundary` and similar internal wording appears in user-visible Settings.
   - Target: developer diagnostics tab, default collapsed.
   - Boundary: keep governance information available for internal review without letting it dominate the product UI.

8. Recapture Settings screenshot after remediation
   - Problem: current `settings_home` is not yet accepted for B10 visual readiness.
   - Target: recaptured Settings should read as a product settings center rather than a configuration/debug page.
   - Boundary: source-runtime screenshot only unless UI-B10 packaging is separately authorized.

### LabTools Calculator P1 Backlog

1. Recompose General Calculator as a calculation workbench
   - Problem: current page has three columns but still feels like a form prototype.
   - Target: `PageHeader + ModeSegmentedTabs + TaskPanel + Input/Formula column + ResultPanel + SafetyNoticeBar`.
   - Boundary: no calculation logic change and no save/export/history enablement.

2. Replace developer-facing calculator copy and states
   - Problem: backend, adapter, draft, and disabled export details dominate the user interface.
   - Target: user-facing copy such as `快速计算与动态公式求解，结果需用户复核。`, plus small local beta/status pills.
   - Boundary: preserve disabled reasons without showing implementation class names or backend contracts.

3. Productize CalculatorTaskPanel
   - Problem: a single combobox does not communicate a task library.
   - Target: searchable task list with task cards for dilution, unit conversion, plating aid, molarity/mass, percentage solution, serial dilution, and formula solving.
   - Boundary: task selection may continue to map to existing internal choices.

4. Productize calculator input and formula cards
   - Problem: input fields are visually flat and missing formula/unit hierarchy.
   - Target: QuickDilutionCard and FormulaSolverCard with clear variables, units, formula display, and action controls.
   - Boundary: if formula solving is not fully enabled, keep state as testing/needs review and avoid fake formal results.

5. Replace output textbox with result cards
   - Problem: current result preview looks like a draft output area.
   - Target: ResultPanel with result value cards, notes, copy action, and disabled save/export actions.
   - Boundary: calculation outputs must stay assistive and require user review.

6. Add bottom calculation safety notice
   - Problem: result review warning is not visible enough.
   - Target: NoticeBar explaining that the tool assists calculation and does not replace experiment design or judgment.
   - Boundary: source-runtime UI only; no report/export enablement.

7. Recapture General Calculator screenshot after remediation
   - Problem: current `labtools_general_calculator` is not yet accepted for B10 visual readiness.
   - Target: recaptured page should read as a usable LabTools calculation workbench.
   - Boundary: source-runtime screenshot only unless UI-B10 packaging is separately authorized.

### LabTools Reagent Preparation P1 Backlog

1. Recompose Reagent Preparation as a reagent workbench
   - Problem: page exposes storage and adapter internals instead of a template/preparation/review workflow.
   - Target: `PageHeader + TemplatePanel + PreparationPanel + TemplateEditorPanel + BottomActionBar + NoticeBars`.
   - Boundary: no calculation logic change, no auto-save, no inventory association, no export enablement.

2. Replace developer-facing reagent copy and states
   - Problem: backend, storage adapter, project context, file picker adapter, and demo template details dominate the page.
   - Target: user-facing states such as 本地测试版, 模板可编辑, 后端可用, 需存储适配, 需复核, 示例模板, 暂未开放.
   - Boundary: technical details may move to developer diagnostics or tooltip, but unavailable capabilities must remain clear.

3. Productize TemplatePanel
   - Problem: template list is sparse and mixed with local reagent management/debug content.
   - Target: searchable/filterable template card list with template name, category, default volume, pH, component count, update time, and status.
   - Boundary: local reagent library management should not occupy the main preparation flow.

4. Productize PreparationPanel
   - Problem: current input and output are mixed and rely on long text.
   - Target: structured preparation inputs plus a PreparationResultTable with component, type, amount, unit, and user review checkbox.
   - Boundary: user review checkboxes default unchecked; calculated values are not formal experiment records.

5. Productize TemplateEditorPanel
   - Problem: current right panel reads like template diagnostics.
   - Target: template information, component table, validation checklist, and disabled save template action with clear reason.
   - Boundary: no automatic template persistence or inventory linkage.

6. Consolidate bottom actions and notices
   - Problem: copy/save/export actions are scattered and developer-worded.
   - Target: BottomActionBar with copy summary, disabled save record, disabled export record, plus save-path and experiment-review NoticeBars.
   - Boundary: disabled actions must not look available.

7. Recapture Reagent Preparation screenshot after remediation
   - Problem: current `labtools_reagent_preparation` is not yet accepted for B10 visual readiness.
   - Target: recaptured page should read as a reagent preparation and review workbench.
   - Boundary: source-runtime screenshot only unless UI-B10 packaging is separately authorized.

## Implementation Plan

Dashboard, Settings, and LabTools reviewed-page implementation plan:

1. Audit current Dashboard, Settings, General Calculator, and Reagent Preparation implementations against existing D1 shared components and `app/ui_style_tokens.py`.
2. Extend shared tokens only where the current token set cannot express reviewed-page needs.
3. Refine or reuse shared Sidebar, PageHeader, TopActionArea, ModuleEntryCard, StatusChip/StatusPill, ActionButton, WorkbenchCard/BaseCard, EmptyState, table/list panel, SettingsTabBar, SettingsRow, capability overview, SystemInfoCard, QuickActionCard, segmented tabs, result cards, notice bars, bottom action bars, and dense workbench layout components.
4. Recompose Dashboard as `AppShell -> Sidebar + MainContent -> PageHeader + ModuleEntryGrid + RecentProjectsPanel`.
5. Recompose Settings as `AppShell -> Sidebar + MainContent -> PageHeader + SettingsTabBar + ContentGrid + QuickActionsPanel`.
6. Recompose General Calculator as `PageHeader + ModeSegmentedTabs + CalculatorTaskPanel + CalculatorInputColumn + ResultPanel + SafetyNoticeBar`.
7. Recompose Reagent Preparation as `PageHeader + TemplatePanel + PreparationPanel + TemplateEditorPanel + BottomActionBar + NoticeBars`.
8. Replace developer-facing copy with Chinese-first user copy while preserving safety/gate semantics.
9. Add focused component and page rendering tests where practical.
10. Run source smoke and focused tests.
11. Recapture `dashboard_home`, `settings_home`, `labtools_general_calculator`, and `labtools_reagent_preparation` and update the D6 remediation evidence.
