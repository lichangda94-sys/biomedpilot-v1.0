# UI Route Feature Inventory

Date: 2026-05-29

Purpose: track every visible button, card, route, page, handler, runtime, artifact, and test before any feature is declared connected or migrated.

Allowed statuses:

`connected`, `partial`, `placeholder`, `empty-button`, `missing-handler`, `missing-target-page`, `old-page`, `figma/new`, `broken`, `not migrated`

Allowed page styles:

`figma/new`, `old`, `hybrid`, `placeholder`, `missing`, `unknown`

## Route Inventory

| Module | UI Text | Source UI Baseline | File | objectName/handler | Click Result | Target Page | Runtime | Test | Status | Page Style |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Shell | Welcome / enter local workspace | `9d4edf3` preview | needs audit | needs audit | needs audit | needs audit | none expected | needs audit | partial | unknown |
| Shell | About | `9d4edf3` preview | needs audit | needs audit | needs audit | needs audit | none expected | needs audit | partial | unknown |
| Shell | Settings | `9d4edf3` preview | needs audit | needs audit | needs audit | needs audit | needs audit | needs audit | partial | unknown |
| Project | Project Management | `9d4edf3` preview is regressed | needs source search | needs audit | image-only/regressed | missing complete project page | needs audit | missing | broken | missing |
| Bioinformatics | Module home buttons | `9d4edf3` preview visual only | needs audit | needs audit | needs audit | needs audit | needs audit | needs audit | not migrated | unknown |
| Meta Analysis | Module home buttons | `9d4edf3` preview visual only plus Phase 4 L3 separately | needs audit | needs audit | needs audit | needs audit | needs audit | needs audit | not migrated | unknown |
| LabTools | Module home buttons | `9d4edf3` preview visual only | needs audit | needs audit | needs audit | needs audit | needs audit | needs audit | not migrated | unknown |

## Audit Rules

- Every user-visible entry must have one row.
- Button existence alone is not connected.
- A row can be marked `connected` only when UI, handler, target page/runtime, output/artifact or state, test, and documentation all exist.
- `old-page` and `placeholder` must not be promoted to complete.

## Historical UI Recovery Commit Matrix

Source: `docs/ui/UI线路既往检查.md`. These rows identify recovery sources only; they do not mark any route as migrated or connected.

Default interpretation for all rows below:

| Field | Value |
| --- | --- |
| Source branch | `codex/integration-labtools-ui-c2-carryover` |
| Status | `recovery-source-confirmed` |
| MainLine status | `not migrated / unknown` |
| Migration method | `scoped plan required` |

### Bioinformatics Recovery Sources

| Module | Route / Page | Historical Commit | Status | Notes |
| --- | --- | --- | --- | --- |
| Bioinformatics | Gate shell and state/action contracts | `08e9bd1cad818195e5a8a3911797d2762abcbf28` | recovery-source-confirmed | Route gate shell source; runtime completeness still requires audit. |
| Bioinformatics | Project Home | `900ba600730bec73872cf1ce6224081515ec7bf4` | recovery-source-confirmed | Same commit also covers Data Source. |
| Bioinformatics | Data Source | `900ba600730bec73872cf1ce6224081515ec7bf4` | recovery-source-confirmed | Requires handler and runtime audit. |
| Bioinformatics | Data Check & Preparation | `62739aab8338bd0ea191e3ad44ce41c2f41b1e41` | recovery-source-confirmed | Historical data check page source. |
| Bioinformatics | Group & Design | `62739aab8338bd0ea191e3ad44ce41c2f41b1e41` | recovery-source-confirmed | Same commit as Data Check & Preparation. |
| Bioinformatics | Analysis Tasks | `4061d7242207d8195fe31ff38c57fc10aa8473bb` | recovery-source-confirmed | Formal actions require runtime gate audit. |
| Bioinformatics | Result & Report | `2d5a560ec2980cb2cc6bde0eda858b022cb8e324` | recovery-source-confirmed | Split from report export. |
| Bioinformatics | Report Export | `2d5a560ec2980cb2cc6bde0eda858b022cb8e324` | recovery-source-confirmed | Export gate remains blocked until artifact proof. |
| Bioinformatics | Workbench surface rebuild | `2063ce81d9b1bed5f75962b425885c1027c3aafa` | recovery-source-confirmed | Current visual surface reference for Bioinformatics. |
| Bioinformatics | Release action wiring | `74c19adeecdd6ad3bff924bd001950948e421295` | recovery-source-confirmed | Wiring must be scoped separately from page visuals. |

