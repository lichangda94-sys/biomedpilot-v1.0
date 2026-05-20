# B9.2 Audited Formal DEG Execution Activation

Date: 2026-05-20

Scope: two-group controlled DEG MVP only.

## Boundary

Implemented only the audited formal DEG path for two-group controlled comparisons using the existing `python_scipy_statsmodels` backend contract. This stage does not implement or enable GSEA, survival analysis, formal plotting, report-ready export, count-model DESeq2/edgeR, or any automatic dependency installation.

## Activation Path

Formal DEG can run only when all gates pass:

- resolver `deg_recompute` input package has no blockers
- DEG-ready package has no blockers
- dependency snapshot passes
- parameter manifest passes
- result schema gate passes
- method is one of the controlled two-group MVP methods:
  - `welch_t_test`
  - `mann_whitney`

The UI action is now `Run controlled two-group DEG`. In the current local environment it remains disabled when scipy/statsmodels are missing.

## Implementation

Added:

- `app/bioinformatics/deg_engine/formal_runner.py`
  - resolves standardized input packages
  - builds DEG-ready package
  - builds parameter manifest
  - checks result schema gate
  - runs controlled DEG backend
  - writes DEG TSV artifact
  - registers result index v2 entry as `formal_computed_result`
  - leaves `plot_artifacts` and `report_artifacts` empty
  - sets `report_ready_eligible=False`

Updated:

- resolver allows display values for controlled two-group DEG, while count-model routing remains blocked by parameter gate.
- DEG-ready sample alignment now preserves matched sample/group assignments for parameter manifest generation.
- parameter gate blocks count-model methods in this controlled MVP.
- Analysis UI action rules enable formal DEG only when all B9.2 controlled MVP gates pass.
- Analysis Center adds a user-visible button for the controlled DEG action, but it is disabled unless gates pass.

## Boundaries Preserved

- Imported DEG remains `imported_external_result`.
- Testing/exploratory/preflight/dry-run outputs are not upgraded.
- No plot artifact is generated.
- No report-ready package is generated.
- No GSEA or survival execution path is added.
- Missing scipy/statsmodels still blocks execution.

## Validation

Passed:

```text
git diff --check
python3 -m pytest tests/bioinformatics/test_deg_parameter_gate.py tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_formal_controlled_deg_runner.py tests/bioinformatics/test_controlled_deg_python_backend.py -q
python3 -m pytest tests/bioinformatics -q -k "analysis_input or resolver or deg_ready or deg_engine or dependency or parameter_gate or result_schema or result_index or result_semantics or analysis_ui or formal_controlled"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or settings or results_browser"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

Observed counts:

- focused DEG/UI tests: 18 passed
- contract selection: 43 passed, 309 deselected
- targeted UI: 11 passed, 96 deselected
- full bioinformatics: 352 passed
- full UI: 174 passed

## Recommendation

Next work should stay narrow: package scipy/statsmodels for the desktop runtime or document formal DEG dependency setup. Do not proceed to GSEA, formal plotting, report-ready export, or survival until the controlled DEG path is exercised on packaged dependency-complete builds.
