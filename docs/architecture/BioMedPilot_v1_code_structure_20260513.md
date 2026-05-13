# BioMedPilot v1.0 Code Structure Principles

日期：2026-05-13

范围：`/Users/changdali/Developer/biomedpilot v1.0/MainLine`

本文件记录 MainLine 当前代码目录概览和推荐的内部结构原则。它不执行目录迁移，不创建业务模块代码，不改变现有功能。

## 当前实际代码目录概览

当前 MainLine 根目录确认存在：

- `app/`
- `tests/`
- `docs/`
- `scripts/`
- `data/`
- `assets/`

当前 `app/` 内确认存在：

- `app/shell/`
- `app/bioinformatics/`
- `app/meta_analysis/`
- `app/shared/`

当前 `app/` 内确认不存在：

- `app/labtools/`
- `app/lab_tools/`
- `app/lab/`

当前 `app/bioinformatics/` 内已存在多类子目录，例如 adapters、download、legacy、models、pages、pipelines、reports、results、retrieval、search_center、services、standard_assets、tcga。

当前 `app/shared/` 内已存在多类共享能力目录，例如 ai_gateway、data_center、environment、logging、project_center、query_intelligence、report_center、settings、storage、task_center、ui_components。

测试运行可能生成 ignored 的 `__pycache__/` 和 `.pytest_cache/`。这些是运行缓存，不属于推荐代码结构。

## 推荐内部结构原则

### `app/shell/`

桌面壳层。

职责包括登录、主窗口、模块选择、侧边栏、主导航、状态面板、主题和基础 shell 交互。

原则：

- 只协调模块入口，不承载具体业务流程。
- 不把业务模块内部 manifest、schema、branch、raw path、asset id 大量暴露到普通 UI。
- 与业务逻辑交互应通过明确的模块入口、shared interface 或 service contract。

### `app/bioinformatics/`

Bioinformatics 模块。

职责包括 GEO / TCGA / GTEx / 本地表达数据相关的数据检索、导入、识别、标准化、分析准备、任务中心、结果浏览和报告辅助。

原则：

- Bioinformatics search 是生信数据源检索，不是 PubMed 文献检索。
- 生信结果必须区分 draft、dry-run、testing-level、imported result 和 real computed result。
- 不生成假 DEG、假统计结果、假图或假报告。
- 仍在使用的 `app/bioinformatics/legacy/` 需要先做依赖审计，再决定归档或替换；不得直接删除。

### `app/meta_analysis/`

Meta 模块。

职责包括 PICO / PICOS / PECO、检索策略、文献库、去重、标题摘要筛选、全文管理、全文资格判断、提取、质评、统计和报告。

原则：

- Meta search 是 PubMed / 文献数据库检索策略和文献流程，不是 GEO / TCGA / GTEx 数据分析。
- Meta 不应接入表达矩阵分析、GEO 下载或 TCGA / GTEx 数据处理流程。
- Meta 输出同样必须区分 draft、dry-run、testing-level、imported result 和 real computed result。

### `app/labtools/`

基础实验工具模块。

当前 MainLine 不存在 `app/labtools/`。这是未来方向，不代表本阶段创建或接入代码。

未来职责可包括稀释、浓度、qPCR、Western blot、ELISA、细胞计数和实验记录辅助。

原则：

- 不污染 Bioinformatics project manifest。
- 不污染 Meta project manifest。
- 不把实验工具记录伪装成生信分析或 Meta 分析结果。

### `app/shared/`

共享能力层。

职责包括 AI Gateway、query intelligence、医学词库接口、project center、data center、task center、report center、环境检查、feature status、配置、审计、存储和共享 UI 组件。

原则：

- shared 只提供共享服务、接口、模型、状态和基础工具。
- shared 不承载具体业务流程。
- 业务判断应留在 Bioinformatics、Meta、LabTools 或对应模块内。
- AI 和本地模型必须通过 `app/shared/ai_gateway/` 的统一边界。

## 为什么不把 search、report、task、data_entry 做成全局顶层业务模块

BioMedPilot 的不同业务模块使用相似词汇，但语义不同。

### Search

