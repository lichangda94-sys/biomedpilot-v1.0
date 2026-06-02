# UI Route Contract Phase 1 Plan

Date: 2026-06-01

Branch: `integration/release-bio-c1-ui-shell`

Current audited HEAD: `066f69654eea01d44074ffce54693defeac00881` plus the in-progress Phase 1 Shell recovery patch.

## Objective

Phase 1 establishes the control line for page recovery and runtime reconnection before further module migration.

The phase must make these rules enforceable:

- Recover pages only after a route migration audit identifies the visual baseline, current target, runtime source, and test proof.
- Rebuild the UI route contract as the release authority for visible routes, pages, buttons, handlers, runtime effects, artifacts, and disabled reasons.
- Freeze shared shell surfaces so module recovery cannot regress Welcome, Home, About, Settings, Sidebar, Centers, shared primitives, or icon/logo assets.
- Connect Bioinformatics, Meta Analysis, and LabTools through module adapters instead of embedding legacy branch logic directly into the shared shell.
- Validate every visible enabled button with live-click proof: service call, expected artifact, result index/manifest/report-ready package, or explicit disabled reason.
- Bring pages and runtime back in module batches, with each batch independently audited, tested, screenshotted, and packaged before moving to the next.

## Evidence Inputs

| Evidence | Current Source | Phase 1 Use |
| --- | --- | --- |
| UI Shell baseline decision | `docs/project-control/UI_SHELL_BASELINE_DECISION.md` | Defines accepted Shell baseline and forbidden interpretations. |
| Existing route inventory | `docs/project-control/UI_ROUTE_FEATURE_INVENTORY.md` | Starting inventory; must be promoted from source audit to executable contract. |
| Feature asset inventory | `docs/project-control/FEATURE_ASSET_INVENTORY.md` | Tracks feature-level migration risk and acceptance state. |
| Historical UI recovery check | `docs/ui/UI线路既往检查.md` | Identifies historical recovery commits and branches. |
| Latest release validation | `docs/release_validation/20260602_phase1_preview_startup.md` | Supplies current Shell screenshot and live-click evidence for Welcome, Home, Sidebar, Settings, Centers, About, and module adapter entries. |
| Button contract test | `tests/ui/test_release_ui_button_contracts.py` | Existing static contract test for button metadata and disabled reasons. |
| Preview launch repair | commits `8519391`, `75e98c9`, `58d06df`, `066f696` package gate | Confirms packaged preview must be validated through real LaunchServices opening, not smoke-only. |

## Phase 1 Scope

### Included

- Governance docs and route contract definition.
- Shared Shell freeze criteria.
- Adapter boundary rules for module entry points.
- Button live-click acceptance model.
- Batch order and per-module entry/exit gates.
- Audit scripts or tests that inspect current UI contracts without migrating feature pages.
- Screenshots and reports needed to prove Phase 1 baseline.

### Excluded

- Whole-branch merge.
- Direct cherry-pick of historical UI commits.
- Broad page migration from Bioinformatics, Meta Analysis, or LabTools.
- Runtime feature completion for DEG, ORA/GSEA, survival, PubMed full workflow, WB image analysis, or other module internals.
- `project_storage/` migration.
- Replacing mature gated pages with old pages.

## Frozen Shared Shell Contract

The shared shell is frozen before module batches begin. A later module batch may consume shell services but must not rewrite shell ownership.

Frozen surfaces:

| Surface | Frozen Files / Areas | Contract |
| --- | --- | --- |
| Welcome | `app/shell/login.py`, `assets/icons/ui01_login/`, `assets/images/welcome/` | Enter workspace, About, and Settings affordances keep UIShell baseline behavior. Register/forgot remain disabled placeholders unless account runtime exists. |
| Home / Dashboard | `app/shell/module_selection.py`, `app/shell/dashboard.py`, `assets/icons/ui02_module_selection/`, `assets/icons/modules/` | Three module cards route through adapters. Home support placeholders must not be represented as connected. |
| Sidebar | `app/shell/sidebar.py` | Sidebar route keys are stable. Adding route keys requires route contract rows and live-click proof. |
| About | `app/shell/main_window.py` About page block | Mature text About page remains the baseline. |
| Settings | `app/shell/settings_page.py`, `assets/icons/settings/resources/`, `assets/icons/status/` | External capabilities remain detect-only or disabled with reason unless a formal runtime install/execute contract exists. |
| Centers | `app/shell/centers_page.py`, shared center services | Centers stays a shell support surface; it must not become a hidden module runtime bypass. |
| Shared UI primitives | `app/shared/ui_components/**`, `app/ui_style_tokens.py`, `app/app_identity.py` | Tokens/icons/components are stable dependencies. Module pages may use them but not redefine shell semantics. |

Freeze proof required:

- `tests/ui/test_login_page.py`
- `tests/ui/test_module_selection.py`
- `tests/ui/test_settings_shell.py`
- `tests/ui/test_sidebar.py`
- `tests/ui/test_shell_centers.py`
- `python3 -m app.main --smoke-test`
- Packaged `.app` LaunchServices open check.

