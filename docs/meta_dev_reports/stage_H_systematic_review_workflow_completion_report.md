# Stage H: Systematic Review Workflow Completion Report

## 本阶段目标

补齐系统综述真实流程中的 Full-text Management、Full-text Screening、Exclusion Reasons 和基础 Quality Assessment，使 Meta Analysis 更接近正式论文工作流。

本阶段不做 OCR、PDF 自动表格提取、AI full-text extraction、双人冲突仲裁完整系统、Word/PDF 报告或高级统计。

## Full-text 新增能力

- 新增 `FullTextFile` 数据模型。
- 支持 `attach_fulltext(project_dir, record_id, source_file_path)`。
- PDF 会复制到 `project_dir/fulltext/` 内。
- 支持 fulltext registry 保存/读取。
- 支持按 record_id 查询 full-text。
- 支持 full-text availability 更新。
- 新增 `FullTextScreeningDecision`。
- 支持 include / exclude / maybe 全文筛选决策。
- 支持 full-text exclusion report CSV 导出。

## Exclusion Reason 字典

- wrong population
- wrong intervention or exposure
- wrong comparator
- wrong outcome
- wrong study design
- duplicate cohort
- insufficient data
- no full text
- review or editorial
- animal or in vitro study
- conference abstract only
- language restriction
- other

## Quality Tool Registry 支持范围

- NOS
- QUADAS-2
- RoB2 simplified
- JBI checklist placeholder
- GRADE placeholder

## 新增输出路径

- `project_dir/fulltext/fulltext_registry.json`
- `project_dir/fulltext/fulltext_screening_decisions.json`
- `project_dir/reports/full_text_exclusion_report.csv`
- `project_dir/quality/quality_assessments.json`
- `project_dir/exports/quality_assessment_table.csv`

## Reporting 集成情况

- Formal Markdown report 增加 full-text registry、full-text screening decisions、full-text exclusion report 引用。
- Formal Markdown report 增加 quality assessments 和 quality assessment table 引用。

## Data Center / Task Center 新增类型

- Data Center:
  - `fulltext_registry`
  - `fulltext_screening_decisions`
  - `full_text_exclusion_report`
  - `quality_assessments`
  - `quality_assessment_table`
- Task Center:
  - `fulltext_attach`
  - `fulltext_screening_decision`
  - `fulltext_exclusion_export`
  - `quality_assessment_save`
  - `quality_assessment_export`

## 测试结果

已验证：

- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest tests/meta_analysis/test_systematic_review_workflow_completion.py tests/meta_analysis/test_prisma_formal_report_mvp.py -q`
  - 6 passed。
- `python -m compileall -q .`
  - 当前 shell 中 `python` 命令不存在，原样命令无法运行。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`
  - 通过。
- `pytest -q`
  - 当前 shell 中 `pytest` 命令不存在，原样命令无法运行。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`
  - 217 passed。
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`
  - 217 passed。
- `python3 -m app.main --smoke-test`
  - 通过，输出 `meta_analysis_features=7`。

## 当前限制

- 不做 OCR。
- 不做 PDF 自动表格提取。
- 不做 AI full-text extraction。
- 不做完整双人冲突仲裁。
- Quality / GRADE 仍为 testing 基础登记，不是正式证据评级系统。
- Word/PDF 报告仍未开放。

## 下一阶段建议

进入 Stage I：Publication Export & Reproducibility，开发 HTML/Word-ready report、supplementary exports、figure package、project snapshot 和 reproducibility package。
