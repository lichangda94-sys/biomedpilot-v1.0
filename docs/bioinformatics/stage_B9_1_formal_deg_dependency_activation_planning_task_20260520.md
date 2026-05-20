# B9.1 Formal DEG Dependency Activation Planning / Task File

Date: 2026-05-20

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Branch: `dev/bioinformatics`

Baseline: `3ea2b64 rebuild Bioinformatics analysis center gates`

## 1. Objective

Plan the first audited path toward formal DEG activation without directly enabling formal DEG execution.

B9.1 is a planning and gate-design stage. It must turn the B8 contracts and B8.9 UI gates into explicit implementation tasks for dependency policy, parameter manifest validation, result index v2 registration, and UI execution controls.

Primary goal:

- Define what must be true before the `formal_deg` action can ever be enabled.
- Define how scipy/statsmodels dependency policy will be detected, packaged, displayed, and blocked when missing.
- Define the required DEG parameter manifest before execution.
- Define the result schema gate for registering formal DEG output in result index v2.
- Define UI controls so formal DEG remains disabled until resolver, DEG-ready, dependency, parameter, and result schema gates all pass.

Non-goal:

- Do not enable the formal DEG button in B9.1 planning.
- Do not run or wire a user-facing formal DEG executor.
- Do not change result semantics to `formal_computed_result` for any testing, imported, exploratory, or preflight output.
- Do not add formal GSEA, survival statistics, formal plotting, or report-ready bypass.
- Do not install dependencies automatically from Settings or the UI.

## 2. Source Documents

Must read before implementation:

- `docs/bioinformatics/stage_B8_1_standardized_analysis_input_resolver_20260520.md`
- `docs/bioinformatics/stage_B8_2_deg_ready_matrix_and_preflight_20260520.md`
- `docs/bioinformatics/stage_B8_3_controlled_deg_backend_mvp_20260520.md`
- `docs/bioinformatics/stage_B8_4_result_index_and_browser_foundation_20260520.md`
- `docs/bioinformatics/stage_B8_8_analysis_contract_closure_audit_20260520.md`
- `docs/bioinformatics/stage_B8_9_analysis_ui_rebuild_planning_task_20260520.md`
- `docs/bioinformatics/stage_B8_10_analysis_ui_rebuild_implementation_20260520.md`
- `config/bioinformatics/package_requirements.yaml`

Relevant code:

