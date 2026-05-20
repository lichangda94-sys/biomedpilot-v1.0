# Bioinformatics B9.4 Formal DEG User Parameter Confirmation Flow

Date: 2026-05-20

## Scope

B9.4 adds the final user confirmation layer before controlled formal DEG execution. It does not extend the DEG algorithm and does not activate GSEA, survival, formal plotting, or report-ready export.

The confirmation layer covers:

1. comparison: case/control groups, sample counts, and sample lists
2. method: `welch_t_test` or `mann_whitney`
3. thresholds: log2FC, p-value, FDR, and pseudocount
4. value type and method compatibility
5. dependency snapshot: numpy, pandas, scipy, statsmodels versions
6. output plan: task-run id, result id, result table path, task-run log path, result index registry path
7. formal DEG execution only after confirmation gate passes
8. post-run boundary: no plot artifacts, no report artifacts, report-ready remains false

## Implementation

New contract:

- `app/bioinformatics/deg_engine/confirmation.py`
- confirmation path: `manifests/formal_deg_parameter_confirmation.json`
- schema: `biomedpilot.formal_deg_parameter_confirmation.v1`

The confirmation manifest stores:

- `parameter_manifest`
- `dependency_snapshot`
- `output_plan`
- `user_confirmation_summary`
- `confirmed_by_user`
- `blockers` / `warnings`

The formal DEG runner now requires `validate_deg_parameter_confirmation(...)` to pass before execution. A missing, stale, blocked, or dependency-version-mismatched confirmation blocks formal DEG and does not write result index output.

## UI Flow

Analysis Task Center now includes:

- method selector: `welch_t_test` / `mann_whitney`
- threshold inputs: log2FC, p-value, FDR
- `确认 formal DEG 参数` button
- confirmation preview table showing comparison, method, thresholds, value type compatibility, dependency snapshot, output plan, and confirmation gate

Action matrix behavior:

- `Confirm formal DEG parameters` is available only after resolver, DEG-ready, dependency, parameter, and result schema gates pass.
- `Run controlled two-group DEG` remains disabled until the user parameter confirmation gate passes.
- `can_run=True` task readiness does not bypass confirmation.

## Result Boundary

After a confirmed formal DEG run:

- `result_semantics=formal_computed_result`
- result index v2 registration path: `results/summaries/result_index.json`
- output table: `results/tables/<result_id>.tsv`
- task-run log: `analysis/formal_deg/<result_id>_run_log.json`
- `plot_artifacts=[]`
- `report_artifacts=[]`
- `report_ready_eligible=False`

No GSEA, survival, formal plot, or report-ready behavior is activated in B9.4.

## Validation

Passed checks:

```bash
git diff --check
python3 -m pytest tests/bioinformatics/test_deg_parameter_confirmation.py tests/bioinformatics/test_formal_controlled_deg_runner.py tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_formal_deg_runtime_validation.py -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or settings or results_browser"
python3 -m pytest tests/bioinformatics -q -k "parameter_confirmation or formal_controlled_deg or analysis_ui or formal_deg_runtime"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

Observed totals:

- focused B9.4 bioinformatics tests: 19 passed
- targeted UI task-center tests: 11 passed
- full bioinformatics suite: 360 passed
- full UI suite: 174 passed
- controlled scipy/statsmodels runtime check: `status=passed`

Runtime validation with the controlled scipy/statsmodels environment continues to pass because the B9.3 runtime check now creates a confirmation manifest before invoking the formal runner.

## Conclusion

B9.4 provides the required final user confirmation gate. The next stage can focus on improving the parameter confirmation UX if needed, but broader formal analysis expansion remains out of scope.
