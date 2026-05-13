# Integration Package Readiness Audit Rerun - 2026-05-13

## Decision

`READY_FOR_RELEASEBUILD_PREVIEW_PACKAGING`

Current `dev/integration` source at `f2b5679` is suitable to hand off to ReleaseBuild for a controlled first `BioMedPilot Integration Preview.app` desktop test package.

This decision applies only to the current Integration-approved source. It does not approve whole-branch merges from Bioinformatics, Meta, LabTools, UIShell, or ReleaseBuild; it does not approve overwriting `/Users/changdali/Desktop/BioMedPilot Dev.app` or any existing formal `BioMedPilot.app`; it does not approve remote push.

No packaging was run during this audit.

## Current branches and status

| Area | Branch | HEAD | Dirty status | MainLine comparison |
| --- | --- | --- | --- | --- |
| MainLine baseline | `stable/mainline` | `fd0b9a0` | clean | stable baseline |
| Integration candidate | `dev/integration` | `f2b5679` | clean | `stable-only/module-only = 30/19` |
| Bioinformatics | `dev/bioinformatics` | `6745d7c` | untracked `docs/bioinformatics/Bioinformatics_handoff_report_20260513.md` | `88/13`; branch too broad/stale for whole merge |
| Meta | `dev/meta-analysis` | `5eaf2b1` | untracked `docs/meta_dev_reports/Meta_handoff_report_20260513.md` | `46/26`; branch too broad for whole merge |
| LabTools | `dev/labtools` | `44597bb` | clean | `30/25`; branch broader than L6A.1 preview scope |
| UIShell | `dev/ui-shell` | `a2084a2` | clean | `30/3`; source branch is not preview source |
| ReleaseBuild | `dev/release-internal-test` | `d2bc191` | untracked `docs/release/ReleaseBuild_handoff_report_20260513.md` | `30/7`; packaging executor reference only |

## Module decisions

| Module | Decision | Preview content allowed | Not allowed |
| --- | --- | --- | --- |
| MainLine baseline | `YES` | Stable shell baseline and comparison reference. | No direct adoption of module dev branches. |
| Bioinformatics | `YES` | B5 result/report loop scoped integration already present in Integration source. | Do not merge whole `dev/bioinformatics`; do not open real DEG executor, volcano, heatmap, enrichment, GSEA, survival, correlation, network, AI, or download features. |
| Meta | `YES` | M10-M13 carry-over user flow in Integration source: effect-size normalization preview, pairwise fixed-effect executor MVP, computed/user review/report_ready gate, draft report summary. | Do not merge whole `dev/meta-analysis`; do not present testing executor output as publication/clinical/regulatory/production result. |
| LabTools | `YES` | L6A.1 ROI export package hardening already present in Integration source. | Do not merge whole `dev/labtools`; no automatic ROI, automatic cell counting, grayscale/WB/gel, OpenCV, scikit-image, ImageJ/Fiji, AI, network, database, autosave/history, batch export, or formal report system. |
| UIShell | `YES-DOCS-ONLY` | Repair audit and handoff can inform future shell work. Current Integration UI tests pass without bringing in `dev/ui-shell` as source. | Do not use `dev/ui-shell` as preview source; it is stale against MainLine/Integration and reports only 2 workspace entries in smoke. |
| ReleaseBuild | `YES-DOCS-ONLY / PACKAGING-READY REFERENCE` | Can execute packaging after this audit, using Integration-approved source only. | ReleaseBuild must not make business maturity decisions and must not package from module dev branches. |

## Blocking status

No current P0/P1 blocker prevents ReleaseBuild from generating a controlled Integration Preview package from `dev/integration` at `f2b5679`.

Items that remain explicitly blocked from entering the package:

- whole `dev/bioinformatics`, `dev/meta-analysis`, `dev/labtools`, `dev/ui-shell`, or `dev/release-internal-test` source branches;
- UIShell branch source changes as a package source;
- ReleaseBuild as a business maturity source;
- formal scientific/clinical/regulatory/production claims for Bioinformatics, Meta, or LabTools outputs;
- any desktop overwrite of existing Dev or formal app bundles.

## Scoped-fix status

No additional scoped fix is required before ReleaseBuild preview packaging from current Integration source.

Recently completed scoped fixes now reflected in this audit:

- Bioinformatics B5 result/report loop scoped integration is present and verified.
- LabTools L6A.1 ROI export hardening scoped integration is present and verified.
- Meta M10-M13 user-flow validation and active UI wiring/failure-audit fixes are present and verified in Integration.
- Meta M10-M13 MainLine carry-over precheck is documented separately; that is for MainLine promotion, not required for Integration Preview packaging.

## Recent report paths

| Area | Reports used |
| --- | --- |
| Project control / global rules | `docs/handoff/BioMedPilot_v1_current_handoff_summary_20260513.md`; `docs/handoff/Global_Development_Manual.md` |
| MainLine | `docs/handoff/MainLine_current_baseline_20260513.md` |
| Bioinformatics | `docs/bioinformatics/stage_B5_result_report_loop_stabilization_20260513.md`; `docs/integration/Integration_bioinformatics_b5_scoped_integration_20260513.md`; module handoff exists in Bioinformatics worktree as untracked `docs/bioinformatics/Bioinformatics_handoff_report_20260513.md` |
| Meta | `docs/meta_dev_reports/Meta_M10_statistical_result_state_gating_report_20260513.md`; `Meta_M11_effect_size_normalization_report_20260513.md`; `Meta_M12_pairwise_meta_executor_mvp_report_20260513.md`; `Meta_M13_result_review_report_ready_transition_20260513.md`; `docs/integration/Integration_i_meta_2_m10_m13_user_flow_validation_20260513.md`; `docs/integration/Integration_j_meta_m10_m13_user_path_fix_20260513.md`; `docs/integration/Integration_meta_m10_m13_mainline_scoped_carryover_precheck_20260513.md` |
| LabTools | `docs/stage_labtools_l6a_image_roi_export_package_report.md`; `docs/stage_labtools_l6a1_image_roi_export_hardening_report.md`; `docs/integration/Integration_labtools_l6a1_scoped_integration_report_20260513.md` |
| UIShell | `docs/UIShell_repair_audit_20260513.md`; `docs/UIShell_handoff_report_20260513.md` |
| ReleaseBuild | `docs/release/ReleaseBuild_sync_from_MainLine_pre_package_validation_20260513.md`; `docs/release/ReleaseBuild_handoff_report_20260513.md` in ReleaseBuild worktree is untracked |

## Validation performed in this audit

Integration source at `f2b5679`:

- `git diff --check`: passed
- `python3 -m app.main --smoke-test`: passed, `git_head=f2b5679`, `workspace_entries=3`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_module_boundary_contract.py -q`: `5 passed`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`: `277 passed`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`: `130 passed`
- Meta M10-M13 targeted suite: `59 passed`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`: `178 passed`

Additional reference checks:

- UIShell `a2084a2`: smoke passed; `tests/ui` returned `46 passed, 87 skipped`; not selected as preview source.
- ReleaseBuild `d2bc191`: smoke passed; `tests/test_package_app.py tests/test_versioned_packaged_entry.py` returned `3 passed`; no packaging run.

## Recommended first Integration Preview package content

ReleaseBuild may package only:

- MainLine/Integration shell as represented by current `dev/integration` source;
- Bioinformatics B5 scoped result/report loop stabilization;
- LabTools L6A.1 ROI export package hardening;
- Meta M10-M13 Developer Preview/testing user flow;
- existing Developer Preview/testing disclaimers and module boundaries.

The package must be named and identified as Integration Preview:

- package name: `BioMedPilot Integration Preview.app`
- metadata / `CFBundleName` / `CFBundleExecutable`: must clearly say Integration Preview
- packaged smoke must pass
- package report must be generated by ReleaseBuild

## Not recommended for entry

- whole module dev branches;
- UIShell branch source;
- ReleaseBuild source as business logic;
- direct MainLine promotion without separate MainLine scoped apply validation;
- desktop overwrite of old Dev or formal app bundles;
- any user-facing claim that preview outputs are formal scientific conclusions.

## Next step

Yes, recommend the next step: ask ReleaseBuild to generate `BioMedPilot Integration Preview.app` from `dev/integration` at `f2b5679`, with the constraints above.

ReleaseBuild may proceed only after consuming this Integration audit and must produce a separate preview package report. Packaging remains forbidden in Integration.
