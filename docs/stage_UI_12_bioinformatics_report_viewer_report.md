# UI-12 生信报告查看页报告

## 本阶段做了什么
- 新增 `BioinformaticsReportViewerWidget`。
- 新增 `app/bioinformatics/reports/project_report_builder.py`。
- 包装现有 `reporting.bioinformatics_standard_report.generate_standard_report()` 生成项目级 Markdown 报告。

## 修改文件
- `app/bioinformatics/reports/project_report_builder.py`
- `app/bioinformatics/workflow_pages.py`
- `app/bioinformatics/workspace.py`
- `tests/bioinformatics/test_workflow_adapters.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

## artifact 契约
- Markdown：`reports/project_analysis_report.md`
- Manifest：`reports/project_report_manifest.json`
- Builder log：`logs/reports/project_report_builder_report.json`

## 当前边界
- 不生成正式 PDF。
- DOCX/HTML 只作为 testing placeholder。
- 不运行分析，不伪造报告内容。

## 测试结果
- 已覆盖无报告空状态、Markdown 生成/读取、report builder 调用和 PDF placeholder 文案。
- 全量回归：`QT_QPA_PLATFORM=offscreen python3 -m pytest`，92 passed。
- 入口 smoke：`QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`，通过。