### Meta Analysis Recovery Sources

| Module | Route / Page | Historical Commit | Status | Notes |
| --- | --- | --- | --- | --- |
| Meta Analysis | Project and Question pages | `bf6aaf86872ee8db28f9cebcaf03968ff33c4aca` | recovery-source-confirmed | Requires route and handler audit. |
| Meta Analysis | Search and Reference pages | `e551f44718c09ccf90a36888933d715445885fdc` | recovery-source-confirmed | Requires runtime boundary audit. |
| Meta Analysis | Screening / Extraction / ROB pages | `557b6451f7a096c4991fb5b18bbe392f7a56cd5b` | recovery-source-confirmed | Do not overwrite later validated Meta workflow without scoped comparison. |
| Meta Analysis | Result / Report / Export gates | `6fe2295738fc248e5b066e4d35360f6e446c5245` | recovery-source-confirmed | Export remains gated until artifact proof. |
| Meta Analysis | Workbench surface rebuild | `87f3f9a880748c1e35e2aa9c6c5b9b00a55ec0a3` | recovery-source-confirmed | Current visual surface reference for Meta. |
| Meta Analysis | Release connection matrix | `8c4e8bdab560ae99a7fdab2a2c4b6131cc0d8d1a` | recovery-source-confirmed | Wiring must be audited before migration. |

### LabTools Recovery Sources

| Module | Route / Page | Historical Commit | Status | Notes |
| --- | --- | --- | --- | --- |
| LabTools | Navigation shell | `3bf79f4fa36a099b2442ebcdc0e9df865a69bc02` | recovery-source-confirmed | Page style unknown until reconciliation. |
| LabTools | General calculator UI | `ca006ee8a35156e2bb5c396a890942924b4ff99a` | recovery-source-confirmed | Do not assume final Figma/new style. |
| LabTools | Reagent preparation UI | `f18b9a0e650fa9bd3cd76cc260ca8e7c145e4bee` | recovery-source-confirmed | Needs storage/write audit. |
| LabTools | Western blot loading UI | `a33cffeb0103c47d03bbbe68643ad431482e2ca5` | recovery-source-confirmed | Needs page style and runtime audit. |
| LabTools | Boundary pages | `00f4ec6cf68634fb01adb889a9b5041ed16df92c` | recovery-source-confirmed | Boundary pages are not runtime completion proof. |
| LabTools | Workbench surface rebuild | `ed396b49e698dcbb28a973cdb7060cd855dcf7b8` | recovery-source-confirmed | Current visual surface reference for LabTools. |
| LabTools | Workspace main window wiring | `a4edda1409f95a2ab43ffd435b84f3b9bd4180e4` | recovery-source-confirmed | Wiring must be scoped separately from `app/labtools/**`. |

## Current UI Route Inventory Audit: Welcome, Home, Sidebar, Module Homes

Date: 2026-05-31

Branch / HEAD audited: `integration/software-remediation-control` / `aed62741a465965220f58c5934db2ab7eb81b742`

Scope: source-level route and handler audit only. No business code was modified, no feature files were migrated, no merge or cherry-pick was run, and no `project_storage/` runtime click test was executed. In this section, `connected` means the entry has a source-visible handler and target page or state transition; artifact-producing click tests remain required before release sign-off.

### Welcome / Login Surface

