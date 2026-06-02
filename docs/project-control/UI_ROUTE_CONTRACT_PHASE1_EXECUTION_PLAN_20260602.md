# UI Route Contract Phase 1 Execution Plan

- date: `2026-06-02`
- branch: `integration/release-bio-c1-ui-shell`
- planning_head: `585aa1d017c07256417c55587586d97fb767fd32`
- scope: shared Shell freeze, module adapter route contracts, live-click verification, screenshot evidence, preview package gate.

## Purpose

Phase 1 is the stabilization stage before the next release preview. It must prove that the accepted UI Shell baseline is frozen and that Bioinformatics, Meta Analysis, and LabTools are entered through module adapters with button-level route contracts.

This stage is not a broad UI redesign and not a whole-branch migration. High-fidelity UIShell pages stay as the visual baseline. Old pages may provide backend services or adapters, but must not replace mature gated pages.

## Current Evidence Snapshot

The worktree already contains Shell, Bioinformatics, Meta Analysis, and LabTools route-contract evidence. The current HEAD has advanced through later docs-only and scoped adapter commits, so the release gate must refresh contract evidence at the current HEAD before claiming release readiness.

| Area | Current evidence files | Rows | Connected | Disabled with reason | Broken | Evidence caveat |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Shell + Centers | `UI_ROUTE_CONTRACT_PHASE1_BATCH0.*` | 28 | 23 | 5 | 0 | Needs replay at current HEAD after later commits. |
| Bioinformatics C1 | `UI_ROUTE_CONTRACT_BIO_BATCH1/4/5/6/7/8/9/10/11/12/13/14.*`, `UI_ROUTE_CONTRACT_BIO_C1_CLOSURE_MATRIX.*` | 219 | 158 | 61 | 0 | Mature 7-step pages retained; several formal executors remain intentionally gated. |
| Meta Analysis | `UI_ROUTE_CONTRACT_META_BATCH3/4/5/6/7/8/9.*` | 71 | 49 | 22 | 0 | PubMed handoff and reviewer workflow are connected; downstream formal analysis/report/export remain partially gated. |
| LabTools | `UI_ROUTE_CONTRACT_LABTOOLS_BATCH2/3/4/5.*` | 159 | 144 | 15 | 0 | Accepted home/secondary structure is present; qPCR currently uses an existing adapter surface, not a new high-fidelity visual page. |

## Phase 1 Release Rule

A button or route can be marked `connected` only when the current HEAD provides all of the following:

| Requirement | Proof |
| --- | --- |
| Stable visible control | `objectName` or stable route key is recorded in the contract row. |
| Handler or target | Click reaches the expected page, adapter, service, or state transition. |
| Runtime effect | A service call, artifact, manifest, result index, report-ready package, or state transition is observed. |
| Live-click evidence | A script or UI test clicks the control and asserts the effect. |
| Screenshot evidence | The runtime page screenshot is stored under `docs/ui/runtime_screenshots/`. |

Disabled controls are acceptable only when the control is disabled and the contract records a precise `disabledReason`. Empty enabled buttons, missing handlers, missing target pages, old-page substitutions, and placeholder controls without reason are release blockers.

## Execution Batches

### Batch A: Current-HEAD Contract Replay

Goal: refresh all existing route-contract JSON/Markdown evidence at `585aa1d` or the latest execution HEAD.

Commands:

