# Bioinformatics B11.1 GSEA Preranked Input / Resource / Parameter Gate

Date: 2026-05-21
Baseline: B10.4 ORA report-ready / E2E acceptance
Scope: GSEA preranked gates only; no GSEA execution

## Old Implementation Audit

Reviewed the active enrichment/GSEA-adjacent surfaces:

- `app/bioinformatics/enrichment/*`: B10 ORA gates and runner are reusable as patterns for local GMT/resource validation, but the ORA runner was not reused as GSEA execution.
- `app/bioinformatics/services/enrichment_runner.py`: legacy/local over-representation enrichment runner only. Not migrated into GSEA because it computes ORA-style enrichment, not preranked GSEA.
- `app/bioinformatics/gene_set_resources.py`: reusable local GMT registry and validation surface.
- `app/bioinformatics/results/*`: reused result index v2 registry/semantics contracts.
- `app/bioinformatics/plots/*`: no GSEA plot path activated.
- `app/bioinformatics/reports/*`: no GSEA report-ready path activated.
- `app/bioinformatics/analysis_ui/*` and `workflow_pages.py`: extended gate display and disabled reasons only.
- `config/bioinformatics/enrichment_defaults.yaml`: documented B11.1 GSEA gate-only policy.

Conclusion: minimal reuse only. B11.1 does not copy legacy enrichment runner logic into a formal GSEA executor and does not treat ORA as GSEA.

## GSEA Preranked Input Schema

Added `app/bioinformatics/gsea/input_gate.py` with:

- `build_gsea_preranked_input_gate(...)`

Allowed sources:

- formal DEG result index entry with `result_semantics=formal_computed_result`
- imported DEG result index entry with `result_semantics=imported_external_result`, confirmed column mapping, and external provenance

Blocked sources:

- raw expression
- ORA result
- testing-level
- exploratory
- preflight/dry-run/developer-preview
- clinical/survival preflight
- plot artifact or report package alone

The input gate writes a local preranked `.rnk` input artifact only when source and rank gates pass. This is an input artifact, not a GSEA result.

## Rank Metric Gate

Added `app/bioinformatics/gsea/rank_metric_gate.py` with:

- `build_gsea_rank_metric_gate(...)`

Allowed rank metrics:

- `signed_log10_fdr_by_log2fc`
- `signed_log10_pvalue_by_log2fc`
- `log2_fold_change`
- `statistic`
- `custom_rank_column`

The gate checks:

- required metric columns exist
- numeric rank values
- no all-zero rank
- no all-NA rank
- explicit duplicate gene policy
- minimum ranked gene count
- known/mapped gene id type
- explicit direction sign policy

Default rank metric is `signed_log10_fdr_by_log2fc`.

## Gene Set Resource Gate

Added `app/bioinformatics/gsea/gene_set_gate.py` with:

- `build_gsea_gene_set_resource_gate(...)`

Supported resources:

- local GMT path
- project gene set resource registry entry

The gate checks:

- GMT validity
- species/gene id compatibility via the shared gene set gate
- min/max gene set size
- term count after size filter
- overlap between ranked genes and gene sets
- MSigDB/manual license warning and acknowledgement

No MSigDB/GO/KEGG/Reactome download is performed.

## Parameter Gate

Added `app/bioinformatics/gsea/parameter_gate.py` with:

- `build_gsea_parameter_manifest(...)`
- `validate_gsea_parameter_manifest(...)`

The manifest includes:

- source DEG and GSEA input ids
- gene set resource id
- rank metric and policy
- min/max gene set size
- `permutation_type=gene_set`
- planned `permutation_count`
- required `random_seed`
- scoring and normalization policy
- p-value/FDR thresholds
- multiple testing policy
- gene id/species policy
- MSigDB acknowledgement state

B11.1 only plans these parameters. It does not execute permutations.

## Result Schema Gate

Added `app/bioinformatics/gsea/result_schema.py` with:

- `build_gsea_result_schema_gate(...)`
- `validate_gsea_result_index_entry(...)`
- `validate_gsea_result_table_row(...)`

Future result contract:

- `task_type=gsea_preranked`
- result index v2 fields including `gsea_input_id`, source DEG id, gene set id, dependency snapshot, output artifacts, plot/report artifacts, warnings/blockers, and `report_ready_eligible`
- future result table columns including enrichment score, normalized enrichment score, p-value, adjusted p-value, leading edge genes, and rank metric

The schema gate records `execution_enabled=False`, `plot_artifacts_allowed=False`, and `report_ready_eligible=False` for B11.1.

## UI Gate

Analysis Center now shows:

- `Review GSEA preranked readiness`
- `Run GSEA preranked`
- GSEA source DEG result gate
- GSEA rank metric gate
- GSEA gene set resource gate
- GSEA parameter manifest gate
- GSEA future result schema gate
- B11.1 execution boundary

`Review GSEA preranked readiness` is gate-review only.

`Run GSEA preranked` remains disabled with `b11_2_gsea_execution_required`.

GSEA plot and GSEA report-ready remain unavailable.

## Test Results

Commands run:

```text
python3 -m pytest tests/bioinformatics/test_gsea_input_gate.py tests/bioinformatics/test_gsea_rank_metric_gate.py tests/bioinformatics/test_gsea_gene_set_gate.py tests/bioinformatics/test_gsea_parameter_gate.py tests/bioinformatics/test_gsea_result_schema_gate.py -q
python3 -m pytest tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py -q
python3 -m pytest tests/bioinformatics -q -k "formal_deg or result_semantics or enrichment or ora or gsea or analysis_ui"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or results_browser or report"
git diff --check
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
```

Results:

- GSEA gate tests: 30 passed.
- Analysis UI state/action tests: 14 passed.
- Targeted bioinformatics formal DEG/result semantics/enrichment/ORA/GSEA/UI tests: 122 passed, 376 deselected.
- Targeted UI workflow tests: 14 passed, 96 deselected.
- `git diff --check`: passed.
- Full bioinformatics tests: 498 passed.
- Full UI tests: 267 passed.
- `python3 -m app.main --smoke-test`: passed.

## Explicitly Not Implemented

- Formal GSEA execution.
- GSEA p-value or FDR computation.
- GSEA result table generation.
- GSEA enrichment plot.
- GSEA report-ready package.
- MSigDB/GO/KEGG/Reactome automatic download.
- ORA-as-GSEA compatibility path.
- Survival/KM/Cox/log-rank/HR.
- Pathway activation/inhibition or clinical conclusion.

## Issues

Blockers: none.

Major: none.

Minor:

- B11.1 creates a preranked input artifact when the input/rank gates pass. This is not a GSEA result and is not report-ready eligible.

## Next Step

Recommended next stage: B11.2 audited GSEA preranked execution planning. It should define runtime dependencies, permutation/statistics behavior, result table validation, and result index write-back before any user-visible GSEA executor is enabled.
