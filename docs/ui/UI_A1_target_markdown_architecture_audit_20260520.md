# UI-A1 Target Markdown Architecture Audit

审计日期：2026-05-20

本阶段目标：读取 `/Users/changdali/Desktop/UI` 下全部 Markdown 目标设计草案，归档原文，提取目标 UI 架构，检查草案间冲突、缺口和重复内容，并与当前 `dev/ui-shell` 代码运行态、旧 UI 审计报告、Bioinformatics B8.0.1 审计报告和 LabTools/Meta 状态文档对照。

本阶段结论：这些 Markdown 已足够建立 `UI_Rebuild_MasterPlan` 和低保真 shell 开发边界，但不足以直接进入高保真 UI 制作或把 Bioinformatics / Meta Analysis / LabTools 的 planned 功能作为正式可运行按钮。下一步建议先进入 UI-A2 视觉系统、品牌与图标资源审计，再进入 UI-A3 i18n 审计，最后以 UI-A4 制定实施路线。

## 1. 审计范围

### 1.1 输入资料

本次读取本地 UI 设计资料夹：

`/Users/changdali/Desktop/UI`

读取到 Markdown 文件 8 个，共 7327 行：

| 文件 | 行数 | 归档路径 |
|---|---:|---|
| `/Users/changdali/Desktop/UI/LabTools_UI_Architecture_Discussion_20260520.md` | 1021 | `docs/ui/target_design_drafts/LabTools_UI_Architecture_Discussion_20260520.md` |
| `/Users/changdali/Desktop/UI/Settings_External_Engines_Models_Resources_UI_20260520.md` | 956 | `docs/ui/target_design_drafts/Settings_External_Engines_Models_Resources_UI_20260520.md` |
| `/Users/changdali/Desktop/UI/UI_Architecture_Discussion_Confirmed_20260519.md` | 637 | `docs/ui/target_design_drafts/UI_Architecture_Discussion_Confirmed_20260519.md` |
| `/Users/changdali/Desktop/UI/UI_Architecture_Discussion_Supplement_20260519.md` | 1032 | `docs/ui/target_design_drafts/UI_Architecture_Discussion_Supplement_20260519.md` |
| `/Users/changdali/Desktop/UI/UI_Architecture_Discussion_Supplement_2_20260519.md` | 1364 | `docs/ui/target_design_drafts/UI_Architecture_Discussion_Supplement_2_20260519.md` |
| `/Users/changdali/Desktop/UI/UI_Architecture_Discussion_Supplement_3_20260519.md` | 1201 | `docs/ui/target_design_drafts/UI_Architecture_Discussion_Supplement_3_20260519.md` |
| `/Users/changdali/Desktop/UI/UI_Welcome_About_Page_Decisions_20260519.md` | 519 | `docs/ui/target_design_drafts/UI_Welcome_About_Page_Decisions_20260519.md` |
| `/Users/changdali/Desktop/UI/meta/Meta_Analysis_UI_Target_Architecture_Initial_20260520.md` | 597 | `docs/ui/target_design_drafts/meta/Meta_Analysis_UI_Target_Architecture_Initial_20260520.md` |

### 1.2 项目内参考资料

本次对照读取以下项目内审计与代码资料：

| 类型 | 路径 | 用途 |
|---|---|---|
| 旧 UI 审计 | `docs/ui/UI_Cross_Branch_Runtime_IA_Audit_20260519.md` | 对照 LabTools 在 `dev/ui-shell`、`dev/integration`、`stable/mainline`、`ReleaseBuild` 的真实挂载差异 |
| 旧 UI 审计 | `docs/ui/UI_Current_Information_Architecture_Audit_20260519.md` | 对照当前全局 IA 与旧隐藏/降级建议 |
| UI 冻结基线 | `docs/ui/UI_Freeze_Consolidation_Baseline_20260519.md` | 对照当前可见入口、隐藏技术中心、Developer Preview 边界 |
| UI 宪法 | `docs/ui/BioMedPilot_UI_Design_Constitution_v2_20260519.md` | 对照状态标签、信息层级、视觉/文案边界 |
| Bioinformatics B8.0.1 审计 | `docs/bioinformatics/stage_B8_0_1_analysis_ui_prebuild_supplemental_audit_20260520.md` | 对照 Bioinformatics 分析按钮、result schema、resolver/preflight gating |
| 当前 shell 代码 | `app/shell/*.py` | 对照 Login、Dashboard、sidebar、Settings、测试模式 |
| 当前 Bioinformatics 代码 | `app/bioinformatics/*.py`, `app/bioinformatics/pages/*.py`, `app/bioinformatics/services/*.py` | 对照 13 页当前 workflow 与目标 7-8 页 |
| 当前 Meta 代码 | `app/meta_analysis/*.py` | 对照 UIShell 当前 Meta shell-only 状态 |
| 当前 UI 测试 | `tests/ui/*.py` | 对照现有测试覆盖面 |

### 1.3 阶段边界

本阶段只做文档归档和审计：

- 未修改业务代码。
- 未重构 UI。
- 未制作新页面。
- 未替换 Logo、图标、图片资源。
- 未删除旧资源。
- 未移动或覆盖桌面入口。
- 未重新打包。
- 未运行 packaged app。
- 未推进 Bioinformatics / Meta Analysis / LabTools 功能开发。

## 2. 读取的 Markdown 文件索引

草案已归档到：

`docs/ui/target_design_drafts/`

索引文件：

`docs/ui/target_design_drafts/README.md`

索引 README 已按任务要求记录每个文件的主题、所属范围、是否包含页面结构、按钮/交互、视觉规则、开发任务和待用户确认内容。

## 3. 新目标 UI 一级架构

### 3.1 目标启动与全局入口

目标启动结构：

```text
Welcome / 欢迎页
  -> Dashboard / 工作台首页
       -> Bioinformatics / 生信分析
       -> Meta Analysis / Meta 分析
       -> LabTools / 实验工具
       -> Settings / 设置中心
       -> 测试反馈 / About / 开发者诊断辅助入口
```

目标变化：

- 现有伪登录页应重建为轻量 Welcome Page。
- 第一屏不出现账号密码、注册、忘记密码、VIP、License 购买等流程。
- 目标品牌第一信号为 `萤火虫 / Firefly`，副标题为 `BioMedPilot / 医研智析`。
- `进入本地工作台` 是主按钮；`打开最近项目`、`设置`、`关于` 是辅助入口。
- Welcome/About 必须明确 Developer Preview / 本地测试版边界，输出不得表述为临床、诊断、正式统计或投稿级结论。

