# B9.1 Formal DEG Gate Hardening Implementation

Date: 2026-05-20

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Task file: `docs/bioinformatics/stage_B9_1_formal_deg_dependency_activation_planning_task_20260520.md`

Important boundary: this file uses the planned `stage_B9_2...` filename, but the implementation described here is B9.1 gate hardening. It is not formal DEG activation.

## Scope

Implemented dependency policy, parameter manifest gate, result schema gate, and UI execution controls required before future formal DEG activation.

Not implemented:

- No user-visible formal DEG executor.
- No enabled formal DEG button.
- No automatic installation of scipy, statsmodels, R packages, or lifelines.
- No formal GSEA.
- No survival statistics.
- No formal plotting.
- No report-ready bypass.
- No promotion of testing/imported/exploratory/preflight/dry-run output to `formal_computed_result`.

## Dependency Policy

Conclusion:

- Formal DEG requires `numpy`, `pandas`, `scipy`, and `statsmodels`.
- `scipy` is required for statistical tests.
- `statsmodels` is required for multiple-testing correction / FDR.
- Missing scipy/statsmodels blocks formal DEG; no fallback p-value or FDR is allowed.
- R DEG backends remain optional and not configured in this stage.
- Settings and Analysis Center remain detect-first and no-install.

Implemented:

- `app/bioinformatics/deg_engine/dependency_check.py`
  - Dependency snapshot schema updated to `biomedpilot.deg_dependency_snapshot.v2`.
  - Records installed/available status, version, missing reason, missing packages, packaging impact, dependency policy, and install action.
  - Keeps `install_action=none_detect_first_only`.
- `config/bioinformatics/package_requirements.yaml`
  - Records formal DEG Python package requirements and packaging impact.
- Analysis UI dependency rows now include packaging impact.

## Parameter Gate

Added:

- `app/bioinformatics/deg_engine/parameter_gate.py`
- `tests/bioinformatics/test_deg_parameter_gate.py`

Parameter manifest fields:

- `schema_version`
- `created_at`
- `input_package_id`
- `deg_ready_package_id`
- `comparison_id`
- `case_group`
- `control_group`
- `case_samples`
- `control_samples`
- `group_design_source`
- `method`
- `method_family`
- `value_type`
- `value_type_policy`
- `gene_id_type`
- `gene_mapping_policy`
- `sample_alignment_policy`
- `log2fc_threshold`
- `p_value_threshold`
- `fdr_threshold`
- `fdr_policy`
- `pseudocount`
- `pseudocount_policy`
- `minimum_group_size`
- `missing_value_policy`
- `multiple_testing_policy`
- `engine_candidate`
- `dependency_snapshot`
- `warnings`
- `blockers`

Parameter blockers:

- `missing_case_or_control_group`
- `same_case_control_group`
- `missing_case_samples`
- `missing_control_samples`
- `case_control_samples_overlap`
- `minimum_group_size_not_met`
- `sample_group_mismatch`
- `count_model_requested_for_display_value_type`
- `method_incompatible_with_count_value_type`
- `unknown_value_type`
- `probe_or_id_ref_mapping_missing`
- `invalid_pseudocount`
- `missing_fdr_policy`
- `invalid_threshold:<field>`
- `dependency_snapshot_not_passed`
- dependency snapshot blockers such as `missing_python_package:scipy`

The parameter gate emits a manifest/check object only. It does not execute DEG and does not register a result.

## Result Schema Gate

Enhanced:

- `app/bioinformatics/deg_engine/result_schema.py`
- `tests/bioinformatics/test_deg_result_schema_gate.py`

Formal DEG result index v2 required fields:

- `result_id`
- `task_run_id`
- `task_type`
- `result_semantics=formal_computed_result`
- `input_package_id`
- `source_dataset_id`
- `source_repository_manifest`
- `parameters_manifest`
- `engine_name`
- `engine_version`
- `dependency_snapshot`
- `output_artifacts`
- `plot_artifacts`
- `report_artifacts`
- `validation_status`
- `warnings`
- `blockers`
- `log_artifacts`
- `failure_reason`
- `created_at`
- `updated_at`
- `schema_version`
- `report_ready_eligible`
- `migration_status`

Formal DEG table required columns:

- `feature_id`
- `gene_symbol`
- `base_mean_or_mean_expression`
- `case_mean`
- `control_mean`
- `log2_fold_change`
- `statistic`
- `p_value`
- `adjusted_p_value`
- `significance_label`
- `warnings`

Result schema blockers:

- missing required result index field
- missing `input_package_id`
- missing `parameters_manifest`
- missing `dependency_snapshot`
- missing engine/version
- missing output artifact
- validation status failed/blocked
- formal result with blockers
- non-formal semantics marked for formal DEG schema

## UI Execution Controls

Updated:

- `app/bioinformatics/analysis_ui/state.py`
- `app/bioinformatics/analysis_ui/action_rules.py`
- `app/bioinformatics/analysis_ui/labels.py`
- `app/bioinformatics/workflow_pages.py`
- `tests/bioinformatics/test_analysis_ui_state.py`
- `tests/bioinformatics/test_analysis_ui_action_rules.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

Formal DEG enablement is now modeled as conjunction of:

- resolver DEG recompute package
- DEG-ready matrix gate
- dependency policy gate
- parameter manifest gate
- result schema gate
- B9.2 activation gate

B9.1 still forces:

- `b9_2_activation_required`
- `enabled=False`
- no user-visible formal execution path

Analysis Center now shows `analysisFormalDegGateTable` with:

- Resolver package
- DEG-ready matrix
- Dependency policy
- Parameter manifest
- Result schema gate
- B9.2 activation

Settings and Analysis Center dependency tables show packaging impact and no install action.

## Validation Results

Passed:

```text
git diff --check
python3 -m pytest tests/bioinformatics/test_deg_dependency_check.py -q
python3 -m pytest tests/bioinformatics/test_deg_parameter_gate.py -q
python3 -m pytest tests/bioinformatics/test_deg_result_schema_gate.py -q
python3 -m pytest tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py -q
python3 -m pytest tests/bioinformatics -q -k "analysis_input or resolver or deg_ready or deg_engine or dependency or parameter_gate or result_schema or result_index or result_semantics or analysis_ui"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or settings or results_browser"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

Observed counts:

- Dependency test: 1 passed.
- Parameter gate tests: 4 passed.
- Result schema gate tests: 4 passed.
- Analysis UI state/action tests: 9 passed.
- Contract-focused bioinformatics selection: 39 passed, 309 deselected.
- Targeted UI selection: 11 passed, 96 deselected.
- Full bioinformatics tests: 348 passed.
- Full UI tests: 174 passed.
- Source smoke: passed.
- Package smoke: passed.
- LaunchServices smoke: passed.
- Codesign verify: passed.

## Remaining Boundaries

B9.1 does not activate formal DEG. The formal DEG action remains disabled and includes `b9_2_activation_required`.

Before B9.2 activation, the next audit must decide:

- whether packaged app dependency bundling is sufficient for scipy/statsmodels,
- how a user confirms final formal DEG parameters,
- how formal output artifacts are written before result index registration,
- how task-run logs/status/dependency snapshots are preserved,
- whether the UI should expose an audited final confirmation step.

## Recommendation

Proceed to B9.2 audited formal DEG execution activation only after reviewing the B9.1 gate outputs in a packaged app and confirming dependency bundling policy.
