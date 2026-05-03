# UI-11 生信结果浏览页报告

## 本阶段做了什么
- 新增 `BioinformaticsResultsBrowserWidget`。
- 新增 `app/bioinformatics/results/project_results.py`。
- 读取 `manifests/result_manager.json` 与 `results/summaries/result_index.json`。

## 修改文件
- `app/bioinformatics/results/__init__.py`
- `app/bioinformatics/results/project_results.py`
- `app/bioinformatics/workflow_pages.py`
- `app/bioinformatics/workspace.py`
- `tests/bioinformatics/test_workflow_adapters.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

## 当前行为
- 展示结果名称、分析类型、文件类型、创建时间、路径、状态和 warning。
- 缺失文件显示中文 warning，不崩溃。

## 当前边界
- 不运行分析，不生成新统计结果，不伪造图表。

## 测试结果
- 已覆盖无 result index 空状态、mock result index、缺失文件 warning 和继续报告页信号。
- 全量回归：`QT_QPA_PLATFORM=offscreen python3 -m pytest`，92 passed。
- 入口 smoke：`QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`，通过。
