# Stage M End-to-End Validation Report

## 本阶段目标

用一个小型模拟真实项目验证 Meta Analysis testing 主链能否从本地文献输入串到报告与复现包。Stage M 不新增联网检索，不把任何功能标为 production。

## 实际完成内容

- 新增 `examples/meta_analysis_e2e_project/`，包含 CSV 主输入、RIS 伴随输入、README 和 manifest。
- 新增 Stage M E2E 测试，在 pytest 临时目录构建项目并调用现有 service 跑通：
  Import -> Prepare Screening -> Duplicate Review -> Deduplicated Literature -> Screening decisions -> Full-text status -> ExtractionRecord -> Quality Assessment -> Analysis-ready dataset -> Meta-analysis run -> Forest plot -> Funnel plot -> PRISMA summary -> Formal Markdown/HTML/DOCX testing report -> Supplementary exports -> Figure package -> Project snapshot -> Reproducibility package。
- 生成物仅在临时目录创建，不提交大型运行输出或 ZIP。

## 修改/新增文件列表

- `examples/meta_analysis_e2e_project/README.md`
- `examples/meta_analysis_e2e_project/manifest.json`
- `examples/meta_analysis_e2e_project/inputs/mock_literature.csv`
- `examples/meta_analysis_e2e_project/inputs/mock_literature.ris`
- `tests/meta_analysis/e2e_project_builder.py`
- `tests/meta_analysis/test_stage_m_end_to_end_validation.py`
- `docs/meta_dev_reports/stage_M_end_to_end_validation_report.md`

## 跑通步骤

- 完全跑通：Import、Prepare Screening、Duplicate Review、Screening decisions、Full-text status registry、ExtractionRecord 保存、Quality Assessment 保存与导出、Analysis-ready dataset、Meta-analysis run、Forest plot、Funnel plot、PRISMA summary、Formal Markdown/HTML/DOCX testing report、Supplementary exports、Figure package、Project snapshot、Reproducibility package。
- 需要手动补数据：ExtractionRecord 和 Quality Assessment 由测试按 mock 文献种子化录入，代表当前真实用户仍需人工提取和质评。
- 合理 warning：小样本 publication bias warning；PRISMA full-text workflow incomplete note。

## 成功生成 artifact

- `literature/literature_records.json`
- `screening/screening_ready_records.json`
- `deduplication/duplicate_candidate_groups.json`
- `deduplication/deduplicated_literature.json`
- `screening/screening_decisions.json`
- `fulltext/fulltext_registry.json`
- `reports/full_text_exclusion_report.csv`
- `extraction/extraction_records.json`
- `exports/quality_assessment_table.csv`
- `analysis/analysis_ready_datasets.json`
- `analysis/analysis_results.json`
- `figures/forest_plot_<result_id>.png`
- `figures/funnel_plot_<result_id>.png`
- `reports/prisma_flow_summary.json`
- `reports/prisma_flow_summary.md`
- `reports/formal_meta_report.md`
- `reports/formal_meta_report.html`
- `reports/formal_meta_report.docx`
- `exports/supplementary/`
- `exports/figures_package.zip`
- `snapshots/snapshot_<snapshot_id>.json`
- `exports/reproducibility_package_<timestamp>.zip`

## 缺失或 placeholder

- Full-text PDF 管理在本验证中只使用 availability/decision registry，没有真实 PDF 附件。
- PRISMA full-text 数字仍为 testing estimate，不是完整正式 PRISMA。
- PDF report 仍未实现，仅 HTML/DOCX testing export 可用。
- Network meta-analysis 仍是 not implemented placeholder。

## 阻碍真实用户使用的问题

- Import/Prepare/Dedup 的早期输出仍基于统一 storage root，真实项目目录需要更清晰的一致化项目工作区写入策略。
- Extraction 与 Quality 仍需要人工补录，尚未形成成熟的研究者录入体验。
- Publication bias 和 funnel plot 在小样本下只能作为流程验证，不适合解释为稳定统计结论。

## 测试结果

Stage M 新增测试覆盖端到端 artifact 生成、formal report 路径引用、合理 warning 和 reproducibility package 内容。

- Stage M focused test: `1 passed`
- M-P focused tests: `18 passed`
- Full venv pytest: `256 passed`
- Unified `scripts/run_tests.py`: `256 passed`
- Smoke test: passed
- Local shell `python` / `pytest`: unavailable in this environment; venv commands passed.

## 当前状态

Meta Analysis 仍为 Developer Preview / testing。Stage M 证明本地 mock 项目可从导入跑到报告与复现包，但不能升级为 production。
