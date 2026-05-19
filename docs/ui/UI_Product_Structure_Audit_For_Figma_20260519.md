# BioMedPilot UI / Figma 前置产品结构审计

日期：2026-05-19  
审计对象：`dev/integration` worktree，HEAD `6564227`  
目标：为 Figma 设计前置整理当前桌面软件的真实产品结构、页面树、状态边界、核心流程和每页 UI 信息需求。

## 1. 审计边界

本审计只读取当前代码、docs、测试和模块入口，未修改业务代码，未重构 UI，未运行破坏性命令。

主要依据：

- 桌面入口：`app/main.py`
- 主窗口与外壳：`app/shell/main_window.py`、`app/shell/module_selection.py`、`app/shell/sidebar.py`、`app/shell/login.py`
- 功能状态注册：`app/shared/feature_availability.py`、`app/shared/feature_status.py`
- Bioinformatics：`app/bioinformatics/workspace.py`、`app/bioinformatics/workflow_pages.py`、`docs/bioinformatics_developer_preview_status.md`
- Meta Analysis：`app/meta_analysis/workspace.py`、`app/meta_analysis/pages/*_page.py`、`app/meta_analysis/services/ui_construction_readiness_service.py`
- LabTools：`app/labtools/workspace.py`、`app/labtools/labtools_tool_registry.py`、`app/labtools/ui/*`
- AI Gateway：`app/shared/ai_gateway/*`、`docs/ai_gateway_internal_design_v1.md`、`docs/ai_gateway_desktop_ai_module_v1.md`
- ImageJ / Fiji：`app/shared/local_engines/*`、`app/labtools/imagej_bridge.py`、`app/labtools/image_analysis/local_engine_consumer.py`
- 测试/限制说明：`docs/user_testing/feature_availability.md`、`docs/user_testing/known_limitations.md`

重要解释：

- `stable/mainline` 当前只代表稳定桌面外壳和模块选择入口，不应被当作当前全部功能的真实实现面。
- 当前可用于产品结构审计的集成视图是 `dev/integration`。
- 全局版本状态是 `0.1.0-internal-beta` / `Developer Preview / testing`。

## 2. 状态标签定义

Figma 中必须使用统一状态标签，不能把 testing 或 placeholder 画成已完成能力。

| 状态 | 含义 | Figma 表现 |
| --- | --- | --- |
| stable | 外壳、入口或基础记录能力已经稳定可展示；仍不等于正式生产版。 | 可画成常规可用页面，但保留 internal beta 标记。 |
| MVP | 可执行最小真实任务，但通常需要人工输入、人工复核或明确限制。 | 可画完整操作链，强调人工复核和限制。 |
| developer preview | 内部测试功能；允许用户试走流程，结果不能用于正式科研结论。 | 页面上持续显示 Developer Preview / testing。 |
| placeholder | 有入口、状态或占位说明，但无真实执行能力。 | 只能画空状态、锁定态、规划说明，不画完成结果。 |
| planned | 已登记未来方向，当前版本不开放。 | 只能画路线图或 disabled 入口。 |
| out-of-v1.0 | 当前 v1.0 不应交付或不应承诺的能力。 | 不进入主流程；如出现只能在“未开放”区域说明。 |

## 3. 当前软件主模块