- Bioinformatics search：GEO / TCGA / GTEx / 本地表达数据相关的数据检索、数据集识别和数据源选择。
- Meta search：PubMed / 文献数据库检索策略、关键词、布尔式、文献候选集和检索审计。

两者概念、数据结构、用户期望和合规边界不同，必须留在各自模块内。共享层最多提供 query intelligence、词库和通用检索辅助接口。

### Report

- Bioinformatics report：表达数据、数据源、识别、标准化、分析任务、结果资产和生信解释辅助。
- Meta report：PRISMA、纳排、提取、质评、统计、森林图、异质性和系统评价报告结构。
- LabTools report：未来可用于实验工具记录或计算摘要。

报告可以共享导出接口、manifest、模板基础设施和审计字段，但具体结论和业务结构应留在模块内。

### Task

- Bioinformatics task：数据下载、标准化、分析准备、DEG / enrichment / correlation / survival 等任务。
- Meta task：文献导入、去重、筛选、全文、提取、质评、统计和报告任务。
- LabTools task：未来可用于实验工具计算和记录流程。

共享 task center 只提供任务状态、记录、审计和基础调度接口，不承载业务决策。

### Data entry

- Bioinformatics data entry：表达矩阵、样本分组、数据源配置和分析输入。
- Meta data entry：PICO、纳排标准、文献字段、提取字段和质评字段。
- LabTools data entry：未来实验参数和计算输入。

输入结构不同，不应抽象成全局顶层业务模块。

## 报告结构原则

推荐方向：

- `app/bioinformatics/reports/`：Bioinformatics 业务报告构建、报告资产和模块内报告规则。
- `app/meta_analysis/reports/`：Meta 业务报告构建、PRISMA / 统计 / extraction / quality 报告规则。当前若目录不存在，应由 Meta 阶段任务按需创建。
- `app/labtools/reports/`：未来 LabTools 报告方向。当前 MainLine 不存在 `app/labtools/`，不得在本阶段创建业务代码。
- `app/shared/report_center/`：共享报告接口、manifest、导出基础设施、状态和审计字段。

`app/shared/report_center/` 不应写具体业务结论，不应生成 Bioinformatics、Meta 或 LabTools 的业务解释。

## 数据和缓存原则

默认不得进入 Git：

- 用户项目数据。
- 下载数据集。
- PDF。
- 中间分析结果。
- 本地运行缓存。
- Python cache。
- pytest cache。
- 打包产物。
- 本地日志。

允许进入 Git 的例外：

- 小型、可解释、可复现的 `tests/fixtures/`。
- 小型、可追踪、用于 UI 或功能演示的 demo data，但必须标记用途和范围。
- 当前应用身份、图标和测试依赖的静态资源，例如 `assets/icons/`，不得作为构建缓存误删。

Demo projects 如存在，应保持：

- 小型。
- 可追踪。
- 可解释。
- 不包含真实用户数据。
- 不包含无法复现或无法说明来源的大型分析结果。

Tracked logs、legacy snapshots、示例项目和历史审计文件属于人工确认项。除非独立阶段明确授权并完成审计，否则不直接删除或停止跟踪。

## 功能状态和结果状态原则

功能状态必须区分：

- 可用。
- 测试级。
- 草稿。
- 待确认。
- 阻塞。
- 未接入。
- 开发者预览。

结果状态必须区分：

- `draft`
- `dry-run`
- `testing-level`
- `imported result`
- `real computed result`

UI、报告、handoff 和 stage report 不得把 dry-run 或 testing-level 描述为真实分析结果，不得写临床结论，不得声称 production-ready。

## 当前状态与推荐方向

当前状态：

- MainLine 已有 shell、Bioinformatics、Meta 最小入口和 shared 代码。
- MainLine 没有 `app/labtools/`。
- `app/shared/report_center/` 已存在。
- `app/bioinformatics/legacy/` 仍存在，并且历史审计显示仍有 active import 或动态依赖。

推荐方向：

- 保持 MainLine 稳定可测试。
- 在模块 worktree 中推进模块功能。
- 通过 Integration 做合并验证。
- 确认通过后再进入 MainLine 或 ReleaseBuild。
- 不把推荐结构误执行为目录迁移；目录创建必须由对应阶段任务和测试覆盖驱动。
