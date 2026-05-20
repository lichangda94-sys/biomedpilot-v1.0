# Meta 分析模块全版本目录与进度审计

审计日期：2026-05-13
审计目标分支：`dev/meta-analysis`
当前 HEAD：`e97d87e chore(meta): remove backup artifact and ignore local conflict copies`
真实仓库路径：`/Users/changdali/Developer/BioMedPilot`
文稿入口：`/Users/changdali/Documents/BioMedPilot -> /Users/changdali/Developer/BioMedPilot`

## 结论摘要

Meta 分析当前有效开发线是 `dev/meta-analysis`。该分支不是 mainline 壳页面，而是已经接入桌面入口的 8 步中文 workflow：

1. 项目首页
2. 研究问题与 PICO
3. 检索策略
4. 文献库与导入
5. 去重与筛选
6. 数据提取与质量评价
7. 统计分析
8. 报告导出

当前已经完成并接入桌面入口的是 M0-M3：

- M0：恢复真实 Meta Workflow 入口。
- M1：项目首页与 PICO / Protocol 闭环。
- M2：confirmed Protocol -> 检索策略 -> PubMed testing-level 执行 -> candidates preview -> 选择加入文献库。
- M3：文献库诊断 -> 重复文献识别 -> 人工去重 -> 去重后文献库 -> PRISMA 数字摘要 -> 筛选队列准备。

服务层比当前桌面主流程更宽，已经存在 full-text、extraction、quality、analysis、report、AI suggestion 等 testing-level 服务和页面状态。但这些不能被汇报为生产级系统综述软件，也不能被描述为投稿级、临床级或完整 PRISMA / 统计平台。

`app/meta_analysis/legacy/` 是历史快照和参考区，不是当前 Meta runtime 边界。它包含大量旧桌面壳、GEO/Bioinformatics readiness、旧 literature/dedup、旧 task runner 和旧 packaging 资料；除已有过渡 adapter 外，后续不应新增对 legacy 的直接依赖。

## 审计范围

本次审计读取了：

- 当前工作树 `dev/meta-analysis`。
- 所有本地分支的 `app/meta_analysis` 文件数量和目录结构。
- Meta 相关历史分支：`codex/meta-analysis-refresh`、`codex/meta-workflow-ui`、`codex/meta-search-ui-main`、`codex/meta-search-main`、`codex/meta-search-main-v2`、`codex/bio-chinese-dataset-search-page`、`codex/biomedpilot-root`。
- mainline / shared / bio 分支中携带的 Meta 快照或 shell 状态。
- 当前测试：`tests/meta_analysis` 与 `tests/ui/test_meta*`。
- 既有报告：`docs/meta_analysis_current_status.md`、`docs/meta_analysis_legacy_migration_audit.md`、`docs/meta_dev_reports/`。

本次审计没有合并历史分支，没有恢复旧 schema，没有改业务代码。

## 分支版本图谱

| 分支 | HEAD | Meta 文件数 | 测试文件数 | 定位 |
| --- | --- | ---: | ---: | --- |
| `stable/mainline` | `67e5b13` | 4 | 2 | mainline shell contract。只有 `__init__.py`、`project_workspace.py`、`version.py`、`workspace.py`，不是完整 Meta workflow。 |
| `dev/shared-vocabulary` | `2153307` | 4 | 2 | Shared vocabulary 线，保留 mainline shell 级 Meta 文件，不承载 Meta 开发。 |
| `codex/meta-search-main` | `4e0ca45` | 427 | 74 | 早期 Meta 主体快照，包含 legacy 和 active services，但无当前 workflow_pages。 |
| `codex/meta-search-main-v2` | `4e0ca45` | 427 | 74 | 与 `codex/meta-search-main` 同提交。 |
| `codex/meta-search-ui-main` | `b026f9d` | 433 | 76 | Search UI / PubMed execution 方向，含 `app/meta_analysis/search` 早期实现。 |
| `codex/bio-chinese-dataset-search-page` | `dcb07cc` | 442 | 82 | 加入 PICO workspace v2 的中间快照，但分支名称属于 Bio 工作线，不是当前目标分支。 |
| `codex/meta-workflow-ui` | `8b6d0b6` | 454 | 95 | 工作流 UI 后续阶段连接线，是当前 UI 接入的重要历史来源。 |
| `codex/meta-analysis-refresh` | `e9c17c2` | 455 | 95 | 较新的项目首页 UI refresh，已作为 M0-M1 的参考来源。 |
| `codex/ai-gateway-call-isolation-audit` | `2fea2a6` | 454 | 95 | 非 Meta 所有权分支，携带接近当前的 Meta 快照。 |
| `dev/bioinformatics` | `59369de` | 454 | 95 | Bioinformatics 开发线，携带 Meta 快照但不是 Meta 主线。 |
| `dev/meta-analysis` | `e97d87e` | 455 | 96 | 当前 Meta 目标分支，已完成 M0-M3，并清理 backup / conflict 副本包装风险。 |

