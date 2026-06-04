# LabTools ImageJ Macro Audit - 2026-06-04

## Scope

Source branch audited: `dev/labtools`.

Source commits:

- `2fa005d Add migration streak ROI ImageJ workflow`
- `f77bfe4 Add planned ImageJ image workflows`

Target runtime: Integration `app/labtools/image_analysis/**` and LabTools cell image analysis UI.

This audit intentionally does not merge or copy the standalone `labtools/` package layout. Only cell experiment image-recognition macro content that maps to the current Integration runtime is adapted.

## Accepted Into Integration

| Source content | Integration status | Reason |
|---|---|---|
| `generic_particle_analysis` | Included as ImageJ gated workflow and macro template | Fits cell image particle/cell counting preparation. Produces `generic_particle_results.csv`; requires threshold review. |
| `migration_streak_roi` | Included as ImageJ gated workflow and macro template | Fits migration/scratch ROI analysis. Included with manual review requirement because threshold strategy still needs real-image validation. |
| `roi_intensity_batch` | Included as gated workflow and macro template | Useful for ROI intensity workflows. If no ROI zip is selected, macro writes `missing_roi_zip` blocker instead of a formal result. |
| `cell_skeleton_morphology` | Included as Fiji-required gated workflow and macro template | Requires Fiji Skeletonize / Analyze Skeleton capability. Registered with `fiji` minimum engine requirement. |

Integration changes:

- Registered new task types in `app/labtools/image_analysis/analysis_task.py`.
- Added runtime macro renderers in `app/labtools/image_analysis/cell_imagej_workflows.py`.
- Added built-in macro registry entries in `app/labtools/image_analysis/macro_registry.py`.
- Added static built-in macro templates under `app/labtools/image_analysis/macros/cell_experiment/`.
- Added UI template selector and load action to the cell ImageJ macro preparation panel.
- Added tests for registry, renderer output, run-request generation, and UI template loading.

## Deferred Or Returned To Neptors

| Source content | Decision | Required follow-up |
|---|---|---|
| `dot_blot_grid` / `labtools/western_blot/imagej.py` | Not included in this cell-image batch | Move to a separate WB/protein-image remediation batch with WB UI wiring and sample validation. |
| `labtools/__main__.py` CLI additions | Not included | Current Integration app does not use the standalone package CLI. Provide an Integration-specific CLI or app action plan if needed. |
| Standalone README/docs deltas | Not included | Rewrite against Integration app paths and UI gates before adding docs. |
| ROI name preservation in ROI intensity macro | Needs improvement | Current Integration-safe renderer uses deterministic `roi_<index>` names. Neptors should validate a reliable ImageJ ROI Manager name retrieval method before requiring original ROI labels. |
| `migration_streak_roi` threshold defaults | Needs sample validation | Validate on representative scratch/migration images and provide recommended threshold presets per staining/background type. |
| `cell_skeleton_morphology` Fiji plugin dependency | Needs engine validation | Provide a Fiji sample-run checklist proving Skeletonize / Analyze Skeleton commands are present and output CSVs are stable. |

## Current Gate Statement

The accepted workflows are available for ImageJ/Fiji call preparation and RunRequest generation. They do not yet represent production-grade automated cell-image interpretation. Each output still requires external engine availability, threshold/ROI validation, and manual scientific review.