### 3.2 目标主侧边栏

目标普通用户侧边栏：

| 顺序 | 入口 | 状态 |
|---:|---|---|
| 1 | `Dashboard / 工作台` | 一级入口 |
| 2 | `Bioinformatics / 生信分析` | 一级模块 |
| 3 | `Meta Analysis / Meta 分析` | 一级模块 |
| 4 | `LabTools / 实验工具` | 一级模块 |
| 5 | `Settings / 设置中心` | 一级入口 |
| 辅助 | `测试反馈` | 底部/辅助入口 |
| 辅助 | `关于` | 底部/辅助入口 |

不应作为一级导航的入口：

- Project Center / Data Center / Task Center / Report Center。
- External Engines / Packaging / Environment / Developer Diagnostics。
- Account / Local AI / PDF OCR / ImageJ/Fiji。
- 单个 planned 分析功能或实验工具。

### 3.3 Dashboard 目标

Dashboard 是用户进入工作台后的模块入口页，不是营销页、项目中心、设置页或测试页。

目标内容：

- 三张并列模块卡片：Bioinformatics、Meta Analysis、LabTools。
- 每张卡片只展示模块目标、当前状态和 `进入`。
- 三个模块统一标注 `测试中` 或 Developer Preview 语义。
- 最近项目是轻量辅助区，不成为完整 Project Center。
- 本地环境和外部引擎状态可以作为底部折叠/提示，不进入主流程。

Dashboard 不应展示：

- 账号、订阅、License 购买。
- 项目中心、数据中心、任务中心、报告中心。
- packaging / manifest / cache / internal id。
- 图标资源状态明细。

### 3.4 Settings 目标

Settings 目标一级结构：

| Settings 子页 | 定位 |
|---|---|
| 常规设置 | 语言、主题、默认路径、基础偏好 |
| 账户与订阅 | 预留；当前不进入购买/VIP流程 |
| 本地项目与存储 | 默认项目路径、缓存、存储策略 |
| 外部引擎、模型与分析资源 | 图像引擎、OCR、本地模型、云端 AI、分析资源与工具 |
| 开发者诊断 | logs、环境详情、反馈包、内部诊断 |

外部资源原则：

- detect-first：可自动检测，不自动下载、安装、更新、删除、上传、启用。
- user-triggered：安装、下载、更新、删除、路径修改、启用、云端配置必须用户触发。
- 技术入口不进入普通用户主流程。
- 云端 AI 当前仅说明/预留，默认关闭，不展示 API key 购买或 provider 绑定流程。

## 4. 新目标 UI 二级页面结构

### 4.1 全局页面

| 页面名称 | 用户可见入口名称 | 所属模块 | 页面层级 | 页面目标 | 主要按钮 | 主要状态 | 复用/重建建议 |
|---|---|---|---|---|---|---|---|
| Welcome | 欢迎页 | 全局 | 启动页 | 进入本地工作台，说明 Developer Preview 边界 | 进入本地工作台、打开最近项目、设置、关于 | Developer Preview / 本地测试版 | 重建；当前 Login 只可参考布局能力 |
| Dashboard | 工作台 / Dashboard | 全局 | 一级 | 三模块入口和最近项目 | 进入生信分析、进入 Meta 分析、进入实验工具 | 测试中 | 重建；复用当前 module card 技术结构 |
| Sidebar | 主导航 | 全局 | 全局壳 | 提供稳定一级入口 | Dashboard、Bioinformatics、Meta、LabTools、Settings | 测试反馈/关于辅助 | 局部重建；当前 sidebar 缺 LabTools 和 About |
| About | 关于萤火虫 / About Firefly | 全局 | 辅助页 | 品牌说明、边界声明、社区邀请 | 返回、查看许可/版本信息 | Developer Preview | 新建；需要视觉和文案冻结 |
| Test Feedback | 测试反馈 | 全局 | 辅助页 | 反馈模板和诊断包 | 生成反馈模板、复制/导出 | Developer Preview | 可复用当前 testing page 后降噪 |

### 4.2 Bioinformatics 目标页面

目标主流程：

```text
Project Home
  -> Data Source
  -> Data Check & Preparation
  -> Group & Design
  -> Analysis Tasks
  -> Result & Report
  -> Report Export

Bioinformatics Settings / Project Logs & Technical Details 为辅助入口。
```

| 页面名称 | 用户可见入口名称 | 所属模块 | 页面层级 | 页面目标 | 主要按钮 | 主要状态 | 是否已有旧实现可复用 | 重建/隐藏/依赖 |
|---|---|---|---|---|---|---|---|---|
| Project Home | 生信项目首页 | Bioinformatics | 模块首页 | 新建/打开项目，显示项目进度 | 新建项目、打开项目、继续 | 无项目/已有项目/测试中 | 有 `BioinformaticsProjectHomeWidget` | 可复用骨架，需重写信息层级 |
| Data Source | 数据来源 | Bioinformatics | 主流程 | 本地导入、GEO、TCGA、GTEx、中文问题辅助 | 添加本地文件、登记公共数据库、继续检查 | 已记录/已下载/需补充 | 有 Data Source、Chinese Search、Acquisition Status | 合并重建；Acquisition Status 不独立展示 |
| Data Check & Preparation | 数据检查与准备 | Bioinformatics | 主流程 | 文件级识别、准备状态和缺失项 | 进入分组与分析设计、返回补充 | 可进入/需确认/需补充 | 有 Recognition、Readiness、Standardized Assets | 合并重建；技术详情折叠 |
| Group & Design | 分组与分析设计 | Bioinformatics | 主流程 | 管理原始分组字段和多个分析设计 | 保存分析设计并进入分析任务 | 可保存/需确认/字段冲突 | 有 Group Comparison Design | 复用服务，重写为非 DEG-only |
| Analysis Tasks | 分析任务 | Bioinformatics | 主流程 | 按输入准备度展示可做/不可做任务 | 查看准备状态、开始可用任务、返回设计 | 可开始/缺输入/后续开放 | 有 Analysis Task Center | 需重建按钮状态；B8.1 前不得正式化 DEG/GSEA/生存等 |
| Result & Report | 结果与报告 | Bioinformatics | 任务结果页 | 单次任务结果、表格/图形预览、加入报告草稿 | 保存、导出数据、导出图、加入报告草稿 | 无结果/结果草稿/待开发 | 有 Results Browser | 依赖 result schema；不能自动科学结论 |
| Report Export | 报告导出 | Bioinformatics | 报告页 | 汇总用户加入草稿的结果并导出 | 导出 Markdown、HTML 可选、DOCX/PDF 后续 | 草稿/可导出/后续开放 | 有 Report Viewer / builder | 复用 builder，先 Markdown |
| Bioinformatics Settings | 生信设置 | Bioinformatics | 辅助 | 模块内识别偏好、默认物种、Gene ID、报告偏好 | 保存设置、查看资源状态 | 模块设置 | 有 Settings and Local AI | 重建；全局 AI/外部引擎移到 Settings |
| Project Logs & Technical Details | 项目日志与技术详情 | Bioinformatics | 辅助 | 统一收纳 logs、manifest、调试详情 | 导出反馈包、查看日志 | 开发者诊断 | 分散存在 | 新建/合并；不得做主流程 |

