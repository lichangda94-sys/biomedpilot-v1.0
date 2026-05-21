# Bioinformatics B10.3 ORA Plot Artifact / Pathway Visualization Gate

Date: 2026-05-21
Baseline: B10.2 controlled ORA execution / result review
Scope: ORA result-derived plot artifact/spec gate only

## Audit Scope

Reviewed the active plotting and ORA/result/UI surfaces before implementation:

- `app/bioinformatics/plots/*`: reused the existing `PlotArtifact` model, `validate_plot_artifact`, and result-index write-back pattern from `formal_deg.py`.
- `app/bioinformatics/enrichment/*`: reused ORA result schema and table validation rules from `result_schema.py`; no ORA statistics changes were made.
- `app/bioinformatics/results/*`: continued using result index v2 registry APIs only.
- `app/bioinformatics/analysis_ui/*` and `app/bioinformatics/workflow_pages.py`: added gate-aware UI state and disabled reasons.
- `config/bioinformatics/plotting_defaults.yaml`: added B10.3 ORA spec-only plotting policy.
- Tests under `tests/bioinformatics/*plot*`, `tests/bioinformatics/*ora*`, and `tests/ui/test_bioinformatics_workflow_pages.py`.

Legacy/older plot code was not migrated into the formal ORA path. Existing generic plot encoders remain outside the B10.3 ORA gate unless the source result passes the new ORA-specific contract.

## Implementation Summary

Added `app/bioinformatics/plots/ora.py` with:

- `build_ora_plot_gate(...)`
- `create_ora_plot_artifact(...)`

Supported plot artifact/spec types:

- `ora_barplot`
- `ora_dotplot`

The implementation creates a plot artifact/spec only. It does not render PNG, SVG, or PDF images and does not add matplotlib, seaborn, R, or ggplot2 dependencies.

## ORA Plot Gate

The gate requires:

- `source_result_id` exists in result index v2.
- Source result has `task_type=ora_enrichment`.
- Source result semantics are allowed.
- Formal ORA source keeps `source_result_semantics=formal_computed_result`.
- Imported-derived ORA source keeps `source_result_semantics=imported_external_result` and emits an imported-derived warning.
- Source validation status is not `blocked` or `failed`.
- Source result has no blockers.
- ORA result index entry passes B10.1/B10.2 schema validation.
- ORA result table exists and is non-empty.
- Required table columns are present.
- `p_value`, `adjusted_p_value`, `overlap_count`, `gene_set_size`, and `enrichment_ratio` are numeric where required.
- `term_id` and `term_name` are present.
- Plot parameters are valid: supported `plot_type`, positive `top_n`, allowed `sort_by`, and `0 <= fdr_threshold <= 1`.

Blocked sources include preflight-only, testing-level, exploratory, configured-not-run, blocked, failed, raw expression, DEG-only results, GSEA preflight, and survival/clinical preflight.

## Plot Artifact Schema

Registered ORA plot artifacts include:

- `plot_id`
- `plot_type`
- `source_result_id`
- `source_task_type=ora_enrichment`
- `source_result_semantics`
- `plot_semantics`
- `source_ora_table`
- `plot_spec_artifact`
- `image_artifacts=[]`
- `engine_name`
- `engine_version`
- `dependency_snapshot`
- `parameters_manifest`
- `warnings`
- `blockers`
- `created_at`
- `schema_version`

The plot spec records:

- `plot_type`
- `top_n`
- `sort_by`
- `x_field`
- `y_field`
- `size_field`
- `color_field`
- `term_label_field`
- `fdr_threshold`
- `source_result_id`
- `source_table`
- `rendering=spec_only_no_image_dependency`
- `image_output=none`

## Plot Semantics

Semantics are inherited from the source ORA result:

- Formal ORA result -> `plot_semantics=formal_computed_result`
- Imported-derived ORA result -> `plot_semantics=imported_external_result`

The plot gate never upgrades imported, testing, exploratory, or preflight outputs into formal recomputed results.

## Result Index Write-Back

On success:

- The artifact is appended to the source ORA result `plot_artifacts`.
- Existing plot artifact with the same `plot_id` is replaced instead of duplicated.
- `report_artifacts=[]` is preserved.
- `report_ready_eligible=False` is forced.

On failure:

- No plot artifact is registered.
- No report artifact is created.
- No report-ready status is enabled.

## UI Changes

Analysis Center:

- ORA plot action is now gate-aware.
- It is enabled only when the ORA plot gate passes.
- Disabled states show concrete blocker reasons.

Results Browser:

- Added ORA plot type selector for `ora_barplot` and `ora_dotplot`.
- Added `Generate ORA plot artifact/spec` action.
- Status text explicitly says this is spec-only, does not render PNG/SVG/PDF, does not enter report-ready, and does not activate GSEA or survival.

GSEA plot, KM/survival plot, and report-ready inclusion remain disabled.

## Boundary Decisions

Not implemented in B10.3:

- Real PNG/SVG/PDF rendering.
- matplotlib/seaborn/R/ggplot2 dependency activation.
- GSEA plot.
- Survival/KM plot.
- ORA report-ready package inclusion.
- Pathway activation/inhibition conclusion.
- Clinical interpretation or treatment recommendation.

## Test Results

Commands run:

```text
python3 -m pytest tests/bioinformatics/test_ora_plot_artifact.py -q
python3 -m pytest tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or results_browser or report"
python3 -m pytest tests/bioinformatics -q -k "ora or enrichment or plot or result_semantics or analysis_ui"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
git diff --check
python3 -m app.main --smoke-test
```

Results:

- `tests/bioinformatics/test_ora_plot_artifact.py`: 7 passed.
- `tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py`: 13 passed.
- Targeted UI workflow tests: 14 passed, 96 deselected.
- Targeted bioinformatics tests: 68 passed, 388 deselected.
- Full bioinformatics tests: 456 passed.
- Full UI tests: 267 passed.
- `git diff --check`: passed.
- `python3 -m app.main --smoke-test`: passed.

## Issues

Blockers: none.

Major: none.

Minor:

- The ORA plot artifact is a spec and registry artifact only. A later rendering stage is required before user-facing figure files exist.

## Conclusion

B10.3 ORA plot artifact/spec gate is implemented within the requested boundaries. The product can now register ORA barplot/dotplot specs from controlled ORA result index entries while keeping report-ready, GSEA, survival, and image rendering disabled.

Recommended next stage: B10.4 ORA report-ready gate planning/implementation, limited to deciding whether formal ORA sections may enter a report-ready package and under what provenance/limitations constraints.
