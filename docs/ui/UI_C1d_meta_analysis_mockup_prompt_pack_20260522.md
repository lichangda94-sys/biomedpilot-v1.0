# UI-C1d Meta Analysis High-Fidelity Mockup Prompt Pack

## 1. Shared Visual Direction

Use a desktop PySide application style consistent with BioMedPilot / Firefly:

- light workspace background
- left module navigation
- top workflow stepper
- rounded cards with 6-8 px radius
- status chips for Developer Preview / testing / planned / shell-only / blocked
- dense tables with clear row states
- right-side review/gate panels where appropriate
- disabled buttons must visibly remain disabled with reason labels
- Chinese primary UI text with English scientific terms where stable

Do not use marketing hero composition. These are real operation mockups for a technical research workflow.

Global must-not-claim rules:

- no production systematic review claim
- no publication-ready claim
- no clinical-grade or regulatory-grade claim
- no Network Meta active capability
- no Chinese database direct retrieval
- no Chinese PDF extraction
- no AI automatic conclusion
- no fake forest plot
- no fake pooled effect
- no report-ready package
- no active export

## Prompt A: Meta Project Home + Workflow Overview

Create a high-fidelity desktop PySide mockup for BioMedPilot Meta Analysis Project Home.

Page goal:

- Show the Meta project entry and workflow overview.
- Make Developer Preview / testing status visible.
- Show workflow progress without implying production readiness.

Layout:

- Left sidebar with app modules: 工作台, 生信分析, Meta 分析, 实验工具, 设置中心.
- Main header: `Meta 分析 / Meta Analysis`.
- Status chip: `Developer Preview / 本地测试版`.
- Top workflow overview stepper:
  1. 项目首页
  2. 研究问题与类型
  3. 检索策略
  4. 文献导入与去重
  5. 文献筛选
  6. 全文与提取
  7. 质量评价
  8. 统计分析
  9. 结果与报告
  10. 报告导出
- Main area: three cards:
  - Project Summary
  - Workflow Readiness
  - Gate Summary
- Bottom: recent activity table with mock rows and empty-state style if no project.

Example data:

- Project title: `Thyroid cancer and adiponectin`
- Meta type candidate: `prognostic_factor_meta`
- Current state: `project_open / testing`
- Gate blockers: `research question not confirmed`, `no imported references`, `no formal result`

Buttons:

- `打开项目` allowed as shell action.
- `创建项目草稿` allowed as shell action.
- `开始检索` disabled until research question/type confirmed.
- `生成报告` disabled.
- `导出` disabled.

Must not claim:

- Systematic review complete.
- Report-ready.
- Publication-grade evidence.

## Prompt B: Question & Meta Type Selection + PICO / PECO Setup

Create a high-fidelity mockup for the Meta Analysis research question and Meta type selection page.

Page goal:

- Let the user define a research question and select one active Meta type.
- Make type selection a workflow-control item, not a decorative tag.

Layout:

- Header: `研究问题与 Meta 类型`.
- Left panel: research question input with Chinese and English draft fields.
- Middle panel: PICO / PECO / PICOS structured fields.
- Right panel: selected type summary, downstream effects, and blockers.
- Below: 10 active type cards grouped by category.

Active type cards:

- 二分类结局 Meta
- 连续结局 Meta
- 生存结局 Meta
- 患病率 / 发生率 Meta
- 诊断准确性 Meta
- 暴露-疾病风险 Meta
- 生物标志物表达差异 Meta
- 相关性 Meta
- 预后因素 Meta
- 剂量反应 Meta

Network Meta:

- Show a planned-only callout: `Network Meta: planned only / not enabled`.
- The planned button must be disabled.

Example data:

- Chinese question: `甲状腺癌患者中 adiponectin 是否与预后相关？`
- English draft: `Is adiponectin associated with prognosis in thyroid cancer?`
- Population: adults with thyroid cancer
- Exposure: adiponectin expression or circulating level
- Outcome: overall survival / recurrence

