# UI-09 生信工作流总控页报告

## 本阶段做了什么
- 新增 `BioinformaticsWorkflowStatusWidget`。
- 新增 `app/bioinformatics/project_workflow_orchestrator.py`。
- 工作流总控读取/写入 `manifests/project_workflow_state.json`、`logs/workflow/project_workflow_summary.json`、`logs/workflow/project_workflow_report.md`。

## 修改文件
- `app/bioinformatics/project_workflow_orchestrator.py`
- `app/bioinformatics/workflow_pages.py`
- `app/bioinformatics/workspace.py`
- `tests/bioinformatics/test_workflow_adapters.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

## 状态映射
- not_started：未开始
- running：运行中
- completed：已完成
- completed_with_warnings：完成但有警告
- skipped：已跳过
- failed：失败
- unavailable：不可用

## 当前边界
- 只串联已存在的 active adapter 和 artifact 读取。
- 不新增后端流程，不吞掉错误，不伪造完成。

## 测试结果
- 已覆盖无 workflow state、mock/默认步骤状态、运行完整流程、运行单步和失败/警告状态展示。
- 全量回归：`QT_QPA_PLATFORM=offscreen python3 -m pytest`，92 passed。
- 入口 smoke：`QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`，通过。
