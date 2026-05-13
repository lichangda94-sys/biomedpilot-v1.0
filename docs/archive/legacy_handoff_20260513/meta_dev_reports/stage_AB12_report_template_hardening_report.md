# Stage AB12 - Report Template Hardening

## 本阶段目标

把 formal Markdown / HTML / DOCX testing report 加固为 internal beta 报告草稿：补充 protocol、study selection、PRISMA、quality、statistical methods、results、figures、tables、applicability warnings、limitations 和 reproducibility 章节，同时保持正式 PDF 未实现。

## Continuity Audit

- 当前分支：`codex/biomedpilot-root`
- 起始 HEAD：`ec7d041 feat(meta): add simplified prisma flow`
- 工作区状态：仅存在既有未跟踪 `test_inputs/`，本阶段未修改或提交该目录。
- 审计正式项目模块：
  - `app/meta_analysis/services/formal_report_service.py`
  - `app/meta_analysis/services/publication_export_service.py`
  - `app/meta_analysis/services/report_manifest_service.py`
  - `app/meta_analysis/pages/reporting_page.py`
  - `tests/meta_analysis/test_publication_export_reproducibility.py`
  - `tests/meta_analysis/test_prisma_formal_report_mvp.py`
  - `tests/meta_analysis/test_stage_t_report_manifest_consistency.py`
- 已有能力：formal Markdown report、HTML/DOCX testing export、PDF placeholder、report manifest、supplementary exports、figure package、snapshot、reproducibility package。

## Legacy Capability Audit

- 检查 legacy 目录中 report template / PDF / Word 相关内容。
- legacy 主要是 demo 或 placeholder，且不接入当前 manifest / report_manifest / project contract。
- 本阶段未迁移 legacy 代码；正式项目已有轻量 DOCX/HTML exporter 和 PDF placeholder，更适合直接增强。

## 本阶段新增行为

- formal Markdown report 标题更新为 internal beta report draft。
- 新增或强化报告章节：
  - Title
  - Protocol summary
  - Search and import summary
  - Study selection
  - PRISMA summary
  - Full-text screening summary
  - Included studies summary
  - Extraction summary
  - Quality assessment
  - Statistical methods
  - Analysis summary
  - Advanced method summary
  - Figures
  - Tables
  - Applicability warnings
  - Reproducibility notes
  - Known limitations
- `_artifact_summary()` 纳入：
  - review protocol
  - search strategy preview
  - criteria summary
  - analysis plan
  - applicability warnings
  - simplified PRISMA SVG
- Report manifest 增加 section：
  - `protocol`
  - `applicability`
- HTML/DOCX 继续从 Markdown 转换，因此章节内容保持一致。
- PDF 仍为 placeholder，并继续输出 `pdf_export_not_implemented`。

## Data Center / Task Center / Audit / Manifest / Lineage 影响

- Data Center / Task Center 未新增类型，继续复用：
  - `formal_meta_report`
  - `formal_html_report`
  - `formal_word_report`
  - `formal_pdf_report` placeholder
  - `formal_report_export`
  - `html_report_export`
  - `word_report_export`
  - `pdf_report_export` placeholder
- Report manifest 新增/强化 section-level source references。
- Manifest / lineage 不改变主链格式。

## 测试

新增：

- `tests/meta_analysis/test_stage_ab12_report_template_hardening.py`

覆盖：

- Markdown report 包含 internal beta 章节；
- Developer Preview / testing disclaimer 保留；
- report_manifest 包含 protocol、analysis、applicability、PRISMA sources；
- HTML 和 DOCX testing export 包含同一批关键章节；
- PDF 策略仍为 placeholder，不生成正式 PDF。

## 当前限制

- 正式 PDF 未实现。
- DOCX 是轻量 testing export，不是 journal-ready Word 模板。
- Report 内容来源仍依赖本地 artifacts；缺失 artifact 时报告继续生成并标记 missing。
- PRISMA SVG 是简化 testing 图，不是正式 PRISMA 2020。

## 下一阶段建议

进入 AB13：Internal Beta Sample Project Pack。建议基于既有 examples / fixtures 组织治疗效果和 biomarker/prevalence/correlation 样例，提供 expected counts、walkthrough 和 known limitations，不提交大型生成输出。
