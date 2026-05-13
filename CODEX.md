# CODEX.md - Meta Analysis

## 当前工作区

路径：`/Users/changdali/Developer/biomedpilot v1.0/Meta`
分支：`dev/meta-analysis`
当前 handoff HEAD：`76f9a0e` (`refactor(meta): retire active runtime legacy bridge`)

本工作区只负责 BioMedPilot 的医学文献型 Meta Analysis 工作流。Meta 不处理 Bioinformatics 的 GEO / TCGA / GTEx / 表达矩阵数据，也不承担 ReleaseBuild、MainLine、Integration、UIShell、LabTools 或 Bioinformatics worktree 的职责。

## 当前定位

Meta 当前是 `Developer Preview / testing`。它不是生产级统计分析软件，不是临床级、监管级、投稿级或正式证据生成系统。UI、报告、handoff、测试输出和统计输出都必须保留 testing-level / draft / human-review wording。

当前 active Meta runtime 已存在，桌面 workflow、active services、active adapters、active pages 和测试级报告链路均在本 worktree 中维护。active runtime 的 legacy bridge 已退休：active adapters/services 不应再通过 `_legacy_path()`、`LEGACY_ROOT`、legacy service loader、legacy parser 或 legacy normalizer 调用 `app/meta_analysis/legacy/**`。

`app/meta_analysis/legacy/**` 只保留为历史隔离区和参考快照。不要删除、移动或重构 legacy 文件；也不要让任何新功能依赖它。

## 当前用户工作流

当前 Meta active runtime 支持 testing-level 的文献型 Meta Analysis 流程：

1. 创建或打开 Meta project。
2. PICO / PICOS / PECO 与 protocol 草稿、编辑和人工确认。
3. 检索策略草稿、确认和导出。
4. 文献导入 / 检索候选：本地 NBIB / RIS / CSV 导入，testing-level PubMed candidate preview 与 handoff。
5. 文献库诊断、来源过滤、备注和导出摘要。
6. 去重审核、人工去重决策、deduplicated set 与 screening queue 准备。
7. 标题摘要筛选：人工 include / exclude / uncertain / needs review，排除原因需要人工记录。
8. 全文处理：全文状态 / PDF attachment registry、testing-level parsing、全文资格判断。
9. 数据提取和质量评价：手工 study units、effect rows、CSV draft、测试级质量记录。
10. 分析计划与 testing-level statistical placeholders：分析计划 draft/confirmed、analysis-ready dataset、测试级统计输出。
11. 报告草稿：PRISMA summary、Markdown/HTML/DOCX testing artifacts、supplementary exports、snapshot 和 reproducibility package。

所有筛选、提取、质量评价、统计和报告结论都需要用户人工确认。AI 或规则输出只能作为 suggestion，不能自动成为 accepted evidence、confirmed decision 或 final conclusion。

## 当前限制

- WOS / Embase / Cochrane / CNKI / WanFang / VIP 在线检索不是 active fully implemented retrieval backend；除非当前代码和测试证明，否则只能描述为 draft、export-oriented、network-dependent 或 not fully implemented。
- PubMed candidate retrieval 是 testing-level preview，不能描述为完整系统综述检索。
- Screening 仍是 manual 或 assisted-only；系统不得自动正式纳入或排除文献。
- AI suggestions 只是建议，必须经用户 accept / reject / edit 后才可进入用户确认状态。
- Quality assessment tools 是 staged/testing workflow，评价维度、理由和总体判断必须由用户确认。
- Full-text parsing 不包含 OCR，也不能把 PDF 内容自动变成 confirmed evidence。
- Statistical outputs 是 testing-level foundations；除非未来接入并验证真实统计执行器，否则不得作为正式发表、投稿、临床、监管或 publication-grade 结果。
- Report artifacts 是测试草稿；不能包装成正式论文、正式 PRISMA submission 或监管归档。

## 下一步开发阶段

- M4B - Screening workspace refinement：把文献筛选做成清楚、中文友好的可操作工作台。
- M4C - Full-text management workspace：管理全文状态、PDF attachment、无法获取、待检查和确认状态，不做自动科学结论抽取。
- M5 - Extraction table and evidence-state governance：结构化提取表、PICO/PECO 字段、效应量字段和 draft/suggested/user_accepted/user_edited/confirmed/rejected 状态治理。
- M6 - Quality assessment user workflow：优先把 NOS 或 ROB2 做成可点击、可保存、可报告的人工评价工作台。
- M7 - Statistical plan confirmation：在真实统计执行前确认研究类型、效应量、模型、异质性、亚组/敏感性/发表偏倚计划。
- M8 - Report draft generation：优先生成结构化 Markdown 报告草稿，明确区分用户确认、系统建议、测试级输出、真实统计结果和未完成部分。
- M9 - Real statistical executor integration audit：审计真实统计执行器的输入、方法、假设、验证基线和安全边界，确认后再接入。

## 禁止事项

- 不要修改其他 worktree。
- 不要整分支 merge 到 MainLine 或 Integration。
- 不要从 Meta module worktree 打包 internal beta 或 release build。
- 不要 push remote。
- 不要删除、移动或依赖 `app/meta_analysis/legacy/**`。
- 不要修改 Bioinformatics、LabTools、UIShell、ReleaseBuild、MainLine、Integration、Vocabulary 或 AI Gateway，除非任务明确授权。
- 不要把 testing-level PubMed、statistics、reports、AI suggestions、full-text parsing 或 quality assessment 描述为 production-ready、clinical-ready、regulatory-ready、submission-ready 或 publication-ready。
- 不要引入 GEO / TCGA / GTEx 到 Meta。
- 不要引入 network retrieval、外部 API、模型调用、PDF 自动下载、OCR、自动筛选、自动提取、自动质量评价、自动统计结论或自动报告结论，除非有专门任务和明确人工确认边界。
- 不要在主 UI 暴露 branch、schema、manifest path、raw JSON、internal id 或 debug path；开发者诊断必须折叠显示。

## 验证

Meta worktree 默认验证：

```bash
git diff --check
python3 -m pytest tests/meta_analysis -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
```

Docs-only 任务可以按任务说明缩小验证范围，但最终报告必须写清楚实际运行命令、精确结果、跳过项和剩余风险。
