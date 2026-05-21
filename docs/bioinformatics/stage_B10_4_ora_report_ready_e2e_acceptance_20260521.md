# Bioinformatics B10.4 ORA Report-Ready Gate / E2E Acceptance Audit

Date: 2026-05-21
Baseline: B10.3 ORA plot artifact/spec gate
Scope: ORA-specific report-ready package and ORA E2E acceptance audit

## Old Implementation Audit

Reviewed the active report and ORA surfaces before implementation:

- `app/bioinformatics/reports/formal_deg.py`: reusable gate/package structure for timestamped package paths, manifests, logs, limitations, provenance, and result index write-back.
- `app/bioinformatics/reports/readiness.py` and `export_package.py`: generic report package logic remains separate and is not used to bypass ORA-specific gates.
- `app/bioinformatics/enrichment/*`: ORA input/resource/parameter/result schema/review contracts are reused; no ORA statistics changes were made.
- `app/bioinformatics/plots/ora.py`: ORA report gate accepts only B10.3 `ora_plot_spec` artifacts or explicit table-only mode.
- `app/bioinformatics/results/*`: result index v2 registry remains the only write-back surface.
- `app/bioinformatics/analysis_ui/*` and `workflow_pages.py`: ORA report action is gate-aware and remains separate from full report export.

Decision: reused the formal DEG report package pattern, but implemented an independent ORA package. No legacy report builder was promoted into a formal integrated report path.

## ORA Report-Ready Gate

Added `app/bioinformatics/reports/ora.py`:

- `evaluate_ora_report_ready_gate(...)`
- `create_ora_report_ready_package(...)`

The gate checks:

- ORA result exists in result index v2.
- `task_type=ora_enrichment`.
- Allowed semantics only: `formal_computed_result` or `imported_external_result`.
- Formal ORA must point to a formal DEG source.
- Imported-derived ORA must point to an imported DEG source and receives explicit imported-derived warnings.
- ORA result table exists, is non-empty, has required columns, and has numeric p-value/FDR fields.
- Parameter manifest is present.
- Gene set resource manifest is present and passes local GMT validation.
- Dependency snapshot has `status=passed`.
- Task-run log exists.
- Plot artifact exists, unless explicit ORA table-only mode is enabled.
- Source result has no blockers and is not blocked/failed.

Blocked sources:

- `testing_level`
- `exploratory`
- `preflight_only`
- `configured_not_run`
- `blocked`
- `failed`
- raw expression
- DEG result without ORA result
- ORA input gate only
- ORA plot artifact only
- GSEA/survival/clinical preflight

## Package Structure

Package path:

```text
report_package/ora/<result_id>/<timestamp>/
```

Package contents:

```text
ora_report.md
tables/
  ora_result_table.tsv
plots/
  ora_plot_artifact.json
manifests/
  ora_result_index_snapshot.json
  source_deg_result_snapshot.json
  ora_parameters_manifest.json
  gene_set_resource_manifest.json
  dependency_snapshot.json
  plot_artifacts.json
  gate_snapshot.json
  provenance.json
  warnings.json
  package_inventory.json
logs/
  task_run_log.json
README_limitations.md
ora_report_package_manifest.json
```

Every export uses a new timestamped directory and does not overwrite a previous package.

## Table-Only Mode

Explicit table-only mode is supported for ORA packages.

Required wording is included in `ora_report.md` and `README_limitations.md`:

- It is a no-plot ORA report.
- It does not mean plot generation failed.
- It must not imply ORA barplot, ORA dotplot, GSEA plot, volcano, or heatmap figures were generated.

When table-only mode is not enabled, a valid ORA plot artifact/spec is required.

## Imported-Derived ORA Policy

Imported-derived ORA is allowed only as an imported-derived ORA package:

- status: `imported_derived_ora_report_package_created`
- section scope: `imported_derived_ora_only`
- warning: `imported_derived_ora_report_not_biomedpilot_formal_recomputed_ora`
- `report_ready_eligible` remains `False`

Imported-derived ORA is never labeled as BioMedPilot formal recomputed ORA.

Formal ORA packages use:

- status: `ora_report_ready_package_created`
- section scope: `formal_ora_only`
- `report_ready_eligible=True` only after the ORA gate passes and the package is created.

## E2E Acceptance Audit

Added `app/bioinformatics/enrichment/e2e_audit.py`:

- `audit_ora_e2e_acceptance(...)`

The audit covers:

- source DEG result -> ORA result traceability
- ORA result table -> ORA review consistency
- ORA plot artifact -> package consistency
- ORA report-ready gate snapshot
- package inventory and independent reviewability
- dependency/gene set/task log/provenance traceability
- table-only wording
- imported-derived labeling
- testing/exploratory/preflight non-upgrade boundary
- statistical-only guard copy

## UI Changes

Analysis Center:

- Added ORA report-ready action row.
- Button state is driven by `evaluate_ora_report_ready_gate`.
- Disabled reasons show concrete gate blockers.
- Imported-derived ORA has a separate button behavior and warning text.

Results Browser:

- Added `oraTableOnlyReportMode`.
- Added `oraReportReadyButton`.
- Added `oraReportReadyStatus`.
- Export success shows user-visible package output path.
- Status text states ORA-only scope and says GSEA, survival, full integrated report, and clinical conclusions are disabled.

Report Viewer:

- Gate preview now includes ORA report-ready gate status.

## Test Results

Commands run:

```text
python3 -m pytest tests/bioinformatics/test_ora_report_ready.py tests/bioinformatics/test_ora_e2e_acceptance_audit.py -q
python3 -m pytest tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py -q
python3 -m pytest tests/bioinformatics -q -k "ora or enrichment or report or e2e or result_semantics or analysis_ui"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or results_browser or report"
git diff --check
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
```

Results:

- ORA report/E2E tests: 11 passed.
- Analysis UI state/action tests: 14 passed.
- Targeted bioinformatics ORA/report/E2E tests: 109 passed, 359 deselected.
- Targeted UI workflow tests: 14 passed, 96 deselected.
- `git diff --check`: passed.
- Full bioinformatics tests: 468 passed.
- Full UI tests: 267 passed.
- `python3 -m app.main --smoke-test`: passed.

## Explicitly Not Implemented

- Full integrated scientific report.
- GSEA.
- Survival/KM/Cox/log-rank/HR.
- Clinical association statistics.
- Clinical conclusion, diagnosis, or treatment recommendation.
- Automatic gene set download.
- Real ORA image rendering beyond B10.3 plot artifact/spec.

## Issues

Blockers: none.

Major: none.

Minor:

- ORA package can include a plot artifact/spec, but no rendered PNG/SVG/PDF image is generated in B10.4.

## Next Step

Recommended next stage: B10.5 ORA package UX polish or B11 planning for audited enrichment expansion. Do not enter GSEA or survival execution without a new scoped gate plan.
