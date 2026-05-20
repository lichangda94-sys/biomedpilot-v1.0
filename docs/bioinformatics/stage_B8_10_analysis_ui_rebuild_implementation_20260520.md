# B8.10 Analysis UI Rebuild Implementation

Date: 2026-05-20

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Baseline task file: `docs/bioinformatics/stage_B8_9_analysis_ui_rebuild_planning_task_20260520.md`

## Scope

Implemented B8.9 Analysis UI Rebuild as a UI/state rebuild only. No formal GSEA, formal survival statistics, formal plotting, report-ready bypass, new scipy/statsmodels/R/lifelines dependency, or legacy runner promotion was added.

## Added State Layer

New module: `app/bioinformatics/analysis_ui/`

- `state.py`
  - Builds `biomedpilot.analysis_center_ui_state.v1`.
  - Reads B8 contracts:
    - `resolve_analysis_inputs(project_root)`
    - read-only analysis task center snapshot
    - `load_task_records(project_root)`
    - `load_result_index(project_root)`
    - `check_deg_backend_dependencies()`
    - `check_survival_backend_dependencies()`
    - `evaluate_report_ready_gate(project_root)`
  - Does not write `analysis_task_center.json` while building UI state.
  - Emits package rows, action rows, dependency rows, result rows, plot/report gate preview rows, survival/clinical preflight rows, top blockers/warnings, and developer diagnostics.
- `action_rules.py`
  - Separates preflight/config/exploratory/developer actions from formal actions.
  - Keeps formal DEG disabled with explicit gate reasons and B9.1 activation requirement.
  - Keeps formal GSEA, formal survival, KM/Cox/log-rank hidden/disabled.
  - Blocks plot spec for preflight-only source results.
  - Keeps report-ready export controlled by B8.6 report-ready gate.
- `labels.py`
  - Centralizes package labels, status labels, result semantics labels, and repair guidance.

## UI Changes

Updated `app/bioinformatics/workflow_pages.py`.

Analysis Task Center now renders:

- Resolver package table: `analysisPackageTable`
  - package status, value type, gene id type, downstream tasks, blockers, warnings, repair guidance.
- Action matrix: `analysisActionGateTable`
  - action state, button behavior, disabled reason, next step.
- Dependency panel: `analysisDependencyTable`
  - numpy, pandas, scipy, statsmodels, optional R DEG backend, lifelines, optional R survival backend.
  - detect-only; no install action.
- Result / plot / report preview: `analysisGatePreviewTable`
  - result index availability, plot source-result eligibility, report-ready gate.
- Survival / clinical rows: `analysisSurvivalClinicalTable`
  - survival design preflight, KM/Cox/log-rank/HR disabled row, clinical association preflight row.

Results Browser now renders:

- `resultsGatePreviewTable`, exposing result semantics, plot source-result gate, and report-ready gate preview.

Report Viewer now renders:

- `reportReadyGateTable`, exposing B8.6 report-ready gate status and blockers next to draft report sections.

Settings now renders:

- `analysisDependencyStatusTable`, a detect-first dependency panel with no install action.

## Formal Action Evidence

- Formal DEG remains disabled even when `can_run=True`; action rules add:
  - `parameters_gate_not_connected_for_formal_deg`
  - `formal_result_schema_gate_not_connected`
  - `b9_1_activation_required`
- Formal GSEA is `hidden_until_ready` and disabled.
- Formal survival and KM/Cox/log-rank are `hidden_until_ready` and disabled.
- Plot spec is source-result-driven and blocks `preflight_only` sources with `preflight_only_source_cannot_generate_formal_plot`.
- Report-ready export follows `evaluate_report_ready_gate`; testing/exploratory/imported/preflight outputs do not pass as formal report-ready outputs.
- Developer GEO DEG runner remains developer diagnostics only and still labels output as `testing_level`.

## Tests Added / Updated

Added:

- `tests/bioinformatics/test_analysis_ui_state.py`
- `tests/bioinformatics/test_analysis_ui_action_rules.py`

Updated:

- `tests/ui/test_bioinformatics_workflow_pages.py`

Coverage added:

- State builder uses B8 contracts and does not write task center manifests.
- `can_run` does not enable formal DEG.
- Missing DEG gates and B9.1 activation keep formal DEG disabled.
- Formal GSEA, formal survival, KM/Cox/log-rank are disabled/hidden.
- Preflight-only plot source is blocked.
- Report-ready export is B8.6-gated.
- Settings dependency status is detect-first and no-install.
- Analysis Center, Results Browser, and Report Viewer expose gate preview tables.

## Validation Results

Passed:

```text
git diff --check
python3 -m pytest tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py -q
python3 -m pytest tests/bioinformatics -q -k "analysis_input or resolver or task_run or deg_ready or deg_engine or dependency or result_index or result_registry or result_semantics or plot or report or survival or clinical or analysis_ui"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or results_browser or report or settings"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

Observed counts:

- Analysis UI unit tests: 8 passed.
- Contract-focused bioinformatics selection: 82 passed, 257 deselected.
- Targeted UI selection: 14 passed, 93 deselected.
- Full bioinformatics tests: 339 passed.
- Full UI tests: 174 passed.
- Source smoke: passed.
- Package smoke: passed.
- LaunchServices smoke: passed.
- Codesign verify: passed.

## Remaining Issues

No blocker found in B8.9 scope.

Minor remaining limitations:

- Formal DEG execution remains intentionally unavailable until B9.1.
- GSEA and survival remain design/preflight surfaces only.
- Plot generation remains spec/source-result eligibility preview, not formal plotting.
- Report generation remains draft/report-ready gate preview unless B8.6 gate passes.

## Recommendation

Proceed to B9.1 formal DEG dependency activation planning. Do not activate formal DEG until dependency policy, package parameter gate, result schema gate, and UI execution controls are reviewed together.