| 模块 | 当前产品定位 | 当前状态 | Figma 设计边界 |
| --- | --- | --- | --- |
| Shell / Dashboard | 本地登录、模块选择、侧边栏、最近项目、测试模式、设置中心入口。 | stable + developer preview | 可画成真实桌面外壳；必须保留本地测试版、账号/订阅占位、设置占位说明。 |
| Bioinformatics | GEO / TCGA / GTEx / 本地表达矩阵的导入、识别、预检、结果浏览、测试摘要。 | developer preview；部分 MVP | 可画完整 11 步工作台，但多数分析页是 preflight/testing，不是正式统计分析。 |
| Meta Analysis | 中文 Meta 分析工作流：PICO、检索、导入、去重、筛选、全文、提取、质量、统计、报告。 | developer preview；部分 testing MVP | 可画主工作流和表单；所有统计、报告、PRISMA、AI 建议必须标注 testing / 人工复核。 |
| LabTools | 本地实验工具：试剂计算、Western Blot 流程、ImageJ/Fiji 外部引擎配置、规划工具。 | calculators/WB 为 MVP；多个 planned | 只画本地计算和人工 ROI 辅助，不画自动识别、自动计数或内置图像算法。 |
| Shared AI Gateway | 内部 AI 调用安全边界，默认关闭，当前主要供本地 Ollama 草稿辅助。 | developer preview / disabled by default | 不画成云 AI、外部 API、自动科研结论生成器。 |
| Shared Local Engines | ImageJ/Fiji、Ollama、PaddleOCR 等外部引擎检测/配置。 | developer preview | 画成外部依赖配置中心，不画成 BioMedPilot 内置算法。 |
| Shared Vocabulary / Query Intelligence | 医学词表、检索词辅助、模块边界策略。 | support layer | 可作为后台能力提示，不建议作为一线主页面。 |

## 4. 全局页面树

```text
BioMedPilot Desktop
├─ Login / 本地测试登录
├─ Module Selection / Dashboard
│  ├─ Bioinformatics card
│  ├─ Meta Analysis card
│  ├─ LabTools card
│  ├─ 最近项目
│  └─ 本地测试信息 / 环境状态
├─ Common sidebar
│  ├─ Dashboard
│  ├─ 生信分析
│  ├─ Meta 分析
│  ├─ 实验工具
│  ├─ 设置中心
│  └─ 测试模式
├─ Settings / 设置中心
│  ├─ 图标资源状态
│  ├─ External Engine Manager
│  ├─ 默认项目路径
│  ├─ 语言
│  ├─ Python/R 环境
│  ├─ 本地 AI 模型
│  ├─ 数据库设置
│  ├─ 图表样式
│  ├─ 导出格式
│  └─ 缓存清理
└─ Testing Mode / 用户测试模式
   ├─ 推荐测试流程
   ├─ 可测试功能
   ├─ 暂未开放功能
   ├─ 已知限制
   └─ 反馈模板生成
```

### Bioinformatics 页面树

```text
Bioinformatics Workspace
├─ Project Home
├─ Data Source / 数据来源与登记
│  ├─ 本地数据导入
│  ├─ GSE 编号检索
│  ├─ 中文研究主题检索
│  │  ├─ GEO/GSE tab
│  │  ├─ TCGA/GDC tab
│  │  └─ GTEx tab
│  └─ 登记状态 / 技术详情
├─ Acquisition Status
├─ Recognition / 数据识别
├─ Readiness Dashboard
├─ Standardized Assets
├─ Group Comparison Design
├─ Workflow Status
├─ Analysis Task Center
├─ DEG Config
├─ Imported DEG Browser
├─ Results Browser
├─ Report Viewer
└─ Settings & Local AI
```

### Meta Analysis 页面树

```text
Meta Analysis Workspace
├─ Project Home
├─ Workflow Dashboard
├─ Protocol / Research Question
├─ Search Strategy
├─ Literature Acquisition / Import
├─ Literature Library
├─ Duplicate Review
├─ Exclusion Criteria
├─ Screening
├─ Full-text Management / Eligibility
├─ Attachment Registry
├─ Extraction
├─ Quality Assessment
├─ Analysis Setup / Results
├─ Reporting / PRISMA / Exports
├─ AI Suggestions
└─ Audit Log
```

当前代码中 Meta 还有 `workflow_integration_page` 的 8 步/中文流程状态聚合视图。Figma 应把它当作 Meta 工作流导航和状态总览，而不是额外的独立分析能力。

### LabTools 页面树

```text
LabTools Workspace
├─ Tools Home
├─ General Reagent Preparation / 通用试剂制备
├─ ImageJ 本地引擎配置
├─ 试剂与实验记录
├─ Cell Experiment Tools
├─ Western Blot Tools
├─ PCR/qPCR Tools
└─ ELISA / Absorbance Tools
```

## 5. 页面状态总表

### Shell / Shared

