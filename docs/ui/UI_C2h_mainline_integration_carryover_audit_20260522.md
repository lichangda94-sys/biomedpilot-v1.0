# UI-C2h MainLine / Integration Carry-over Audit

Date: 2026-05-22

## 1. Scope

This audit checks whether the completed LabTools UI-C2 work from `dev/ui-shell` can be carried into the local Integration and MainLine workflows.

Source:

- Worktree: `/Users/changdali/Developer/biomedpilot v1.0/UIShell`
- Branch: `dev/ui-shell`
- HEAD: `6072aec4d61b`

Targets reviewed:

| Target | Worktree / Branch | HEAD |
| --- | --- | --- |
| Integration | `/Users/changdali/Developer/biomedpilot v1.0/Integration` / `dev/integration` | `ea57a495d682` |
| MainLine worktree | `/Users/changdali/Developer/biomedpilot v1.0/MainLine` / `codex/mainline-survival-clinical-carryover` | `7bcdb7f53430` |
| MainLine stable branch reference | `stable/mainline` | `be8c924336f4` |

Strict boundary for this stage:

- Audit only.
- No merge.
- No cherry-pick.
- No push.
- No packaged app.
- No package smoke.
- No App icon / Finder icon / `.icns` / Info.plist / LaunchServices.
- No changes to `app/**`, `tests/**`, `assets/**`, `scripts/**`, or `dist/**`.

This stage adds only:

- `docs/ui/UI_C2h_mainline_integration_carryover_audit_20260522.md`
- `docs/ui/UI_C2h_labtools_mainline_integration_carryover_matrix_20260522.csv`

## 2. Reviewed LabTools UI-C2 Chain

| Stage | Commit | Summary |
| --- | --- | --- |
| UI-C2b | `3bf79f4` | `feat(ui): implement LabTools navigation shell` |
| UI-C2c | `ca006ee` | `feat(ui): implement LabTools general calculator UI` |
| UI-C2d | `f18b9a0` | `feat(ui): implement LabTools reagent preparation UI` |
| UI-C2e | `a33cffe` | `feat(ui): implement LabTools WB loading UI` |
| UI-C2f | `00f4ec6` | `feat(ui): implement LabTools boundary pages` |
| UI-C2g | `6072aec` | `docs(ui): audit LabTools UI implementation closure` |

Important dependency note:

UI-C2b through UI-C2g are not standalone patches. They depend on earlier UI shell work on `dev/ui-shell`, including global shell rebuild, semantic key adoption, Settings shell/resource icon adoption, LabTools IA shell, and LabTools active icon pilots. The missing source-side sequence visible against both reviewed targets includes:

- `64841f6 feat(ui): rebuild low fidelity global shell`
- `5f8ea5a feat(ui): add settings external capability shell`
- `749f735 feat(ui): add labtools IA shell`
- `f11aacd feat(ui): expand selective semantic key adoption`
- `e8eb17f feat(ui): improve low fidelity shell usability`
- `417b66f feat(ui): calibrate low fidelity shell visuals`
- `4031dd3 docs(ui): review c2 runtime screenshots`
- `e82a2a9 feat(ui): pilot active LabTools icons`
- `2458ad7 feat(ui): pilot active Settings resource icons`
- `7718cc0 docs/ui: plan LabTools adapter-first implementation`
- `3bf79f4` through `6072aec`

Therefore a direct cherry-pick of only C2b-C2g is high risk.

## 3. Worktree Cleanliness

All reviewed worktrees were clean at audit time:

| Worktree | Status |
| --- | --- |
| UIShell | clean before audit document creation |
| Integration | clean |
| MainLine | clean |
| LabTools | clean |

No target worktree was modified during this audit.

## 4. Merge-base And Divergence

| Comparison | Merge Base | Source-only relevant commits | Target-only relevant commits |
| --- | --- | --- | --- |
| `dev/integration...dev/ui-shell` | `fd2d04e90a25` | UI shell sequence through C2g | `476db6c feat(shared): add external engine manager page`; `a2e9c99 feat(integration): scope labtools l6a1 onto mainline baseline`; `dbf4323 feat(integration): stage meta active runtime integration` |
| `codex/mainline-survival-clinical-carryover...dev/ui-shell` | `67e5b138ae38` | UI shell sequence through C2g | `83749d1 Carry over LabTools local engine closure`; `b8409ec refactor(ui): pilot shared token qss migration` |
| `stable/mainline...dev/ui-shell` | `67e5b138ae38` | UI shell sequence through C2g | `83749d1`; `b8409ec` from the current MainLine worktree path are not identical to `stable/mainline` HEAD; stable branch remains separate reference |