| Surface | Entry | Current Source | Handler / Target | Status | Best Recovery Source | Audit Note |
| --- | --- | --- | --- | --- | --- | --- |
| Welcome | Top settings icon | `app/shell/login.py` / `loginTopIconButton` | Disabled; tooltip says settings placeholder | `placeholder` | `codex/integration-labtools-ui-c2-carryover` / `9d4edf3`, shell polish `78385b2`, `285d234` | Visible affordance is intentionally closed. It should not be counted as connected settings. |
| Welcome | Enter BioMedPilot | `app/shell/login.py` / `primaryButton` | `attempt_login()` emits `login_succeeded`; `MainWindow._complete_login()` opens Dashboard | `connected` | Current branch plus `9d4edf3` release UI gate button provenance | Source handler and target shell page exist. Runtime login click test not run in this audit. |
| Welcome | Register account | `app/shell/login.py` / `linkButton` | Disabled placeholder | `placeholder` | Shell baseline `9d4edf3` / `78385b2` | No account creation service target. |
| Welcome | Forgot password | `app/shell/login.py` / `linkButton` | Disabled placeholder | `placeholder` | Shell baseline `9d4edf3` / `78385b2` | No password reset service target. |

### Home / Dashboard Surface

| Surface | Entry | Current Source | Handler / Target | Status | Best Recovery Source | Audit Note |
| --- | --- | --- | --- | --- | --- | --- |
| Home module card | Bioinformatics card click | `app/shell/module_selection.py` / `ModuleEntryCard.clicked` | `open_bioinformatics_requested.emit` -> `MainWindow.show_bioinformatics()` | `connected` | Dashboard shell `285d234`, Bio UI recovery `2063ce8`, wiring `74c19ad` | Card itself is clickable, not only the inner button. |
| Home module button | Enter Bioinformatics module | `app/shell/module_selection.py` / `bioModuleButton` | Same as Bio card; opens `BioinformaticsWorkspaceWidget` | `connected` | `2063ce8`, `900ba60`, `74c19ad` | Target exists, but full Formal DEG / enrichment / clinical report gates still require downstream button artifact tests. |
| Home module card | Meta Analysis card click | `app/shell/module_selection.py` / `ModuleEntryCard.clicked` | `open_meta_analysis_requested.emit` -> `MainWindow.show_meta_analysis()` | `connected` | Dashboard shell `285d234`, Meta UI recovery `87f3f9a`, matrix `8c4e8bd` | Current target is the later active Meta workflow and should not be overwritten blindly by historical UI shell. |
| Home module button | Enter Meta Analysis module | `app/shell/module_selection.py` / `metaModuleButton` | Same as Meta card; opens `MetaAnalysisWorkspaceWidget` | `connected` | `87f3f9a`, `bf6aaf8`, `8c4e8bd` | Target exists with gated project workflow. |
| Home module card | LabTools card click | `app/shell/module_selection.py` / `ModuleEntryCard.clicked` | `open_labtools_requested.emit` -> `MainWindow.show_labtools()` | `old-page` | LabTools shell `ed396b4`, navigation `3bf79f4`, main-window wiring `a4edda1`, cell experiment workspace `4cd06fb` | Handler exists, but target is the minimal ImageJ/Fiji boundary page rather than the recovered LabTools module home. |
| Home module button | Enter LabTools module | `app/shell/module_selection.py` / `labToolsModuleButton` | Same as LabTools card; opens `LabToolsWorkspaceWidget` | `old-page` | `ed396b4`, `3bf79f4`, `a4edda1`, `4cd06fb` | This is the main release risk for LabTools: route is wired, but expected second-level module list is absent. |
| Home recent projects | Recent project rows | `app/shell/module_selection.py` / `_build_recent_projects_card()` | Labels only, no clickable open handler | `placeholder` | Dashboard shell `285d234`; current old `MainWindow._recent_projects_card()` has clickable record buttons but is unused | Current visible dashboard has no recent-project route. |
| Home support | Settings entry | `app/shell/module_selection.py` / `secondaryButton` | Disabled settings placeholder | `placeholder` | Settings shell `78385b2`, dashboard shell `285d234`, settings gate `e13d0f5` | Settings is reachable from Sidebar, but this Home support button is not. |
| Home support | Logout | `app/shell/module_selection.py` / `logoutButton` | `logout_requested.emit` -> `MainWindow.logout()` | `connected` | Current branch / shell baseline `9d4edf3` | Source handler exists; runtime click test not run. |

