# Meta preview 页面按钮/模块接入审计

日期：2026-06-11
范围：当前 active runtime `app/meta_analysis/workspace.py` 与 `app/meta_analysis/pages/workflow_integration_page.py`。不把 `app/meta_analysis/legacy/` 作为当前页面证据。

## 本轮结论

- 主工作台侧栏已从 8 个粗粒度步骤扩展为可直接进入的 18 个页面：项目首页、页面能力审计、PICO、检索策略、文献库与导入、去重与筛选、排除标准、标题摘要筛选、全文管理、数据提取、AI 辅助提取、质量评价、分析计划、统计分析、图表结果、PRISMA、报告导出、复现包。
- 已实现但此前未独立暴露的页面函数现在有侧栏路由：排除标准、标题摘要筛选、全文管理、AI 辅助提取、质量评价、分析计划、统计分析、图表结果、PRISMA、复现包。
- 去重页和提取页不再重复嵌套全文/质量大页面，改为明确下一步提示，避免同一功能在不同页面重复显示。
- 当前统计、报告、全文、AI 和质量功能仍保留 Developer Preview / testing 边界；页面按钮和模块已接入可执行本地服务、只读数据源或明确的页面跳转，但不声明临床、投稿、监管或正式生产统计结论。

## 页面与按钮/模块接入表