Status chips:

- `testing`
- `review required`
- `schema shell`

Must not claim:

- AI finalizes the question.
- Network Meta is available.
- Type selection can be skipped without downstream impact.

## Prompt C: Search Strategy Builder

Create a high-fidelity mockup for the Meta Analysis search strategy builder.

Page goal:

- Generate and review English search strategy drafts from reviewer-provided terms.
- Keep search execution gated and reviewer-confirmed.

Layout:

- Header: `检索策略 / Search Strategy`.
- Top stepper highlights Search Strategy.
- Left panel: term groups for Population, Exposure/Marker, Outcome, Study design.
- Center panel: query draft editor with tabs:
  - PubMed draft
  - Web of Science draft
  - Embase draft
  - Cochrane draft
- Right panel: review checklist and boundary notices.
- Bottom table: query version history / reviewer notes.

Example PubMed query:

```text
("thyroid cancer"[Title/Abstract] OR "thyroid carcinoma"[Title/Abstract])
AND
("adiponectin"[Title/Abstract] OR "ADIPOQ"[Title/Abstract])
AND
("prognosis"[Title/Abstract] OR "survival"[Title/Abstract])
```

Buttons:

- `复制检索式` allowed.
- `保存草稿` disabled or adapter-needed unless storage gate exists.
- `执行 PubMed 检索` disabled/gated in this mockup.
- `执行中文数据库检索` must not appear.

Boundary copy:

- `中文输入可辅助生成英文检索式；当前不直接检索中文数据库。`
- `AI suggestion 仅提供检索词建议，需人工确认。`

Must not claim:

- CNKI/WanFang/VIP direct retrieval.
- automatic import.
- final search strategy.

## Prompt D: Import / Reference Management + Deduplication

Create a high-fidelity mockup for Meta literature import and reference management with deduplication review.

Page goal:

- Show reference intake and dedup review without performing active imports or automatic merges.

Layout:

- Header: `文献导入与去重`.
- Left panel: import source cards:
  - PubMed/NBIB
  - RIS / EndNote / Zotero
  - CSV
  - Manual citation
- Center panel: reference table with title, year, source, DOI/PMID, screening status, dedup status.
- Right panel: duplicate group review with risk level, merge preview, reviewer decision controls.
- Bottom: provenance / import batch summary.

Example rows:

- REF-001, Serum adiponectin and clinicopathological features in thyroid carcinoma, 2018, PubMed mock.
- REF-002, ADIPOQ expression and survival outcomes in differentiated thyroid cancer, 2020, RIS mock.
- REF-003, Adiponectin signaling in thyroid neoplasm progression, 2021, CSV mock.

Buttons:

- `选择文件` disabled or adapter-needed.
- `预览导入格式` allowed as mockup shell.
- `确认导入` disabled.
- `合并重复项` disabled until reviewer decision and backend gate.
- `进入筛选` disabled until references are reviewer-confirmed.

Must not claim:

- automatic dedup merge.
- automatic import to screening.
- Chinese database online import.
- PRISMA counts updated.

## Prompt E: Screening Workspace

Create a high-fidelity mockup for Meta title/abstract screening.

Page goal:

- Support reviewer screening decisions while keeping AI suggestions advisory.

Layout:

- Header: `文献筛选 / Screening`.
- Left column: reference queue with status chips: not_started, include_draft, exclude_draft, uncertain.
- Center reading pane: title, abstract, keywords, source metadata.
- Right panel:
  - reviewer decision controls
  - exclusion reason selector
  - AI suggestion box labelled advisory only
  - next required action
- Bottom: screening progress table and blockers.

Example data:

- REF-001 likely include suggestion, confidence 0.72.
- REF-002 needs review.
- REF-004 likely exclude suggestion due to wrong endpoint.

Buttons:

