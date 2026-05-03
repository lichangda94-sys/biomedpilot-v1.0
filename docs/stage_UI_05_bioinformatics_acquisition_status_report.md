# UI-05 生信数据获取状态页报告

## 本阶段做了什么
- 新增 `BioinformaticsAcquisitionStatusWidget`。
- 读取 `acquisition/plans/latest_acquisition_plan.json`、`acquisition/handoffs/latest_acquisition_handoff.json`、`acquisition/records/latest_acquisition_record.json`。
- 展示 source、策略、plan、handoff、record、raw_data 路径和 plan_only 警告。

## 修改文件
- `app/bioinformatics/workflow_pages.py`
- `app/bioinformatics/project_workspace_binding.py`
- `app/bioinformatics/workspace.py`
- `tests/bioinformatics/test_workflow_adapters.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

## artifact 契约
- acquisition plan：`acquisition/plans/`
- acquisition handoff：`acquisition/handoffs/`
- acquisition record：`acquisition/records/`
- 策略字段固定为 `copy`、`reference`、`plan_only`。

## 当前边界
- 页面只显示状态。
- 不下载数据，不识别文件，不标准化，不运行分析。

## 测试结果
- 已覆盖无 acquisition 文件空状态、plan_only 状态、继续信号和 strategy 传递。
- 全量回归：`QT_QPA_PLATFORM=offscreen python3 -m pytest`，92 passed。
- 入口 smoke：`QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`，通过。