| 页面 | 按钮 / 模块 | 接入功能或指向 |
| --- | --- | --- |
| 项目首页 | 新建 Meta 项目 | 创建项目目录、manifest、config 和标准目录结构 |
| 项目首页 | 打开已有项目 | 选择并校验 Meta 项目文件夹 |
| 项目首页 | 继续：研究问题 / PICO | 跳转 `pico_workspace` |
| 页面能力审计 | 页面/按钮/模块接入表 | 在应用内只读展示 active runtime 每个页面按钮和模块接入的服务、跳转和边界 |
| 页面能力审计 | 导出审计记录 JSON | 写入 `audit/meta_page_button_audit_runtime.json`，无项目时写入默认本地 Meta audit 存储 |
| 页面能力审计 | 导出审计表 CSV | 写入 `audit/meta_page_button_audit_runtime.csv`，包含页面、按钮或模块、接入功能、边界和 route_key |
| 页面能力审计 | 导出能力总清单 | 写入 `audit/meta_workflow_capability_manifest.json`，汇总 route/page/button-or-module 覆盖和全流程 artifact 存在状态 |
| 页面能力审计 | 导出页面审计包 | 写入 `audit/meta_page_button_audit_package.zip`，打包按钮/模块审计 JSON、Markdown 审计表和现有全流程整理 manifest/package |
| 页面能力审计 | 导出完整交付包 | 写入 `audit/meta_preview_delivery_package.zip`，一键生成并打包页面审计、能力总清单、检索、文献、筛选、全文、提取、质量、统计、图表、PRISMA 和报告交付包 |
| 页面能力审计 | 导出交付校验清单 | 写入 `audit/meta_preview_integrity_manifest.json`，记录关键交付 artifact 是否存在、大小和 SHA-256 |
| 页面能力审计 | 跳转到选中页面 | 根据审计表选中行的页面名称跳转到对应 Meta route |
| 页面能力审计 | 继续：研究问题 / PICO | 跳转 `pico_workspace` |
| 无项目空状态 | 继续：研究问题 / PICO（禁用） | 项目未创建/打开前保持 disabled，引导用户先完成项目管理 |
| 研究问题与 PICO | 生成 PICO 草稿 | `PICOWorkspaceService` 生成草稿 |
| 研究问题与 PICO | 保存草稿编辑 | 保存人工编辑草稿 |
| 研究问题与 PICO | 确认研究问题 | 写入 confirmed protocol artifact |
| 研究问题与 PICO | 下一步：检索策略 | 跳转 `search_strategy` |
| 检索策略 | 生成检索策略 | `SearchStrategyBuilderService` 生成 PubMed/WOS/Embase/Cochrane/CNKI/WanFang/VIP 草稿 |
| 检索策略 | 保存当前编辑 | 保存当前数据库检索式编辑 |
| 检索策略 | 确认当前检索式 / 确认全部检索式 | 写入 reviewer confirmation |
| 检索策略 | 导出 TXT / MD / JSON | 导出检索策略 artifact |
| 检索策略 | 复制检索式 | 复制当前检索式到剪贴板 |
| 检索策略 | 复制数据库入口 | 复制当前数据库的人工检索入口 URL，包括 PubMed/WOS/Embase/Cochrane/CNKI/WanFang/VIP |
| 检索策略 | 导出检索执行清单 | 写入 `protocol/search_strategy_v2/search_execution_manifest.json`，记录 PubMed testing 执行路径和 WOS/Embase/Cochrane/CNKI/WanFang/VIP 人工检索入口 |
| 检索策略 | 导出检索策略包 | 写入 `exports/search_strategy_package.zip`，打包检索策略草稿、确认记录、TXT/MD/JSON 和执行清单 |
| 检索策略 | 执行 PubMed testing-level 检索 | `PubMedSearchService` 执行 reviewer-confirmed PubMed 查询 |
| 检索策略 | 全选 / 取消全选 / 选择加入文献库 / 忽略本批次 | 管理 PubMed candidates handoff 到文献库 |
| 文献库与导入 | 导入选中文献 | 将已选择 candidates 写入 normalized literature library |
| 文献库与导入 | 选择文件导入 | `MultiSourceLiteratureImportService` 导入本地 PubMed XML/MEDLINE、WOS text/tab、RIS、Embase RIS、Cochrane RIS、CNKI 风格导出 |
| 文献库与导入 | 导出文献库摘要 | 导出当前文献库摘要 |
| 文献库与导入 | 复制 PubMed 链接 / 复制 DOI 链接 | 根据当前文献 PMID/DOI 生成标准 PubMed 或 DOI URL 并复制到剪贴板 |
| 文献库与导入 | 复制引用信息 | 基于当前 normalized literature record 复制标题、作者、年份、期刊、DOI、PMID 和来源 |
| 文献库与导入 | 导出引用整理清单 | 写入 `literature/literature_citation_manifest.json`，汇总全部文献 citation text、DOI/PubMed 链接和缺失字段 |
| 文献库与导入 | 导出 RIS | 写入 `literature/literature_library_export.ris`，供 EndNote/Zotero 等引用工具人工导入 |
| 文献库与导入 | 导出 BibTeX | 写入 `literature/literature_library_export.bib`，供 BibTeX/Zotero 等引用工具人工导入 |
| 文献库与导入 | 导出 CSL-JSON | 写入 `literature/literature_library_export.csl.json`，供 Zotero/Pandoc citeproc 等工作流人工导入 |
| 文献库与导入 | 导出文献台账 CSV | 写入 `literature/literature_register.csv`，包含题名、作者、年份、期刊、DOI/PMID、链接和筛选/去重状态 |
| 文献库与导入 | 导出文献整理包 | 写入 `exports/literature_organization_package.zip`，打包文献库、引用清单、RIS/BibTeX/CSL-JSON、检索/筛选/全文整理 manifest |
| 文献库与导入 | 生成全部文献整理产物 | 写入 `literature/literature_capability_artifact_index.json`，并生成检索、引用、筛选、全文和文献整理包 artifact |
| 文献库与导入 | 导出获取/整理清单 | 写入 `literature/literature_acquisition_organization_manifest.json`，汇总 PubMed preview、本地导入、文献库、去重、筛选和全文组织状态 |
| 文献库与导入 | 保存备注 | 写入页面备注 / 操作反馈 |
| 文献库与导入 | 下一步：去重与筛选 | 跳转 `screening_review` |
| 去重与筛选 | 生成重复组 | `DedupReviewV2Service` 生成重复候选组 |
| 去重与筛选 | 保存人工决定 | 保存 keep/merge/master/not-duplicate/skip 决策 |
| 去重与筛选 | 生成去重后文献库 | 导出 deduplicated literature，不破坏原始文献库 |
| 去重与筛选 | 创建标题摘要筛选队列 | 建立 reviewer screening queue |
| 去重与筛选 | 导出筛选整理清单 | 写入 `screening/screening_organization_manifest.json`，汇总重复组、去重决定、去重后文献、筛选队列、筛选决定和全文需求 |
| 去重与筛选 | 纳入 / 排除 / 不确定 / 需要全文 / 保存并下一篇 / 保存筛选决定 | `TitleAbstractScreeningV2Service` 保存人工筛选决策 |
| 去重与筛选 | 下一步：排除标准 | 跳转 `exclusion_criteria` |
| 排除标准 | 保存排除标准草稿 / 确认排除标准 | `ExclusionCriteriaLibraryService` 保存或确认项目排除标准 |
| 排除标准 | 新增理由 | 增加自定义排除理由 |
| 排除标准 | 下一步：标题摘要筛选 | 跳转 `title_abstract_screening` |
| 标题摘要筛选 | 生成筛选队列 | `TitleAbstractScreeningV2Service` 创建 reviewer queue |
| 标题摘要筛选 | 保存人工决定 | 保存标题摘要筛选人工决定 |
| 标题摘要筛选 | 导出筛选决定 CSV | 写入 `screening/title_abstract_screening_decisions.csv`，导出现有筛选队列、人工决定、排除理由和备注 |
| 标题摘要筛选 | 下一步：全文管理 | 跳转 `fulltext_management` |
| 全文管理 | 建立全文队列 | `FullTextManagementService` 从筛选结果创建全文 registry |
| 全文管理 | 上传全文 | 绑定本地 PDF 文件 |
| 全文管理 | OCR 识别 PDF | `FullTextParsingService` 执行 testing-level 本地解析/OCR 路径 |
| 全文管理 | 标记无法获取 / 全文确认 / 保存全文状态 | 更新全文管理状态与 audit |
| 全文管理 | 保存全文筛选 | `FullTextEligibilityService` 保存全文筛选状态和排除原因 |
| 全文管理 | 复制获取链接 | 根据选中文献 DOI/PMID/PMCID 复制 DOI、PubMed、PMC 获取链接集合 |
| 全文管理 | 导出全文获取 CSV | 写入 `fulltext/fulltext_retrieval_register.csv`，导出 DOI/PubMed/PMC 链接、本地 PDF 路径和人工获取状态台账 |
| 全文管理 | 导出全文获取清单 | 写入 `fulltext/fulltext_retrieval_manifest.json`，汇总 DOI/PubMed/PMC 链接、本地 PDF 路径和人工获取状态 |
| 全文管理 | 导出全文获取包 | 写入 `exports/fulltext_retrieval_package.zip`，打包全文获取清单、CSV、全文管理/解析 manifest 和缺失全文报告 |
| 全文管理 | 下一步：数据提取 | 跳转 `manual_extraction` |
| 数据提取 | 新建 study unit / 新建提取行 | `ManualExtractionEffectRowService` 建立人工提取结构 |
| 数据提取 | 保存结构化草稿 / 完成本行提取 / 用户确认 / 标记缺失数据 | 保存或确认结构化提取记录 |
| 数据提取 | 导出空模板 CSV / 导出当前 CSV / 导入 CSV 草稿 | CSV 模板、当前表和草稿导入路径 |
| 数据提取 | 导出提取整理清单 | 写入 `extraction/extraction_organization_manifest.json`，汇总 study unit、effect row、结构化提取、校验和 AI 建议状态 |
| 数据提取 | 导出提取整理包 | 写入 `exports/extraction_organization_package.zip`，打包提取 JSON、模板/当前 CSV、校验报告和 AI 建议记录 |
| 数据提取 | 下一步：AI 辅助提取 | 跳转 `ai_extraction` |
| AI 辅助提取 | 接受建议 / 拒绝建议 / 写入人工草稿 | `AIAssistedExtractionQueueService` 审核建议，accepted 后仅写入人工草稿 |
| AI 辅助提取 | 下一步：质量评价 | 跳转 `quality_assessment` |
| 质量评价 | 保存评分草稿 | `QualityAssessmentService` 保存人工评分草稿 |
| 质量评价 | 已确认 | 用户确认质量评价记录 |
| 质量评价 | 导出 CSV | 导出质量评价 CSV |
| 质量评价 | 导出 JSON | 写入 `quality/quality_assessment_v1_export.json`，导出质量评价 v1 记录 |
| 质量评价 | 导出质量评价包 | 写入 `exports/quality_assessment_package.zip`，打包质量评价 JSON/CSV、summary、alias 和组织清单 |
| 质量评价 | 下一步：分析计划 | 跳转 `analysis_plan` |
| 分析计划 | 生成分析计划草稿 | `AnalysisPlanService` 基于 protocol、提取、质量记录生成计划草稿 |
| 分析计划 | 保存计划编辑 | 保存人工编辑分析计划 |
| 分析计划 | 确认分析计划 | 写入 confirmed analysis plan |
| 分析计划 | 刷新效应量标准化预检查 | 刷新并展示 effect normalization precheck 状态 |
| 分析计划 | 运行 pairwise executor | `PairwiseMetaExecutorService` 基于 confirmed analysis plan 运行 testing-level pairwise 计算 |
| 分析计划 | 接受进入报告草稿 / 标记需要修订 / 不纳入报告 / 申请报告就绪 | `StatisticalResultReviewService` 记录统计结果审核状态和报告就绪申请 |
| 分析计划 | 下一步：统计分析 | 跳转 `statistics_analysis` |
| 统计分析 | 运行统计分析 | `MetaStatisticsEngineService` 从 confirmed analysis plan 运行 testing-level 统计 |
| 统计分析 | 导出统计结果清单 | 写入 `analysis/statistics_results_manifest.json`，汇总 confirmed plan、analysis manifest、run 和 result 文件 |
| 统计分析 | 导出统计结果包 | 写入 `exports/statistics_results_package.zip`，打包分析计划、analysis manifest、统计 run/result 和审核记录 |
| 统计分析 | 下一步：图表结果 | 跳转 `figure_results` |
| 图表结果 | 下一步：PRISMA | 跳转 `prisma`；图表表格读取现有 figure/result artifacts |
| 图表结果 | 导出图表结果清单 | 写入 `figures/figure_results_manifest.json`，汇总 figure artifact 和统计 result 文件 |
| 图表结果 | 导出图表结果包 | 写入 `exports/figure_results_package.zip`，打包 figures 目录和统计 result 文件 |
| PRISMA | 生成 PRISMA summary | `PRISMAService` 汇总真实导入、去重、筛选、全文记录 |
| PRISMA | 导出 Markdown | 导出 PRISMA Markdown |
| PRISMA | 导出 PRISMA 报告包 | 写入 `exports/prisma_reporting_package.zip`，生成并打包 PRISMA summary JSON/Markdown、简化 flow Markdown/SVG 和 manifest |
| PRISMA | 下一步：报告导出 | 跳转 `report_export` |
| 报告导出 | 生成报告草稿 | `FormalMarkdownReportBuilder` 生成 Markdown 草稿 |
| 报告导出 | 打开报告位置 | 复制项目 `reports` 目录绝对路径到剪贴板并提示位置 |
| 报告导出 | 导出 HTML / 导出 DOCX | `PublicationExportService` 导出 testing report |
| 报告导出 | 导出报告交付包 | 写入 `exports/formal_report_package.zip`，打包 Markdown、HTML、DOCX、report manifest、PRISMA artifact 和交付清单 |
| 报告导出 | 下一步：复现包 | 跳转 `reproducibility_package` |
| 复现包 | 导出可复现项目包 | `PublicationExportService` 导出 reproducibility package ZIP |
| 所有页面 | 开发者诊断 | 展开/折叠 artifact、manifest、debug 路径 |

