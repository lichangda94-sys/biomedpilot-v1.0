# Stage 0.5 Old Markdown Deletion Audit

Date: 2026-05-27

Worktree: `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`

## Scope

This audit identifies old Markdown documents that can be deleted or consolidated in a later cleanup pass.

No files were deleted in this audit.

## Current Document Footprint

- `docs/`: 462 tracked/untracked files observed, about 4.1 MB.
- `docs/archive/legacy_handoff_20260513/`: 100 Markdown files, about 708 KB.
- `docs/bioinformatics/`: 144 files, about 1.2 MB.
- `docs/ui/`: about 652 KB.
- `docs/handoff/`: about 212 KB.
- `docs/meta_dev_reports/`: about 136 KB.
- `docs/release/`: about 60 KB.

## Delete Candidate Set A - Safe If Git History Is Enough

These are the strongest deletion candidates:

- `docs/archive/legacy_handoff_20260513/**`

Reasoning:

- The directory is already an archive created on 2026-05-13.
- The archive README says these were old Markdown audit, stage, migration and handoff files.
- The matching cleanup report says this archive was a move-only preservation step, not active runtime documentation.
- Current app code and tests do not depend on these Markdown files.
- Most external references are archive index or cleanup provenance references, not runtime dependencies.

Tradeoff:

- Deleting the directory removes convenient in-tree historical provenance.
- Git history still preserves the content.
- If a human still wants local searchable history, keep the archive but remove only exact duplicates.

## Delete Candidate Set B - Exact Duplicate

If Set A is not deleted, this duplicate can still be removed:

- `docs/archive/legacy_handoff_20260513/meta_dev_reports/ui_construction_preparation_report.md`

It has the same SHA-256 hash as:

- `docs/meta_dev_reports/ui_construction_preparation_report.md`

## Delete Candidate Set C - Superseded UIShell 2026-05-13 Reports

These can be deleted after confirming the 2026-05-19 UIShell audit remains the current reference:

- `docs/UIShell_handoff_report_20260513.md`
- `docs/UIShell_repair_audit_20260513.md`

Keep:

- `docs/UIShell_ui_design_progress_audit_20260519.md`

Reasoning:

- The 2026-05-19 report is newer and already says the UIShell branch should not be treated as Integration Preview or ReleaseBuild source.
- The two 2026-05-13 files are older repair/handoff snapshots.

## Delete Candidate Set D - Granular Meta Stage Reports

These have little standalone value once `Meta_handoff_report_20260513.md`, `meta_analysis_full_version_audit_2026-05-13.md`, and the active Meta docs are kept:

- `docs/meta_dev_reports/Meta_M4B_screening_workspace_report_20260513.md`
- `docs/meta_dev_reports/Meta_M4C_full_text_management_report_20260513.md`
- `docs/meta_dev_reports/Meta_M5_extraction_table_report_20260513.md`
- `docs/meta_dev_reports/Meta_M6_quality_assessment_report_20260513.md`
- `docs/meta_dev_reports/Meta_M7_analysis_plan_report_20260513.md`
- `docs/meta_dev_reports/Meta_M8_draft_report_generation_report_20260513.md`
- `docs/meta_dev_reports/Meta_M9_statistical_executor_preintegration_audit_20260513.md`
- `docs/meta_dev_reports/Meta_M10_statistical_result_state_gating_report_20260513.md`
- `docs/meta_dev_reports/Meta_M11_effect_size_normalization_report_20260513.md`
- `docs/meta_dev_reports/Meta_M12_pairwise_meta_executor_mvp_report_20260513.md`
- `docs/meta_dev_reports/Meta_M13_result_review_report_ready_transition_20260513.md`
- `docs/meta_dev_reports/Meta_M14_runtime_integration_readiness_audit_20260513.md`

Recommended handling:

- Prefer deletion only after a short Meta summary index is kept or confirmed unnecessary.
- Do not delete `docs/meta_dev_reports/Meta_handoff_report_20260513.md` in this pass.
- Do not delete `docs/meta_analysis_full_version_audit_2026-05-13.md`; it still documents the active-vs-legacy boundary.