### Main Sidebar Surface

| Surface | Entry | Current Source | Handler / Target | Status | Best Recovery Source | Audit Note |
| --- | --- | --- | --- | --- | --- | --- |
| Sidebar | Dashboard | `app/shell/sidebar.py` | `on_dashboard` -> `MainWindow.show_dashboard()` | `connected` | Dashboard shell `285d234`, `35446c5` | Visible button is wired. |
| Sidebar | Bioinformatics | `app/shell/sidebar.py` | `on_bioinformatics` -> `MainWindow.show_bioinformatics()` | `connected` | Bio UI recovery `2063ce8`, action wiring `74c19ad` | Visible button is wired. |
| Sidebar | Meta Analysis | `app/shell/sidebar.py` | `on_meta_analysis` -> `MainWindow.show_meta_analysis()` | `connected` | Meta UI recovery `87f3f9a`, connection matrix `8c4e8bd` | Visible button is wired. |
| Sidebar | LabTools | `app/shell/sidebar.py` | `on_labtools` -> `MainWindow.show_labtools()` | `old-page` | LabTools recovery `ed396b4`, `3bf79f4`, `4cd06fb`, `a4edda1` | Visible route is wired, target page is the old/minimal LabTools page. |
| Sidebar | Settings Center | `app/shell/sidebar.py` | `on_settings` -> `MainWindow.show_settings()` | `placeholder` | Settings shell `78385b2`, `e13d0f5` | Target page exists but is explicitly a placeholder settings page. |
| Sidebar | Testing Mode | `app/shell/sidebar.py` | `on_testing` -> `MainWindow.show_testing_mode()` | `connected` | LAN/testing feedback shell `35446c5`, `feat(ui): add LAN feedback reporting and shell polish` | Target page and feedback-template handler exist. Artifact click test not run. |
| Sidebar registry only | Project Center / Data Center / Task Center / Report Center / Local Environment / Packaging | `app/shell/sidebar.py` / `COMMON_SIDEBAR_ITEMS` | Not rendered by `SidebarWidget`; no callbacks supplied to constructor | `missing-target-page` | Dashboard/settings shell `285d234`; project-control restoration required before UI migration | These entries exist only in the registry constant, not as visible sidebar buttons. |

### Bioinformatics Module Home

| Surface | Entry | Current Source | Handler / Target | Status | Best Recovery Source | Audit Note |
| --- | --- | --- | --- | --- | --- | --- |
| Bio Home header | Back to module selection home | `app/bioinformatics/project_home.py` / `secondaryButton` | `back_requested.emit` -> `MainWindow.show_dashboard()` | `connected` | Bio project home `900ba60`, workbench rebuild `2063ce8` | Route back exists. |
| Bio Home create project | Choose save location | `app/bioinformatics/project_home.py` | `_choose_save_location()` | `connected` | `900ba60` | File dialog handler exists; click test not run. |
| Bio Home create project | Create project and continue | `app/bioinformatics/project_home.py` / `primaryButton` | `create_project_from_inputs()` -> project summary -> `continue_requested` | `connected` | `900ba60`, release action wiring `74c19ad` | Writes project assets when clicked; not executed in this no-`project_storage/` audit. |
| Bio Home open project | Choose project folder | `app/bioinformatics/project_home.py` | `_choose_existing_project()` | `connected` | `900ba60` | File dialog handler exists. |
| Bio Home open project | Confirm and continue | `app/bioinformatics/project_home.py` / `primaryButton` | `open_selected_project()` -> validation -> `continue_requested` | `connected` | `900ba60`, `74c19ad` | Validation and transition are source-visible; runtime test remains required. |
| Bio Home current project | Continue: choose data source | `app/bioinformatics/project_home.py` / `primaryButton` | `_continue_to_data_source()` -> `BioinformaticsWorkspaceWidget.show_data_source()` | `connected` | Data source page `900ba60`; gate shell `08e9bd1`; wiring `74c19ad` | Requires an open project summary; otherwise shows disabled reason/status. |
| Bio Home current project | Open project folder | `app/bioinformatics/project_home.py` / `secondaryButton` | `_open_project_folder()` -> `QDesktopServices.openUrl()` | `connected` | `900ba60` | Handler exists; no Finder/runtime click test in this audit. |
| Bio Home current project | View project structure | `app/bioinformatics/project_home.py` / `secondaryButton` | `_show_project_structure()` | `connected` | `900ba60` | Handler exists. |
| Bio Home diagnostics | Technical details | `app/bioinformatics/project_home.py` / `secondaryButton` checkable | `toggled` -> `_toggle_technical_details()` | `connected` | `900ba60`, workbench rebuild `2063ce8` | UI-only diagnostic toggle. |
| Bio Home recent project text | Recent project placeholder text | `app/bioinformatics/project_home.py` | Label only | `placeholder` | Project Center remediation line; dashboard shell `285d234` | Explicitly says recent projects are a placeholder pending Project Center. |