### 4.3 LabTools 目标页面

目标一级结构：

```text
LabTools
  -> 通用计算器
  -> 试剂制备
  -> 实验模块
       -> 细胞实验
       -> 蛋白实验
       -> 核酸实验
       -> 免疫/吸光度实验
       -> IHC
```

| 页面名称 | 用户可见入口名称 | 所属模块 | 页面层级 | 页面目标 | 主要按钮 | 主要状态 | 是否已有旧实现可复用 | 重建/隐藏/依赖 |
|---|---|---|---|---|---|---|---|---|
| LabTools Home | 实验工具首页 | LabTools | 模块首页 | 展示三类入口和测试边界 | 进入通用计算器、试剂制备、实验模块 | 测试中 | `dev/integration`/ReleaseBuild 有类似入口 | `dev/ui-shell` 当前无代码；需最小 shell |
| General Calculator | 通用计算器 | LabTools | 二级 | 通用公式、单位换算、稀释、RPM/RCF 等 | 新建计算、保存到记录 | 可用/测试中 | integration 有 `general_calculators` 概念 | 需重建边界，排除实验专用计算 |
| Reagent Preparation | 试剂制备 | LabTools | 二级 | 模板、当前配制单、配制记录 | 选择模板、复制模板、生成配制单、保存记录 | 草稿/已保存 | integration 有 reagent records 概念 | 需重建为模板-配制-记录链 |
| Experiment Modules | 实验模块 | LabTools | 二级 | 按实验类型组织专用计算与记录 | 进入细胞/蛋白/核酸/免疫/IHC | planned/testing | integration 有部分页面 | 需分阶段；planned 不进主操作区 |
| Image Analysis Assist | 图像分析辅助 | LabTools | 模块内嵌 | 在 WB、划痕、Transwell、荧光/IHC 等内部调用 | 导入图像、记录测量、确认结果 | 辅助/需确认 | integration 有 `imagej_fiji` 技术页 | 不作为 LabTools 一级页；引擎配置进 Settings |
| Materials Record | 物料/库存记录 | LabTools | 横向记录 | 本地耗材、试剂、批次记录 | 记录批次、关联配制 | 本地记录 | 未在 UIShell | 不做一级导航；先作为模块内记录 |

关键边界：

- MTT / CCK-8 / AlamarBlue 属于细胞功能/活性实验，不属于 ELISA/吸光度模块。
- BCA 属于蛋白样本/蛋白定量，不属于通用计算器或 ELISA。
- SDS-PAGE 配胶属于 Western Blot 流程，不属于通用计算器。
- ImageJ/Fiji 只在 Settings 技术配置或实验模块内部辅助，不作为 LabTools 主任务页。

### 4.4 Meta Analysis 目标页面

目标主流程：

```text
Project Home
  -> Question & Meta Type
  -> Search Strategy
  -> Import & Deduplication
  -> Screening
  -> Full-text & Extraction
  -> Quality Assessment
  -> Meta Analysis Tasks
  -> Result & Report
  -> Report Export
  -> Meta Settings
```

目标 v1 类型：

| 类型 key | 用户语义 | 状态建议 |
|---|---|---|
| `binary_outcome_meta` | 二分类结局 Meta | testing schema |
| `continuous_outcome_meta` | 连续结局 Meta | testing schema |
| `survival_outcome_meta` | 生存结局 Meta | testing schema |
| `prevalence_incidence_meta` | 患病率/发病率 Meta | testing schema |
| `diagnostic_accuracy_meta` | 诊断准确性 Meta | testing schema |
| `exposure_disease_risk_meta` | 暴露-疾病风险 Meta | testing schema |
| `biomarker_expression_difference_meta` | 生物标志物表达差异 Meta | testing schema |
| `correlation_meta` | 相关性 Meta | testing schema |
| `prognostic_factor_meta` | 预后因素 Meta | testing schema |
| `dose_response_meta` | 剂量反应 Meta | testing schema only |

目标边界：

- Meta Type 是工作流控制项，不是普通标签。
- `NETWORK_META_ANALYSIS` 只能作为 planned，不可实现为正式入口。
- AI suggestion 只能作为建议，不得写成自动结论。
- 生产级在线数据库适配、Network Meta、HSROC 高级诊断、meta-regression、trim-and-fill、正式 PRISMA、生产 PDF、多审稿人协作、publication-grade 输出均不得作为已可用功能展示。

## 5. 首页 / 登录页 / Dashboard 审计

### 5.1 当前运行态

当前 `dev/ui-shell`：

- `app/shell/main_window.py` 先显示 `BioMedPilotLoginWidget`，登录后进入 shell。
- `app/shell/sidebar.py` 侧边栏为 `Dashboard`、`生信分析`、`Meta 分析`、`设置中心`、`测试入口`。
- `app/shell/module_selection.py` Dashboard 只有 Bioinformatics 和 Meta 两张模块卡片。
- Dashboard header 仍展示 `BioMedPilot / 医研智析`、当前用户、账号等级、License 状态等信息。
- Settings 是占位页，并展示图标资源状态明细。
- LabTools 在当前 `dev/ui-shell` 不存在。

### 5.2 目标差距

