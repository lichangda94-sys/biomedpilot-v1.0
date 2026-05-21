# B16.5 Legacy Asset Pipeline UI Exposure

Date: 2026-05-21

## Scope

B16.5 exposes the B16 legacy absorption chain in the Analysis Center as a review-only diagnostic surface:

- B16 adapter manifests.
- B16.1 standardized asset candidate bundle.
- B16.2 materialized candidate assets.
- B16.3 repository manifest merge.
- B16.4 user-confirmed asset selection.

This stage does not enable a formal analysis runner and does not create analysis input repository entries, result index entries, plot artifacts, report packages, GSEA, survival, or clinical outputs.

## Implementation

- Added `legacy_asset_pipeline` to `build_analysis_center_state`.
- Added a review-only `legacy_asset_pipeline_review` action row.
- Added an Analysis Center `Legacy asset pipeline` table with artifact path, status, counts, blockers/warnings, and next-step guidance.
- Added tests for state purity, review-only action behavior, and UI rendering.

## Boundary

The UI explicitly records:

- `formal_analysis_enabled=False`
- `writes_analysis_input_repository=False`
- `writes_result_index=False`
- `report_ready_eligible=False`

Legacy assets remain acquisition and standardization inputs only. Formal DEG, ORA, GSEA, KM, Cox, plot, and report-ready gates still require their own B8/B9/B10/B11/B12/B13/B14 contracts.

## Validation

Targeted validation was added for:

- Analysis Center state side-effect safety.
- Legacy pipeline artifact discovery.
- Action matrix review-only behavior.
- Workflow page visibility and copy boundaries.
