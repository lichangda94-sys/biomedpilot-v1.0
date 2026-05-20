# Bioinformatics B9.7 Formal DEG Report-Ready Gate

Date: 2026-05-20

## Scope

B9.7 defines and implements the report-ready gate for the audited formal DEG result section only.

Allowed report-ready source:

- `task_type=deg`
- `result_semantics=formal_computed_result`
- result index v2 formal DEG schema validation passes
- formal DEG parameter confirmation manifest exists and is not expired
- dependency snapshot status is `passed`
- DEG result table validation passes
- at least one qualified formal DEG plot artifact exists, or table-only report mode is explicitly enabled

Blocked sources:

- imported DEG
- testing-level result
- exploratory output
- preflight-only output
- non-DEG result
- formal DEG result with failed/blocked validation, missing dependency snapshot, missing confirmation, expired confirmation, invalid table, or unqualified plot artifact

## Package Output

The package is written under:

`report_package/formal_deg/`

It contains only the formal DEG section:

- `formal_deg_report.md`
- `README_limitations.md`
- DEG result table copy
- formal DEG result entry manifest
- parameter confirmation manifest snapshot
- dependency snapshot
- plot artifact manifest snapshot
- validation report
- provenance
- warnings
- task-run logs when present

The result index entry is updated with:

- `report_ready_eligible=True`
- `report_artifacts` entry for the formal DEG package manifest

## Required Report Content

The generated formal DEG report section includes:

- warnings
- limitations
- dependency versions
- parameter thresholds and method
- input package / task-run / result provenance
- source result table and plot artifact provenance

## Hard Boundaries

B9.7 still does not:

- include GSEA
- include survival/KM/Cox/log-rank/HR
- include clinical association
- produce clinical conclusions or treatment recommendations
- mix imported/testing/exploratory/preflight outputs into formal report-ready

## UI

Results Browser now exposes a formal DEG report-ready package action. The action remains disabled until the B9.7 gate passes. A separate checkbox allows explicit no-plot table-only report mode.

Analysis Center preview now includes a `Formal DEG report-ready` gate row and uses the B9.7 gate as the normal-user report-ready action source.

## Validation

Expected validation commands:

```bash
git diff --check
python3 -m pytest tests/bioinformatics/test_formal_deg_report_ready.py -q
python3 -m pytest tests/bioinformatics/test_formal_deg_plot_artifact.py tests/bioinformatics/test_report_ready_gate.py tests/bioinformatics/test_report_export_package.py -q
python3 -m pytest tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "results_browser or analysis_task or report"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```
