# Bioinformatics B22 Real KM/Cox Plot Artifact Renderer

Date: 2026-05-22

## Scope

B22 adds a gated real plot artifact path for Survival/Clinical KM and Cox results.

Implemented scope:

- KM/log-rank formal result to real SVG plot artifact.
- Cox univariate and Cox multivariate formal result to real SVG forest plot artifact.
- Renderer dependency snapshot and gate diagnostics.
- Result index registration of plot artifacts without changing the source result semantics.
- Analysis Center rows and action rules for KM/Cox real plot availability and disabled reasons.

Out of scope:

- Survival report-ready export.
- Clinical prognosis, treatment recommendation, or conclusion generation.
- Risk score or nomogram execution.
- GSEA/ORA/DEG behavior changes.
- PNG/PDF renderer activation through matplotlib/R.

## Source Gate

The real renderer accepts only result index entries with:

- `result_semantics=formal_computed_result`
- `validation_status=passed` or `warning`
- no result blockers
- task type in:
  - `survival_km_logrank`
  - `cox_univariate`
  - `cox_multivariate`
- required source table artifact:
  - KM: `km_curve_table`
  - Cox univariate: `cox_result_table`
  - Cox multivariate: `cox_multivariate_result_table`

Blocked sources return a plot artifact payload with `image_artifacts=[]` and do not update the source result index entry.

## Renderer Policy

B22 uses `builtin_svg` as the default renderer. This avoids introducing a new packaged runtime dependency while still producing a real SVG artifact.

Renderer dependency behavior:

- `builtin_svg`: passed, no external dependency.
- `matplotlib_png`: detect-first only. If matplotlib is missing, returns `matplotlib_missing_for_survival_plot_renderer`.
- `r_survminer`: not configured and blocked.

No renderer path performs auto-install.

## Artifact Contract

Generated plot artifacts include:

- `plot_id`
- `plot_type`
- `source_result_id`
- `source_result_semantics`
- `source_task_type`
- `plot_semantics`
- `plot_artifact_scope=formal_survival_real_plot_artifact`
- `input_package_id`
- `task_run_id`
- `parameters_manifest`
- `plot_spec_artifact`
- `image_artifacts`
- `table_artifacts`
- `engine_name=biomedpilot_survival_svg_renderer`
- `engine_version`
- `dependency_snapshot`
- `warnings`
- `blockers`
- `created_at`
- `schema_version`

The generated manifest is written under:

- `results/plots/survival/<plot_id>_manifest.json`

The generated SVG image is written under:

- `results/plots/survival/<plot_id>.svg`

The source result retains:

- `result_semantics=formal_computed_result`
- `report_ready_eligible=False`

## UI Changes

Analysis Center now shows:

- `KM real plot artifact`
- `Cox real forest plot artifact`
- renderer status and disabled reasons
- `generate_km_plot`
- `generate_cox_plot`

Action rows are enabled only when the corresponding real plot gate passes. Disabled rows show the exact source-result or renderer blocker.

Settings dependency detection includes:

- survival builtin SVG renderer
- optional matplotlib renderer status
- detect-first/no-install messaging

## Boundaries Preserved

- Spec-only KM/Cox plot artifact functions remain available for earlier B13/B14 tests.
- Preflight/testing/imported/exploratory sources cannot generate formal survival real plot artifacts.
- Plot artifacts inherit source semantics and cannot upgrade source results.
- Plot generation failure does not alter the statistical result.
- No survival report-ready package is generated in B22.
- No clinical conclusion, prognosis, treatment advice, risk group, or risk score is produced.

## Validation Summary

Focused validation completed during implementation:

- `python3 -m pytest tests/bioinformatics/test_survival_real_plot_renderer.py tests/bioinformatics/test_km_plot_artifact.py tests/bioinformatics/test_cox_plot_artifact.py tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_capability_map.py -q`
  - 30 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task_center_userized_main_surface_and_diagnostics"`
  - 1 passed, 111 deselected

Full validation results are recorded in the final task report after package and smoke checks.

Full validation completed:

- `git diff --check`
  - passed
- `python3 -m pytest tests/bioinformatics -q -k "plot or survival or cox or km or analysis_ui or capability_map"`
  - 122 passed, 507 deselected
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or settings or results_browser"`
  - 14 passed, 98 deselected
- `python3 -m pytest tests/bioinformatics -q`
  - 629 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - 269 passed
- `python3 -m app.main --smoke-test`
  - passed
- `python3 scripts/package_app.py --smoke-test`
  - passed
- `open -W -n dist/BioMedPilot.app --args --smoke-test`
  - passed
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`
  - passed

## Conclusion

B22 is implemented as a gated real SVG plot artifact renderer for formal KM/Cox results. It does not activate survival report-ready, risk score, clinical interpretation, or any enrichment/DEG capability.

Recommended next stage: B23 Full Integrated Report Gate and Export Package planning.
