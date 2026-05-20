# Bioinformatics B9.6 Formal DEG Plot Artifact Activation

Date: 2026-05-20

## Scope

B9.6 activates plot artifact registration for audited formal DEG results only.

Allowed source:

- `task_type=deg`
- `result_semantics=formal_computed_result`
- result index v2 formal DEG schema gate passes
- `output_artifacts` includes `artifact_type=deg_result_table`

Blocked sources:

- imported DEG
- testing-level DEG
- exploratory output
- preflight-only output
- non-DEG formal results
- formal DEG entries without a DEG result table

## Implementation

Added `app/bioinformatics/plots/formal_deg.py` with:

- `build_formal_deg_plot_gate`
- `create_formal_deg_plot_artifact`

The artifact is spec/schema driven and registered under the source result index entry `plot_artifacts`.

The artifact records:

- source result id
- source result semantics
- inherited plot semantics
- `plot_artifact_scope=formal_deg_plot`
- input package id
- task-run id
- source parameters manifest
- dependency snapshot
- source DEG table artifact reference
- warnings/blockers

## Boundaries

B9.6 does not:

- generate report-ready output
- set `report_ready_eligible=True`
- start GSEA
- start survival/KM/Cox/log-rank
- provide clinical interpretation
- convert imported/testing/exploratory/preflight output into a formal plot

Imported DEG may use a separate imported plot pathway later, but it cannot be labeled as a BioMedPilot formal recomputed plot.

## UI

The Results Browser formal DEG review card now includes a formal plot artifact control. The button is enabled only when the B9.6 gate passes.

Analysis Center plot action is now formal DEG specific. Imported/testing/exploratory/preflight results show disabled reasons instead of formal plot readiness.

## Report-Ready Hardening

Report-ready gate now requires included results to be explicitly marked `report_ready_eligible=True`. B9.6 plot registration keeps this field false, so report export remains blocked until the later report-ready stage.

## Tests

Validation commands for this stage:

```bash
git diff --check
python3 -m pytest tests/bioinformatics/test_formal_deg_plot_artifact.py -q
python3 -m pytest tests/bioinformatics/test_plot_artifact_schema.py tests/bioinformatics/test_plot_semantics_inheritance.py tests/bioinformatics/test_report_ready_gate.py -q
python3 -m pytest tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "results_browser or analysis_task"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```