| 当前项 | 目标项 | 差距 | 建议 |
|---|---|---|---|
| Login / 本地测试用户 | Welcome / 欢迎页 | 当前有登录语义、账号等级、License 状态 | 重建为无账号流程 Welcome |
| Dashboard 两模块 | Dashboard 三模块 | 缺 LabTools；Bio/Meta 描述含正式能力过多 | 增加 LabTools shell，统一测试中状态 |
| Sidebar 无 About | Sidebar 底部 About/测试反馈 | 关于页缺失 | 新增辅助入口 |
| Settings 占位 + 图标明细 | Settings 分层结构 | 技术信息暴露给普通用户 | 重建 Settings IA，图标状态进开发者诊断 |
| Brand 第一信号 BioMedPilot | Brand 第一信号萤火虫/Firefly | 品牌关系未冻结 | UI-A2 先做品牌和 Logo 审计 |

### 5.3 审计结论

首页/登录页/Dashboard 不适合局部修补。应先形成 `UI_Rebuild_MasterPlan`，再以 Welcome、Dashboard、Sidebar、About、Settings shell 作为 UI 重建首批页面。

## 6. LabTools 目标架构审计

### 6.1 新目标结构

LabTools 目标是一级科研模块，与 Bioinformatics、Meta Analysis 并列。模块内部只保留三类顶层入口：

1. 通用计算器。
2. 试剂制备。
3. 实验模块。

图像分析、物料记录、外部引擎、协作、LIMS 等均不应作为 LabTools 顶层入口。

### 6.2 与旧运行态差异

旧跨分支审计显示：

- `dev/ui-shell` 无 LabTools 入口、无 `app.labtools`。
- `dev/integration` / `ReleaseBuild` 曾有完整 LabTools 工作台，页面包括 `home`、`general_calculators`、`imagej_fiji`、`reagent_records`、`cell_experiments`、`western_blot`、`pcr_qpcr`、`elisa_absorbance`。
- `stable/mainline` 只承接过最小 `image_analysis` / ImageJ-Fiji 边界页。

目标草案要求：

- `imagej_fiji` 不再作为 LabTools 主任务页。
- `reagent_records` 应扩展为试剂制备链，而不是孤立记录页。
- planned 实验模块不得与 current/testing 页面同级显示。
- 通用计算器必须排除实验专用计算。

### 6.3 LabTools 风险

| 风险 | 严重程度 | 建议 |
|---|---|---|
| 把 ImageJ/Fiji 作为 LabTools 主任务页 | 高 | 移入 Settings 外部引擎，实验模块内只保留图像分析辅助 |
| 把 BCA、SDS-PAGE、MTT/CCK-8 混入通用计算器 | 高 | 按实验上下文归位 |
| 把 planned PCR/qPCR、ELISA、细胞实验作为可用主流程 | 中 | 先隐藏或标注 planned，待闭环后开放 |
| 把物料/库存做成一级入口 | 中 | 先作为模块内横向记录 |

## 7. Bioinformatics 目标架构审计

### 7.1 新目标结构

Bioinformatics 目标是把当前历史 13 页收敛为 7 个主流程页 + 2 个辅助页：

- Project Home。
- Data Source。
- Data Check & Preparation。
- Group & Design。
- Analysis Tasks。
- Result & Report。
- Report Export。
- Bioinformatics Settings。
- Project Logs & Technical Details。

### 7.2 与当前代码差异

当前 `app/bioinformatics/workspace.py` 真实挂载页面包括：

- Project Home。
- Data Source。
- Chinese Dataset Search。
- Acquisition Status。
- Recognition。
- Readiness Dashboard。
- Standardized Assets。
- Group Comparison Design。
- Workflow Status。
- Analysis Task Center。
- Results Browser。
- Report Viewer。
- Settings and Local AI。

目标不是新增更多页面，而是合并、折叠、降级现有技术页：

- Data Source 合并 Chinese Search 和 Acquisition Status。
- Data Check & Preparation 合并 Recognition、Readiness、Standardized Assets。
- Group & Design 不再是 DEG-only。
- Analysis Tasks 不得把 planned/preflight/dry-run 写成正式产品能力。
- Result & Report 是单次任务结果页，不是全局历史结果中心。
- Settings and Local AI 拆分：模块偏好留在 Bioinformatics Settings，外部模型/AI/资源移到全局 Settings。

### 7.3 B8.0.1 冲突门槛

B8.0.1 审计结论明确：UIShell 当前适合分析 UI 重建规划，但不适合将 DEG、GSEA、survival、clinical association、plot generation、report-ready export 作为主要正式可运行动作暴露。

因此 Bioinformatics UI 开发必须遵守：

- resolver-first。
- preflight-first。
- result-schema-first。
- standardized repository / analysis input package 先行。
- Developer Preview 功能不能写成正式产品能力。
- TCGA+GTEx 自动合并不能作为默认分析路径。

## 8. Meta Analysis 目标架构审计

### 8.1 新目标结构

Meta Analysis 草案提出“共用流程 + Meta 类型前置 + 类型特异 extraction / QA / statistics / report templates”。这是正确方向，避免把所有 Meta 类型塞入完全泛化流程。

### 8.2 当前 UIShell 状态

当前 `app/meta_analysis/workspace.py` 只是 mainline shell：

- 页面 key 为 `workflow_home`、`project_contract`、`dev_branch`。
- 页面文案明确完整功能在 `dev/meta-analysis`。
- 当前 UIShell 不应被描述为完整 Meta runtime。

### 8.3 风险

| 风险 | 严重程度 | 建议 |
|---|---|---|
| 把当前 testing / Developer Preview 写成生产级系统综述能力 | 高 | 所有 Meta 主流程先标 testing/schema/shell |
| 旧流程与新类型前置流程并列 | 高 | 以目标类型前置流程为唯一新 IA，旧流程进入映射/迁移表 |
| 中文数据库直接检索或中文 PDF 抽取能力混入目标 | 中 | 未明确后端前不展示为正式入口 |
| AI suggestion 写成自动结论 | 高 | 只能展示为建议，不自动形成结论 |
| Network Meta 出现在正式入口 | 高 | 只能 planned/隐藏 |

## 9. Settings 目标架构审计

### 9.1 目标结构

Settings 需要从当前占位页升级为二级导航结构：

- 常规设置。
- 账户与订阅。
- 本地项目与存储。
- 外部引擎、模型与分析资源。
- 开发者诊断。

### 9.2 外部引擎、模型与分析资源

目标分区：

