# Bioinformatics B11.3 GSEA Plot / Report-Ready / E2E Acceptance

Date: 2026-05-21

## Scope

B11.3 adds GSEA-specific plot artifact/spec gating, GSEA-specific report-ready package generation, and a GSEA end-to-end acceptance audit for the B11.2 controlled preranked GSEA MVP.

This stage remains limited to `task_type=gsea_preranked`. It does not create a full integrated research report, does not enable survival/KM/Cox/log-rank/HR, and does not generate clinical/pathway activation conclusions.

## Old Implementation Audit

The existing reusable patterns were:

- B9 formal DEG plot/report gates: result-index driven, provenance preserving, no automatic clinical interpretation.
- B10 ORA plot/report gates: spec-only plot artifact, table-only package mode, timestamped package path, package inventory, and imported-derived warning.
- B11.2 GSEA execution/review: controlled preranked result table and result index v2 registration, no plot/report output.

B11.3 reuses these patterns only as GSEA-specific gates. It does not copy ORA/DEG as a complete integrated report workflow.

## GSEA Plot Artifact Gate

Implemented:

- `app/bioinformatics/plots/gsea.py`
- `build_gsea_plot_gate(...)`
- `create_gsea_plot_artifact(...)`

Supported plot types:

- `gsea_enrichment_curve_spec`
- `gsea_nes_barplot_spec`

Rendering policy:

- `image_artifacts=[]`
- `rendering=spec_only_no_image_dependency`
- no PNG/SVG/PDF rendering

Allowed sources:

- `result_semantics=formal_computed_result`, `task_type=gsea_preranked`
- `result_semantics=imported_external_result`, `task_type=gsea_preranked`, with imported-derived warning

Blocked sources:

- DEG result alone
- ORA result alone
- raw expression
- testing/exploratory/preflight/dry-run
- survival/clinical preflight
- invalid/missing GSEA result table

## GSEA Report-Ready Gate

Implemented:

- `app/bioinformatics/reports/gsea.py`
- `evaluate_gsea_report_ready_gate(...)`
- `create_gsea_report_ready_package(...)`

Gate requires:

- complete GSEA result index v2 entry
- allowed result semantics
- `task_type=gsea_preranked`
- source DEG result id and semantics
- valid GSEA result table with numeric `p_value` and `adjusted_p_value`
- parameter manifest
- gene-set resource manifest
- dependency snapshot `status=passed`
- task-run log
- GSEA plot artifact or explicit table-only mode
- warnings/limitations/provenance present
- no source blockers

Formal GSEA packages can set `report_ready_eligible=True`. Imported-derived GSEA packages remain `report_ready_eligible=False` and carry an imported-derived warning.

## Package Structure

Package path:

```text
report_package/gsea/<result_id>/<timestamp>/
```

Contents:

```text
gsea_report.md
tables/gsea_result_table.tsv
plots/gsea_plot_artifact.json
manifests/gsea_result_index_snapshot.json
manifests/source_deg_result_snapshot.json
manifests/gsea_parameters_manifest.json
manifests/gene_set_resource_manifest.json
manifests/dependency_snapshot.json
manifests/gate_snapshot.json
manifests/package_inventory.json
logs/task_run_log.json
README_limitations.md
```

Each export uses a new timestamped directory and does not overwrite earlier packages.

## Table-Only Mode

Explicit `allow_table_only_report=True` allows a GSEA table/manifests-only package without a plot artifact.

Required wording states that a no-plot GSEA report is intentional, does not mean plot generation failed, and must not imply that GSEA enrichment curve, NES barplot, volcano, heatmap, ORA, or survival figures were generated.

## Imported-Derived Policy

Imported-derived GSEA is allowed only as imported-derived/package review output:

- result semantics remain `imported_external_result`
- package status is `imported_derived_gsea_report_package_created`
- section scope is `imported_derived_gsea_only`
- it is not labeled as BioMedPilot formal recomputed GSEA
- `report_ready_eligible` remains false

## E2E Acceptance Audit

Implemented:

- `app/bioinformatics/gsea/e2e_audit.py`
- `audit_gsea_e2e_acceptance(...)`

Audit chain:

```text
source DEG result
-> GSEA input gate
-> rank metric / gene set / parameter gates
-> GSEA execution result
-> GSEA review
-> GSEA plot artifact
-> GSEA report-ready gate
-> report package
```

It validates traceability for source DEG id, GSEA result id, gene set id, rank metric, parameter manifest, dependency snapshot, task-run log, and package ids. It also checks review/table consistency, packaged table consistency, plot artifact registration, gate snapshot contents, and independent package reviewability.

## UI Changes

Analysis Center:

- Shows GSEA plot gate status via action matrix.
- Shows GSEA report-ready gate status via action matrix.
- Keeps disabled reasons visible for invalid/missing GSEA result, dependency, table, plot, or table-only gate.

Results Browser:

- Adds GSEA plot artifact/spec action.
- Adds GSEA report package export action.
- Displays GSEA export output path on success.
- Shows explicit table-only mode checkbox.
- Keeps GSEA distinct from DEG and ORA.
- Survival and full integrated report remain disabled/hidden.

## Tests

Commands run in closeout:

- `git diff --check` - passed
- `python3 -m pytest tests/bioinformatics/test_gsea_plot_artifact.py tests/bioinformatics/test_gsea_report_ready.py tests/bioinformatics/test_gsea_e2e_acceptance_audit.py -q` - 16 passed
- `python3 -m pytest tests/bioinformatics -q -k "gsea or enrichment or report or e2e or plot or result_semantics or analysis_ui"` - 145 passed, 376 deselected
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or results_browser or report"` - 15 passed, 96 deselected
- `python3 -m pytest tests/bioinformatics -q` - 521 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` - 268 passed
- `python3 -m app.main --smoke-test` - passed

Packaging smoke was not rerun because B11.3 did not modify packaging/runtime dependency inclusion or launcher behavior.

## Explicit Non-Implemented Items

- full integrated research report
- survival/KM/Cox/log-rank/HR
- clinical interpretation, diagnosis, or treatment recommendation
- pathway activation/inhibition conclusion
- phenotype permutation GSEA
- ssGSEA/GSVA
- raw expression GSEA
- online gene-set download
- rendered PNG/SVG/PDF GSEA plots

## Next Step

Proceed only to a scoped next GSEA stage if needed, such as rendered plot backend validation or integrated report planning. Do not merge GSEA into a full multi-section report without a separate audited stage.
