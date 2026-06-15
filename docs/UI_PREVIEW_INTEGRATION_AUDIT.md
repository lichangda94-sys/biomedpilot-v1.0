# UI Preview Integration Audit

Generated: `2026-06-15`

Scope: UI/preview boundary audit only. This pass did not refactor the UI, add a new analysis page, activate full mode, migrate additional modules, or change app-dev dependencies.

## 1. UI Refactor Status

No UI refactor was performed. The change is limited to read-only catalog/state metadata and tests that prevent preview surfaces from confusing evidence visibility with production execution readiness.

## 2. UI Consumption Boundary Status

Current status: `passed` for preview boundary controls.

The UI state is built through `app/bioinformatics/analysis_ui/state.py`, which calls `build_standard_analysis_package_catalog()` from `app/analysis_runtime/package_catalog.py`. The catalog source policy is:

```text
result_index_standard_result_package_artifacts_only
```

The package catalog does not scan arbitrary module folders and `build_standard_analysis_package_detail()` is constrained to the standard result package directory.

## 3. Package Catalog Coverage

Covered states:

- mock/testing standard result packages
- lite/testing standard result packages
- blocked full standard result packages
- full/formal standard-worker packages as review-only scoped evidence
- legacy sidecar packages as review-only, never migration evidence

New preview fields exposed per catalog row:

- `preview_readiness`
- `preview_display_status`
- `preview_review_only`
- `global_full_ready_eligible`

All catalog rows remain `ui_execution_eligible=False` by default. A passed full/formal standard package can support scoped migration evidence only; it does not imply UI execution readiness or global full activation.

## 4. Analysis Center State Coverage

`build_analysis_center_state()` now exposes:

- `preview_readiness_matrix`
- `preview_readiness_rows`

The matrix covers:

- standard package catalog
- results browser
- module-specific detail views
- legacy sidecar detail view
- survival preview
- r-bio-full environment evidence
- blocked full modules

The matrix source policy is:

```text
ui_preview_reads_catalog_and_gate_state_no_module_private_r_outputs
```

## 5. Results Browser Coverage

The results browser state reads result-index entries and joins them to catalog rows by `result_id`. It displays standard package status, validation status, path, and artifact counts from catalog rows. It does not read R package internal output folders or module-private survival full outputs.

## 6. Module-Specific Detail Views Coverage

Module detail views are covered through standard package detail metadata and frontend consumption gate rows. Current status has no pending detail-view migration blockers. Detail views must continue to use package catalog/detail outputs for tables, plots, reports, logs, provenance, worker boundary, and validation state.

## 7. Legacy Sidecar Review-Only Status

Legacy DEG/survival sidecar producers remain transitional and review-only. They cannot count as:

- UI execution readiness
- standard-worker migration evidence
- full/formal production activation

Catalog policy labels legacy sidecars with `legacy_sidecar_review_only_not_ui_execution_readiness`.

## 8. Survival Preview Status

Current code evidence includes scoped survival `survival_minimal_v1` standard-worker migration evidence. Preview must display it only as scoped/review-only evidence while global full activation remains blocked.

Required preview status:

```text
scoped_survival_minimal_v1_review_only_global_activation_blocked
```

Survival must not be displayed as global full-ready or production-ready. Expanded survival methods remain outside the scoped evidence.

## 9. Preview Can Display

Preview may display:

- mock standard packages
- lite standard packages
- blocked full packages
- scoped survival `survival_minimal_v1` evidence as review-only
- r-bio-full evidence as environment evidence only
- provenance, runtime, worker boundary, validation state, input hash, parameter hash, random seed, command, and artifact manifest metadata

## 10. Preview Must Not Display As Ready

Preview must not display the following as production-ready:

- global full activation
- blocked full modules
- scaffold or blocked full packages
- lite/testing packages
- legacy sidecar packages
- r-bio-full evidence alone
- survival scoped evidence beyond `survival_minimal_v1`
- module-private output folders or copied artifacts

Current audit result: no full-ready preview misreport was found after adding explicit preview readiness fields and matrix rows.

## 11. Preview Readiness Matrix

| Surface | Current Status | Boundary | Production Claim |
| --- | --- | --- | --- |
| standard_package_catalog | passed | result-index registered standard packages only | no global full-ready |
| results_browser | passed | standard package catalog rows only | no global full-ready |
| module_detail_views | passed | standard package detail, no module-private output scan | no global full-ready |
| legacy_sidecar_detail_view | review_only | legacy sidecar review-only | no migration/full evidence |
| survival_preview | scoped_survival_minimal_v1_review_only_global_activation_blocked | scoped survival evidence only | no global full-ready |
| r_bio_full_environment_evidence | evidence_restored_review_only_global_activation_blocked | environment evidence only | no global full-ready |
| blocked_full_modules | blocked_modules_review_only | blocked module diagnostics only | not production runnable |

## 12. Next UI Audit Trigger

Run the next UI/preview audit when any of these happen:

- a new full/formal module migration is registered
- `--require-full-ready` is expected to pass
- a new analysis result detail page is added
- legacy sidecar display is changed
- package catalog fields or result-index schema change
- spatial transcriptomics, docking, or molecular dynamics preview is introduced