判断标准：

- 当前开发与后续修复应以 `dev/meta-analysis` 为唯一目标。
- 历史分支只能作为参考或 cherry-pick 来源，不应整分支 merge。
- `stable/mainline` 的 Meta 状态是 shell contract，不代表 Meta 功能丢失；它与 `dev/meta-analysis` 是不同目标线。

## 当前目录清单

`app/meta_analysis` 当前共有 455 个已跟踪文件。目录分布如下：

| 目录 | 文件数 | 内容定位 |
| --- | ---: | --- |
| `app/meta_analysis/adapters/` | 8 | active Meta 与旧 import/dedup 等兼容层的 adapter。 |
| `app/meta_analysis/analysis/` | 1 | 分析包占位入口。 |
| `app/meta_analysis/extraction/` | 2 | extraction schema registry 包入口。 |
| `app/meta_analysis/legacy/` | 334 | 历史快照、旧 UI、旧 literature/dedup、GEO/Bioinformatics readiness、旧测试与文档。非当前 runtime 主边界。 |
| `app/meta_analysis/models/` | 14 | protocol、criteria、dedup、extraction、prisma、publication、analysis 等数据模型。 |
| `app/meta_analysis/pages/` | 19 | workflow dashboard、protocol、literature、dedup、screening、fulltext、extraction、quality、analysis、reporting 等页面状态。 |
| `app/meta_analysis/search/` | 7 | Meta-owned search 层，包括 PubMed、search strategy builder、candidate handoff。 |
| `app/meta_analysis/services/` | 55 | 当前服务层主体，覆盖 PICO、search、library、import、dedup、screening、fulltext、extraction、quality、analysis、report、AI、audit、governance 等。 |
| `app/meta_analysis/stats/` | 4 | testing-level meta effect、heterogeneity、模型工具。 |
| `app/meta_analysis/quality/` | 2 | 质量评价工具 registry。 |
| root files | 12 | `workspace.py`、`project_workspace.py`、`workflow_pages.py`、`ui_text.py`、`version.py` 等入口和兼容导出。 |

当前测试目录：

- `tests/meta_analysis/`：96 个文件，覆盖服务、阶段报告、M0-M3、内部 beta、统计和报告 testing。
- `tests/ui/` 中 Meta 相关文件：3 个，覆盖 workflow、M2 search UI、M3 dedup UI。

## 当前主入口与桌面接入

关键入口：

- `app/meta_analysis/workspace.py`
  - 定义 `MetaAnalysisWorkspaceWidget`。
  - 桌面入口中的 Meta 模块真实挂载点。
  - 负责项目首页、PICO、检索策略、文献库、去重、数据提取、统计、报告导出 8 步页面。
  - 当前文件约 3234 行，是 M0-M3 UI 接入的主要承载。
- `app/meta_analysis/pages/workflow_integration_page.py`
  - 定义 8 步 workflow 元数据和状态联动。
  - 将项目 artifact 映射到 `未开始 / 草稿 / 待确认 / 已完成 / 有警告 / 阻塞 / 待筛选` 等状态。
- `app/meta_analysis/project_workspace.py`
  - 创建 / 打开 / 校验 Meta 项目。
  - 写入 `meta_project_manifest.json` 和 `meta_project_config.json`。
  - 创建研究问题、检索策略、文献库、screening、extraction、quality、analysis、prisma、reports、exports 等目录。

桌面入口当前不是 shell-only 页面。`stable/mainline` 的 shell 页面曾覆盖桌面入口，这是 M0 修复对象；当前 `dev/meta-analysis` 已恢复真实 workflow。