## 模块级接入审计补充

| 页面 | 模块 | 接入功能 / 数据源 |
| --- | --- | --- |
| 项目首页 | 项目管理表单 | 项目名称、研究主题、保存位置、最终项目路径预览、本地项目创建/打开流程 |
| 项目首页 | 流程进度摘要 | 读取 workflow integration state，展示页面 artifact 数量、状态、警告和下一步 |
| 页面能力审计 | 页面/按钮/模块审计表 | 展示 runtime 审计 rows，包含页面、按钮或模块、接入功能、边界和 route_key |
| 研究问题与 PICO | 研究问题输入与 PICO/PICOS/PECO 草稿字段 | 接入 protocol draft、confirmed protocol 和 UI draft 字段 |
| 研究问题与 PICO | 已确认研究问题卡片 | 读取 `protocol/pico_workspace_confirmed.json` |
| 检索策略 | 数据库列表与检索式编辑器 | 接入 search strategy drafts/confirmed，按数据库展示草稿、确认检索式和人工入口 |
| 检索策略 | PubMed 候选文献表与详情 | 读取 PubMed handoff preview/report，展示 PMID、题名、摘要、期刊和处理状态 |
| 文献库与导入 | PubMed 候选列表 | 读取 PubMed handoff preview，支持候选批次导入或忽略 |
| 文献库与导入 | 文献库表格与详情 | 读取 `literature/literature_records.json`、`import_batches.json` 和 `library_manifest.json` |
| 文献库与导入 | 文献备注区 | 写入本地 literature notes，备注不改变筛选决策 |
| 去重与筛选 | 重复组列表与候选详情 | 读取 duplicate groups、review queue 和人工去重决策 |
| 去重与筛选 | 标题摘要快速筛选区 | 读取/写入 screening queue 和人工 decision |
| 排除标准 | 排除标准库与自定义理由 | 接入 exclusion criteria library、selection 和 confirmed artifact |
| 标题摘要筛选 | 筛选队列列表与决策表单 | 接入 title/abstract queue、decisions、排除理由和备注 |
| 全文管理 | 全文 registry 列表与状态编辑区 | 接入 fulltext management registry、fulltext registry、parse manifest 和 eligibility records |
| 全文管理 | 全文获取链接集合 | 根据 DOI/PMID/PMCID 生成 DOI、PubMed、PMC 链接用于人工获取 |
| 数据提取 | 文献、study unit、effect row 三列表 | 读取可提取文献、study units 和 effect rows，选择后填充结构化表单 |
| 数据提取 | 结构化提取表单 | 接入研究基本信息、PICO/PECO、效应量和诊断字段，写入 manual extraction draft |
| AI 辅助提取 | AI suggestion 队列 | 读取 extraction AI suggestion queue/application，展示 confidence、状态和建议 ID |
| 质量评价 | 质量评价研究列表与评分表单 | 接入 quality records、summary 和 tool registry，展示 domain rating、overall rating 和备注 |
| 分析计划 | 分析计划编辑表单 | 接入 draft/confirmed analysis plan、效应量类型、模型偏好、亚组/敏感性/发表偏倚计划 |
| 分析计划 | 统计前置审核区 | 接入 effect normalization precheck、pairwise executor 和 statistical result review |
| 统计分析 | 统计结果 JSON 预览 | 读取 latest analysis result JSON、run_count 和 testing-level 结果 |
| 图表结果 | figure artifact 表 | 读取 `figures/figure_artifacts.json` 和 `analysis/results` |
| PRISMA | PRISMA summary 卡片 | 读取 `reports/prisma_flow_summary.json` 并展示 identified、duplicates、screened、excluded、included |
| 报告导出 | 报告预览 | 读取 `reports/formal_meta_report.md` 并展示 Markdown 前 12000 字符 |
| 复现包 | 复现包列表 | 读取 `exports/reproducibility_package_*.zip` |

