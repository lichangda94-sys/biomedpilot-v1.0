# UI-10 生信分析任务中心页报告

## 本阶段做了什么
- 新增 `BioinformaticsAnalysisTaskCenterWidget`。
- 新增 `app/bioinformatics/project_analysis_tasks.py`。
- 从 capability matrix 生成 `manifests/analysis_task_center.json`，并可创建 `analysis/task_records/*.json` 任务记录。

## 修改文件
- `app/bioinformatics/project_analysis_tasks.py`
- `app/bioinformatics/workflow_pages.py`
- `app/bioinformatics/workspace.py`
- `tests/bioinformatics/test_workflow_adapters.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

## 当前行为
- 展示差异表达、富集、GSEA、相关性、生存、临床变量关联、TCGA + GTEx、报告生成任务。
- 不可运行任务显示缺失输入。
- TCGA + GTEx 固定显示未进行正式 batch correction 的 preview/testing 警告。

## 当前边界
- 只创建任务记录，不运行正式分析。
- 不把 preview runner 描述为正式统计。

## 测试结果
- 已覆盖 task center 生成、不可运行任务、缺失输入、TCGA + GTEx 警告和创建任务失败边界。
- 全量回归：`QT_QPA_PLATFORM=offscreen python3 -m pytest`，92 passed。
- 入口 smoke：`QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`，通过。