## Delete Candidate Set E - Old Integration / Release Packaging Snapshots

These are old package readiness snapshots and can be deleted if the project no longer needs per-package historical evidence:

- `docs/integration/Integration_package_readiness_audit_20260513.md`
- `docs/integration/Integration_package_readiness_audit_rerun_20260513.md`
- `docs/integration/Integration_preview_packaging_readiness_recheck_20260513.md`
- `docs/release/ReleaseBuild_integration_preview_package_report_20260513.md`
- `docs/release/ReleaseBuild_integration_preview_package_report_2_20260514.md`

Recommended handling:

- Keep newer or current runtime acceptance docs such as PaddleOCR and current ReleaseBuild candidate reports.
- If deleting these, preserve any package path / source commit / readiness decision that is still needed in a consolidated release index.

## Delete Candidate Set F - Early Bioinformatics B1-B5 Userization Reports

These are older stage reports now superseded by later B8-B44 implementation reports and ReleaseBuild carry-over reports:

- `docs/bioinformatics/stage_B1A_data_selection_convergence_20260513.md`
- `docs/bioinformatics/stage_B1B_chinese_topic_search_page_20260513.md`
- `docs/bioinformatics/stage_B1C_standardization_page_userization_20260513.md`
- `docs/bioinformatics/stage_B1D_analysis_task_center_userization_20260513.md`
- `docs/bioinformatics/stage_B1E_results_report_userization_20260513.md`
- `docs/bioinformatics/stage_B1_user_test_entry_audit_20260513.md`
- `docs/bioinformatics/stage_B1_user_test_closure_report_20260513.md`
- `docs/bioinformatics/stage_B2_deg_config_preflight_20260513.md`
- `docs/bioinformatics/stage_B3_imported_deg_result_browser_20260513.md`
- `docs/bioinformatics/stage_B5_6_local_multifile_import_handoff_fix_20260513.md`
- `docs/bioinformatics/stage_B5_7_recognition_standardization_gate_fix_20260513.md`
- `docs/bioinformatics/stage_B5_result_report_loop_stabilization_20260513.md`

Recommended handling:

- Do not delete these in the same pass as integration snapshots unless the old integration docs that reference B5 are deleted or updated first.
- Keep later Bioinformatics B8-B44 docs for now; they are the current audit trail for active ReleaseBuild functionality.

## Do Not Delete In This Cleanup Pass

Keep these categories:

- `docs/handoff/Global_Development_Manual.md`
- current architecture and module-boundary docs
- `docs/meta_analysis_full_version_audit_2026-05-13.md`
- `docs/vocabulary/**` and active medical term governance docs
- `docs/user_testing/**`
- latest Bioinformatics B8-B44 stage reports
- current ReleaseBuild candidate and packaging gate reports
- AI Gateway direct-call audit docs until direct legacy paths are retired
- LabTools reports that still govern local integration boundaries

## Existing Worktree Caveat

The worktree had a pre-existing non-doc code change during final status review:

- `app/bioinformatics/survival_clinical/risk_score_plot_schema.py`

It also had an existing untracked file:

- `docs/release/ReleaseBuild_handoff_report_20260513.md`

This audit did not modify or classify those code changes. The untracked release handoff file looks stale and should be handled separately: either delete it as a local obsolete snapshot or intentionally add it after reviewing its content.

## Recommended Cleanup Order

1. Delete `docs/archive/legacy_handoff_20260513/**` if local historical Markdown search is no longer required.
2. Delete the two old UIShell 2026-05-13 reports and keep the 2026-05-19 audit.
3. Consolidate or delete old Meta M4B-M14 per-stage reports.
4. Consolidate or delete old Integration / Release package snapshots.
5. Delete early Bioinformatics B1-B5 userization reports only after old integration references are removed or accepted as historical dead links in Git history.
