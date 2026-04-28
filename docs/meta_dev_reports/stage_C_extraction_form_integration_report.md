# Stage C Extraction Form Integration Report

## 本阶段目标

在保留现有 Extraction 页面和 `extraction_pool` 工作流的基础上，将 Stage B 的 Structured Extraction Core 接入 testing 表单流程，使用户可以录入、校验、保存和导出正式 `ExtractionRecord`。

## 实际完成内容

- 保留现有 Extraction Pool 生成逻辑和页面摘要。
- 新增 `ExtractionFormService`，统一处理：
  - extraction_pool 候选文献读取
  - form data 到 `ExtractionRecord` 的构建
  - validation service 调用
  - error 阻止保存
  - warning 允许保存
  - `extraction_records.csv` 导出
  - Data Center / Task Center 登记
- Extraction 页面新增 testing 结构化表单区域。
- Extraction page state 新增 profile、outcome type、study fields、binary/continuous/generic effect fields、empty state 和 export path。
- 更新 Feature Availability 和用户测试文档，保持 Extraction 为 testing。

## Extraction 页面新增内容

- project_dir 输入
- record_id / study_id / reviewer_id 输入
- profile_type 输入
- outcome_data_type 输入
- study characteristics 字段
- binary outcome 字段
- continuous outcome 字段
- generic effect outcome 字段
- validation summary
- 保存 ExtractionRecord 按钮
- 导出 extraction_records.csv 按钮
- extraction_pool 无候选时显示 empty state，不崩溃

## 保存路径

结构化记录保存到：

`project_dir/extraction/extraction_records.json`

## 导出路径

CSV 导出到：

`project_dir/exports/extraction_records.csv`

## validation 行为

- 保存前调用 `ExtractionValidationService`。
- 有 error 时阻止保存。
- 有 warning 时允许保存，并在页面/结果中返回 warning。
- 当前支持 binary、continuous、generic effect 三类 outcome。

## Data Center / Task Center 新增类型

新增 Data Center 类型：

- `extraction_records_export`

继续使用 Stage B 新增 Data Center 类型：

- `extraction_records`

新增 Task Center 类型：

- `extraction_export`

继续使用 Stage B 新增 Task Center 类型：

- `extraction_record_save`
- `extraction_record_validation`

保留既有类型：

- Data Center：`extraction_pool`
- Task Center：`extraction`

## 修改/新增文件列表

- `app/meta_analysis/services/extraction_form_service.py`
- `app/meta_analysis/pages/extraction_page.py`
- `app/shared/task_center/service.py`
- `app/shared/feature_availability.py`
- `docs/meta_analysis_current_status.md`
- `docs/user_testing/feature_availability.md`
- `docs/user_testing/known_limitations.md`
- `tests/meta_analysis/test_extraction_form_integration.py`
- `docs/meta_dev_reports/stage_C_extraction_form_integration_report.md`

## 新增测试

- Extraction page state 暴露 testing 表单字段。
- 没有 extraction_pool 时候选读取安全返回 empty state。
- 合法 binary extraction record 可保存。
- 非法 binary outcome 阻止保存。
- `extraction_records.csv` 可导出。
- Data Center / Task Center 登记成功。
- 原有 `extraction_pool` 测试仍通过。

## 测试结果

已验证：

- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest tests/meta_analysis/test_extraction_form_integration.py tests/meta_analysis/test_extraction_service.py -q`
  - 11 passed。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest tests/meta_analysis -q`
  - 86 passed。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`
  - 通过。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`
  - 192 passed。
- `python3 -m app.main --smoke-test`
  - 通过，输出 `meta_analysis_features=7`。
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`
  - 192 passed。

环境说明：

- `python -m compileall -q .`
  - 当前 shell 中 `python` 命令不存在。

## 已知限制

- 当前表单是 testing 级输入区，不是最终生产级 extraction UI。
- 尚未提供 record selector 的完整列表控件和动态 outcome form 切换。
- 尚未生成 `analysis_ready_dataset`。
- 尚未运行正式 Meta 统计。
- 尚未接入 forest plot、formal report、full-text workflow、quality assessment 或 AI suggestion。

## 下一阶段建议

进入 Stage D：Analysis-ready Dataset Builder。读取 `project_dir/extraction/extraction_records.json`，按 profile/outcome/effect_measure 构建统计前数据集，并输出 included/excluded study row 质控摘要。
