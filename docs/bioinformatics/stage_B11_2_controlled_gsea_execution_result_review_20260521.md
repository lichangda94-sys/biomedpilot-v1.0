# Bioinformatics B11.2 Controlled GSEA Execution / Result Review

Date: 2026-05-21

## Scope

B11.2 activates only the controlled preranked GSEA MVP. The source must be an audited DEG result from result index v2: `formal_computed_result` DEG, or `imported_external_result` DEG with confirmed imported column mapping and provenance. Gene sets must come from a validated local GMT or project gene-set registry.

This stage does not implement phenotype permutation, sample-level GSEA, ssGSEA/GSVA, online gene-set downloads, GSEA plot artifacts, GSEA report-ready packages, survival, or clinical/pathway activation conclusions.

## Old Implementation Audit

B11.1 already provided GSEA input, rank metric, gene-set, parameter, and future result-schema gates. It deliberately left execution disabled with a B11.2 activation blocker. B11.2 replaces that activation blocker with a controlled execution path while preserving all source/result semantics gates.

## Execution Scope

Implemented:

- `app/bioinformatics/gsea/executor.py`
- `run_controlled_preranked_gsea(...)`
- gene-set permutation only
- deterministic `random_seed`
- explicit `permutation_count`
- rank metric inherited from B11.1 rank gate
- result index v2 registration
- task-run log under `analysis_runs/gsea/`

The executor writes a GSEA TSV table only. It does not write plot or report artifacts.

## Algorithm Policy

The MVP sorts the B11.1 `.rnk` file by rank score, computes weighted running-sum enrichment score per term, records leading-edge genes, builds a gene-set permutation null by deterministic random sampling, calculates empirical p-values, and applies Benjamini-Hochberg FDR via `statsmodels.stats.multitest.multipletests`.

No fake p-value or fake FDR fallback is allowed. Missing or broken dependencies block execution.

## Dependency Policy

Added detect-first dependency snapshot:

- `numpy`
- `pandas`
- `scipy`
- `statsmodels`

Missing packages produce `missing_python_package:<name>` blockers. There is no install action and no automatic installation.

## Result Semantics

Formal DEG source:

- `task_type=gsea_preranked`
- `result_semantics=formal_computed_result`
- `source_result_semantics=formal_computed_result`

Imported DEG source:

- `task_type=gsea_preranked`
- `result_semantics=imported_external_result`
- `source_result_semantics=imported_external_result`
- warning: `imported_deg_derived_gsea_not_biomedpilot_recomputed_deg_formal_gsea`

Testing, exploratory, preflight, raw expression, ORA, and non-DEG results remain blocked.

## Result Index Schema

The B11.2 GSEA result schema requires:

- `result_id`
- `task_run_id`
- `task_type=gsea_preranked`
- `result_semantics`
- `input_package_id` / `gsea_input_id`
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

## Task-Run Log

The task-run log records:

- `task_run_id`
- `gsea_input_id`
- `source_result_id`
- `gene_set_resource_id`
- `parameters_manifest`
- `dependency_snapshot`
- `status`
- timestamps
- `output_table`
- `result_index_path`
- `random_seed`
- `permutation_count`
- warnings/blockers/failure reason

## Result Review

Added:

- `app/bioinformatics/gsea/review.py`
- `app/bioinformatics/gsea/export.py`

Review table columns:

- `term_id`
- `term_name`
- `set_size`
- `overlap_size`
- `enrichment_score`
- `normalized_enrichment_score`
- `p_value`
- `adjusted_p_value`
- `leading_edge_genes`
- `rank_metric`
- `significance_label`

Summary includes term counts, significant term count, top positive/negative NES terms, source DEG, rank metric, gene set, dependency versions, permutation count, and random seed.

Export is TSV/CSV table-only and never creates report-ready output.

## UI Changes

Analysis Center:

- Adds `Run controlled preranked GSEA`
- Enables only when B11.1 input/rank/gene-set/parameter/result-schema gates and B11.2 dependency gate pass
- Shows disabled reasons for source, rank, gene set, parameter, dependency, and schema blockers

Results Browser:

- Adds controlled preranked GSEA review section
- Shows GSEA summary, sortable/filterable table, provenance, task-run log, and result index path
- Keeps plot/report disabled with B11.3/future report-gate messaging

Report Viewer:

- No automatic GSEA inclusion.

## Explicit Non-Implemented Items

- phenotype permutation
- sample-level GSEA
- ssGSEA / GSVA
- formal GSEA plots
- GSEA report-ready package
- raw expression GSEA
- online gene-set downloads
- GSEA clinical/pathway activation conclusions
- survival / KM / Cox / log-rank

## Tests

Commands run:

- `git diff --check` - passed
- `python3 -m pytest tests/bioinformatics/test_gsea_execution.py tests/bioinformatics/test_gsea_result_review.py -q` - 6 passed
- `python3 -m pytest tests/bioinformatics -q -k "gsea or enrichment or formal_deg or result_semantics or analysis_ui"` - 86 passed, 419 deselected
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or results_browser or report"` - 14 passed, 96 deselected
- `python3 -m pytest tests/bioinformatics -q` - 505 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` - 267 passed
- `python3 -m app.main --smoke-test` - passed

Packaging smoke was not rerun because B11.2 did not change packaging/runtime dependency inclusion or launcher behavior.

## Next Stage

Proceed to B11.3 only for GSEA plot artifact gate design/activation, with the same rule that plot artifacts must inherit source result semantics and must not create report-ready output.