| 页面 | 状态 | 说明 |
| --- | --- | --- |
| Login | stable + developer preview | 本地测试登录；无真实线上账号、支付、注册或订阅系统。 |
| Module Selection | stable | 三大模块入口、最近项目、本地测试信息可画成真实可用。 |
| Sidebar | stable | 代码实际开放 Dashboard、生信、Meta、LabTools、设置、测试模式。Project/Data/Task/Report Center 在 sidebar 常量中存在，但当前主 sidebar 未作为独立页面开放。 |
| Settings | placeholder + developer preview | 多数设置项为占位；External Engine Manager 可展示外部引擎配置状态。 |
| Testing Mode | stable | 可生成测试反馈模板，展示测试流程和限制。 |
| Project Center | stable support layer | JSON 项目记录和最近项目支持；当前没有完整项目管理 UI。 |
| Data Center / Task Center / Report Center | developer preview support layer | 服务层存在并被模块写入/读取；不应画成完整独立中心。 |

### Bioinformatics

| 页面 | 状态 | 当前能力 | 不能画成 |
| --- | --- | --- | --- |
| Project Home | stable + developer preview | 新建/打开本地项目、显示项目健康和下一步。 | 线上项目协作、云同步。 |
| Data Source | MVP / testing | 本地表达矩阵导入、GSE accession、中文主题检索入口、候选登记。 | 自动完成所有数据库检索和下载。 |
| Chinese Dataset Search | testing | 规则词库 + 可选本地 AI 草稿；GEO/TCGA/GTEx 分 tab 候选。 | AI 自动检索、自动确认、自动下载。 |
| Acquisition Status | testing | 展示登记/下载/候选状态。 | 正式下载中心或全自动 pipeline。 |
| Recognition | testing | 对本地/下载产物做表达矩阵、样本注释等识别。 | 生产级数据质控结论。 |
| Readiness Dashboard | testing | 汇总可继续项、缺失项、GSEA 资源状态和待办。 | 完成度等于可发表分析。 |
| Standardized Assets | testing | 资产标准化预览、确认候选、默认资产表。 | 自动清洗完成的标准矩阵。 |
| Group Comparison Design | testing | 帮助用户确认比较组和分组结构。 | 自动推断病例/对照。 |
| Workflow Status | developer preview | 工作流状态总控。 | 正式 pipeline 监控台。 |
| Analysis Task Center | testing | 管理分析任务、预检结果和下一步。 | 真实批处理统计平台。 |
| DEG Config | placeholder / planned | 方法参数草稿；DESeq2/edgeR/limma 待接入。 | 已运行正式差异表达分析。 |
| Imported DEG Browser | MVP / testing | 浏览用户导入的 DEG 结果候选，支持报告候选标记。 | BioMedPilot 自己计算出的正式 DEG 结果，除非来源明确为导入。 |
| Results Browser | testing | 浏览已登记结果，区分 testing-level/imported/real computed semantics。 | 正式结论浏览器。 |
| Report Viewer | testing | 生成/预览 Markdown testing summary。 | 正式 Word/PDF 或投稿级报告。 |
| Settings & Local AI | developer preview | AI 默认关闭；只允许配置本地 Ollama 辅助草稿。 | 云端 AI、外部 API Key、自动科研解释。 |

### Meta Analysis

