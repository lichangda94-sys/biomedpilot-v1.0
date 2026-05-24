# Bioinformatics B27 DEG/ORA/GSEA Real Plot Renderer

Date: 2026-05-24

## Scope

B27 upgrades the DEG, ORA, and GSEA plot artifact path from spec-only metadata to real builtin SVG image artifacts.

Implemented scope:

- Formal DEG SVG plot artifacts from `formal_computed_result` DEG results.
- ORA SVG plot artifacts from eligible ORA result index entries.
- GSEA SVG plot artifacts from eligible preranked GSEA result index entries.
- Builtin SVG renderer dependency snapshot with no external plotting dependency.
- Result index registration of plot artifacts with image artifact paths and manifest files.
- UI copy/action rows updated from spec-only wording to SVG artifact wording.

Out of scope:

- No report-ready unlock by plot generation alone.
- No full integrated report activation.
- No GSEA/survival/clinical expansion beyond existing gates.
- No pathway activation/inhibition conclusion.
- No clinical conclusion, prognosis, or treatment recommendation.
- No matplotlib, seaborn, R ggplot2, plotly, PDF, or PNG renderer dependency activation.

## Renderer Policy

Default renderer:

- `builtin_svg`

Dependency behavior:

- `status=passed`
- `install_action=none_detect_first_only`
- `packaging_impact=no_external_runtime_dependency_for_deg_ora_gsea_svg_plots`

Unsupported renderer requests are blocked with `unsupported_omics_plot_renderer:<renderer>`.

## Plot Types

DEG:

- `volcano_plot`
- `deg_heatmap` as ranked effect-size heatmap from DEG table fields

ORA:

- `ora_barplot`
- `ora_dotplot`

GSEA:

- `gsea_enrichment_curve_spec` now writes a real SVG curve artifact while retaining the historical plot type id.
- `gsea_nes_barplot_spec` now writes a real SVG NES barplot artifact while retaining the historical plot type id.

Historical `*_spec` ids are retained to avoid breaking result/report gates that already key on these plot types.

## Artifact Contract

Generated artifacts include:

- `plot_id`
- `plot_type`
- `source_result_id`
- `source_result_semantics`
- `plot_semantics`
- `plot_artifact_scope`
- `input_package_id`
- `task_run_id`
- `parameters_manifest`
- `plot_spec_artifact.rendering=real_svg_artifact_no_report_ready`
- `image_artifacts[0].format=svg`
- `table_artifacts`
- `engine_name=biomedpilot_omics_svg_renderer`
- `engine_version`
- `dependency_snapshot`
- `warnings`
- `blockers`

Output paths:

- DEG: `results/plots/deg/<plot_id>.svg`
- ORA: `results/plots/ora/<plot_id>.svg`
- GSEA: `results/plots/gsea/<plot_id>.svg`
- Manifests: matching `<plot_id>_manifest.json`

## Gate Boundaries

Preserved blockers:

- Preflight, testing, exploratory sources cannot generate formal DEG plots.
- Formal DEG plot requires `result_semantics=formal_computed_result`, `task_type=deg`, and a DEG result table.
- ORA/GSEA plots require their own task type and valid result table.
- Imported-derived ORA/GSEA plots inherit `imported_external_result` semantics and keep imported warnings.
- Plot artifacts do not upgrade imported/testing/exploratory/preflight results.
- Plot generation forces `report_ready_eligible=False` on the source entry.

## UI Changes

Analysis UI and Results Browser now describe:

- ORA SVG plot artifact instead of ORA plot artifact/spec.
- GSEA SVG plot artifact instead of GSEA plot artifact/spec.
- Builtin SVG renderer instead of spec-only/no-image rendering.
- Report-ready, full integrated report, survival, and clinical interpretation remain disabled unless their separate gates pass.

## Validation

Commands run:

```text
git diff --check
python3 -m pytest tests/bioinformatics/test_formal_deg_plot_artifact.py tests/bioinformatics/test_ora_plot_artifact.py tests/bioinformatics/test_gsea_plot_artifact.py tests/bioinformatics/test_analysis_ui_action_rules.py -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "results_browser or analysis_task"
python3 -m pytest tests/bioinformatics -q -k "plot or report or gsea or ora or formal_deg or result_semantics or analysis_ui"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

Results:

- focused plot/action tests: 35 passed
- focused UI tests: 16 passed, 100 deselected
- broad plot/report/enrichment/UI-state tests: 235 passed, 471 deselected
- full bioinformatics tests: 706 passed, 1 scipy precision warning
- full UI tests: 273 passed
- source smoke: passed
- package smoke: passed
- open-W packaged smoke: passed
- codesign verify: passed
- `git diff --check`: passed

## Conclusion

B27 activates a real builtin SVG plot artifact renderer for DEG/ORA/GSEA while preserving result semantics, report-ready gates, and clinical/pathway interpretation boundaries.

Recommended next stage: continue toward B28 Cox multivariate review/report-ready integration only after B27 package/open-W/smoke checks pass.