| 分区 | 包含内容 | UI 原则 |
|---|---|---|
| 图像分析引擎 | ImageJ/Fiji、未来图像分析工具 | detect-first；配置在 Settings；实验模块调用 |
| PDF 识别与 OCR 引擎 | PDF/OCR 相关依赖 | 默认不进入普通主流程 |
| 本地语言模型 | Ollama/local model 等 | 默认关闭，用户配置 |
| 云端 AI 服务 | 未来云端 provider | 当前说明/预留，不展示购买/API key |
| 分析资源与工具 | R/Python 包、GO/KEGG、本地缓存、统计/绘图依赖 | 检测、说明、用户触发安装/更新 |

### 9.3 与当前代码差异

当前 Settings：

- 是单页占位。
- 将默认项目路径、语言、Python/R、本地 AI、数据库、图表样式、导出格式、缓存清理平铺。
- 展示图标资源状态明细。

目标要求：

- 普通用户只看到可理解设置项。
- 外部资源进入统一状态模型。
- 图标资源、内部诊断、manifest/cache/logs 进入开发者诊断。
- 具体模块只引用全局资源状态，不重复创建设置入口。

## 10. Markdown 冲突表

| file_a | file_b | conflict_topic | conflict_detail | severity | suggested_resolution |
|---|---|---|---|---|---|
| `UI_Architecture_Discussion_Confirmed_20260519.md` | `Settings_External_Engines_Models_Resources_UI_20260520.md` | Settings 命名范围 | 早期文件使用“外部引擎与模型”，后续文件扩展为“外部引擎、模型与分析资源”。 | Medium | 以后者为准；Settings 资源页必须覆盖分析资源与工具。 |
| `UI_Architecture_Discussion_Supplement_20260519.md` | `UI_Welcome_About_Page_Decisions_20260519.md` | Welcome / Dashboard 品牌层级 | 全局补充仍以 BioMedPilot 为主，Welcome/About 明确以萤火虫/Firefly 为第一品牌。 | Medium | UI-A2 先冻结品牌关系；目标建议“萤火虫 / Firefly”为主，`BioMedPilot / 医研智析` 为副标题。 |
| `UI_Architecture_Discussion_Supplement_2_20260519.md` | `docs/bioinformatics/stage_B8_0_1_analysis_ui_prebuild_supplemental_audit_20260520.md` | Bioinformatics 正式分析按钮 | 草案在 Analysis Tasks 中允许 DEG 等在输入满足时开始分析；B8.0.1 要求 resolver/preflight/result schema 先完成。 | High | UI 可做任务壳和 readiness 状态，但正式 DEG/GSEA/survival/report 按钮必须 gated 或降级为 Developer Preview/preflight。 |
| `UI_Architecture_Discussion_Supplement_3_20260519.md` | `docs/bioinformatics/stage_B8_0_1_analysis_ui_prebuild_supplemental_audit_20260520.md` | Result & Report 正式化 | 草案描述结果页、图表、报告草稿；B8.0.1 认为 result schema/report-ready export 未完成。 | High | 先实现空状态、schema placeholder、Markdown 草稿边界；不得自动形成科学结论。 |
| `UI_Architecture_Discussion_Supplement_2_20260519.md` | `Settings_External_Engines_Models_Resources_UI_20260520.md` | GO/KEGG 下载策略 | Bioinformatics 草案提到 GO/KEGG 可联网下载/缓存，Settings 草案要求 detect-first/user-triggered。 | Medium | 所有资源下载必须用户确认，状态进入全局资源注册表。 |
| `LabTools_UI_Architecture_Discussion_20260520.md` | `docs/ui/UI_Cross_Branch_Runtime_IA_Audit_20260519.md` | ImageJ/Fiji 层级 | 旧 integration/ReleaseBuild 有 `imagej_fiji` LabTools page_key；新草案要求图像引擎配置进入 Settings，图像分析仅模块内嵌。 | High | 旧 `imagej_fiji` 不可原样作为目标主任务页；迁移为 Settings 技术配置或模块内辅助。 |
| `LabTools_UI_Architecture_Discussion_20260520.md` | `docs/ui/UI_Cross_Branch_Runtime_IA_Audit_20260519.md` | planned LabTools 页面 | 旧 runtime 中 PCR/qPCR、ELISA、细胞实验等 planned/testing 页面同级；新草案强调只保留三类顶层入口。 | Medium | LabTools 主区只展示 Calculator/Reagent/Experiment Modules；planned 子模块隐藏或标后续开放。 |
| `LabTools_UI_Architecture_Discussion_20260520.md` | `UI_Architecture_Discussion_Confirmed_20260519.md` | Dashboard 模块卡能力描述 | 全局草案希望模块卡显示目标能力；LabTools 草案把很多能力限定为模块内部或后续版本。 | Medium | Dashboard card 只写模块定位和测试状态，不列未完成细分功能。 |
| `meta/Meta_Analysis_UI_Target_Architecture_Initial_20260520.md` | `app/meta_analysis/workspace.py` current runtime | Meta 目标流程 vs 当前 shell | 草案给出完整 10 页流程；当前 UIShell 只有 mainline shell 3 个 page_key。 | High | 目标流程可进入 MasterPlan；当前 UI 不可宣称完整流程已接入。 |
| `meta/Meta_Analysis_UI_Target_Architecture_Initial_20260520.md` | `docs/ui/UI_Freeze_Consolidation_Baseline_20260519.md` | Meta production 能力 | 草案涉及多类型 Meta 目标，冻结基线要求真实 workflow 前不得高保真包装 planned 能力。 | High | 所有 Meta 类型先标 testing schema / planned；禁用 production-grade 文案。 |
| `UI_Architecture_Discussion_Supplement_20260519.md` | `app/shell/main_window.py` current runtime | Project/Data/Task/Report Center | 草案要求这些中心不要作为一级入口；当前代码中有 ProjectCenter 服务和最近项目，但无主导航中心。 | Low | 保持隐藏；最近项目留 Dashboard，完整中心暂不显示。 |
| `Settings_External_Engines_Models_Resources_UI_20260520.md` | `app/shell/main_window.py` current runtime | 图标资源状态 | 当前 Settings 展示图标资源明细；目标 Settings 只保留用户设置，技术信息进开发者诊断。 | Medium | 迁移到开发者诊断；普通 Settings 不显示 icon slot 明细。 |

## 11. 当前代码与目标页面映射表