| 页面 | 状态 | 当前能力 | 不能画成 |
| --- | --- | --- | --- |
| Project Home | stable + developer preview | 新建/打开 Meta 项目、展示流程入口。 | 多人协作项目空间。 |
| Workflow Dashboard | MVP / testing | 步骤状态、warning、下一步提示。 | 正式审稿/发表状态。 |
| Protocol / Research Question | testing | PICO/PICOS/PECO 草稿、检索式草稿、PubMed testing-level 执行。 | 投稿级最终检索策略。 |
| Search Strategy | testing | 多数据库检索式生成/编辑/确认，PubMed testing-level 候选。 | Web of Science/Embase/CNKI 自动真实检索。 |
| Literature Import | MVP / testing | NBIB/RIS/CSV/PubMed XML testing 导入，diagnostics 和 audit。 | 生产级导入向导或自动修复文件。 |
| Literature Library | testing | 只读文献表、重复风险、状态过滤。 | 自动可信文献库。 |
| Duplicate Review | testing | 疑似重复组、merge preview、最小人工决定。 | 自动合并权威结果或多人仲裁。 |
| Screening | testing | 标题摘要队列、人工 include/exclude/maybe 决策。 | 完整双人筛选系统或 AI 自动筛选。 |
| Full-text / Attachment | testing | 全文状态、附件 registry、缺失报告。 | 自动 PDF 下载、OCR、机构全文访问、Zotero 双向同步。 |
| Extraction | testing MVP | 结构化 ExtractionRecord、人工录入、校验、CSV 导出。 | 自动全文提取或生产级 extraction form。 |
| Quality Assessment | testing + placeholder | ROB/NOS/QUADAS/JBI/AHRQ 表单和 overall suggestion；GRADE placeholder。 | 正式 GRADE evidence profile 或自动质量结论。 |
| Analysis | testing MVP | analysis-ready dataset、基础 pooled effect、prevalence/correlation/diagnostic basic、subgroup、leave-one-out、publication bias basic、forest/funnel PNG、CSV。 | 生产级统计、临床结论、network meta、HSROC、meta-regression。 |
| Reporting | testing MVP | Markdown/HTML/DOCX testing report、简化 PRISMA SVG、补充表、figure package、snapshot、reproducibility package。 | 正式 PDF、正式 PRISMA 2020、投稿级文件。 |
| AI Suggestions | testing | AI suggestion queue，必须人工 accept/reject/edit/apply。 | AI 直接覆盖正式数据。 |
| Audit Log | testing | 只读 testing 事件视图。 | 合规审计系统或 Task Center 替代品。 |

### LabTools

| 页面 | 状态 | 当前能力 | 不能画成 |
| --- | --- | --- | --- |
| Tools Home | stable + developer preview | 工具入口和状态说明。 | 完整实验室信息系统。 |
| General Reagent Preparation | MVP | 本地换算、模板、制备清单；不提供内置配方库。 | 实验方案推荐或安全 SOP。 |
| Western Blot Tools | MVP + placeholder sections | 样品准备、BCA、上样计算、配胶、lane layout、流程记录。 | 自动条带识别、灰度定量、自动 ROI、结果解释。 |
| ImageJ 本地引擎配置 | developer preview | 检测/配置外部 ImageJ/Fiji 路径；失败仍可继续 manual-review workflow 准备。 | 内置图像识别引擎。 |
| 试剂与实验记录 | placeholder / planned | recipe draft、experiment record draft 归类说明。 | 完整 ELN、权限、电子签名、合规审计。 |
| Cell Experiment Tools | planned | 细胞接种、处理分组、实验记录占位。 | 自动细胞计数、活率识别、pathology workflow。 |
| PCR/qPCR Tools | planned | PCR mix、qPCR 结果整理 workflow 占位。 | Ct/Delta Ct/Delta Delta Ct 自动结论或统计解释。 |
| ELISA / Absorbance Tools | planned | 标准曲线、OD 数据整理占位。 | 自动拟合标准曲线、自动反推浓度、实验结论。 |
| Image ROI Export | MVP support capability | fluorescence manual ROI grayscale、wound manual ROI + threshold export package。 | 自动 ROI、自动细胞计数、WB/gel 灰度、交互式图像复核器。 |

## 6. 核心用户流程

### 全局进入流程

1. 本地测试登录。
2. 进入 Module Selection。
3. 选择 Bioinformatics / Meta Analysis / LabTools。
4. 在模块内新建或打开本地项目。
5. 完成当前模块的 testing/MVP 流程。
6. 在 Testing Mode 或模块报告页输出内部测试材料。

### Bioinformatics 主流程

1. 创建或打开生信项目。
2. 选择数据来源：本地表达矩阵、GSE accession、中文主题检索。
3. 登记数据来源或加入下载候选。
4. 进行数据资产识别。
5. 查看 readiness，处理缺失项。
6. 标准化资产并人工确认分组。
7. 进入分析任务中心。
8. 如为导入 DEG，可浏览并标记报告候选；如为内置分析，当前主要是预检/配置。
9. 浏览结果。
10. 导出 Markdown testing summary。

