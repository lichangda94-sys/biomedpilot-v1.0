# Stage I: Publication Export & Reproducibility Report

## 本阶段目标

将 Meta Analysis 的结果输出能力从 Markdown testing report 扩展为更接近投稿和审稿材料的 testing 导出系统，包括 HTML/DOCX 报告、supplementary exports、figure package、project snapshot、reproducibility package 和基础 artifact lock。

本阶段不做 AI、网络 Meta、高级协作、云同步或生产级 PDF 报告。

## 已实现导出格式

- 保留 `project_dir/reports/formal_meta_report.md`。
- 新增 HTML testing report:
  - `project_dir/reports/formal_meta_report.html`
- 新增 DOCX testing report:
  - `project_dir/reports/formal_meta_report.docx`
  - 使用标准库生成最小 WordprocessingML，不新增外部依赖。
- 新增 PDF placeholder:
  - `project_dir/reports/formal_meta_report_pdf_placeholder.txt`
  - 不登记为可用 `formal_pdf_report` 数据资产。

## Word/PDF 是否真正可用

- Word / DOCX: testing 可用，可由本地 Markdown report draft 生成。当前包含报告文本、forest plot 路径和 result table 路径引用，但不是投稿级模板。
- PDF: 当前不可用。没有引入重型系统依赖或 PDF renderer，服务会返回明确 `pdf_export_not_implemented` warning。

## Supplementary Exports 列表

输出目录：

- `project_dir/exports/supplementary/`

当前生成：

- `literature_records.csv`
- `deduplicated_literature.csv`
- `screening_decisions.csv`
- `full_text_exclusion_report.csv`
- `extraction_records.csv`
- `quality_assessment_table.csv`
- `analysis_ready_dataset.csv`
- `analysis_result_table.csv`
- `manifest.json`

## Figure Package

输出：

- `project_dir/exports/figures_package.zip`

当前打包：

- `project_dir/figures/` 下的图表 artifacts。
- `project_dir/exports/analysis_result_table_*.csv` 结果表。

## Project Snapshot

新增 `ProjectSnapshot` 数据模型，字段包括：

- `snapshot_id`
- `project_id`
- `created_at`
- `software_version`
- `artifact_manifest`
- `data_manifest`
- `task_manifest`
- `notes`

输出：

- `project_dir/snapshots/snapshot_<snapshot_id>.json`

## Reproducibility Package 内容

输出：

- `project_dir/exports/reproducibility_package_<timestamp>.zip`

当前打包项目目录内已有 artifacts，并额外写入：

- `software_version.json`
- `PACKAGE_MANIFEST.txt`

覆盖范围包括已有的 project metadata、literature records、deduplication outputs、screening decisions、full-text decisions、extraction records、quality assessments、analysis-ready datasets、analysis results、figures、reports 和 exports。缺失 artifact 不会导致崩溃。

## Lock 机制

新增基础 `ArtifactLock`：

- 支持 lock analysis result。
- 支持 lock figure artifact。
- 支持 lock formal report。

锁定 formal report 后，后续 HTML/DOCX/figure package 等对应导出不会覆盖锁定目标，会生成带时间戳的新版本，并返回 warning，例如：

- `formal_report_locked_new_version_created`

## Data Center / Task Center 新增类型

Data Center 新增：

- `formal_word_report`
- `formal_html_report`
- `supplementary_exports`
- `figure_package`
- `project_snapshot`
- `reproducibility_package`

PDF 未真正生成，因此本阶段不将 `formal_pdf_report` 登记为可用数据资产。

Task Center 新增：

- `word_report_export`
- `html_report_export`
- `pdf_report_export`
- `supplementary_export`
- `figure_package_export`
- `project_snapshot_create`
- `reproducibility_package_export`
- `artifact_lock`

## 新增 / 修改文件

- `app/meta_analysis/models/publication.py`
- `app/meta_analysis/services/publication_export_service.py`
- `app/meta_analysis/pages/reporting_page.py`
- `app/meta_analysis/services/formal_report_service.py`
- `app/shared/task_center/service.py`
- `app/shared/feature_availability.py`
- `tests/meta_analysis/test_publication_export_reproducibility.py`
- `tests/meta_analysis/test_developer_preview_stabilization.py`
- `docs/meta_analysis_current_status.md`
- `docs/user_testing/feature_availability.md`
- `docs/user_testing/known_limitations.md`
- `docs/meta_dev_reports/stage_I_publication_export_reproducibility_report.md`

## 新增测试

新增 `tests/meta_analysis/test_publication_export_reproducibility.py`，覆盖：

- HTML report 生成。
- DOCX report 生成。
- supplementary exports 生成。
- figure package ZIP 生成。
- ProjectSnapshot 创建、保存和读取。
- reproducibility package ZIP 生成。
- locked formal report 不被覆盖并生成新版本。
- Data Center / Task Center 登记。
- Reporting page state 暴露 publication export 字段。

旧 formal markdown report 测试继续保留并通过。

## 测试结果

已验证：

- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q tests/meta_analysis/test_publication_export_reproducibility.py tests/meta_analysis/test_developer_preview_stabilization.py tests/meta_analysis/test_prisma_formal_report_mvp.py`
  - 13 passed。
- `python -m compileall -q .`
  - 当前 shell 中 `python` 命令不存在，原样命令无法运行。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`
  - 通过。
- `pytest -q`
  - 当前 shell 中 `pytest` 命令不存在，原样命令无法运行。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`
  - 221 passed。
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`
  - 221 passed。
- `python3 -m app.main --smoke-test`
  - 通过，输出 `meta_analysis_features=7`。

## 当前限制

- HTML/DOCX 仍为 testing draft，不是 journal-ready report。
- DOCX 当前不嵌入 forest plot 图片，只记录 artifact 路径引用。
- PDF 正式报告未实现。
- Supplementary exports 是通用 CSV 展平，不是投稿期刊定制格式。
- Reproducibility package 是本地 artifact ZIP，不包含云同步、环境锁文件或完整系统审计。
- Artifact lock 是基础保护机制，不是完整版本管理系统。

## 下一阶段建议

进入 Stage J：Advanced Methods Expansion，扩展 prevalence、correlation、diagnostic basic 等更多 Method Profile 和基础统计能力；或进入 Stage K：Advanced Analysis Add-ons，增加 subgroup、sensitivity、publication bias 和 funnel plot。
