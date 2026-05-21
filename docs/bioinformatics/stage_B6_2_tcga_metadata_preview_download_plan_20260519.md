# Bioinformatics B6.2 TCGA Metadata Preview Download Plan

## 阶段目标

B6.2 将 TCGA 数据源从静态中文 registry 和 request 草案推进到真实 GDC metadata 预览与下载计划草案。用户选择 TCGA 项目、分析目的和样本范围后，可以预览 case/sample/file 数、预计下载大小、样本类型分布、访问类型、workflow 和文件格式摘要。

本阶段不推进 B5.19，不实现 DEG/GSEA 执行器，不下载 TCGA 大文件，不构建表达矩阵，不写 `source_files`，也不把 TCGA preview/plan 标记为 ready。

## 修改文件

- `app/bioinformatics/data_sources/__init__.py`
- `app/bioinformatics/data_sources/tcga_preview.py`
- `app/bioinformatics/workflow_pages.py`
- `tests/bioinformatics/test_data_source_registries.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`
- `docs/bioinformatics/stage_B6_2_tcga_metadata_preview_download_plan_20260519.md`

## 新增模型/服务/UI

- `TCGAPreviewRequest`：记录 TCGA 项目、中文名称、分析目的、样本范围、GDC sample type 和是否需要表达/临床 metadata。
- `TCGAPreviewSummary`：记录 case/sample/file 统计、下载大小估算、sample/access/workflow/data_format 分布、warnings、GDC filters 和分页统计。
- `TCGADownloadPlanDraft`：保存 `draft_only` 下载计划草案，包含 GDC filters、file count、预计大小、file id preview 和约束声明。
- `TCGAMetadataPreviewService`：集中构建可 mock 的 GDC `/files` 与 `/cases` 查询，支持分页汇总和 graceful degrade。
- TCGA 页面新增 `预览可下载数据`、`生成下载计划草案`、样本类型分布表、preview summary、warnings 和默认折叠的开发者诊断。

## GDC Metadata Preview 实现说明

表达类目的 GDC file filter 会自动映射到：

- `Transcriptome Profiling`
- `Gene Expression Quantification`
- `RNA-Seq`
- `STAR - Counts`
- `open`
- 用户样本范围对应的 GDC sample type

临床/样本概况通过 GDC `/cases` endpoint 预览 case/sample/diagnosis/demographic 相关字段。本阶段只读取 metadata，不下载表达文件。网络失败、空结果、字段缺失、无癌旁正常样本等情况会生成用户可理解 warning，不导致 UI 崩溃。

## 用户可见流程

1. 在数据源页进入 TCGA 数据库。
2. 选择癌种项目、分析目的、样本范围。
3. 点击 `预览可下载数据`。
4. 页面显示 case/sample/file、预计大小、样本类型分布、预计内容和风险提示。
5. 预览满足条件后点击 `生成下载计划草案`。
6. 系统写入 request/acquisition 草案和 `acquisition/tcga_download_plans/*.json`，但不写 `source_files`。

## 未实现内容

- 未下载 TCGA 大文件。
- 未构建表达矩阵。
- 未进入 DEG/GSEA ready。
- 未实现 B5.19。
- 未做 TCGA + GTEx 自动合并。
- 未把 GTEx 自动作为 TCGA 正常对照。
- 未向普通用户暴露 raw GDC filter、file UUID 全列表或 raw API response；这些只放在开发者诊断中。

## 边界条件

- 空结果不会生成下载计划草案。
- 无 normal 样本时提示用户可更改样本范围。
- 网络失败返回 failed preview，并禁用下载计划草案。
- 文件大小缺失时保留估算值并提示部分文件未知。
- 所有新增网络调用均可通过 fake fetcher mock，测试不依赖真实网络。
- 旧未跟踪文件 `docs/bioinformatics/Bioinformatics_handoff_report_20260513.md` 保留未动。

## 测试结果

- `git diff --check`：passed
- `python3 -m pytest tests/bioinformatics -q`：273 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：163 passed
- `python3 -m app.main --smoke-test`：passed

## Commit

本报告随 B6.2 代码提交生成；最终 commit hash 以本次 Codex 完成汇报为准。
