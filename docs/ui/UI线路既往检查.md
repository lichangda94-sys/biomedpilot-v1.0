# UI线路既往检查

Date: 2026-05-29

Project Control handoff document for checking historical UI line commits after the Integration merge lost multiple Bioinformatics, Meta Analysis, and LabTools subpages and interfaces.

## Scope

- Repository checked: `/Users/changdali/Developer/biomedpilot v1.0/UIShell`
- Current UIShell branch checked: `dev/ui-shell`
- UIShell HEAD at check time: `8a92120e278c17df32fe99cb7742ac390268342a`
- Old integration branch checked: `dev/integration`
- Old integration HEAD at check time: `ea57a495d6826616456b047e09315df7682b3600`
- Current local Integration worktree checked: `/Users/changdali/Developer/biomedpilot v1.0/Integration`
- Current local Integration worktree branch: `codex/integration-labtools-ui-c2-carryover`
- Current local Integration worktree HEAD: `e13d0f5f5dfda36a5c60a00ddc7820748fa1677f`

## Summary

The old `dev/integration` branch is missing the relevant UI line commits for Bioinformatics, Meta Analysis, and LabTools. The local Integration worktree is not on old `dev/integration`; it is already on `codex/integration-labtools-ui-c2-carryover`, which contains the missing page commits and later release wiring.

For recovery work, prefer using `codex/integration-labtools-ui-c2-carryover` as the source branch. Direct cherry-pick from individual old UI commits is possible, but it has known conflicts in shared UI foundation files.

## Preferred Recovery Source

Use this source first:

- Branch: `codex/integration-labtools-ui-c2-carryover`
- HEAD: `e13d0f5f5dfda36a5c60a00ddc7820748fa1677f`
- HEAD commit: `Expose R enrichment package gates in Settings`

Important integration carryover commits:

| Commit | Purpose |
| --- | --- |
| `efb6227d595662ab5fb34d2b8b470b7bb69b51da` | Merge latest UI shell for release preview; carries most UI Shell, Bioinformatics, Meta Analysis, and LabTools page work. |
| `44885c50b17b0c0646074f7a20cfc48f91dc2dc3` | Merge LabTools LAN release increment. |
| `a4edda1409f95a2ab43ffd435b84f3b9bd4180e4` | Wire LabTools workspace into main window. |
| `74c19adeecdd6ad3bff924bd001950948e421295` | Wire bioinformatics release actions. |
| `8c4e8bdab560ae99a7fdab2a2c4b6131cc0d8d1a` | Wire meta release connection matrix. |
| `e13d0f5f5dfda36a5c60a00ddc7820748fa1677f` | Expose R enrichment package gates in Settings. |

## Bioinformatics UI Commits

These commits are missing from old `dev/integration` and present in the current local Integration worktree:

| Commit | Area |
| --- | --- |
| `08e9bd1cad818195e5a8a3911797d2762abcbf28` | Bioinformatics gate shell and state/action contracts. |
| `900ba600730bec73872cf1ce6224081515ec7bf4` | Project Home and Data Source gated pages. |
| `62739aab8338bd0ea191e3ad44ce41c2f41b1e41` | Data Check & Preparation and Group & Design gated pages. |
| `4061d7242207d8195fe31ff38c57fc10aa8473bb` | Analysis Tasks gated page. |
| `2d5a560ec2980cb2cc6bde0eda858b022cb8e324` | Result & Report and Report Export split gates. |
| `2063ce81d9b1bed5f75962b425885c1027c3aafa` | Current Bioinformatics Workbench surface rebuild. |
| `74c19adeecdd6ad3bff924bd001950948e421295` | Bioinformatics release action wiring. |

Key current files expected after recovery:

- `app/bioinformatics/analysis_ui/action_rules.py`
- `app/bioinformatics/analysis_ui/capability_map.py`
- `app/bioinformatics/analysis_ui/labels.py`
- `app/bioinformatics/analysis_ui/state.py`
- `app/bioinformatics/workflow_pages.py`
- `app/bioinformatics/workspace.py`
- `assets/icons/bioinformatics/pages/*`

## Meta Analysis UI Commits

These commits are missing from old `dev/integration` and present in the current local Integration worktree:

| Commit | Area |
| --- | --- |
| `bf6aaf86872ee8db28f9cebcaf03968ff33c4aca` | Project and Question gated pages. |
| `e551f44718c09ccf90a36888933d715445885fdc` | Search and Reference gated pages. |
| `557b6451f7a096c4991fb5b18bbe392f7a56cd5b` | Screening, Extraction, and ROB gated pages. |
| `6fe2295738fc248e5b066e4d35360f6e446c5245` | Result, Report, and Export gates. |
| `87f3f9a880748c1e35e2aa9c6c5b9b00a55ec0a3` | Current Meta Analysis Workbench surface rebuild. |
| `8c4e8bdab560ae99a7fdab2a2c4b6131cc0d8d1a` | Meta release connection matrix wiring. |

Key current files expected after recovery:

- `app/meta_analysis/connection_matrix.py`
- `app/meta_analysis/workflow_pages.py`
- `app/meta_analysis/workspace.py`
- `assets/icons/meta/pages/*`

## LabTools UI and Interface Commits

These commits are missing from old `dev/integration` and present in the current local Integration worktree:

