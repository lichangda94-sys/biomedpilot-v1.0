# Stage J: Advanced Methods Expansion Report

## 本阶段目标

在已有 Extraction、Analysis-ready Dataset、Analysis Core、Figures 和 Reports 基础上，扩展更多 Method Profile 和基础统计方法，使 Meta Analysis 从普通治疗效果 Meta 分析扩展为多类型医学 Meta 分析 testing 平台。

本阶段不做 AI、团队协作、完整网络 Meta 高级算法、diagnostic bivariate model 或 HSROC。

## 新增 Profile

在不移除既有三个 profile 的前提下，新增：

- `DIAGNOSTIC_ACCURACY_META`
- `PREVALENCE_INCIDENCE_META`
- `CORRELATION_META`
- `SINGLE_ARM_OUTCOME_META`
- `CONTINUOUS_BIOMARKER_DIFFERENCE_META`
- `EXPOSURE_DISEASE_RISK_META`
- `NETWORK_META_ANALYSIS`

保留：

- `TREATMENT_EFFECT_META`
- `BIOMARKER_PREVALENCE_ASSOCIATION_META`
- `PROGNOSTIC_FACTOR_META`

每个 profile 均定义：

- `profile_type`
- `description`
- `allowed_outcome_data_types`
- `supported_effect_measures`
- `required_study_fields`
- `required_outcome_fields`
- `recommended_quality_tools`
- `recommended_figures`
- `report_sections`
- `validation_rules`
- `downstream_analysis_hint`

## 新增 Outcome Data Models

- `DiagnosticAccuracyOutcomeData`
  - `outcome_name`
  - `tp`
  - `fp`
  - `fn`
  - `tn`
  - `effect_measure`
  - `sensitivity`
  - `specificity`
  - `cutoff`
  - `index_test`
  - `reference_standard`
  - `notes`
- `ProportionOutcomeData`
  - `outcome_name`
  - `events`
  - `total`
  - `effect_measure`
  - `population_source`
  - `diagnostic_criteria`
  - `timepoint`
  - `subgroup`
  - `notes`
- `CorrelationOutcomeData`
  - `outcome_name`
  - `r`
  - `sample_size`
  - `effect_measure`
  - `correlation_type`
  - `p_value`
  - `variable_x`
  - `variable_y`
  - `notes`

## 新增统计能力

新增基础 testing 统计能力：

- Proportion / prevalence / incidence:
  - raw proportion
  - logit transformed proportion
  - standard error
  - 可复用 existing fixed / random inverse variance pooling
- Correlation:
  - r to Fisher z
  - Fisher z pooling 基础支持
  - back-transform to r
- Diagnostic basic:
  - sensitivity
  - specificity
  - PLR
  - NLR
  - DOR

Analysis-ready dataset builder 现在支持：

- `proportion`
- `correlation`
- `diagnostic_accuracy`

## 明确 Not Implemented 的高级方法

- `NETWORK_META_ANALYSIS` 只作为 profile placeholder。
- Network meta 当前返回 `network_meta_analysis_not_implemented`。
- Diagnostic bivariate model 未实现。
- HSROC 未实现。
- SUCRA、league table、network forest plot 未实现。

## UI 增强点

- Extraction page state 新增 advanced outcome type:
  - `diagnostic_accuracy`
  - `proportion`
  - `correlation`
- Extraction page state 新增字段组：
  - diagnostic accuracy fields
  - proportion fields
  - correlation fields
- Analysis page state 说明中明确：
  - prevalence / correlation / diagnostic basic 支持
  - network meta 显示 not implemented
- Formal Markdown report 增加 `Advanced method summary`。

## 新增 / 修改文件

- `app/meta_analysis/models/extraction.py`
- `app/meta_analysis/extraction/schema_registry.py`
- `app/meta_analysis/services/extraction_validation_service.py`
- `app/meta_analysis/services/extraction_form_service.py`
- `app/meta_analysis/services/analysis_dataset_service.py`
- `app/meta_analysis/stats/meta_effects.py`
- `app/meta_analysis/pages/extraction_page.py`
- `app/meta_analysis/pages/analysis_page.py`
- `app/meta_analysis/services/formal_report_service.py`
- `app/shared/feature_availability.py`
- `tests/meta_analysis/test_advanced_methods_expansion.py`
- `tests/meta_analysis/test_structured_extraction_core.py`
- `docs/meta_analysis_current_status.md`
- `docs/user_testing/feature_availability.md`
- `docs/user_testing/known_limitations.md`
- `docs/meta_dev_reports/stage_J_advanced_methods_expansion_report.md`

## 测试结果

已验证：

- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q tests/meta_analysis/test_advanced_methods_expansion.py tests/meta_analysis/test_structured_extraction_core.py tests/meta_analysis/test_analysis_ready_dataset_service.py tests/meta_analysis/test_analysis_core_mvp.py tests/meta_analysis/test_extraction_form_integration.py tests/meta_analysis/test_prisma_formal_report_mvp.py`
  - 43 passed。
- `python -m compileall -q .`
  - 当前 shell 中 `python` 命令不存在，原样命令无法运行。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`
  - 通过。
- `pytest -q`
  - 当前 shell 中 `pytest` 命令不存在，原样命令无法运行。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`
  - 228 passed。
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`
  - 228 passed。
- `python3 -m app.main --smoke-test`
  - 通过，输出 `meta_analysis_features=7`。

## 当前限制

- Advanced methods 仍为 Developer Preview / testing。
- Diagnostic 只支持基础 2x2 指标，不支持 bivariate model 或 HSROC。
- Network meta 只有 profile placeholder，不能运行。
- Correlation / proportion pooling 复用 inverse variance 基础框架，尚未做 publication-grade method options。
- UI 仍是 testing page state / 简易表单字段，不是最终生产表单。
- Formal report 只列出 advanced method summary，不提供投稿级解读。

## 下一阶段建议

进入 Stage K：Advanced Analysis Add-ons，开发 subgroup analysis、leave-one-out sensitivity analysis、publication bias basic tests 和 funnel plot。