## 5. Non-destructive Merge Simulation

Command pattern used:

```bash
base=$(git merge-base <target> dev/ui-shell)
git merge-tree "$base" <target> dev/ui-shell > /tmp/ui_carryover_<target>_merge_tree.txt
```

Results:

| Target | `changed in both` count | Conflict marker count | Audit result |
| --- | ---: | ---: | --- |
| `dev/integration` | 13 | 30 | Not safe for blind merge/cherry-pick. Manual reconciliation required. |
| `codex/mainline-survival-clinical-carryover` | 16 | 42 | Not safe for blind merge/cherry-pick. Manual reconciliation required. |

High-conflict surfaces:

- `app/shell/main_window.py`
- `app/shared/semantic_keys.py`
- UI docs already modified or absent across target histories
- broad UI shell and Settings/LabTools surfaces

`app/labtools_runtime.py` and LabTools focused tests are source-only additions relative to both reviewed targets, but they depend on the current `app/shell/main_window.py` structure and semantic key registry.

## 6. File-level Carry-over Matrix

Detailed matrix:

`docs/ui/UI_C2h_labtools_mainline_integration_carryover_matrix_20260522.csv`

Summary:

| File / Area | Integration Status | MainLine Status | Carry-over Risk |
| --- | --- | --- | --- |
| `app/shell/main_window.py` | changed in both | changed in both | High |
| `app/labtools_runtime.py` | missing in target | missing in target | Medium |
| `app/shared/semantic_keys.py` | missing in target comparison | missing in target comparison | Medium |
| `tests/ui/test_labtools_*.py` | missing in target | missing in target | Medium |
| UI-C2 docs | missing in target | missing in target | Low to medium |
| icon/resource docs and active assets | mostly source-only | mostly source-only | Medium; carry only if UI icon registry paths are also reconciled |

## 7. Integration Target Audit

Integration target state:

- Branch: `dev/integration`
- HEAD: `ea57a495d682`
- Worktree clean.

Observed target-side relevant commits:

- `476db6c feat(shared): add external engine manager page`
- `a2e9c99 feat(integration): scope labtools l6a1 onto mainline baseline`
- `dbf4323 feat(integration): stage meta active runtime integration`

Risks:

1. `app/shell/main_window.py` has target-specific Integration changes and source-specific UI shell changes.
2. `app/labtools_runtime.py` does not exist in Integration and must be added with its read-only/no-store guarantees.
3. Semantic key additions and LabTools icon/resource registries may be prerequisites before the LabTools pages render.
4. Integration may already carry older LabTools L6A1 concepts; those must not override the UI-C2 boundary rules:
   - no default `~/.labtools` writes
   - no save/export/history activation
   - no ImageJ/Fiji first-level LabTools entry
   - no ELISA backend claim
   - no macro/auto ROI/auto cell counting/auto band recognition

Recommended Integration sequence:

1. Create a local audit/merge branch from `dev/integration`.
2. Carry over prerequisite UI shell/semantic key changes first, not C2b-C2g alone.
3. Manually reconcile `app/shell/main_window.py`.
4. Add `app/labtools_runtime.py` and LabTools focused tests.
5. Run focused tests:
   - `tests/ui/test_labtools_shell.py`
   - `tests/ui/test_labtools_navigation_shell.py`
   - `tests/ui/test_labtools_general_calculator_ui.py`
   - `tests/ui/test_labtools_reagent_preparation_ui.py`
   - `tests/ui/test_labtools_wb_loading_ui.py`
   - `tests/ui/test_labtools_boundary_pages.py`
6. Only after source smoke passes should packaging-specific validation be planned.

## 8. MainLine Target Audit

MainLine reviewed state:

- Worktree branch: `codex/mainline-survival-clinical-carryover`
- HEAD: `7bcdb7f53430`
- Separate stable branch: `stable/mainline` at `be8c924336f4`
- Worktree clean.