### Meta Analysis Module Home

| Surface | Entry | Current Source | Handler / Target | Status | Best Recovery Source | Audit Note |
| --- | --- | --- | --- | --- | --- | --- |
| Meta global nav | Back to home | `app/meta_analysis/workspace.py` / `metaSecondaryButton` | `on_back` -> `MainWindow.show_dashboard()` | `connected` | Meta workbench rebuild `87f3f9a` | Route back exists. |
| Meta project side nav | New Meta project | `app/meta_analysis/workspace.py` | `show_step("workflow_home")` | `connected` | Project/question pages `bf6aaf8`, workbench rebuild `87f3f9a` | Navigation target exists. |
| Meta project side nav | Open existing project | `app/meta_analysis/workspace.py` | `_choose_existing_project_folder()` -> `open_meta_project_folder()` | `connected` | `bf6aaf8`, `87f3f9a` | File dialog and validation handler exist. |
| Meta project side nav | Workflow step list | `app/meta_analysis/workspace.py` / `metaWorkflowStepList` | `currentRowChanged` -> `_page_stack.setCurrentIndex` | `connected` | Meta page groups `bf6aaf8`, `e551f44`, `557b645`, `6fe2295`; matrix `8c4e8bd` | Route list is wired; project-less pages intentionally show gated empty states. |
| Meta project side nav | Back to module home | `app/meta_analysis/workspace.py` / `metaSecondaryButton` | `on_back` -> `MainWindow.show_dashboard()` | `connected` | `87f3f9a` | Route back exists. |
| Meta Home no project | Choose save location | `app/meta_analysis/workspace.py` | `_choose_save_location()` | `connected` | `bf6aaf8`, `87f3f9a` | File dialog handler exists. |
| Meta Home no project | Create project | `app/meta_analysis/workspace.py` / `metaPrimaryButton` | `create_meta_project_from_form()` | `connected` | `bf6aaf8`, `8c4e8bd` | Writes project assets when clicked; not executed in this no-`project_storage/` audit. |
| Meta Home no project | Choose existing project folder | `app/meta_analysis/workspace.py` / `metaSecondaryButton` | `_choose_existing_project_folder()` | `connected` | `bf6aaf8`, `87f3f9a` | Handler exists. |
| Meta Home no project | Continue: research question / PICO | `app/meta_analysis/workspace.py` / `metaPrimaryButton` | Disabled until project exists | `placeholder` | `bf6aaf8`, `8c4e8bd` | Intentional gate. It should become connected only after project creation/opening. |
| Meta Home current project | Continue: research question / PICO | `app/meta_analysis/workspace.py` / `metaPrimaryButton` | `on_go_pico` -> `show_step("pico_workspace")` | `connected` | `bf6aaf8`, `8c4e8bd` | Connected only in current-project state. |
| Meta Home diagnostics | Developer diagnostics | `app/meta_analysis/workspace.py` | `_developer_details()` toggle | `connected` | `87f3f9a` | UI-only diagnostic toggle. |

### LabTools Module Home