| target_area | target_page | source_markdown | current_code_status | current_runtime_status | test_coverage | reuse_strategy | rebuild_priority | blocker | next_stage |
|---|---|---|---|---|---|---|---|---|---|
| Global | Welcome | `UI_Welcome_About_Page_Decisions_20260519.md` | 有 `BioMedPilotLoginWidget`，不是 Welcome | 当前先登录再进入 shell | `tests/ui/test_login_page.py` | 只复用启动页技术骨架 | P0 | 品牌/视觉冻结 | UI-A2 后实施 |
| Global | Dashboard | `UI_Architecture_Discussion_Confirmed_20260519.md` | 有 `ModuleSelectionWidget` | 只显示 Bioinformatics + Meta | `tests/ui/test_module_selection.py` | 复用卡片与最近项目结构 | P0 | LabTools shell 未接入；品牌视觉未冻结 | UI_Rebuild_MasterPlan |
| Global | Sidebar | `UI_Architecture_Discussion_Supplement_20260519.md` | 有 `SidebarWidget` | 无 LabTools/About，含测试模式 | `tests/ui/test_sidebar.py` | 复用布局，改入口模型 | P0 | LabTools 页面需最小 shell | UI_Rebuild_MasterPlan |
| Global | About | `UI_Welcome_About_Page_Decisions_20260519.md` | 无独立 About | 不可见 | 无 | 新建 | P1 | 文案和视觉系统 | UI-A2 |
| Global | Test Feedback | `UI_Architecture_Discussion_Supplement_20260519.md` | 有 testing page | 可见测试模式 | 部分 sidebar/window 测试 | 降噪后复用 | P2 | 开发者诊断层级 | UI-A4 |
| Settings | Settings Home | `Settings_External_Engines_Models_Resources_UI_20260520.md` | 单页占位 | 可见，内容平铺 | 间接覆盖 | 重建为左二级 nav + 内容页 | P0 | 视觉组件和状态标签 | UI-A2/UI-A4 |
| Settings | External Engines, Models & Analysis Resources | `Settings_External_Engines_Models_Resources_UI_20260520.md` | 部分环境/GEO/AI 文案分散 | 不成体系 | B8.0.1 文档覆盖，UI 测试不足 | 新建统一 registry UI | P0 | 资源清单和 detect API | UI-A4 |
| Settings | Developer Diagnostics | `Settings_External_Engines_Models_Resources_UI_20260520.md` | 图标状态、testing、logs 分散 | 部分可见 | `tests/ui/test_feature_availability.py` | 合并技术细节 | P1 | 诊断范围定义 | UI-A4 |
| Bioinformatics | Project Home | `UI_Architecture_Discussion_Supplement_2_20260519.md` | 有 `BioinformaticsProjectHomeWidget` | 可见 | `tests/ui/test_bioinformatics_project_home.py` | 复用项目绑定能力 | P0 | 新 IA 文案 | UI-A4 |
| Bioinformatics | Data Source | `UI_Architecture_Discussion_Supplement_2_20260519.md` | 有 Data Source + Chinese Search + Acquisition Status | 可见/分散 | `tests/ui/test_bioinformatics_workflow_pages.py` | 合并为一页 | P0 | 数据来源状态模型 | UI-A4 |
| Bioinformatics | Data Check & Preparation | `UI_Architecture_Discussion_Supplement_2_20260519.md` | Recognition/Readiness/Standardized Assets 分散 | 可见 | `tests/ui/test_bioinformatics_workflow_pages.py` | 服务可复用，UI 合并 | P0 | 文件级识别表和缺失项文案 | UI-A4 |
| Bioinformatics | Group & Design | `UI_Architecture_Discussion_Supplement_2_20260519.md` | 有 Group Comparison Design | 可见 | UI workflow tests | 复用设计服务，去 DEG-only | P0 | 多比较设计边界 | UI-A4 |
| Bioinformatics | Analysis Tasks | `UI_Architecture_Discussion_Supplement_2_20260519.md` | 有 Analysis Task Center | 可见 | UI workflow tests | 复用 readiness/preflight 服务 | P0 | B8.1 resolver/result schema | B8.1 + UI-A4 |
| Bioinformatics | Result & Report | `UI_Architecture_Discussion_Supplement_3_20260519.md` | 有 Results Browser | 可见 | UI workflow tests | 先保留结果浏览壳 | P1 | 结果 schema、图表导出 | B8.1 |
| Bioinformatics | Report Export | `UI_Architecture_Discussion_Supplement_3_20260519.md` | 有 Report Viewer / builder | 可见 | UI workflow tests | 先 Markdown draft | P1 | 报告模板/i18n | UI-A3/B8.1 |
| Bioinformatics | Bioinformatics Settings | `UI_Architecture_Discussion_Supplement_3_20260519.md` | 有 Settings and Local AI | 可见 | UI workflow tests | 拆分模块设置与全局资源 | P1 | Settings registry | UI-A4 |
| Bioinformatics | Project Logs & Technical Details | `UI_Architecture_Discussion_Supplement_3_20260519.md` | 技术细节分散 | 部分可见 | 不完整 | 新建辅助页 | P2 | feedback package 格式 | UI-A4 |
| LabTools | LabTools Home | `LabTools_UI_Architecture_Discussion_20260520.md` | `dev/ui-shell` 无 `app.labtools` | 不可见 | 当前分支无 LabTools UI 测试 | 可参考 integration/ReleaseBuild shell | P0 | 合入范围和最小 shell | UI-A4 |
| LabTools | General Calculator | `LabTools_UI_Architecture_Discussion_20260520.md` | 当前分支无 | 不可见 | 无 | 复用旧概念，不复用旧层级 | P1 | 通用/实验专用计算边界 | UI-A4 |
| LabTools | Reagent Preparation | `LabTools_UI_Architecture_Discussion_20260520.md` | 当前分支无 | 不可见 | 无 | 旧 reagent records 只能参考 | P1 | 模板/配制/记录数据模型 | UI-A4 |
| LabTools | Experiment Modules | `LabTools_UI_Architecture_Discussion_20260520.md` | 当前分支无 | 不可见 | 无 | 分阶段重建 | P1 | 各实验闭环和状态标注 | UI-A4 |
| LabTools | Image Engine Config | `Settings_External_Engines_Models_Resources_UI_20260520.md` | 当前分支无 LabTools；旧分支有 `imagej_fiji` | 当前不可见 | 无 | 移到 Settings，模块内只调用 | P1 | Settings detect-first registry | UI-A4 |
| Meta Analysis | Project Home | `meta/Meta_Analysis_UI_Target_Architecture_Initial_20260520.md` | 有 shell `workflow_home` | 可见但 shell-only | sidebar/module tests | 复用项目 contract 壳 | P0 | Meta 专线 runtime 状态 | UI-A4 |
| Meta Analysis | Question & Meta Type | `meta/Meta_Analysis_UI_Target_Architecture_Initial_20260520.md` | 当前 UIShell 无 | 不可见 | 无 | 新建，类型注册表先行 | P0 | type registry / templates | UI-A4 |
| Meta Analysis | Search/Import/Screening/Extraction/QA | `meta/Meta_Analysis_UI_Target_Architecture_Initial_20260520.md` | 当前 UIShell 无完整流程 | 不可见 | 无 | 需从 Meta 专线验证后迁移 | P1 | 当前真实 runtime 审计 | Meta 专线审计 |
| Meta Analysis | Meta Analysis Tasks | `meta/Meta_Analysis_UI_Target_Architecture_Initial_20260520.md` | 当前 UIShell 无 | 不可见 | 无 | 新建 testing/schema shell | P1 | 统计后端和类型模板 | UI-A4 |
| Meta Analysis | Result & Report / Export | `meta/Meta_Analysis_UI_Target_Architecture_Initial_20260520.md` | 当前 UIShell 无 | 不可见 | 无 | 新建，先草稿/preview | P2 | report schema / export assets | UI-A3/UI-A4 |

