# Stage B Structured Extraction Core Report

## 本阶段目标

在不破坏现有 `extraction_pool` 的前提下，为 Meta Analysis 新增正式结构化 Extraction Core，包括数据模型、schema registry、validation service、storage service 和测试。当前阶段不开发复杂 UI，不运行正式统计。

## 实际完成内容

- 当前状态：已完成并通过统一测试。
- 新增结构化 extraction 数据模型。
- 新增 extraction schema registry，第一批支持 3 个 profile。
- 新增 extraction validation service，覆盖 study、binary outcome、continuous outcome、generic effect outcome 和完整 ExtractionRecord。
- 新增 project_dir 内 storage service，保存和读取 `extraction_records.json`。
- 新增 Data Center 登记：`extraction_records`。
- 新增 Task Center 类型：`extraction_record_save`、`extraction_record_validation`。
- 保留现有 `extraction_pool` service 和旧 Analysis preflight 链路。
- 更新 Feature Availability 和用户测试文档，明确 Extraction 仍为 testing，表单和统计尚未完成。

## 新增数据模型

- `StudyCharacteristics`
- `ExtractionRecord`
- `ExtractedOutcome`
- `BinaryOutcomeData`
- `ContinuousOutcomeData`
- `GenericEffectOutcomeData`
- `ExtractionValidationResult`
- `OutcomeDataType`
- `ExtractionValidationStatus`

## 新增 schema registry

新增 `app/meta_analysis/extraction/schema_registry.py`，提供：

- `list_extraction_schema_profiles`
- `get_extraction_schema_profile`

## 支持的 profile

- `TREATMENT_EFFECT_META`
- `BIOMARKER_PREVALENCE_ASSOCIATION_META`
- `PROGNOSTIC_FACTOR_META`

每个 profile 定义：

- `allowed_outcome_data_types`
- `supported_effect_measures`
- `required_study_fields`
- `required_outcome_fields`
- `validation_rules`
- `recommended_quality_tools`
- `downstream_analysis_hint`

## validation 规则

已实现：

- `sample_size` 必须大于 0。
- binary outcome events 不能大于 total。
- binary / continuous total 必须大于 0。
- continuous SD 不能小于 0。
- generic effect CI lower 不能大于 CI upper。
- OR / RR / HR 的 effect 必须大于 0。
- effect_measure 必须被当前 profile 支持。
- outcome_name 缺失返回 error。
- required study fields 缺失返回 warning。

## storage 路径

默认保存到：

`project_dir/extraction/extraction_records.json`

支持：

- `save_extraction_records(project_dir, records)`
- `load_extraction_records(project_dir)`
- `append_or_update_extraction_record(project_dir, record)`
- `get_extraction_records_by_record_id(project_dir, record_id)`
- `get_extraction_records_by_study_id(project_dir, study_id)`
- `list_extraction_outcomes(project_dir)`

## Data Center / Task Center 新增类型

新增 Data Center 类型：

- `extraction_records`

新增 Task Center 类型：

- `extraction_record_save`
- `extraction_record_validation`

保留 Data Center 类型：

- `extraction_pool`

保留 Task Center 类型：

- `extraction`

## 修改/新增文件列表

- `app/meta_analysis/models/extraction.py`
- `app/meta_analysis/extraction/schema_registry.py`
- `app/meta_analysis/services/extraction_validation_service.py`
- `app/meta_analysis/services/extraction_record_storage_service.py`
- `app/shared/task_center/service.py`
- `app/shared/feature_availability.py`
- `docs/meta_analysis_current_status.md`
- `docs/user_testing/feature_availability.md`
- `docs/user_testing/known_limitations.md`
- `tests/meta_analysis/test_structured_extraction_core.py`
- `docs/meta_dev_reports/stage_B_structured_extraction_core_report.md`

## 新增测试

- StudyCharacteristics 创建。
- BinaryOutcomeData 创建。
- ContinuousOutcomeData 创建。
- GenericEffectOutcomeData 创建。
- ExtractionRecord 创建。
- schema registry 三个 profile 可读取。
- 合法 binary outcome 校验通过。
- events > total 被识别为 error。
- CI lower > CI upper 被识别为 error。
- OR/RR/HR effect <= 0 被识别为 error。
- extraction record validation 任务登记。
- `extraction_records.json` 保存与读取。
- `get_extraction_records_by_record_id` / `get_extraction_records_by_study_id` 正常工作。
- `append_or_update_extraction_record` 正常工作。
- 原有 `extraction_pool` 功能不受影响。

## 测试结果

已通过：

- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest tests/meta_analysis/test_structured_extraction_core.py -q`
  - 11 passed。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest tests/meta_analysis -q`
  - 81 passed。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`
  - 通过。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`
  - 187 passed。
- `python3 -m app.main --smoke-test`
  - 通过，输出 `meta_analysis_features=7`。
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`
  - 187 passed。

环境说明：

- `python -m compileall -q .`
  - 当前 shell 中 `python` 命令不存在。

## 已知限制

- Structured Extraction Core 已可保存结构化数据，但 Extraction 页面尚未提供正式录入表单。
- 当前不生成 `analysis_ready_dataset`。
- 当前不运行正式 Meta 统计。
- 当前不生成 forest plot、formal report、full-text workflow、quality assessment 或 AI suggestion。
- schema registry 是第一批最小 profile，不包含 diagnostic、prevalence、correlation 等高级 profile。

## 下一阶段建议

进入 Stage C：Extraction Form Integration。将 structured ExtractionRecord core 接入 Extraction 页面，提供 testing 表单、保存校验和 CSV 导出，同时继续保留现有 extraction_pool 显示与链路。
