# Stage AB9: Quality Assessment UI Report

## 本阶段目标

把已有质量评价 registry 和 service 包装成可理解、可测试的 Quality Assessment page-state flow：根据 included studies 显示待评价研究、推荐 NOS / QUADAS-2 / RoB2 simplified 工具、展示 domain judgement fields、domain notes、overall judgement suggestion、completeness summary，并导出 quality summary / table artifacts。

当前仍为 Developer Preview / testing，不是 production quality assessment 或正式 GRADE 系统。

## Continuity audit

审计了当前正式项目：

- `app/meta_analysis/services/quality_service.py`
- `app/meta_analysis/pages/quality_page.py`
- `app/meta_analysis/quality/tool_registry.py`
- `app/meta_analysis/models/systematic_review.py`
- `app/meta_analysis/services/project_contract_service.py`
- `app/meta_analysis/services/report_manifest_service.py`
- `tests/meta_analysis/test_systematic_review_workflow_completion.py`
- `tests/meta_analysis/test_stage_s_extraction_quality_hardening.py`
- `docs/meta_dev_reports/stage_H_systematic_review_workflow_completion_report.md`
- `docs/meta_dev_reports/stage_S_extraction_quality_input_hardening_report.md`

确认当前已有 quality model、quality tool registry、quality save/export、domain notes、overall judgement suggestion 和 completeness summary。

## Legacy capability audit

审计了只读 legacy 目录：

- `/Users/changdali/Documents/model9/bias/`
- `/Users/changdali/Documents/New project 2/app/meta_analysis/legacy/bias/`
- legacy demo risk-of-bias widgets

legacy bias service 支持较早的 bias domains 和 bias table，但没有当前 BioMedPilot 的 quality tool registry、quality_assessments.json、Data Center、Task Center、audit、manifest、report manifest 集成。因此未迁移 legacy 代码。

## 已存在能力

- `QualityAssessment` 数据模型。
- `QualityToolDefinition`。
- `NOS`、`QUADAS-2`、`RoB2 simplified`、`JBI checklist placeholder`、`GRADE placeholder`。
- domain-level notes。
- non-forced overall judgement suggestion。
- quality completeness summary。
- `quality/quality_assessments.json`。
- `exports/quality_assessment_table.csv`。

## 复用能力

- 复用 `QualityAssessmentService`。
- 复用 `quality/tool_registry.py`。
- 复用 `systematic_review.py` 的模型。
- 复用 Data Center / Task Center。
- 复用 AB7 `fulltext/final_included_studies.json` 作为待评价研究来源。

## 新增行为

### Quality page-state flow

新增 `quality_state_from_project()`，返回：

- included study rows
- recommended tool by study design / method profile
- selected tool metadata
- domain fields
- domain note fields
- judgement options
- suggested overall judgement
- completeness summary
- output paths
- warnings
- testing limitations

### Beta output aliases

在保留旧路径的同时新增 internal beta 友好输出：

- `quality/quality_assessment.json`
- `quality/quality_table.csv`
- `quality/quality_summary.md`

兼容旧路径仍保留：

- `quality/quality_assessments.json`
- `exports/quality_assessment_table.csv`

### Audit / manifest

- 保存 quality assessment 时写 `record_saved` audit event。
- 导出 quality table / summary 时写 `report_exported` audit event。
- 如果传入 project contract，则刷新 project manifests。

## Data Center / Task Center / audit / manifest / lineage 影响

Data Center 新增或登记：

- `quality_assessments`
- `quality_assessment_table`
- `quality_assessment`
- `quality_table`
- `quality_summary`

Task Center：

- 继续复用 `quality_assessment_save`。
- 继续复用 `quality_assessment_export`。

Audit log：

- `record_saved`：quality assessment save。
- `report_exported`：quality table / quality summary export。

Manifest / lineage：

- 新增 canonical paths：
  - `quality/quality_assessment.json`
  - `quality/quality_table.csv`
  - `quality/quality_summary.md`
- 新增 source reference：quality beta outputs 追溯到 `quality/quality_assessments.json`。

Report manifest：

- Quality section 增加 alias artifacts 和 summary：
  - `quality/quality_assessment.json`
  - `quality/quality_table.csv`
  - `quality/quality_summary.md`

## 新增/修改文件

新增：

- `tests/meta_analysis/test_stage_ab9_quality_assessment_ui.py`
- `docs/meta_dev_reports/stage_AB9_quality_assessment_ui_report.md`

修改：

- `app/meta_analysis/services/quality_service.py`
- `app/meta_analysis/pages/quality_page.py`
- `app/meta_analysis/services/project_contract_service.py`
- `app/meta_analysis/services/report_manifest_service.py`

## 未迁移内容及原因

未迁移 legacy bias service / bias store，因为旧结构的 `BiasRecord` 与当前 `QualityAssessment` 数据契约不同，并且缺少 manifest/audit/report integration。当前正式项目已经有更适配 AB9 的质量评价基础。

## 未实现内容

- 不做正式 GRADE evidence profile。
- 不做双人冲突仲裁完整系统。
- 不做复杂 PySide 重构。
- 不做 AI 自动质量评价。
- 不把 quality assessment 标记为 production。

## 测试结果

已运行：

- `python3 -m compileall -q .`：通过
- `python3 -m pytest -q tests/meta_analysis/test_stage_ab9_quality_assessment_ui.py`：4 passed
- `python3 -m pytest -q`：381 passed
- `python3 scripts/run_tests.py`：381 passed
- `python3 -m app.main --smoke-test`：通过，`workspace_entries=2`、`bioinformatics_features=11`、`meta_analysis_features=7`
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`：通过
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`：381 passed
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`：381 passed

## 下一阶段建议

进入 Stage AB10：Analysis Setup and Applicability。建议复用 analysis-ready dataset builder、statistics engine 和 applicability service，重点补 setup -> run -> explain page-state，不新增高级统计。
