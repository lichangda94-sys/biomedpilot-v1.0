# UI-C3b Integration / MainLine Scoped Carry-over Audit

Date: 2026-05-24

## 1. Scope

This audit evaluates what can safely move from the current `dev/ui-shell` UI track toward Integration/MainLine, and what must remain scoped, blocked, or require human decision.

This stage is audit-only. It does not merge branches, switch branches, push, package, run a packaged app, modify desktop entry, or touch App icon / Finder icon / `.icns` / Info.plist / LaunchServices.

## 2. Current Worktree Snapshot

Current UIShell:

- path: `/Users/changdali/Developer/biomedpilot v1.0/UIShell`
- branch: `dev/ui-shell`
- HEAD: `a8ee3d7 docs(ui): audit Meta Analysis adapter readiness`
- recent completed UI stages:
  - `402ebba feat(ui): harden LabTools adapter error states`
  - `a0eb47d docs(ui): audit Bioinformatics formal DEG readiness`
  - `a8ee3d7 docs(ui): audit Meta Analysis adapter readiness`

Other worktrees:

| Worktree | Branch | HEAD | Status |
| --- | --- | --- | --- |
| Integration | `codex/integration-labtools-ui-c2-carryover` | `1937aae` | clean |
| MainLine | `codex/mainline-survival-clinical-carryover` | `7bcdb7f` | clean |
| LabTools | `dev/labtools` | `9b77128` | dirty |
| Bioinformatics | `dev/bioinformatics` | `70f93df` | has untracked docs/project_storage |
| Meta | `dev/meta-analysis` | `3aad58a` | clean |
| ReleaseBuild | `codex/releasebuild-formal-deg-carryover` | `cb0a21d` | not audited for UI-B10 in this stage |

## 3. Dirty / Untracked Boundary

UIShell currently has uncommitted local_data-related changes outside the UI-C3g/C3a audits:

- `app/labtools_runtime.py`
- `app/shell/main_window.py`
- `tests/ui/test_labtools_shell.py`
- `tests/labtools/`
- `tests/ui/test_labtools_local_data_read_integration.py`

These are not part of the committed UI-C3g adapter error-state hardening scope. They must be reviewed as a separate LabTools local data read integration stage before any Integration/MainLine carry-over.

LabTools worktree also has dirty local data adapter changes:

- `labtools/local_data/datasource_adapter.py`
- `tests/labtools/test_labtools_datasource_adapter.py`

Bioinformatics worktree has untracked handoff/project storage files:

- `docs/bioinformatics/Bioinformatics_handoff_report_20260513.md`
- `project_storage/bioinformatics/`

Because of these dirty/untracked states, this audit does not perform automatic carry-over.

## 4. Safe Carry-over Candidates

The following UIShell commits are safe candidates for scoped carry-over after local dirty changes are resolved:

| Commit | Scope | Carry-over decision |
| --- | --- | --- |
| `ea29b1a` | current UI completion audit | docs-only, safe |
| `aefe9fd` | LabTools save/export/history closure audit | docs-only, safe |
| `402ebba` | LabTools adapter error-state hardening | runtime/test/docs, safe if LabTools local_data diff is excluded |
| `a0eb47d` | Bioinformatics formal DEG readiness audit | docs-only, safe |
| `a8ee3d7` | Meta Analysis adapter readiness audit | docs-only, safe |

Potentially safe but needs scoped review:

- LabTools C3 save/export/history runtime commits from `edfa2a5`, `85fcdf4`, `82de31d`
- Bioinformatics C2 gated UI chain through `a3a7f2e`
- Meta C2 gated UI chain through `d6e3542`

## 5. Must Not Carry Wholesale

Do not wholesale merge these surfaces:

- `dev/bioinformatics` into UIShell or Integration: branch contains broader B16 / legacy / project storage changes and untracked files.
- MainLine formal DEG / survival / legacy pipeline into UIShell: MainLine has formal execution commits that exceed current gated UI readiness.
- LabTools local_data dirty changes: these need a separate reviewed integration stage.
- ReleaseBuild packaging/App icon/LaunchServices: belongs to UI-B10 and must not be mixed with ordinary UI carry-over.

## 6. Scoped Carry-over Rules

Before any carry-over:

1. current target worktree must be clean or changes must be explicitly staged by scope
2. source worktree dirty changes must be audited
3. docs-only carry-over can be cherry-picked first
4. runtime carry-over must keep tests with it
5. no formal executor can become enabled by merge side effect
6. no report/export file write can become enabled by merge side effect
7. no App icon / Finder / LaunchServices / packaging change can enter ordinary UI carry-over

## 7. Recommended Carry-over Order

Recommended:

1. Resolve or explicitly stage/commit LabTools local_data read integration separately.
2. Cherry-pick docs-only UI completion/readiness audits into Integration.
3. Cherry-pick LabTools C3g hardening with its focused test.
4. Re-run LabTools, Bioinformatics, Meta, shared RRE, source smoke.
5. Only then evaluate whether Integration should receive Bioinformatics/Meta C2 gated UI chains.
6. Keep MainLine formal DEG/survival carry-over separate from UIShell gated UI until the formal readiness gates are complete.

## 8. UI-B10 Readiness

UI-B10 should not begin until one of these is true:

- the user explicitly approves proceeding despite ordinary UI/runtime work still changing
- or Integration/MainLine carry-over is complete and worktrees are clean

UI-B10 will need separate decisions for:

- final App icon asset
- Finder icon / `.icns` / iconset
- Info.plist binding
- LaunchServices validation
- package smoke and packaged app runtime
- signing / codesign boundary if packaging requires it

## 9. Verification

Audit commands run:

- `git status --short`
- `git branch --show-current`
- `git branch --list --all --no-color`
- `git worktree list`
- `git log --oneline --decorate -25`
- per-worktree `git status --short` and `git log --oneline`

CSV structure check and source smoke are recorded after document generation.

Verification results:

| Command | Result |
| --- | --- |
| CSV structure check for `docs/ui/UI_C3b_integration_mainline_scoped_carryover_matrix_20260524.csv` | passed, 13 rows |
| `python3 -m app.main --smoke-test` | passed |
| `git diff --check` | passed |

## 10. Conclusion

Integration/MainLine carry-over is not blocked by the completed UI audit commits themselves. It is blocked by scope control:

- UIShell has unrelated local_data changes in progress.
- LabTools has dirty local_data adapter changes.
- Bioinformatics has untracked handoff/project storage artifacts.
- MainLine contains formal DEG/survival work that must not be merged into the gated UI path without a separate formal readiness stage.

Next required human or process decision: decide whether the in-progress LabTools local_data read integration should be completed and committed before Integration carry-over, or parked outside this UI track.