## M0-M3 当前进度

### M0：Workflow 入口

已实现：

- 8 步中文 workflow。
- 左侧项目侧栏、项目状态、步骤导航。
- 主界面隐藏 branch/schema/manifest 原始 JSON，只在开发者诊断折叠区显示。
- 主界面不再显示“完整功能开发保留在 dev/meta-analysis”等壳文案。
- 无项目时阻塞业务步骤，只允许新建或打开项目。

代表文件：

- `app/meta_analysis/workspace.py`
- `app/meta_analysis/pages/workflow_integration_page.py`
- `tests/meta_analysis/test_meta_workspace_ui_navigation.py`

### M1：项目首页 + PICO / Protocol

已实现：

- 新建 Meta 项目。
- 打开已有 Meta 项目。
- 项目 manifest / config 写入。
- 中文研究问题输入。
- PICO / PICOS / PECO 选择。
- PICO 草稿生成、编辑、保存。
- Protocol 确认。
- confirmed protocol 写入 `protocol/pico_workspace_confirmed.json`。
- 检索策略页可读取 confirmed protocol，并在未确认时阻塞。

代表文件：

- `app/meta_analysis/project_workspace.py`
- `app/meta_analysis/services/pico_workspace_service.py`
- `app/meta_analysis/pages/protocol_page.py`
- `tests/meta_analysis/test_pico_workspace_v2_service.py`
- `tests/meta_analysis/test_meta_workspace_ui_navigation.py`

### M2：检索策略与文献获取闭环

已实现：

- confirmed Protocol -> 多数据库检索策略草稿。
- 支持数据库：PubMed、Web of Science、Embase、Cochrane Library、CNKI、WanFang、VIP。
- PubMed 检索式可保存、编辑、确认。
- PubMed 仅在确认后提供 testing-level 在线执行。
- 非 PubMed 数据库只支持检索式生成、编辑、确认、复制/导出；不显示在线检索。
- PubMed candidates preview 展示标题、作者、年份、期刊、PMID、DOI、摘要状态。
- 用户可选择 candidates 加入 literature library。
- 用户备注只作为人工备注，不参与识别、检索和去重。

代表文件：

- `app/meta_analysis/search/search_strategy_builder_service.py`
- `app/meta_analysis/search/pubmed_search_service.py`
- `app/meta_analysis/search/pubmed_candidates_handoff_service.py`
- `app/meta_analysis/services/literature_library_service.py`
- `app/meta_analysis/services/multisource_literature_import_service.py`
- `tests/ui/test_meta_search_stage_m2.py`
- `tests/meta_analysis/test_search_strategy_builder_v2_service.py`
- `tests/meta_analysis/test_pubmed_candidates_handoff.py`

边界：

- PubMed 是 testing-level 查询，不代表系统综述正式检索完成。
- WOS / Embase / Cochrane / CNKI / WanFang / VIP 没有联网自动检索 client。
- 检索结果不会自动导入、自动去重、自动筛选或自动更新 PRISMA。

### M3：文献库诊断、去重 Review、PRISMA 数字联动

已实现：

- 文献库诊断：总数、来源统计、最近导入批次、成功/跳过/失败、字段缺失摘要。
- 文献列表：标题、年份、期刊、PMID、DOI、来源、摘要状态、当前状态。
- 文献详情：标题、作者、年份、期刊、PMID、DOI、abstract、来源、批次、筛选状态、用户备注。
- 本地导入入口：NBIB、RIS、CSV、PubMed XML；其他来源保持 testing / preview 边界。
- 重复组生成。
- 重复组风险等级。
- 重复组详情和并排比较文本。
- 人工决定：合并、保留全部、标记非重复、选择主记录、跳过稍后处理。
- 去重后文献库生成，不物理删除原始记录。
- provenance 保留：原始导入记录、主记录、merged_from、merge_decision、decision_time、user_decision。
- PRISMA literature acquisition summary：
  - PubMed 来源识别数。
  - local imports 识别数。
  - 去重前总数。
  - 移除重复数。
  - 去重后记录数。
  - title/abstract screening ready 数。
- 筛选队列准备：active records > 0 且完成去重或允许跳过去重后，可创建标题摘要筛选队列。

代表文件：

