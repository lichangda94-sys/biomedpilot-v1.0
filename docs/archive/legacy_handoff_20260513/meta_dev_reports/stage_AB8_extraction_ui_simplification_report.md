# Stage AB8: Extraction UI Simplification Report

## 本阶段目标

把已有结构化 ExtractionRecord core 整理成更适合测试人员和医学研究者理解的简化 page-state：study characteristics 表格、outcome row templates、required field marker、field help、draft 状态、复制上一条 study 信息、导出前 completeness check 和人工补充日志。

当前仍为 Developer Preview / testing，不是 production extraction UI。

## Continuity audit

审计了当前正式项目：

- `app/meta_analysis/models/extraction.py`
- `app/meta_analysis/services/extraction_form_service.py`
- `app/meta_analysis/services/extraction_record_storage_service.py`
- `app/meta_analysis/services/extraction_validation_service.py`
- `app/meta_analysis/pages/extraction_page.py`
- `app/meta_analysis/services/project_contract_service.py`
- `app/meta_analysis/services/report_manifest_service.py`
- `tests/meta_analysis/test_extraction_form_integration.py`
- `tests/meta_analysis/test_stage_s_extraction_quality_hardening.py`
- `docs/meta_dev_reports/stage_C_extraction_form_integration_report.md`
- `docs/meta_dev_reports/stage_S_extraction_quality_input_hardening_report.md`

确认现有 Extraction core 已经支持正式 `ExtractionRecord`、draft、multi-outcome rows、field-level validation、completeness score 和 CSV export。

## Legacy capability audit

审计了 legacy 目录：

- `/Users/changdali/Documents/model9/extraction/`
- `/Users/changdali/Documents/model9/app_meta/ui/data_extraction_page.py`
- `/Users/changdali/Documents/New project 2/app/meta_analysis/legacy/extraction/`
- `/Users/changdali/Documents/New project 2/app/meta_analysis/legacy/app_meta/ui/data_extraction_page.py`

legacy 提供较早的 `ExtractionRecord`、`OutcomeRecord`、field source traces 和 demo extraction UI。由于当前 BioMedPilot 已经有更完整的 extraction schema registry、validation service、Data Center、Task Center、manifest 和 workflow dashboard 集成，本阶段未迁移 legacy 代码。

## 已存在能力

- `ExtractionRecord` core。
- `StudyCharacteristics`。
- Binary / Continuous / Generic effect / Diagnostic / Proportion / Correlation outcome data。
- `ExtractionFormService.build_extraction_record()`。
- `ExtractionFormService.build_extraction_record_with_outcomes()`。
- draft save/load/delete。
- copy previous study characteristics。
- required field metadata。
- field-level validation summary。
- completeness score。
- pre-export completeness check。
- `extraction_records.csv` export。

## 复用能力

- 复用 `ExtractionFormService`，没有重写 extraction schema。
- 复用 `ExtractionValidationService`。
- 复用 `ExtractionRecordStorageService`。
- 复用 `OutcomeDataType` 和 extraction schema registry。
- 复用现有 Extraction page 的字段分组定义。

## 新增行为

### Simplified extraction page-state

新增 `simplified_extraction_state_from_project()`，返回：

- study rows
- outcome row templates
- field help text
- required field markers
- draft count
- saved record count
- manual edits log path
- extraction records path
- extraction records CSV path
- validation report path
- copy previous availability
- completeness summary
- export readiness
- warnings
- testing limitations

### Manual edits log

新增 `ExtractionFormService.record_manual_edit()` 和 `load_manual_edits()`。

写入：

`extraction/manual_edits_log.jsonl`

每条人工补充记录包含：

- edit_id
- project_id
- extraction_id
- record_id
- field_name
- before_value
- after_value
- reviewer_id
- note
- source_location
- used_for_formal_analysis
- created_at

## Data Center / Task Center / audit / manifest / lineage 影响

Data Center：

- 新增或登记 `extraction_manual_edits_log`。

Task Center：

- 未新增 shared TaskType。
- 继续复用既有 `extraction_record_save`、`extraction_export` 等任务类型。

Audit log：

- 人工补充写入 `extraction_updated` 事件。

Manifest / lineage：

- 新增 canonical path：
  - `extraction/manual_edits_log.jsonl`
- `manual_edits_log.jsonl` source reference 指向 `extraction/extraction_records.json`。

Report manifest：

- Extraction section 增加 `extraction/manual_edits_log.jsonl` 作为来源 artifact。

## 新增/修改文件

新增：

- `tests/meta_analysis/test_stage_ab8_extraction_ui_simplification.py`
- `docs/meta_dev_reports/stage_AB8_extraction_ui_simplification_report.md`

修改：

- `app/meta_analysis/services/extraction_form_service.py`
- `app/meta_analysis/pages/extraction_page.py`
- `app/meta_analysis/services/project_contract_service.py`
- `app/meta_analysis/services/report_manifest_service.py`

## 未迁移内容及原因

未迁移 legacy extraction store/UI，因为 legacy 的 outcome model 与当前正式项目的 extraction schema registry、Analysis-ready Dataset Builder 和 manifest/audit 机制不一致。直接迁移会增加兼容风险。

## 未实现内容

- 未做复杂 PySide UI 重构。
- 未做自动 full-text 表格提取。
- 未做 OCR。
- 未做 AI 自动提取。
- 未让人工补充静默覆盖正式 extraction data。
- 未把 extraction 标记为 production。

## 测试结果

已运行：

- `python3 -m compileall -q .`：通过
- `python3 -m pytest -q tests/meta_analysis/test_stage_ab8_extraction_ui_simplification.py`：4 passed
- `python3 -m pytest -q`：377 passed
- `python3 scripts/run_tests.py`：377 passed
- `python3 -m app.main --smoke-test`：通过，`workspace_entries=2`、`bioinformatics_features=11`、`meta_analysis_features=7`
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`：通过
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`：377 passed
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`：377 passed

## 下一阶段建议

进入 Stage AB9：Quality Assessment UI。建议复用已有 quality tool registry、domain notes、overall judgement suggestion 和 quality completeness summary，补 page-state flow 和 report manifest consistency，不重写质量评价数据结构。
