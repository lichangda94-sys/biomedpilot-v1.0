# Stage G: PRISMA & Formal Markdown Report MVP Report

## 本阶段目标

基于 Import、Deduplication、Screening、Extraction、AnalysisResult 和 FigureArtifact，开发 PRISMA flow number collector 和 formal Markdown report builder。

Reporting 仍为 testing 状态，不生成 Word/PDF，不伪装为完整投稿级报告。

## 实际完成内容

- 新增 `PRISMAFlowSummary` 数据模型。
- 新增 `PRISMAService`。
- 新增 `FormalMarkdownReportBuilder`。
- 支持从项目目录已有 JSON artifacts 汇总 testing PRISMA 数字。
- 支持保存 PRISMA JSON 和 Markdown。
- 支持生成 `formal_meta_report.md`。
- Reporting 页面 testing UI 增加 PRISMA summary 和 formal Markdown report 入口。
- 保留旧 `ReportingService.export_preflight_report` 和旧 `meta_analysis_report` 测试摘要逻辑。

## 修改/新增文件列表

- `app/meta_analysis/models/prisma.py`
- `app/meta_analysis/pages/reporting_page.py`
- `app/meta_analysis/services/formal_report_service.py`
- `app/shared/feature_availability.py`
- `app/shared/task_center/service.py`
- `docs/meta_analysis_current_status.md`
- `docs/user_testing/feature_availability.md`
- `docs/user_testing/known_limitations.md`
- `tests/meta_analysis/test_developer_preview_stabilization.py`
- `tests/meta_analysis/test_prisma_formal_report_mvp.py`

## PRISMAFlowSummary 字段

- `records_identified`
- `records_after_deduplication`
- `records_screened`
- `records_excluded_title_abstract`
- `full_text_reports_sought`
- `full_text_reports_assessed`
- `full_text_reports_excluded`
- `full_text_exclusion_reasons`
- `studies_included`
- `reports_included`
- `data_sources`
- `notes`
- `created_at`

## Formal Report Sections

- Project summary
- Current software status
- Research question
- Search and import summary
- Deduplication summary
- Screening summary
- Full-text screening summary / limitation note
- Included studies summary
- Extraction summary
- Analysis summary
- Forest plot artifact path
- Result table artifact path
- Reproducibility notes
- Known limitations
- Missing artifact warnings

## 输出路径

- `project_dir/reports/prisma_flow_summary.json`
- `project_dir/reports/prisma_flow_summary.md`
- `project_dir/reports/formal_meta_report.md`

## 对 full-text incomplete 的处理方式

- `full_text_reports_sought` 和 `full_text_reports_assessed` 使用 included / maybe screening 决策估算。
- `notes` 明确写入 `full-text workflow incomplete`。
- Formal Markdown report 中明确标记 full-text workflow incomplete。

## Data Center / Task Center 新增类型

- Data Center:
  - `prisma_flow_summary`
  - `formal_meta_report`
- Task Center:
  - `prisma_collect`
  - `formal_report_export`

## 测试结果

已验证：

- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest tests/meta_analysis/test_prisma_formal_report_mvp.py tests/meta_analysis/test_reporting_service.py tests/meta_analysis/test_developer_preview_stabilization.py -q`
  - 14 passed。
- `python -m compileall -q .`
  - 当前 shell 中 `python` 命令不存在，原样命令无法运行。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`
  - 通过。
- `pytest -q`
  - 当前 shell 中 `pytest` 命令不存在，原样命令无法运行。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`
  - 214 passed。
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`
  - 214 passed。
- `python3 -m app.main --smoke-test`
  - 通过，输出 `meta_analysis_features=7`。

## 当前报告限制

- 不生成 Word。
- 不生成 PDF。
- 不生成 PRISMA 图片。
- 不提供 journal template。
- 不提供 GRADE summary。
- Full-text workflow 尚未完成，PRISMA full-text 数字为 testing estimate。

## 下一阶段建议

进入 Stage H：Systematic Review Workflow Completion，补齐 full-text management、full-text screening exclusion reasons 和基础 quality assessment。
