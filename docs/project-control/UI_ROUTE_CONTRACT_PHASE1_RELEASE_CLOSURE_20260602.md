# UI Route Contract Phase 1 Release Closure

- date: `2026-06-02`
- branch: `integration/release-bio-c1-ui-shell`
- closure_head: `b427a7dfbd5f7ee7001152c4789d92dba3af5870`
- scope: Shell freeze, Bioinformatics C1, Meta Analysis, LabTools, route-contract rollup, latest preview package gate.

## Closure Summary

Phase 1 has rebuilt the release route-contract evidence for the accepted UIShell baseline and the three module adapters. The current HEAD contains no route-contract `broken` rows and no `stale-code-proof` batches in the rollup.

| Area | Evidence commit | Rows | Connected | Disabled with reason | Broken | Runtime status |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Shell + Centers | `e837762` | 28 | 23 | 5 | 0 | Frozen shared shell; Welcome/Home/About/Settings/Sidebar/Centers live-clicked. |
| Bioinformatics C1 | `fc2cdb2` | 219 | 158 | 61 | 0 | Mature 7-step Bio pages retained; GEO/Local/TCGA/GTEx acquisition/data-check and formal DEG/ORA subset connected. |
| Meta Analysis | `bc30258` | 71 | 49 | 22 | 0 | Mature Meta IA retained; PubMed handoff, import/dedup, screening, fulltext/quality/analysis gates audited. |
| LabTools | `b427a7d` | 159 | 144 | 15 | 0 | Accepted LabTools home/second-level structure retained; calculators/reagents/cell/WB/qPCR adapters audited. |
| Full rollup | `b427a7d` | 477 | 374 | 103 | 0 | `prior-proof-docs-only-head-drift=24`; no code-path drift after batch evidence. |

## Route Contract Rollup

Current rollup:

- Report: `docs/project-control/UI_ROUTE_CONTRACT_PHASE1_ROLLUP.md`
- JSON: `docs/project-control/UI_ROUTE_CONTRACT_PHASE1_ROLLUP.json`
- Batch count: `24`
- Row count: `477`
- Connected: `374`
- Disabled with reason: `103`
- Broken: `0`
- Stale code proof: `0`

The rollup classifies all batches as `prior-proof-docs-only-head-drift` at closure time because evidence was refreshed per module and then committed as documentation. The rollup checks recorded implementation paths with `git diff evidence_head..HEAD -- app/ tests/`; no implementation paths changed after the evidence commits.

## Verification Commands

| Area | Command | Result |
| --- | --- | --- |
| Shell tests | `QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/ui/test_login_page.py tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/ui/test_settings_shell.py tests/ui/test_shell_centers.py tests/ui/test_release_ui_button_contracts.py` | `29 passed` |
| Shell preview validation | `QT_QPA_PLATFORM=offscreen python3 scripts/phase1_preview_startup_validation.py` | `14/14 clicks passed`; LaunchServices gate passed at `e837762` package validation. |
| Bio tests | Bio targeted UI/workflow/service pytest set | `254 passed` |
| Meta tests | Meta targeted UI/workflow pytest set | `71 passed` |
| LabTools tests | LabTools targeted UI/service pytest set | `187 passed` |
| App smoke | `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test` | passed through each module replay; latest source smoke must be rerun before final package handoff. |

## Accepted Disabled Gates

Disabled controls remain in the release route contract only when they expose a precise `disabledReason`.

| Module | Accepted disabled gates |
| --- | --- |
| Shell | Developer-preview support buttons, release build without explicit command, account/register/forgot-password placeholders. |
| Bioinformatics | Formal GSEA executor; survival KM/log-rank/Cox/risk-score/report-ready execution; non-light full-scale TCGA/GTEx download execution; non-DEG report-ready exports. |
| Meta Analysis | Source-file import when no source is selected, automatic screening/PRISMA shortcuts, downstream formal analysis/report/export controls without proven runtime schema. |
| LabTools | Immuno/Absorbance and IHC runtime pages; image/external-engine actions without proven dependency gate; optional automation actions without service proof. |

## Screenshot Evidence

Representative screenshot directories:

- Shell: `docs/ui/runtime_screenshots/20260602_phase1_preview_startup/`
- Bioinformatics: `docs/ui/runtime_screenshots/20260602_bio_batch8_visible_buttons/`
- Meta Analysis: `docs/ui/runtime_screenshots/20260602_meta_batch4_pubmed_handoff/`, `docs/ui/runtime_screenshots/20260602_meta_batch6_screening_decisions/`, `docs/ui/runtime_screenshots/20260602_meta_batch7_fulltext_extraction/`, `docs/ui/runtime_screenshots/20260602_meta_batch8_quality_assessment/`, `docs/ui/runtime_screenshots/20260602_meta_batch9_analysis_tasks/`
- LabTools: `docs/ui/runtime_screenshots/20260602_labtools_batch2_route_contract/`, `docs/ui/runtime_screenshots/20260602_labtools_batch3_cell_experiments/`, `docs/ui/runtime_screenshots/20260602_labtools_batch4_protein_wb/`, `docs/ui/runtime_screenshots/20260602_labtools_batch5_secondary_remainder/`

## Latest Preview Package Gate

The latest preview package was rebuilt at the closure HEAD and passed:

```bash
QT_QPA_PLATFORM=offscreen python3 scripts/package_app.py --app-name "BioMedPilot Integration Preview" --smoke-test
codesign --verify --deep --strict --verbose=2 "dist/BioMedPilot Integration Preview.app"
open -W -n "dist/BioMedPilot Integration Preview.app" --args --gui-startup-check --gui-startup-check-output /tmp/biomedpilot_phase1_release_closure_b427a7d_gui_startup.json
```

Observed package state:

- `BioMedPilotGitHead`: `b427a7d`.
- `CFBundleExecutable`: `BioMedPilotIntegrationPreview`.
- Launcher architecture: `Mach-O 64-bit executable arm64`.
- Code signature: `valid_on_disk`.
- Direct packaged launcher smoke: `passed`.
- LaunchServices startup JSON: `status=passed`, `window_visible=true`, `window_active=true`, active title `BioMedPilot / 医研智析`, window size `1120x720`.
- Shell live-click validation at closure package: `14/14` passed, failed clicks `0`, visible disabled buttons without reason `0`.
- Evidence report: `docs/release_validation/20260602_phase1_preview_startup.md`.

## Closure Decision

Phase 1 route-contract remediation is ready for user visual review and final release-build handoff from the current preview package.

Phase 1 does not claim that every scientific backend is production-complete. It claims that every visible route/button in scope is contract-classified and either connected by live-click evidence or disabled with a documented reason.