## Module Adapter Boundary

Module code must be reached through adapter boundaries. `MainWindow` owns shell routing only; modules own module-level routing and runtime gates.

Required adapter shape:

| Module | Shell Adapter Entry | Adapter Must Provide | Adapter Must Not Do |
| --- | --- | --- | --- |
| Bioinformatics | `BioinformaticsWorkspaceWidget` | Stable page keys, route methods, button contract metadata, runtime gate state, artifact paths. | Import legacy GEO/UI tools directly into Shell. |
| Meta Analysis | `MetaAnalysisWorkspaceWidget` | Stable target IA page keys, PubMed/search/screening adapter state, report/export gates. | Overwrite current active Meta workflow with historical UI without scoped comparison. |
| LabTools | `LabToolsWorkspaceWidget` | Stable page keys, second/third-level page routes, calculator/reagent/WB/cell/image adapters, safe fallback widgets. | Let optional image/WB imports crash Shell or bypass route contract rows. |

Adapter acceptance criteria:

- Every adapter exposes page keys for route inventory.
- Every visible enabled button has `buttonBehavior`.
- Every disabled button has `disabledReason`.
- Every service-producing button writes an artifact or observable state that a test can assert.
- Optional runtime dependencies degrade inside the module page, not at Shell startup.

## Route Contract Schema

Phase 1 promotes `UI_ROUTE_FEATURE_INVENTORY.md` into a contract table with one row per visible route/button.

Required fields:

| Field | Meaning |
| --- | --- |
| `contract_id` | Stable ID: `SHELL-WELCOME-ENTER`, `BIO-DATA-SOURCE-GEO`, `LAB-WB-SAVE-RECORD`, etc. |
| `module` | `Shell`, `Bioinformatics`, `Meta Analysis`, `LabTools`, `Centers`. |
| `surface` | Page or route surface where the control is visible. |
| `ui_baseline` | Current accepted visual source or current Integration source. |
| `current_file` | Current implementation file. |
| `object_name` | Qt `objectName`; must be stable for tests. |
| `route_target` | Page key, handler, adapter method, or disabled target. |
| `button_behavior` | Expected semantic behavior string. |
| `runtime_effect` | Service call, artifact write, state transition, or `none_expected`. |
| `artifact_evidence` | File, manifest, result index, report package, screenshot, or disabled reason. |
| `live_click_test` | Test/script that clicks the control and verifies the effect. |
| `status` | `connected`, `partial`, `placeholder`, `empty-button`, `missing-handler`, `missing-target-page`, `old-page`, `broken`, `not migrated`. |
| `batch` | Phase/batch that owns migration or remediation. |

Promotion rule:

`connected` is allowed only when the row has a current file, object name, handler/target, live-click test, and runtime/artifact/disabled-reason proof.

## Live-Click Verification Model

Button validation is not satisfied by existence checks.

Each visible button must prove exactly one of these outcomes:

| Outcome | Proof |
| --- | --- |
| Calls real service | Monkeypatched or live service invocation is observed and asserted. |
| Generates artifact | Expected JSON/CSV/manifest/report/request file exists and schema is checked. |
| Writes result index | Result index, project manifest, screening queue, task manifest, or report package is updated. |
| Navigates route | Current page key changes to expected adapter page. |
| Disabled with reason | Button is disabled and has specific `disabledReason`; no fake connected state. |

Phase 1 live-click minimum:

- Shell: Welcome Enter/About/Settings; Home module cards/buttons; Sidebar primary routes; Centers action buttons.
- Bioinformatics: 7-step page navigation and first-level gated buttons, including data source request artifacts and existing GSE live validation paths.
- Meta Analysis: active workflow page navigation and PubMed search/import/screening queue path.
- LabTools: module home and second-level page routes; calculator/reagent/WB/cell/image buttons must either write artifacts or show precise disabled reasons.

## Batch Order

### Batch 0: Contract Freeze

Goal: lock route schema and Shell baseline before page recovery.

Deliverables:

- `UI_ROUTE_FEATURE_INVENTORY.md` updated with Phase 1 contract fields or a generated contract appendix.
- Shell freeze checklist added to Project Control.
- `test_release_ui_button_contracts.py` remains green.
- Preview launch test uses real `open -n`, not only `--smoke-test`.

Exit gate:

- No Shell route is `broken`.
- No enabled Shell button lacks `buttonBehavior`.
- No disabled Shell button lacks `disabledReason`.
- Packaged preview opens for at least 10 seconds without traceback.

### Batch 1: Bioinformatics Adapter Contract

Goal: keep mature 7-step Bio pages and connect existing runtime through adapters.

Page order:

1. Project Home
2. Data Source
3. Data Check & Preparation
4. Group & Design
5. Analysis Tasks
6. Result & Report
7. Report Export

Runtime contract:

- GEO / Local / TCGA / GTEx entries connect to acquisition/retrieval/recognition adapters.
- Data Check writes recognition/readiness artifacts.
- Group Design writes group/comparison/covariate state or blocker.
- Formal DEG, ORA/GSEA, survival/clinical either execute through formal service or remain disabled with precise reason.
- Result & Report reads result index/artifact registry.
- Report Export opens only after report-ready gate passes.

Live evidence:

- `GSE6004`: search/download/recognition/readiness expected `ready_with_warnings`.
- `GSE153659`: search/download/recognition expected callable; readiness blocker must be reported accurately until expression matrix parsing is added.

### Batch 2: LabTools Adapter Contract

Goal: restore accepted LabTools home and second-level structure without letting optional image/WB dependencies crash Shell.

Page order:

1. LabTools Home
2. General Calculators
3. Reagent Preparation
4. Experiment Modules
5. Cell Experiments
6. Protein / Western Blot
7. Nucleic Acid Experiments
8. Immuno / Absorbance
9. IHC

Runtime contract:

- Calculator buttons write calculation result state or disabled reason.
- Reagent buttons use storage adapter and export artifacts.
- WB buttons write workflow/loading/ROI request artifacts or disabled reason.
- Cell experiment buttons write cell records/freezing/passaging artifacts or disabled reason.
- Image analysis buttons generate run request artifacts; they must not imply automatic ImageJ/Fiji execution unless the external engine gate is explicitly passed.

### Batch 3: Meta Analysis Adapter Contract

Goal: preserve active Meta workflow while comparing historical mature UI sources.

Page order:

1. Project Home
2. Question / Meta Type
3. Search Strategy
4. Import / Dedup
5. Screening
6. Fulltext / Extraction
7. Quality Assessment
8. Analysis Tasks
9. Result & Report
10. Report Export
11. Settings

Runtime contract:

- PubMed search produces candidate records.
- Import/dedup writes literature records and dedup queue.
- Screening writes screening queue.
- Fulltext/extraction/quality/analysis/report/export must remain gated or disabled with reason until runtime proof exists.

Live evidence:

- PubMed query: `("thyroid cancer" OR "thyroid carcinoma" OR 甲状腺癌) AND (adiponectin OR 脂联素)`.
- Minimum proof: search success, candidates returned, import count, screening queue artifact.

## First Implementation Steps

1. Freeze the Shell baseline by keeping Welcome top-bar Settings visible and preserving Sidebar Centers as a Shell support route.
2. Keep `scripts/ui_route_contract_audit.py` as the Batch 0 contract authority; it must instantiate Shell pages offscreen and emit JSON/Markdown rows.
3. Keep `scripts/phase1_preview_startup_validation.py` as the screenshot/live-click authority for Welcome, Home, Sidebar, Settings, Centers, About, and module adapter entries.
4. Run Batch 0 Shell freeze verification and package preview after every Shell route change.
5. Continue Batch 1 Bioinformatics adapter contract from current mature 7-step pages; `GSE6004` and `GSE153659` GEO retrieval/recognition/readiness now have Batch 10 evidence, while TCGA/GTEx and formal ORA/GSEA/survival remain documented gaps.

## Current Phase 1 Recovery Findings

The current Phase 1 recovery audit found two Shell regressions relative to the frozen contract:

| Finding | Evidence | Recovery |
| --- | --- | --- |
| Welcome Settings was not visible in the runtime page tree. | `scripts/ui_route_contract_audit.py` initially failed with missing `loginTopIconButton`. | Restore `_build_top_bar()` into `BioMedPilotLoginWidget._build_ui()` and live-click `welcome_settings -> settings`. |
| Sidebar Centers route was absent while Centers remained part of the Shell contract. | `scripts/ui_route_contract_audit.py` failed with missing `pageKey=centers`; `tests/ui/test_shell_centers.py` still required the route. | Restore Centers entry in `SidebarWidget`, add `MainWindow.show_centers()`, and route it to `build_centers_page()`. |

The recovery scope is Shell-only: no Bioinformatics, Meta Analysis, LabTools feature page, backend, or `project_storage/` migration is included in this phase.

## Stop Conditions

Stop a batch and record `blocked` in the contract row when:

- A page source conflicts with the frozen Shell baseline.
- A route requires whole-branch merge or broad cherry-pick.
- A button appears connected but cannot be proven by service/artifact/state/disabled reason.
- A runtime dependency is missing and the UI does not expose a precise disabled reason.
- A packaged preview fails real LaunchServices opening.

## Required Reports Per Batch

Each batch must produce:

- Route contract diff.
- Live-click JSON report.
- Screenshot directory.
- Test command output summary.
- Packaged preview path and `BUILD_INFO git_head`.
- Known blockers table with owner module and next runtime requirement.

## Phase 1 Definition of Done

Phase 1 is complete only when:

- Shared Shell is frozen by tests and packaged preview launch proof.
- The route contract schema exists and covers Shell plus module entry surfaces.
- Each module has an adapter boundary and batch plan.
- Existing visible buttons are classified, with no unknown enabled buttons.
- Batch 0 report is committed.
- Batch 1 Bioinformatics can start from a contract row list rather than ad hoc page inspection.