- `app/bioinformatics/analysis_inputs/*`
- `app/bioinformatics/deg_ready/*`
- `app/bioinformatics/deg_engine/dependency_check.py`
- `app/bioinformatics/deg_engine/python_backend.py`
- `app/bioinformatics/results/*`
- `app/bioinformatics/analysis_ui/*`
- `app/bioinformatics/workflow_pages.py`
- `tests/bioinformatics/test_analysis_ui_state.py`
- `tests/bioinformatics/test_analysis_ui_action_rules.py`
- `tests/bioinformatics/test_deg_dependency_check.py`
- `tests/bioinformatics/test_deg_engine.py`
- `tests/bioinformatics/test_result_semantics.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

## 3. Current State

B8.9 added an Analysis Center state layer and UI gates:

- `formal_deg` remains disabled even when task readiness `can_run=True`.
- Disabled reasons include `parameters_gate_not_connected_for_formal_deg`, `formal_result_schema_gate_not_connected`, and `b9_1_activation_required`.
- Dependency detection already reports numpy, pandas, scipy, statsmodels, optional R DEG backend, and survival backends.
- Settings displays dependency detection as detect-first and no-install.
- Result / plot / report gate previews are visible in Analysis Center, Results Browser, and Report Viewer.

Existing backend status:

- `check_deg_backend_dependencies()` checks numpy, pandas, scipy, and statsmodels.
- `run_controlled_deg()` blocks when scipy/statsmodels are unavailable and must not fake p-values or FDR.
- `build_deg_ready_package()` and `build_deg_formal_preflight()` already block many input and value-type errors, but B9.1 must formalize the parameter gate and UI enablement contract.

## 4. Hard Boundaries

1. B9.1 must not directly enable formal DEG execution.
2. B9.1 must not add auto-install behavior.
3. B9.1 must not treat `can_run` from readiness/task center as formal execution readiness.
4. B9.1 must not read `recognition_report.json` as formal analysis input.
5. Resolver packages must remain the formal input source.
6. DEG-ready blockers must still block:
   - multiple candidate matrices without default selection
   - GEO ID_REF/probe without mapping
   - TPM/FPKM/FPKM-UQ routed into count-model DEG
   - unknown value type
   - sample/group mismatch
7. Missing scipy/statsmodels must block formal DEG; no fallback p-value or FDR.
8. Result index v2 must be required before formal output can be considered valid.
9. Testing, exploratory, imported, preflight, developer-preview, and dry-run outputs must not become `formal_computed_result`.
10. UI may show planning/preflight readiness, but must keep the formal DEG button disabled unless every B9.1 gate passes in a later implementation stage.

## 5. B9.1 Workstreams

### B9.1.1 Dependency Policy

Decision points:

- Whether scipy and statsmodels become required runtime/package dependencies for formal DEG.
- Whether they are required for source runtime, packaged `.app`, or only formal DEG activation.
- How missing dependency reasons are exposed in Settings and Analysis Center.
- How package smoke and LaunchServices smoke should prove packaged dependency availability.
- Whether package requirements should record version floors or only presence.

Proposed policy:

- Formal DEG requires:
  - numpy
  - pandas
  - scipy
  - statsmodels
- Settings remains detect-first:
  - installed/missing
  - version
  - blocker
  - packaging impact
  - no install button
- Missing scipy/statsmodels blocks formal DEG with explicit disabled reasons.
- R backends stay optional/not configured in B9.1 unless a separate R dependency strategy is approved.

Suggested files:

```text
config/bioinformatics/package_requirements.yaml
app/bioinformatics/deg_engine/dependency_check.py
app/bioinformatics/analysis_ui/state.py
app/bioinformatics/analysis_ui/labels.py
tests/bioinformatics/test_deg_dependency_check.py
tests/bioinformatics/test_analysis_ui_state.py
tests/ui/test_bioinformatics_workflow_pages.py
```

Acceptance:

- Dependency snapshot includes installed status, version, missing reason, and packaging impact.
- UI displays dependency status without traceback.
- UI has no install action.
- Formal DEG remains disabled when dependency status is not `passed`.
- Packaged app smoke can verify dependency detection without executing formal DEG.

### B9.1.2 Parameter Gate

Formal DEG must require a parameter manifest before execution can be enabled.

Required manifest fields:

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
- `dependency_snapshot_id` or embedded dependency snapshot reference
- `warnings`
- `blockers`

Parameter blockers:

- missing or same case/control group
- missing case/control samples
- sample/group mismatch
- method incompatible with value type
- count-model requested for TPM/FPKM/FPKM-UQ/log data
- unknown value type
- probe/ID_REF mapping missing
- pseudocount invalid for selected method
- FDR policy missing
- threshold values invalid
- dependency snapshot not passed

Suggested files:

```text
app/bioinformatics/deg_engine/parameter_gate.py
app/bioinformatics/deg_ready/preflight.py
app/bioinformatics/analysis_ui/action_rules.py
tests/bioinformatics/test_deg_parameter_gate.py
tests/bioinformatics/test_analysis_ui_action_rules.py
```

Acceptance:

- A valid manifest can be generated from a DEG-ready package and confirmed comparison design.
- Invalid or incomplete parameters produce blockers, not execution.
- Parameter gate output is a manifest/check object, not a formal DEG result.
- UI can show parameter gate status and disabled reasons.

### B9.1.3 Result Schema Gate

Formal DEG output must be registerable in result index v2 before execution can be enabled in a later stage.

Required result index v2 fields:

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

DEG output table minimum schema:

- `feature_id`
- `gene_symbol` or mapped gene id
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

- missing `input_package_id`
- missing `parameters_manifest`
- missing `dependency_snapshot`
- missing engine/version
- missing output artifact
- validation status not passed/warning
- formal result with blockers
- imported/testing/exploratory/preflight semantics marked as formal

Suggested files:

```text
app/bioinformatics/results/validation.py
app/bioinformatics/results/registry.py
app/bioinformatics/deg_engine/result_schema.py
tests/bioinformatics/test_result_semantics.py
tests/bioinformatics/test_result_registry.py
tests/bioinformatics/test_deg_result_schema_gate.py
```

Acceptance:

- Result schema gate can validate a candidate formal DEG bundle before registration.
- Blocked bundles are not registered as `formal_computed_result`.
- A formal DEG result cannot be report-ready unless result schema, provenance, dependency, validation, and report gate pass.
- Existing imported DEG and testing-level results remain non-formal.

### B9.1.4 UI Execution Controls

Formal DEG UI enablement must be a single conjunction of gates:

```text
formal_deg_enabled =
  resolver.deg_recompute package has no blockers
  AND deg_ready package status passed
  AND dependency snapshot status passed
  AND parameter gate status passed
  AND result schema gate status passed or can accept formal output
  AND no B9.1 activation blocker remains