```bash
QT_QPA_PLATFORM=offscreen python3 scripts/ui_route_contract_audit.py
QT_QPA_PLATFORM=offscreen python3 scripts/ui_route_contract_bio_batch8_visible_buttons.py
QT_QPA_PLATFORM=offscreen python3 scripts/ui_route_contract_bio_c1_closure_matrix.py
QT_QPA_PLATFORM=offscreen python3 scripts/ui_route_contract_meta_batch3.py
QT_QPA_PLATFORM=offscreen python3 scripts/ui_route_contract_meta_batch4_pubmed_handoff.py
QT_QPA_PLATFORM=offscreen python3 scripts/ui_route_contract_meta_batch5_dedup_screening.py
QT_QPA_PLATFORM=offscreen python3 scripts/ui_route_contract_meta_batch6_screening_decisions.py
QT_QPA_PLATFORM=offscreen python3 scripts/ui_route_contract_meta_batch7_fulltext_extraction.py
QT_QPA_PLATFORM=offscreen python3 scripts/ui_route_contract_meta_batch8_quality_assessment.py
QT_QPA_PLATFORM=offscreen python3 scripts/ui_route_contract_meta_batch9_analysis_tasks.py
QT_QPA_PLATFORM=offscreen python3 scripts/ui_route_contract_labtools_batch2.py
QT_QPA_PLATFORM=offscreen python3 scripts/ui_route_contract_labtools_batch3_cell_experiments.py
QT_QPA_PLATFORM=offscreen python3 scripts/ui_route_contract_labtools_batch4_protein_wb.py
QT_QPA_PLATFORM=offscreen python3 scripts/ui_route_contract_labtools_batch5_secondary_remainder.py
```

Exit gate:

- No `broken` rows.
- No enabled control without `button_behavior`.
- No disabled control without `disabledReason`.
- Any stale batch that is not rerun must be explicitly marked as prior evidence, not current release evidence.

### Batch B: Shell Freeze Replay

Goal: prove that Welcome, Home/Dashboard, Sidebar, About, Settings, Centers, shared primitives, logo/icon identity, and module adapter entries have not regressed.

Required checks:

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest -q \
  tests/ui/test_login_page.py \
  tests/ui/test_module_selection.py \
  tests/ui/test_sidebar.py \
  tests/ui/test_settings_shell.py \
  tests/ui/test_shell_centers.py \
  tests/ui/test_release_ui_button_contracts.py