| Commit | Area |
| --- | --- |
| `3bf79f4fa36a099b2442ebcdc0e9df865a69bc02` | LabTools navigation shell. |
| `ca006ee8a35156e2bb5c396a890942924b4ff99a` | General calculator UI. |
| `f18b9a0e650fa9bd3cd76cc260ca8e7c145e4bee` | Reagent preparation UI. |
| `a33cffeb0103c47d03bbbe68643ad431482e2ca5` | Western blot loading UI. |
| `00f4ec6cf68634fb01adb889a9b5041ed16df92c` | LabTools boundary pages. |
| `edfa2a595b5b4d249cd91fa9aa1420904e7f8df0` | LabTools storage adapter skeleton. |
| `7afe07bb5a07225bddf43ed1ecc3201ac4443ebf` | Connect local data store to UI read paths. |
| `e64454be34d4dc0ea37c68b06c2f889138ccedf9` | Local reagent write UI integration. |
| `b40cc8df0683c78019375a2f6dbd2b68ce4d35b9` | Local sample write UI integration. |
| `ed396b49e698dcbb28a973cdb7060cd855dcf7b8` | Current LabTools Workbench surface rebuild. |
| `44885c50b17b0c0646074f7a20cfc48f91dc2dc3` | LabTools LAN release increment merge. |
| `a4edda1409f95a2ab43ffd435b84f3b9bd4180e4` | LabTools workspace main window wiring. |

Key current files expected after recovery:

- `app/labtools/labtools_home.py`
- `app/labtools/workspace.py`
- `app/labtools_runtime.py`
- `app/labtools_storage_adapter.py`
- `assets/icons/labtools/*`

## Shared UI Foundation

The UI page commits depend on shared shell and component changes. These are the relevant foundation commits or files:

| Commit | Area |
| --- | --- |
| `82db716f12c2320a49c73c702fe70850fcd7af1c` | Integration shared UI foundation. |
| `d2c6c921b02633b683e5cda5a9694b099f6b5292` | Shared design tokens and primitives. |
| `78385b2b74d7daf67aa68b83d78937a36bb4be6f` | Dashboard and settings shell rebuild. |
| `b691fe6ac89e73c6ca6174e4bd68dae122c61ca7` | Core Workbench primitives. |
| `a731f8a02f7b04c61fdf581812908a9dbbd76bb7` | Common Workbench components. |
| `1d663a73c635c7e2629ce5370513674d45ef5e04` | Dense Workbench components. |
| `cb10694e254d1fb2303327c0517ead3545229f2a` | Specialized Workbench components. |

Expected files:

- `app/shared/ui_components/primitives.py`
- `app/shared/ui_components/common.py`
- `app/shared/ui_components/dense_workbench.py`
- `app/shared/ui_components/specialized.py`
- `app/shared/ui_components/workbench.py`
- `app/shell/settings_page.py`
- `app/shared/result_report_export_shell.py`
- `app/shared/semantic_keys.py`

## Cherry-pick Risk Check

A temporary cherry-pick check was run against old `dev/integration`.

Observed conflicts:

- Direct cherry-pick of `d2c6c92` conflicts in `app/ui_style_tokens.py`.
- Cherry-pick of `efb6227` with `-m 1` conflicts in:
  - `app/app_identity.py`
  - `app/bioinformatics/workflow_pages.py`
  - `app/shared/ui_components/__init__.py`
  - `app/shared/ui_components/primitives.py`
  - `app/ui_style_tokens.py`
  - `tests/test_package_app.py`
  - `tests/ui/test_ui_primitives.py`

Interpretation:

- The historical commits are valid recovery sources, but old `dev/integration` has diverged enough that direct cherry-pick needs manual conflict resolution.
- For Project Control, the lower-risk source is the already-carried integration branch `codex/integration-labtools-ui-c2-carryover`.

## Recommended Recovery Order

Preferred branch-level recovery:

1. Compare target branch against `codex/integration-labtools-ui-c2-carryover`.
2. Restore from `codex/integration-labtools-ui-c2-carryover` rather than replaying every individual historical UI commit.
3. Verify presence of the expected files listed above.
4. Run UI smoke tests for Bioinformatics, Meta Analysis, LabTools, and module selection.

If commit-level cherry-pick is required, use this order:

1. `82db716f12c2320a49c73c702fe70850fcd7af1c`
2. `efb6227d595662ab5fb34d2b8b470b7bb69b51da` with `-m 1`
3. `44885c50b17b0c0646074f7a20cfc48f91dc2dc3` with `-m 1`
4. `a4edda1409f95a2ab43ffd435b84f3b9bd4180e4`
5. `74c19adeecdd6ad3bff924bd001950948e421295`
6. `8c4e8bdab560ae99a7fdab2a2c4b6131cc0d8d1a`
7. `e13d0f5f5dfda36a5c60a00ddc7820748fa1677f`

If the target branch cannot accept merge commits, replay the module groups from the sections above, but expect shared UI conflicts first.

## Verification Checklist

After recovery, check:

- Bioinformatics pages are present: project home, data source, data check and preparation, group design, analysis tasks, result report, report export, settings/resources, project logs.
- Meta Analysis pages are present: project/question, search/reference, import/dedup, screening/extraction/ROB, analysis tasks, result/report/export.
- LabTools pages are present: navigation shell, general calculator, reagent preparation, western blot loading, boundary pages, cell experiment workspace where applicable.
- `app/shell/main_window.py` routes to LabTools, Bioinformatics, and Meta workspaces.
- `app/shell/settings_page.py` contains resource/package gate surfaces.
- Shared Workbench components are present under `app/shared/ui_components/`.

## Project Control Decision

Treat `codex/integration-labtools-ui-c2-carryover` as the current local integration recovery baseline. Treat old `dev/integration` at `ea57a49` as missing the UI line and not sufficient for packaging or tester handoff without restoring the commits listed in this document.