## 12. 视觉 / 图标 / 资源缺口

### 12.1 视觉缺口

| 缺口 | 影响 | 建议 |
|---|---|---|
| 未冻结主品牌视觉 | Welcome、About、Dashboard 无法高保真 | UI-A2 先确认萤火虫/Firefly 与 BioMedPilot/医研智析关系 |
| 未定义完整色彩系统 | 模块卡、状态标签、Settings 状态可能不一致 | 建立颜色 token 和状态 token |
| 未定义字体和字号层级 | 中文/英文混排、按钮长度风险 | UI-A2/UI-A3 联合处理 |
| 未定义布局规范 | Dashboard、Settings、模块工作流页面可能重复设计 | 建立 shell/grid/card/table/form/modal 规则 |
| 未定义卡片/按钮/表格/状态标签组件 | 分析任务和资源状态页会出现多套样式 | 先做组件清单和状态字典 |
| 缺少空状态插图与报告图标 | 项目首页、结果页、报告页体验不完整 | UI-A2 建立资源清单 |

### 12.2 图标与资源缺口

| 资源 | 当前状态 | 建议 |
|---|---|---|
| App icon | 有当前 firefly icon，但目标品牌未冻结 | UI-A2 验证是否继续使用 |
| 模块图标 | 当前 Bio/Meta 有资源，LabTools 缺当前分支接入 | 建立三模块一致图标规范 |
| 状态图标 | 未形成统一状态图标体系 | 与 Settings 状态字典一起定义 |
| 空状态插图 | 未定义 | Welcome/About/Dashboard/结果页统一风格 |
| 登录页/Welcome 主视觉 | 未定义 | UI-A2 设计，不能先用旧登录图 |
| 报告/导出图标 | 未定义 | 与 Report Export 资源一起规划 |

## 13. i18n / 多语言缺口

| 缺口 | 风险 | 建议 |
|---|---|---|
| 中文硬编码 | 当前 shell、Bioinformatics、Settings 文案大量中文硬编码 | UI-A3 建立 i18n key 策略 |
| 英文按钮变长 | Settings、Analysis Tasks、Report Export 按钮可能溢出 | UI-A3 做英文长度压力测试 |
| 医学术语翻译边界 | Meta 类型、Bioinformatics 分析名、LabTools 实验名容易不一致 | 建立中英术语表 |
| 报告模板多语言 | Markdown/HTML/DOCX/PDF 输出文案影响报告可信度 | 报告模板先支持语言参数 |
| Settings 语言切换入口 | 当前有语言占位，但未定义生效范围 | Settings 常规设置中预留并约束范围 |
| Developer Preview 文案 | 中英文边界声明不统一会导致能力误读 | 统一 disclaimer i18n key |

## 14. 功能依赖与按钮状态风险

| 功能/按钮 | 当前风险 | UI 状态建议 |
|---|---|---|
| DEG 正式分析 | B8.0.1 未允许正式 exposure | 仅 preflight / Developer Preview / gated |
| GSEA / enrichment | 依赖资源注册、输入包和结果 schema | planned 或 gated |
| survival / clinical | 后端、输入、统计策略未闭环 | planned 或 hidden |
| TCGA+GTEx 自动合并 | 草案目标与 B8.0.1 风险冲突 | 不作为默认路径 |
| Bioinformatics report-ready export | 报告模板和 result schema 未完成 | Markdown 草稿优先，DOCX/PDF 后续 |
| LabTools planned modules | 旧页面可能让用户误认为可用 | 隐藏或标后续开放 |
| ImageJ/Fiji | 技术依赖抢占普通流程 | Settings 配置，不进入模块首页 |
| Cloud AI | 账号/API/隐私边界未定 | 默认关闭，仅说明 |
| Meta production workflow | 当前 UIShell shell-only | testing/schema shell，不展示生产级能力 |
| AI suggestion | 容易被误读为自动结论 | 只作建议，不自动写结论 |

## 15. 可复用页面、需重建页面、需隐藏页面

### 15.1 可复用页面或能力

| 范围 | 可复用项 | 复用方式 |
|---|---|---|
| Global shell | `MainWindow` stack、sidebar 基础布局、module card 技术结构 | 作为重建骨架，不保留旧 IA |
| Dashboard | 最近项目服务、卡片点击机制、模块图标加载机制 | 文案和模块数重建 |
| Bioinformatics | 项目首页、数据来源、识别、readiness、standardized assets、group design、task center、results/report builder 的服务层 | 合并 UI 层，保留可验证服务 |
| Settings | 环境检测、路径/语言占位、本地资源检查概念 | 纳入新 Settings 二级结构 |
| LabTools | integration/ReleaseBuild 的 LabTools shell 概念和 dev/labtools 后端能力 | 只作迁移参考；不能原样合入主流程 |
| Meta Analysis | 当前 project contract shell | 作为项目绑定壳；完整流程需专线验证 |

### 15.2 必须重建页面

