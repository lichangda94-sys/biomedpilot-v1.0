# Target UI Design Drafts Index

本目录归档自用户本地 UI 设计资料夹：

`/Users/changdali/Desktop/UI`

归档时间：2026-05-20

本目录仅保存目标 UI 草案原文和索引，不代表这些草案已经进入代码实现标准。正式开发前需要先以 `UI_A1_target_markdown_architecture_audit_20260520.md` 的冲突、缺口和映射结论为准。

## 文件索引

| 归档文件路径 | 原始文件路径 | 文件主题 | 所属范围 | 包含页面结构 | 包含按钮或交互 | 包含视觉规则 | 包含开发任务 | 存在待用户确认内容 |
|---|---|---|---|---|---|---|---|---|
| `docs/ui/target_design_drafts/UI_Architecture_Discussion_Confirmed_20260519.md` | `/Users/changdali/Desktop/UI/UI_Architecture_Discussion_Confirmed_20260519.md` | 已确认的全局 UI 架构方向、Dashboard 定位、模块入口、一级导航边界 | 全局 / 首页 / Dashboard / Bioinformatics / Meta Analysis / LabTools / Settings / 视觉 / i18n | 是 | 是 | 是 | 是 | 否；仍需进入审计后形成实施计划 |
| `docs/ui/target_design_drafts/UI_Architecture_Discussion_Supplement_20260519.md` | `/Users/changdali/Desktop/UI/UI_Architecture_Discussion_Supplement_20260519.md` | 全局入口、欢迎页、Dashboard、模块卡片、设置中心与开发者诊断的补充边界 | 全局 / 首页 / 登录页 / Dashboard / Settings / 视觉 / 其他 | 是 | 是 | 是 | 是 | 是；部分入口显示层级和后续版本范围需确认 |
| `docs/ui/target_design_drafts/UI_Architecture_Discussion_Supplement_2_20260519.md` | `/Users/changdali/Desktop/UI/UI_Architecture_Discussion_Supplement_2_20260519.md` | Bioinformatics 目标工作流前半段：项目首页、数据来源、数据检查、分组与分析设计、分析任务 | Bioinformatics / Dashboard / Settings / i18n | 是 | 是 | 是 | 是 | 是；正式分析按钮需与 B8.0.1/B8.1 后端状态再确认 |
| `docs/ui/target_design_drafts/UI_Architecture_Discussion_Supplement_3_20260519.md` | `/Users/changdali/Desktop/UI/UI_Architecture_Discussion_Supplement_3_20260519.md` | Bioinformatics 目标工作流后半段：结果与报告、报告导出、生信设置、项目日志、全局页面汇总 | Bioinformatics / 报告 / 导出 / Settings / i18n | 是 | 是 | 是 | 是 | 是；结果页与报告页需等待结果 schema 和报告资源策略确认 |
| `docs/ui/target_design_drafts/UI_Welcome_About_Page_Decisions_20260519.md` | `/Users/changdali/Desktop/UI/UI_Welcome_About_Page_Decisions_20260519.md` | Welcome / About 页面定位、Firefly/萤火虫品牌关系、Developer Preview 边界文案 | 全局 / 首页 / 登录页 / 视觉 / 品牌 / i18n | 是 | 是 | 是 | 是 | 是；品牌视觉、Logo、关于页最终文案仍需视觉阶段确认 |
| `docs/ui/target_design_drafts/Settings_External_Engines_Models_Resources_UI_20260520.md` | `/Users/changdali/Desktop/UI/Settings_External_Engines_Models_Resources_UI_20260520.md` | 设置中心中外部引擎、模型、分析资源与工具的目标架构和状态原则 | Settings / Bioinformatics / LabTools / Meta Analysis / 视觉 / 其他 | 是 | 是 | 是 | 是 | 是；资源清单、安装策略、平台差异和文案需后续细化 |
| `docs/ui/target_design_drafts/LabTools_UI_Architecture_Discussion_20260520.md` | `/Users/changdali/Desktop/UI/LabTools_UI_Architecture_Discussion_20260520.md` | LabTools 目标信息架构：通用计算器、试剂制备、实验模块、图像分析嵌入边界 | LabTools / Settings / 视觉 / 其他 | 是 | 是 | 是 | 是 | 是；各实验模块的低保真页面和功能状态需后续阶段确认 |
| `docs/ui/target_design_drafts/meta/Meta_Analysis_UI_Target_Architecture_Initial_20260520.md` | `/Users/changdali/Desktop/UI/meta/Meta_Analysis_UI_Target_Architecture_Initial_20260520.md` | Meta Analysis 目标架构初稿：Meta 类型前置、十类 Meta 类型、检索/筛选/提取/QA/统计/报告流程 | Meta Analysis / Settings / 报告 / 导出 / i18n | 是 | 是 | 是 | 是 | 是；当前运行态与目标流程差距、类型注册表和禁用功能需进一步验证 |

## 范围归类摘要

| 范围 | 主要来源文件 | 审计前判定 |
|---|---|---|
| 全局 / 首页 / 登录页 / Dashboard | `UI_Architecture_Discussion_Confirmed_20260519.md`, `UI_Architecture_Discussion_Supplement_20260519.md`, `UI_Welcome_About_Page_Decisions_20260519.md` | 已形成目标方向，但需要与当前 Login runtime、旧 Dashboard、品牌命名和 i18n 策略对齐 |
| LabTools | `LabTools_UI_Architecture_Discussion_20260520.md`, `Settings_External_Engines_Models_Resources_UI_20260520.md` | 目标层级清晰，但与旧 integration/ReleaseBuild 的 ImageJ/Fiji、planned pages、实验模块展示层级存在冲突 |
| Bioinformatics | `UI_Architecture_Discussion_Supplement_2_20260519.md`, `UI_Architecture_Discussion_Supplement_3_20260519.md`, `Settings_External_Engines_Models_Resources_UI_20260520.md` | 目标流程清晰，但不能绕过 B8.0.1 的 resolver-first / preflight-first / result-schema-first 限制 |
| Meta Analysis | `meta/Meta_Analysis_UI_Target_Architecture_Initial_20260520.md` | 有目标初稿，但需要与当前 UIShell shell-only 状态和 Meta 专属开发线真实 runtime 再核对 |
| Settings / 外部资源 | `Settings_External_Engines_Models_Resources_UI_20260520.md`, 其他全局与模块草案 | 目标原则较明确：detect-first、用户触发安装/更新/配置、技术入口不进入普通主流程 |
| 视觉 / 品牌 / 图标 | `UI_Welcome_About_Page_Decisions_20260519.md`, `UI_Architecture_Discussion_Confirmed_20260519.md`, `UI_Architecture_Discussion_Supplement_20260519.md` | 方向明确但缺少 Figma、组件规范、Logo/icon 冻结和多语言长度验证 |
| i18n / 多语言 | 全部草案均有中文 UI 文案风险 | 需要 UI-A3 单独审计；当前草案尚未形成可执行的 i18n key 与术语表 |