| Surface | Entry | Current Source | Handler / Target | Status | Best Recovery Source | Audit Note |
| --- | --- | --- | --- | --- | --- | --- |
| LabTools header | Back to module home | `app/labtools/workspace.py` | `_on_back` -> `MainWindow.show_dashboard()` | `connected` | Main-window wiring `a4edda1`, LabTools workbench `ed396b4` | Route back exists. |
| LabTools current page | ImageJ/Fiji save path | `app/labtools/ui/image_analysis_widgets.py` / `secondaryButton` | `_handle_configure_imagej_fiji()` -> `configure_labtools_imagej_fiji_path()` | `connected` | Image analysis boundary in current branch; LabTools workbench source `ed396b4` | This is the only current LabTools runtime capability. |
| LabTools current page | Detect ImageJ/Fiji | `app/labtools/ui/image_analysis_widgets.py` / `secondaryButton` | `_handle_check_imagej_fiji()` -> `check_labtools_imagej_fiji_status()` | `connected` | Current branch plus `ed396b4` | Handler exists; no local engine click test run. |
| LabTools current page | Clear ImageJ/Fiji path | `app/labtools/ui/image_analysis_widgets.py` / `secondaryButton` | `_handle_clear_imagej_fiji()` -> `clear_labtools_imagej_fiji_path()` | `connected` | Current branch plus `ed396b4` | Handler exists; no storage mutation executed. |
| LabTools expected module nav | General calculator | Not present in current `app/labtools/workspace.py` | No visible route or target page in current LabTools workspace | `missing-target-page` | `ca006ee8a35156e2bb5c396a890942924b4ff99a`, navigation shell `3bf79f4` | Designed page exists in historical UI line but is not in current target. |
| LabTools expected module nav | Reagent preparation | Not present in current `app/labtools/workspace.py` | No visible route or target page in current LabTools workspace | `missing-target-page` | `f18b9a0e650fa9bd3cd76cc260ca8e7c145e4bee`, storage adapter commits `edfa2a5` / `e64454b` | Designed page and storage line must be reconciled before migration. |
| LabTools expected module nav | Western blot loading | Not present in current `app/labtools/workspace.py` | No visible route or target page in current LabTools workspace | `missing-target-page` | `a33cffeb0103c47d03bbbe68643ad431482e2ca5`, workbench `ed396b4` | This directly explains the missing WB UI in the release preview lineage. |
| LabTools expected module nav | Cell experiment workspace / cell information | Not present in current `app/labtools/workspace.py` | No visible route or target page in current LabTools workspace | `missing-target-page` | `4cd06fb87b2d01090fbfe7b260f9bdb211de1e45`, workbench `ed396b4` | The current branch has no second-level cell experiment home or cell information page. |
| LabTools expected module nav | LabTools boundary pages | Current single boundary page only | Expected route set is absent; current `page_keys()` returns only `("image_analysis",)` | `old-page` | `00f4ec6cf68634fb01adb889a9b5041ed16df92c`, `3bf79f4`, `ed396b4` | Current LabTools workspace is a narrow old/minimal page, not the recovered multi-page LabTools workbench. |

### Audit Summary

- No enabled `empty-button` was found in the inspected Welcome/Home/Sidebar/module-home source files.
- Welcome and Home contain multiple intentional `placeholder` entries: settings, register, forgot password, and recent projects.
- Shell routes to Bioinformatics and Meta are source-connected.
- Shell route to LabTools is source-wired but lands on an `old-page`; the designed LabTools second-level module list and WB / reagent / calculator / cell experiment pages are not present in the current target.
- Sidebar registry contains additional planned route names that are not rendered and have no callbacks; they must not be treated as release-ready navigation.
- Best recovery source remains `codex/integration-labtools-ui-c2-carryover`, with shell/dashboard commits `9d4edf3`, `78385b2`, `285d234`, Bio commits `900ba60` / `2063ce8` / `74c19ad`, Meta commits `bf6aaf8` / `87f3f9a` / `8c4e8bd`, and LabTools commits `3bf79f4` / `ca006ee` / `f18b9a0` / `a33cffe` / `4cd06fb` / `ed396b4` / `a4edda1`.
