# Stage D: Analysis-ready Dataset Builder Report

## 本阶段目标

将 Analysis 从只读取 `extraction_pool` 做 preflight，推进到可以读取正式 `extraction_records` 并生成 `analysis_ready_dataset` 的统计前质控模块。

本阶段仍不做 pooled meta-analysis、森林图或正式报告。

## 实际完成内容

- 新增 `StudyAnalysisRow` 和 `AnalysisReadyDataset` 数据模型。
- 新增 `AnalysisDatasetService`。
- 支持从 `project_dir/extraction/extraction_records.json` 构建 analysis-ready dataset。
- 支持 binary、continuous、generic effect 三类 outcome。
- 支持列出可用 outcomes。
- 支持保存、读取、按 ID 读取和列出 analysis-ready datasets。
- 保留原有 `AnalysisPreflightService` 和旧 `analysis_preflight` 链路。
- Analysis 页面状态和 testing UI 增加 dataset builder 输入区与摘要字段。

## 修改/新增文件列表

- `app/meta_analysis/models/analysis_dataset.py`
- `app/meta_analysis/services/analysis_dataset_service.py`
- `app/meta_analysis/pages/analysis_page.py`
- `app/shared/task_center/service.py`
- `app/shared/feature_availability.py`
- `docs/meta_analysis_current_status.md`
- `docs/user_testing/feature_availability.md`
- `docs/user_testing/known_limitations.md`
- `tests/meta_analysis/test_analysis_ready_dataset_service.py`

## 新增数据类型

- `analysis_ready_dataset`

## 新增 Task Center 类型

- `analysis_dataset_build`

## 新增 Data Center 类型

- `analysis_ready_dataset`

## 输出路径

- `project_dir/analysis/analysis_ready_datasets.json`

## Analysis 页面新增内容

- Project directory 输入。
- Profile 输入。
- Outcome name 输入。
- Effect measure 输入。
- Build analysis-ready dataset 按钮。
- Included / excluded study count 摘要。
- Validation errors / warnings 摘要。
- Dataset 输出路径显示。

## Preflight / 质控行为

- 检查 `extraction_records.json` 是否存在。
- 检查是否有匹配 `profile_type`。
- 检查是否有匹配 `outcome_name`。
- 检查是否有匹配 `effect_measure`。
- Binary outcome 检查 events / totals。
- Continuous outcome 检查 totals 和 SD。
- Generic effect outcome 检查 effect、CI、standard error。
- 不可分析记录进入 `excluded_extraction_ids`，每个 excluded row 都包含 `exclusion_reason`。

## 新增测试

- 从 binary extraction records 构建 dataset。
- 从 continuous extraction records 构建 dataset。
- 从 generic effect records 构建 dataset。
- 缺少 `extraction_records.json` 时返回明确错误。
- Outcome 不匹配时返回明确错误。
- 非法 extraction 被 excluded 并记录原因。
- `analysis_ready_dataset` 保存、读取和列出。
- Analysis page state 展示 dataset builder summary 字段。

## 测试结果

已验证：

- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest tests/meta_analysis/test_analysis_ready_dataset_service.py tests/meta_analysis/test_analysis_service.py -q`
  - 16 passed。
- `python -m compileall -q .`
  - 当前 shell 中 `python` 命令不存在，原样命令无法运行。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`
  - 通过。
- `pytest -q`
  - 当前 shell 中 `pytest` 命令不存在，原样命令无法运行。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`
  - 200 passed。
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`
  - 200 passed。
- `python3 -m app.main --smoke-test`
  - 通过，输出 `meta_analysis_features=7`。

## 当前仍然 testing / experimental 的功能

- Analysis-ready dataset builder。
- Analysis Preflight。
- ExtractionRecord form integration。
- Reporting Test Summary。

## 当前仍不能做正式统计的限制

- 不计算 OR / RR / RD / MD / SMD / HR pooled effect。
- 不支持 fixed / random effects model。
- 不计算 Q、I²、tau²。
- 不生成森林图或结果表。
- 不做 subgroup、sensitivity 或 publication bias。

## 已知限制

- Dataset builder 仅做统计前质控和结构化行输出。
- Generic effect 当前要求 effect + standard error 或 effect + CI 才能进入 included。
- UI 是 testing 级输入区，不是最终生产分析界面。

## 下一阶段建议

进入 Stage E：Analysis Core MVP，基于 `analysis_ready_dataset` 实现第一版 pooled effect 计算。