- `app/meta_analysis/services/literature_library_service.py`
- `app/meta_analysis/services/dedup_review_v2_service.py`
- `app/meta_analysis/services/formal_report_service.py`
- `app/meta_analysis/services/title_abstract_screening_v2_service.py`
- `tests/meta_analysis/test_stage_m3_literature_dedup_prisma.py`
- `tests/ui/test_meta_stage_m3_dedup_workflow.py`

边界：

- 去重算法不声明完全自动可靠。
- 原始记录不自动删除。
- 创建筛选队列不等于完成标题摘要筛选。
- PRISMA 数字在去重完成前是 preliminary。

## 服务层已开发但需谨慎汇报的能力

当前服务层存在较多 testing-level 能力，部分已在桌面后续页面中有入口或占位：

- Full-text Management v1：本地 PDF 绑定、全文可用性 registry、不可用原因。无自动 PDF 下载。
- Full-text Parsing v1：本地 PDF 文本解析 testing。无 OCR、无可靠表格抽取、无最终提取值自动写入。
- Extraction Schema Registry v1：多类 Meta extraction schema 模板。
- Manual Extraction Effect Row UI v1：人工提取 effect row draft，保留 evidence refs 和校验。
- Quality Assessment Framework v1：ROB2、ROBINS-I、NOS、QUADAS-2、JBI、AHRQ 等工具推荐与人工评分记录。推荐不是最终风险结论。
- Analysis Plan Builder v1：从 confirmed protocol、extraction、quality 生成分析计划草稿并支持确认。
- Meta Statistics Engine v2：testing-level fixed/random pooling、heterogeneity、subgroup、leave-one-out、Egger/funnel 数据、forest/funnel/result table。
- Reporting：testing Markdown/HTML/DOCX draft、简化 PRISMA、figure package、reproducibility package。
- AI-assisted Review / AI-assisted Extraction Queue：候选建议流，需要人工 accept/apply，不自动覆盖正式数据。

这些能力可描述为“服务层和 testing UI 已有基础”，不能描述为 production-ready。

## Legacy 目录审计

`app/meta_analysis/legacy/` 当前有 334 个已跟踪文件：

| 子目录 | 文件数 | 审计定位 |
| --- | ---: | --- |
| `legacy/app/` | 20 | 旧桌面 shell 和窗口组件。不要作为当前入口恢复。 |
| `legacy/app_meta/` | 21 | 旧 Meta standalone UI 原型。可参考交互概念，不应直接迁移。 |
| `legacy/assets/` | 94 | 旧图标和视觉资产。保留为归档。 |
| `legacy/literature/` | 16 | 旧 literature import/dedup/parser/normalize/store。已有少量过渡 adapter 参考。 |
| `legacy/extraction/` | 7 | 旧 extraction/rule service。仅作为参考。 |
| `legacy/fulltext/` | 4 | 旧 fulltext service。仅作为参考。 |
| `legacy/bias/` | 4 | 旧 bias service。仅作为参考。 |
| `legacy/analysis/` | 10 | 旧 analysis/profile/readiness。多数偏 Bioinformatics/GEO，不属于当前 Meta runtime。 |
| `legacy/analysis_profiles/` | 4 | 旧 profile config。仅供未来评估。 |
| `legacy/geo_readiness/` | 8 | GEO/GSE readiness，明确不属于当前 Meta。不得迁移。 |
| `legacy/local_data/` | 5 | 本地数据 / GEO readiness，属于旧 Bioinformatics 边界。不得迁移到 Meta。 |
| `legacy/core/` | 15 | 旧项目、任务、路径、日志基础设施。不要引入当前 runtime。 |
| `legacy/reporting/` | 4 | 旧 reporting summary。仅供参考。 |
| `legacy/scripts/` | 12 | 旧 dev check / runner / packaging 脚本。不要接入当前主流程。 |
| `legacy/tests/` | 75 | 旧测试快照，记录历史能力。 |
| `legacy/docs/` | 25 | 旧模块开发文档，多数描述 Bio/GEO readiness，不代表当前 Meta。 |

当前明确黑名单：

- `legacy/geo_readiness/`
- GSE33630 / GPL570 / DEG-ready matrix
- TCGA / GTEx / GEO submission readiness
- legacy main window / app shell
- scheduler / automatic task scanning / production downloader
- 任何 Bioinformatics、GEO、TCGA、GDC、GTEx 数据分析 runner