## 精确按钮标签补充

| 页面 | 按钮 | 接入功能 / 指向 |
| --- | --- | --- |
| 项目首页 | 新建 Meta 项目 | 切换到项目创建表单 |
| 项目首页 | 打开已有项目 | 打开本地目录选择器并校验 Meta 项目 |
| 项目首页 | 选择保存位置 | 选择项目保存目录 |
| 项目首页 | 创建项目 | 创建项目目录、manifest、config 和基础结构 |
| 项目首页 | 选择已有项目文件夹 | 打开并校验已有 Meta 项目目录 |
| 项目首页 | 返回首页 / 返回模块首页 | 返回 Meta 模块首页或上一级入口 |
| 页面能力审计 | 导出审计记录 JSON | 写入 `audit/meta_page_button_audit_runtime.json` |
| 研究问题与 PICO | 生成 PICO 草稿 / 保存草稿编辑 / 确认研究问题 | 生成、保存并确认 PICO/PICOS/PECO protocol |
| 检索策略 | 保存当前编辑 / 确认当前检索式 / 确认全部检索式 | 保存或确认当前/全部数据库检索式 |
| 检索策略 | 导出 TXT / MD / JSON / 复制检索式 | 导出本地检索策略 artifact 或复制当前检索式 |
| 检索策略 | 全选 / 取消全选 | 选择或清空 PubMed candidate table 当前行选择 |
| 检索策略 | 选择加入文献库 | 将选中的 PubMed candidates 写入文献库 handoff |
| 检索策略 | 忽略本批次 | 忽略当前 PubMed candidate 批次 |
| 文献库与导入 | 导出文献库摘要 / 保存备注 | 导出当前文献库摘要或保存页面备注 |
| 文献库与导入 | 全选 / 取消全选 | 选择或清空候选文献列表当前选择 |
| 文献库与导入 | 忽略本批次 | 清空/忽略当前候选批次选择，不写入文献库 |
| 排除标准 | 保存排除标准草稿 / 确认排除标准 / 新增理由 | 管理项目排除标准库和自定义理由 |
| 标题摘要筛选 | 生成筛选队列 / 保存人工决定 | 创建 reviewer queue 或保存当前筛选人工决定 |
| 去重与筛选 | 纳入 / 排除 / 不确定 / 需要全文 | 快速写入当前标题摘要筛选记录的人工决策 |
| 去重与筛选 | 保存并下一篇 | 保存当前筛选决定并推进到下一条未筛选记录 |
| 去重与筛选 | 保存筛选决定 | 保存当前记录的标题摘要筛选人工决定 |
| 全文管理 | 上传全文 / OCR 识别 PDF | 绑定本地 PDF 或执行 testing-level OCR/解析 |
| 全文管理 | 标记无法获取 / 全文确认 / 保存全文状态 / 保存全文筛选 | 保存全文获取、可用性和 eligibility 状态 |
| 数据提取 | 新建 study unit / 新建提取行 | 创建人工提取结构 |
| 数据提取 | 保存结构化草稿 / 完成本行提取 / 用户确认 / 标记缺失数据 | 保存、完成、确认或标记当前提取行 |
| 数据提取 | 导出空模板 CSV / 导出当前 CSV / 导入 CSV 草稿 | 导出模板、当前提取表或导入 CSV draft |
| AI 辅助提取 | 接受建议 / 拒绝建议 / 写入人工草稿 | 审核 AI suggestion 并可写入人工 draft |
| 质量评价 | 已确认 | 将当前质量评价记录标记为用户确认 |
| 质量评价 | 导出 CSV | 写入 `exports/quality_assessment_v1.csv` |
| 分析计划 | 生成分析计划草稿 / 保存计划编辑 / 确认分析计划 | 生成、编辑并确认 analysis plan |
| 分析计划 | 接受进入报告草稿 / 标记需要修订 / 不纳入报告 / 申请报告就绪 | 记录统计结果审核状态和报告就绪 gate |
| PRISMA | 生成 PRISMA summary / 导出 Markdown | 保存 PRISMA summary JSON 或 Markdown |
| 报告导出 | 生成报告草稿 / 导出 HTML / 导出 DOCX | 生成 Markdown 草稿并导出 testing report |

## 仍需保持的边界

- PubMed 可执行 testing-level 检索；WOS、Embase、Cochrane、CNKI、WanFang、VIP 当前仍是检索式生成/导出，不是在线抓取客户端。
- PDF/OCR、统计、报告、图表、AI 建议均为内部测试能力，不自动生成最终医学结论。
- 页面能力已经接入本地按钮和路由，但完整 production 级验收仍需要运行项目样例、统一测试、桌面 walkthrough 和包装验证。