Observed target-side relevant commits:

- `83749d1 Carry over LabTools local engine closure`
- `b8409ec refactor(ui): pilot shared token qss migration`

Risks:

1. MainLine has its own UI token/shared style migration work, which may overlap with `dev/ui-shell` low/mid fidelity style changes.
2. MainLine has local LabTools engine closure work; it may overlap semantically with `app/labtools_runtime.py` and no-store/no-export boundaries.
3. `app/shell/main_window.py` has higher merge conflict count than Integration in merge simulation.
4. The current MainLine worktree is not on `stable/mainline`; do not overwrite stable blindly.

Recommended MainLine sequence:

1. Decide whether carry-over target is the current MainLine worktree branch or `stable/mainline`.
2. If the current worktree branch is the target, create a local carry-over branch from `codex/mainline-survival-clinical-carryover`.
3. Reconcile token/style migration before importing UI-C2 widgets.
4. Reconcile LabTools local engine closure with `app/labtools_runtime.py`.
5. Bring over focused tests and run them before any packaging work.
6. Keep `stable/mainline` untouched until the carry-over branch is verified.

## 9. Carry-over Safety Decision

Decision: do not do a direct merge or cherry-pick in the current state.

Reason:

- Non-destructive merge simulation shows conflicts for both Integration and MainLine.
- UI-C2b-C2g depend on earlier UI shell stages.
- `app/shell/main_window.py` is a high-conflict shared surface.
- Target branches contain their own domain changes.

Safe carry-over should be staged and local.

Minimum safe carry-over package:

1. UI shell prerequisites:
   - global shell rebuild
   - Settings shell/resource shell
   - semantic key registry
   - LabTools IA shell
   - relevant icon/resource registry changes
2. LabTools UI-C2 runtime files:
   - `app/labtools_runtime.py`
   - reconciled `app/shell/main_window.py`
3. Focused tests:
   - all `tests/ui/test_labtools_*.py`
4. Documentation:
   - UI-C2a plan/contracts/view model
   - UI-C2g closure audit and matrix
   - this carry-over audit and matrix

## 10. Verification Commands

| Command | Result |
| --- | --- |
| `git status --short` in UIShell | Clean before audit document creation |
| `git -C .../Integration status --short` | Clean |
| `git -C .../MainLine status --short` | Clean |
| `git -C .../LabTools status --short` | Clean |
| `git branch --all --verbose --no-abbrev` | Reviewed local branches and heads |
| `git worktree list --porcelain` | Reviewed local worktrees |
| `git merge-base dev/ui-shell dev/integration` | `fd2d04e90a25` |
| `git merge-base dev/ui-shell codex/mainline-survival-clinical-carryover` | `67e5b138ae38` |
| `git merge-base dev/ui-shell stable/mainline` | `67e5b138ae38` |
| `git merge-tree ... dev/integration dev/ui-shell` | Simulated; conflicts detected |
| `git merge-tree ... codex/mainline-survival-clinical-carryover dev/ui-shell` | Simulated; conflicts detected |
| CSV structure check for `docs/ui/UI_C2h_labtools_mainline_integration_carryover_matrix_20260522.csv` | Passed; 21 rows with required columns |
| `git diff --check` | Passed |
| `git diff --cached --check` | Passed after staging audit docs |

No tests were run in this audit because no runtime code was modified.

## 11. Next Recommendation

Recommended next stage:

`UI-C2h.1 Integration local carry-over planning`

Scope:

- Create an explicit local carry-over plan from `dev/integration`.
- List prerequisite commits to carry before UI-C2b-C2g.
- Define manual reconciliation strategy for `app/shell/main_window.py`.
- Define focused test gate and source smoke gate.
- Still do not push, package, or touch UI-B10.

Alternative:

`UI-C2h.2 MainLine carry-over planning`

Only choose this if the target branch is clarified as either `codex/mainline-survival-clinical-carryover` or `stable/mainline`.

## 12. Non-modification Statement

This audit did not modify Integration, MainLine, LabTools, app code, tests, active assets, scripts, or `dist/**`. It did not merge, cherry-pick, push, package, run package smoke, run a packaged app, or touch App icon / Finder icon / `.icns` / Info.plist / LaunchServices.