Figma 边界：分析链不能画成正式 DEG / enrichment / correlation / survival 执行完成；只能画成预检、导入结果浏览、testing summary。

### Meta Analysis 主流程

1. 创建或打开 Meta 项目。
2. 在 Workflow Dashboard 查看当前步骤和 warning。
3. 填写 Protocol/PICO，生成并人工确认检索策略。
4. 执行 PubMed testing-level 候选或导入 NBIB/RIS/CSV。
5. 进入文献库和 Duplicate Review。
6. 完成标题摘要筛选和全文状态管理。
7. 手工提取研究特征、结局和效应量。
8. 做 quality assessment，保留人工确认。
9. 运行 testing-level analysis。
10. 导出 testing report、简化 PRISMA 和复现包。

Figma 边界：统计图表和报告必须带 testing / manual review / not clinical / not publication-ready 标签。

### LabTools 主流程

1. 进入 LabTools 首页。
2. 选择通用试剂制备或 Western Blot。
3. 完成本地计算或流程记录。
4. 如涉及图像 workflow，只能进入 ImageJ/Fiji 外部引擎配置或 manual ROI 辅助导出。
5. 导出的 ROI 包只作为人工复核材料。

Figma 边界：不能出现自动 ROI、自动细胞计数、自动条带识别、自动 WB 灰度定量完成页。

## 7. 每个页面的 UI 信息需求

### Shell / Shared 页面

| 页面 | 必须显示的信息 | 主操作 | 风险提示 |
| --- | --- | --- | --- |
| Login | 产品名、版本、Developer Preview、本地账号输入、错误提示。 | 进入 BioMedPilot。 | 注册/VIP/License 只能是占位。 |
| Module Selection | 三模块卡片、模块说明、最近项目、本地环境、当前用户、版本。 | 进入模块。 | 不要像营销 landing page。 |
| Settings | 默认路径、语言、Python/R、本地 AI、数据库、图表、导出、缓存、外部引擎状态。 | 保存/检查配置。 | 大多数设置是占位或配置状态，不是完整管理中心。 |
| Testing Mode | 推荐测试流程、可测试功能、暂未开放功能、已知限制、反馈位置。 | 生成反馈模板。 | 不要让用户以为是正式验收系统。 |

### Bioinformatics 页面

| 页面 | 必须显示的信息需求 |
| --- | --- |
| Project Home | 项目名称、保存位置、已有项目路径、验证状态、最近项目摘要、项目健康、下一步按钮、技术详情折叠。 |
| Data Source | 本地导入/GSE/中文主题三入口；已登记来源数、下载候选数、ready 数；候选详情、文件来源、保存/加入下载/忽略动作。 |
| Chinese Dataset Search | 中文研究主题输入、规则/本地 AI 草稿状态、GEO/TCGA/GTEx tabs、候选卡、候选详情、登记状态、AI 草稿需人工确认提示。 |
| Acquisition Status | 获取计划、登记记录、下载候选、状态 summary、失败/空状态、继续识别按钮、技术详情。 |
| Recognition | 文件识别结果、类型标签、表达矩阵/样本注释/平台注释/临床字段候选、warning、下一步。 |
| Readiness Dashboard | readiness 状态、缺失资产、待办、GSEA 资源状态、能力矩阵、继续标准化按钮。 |
| Standardized Assets | 输入来源、表达矩阵状态、样本状态、分组状态、确认候选表、默认资产、用户资产表、developer diagnostics。 |
| Group Comparison Design | 样本列表、推荐分组、人工修改区、保存比较组、warning。 |
| Workflow Status | 当前阶段、ready 状态、步骤列表、可运行阶段、技术状态。 |
| Analysis Task Center | 任务列表、输入摘要、结果摘要、下一步、任务记录、进入 DEG 配置或结果浏览动作。 |
| DEG Config | 输入摘要、比较组摘要、方法草稿、preflight checks、明确 DESeq2/edgeR/limma 待接入。 |
| Imported DEG Browser | 导入 DEG 摘要、结果表、详情预览、用户备注、报告候选标记、边界说明。 |
| Results Browser | 结果来源、语义标签、测试级/导入/真实计算区分、报告 readiness、技术详情。 |
| Report Viewer | 报告草稿状态、结果语义、章节表、Markdown 预览、manifest diagnostics、testing summary 标签。 |
| Settings & Local AI | AI 默认关闭、本地 Ollama 开关、base URL、model、连接状态、隐私提示、草稿用途说明。 |

