# Bioinformatics B10.2 Controlled ORA Execution / Result Review MVP

Date: 2026-05-21

## Scope

B10.2 activates a controlled ORA MVP after B10.1 gates. It supports execution only from eligible DEG result-index sources plus a validated local GMT/project gene-set resource. It registers result index v2 entries, writes task-run logs, and adds ORA result review/export.

This stage does not implement GSEA, ranked enrichment, pathway plots, survival, clinical statistics, or report-ready ORA sections.

## Old Implementation Audit

`app/bioinformatics/services/enrichment_runner.py` already contained a local enrichment runner with:

- DEG CSV input;
- GMT parsing;
- hand-written hypergeometric tail;
- hand-written Benjamini-Hochberg adjustment;
- legacy outputs (`enrichment_results.csv`, `enrichment_summary.json`).

Audit conclusion: the old runner was not promoted to formal ORA. It bypasses B10.1 ORA input/resource/parameter gates, does not write result index v2, does not create an audited task-run contract, and can throw file/runtime exceptions. B10.2 implements a new controlled path under `app/bioinformatics/enrichment/`.

Existing reusable surfaces:

- `app/bioinformatics/enrichment/*` B10.1 gates are reused as hard preconditions.
- `app/bioinformatics/results/registry.py` is used for result index v2 registration.
- `app/bioinformatics/analysis_task_runs.py` path helpers are used for ORA task-run log placement.
- `app/bioinformatics/gene_set_resources.py` remains the local GMT/project registry validator; no online download path is called.

## ORA Execution

New module: `app/bioinformatics/enrichment/executor.py`

Execution flow:

1. Build ORA input gate from result index DEG source.
2. Build gene set resource gate from explicit GMT/resource or selected/single project registry resource.
3. Build ORA parameter manifest.
4. Detect ORA runtime dependencies.
5. Validate future ORA result schema gate.
6. Import `scipy` and `statsmodels` only after dependency gate passes.
7. Execute hypergeometric or Fisher exact ORA.
8. Adjust p-values with statsmodels Benjamini-Hochberg FDR.
9. Write ORA TSV table.
10. Write task-run log.
11. Register result index v2 entry.

Supported methods:

- `hypergeometric`
- `fisher_exact`

Supported sources:

- `formal_computed_result` DEG result -> ORA result semantics `formal_computed_result`
- `imported_external_result` DEG result -> ORA result semantics `imported_external_result` with imported-derived warning

Blocked sources:

- raw expression
- preflight/testing/exploratory/configured-not-run
- non-DEG result
- missing/invalid DEG table
- empty selected gene list
- invalid gene set

## Dependency Policy

New module: `app/bioinformatics/enrichment/dependency_check.py`

Controlled ORA requires:

- `scipy`
- `statsmodels`

Dependency snapshot records package status, importability, version, missing reason, packaging impact, and `install_action=none_detect_first_only`.

If either dependency is missing:

- status is `blocked_missing_dependency`;
- no p-value is generated;
- no adjusted p-value is generated;
- no ORA result is registered;
- a failed ORA task-run log is written.

## Result Semantics

Formal DEG-derived ORA:

- `task_type=ora_enrichment`
- `result_semantics=formal_computed_result`
- `source_result_semantics=formal_computed_result`

Imported DEG-derived ORA:

- `task_type=ora_enrichment`
- `result_semantics=imported_external_result`
- `source_result_semantics=imported_external_result`
- warning: `imported_deg_derived_ora_not_biomedpilot_recomputed_deg_formal_ora`

Imported DEG-derived ORA is not presented as BioMedPilot recomputed formal DEG-derived ORA.

## Result Index Schema

Updated module: `app/bioinformatics/enrichment/result_schema.py`

Registered ORA result entries include:

- `result_id`
- `task_run_id`
- `task_type=ora_enrichment`
- `result_semantics`
- `input_package_id` / `ora_input_id`
- `source_deg_result_id`
- `source_result_semantics`
- `gene_set_resource_id`
- `parameters_manifest`
- `engine_name`
- `engine_version`
- `dependency_snapshot`
- `output_artifacts`
- `plot_artifacts=[]`
- `report_artifacts=[]`
- `validation_status`
- `warnings`
- `blockers`
- `log_artifacts`
- `failure_reason`
- `created_at`
- `updated_at`
- `schema_version`
- `report_ready_eligible=False`
- `migration_status`