- `标记纳入草稿` allowed as draft UI.
- `标记排除草稿` allowed as draft UI.
- `应用 AI 建议` disabled or requires explicit reviewer confirmation.
- `完成筛选阶段` disabled until all records reviewed.

Must not claim:

- AI made final decision.
- final PRISMA counts.
- multi-reviewer adjudication complete.

## Prompt F: Extraction + Risk of Bias

Create a high-fidelity mockup combining Full-text / Extraction with Risk of Bias planning.

Page goal:

- Show full-text management and type-specific extraction form structure.
- Show risk-of-bias planning and blockers.

Layout:

- Header: `全文与提取 / 质量评价`.
- Top tab row must exactly include:
  - 全文管理
  - 提取表设计
  - 提取完成核查
  - 历史记录
- Left panel: full-text status table with PDF/local link status.
- Center panel: type-specific extraction form structure for `Prognostic factor Meta`.
- Right panel: Risk of Bias tool suggestion and domain table.

Extraction fields:

- study ID
- first author
- year
- population
- marker name
- effect measure
- effect value
- CI lower / upper
- adjusted model
- outcome name

Risk of Bias:

- Newcastle-Ottawa Scale suggested.
- ROBINS-I optional suggestion.
- domains incomplete.

Buttons:

- `确认本次提取` means advance to extraction stage; disabled until fields reviewed.
- `保存提取记录` disabled / adapter-needed.
- `完成质量评价` disabled until reviewer inputs exist.

Must not claim:

- automatic PDF extraction.
- Chinese PDF OCR extraction.
- automatic risk-of-bias judgement.
- generic drag-drop extraction field library.
- final extraction saved.

## Prompt G: Result Review + Report-ready Gate

Create a high-fidelity mockup for Meta result review and report-ready gate.

Page goal:

- Show result/report gate state without fake forest plot, fake pooled effect, or report-ready package.

Layout:

- Header: `结果审查 / 报告就绪 Gate`.
- Left panel: Result Review state summary:
  - no formal pooled effect
  - testing summary only
  - missing confirmed analysis plan
  - missing completed extraction / quality assessment
- Center panel: Forest Plot / Table Preview boundary:
  - empty chart frame
  - required inputs list
  - disabled preview controls
  - no data marks or fake chart lines
- Right panel: Report-ready Gate:
  - draft report state
  - blockers
  - reviewer acknowledgement
  - export disabled reasons
- Bottom: disabled export format buttons:
  - DOCX disabled
  - HTML disabled
  - PDF disabled / future
  - CSV disabled
  - XLSX disabled
  - ZIP disabled

Gate state:

- `result.semantic.testing_summary_only`
- `report.status.draft`
- `exportGate=disabled_empty_result`
- `report_ready_package_allowed=false`

Must not claim:

- formal pooled effect.
- generated forest plot.
- report-ready package.
- DOCX/HTML/PDF export.
- publication-grade systematic review.

## 2. Batch Grouping

Recommended mockup generation batches:

| batch | mockups | purpose |
|---|---|---|
| 1 | A, B, C | establish workflow, type selection, search strategy direction |
| 2 | D, E | validate literature intake and screening interaction patterns |
| 3 | F, G | validate extraction, risk-of-bias, result/report/export boundaries |

If only six images can be produced, merge Prompt A and B only after confirming that the 10 active type cards remain readable. Do not remove type selection from the first batch.

## 3. Acceptance Checklist

Each mockup should pass:

- Developer Preview / testing status visible.
- No production systematic review language.
- No Network Meta active state.
- No Chinese database direct retrieval.
- No Chinese PDF extraction.
- AI suggestion is advisory and visibly subordinate to reviewer action.
- Reviewer decision remains authoritative.
- No fake forest plot, fake pooled effect, or fake heterogeneity.
- Report-ready is draft/internal only.
- Export buttons are disabled or gated.
- Chinese UI copy remains user-friendly.
- Tables and panels are dense enough for desktop scientific workflow use.