### Meta Analysis 页面

| 页面 | 必须显示的信息需求 |
| --- | --- |
| Project Home | 项目名称、研究主题、保存位置、创建/打开项目、当前项目摘要、Developer Preview 标签。 |
| Workflow Dashboard | 8 步/18 步流程状态、artifact 摘要、warning、下一步、当前阻塞项。 |
| Protocol / Research Question | review question、PICO/PICOS/PECO 字段、planned databases、检索式草稿、人工确认状态、PubMed testing preview。 |
| Search Strategy | 数据库列表、检索式编辑器、确认/导出/复制、PubMed testing 执行、候选表、候选详情。 |
| Literature Import | PubMed 候选、本地文件导入、source/format、diagnostics、导入批次、文献表、用户备注。 |
| Literature Library | 文献表、DOI/PMID、来源、重复风险、workflow 状态、只读详情。 |
| Duplicate Review | duplicate group list、相似原因、merge preview、record selector、人工决定、decision log。 |
| Screening | 队列摘要、记录列表、标题/摘要详情、AI/规则建议、人工 include/exclude/maybe、排除理由、备注。 |
| Full-text / Attachment | 全文状态、附件路径/链接、缺失全文报告、排除原因、OCR/PDF 不开放提示。 |
| Extraction | included studies、schema profile、outcome rows、field validation、draft save/load、manual edits log、CSV export。 |
| Quality Assessment | study design、tool registry、domain-level judgements、overall suggestion、quality table、GRADE placeholder 明示。 |
| Analysis | preflight、analysis plan、model/effect measure、dataset 状态、testing run result、I2/CI 等结果字段、advanced method blocked states。 |
| Reporting | test summary、formal Markdown/HTML/DOCX testing report、简化 PRISMA SVG、figure package、snapshot、reproducibility package、PDF 未开放。 |
| AI Suggestions | suggestion queue、来源、状态 pending/accepted/rejected/edited/applied、人工操作按钮、不会直接覆盖正式数据。 |
| Audit Log | import/sanitize/normalize/duplicate/screening/fulltext/extraction/analysis/report 事件、只读过滤、空状态。 |

### LabTools 页面

| 页面 | 必须显示的信息需求 |
| --- | --- |
| Tools Home | 工具卡片、状态 badge、类别、说明、边界声明、可用/未启用区别。 |
| General Reagent Preparation | 计算类型 tabs、输入参数、单位、结果、review_notice、模板/制备记录入口。 |
| Western Blot | 样品准备、BCA、上样计算、SDS-PAGE 配胶、lane layout、流程记录、结果与灰度分析 placeholder。 |
| ImageJ Config | ImageJ/Fiji 外部路径、检测状态、错误信息、可继续 manual workflow 提示、不会自动下载/上传/联网。 |
| 试剂与实验记录 | recipe draft、experiment record draft、模板归类、完整 ELN 未开放。 |
| Cell Experiment Tools | planned 状态、未来能力、当前不可做自动细胞计数/活率/pathology。 |
| PCR/qPCR | planned 状态、未来 PCR mix/plate/Ct 整理、当前不解释 Ct 结论。 |
| ELISA/Absorbance | planned 状态、未来标准曲线/OD 整理、当前不拟合、不反推浓度。 |
| Manual ROI Export | ROI 参数、threshold、overlay preview、CSV/JSON/Markdown export、manual_review_required、safety_note。 |

## 8. Figma 禁止误画能力清单