QT_QPA_PLATFORM=offscreen python3 scripts/phase1_preview_startup_validation.py
```

Screenshot review must include:

- Welcome
- Settings from Welcome
- About from Welcome
- Home/Dashboard
- Sidebar route pages
- Bioinformatics adapter entry
- Meta Analysis adapter entry
- LabTools adapter entry

Exit gate:

- Runtime screenshots match the accepted UIShell baseline instead of the older login/home/about/settings fallback.
- The packaged app opens through LaunchServices and remains visible.

### Batch C: Bioinformatics C1 Replay

Goal: keep the mature UIShell 7-step Bio pages and revalidate each visible control against the current adapters.

Page order:

1. Project Home
2. Data Source
3. Data Check & Preparation
4. Group & Design
5. Analysis Tasks
6. Result & Report
7. Report Export

Required live paths:

| Path | Required proof |
| --- | --- |
| `GSE6004` | GEO search/download, recognition, readiness artifact, expected `ready_with_warnings` or precise blocker. |
| `GSE153659` | GEO search/download, recognition, readiness artifact, expected readiness or precise expression-matrix blocker. |
| Local source | Acquisition/request artifact and recognition handoff. |
| TCGA/GTEx | Metadata preview, download-plan artifact, light-validation artifact, Data Check recognition/readiness when available. |
| Formal DEG | Parameter confirmation, dependency check, controlled run, result review, plot artifact, report-ready package, export gate. |
| ORA/GSEA | ORA connected where schema/runtime proof exists; GSEA disabled unless executor and report schema are proven. |
| Survival/clinical | Preflight/detect connected; KM/log-rank/Cox/risk score disabled unless formal executor and report-ready gate are proven. |

Exit gate:

- 7-step visual shell remains intact.
- No old Bio pages replace the mature gated shell.
- Every Bio button is `connected` or disabled with reason in the current-head contract.

### Batch D: Meta Analysis Replay

Goal: revalidate the mature Meta target IA and keep downstream formal gaps explicit.

Required live path:

```text
("thyroid cancer" OR "thyroid carcinoma" OR 甲状腺癌) AND (adiponectin OR 脂联素)
```

Required proof:

- PubMed search returns candidate records or records a precise network/API blocker.
- Selected candidates import into literature library.
- Dedup queue and screening queue artifacts are written.
- Reviewer decisions are saved by explicit reviewer action.
- Fulltext/extraction/quality/analysis/report/export controls either write artifacts or remain disabled with precise reason.

Exit gate:

- No Meta page is substituted by an older page solely because it has backend code.
- Search/import/screening are callable from the visible mature page.

### Batch E: LabTools Replay

Goal: revalidate the accepted LabTools home and second/third-level page structure without broad UI changes.

Required pages:

- LabTools Home
- General Calculators
- Reagent Preparation
- Experiment Modules
- Cell Experiments
- Protein / Western Blot
- Nucleic Acid Experiments
- Immuno / Absorbance
- IHC

Required proof:

- Calculators and reagent actions produce visible state or artifacts.
- Cell experiment actions write records/artifacts or expose disabled reason.
- WB/protein actions write loading, workflow, BCA, ROI, export, or run-request artifacts.
- Nucleic acid qPCR remains adapter-connected; any high-fidelity visual rebuild is a later UI task unless a baseline source is confirmed.
- Immuno/Absorbance and IHC remain disabled with exact reasons until services exist.

Exit gate:

- No Shell crash from optional image/WB dependencies.
- No fake connected state for image analysis, IHC, or external engines.

### Batch F: Preview Package Gate

Goal: produce the first-stage preview only after Batch A-E pass.

Required checks:

```bash
QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
QT_QPA_PLATFORM=offscreen python3 scripts/package_app.py --app-name "BioMedPilot Integration Preview" --smoke-test
codesign --verify --deep --strict --verbose=2 "dist/BioMedPilot Integration Preview.app"
open -W -n "dist/BioMedPilot Integration Preview.app" --args --gui-startup-check --gui-startup-check-output /tmp/biomedpilot_phase1_gui_startup.json
```

Exit gate:

- `Info.plist` package git head matches the current release HEAD.
- LaunchServices opening passes, not only direct smoke.
- First-level and module-entry screenshots are updated.
- No forbidden paths appear in `git diff --name-status`.

## Screenshot Review Protocol

After each batch:

1. Save runtime screenshots under a date-stamped directory in `docs/ui/runtime_screenshots/`.
2. Reference screenshot paths in the batch Markdown report.
3. Present the key screenshots for user review before moving to the next visual page family when the batch includes framework-level UI changes.
4. If a screenshot shows a fallback/old page, stop the batch and restore the accepted visual baseline before adding backend logic.

## Forbidden Changes In Phase 1

- Whole-branch merge.
- Broad feature cherry-pick.
- UI framework replacement.
- Replacing mature UIShell pages with old feature pages.
- Writing committed release artifacts into `project_storage/`.
- Enabling external engines as production runtime without dependency detection, gate state, and report schema proof.

## Commit Strategy

Use small commits per batch:

| Commit type | Allowed content |
| --- | --- |
| `docs(...)` | Route contract reports, screenshots, validation logs, execution plan. |
| `fix(shell)` | Shell freeze regression fixes only. |
| `fix(bio)` | Bio adapter or gate wiring only. |
| `fix(meta)` | Meta adapter or gate wiring only. |
| `fix(labtools)` | LabTools adapter or gate wiring only. |
| `fix(packaging)` | Preview launch/package identity/startup fixes only. |

Do not mix business-code migration with Project Control documentation in the same commit unless the script-generated route contract is the direct proof for that code change.

## First Next Step

Run Batch A current-head contract replay and generate a single closure rollup that classifies every route-contract batch as:

- `current-head-proof`
- `prior-proof-docs-only-head-drift`
- `stale-code-proof`
- `blocked`

Only after that rollup is clean should Phase 1 proceed to Shell freeze replay and preview packaging.