| 页面 | 原因 |
|---|---|
| Login -> Welcome | 目标去账号化，品牌和边界不同 |
| Dashboard | 从两模块变三模块，并去除账号/License/技术明细 |
| Settings | 单页占位无法承载外部资源与开发者诊断 |
| Bioinformatics 13 页流程 | 目标要求收敛为 7-8 页，技术页折叠 |
| LabTools IA | 当前分支无代码，旧 integration 层级与目标冲突 |
| Meta full workflow | 当前 UIShell 只有 shell，目标是类型前置流程 |
| About | 当前缺失，且需要品牌文案/视觉 |

### 15.3 必须隐藏或降级页面/入口

| 入口/页面 | 处理 |
|---|---|
| Project Center / Data Center / Task Center / Report Center 顶层入口 | 暂不显示 |
| Environment / Packaging | 移入开发者诊断或隐藏 |
| Acquisition Status 独立页 | 合并进 Data Source |
| Recognition / Readiness / Standardized Assets 独立技术页 | 合并进 Data Check & Preparation，技术细节折叠 |
| Workflow Status | 降级为日志/技术详情 |
| Settings 图标资源明细 | 移入开发者诊断 |
| ImageJ/Fiji LabTools 主任务页 | 移入 Settings 技术配置 |
| LabTools planned PCR/qPCR、ELISA、细胞实验等 | 隐藏或后续开放，不做主操作区 |
| Bioinformatics DEG/GSEA/survival/report-ready buttons | B8.1 前 gated/developer preview |
| Meta Network Meta / production PDF / multi-reviewer / formal PRISMA | planned/hidden |

## 16. 后续 UI-A2 / UI-A3 / UI-A4 建议

### 16.1 是否足够开始 UI 开发

不建议直接开始高保真 UI 开发。当前 Markdown 足够开始：

- `UI_Rebuild_MasterPlan`。
- 低保真 shell 规划。
- 页面合并/隐藏/降级清单。
- 状态标签和功能 gating 策略。

不足以直接开始：

- 高保真 Welcome/About/Dashboard。
- 正式图标/插图替换。
- Bioinformatics 正式分析按钮。
- Meta 生产流程。
- LabTools 完整实验模块。

### 16.2 缺少的设计输入

- Figma 或同等视觉系统。
- 品牌关系冻结：萤火虫 / Firefly / BioMedPilot / 医研智析。
- Logo、App icon、模块图标、状态图标、空状态插图清单。
- 颜色、字体、间距、卡片、按钮、表格、状态标签组件规范。
- i18n key、术语表、长文本适配规则。
- Bioinformatics B8.1 resolver/preflight/result schema。
- Meta 专线当前 runtime 审计。
- LabTools 最小接入范围和实验模块优先级。

### 16.3 可先做 shell 的页面

- Welcome shell。
- About shell。
- Dashboard 三模块 shell。
- Sidebar 新入口模型。
- Settings 二级导航 shell。
- Bioinformatics 7 页目标 shell，但分析按钮 gated。
- LabTools Home / Calculator / Reagent / Experiment Modules shell。
- Meta Project Home / Question & Meta Type shell。

### 16.4 必须等视觉系统后再做的页面

- Welcome 高保真页。
- About 高保真页。
- Dashboard 高保真模块卡。
- 三模块图标体系。
- 结果/报告/导出图标和空状态。
- Settings 状态标签和资源卡。

### 16.5 建议阶段顺序

1. `UI_Rebuild_MasterPlan`：基于本报告确定页面树、隐藏/降级清单、迁移顺序。
2. `UI-A2`：视觉系统、品牌与图标资源审计。
3. `UI-A3`：i18n、多语言、医学/实验术语表审计。
4. `UI-A4`：实施路线审计，拆分可开发 shell、依赖后端的 gated 页面和后续版本功能。

建议下一步进入 UI-A2。

## 17. 本阶段未修改业务代码声明

本阶段只新增/复制 Markdown 文档：

- `docs/ui/target_design_drafts/**`
- `docs/ui/UI_A1_target_markdown_architecture_audit_20260520.md`

未修改：

- `app/**`
- `tests/**`
- 业务代码。
- UI runtime。
- 图标/图片资源。
- 桌面入口。
- 打包产物。

未运行 packaged app，未重新打包。

### 17.1 执行命令记录

| 命令 | 结果 |
|---|---|
| `find /Users/changdali/Desktop/UI -type f -name '*.md' -print0 \| sort -z \| xargs -0 wc -l` | 成功；读取 8 个 Markdown，共 7327 行 |
| `rg --files app/shell app/bioinformatics app/meta_analysis tests/ui docs/ui docs/bioinformatics` | 成功；用于确认当前 shell/Bioinformatics/Meta/tests/docs 文件面 |
| `rg -n "class\|COMMON_SIDEBAR\|Login\|Dashboard\|Settings\|Bioinformatics\|Meta\|LabTools\|测试模式\|show_\|sidebar\|module" app/shell app/bioinformatics app/meta_analysis tests/ui docs/ui docs/bioinformatics -g '*.py' -g '*.md'` | 成功；用于确认当前导航、页面挂载和旧审计证据 |
| `mkdir -p docs/ui/target_design_drafts/meta && cp /Users/changdali/Desktop/UI/*.md docs/ui/target_design_drafts/ && cp /Users/changdali/Desktop/UI/meta/*.md docs/ui/target_design_drafts/meta/ && find docs/ui/target_design_drafts -type f -name '*.md' \| sort` | 成功；归档 8 个 Markdown，并新增 1 个索引 README |
| `git diff --check` | 成功；无 whitespace error 输出 |
| `git status --short` | 成功；仅显示 `docs/ui/UI_A1_target_markdown_architecture_audit_20260520.md` 和 `docs/ui/target_design_drafts/` 为新增文档 |
| `perl -pi -e 's/[ \t]+$//' docs/ui/target_design_drafts/*.md docs/ui/target_design_drafts/meta/*.md` | 成功；仅清理归档副本的行尾空白以满足仓库校验，未改动桌面原始草案 |
| `git diff --cached --check` | 成功；暂存文档无 whitespace error 输出 |

### 17.2 验证结论

本阶段只新增/复制 Markdown，不涉及 runtime 代码、测试代码、资源文件、桌面入口或打包产物，因此未运行完整测试套件。为满足 `git diff --cached --check`，归档副本移除了行尾空白；桌面原始 Markdown 未改动。