这些能力不能在 Figma 中画成“已完成”“自动完成”或“正式可用”：

1. AI Gateway 默认关闭：`allow_network=false`、`allow_external_model=false`、`allow_sensitive_upload=false`、`default_provider=disabled`。
2. AI 只能作为草稿辅助，不能直接写入最终分析结果、筛选决定、提取数据、统计结论或报告结论。
3. 外部 API provider 未实现；不要画 OpenAI/DeepSeek/Gemini/Claude API Key 管理或云端 AI 服务。
4. ImageJ/Fiji 是外部引擎配置，不是 BioMedPilot 内置自动图像识别。
5. 图像分析不能宣称自动 ROI、自动细胞计数、自动条带识别、自动 WB/gel 灰度定量。
6. fluorescence 和 wound healing 当前只能画成 manual ROI / manual threshold / semi-quantitative 辅助输出。
7. LabTools ROI export 不是正式实验结论、医疗用途解释或实验 SOP。
8. Bioinformatics DEG/enrichment/correlation/survival 多数是 preflight/testing，不是正式统计执行。
9. Bioinformatics 报告是 Markdown testing summary，不是正式 Word/PDF/figure package。
10. Meta Analysis 的 pooled effect、forest/funnel、result table 是 testing-level；不能画成临床/发表级结论。
11. Meta network meta-analysis、diagnostic bivariate / HSROC、meta-regression、trim-and-fill 不开放或未实现。
12. Meta Reporting 不能画正式 PDF、正式 PRISMA 2020 或投稿级 GRADE evidence profile。
13. Meta Full-text / Attachment 不能画自动 PDF 下载、自动 OCR、机构全文访问、绕过 paywall 或 Zotero 双向同步。
14. Duplicate Review、Screening、Extraction、Quality 必须保留人工确认，不允许画成 AI 自动完成。
15. Project/Data/Task/Report Center 服务层存在，但不能画成完整独立管理中心，除非只作为未来规划。

## 9. 可直接给 Figma 使用的设计 brief

请为 BioMedPilot / 医研智析设计 macOS 桌面端 Developer Preview 产品界面。产品是面向医学科研的本地桌面软件，不是网页后台，不是营销站。视觉风格应专业、克制、低噪音，使用 deep navy、teal、white、light gray，保留 `0.1.0-internal-beta`、`Developer Preview / testing`、`本地测试版` 状态标记。核心信息架构包含 Shell、Bioinformatics、Meta Analysis、LabTools、Settings、Testing Mode。每页必须让用户知道当前位置、当前输入、当前状态、下一步和限制。

Bioinformatics 设计为本地项目工作台：数据来源与登记、中文主题检索、数据识别、readiness、标准化资产、分组设计、分析任务、导入 DEG 浏览、结果浏览和 Markdown testing report。多数分析功能是 preflight/testing，不能表现为正式 DEG、富集、相关性、生存分析或发表级报告。

Meta Analysis 设计为中文流程型工作台：Protocol/PICO、检索策略、文献导入、文献库、去重、筛选、全文、提取、质量评价、testing-level analysis、reporting、AI suggestions 和 audit log。所有统计结果、PRISMA、报告和 AI 建议都必须显示 testing/manual review，不可表现为临床或发表级结论。

LabTools 设计为本地实验工具工作台：通用试剂制备、Western Blot 工具、ImageJ/Fiji 外部引擎配置、试剂与实验记录、PCR/qPCR、ELISA/吸光度、细胞实验工具。只展示本地计算、人工录入和 manual ROI 辅助；不要画自动 ROI、自动细胞计数、自动条带识别或内置图像识别。

AI Gateway 必须默认关闭，只能在设置中作为本地 Ollama 草稿辅助开关出现；不设计云 AI、外部 API Key 或自动科研结论。ImageJ/Fiji 必须作为外部引擎配置出现，不是内置算法。

## 10. 可直接给 Figma / AI 设计工具的 prompt