ORA table columns:

- `term_id`
- `term_name`
- `gene_set_size`
- `overlap_count`
- `overlap_genes`
- `background_size`
- `selected_gene_count`
- `p_value`
- `adjusted_p_value`
- `enrichment_ratio`
- `source_gene_list`
- `warnings`

## Task-Run Log

Controlled ORA writes `analysis_runs/ora/<task_run_id>/task_run.json`.

The task-run log records:

- `task_run_id`
- `ora_input_id`
- `source_result_id`
- `gene_set_resource_id`
- `parameters_manifest`
- `dependency_snapshot`
- `status`
- `started_at`
- `finished_at`
- `output_table`
- `result_index_path`
- `warnings`
- `blockers`
- `failure_reason`

Failed or blocked runs write a task-run log and do not register formal ORA output.

## Result Review

New modules:

- `app/bioinformatics/enrichment/review.py`
- `app/bioinformatics/enrichment/export.py`

Review displays:

- `term_id`
- `term_name`
- `overlap_count`
- `gene_set_size`
- `selected_gene_count`
- `enrichment_ratio`
- `p_value`
- `adjusted_p_value`
- `overlap_genes`
- `significance_label`

Summary includes:

- term total
- significant term count
- top term by FDR
- source DEG result id
- source semantics
- gene set resource
- method
- dependency versions
- selected gene count
- background size

Sorting/filtering:

- sort by adjusted p-value, p-value, enrichment ratio, overlap count, significance, or input order
- filter all/significant/not significant

Export:

- TSV/CSV table only
- `report_ready_eligible=False`
- `plot_artifacts=[]`
- `report_artifacts=[]`

Guard copy states that ORA is statistical pathway over-representation analysis and does not prove pathway activation/inhibition, clinical interpretation, or treatment recommendation.

## UI Changes

Analysis Center:

- `run_ora_enrichment` is enabled only when ORA source, gene set resource, parameter, result schema, and dependency gates all pass.
- Missing source/gene set/parameter/dependency shows disabled reasons.
- GSEA remains disabled/hidden.
- ORA plot and ORA report-ready remain disabled/hidden.

Results Browser:

- Adds Controlled ORA result review table.
- Shows source DEG result id and source semantics.
- Shows dependency versions and provenance.
- Provides ORA TSV/CSV export.
- Keeps ORA plot/report-ready/GSEA/survival disabled in copy and downstream labels.

Report Viewer:

- No automatic ORA report-ready integration was added.

## Tests

Commands run:

- `git diff --check` - passed
- `python3 -m pytest tests/bioinformatics/test_ora_execution.py tests/bioinformatics/test_ora_result_review.py -q` - 9 passed
- `python3 -m pytest tests/bioinformatics -q -k "ora or enrichment or formal_deg or result_semantics or analysis_ui"` - 70 passed, 378 deselected
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or results_browser or report"` - 14 passed, 96 deselected
- `python3 -m pytest tests/bioinformatics -q` - 448 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` - 267 passed
- `python3 -m app.main --smoke-test` - passed

Package smoke/open/codesign were not rerun because B10.2 did not modify packaging/runtime bundle scripts or launcher metadata.

## Boundaries Preserved

- No GSEA.
- No ranked enrichment.
- No permutation test.
- No online KEGG/GO/MSigDB download.
- No raw expression enrichment.
- No ORA plot artifact.
- No ORA report-ready package section.
- No survival/KM/Cox/log-rank/HR.
- No pathway activation/inhibition conclusion.
- No clinical conclusion or treatment recommendation.

## Next Step

Recommended next stage: B10.3 ORA plot artifact planning/activation, only if the source is a registered controlled ORA result and the plot artifact inherits ORA result semantics. Report-ready integration should remain blocked until a separate ORA report-ready gate is audited.