```

UI states:

- `blocked_missing_resolver`
- `blocked_missing_input_package`
- `blocked_missing_mapping`
- `blocked_value_type`
- `blocked_missing_backend`
- `blocked_missing_parameters`
- `blocked_missing_result_schema`
- `formal_ready_but_not_activated`
- `enabled_formal_deg` only in a later implementation stage after audit approval

Required UI behavior in B9.1:

- Keep formal DEG disabled.
- Show each failed gate with disabled reason.
- Show dependency packaging impact in Settings.
- Show parameter manifest status in Analysis Center once implemented.
- Show result schema gate status in Analysis Center and Results Browser.
- Keep developer/testing runner separated from normal user actions.

Suggested files:

```text
app/bioinformatics/analysis_ui/action_rules.py
app/bioinformatics/analysis_ui/state.py
app/bioinformatics/workflow_pages.py
tests/bioinformatics/test_analysis_ui_action_rules.py
tests/bioinformatics/test_analysis_ui_state.py
tests/ui/test_bioinformatics_workflow_pages.py
```

Acceptance:

- Formal DEG button stays disabled in B9.1.
- Disabled reasons identify resolver, DEG-ready, dependency, parameter, and result schema gate state.
- `can_run=True` does not enable formal DEG.
- Tests assert formal DEG is disabled until all gates pass and still not activated in B9.1 planning.

## 6. Proposed Implementation Order

1. Dependency policy audit and manifest decision.
2. Dependency snapshot shape update and Settings display update.
3. Parameter gate model and validator.
4. DEG-ready to parameter gate adapter.
5. Result schema gate model and validator.
6. Analysis UI state/action rule updates to include parameter/result schema gate status.
7. Tests and audit report.
8. Only after B9.1 passes: create a separate B9.2 task for audited formal DEG execution activation.

## 7. Required Tests For B9.1 Implementation

Minimum test commands:

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

## 8. Deliverables

For B9.1 implementation:

- Dependency policy decision recorded in docs.
- Parameter gate contract and tests.
- Result schema gate contract and tests.
- UI state/action rule updates showing gate status and disabled reasons.
- Implementation/audit report, suggested path:

```text
docs/bioinformatics/stage_B9_2_formal_deg_dependency_activation_implementation_20260520.md
```

## 9. Exit Criteria

B9.1 is complete when:

- scipy/statsmodels policy is explicit.
- dependency detection reports install status/version/missing reason/packaging impact.
- formal DEG remains disabled when dependencies are missing or policy is not satisfied.
- parameter manifest gate is defined and tested.
- result schema gate is defined and tested.
- UI execution controls show all gate states and disabled reasons.
- no formal DEG execution path is exposed to users.

## 10. Recommendation

Proceed with B9.1 implementation as a gate-hardening task, not as formal DEG activation. Create a separate B9.2 activation task only after dependency, parameter, result schema, and UI control gates pass under tests and packaged smoke validation.