```text
Design a premium macOS desktop application UI for "BioMedPilot / 医研智析", version 0.1.0-internal-beta, Developer Preview / testing. The app is a local biomedical research desktop platform with a restrained professional style: deep navy, teal, white, light gray, compact data-dense layouts, clear status badges, and no marketing hero sections.

Create a coherent product structure with:
1. Login page for local testing user.
2. Module Selection dashboard with three modules: Bioinformatics, Meta Analysis, LabTools, plus recent projects and local environment status.
3. Common sidebar with Dashboard, Bioinformatics, Meta Analysis, LabTools, Settings, Testing Mode.
4. Bioinformatics workspace pages: Project Home, Data Source & Registration, Chinese Dataset Search with GEO/TCGA/GTEx tabs, Recognition, Readiness Dashboard, Standardized Assets, Group Comparison Design, Analysis Task Center, Imported DEG Browser, Results Browser, Report Viewer, Settings & Local AI.
5. Meta Analysis workspace pages: Workflow Dashboard, Protocol/PICO, Search Strategy, Literature Import, Literature Library, Duplicate Review, Screening, Full-text/Attachment, Extraction, Quality Assessment, Analysis Setup/Results, Reporting/PRISMA/Exports, AI Suggestions, Audit Log.
6. LabTools workspace pages: Tools Home, General Reagent Preparation, Western Blot Tools, ImageJ/Fiji External Engine Config, Reagent & Experiment Records, Cell Experiment Tools, PCR/qPCR Tools, ELISA/Absorbance Tools.

All pages must preserve status semantics:
- Shell basics are stable but still internal beta.
- Bioinformatics and Meta Analysis are Developer Preview / testing.
- LabTools calculators and Western Blot are MVP/manual tools; PCR/qPCR, ELISA, cell experiment automation are planned/disabled.
- AI Gateway is disabled by default and only supports explicit local Ollama draft assistance.
- ImageJ/Fiji is an external engine configuration, not built-in automatic image recognition.
- Do not show automatic ROI, automatic cell counting, automatic band detection, clinical conclusions, production statistics, formal PRISMA 2020, formal PDF report, or publication-ready conclusions.

Use explicit badges such as "Testing", "Manual review required", "Placeholder", "Planned", "Not available in v1.0", and "Developer Preview". Make every workflow page show current step, required input, current status, warnings, primary action, secondary actions, and next step.
```

## 11. 建议优先设计的 10 个核心页面

1. Module Selection / Dashboard：决定三大模块的第一印象和状态语言。
2. Bioinformatics Project Home：定义本地项目创建/打开/健康状态的通用模式。
3. Bioinformatics Data Source & Registration：当前生信最核心、最复杂的入口页。
4. Bioinformatics Readiness Dashboard：承接识别、标准化和分析前的状态解释。
5. Bioinformatics Results Browser + Report Viewer：必须建立 testing/imported/real computed 的结果语义边界。
6. Meta Workflow Dashboard：Meta 的全流程导航和 warning 体系核心。
7. Meta Literature Import + Library：导入、diagnostics、文献表是 Meta 的主工作量入口。
8. Meta Extraction + Quality Assessment：最高摩擦的人工表单区，最需要先定交互模式。
9. Meta Analysis + Reporting：最容易被误画成正式科研结论，必须先设计 testing-level 呈现。
10. LabTools Tools Home + Western Blot + ImageJ Config：实验工具状态和外部引擎边界需要一次性统一。

## 12. 设计执行建议

- 先建立统一状态 badge 组件：stable、MVP、Developer Preview、Testing、Manual review required、Placeholder、Planned、Out of v1.0。
- 所有“结果”页面必须包含结果来源、执行等级、人工复核状态、不可用于临床/发表的提示。
- 普通用户页面避免直接显示 `manifest`、`handoff`、`artifact`、`backend`；这些进入折叠技术详情。
- Figma 不要把模块画成营销卡片集合，应画实际工作台和密集但清晰的科研工具界面。
- 每个模块的主色可以沿用统一 navy/teal，但不要把所有页面做成单一蓝绿色；用灰、白、状态色和表格层级建立可读性。
- 第一轮 Figma 只覆盖核心页面和关键状态，不设计 out-of-v1.0 能力的完整页面。