当前可未来评估但需测试先行的候选：

- literature import edge cases
- dedup similar-title thresholds
- primary record completeness scoring
- field-source merge trace
- artifact preview / result detail ideas

## 用户实际使用流程

当前推荐测试流程：

1. 打开桌面入口 `BioMedPilot.app`。
2. 进入 Meta 分析模块。
3. 在项目首页新建或打开 Meta 项目。
4. 进入“研究问题与 PICO”，输入中文研究问题。
5. 选择 PICO / PICOS / PECO，生成草稿。
6. 用户编辑草稿并确认 Protocol。
7. 进入“检索策略”，从 confirmed Protocol 生成各数据库检索式。
8. 用户确认 PubMed 检索式。
9. 执行 PubMed testing-level 检索，查看 candidates preview。
10. 用户选择 candidates 加入文献库。
11. 在“文献库与导入”查看诊断、字段缺失、导入批次和详情；也可本地导入 NBIB / RIS / CSV / PubMed XML。
12. 进入“去重与筛选”，生成重复组。
13. 人工查看重复组详情，保存合并 / 非重复 / 跳过等决定。
14. 生成去重后文献库。
15. 查看 PRISMA literature acquisition 数字。
16. 创建标题摘要筛选队列，进入下一阶段 M4。

## 当前主要风险

1. 分支风险：`stable/mainline` 仍是 shell contract，不能用它判断 Meta 当前功能是否存在。
2. 目录风险：`legacy/` 文件多、内容杂，包含 Bioinformatics/GEO 历史内容；必须继续保持隔离。
3. UI 风险：M0-M3 已接入，M4 之后的页面虽然存在 testing 服务和部分页面，但真实用户工作流还需继续分阶段打磨。
4. 统计风险：`Meta Statistics Engine v2` 是 testing-level，不能承诺 production 或投稿级统计有效性。
5. 联网风险：只有 PubMed testing-level 查询；其他数据库只生成检索式和导出，不执行联网检索。
6. iCloud 风险：历史上仓库和桌面 app 在 iCloud Documents/Desktop 下触发过副本和半下载 `.app`；当前已迁移到 `/Users/changdali/Developer/BioMedPilot` 和 `/Users/changdali/Applications/BioMedPilot.app`。

## 后续开发建议

### M4：标题摘要筛选与全文筛选

优先实现：

- 标题摘要筛选队列的高效人工审核 UI。
- include / exclude / uncertain / needs review 决策保存。
- 排除原因与 PRISMA reason mapping。
- 筛选进度和 PRISMA screened / excluded 初步联动。
- 不引入自动最终筛选。

### M5：数据提取与质量评价重接入

优先实现：

- Manual extraction effect row 的用户级表格体验。
- extraction schema 选择。
- 质量评价工具选择和人工评分。
- extraction / quality 对 analysis plan 的阻塞条件。

### M6：统计分析前置校验

优先实现：

- 只允许 confirmed analysis plan 触发 testing statistics。
- 明确小样本、混合效应量、缺失质量评价等 warning。
- 统计结果继续标记 testing-level。

### M7：报告导出

优先实现：

- 报告草稿汇总真实 artifact。
- 明确 discussion / conclusion 需要人工编辑。
- PRISMA 继续保留 source references。
- 不声称 production PDF 或投稿级报告。

## 审计证据摘要

关键命令结果：

- 当前分支：`dev/meta-analysis`
- 当前 HEAD：`e97d87e`
- `git status --short --branch`：干净
- `app/meta_analysis` 当前已跟踪文件：455
- `tests/meta_analysis` 当前已跟踪文件：96
- `tests/ui` 中 Meta UI 测试文件：3
- `stable/mainline` 中 `app/meta_analysis` 文件：4，属于 shell contract
- `codex/meta-analysis-refresh` 中 `app/meta_analysis` 文件：455，已被当前 M0-M3 参考吸收
- `dev/meta-analysis` 相对 `codex/meta-analysis-refresh` 主要新增：M2 搜索 UI、M3 文献库/去重/PRISMA UI、package backup/conflict ignore

本报告用于项目负责人汇报、后续开发交接和未来 ChatGPT/Codex 继续思考时快速恢复上下文。
