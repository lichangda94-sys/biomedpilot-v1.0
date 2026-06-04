# LabTools ImageJ Macro Audit - 2026-06-04

## Scope

Source branch audited: `dev/labtools`.

Source commits:

- `2fa005d Add migration streak ROI ImageJ workflow`
- `f77bfe4 Add planned ImageJ image workflows`
- `c418eba Fix gated cell ImageJ macro integration scope`

Target runtime: Integration `app/labtools/image_analysis/**` and LabTools cell image analysis UI.

This audit intentionally does not merge or copy the standalone `labtools/` package layout. Only cell experiment image-recognition macro content that maps to the current Integration runtime is adapted.

## Accepted Into Integration

| Source content | Integration status | Reason |
|---|---|---|
| `generic_particle_analysis` | Included as ImageJ gated workflow and macro template | Fits cell image particle/cell counting preparation. Produces `generic_particle_results.csv`; requires threshold review. |
| `migration_streak_roi` | Included as ImageJ gated workflow and macro template | Fits migration/scratch ROI analysis. Included with manual review requirement because threshold strategy still needs real-image validation. |
| `roi_intensity_batch` | Included as gated workflow and macro template | Useful for ROI intensity workflows. If no ROI zip is selected, macro writes `missing_roi_zip` blocker instead of a formal result. |
| `cell_skeleton_morphology` | Included as Fiji-required gated workflow and macro template | Requires Fiji Skeletonize / Analyze Skeleton capability. Registered with `fiji` minimum engine requirement. |
| `c418eba` gated scope correction | Included as scoped runtime patch | Removes WB/CLI expansion from the accepted scope, updates migration-streak defaults, adds ImageJ/Fiji app path discovery, preserves ROI names with fallback, and adds a real-sample Fiji gate test. |

Integration changes:

- Registered new task types in `app/labtools/image_analysis/analysis_task.py`.
- Added runtime macro renderers in `app/labtools/image_analysis/cell_imagej_workflows.py`.
- Added built-in macro registry entries in `app/labtools/image_analysis/macro_registry.py`.
- Added static built-in macro templates under `app/labtools/image_analysis/macros/cell_experiment/`.
- Added UI template selector and load action to the cell ImageJ macro preparation panel.
- Added tests for registry, renderer output, run-request generation, and UI template loading.
- Added synthetic skeleton sample validation that runs only when a local Fiji/ImageJ executable is available.

## Deferred Or Returned To Neptors

| Source content | Decision | Required follow-up |
|---|---|---|
| `dot_blot_grid` / `labtools/western_blot/imagej.py` | Not included in this cell-image batch | Move to a separate WB/protein-image remediation batch with WB UI wiring and sample validation. |
| `labtools/__main__.py` CLI additions | Not included | Current Integration app does not use the standalone package CLI. Provide an Integration-specific CLI or app action plan if needed. |
| Standalone README/docs deltas | Not included | Rewrite against Integration app paths and UI gates before adding docs. |
| Representative migration/scratch threshold presets | Needs sample validation | `c418eba` conservative defaults are integrated, but Neptors should still validate presets by staining/background type on real images. |
| Fiji skeleton output stability on real user images | Needs engine validation | Synthetic sample gate is integrated; Neptors should provide real-image fixtures and expected CSV tolerances for production confidence. |

## Current Gate Statement

The accepted workflows are available for ImageJ/Fiji call preparation and RunRequest generation. They do not yet represent production-grade automated cell-image interpretation. Each output still requires external engine availability, threshold/ROI validation, and manual scientific review.
