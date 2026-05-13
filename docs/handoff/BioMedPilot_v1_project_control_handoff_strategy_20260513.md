# BioMedPilot v1.0 Project Control Handoff Versioning Strategy Audit

审计日期：2026-05-13
审计工作区：`/Users/changdali/Developer/biomedpilot v1.0/MainLine`
分支：`stable/mainline`
审计类型：总控 handoff 版本化策略审计

## 1. Scope

本阶段只审计总控 handoff 的版本化策略，不开发业务功能，不修改 Bioinformatics、Meta、LabTools、AI、Vocabulary、UIShell、Integration 或 ReleaseBuild 的业务代码。

本报告是 MainLine 内的只读审计文档。它不移动、不删除、不提交、不重写以下总控 handoff 原文件：

```text
/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/current_handoff_20260513.md
```

## 2. Required Files Read

- `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/current_handoff_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/CODEX.md`
- `/Users/changdali/Developer/biomedpilot v1.0/README_总说明.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/handoff/Global_Development_Manual.md`

`01_ProjectControl/Global_Development_Manual.md` and `MainLine/docs/handoff/Global_Development_Manual.md` were checked with `cmp`; they are byte-for-byte synchronized at audit time.

No conflict was found between the global manual and this audit task. The global manual permits documentation-only governance work and requires preserving unrelated dirty files, avoiding remote writes, and committing only in-scope files after validation.

## 3. Root And Handoff Tracking Findings

### 3.1 Local root is not a Git worktree

Command:

```bash
git rev-parse --show-toplevel
```

Run from:

```text
/Users/changdali/Developer/biomedpilot v1.0
```

Result:

```text
fatal: not a git repository (or any of the parent directories): .git
```

Finding: the v1.0 local root is a development management layer, not a normal Git worktree.

### 3.2 Worktrees are attached to the bare repository

Command:

```bash
git --git-dir=_repo.git worktree list --porcelain
```

Observed worktrees:

| Worktree | Branch | HEAD |
| --- | --- | --- |
| `_repo.git` | bare repository | not editable as a worktree |
| `AI` | `dev/ai-gateway` | `2a2d1da444f62746d0728d9b5764995da5da7701` |
| `Bioinformatics` | `dev/bioinformatics` | `f10d4a49e42e6091344b52503e0f9e9b9084dc5d` |
| `Integration` | `dev/integration` | `ba41dca1c2b3664312af3f93bacdbac27f3d72fa` |
| `LabTools` | `dev/labtools` | `3ce03b9fdd51ffd807cbccb007b247f8195a295e` |
| `MainLine` | `stable/mainline` | `4e5c4ac1ee7017fb8732f9fdae1f66e5d17ee2d2` |
| `Meta` | `dev/meta-analysis` | `76f9a0ee6017ba47519c969d5a987698691d68a1` |
| `ReleaseBuild` | `dev/release-internal-test` | `c369b262f371778c6ab09aea27adca448493465b` |
| `UIShell` | `dev/ui-shell` | `391c882c560760fd09b1b95cd6d3c3ab89d38e8e` |
| `Vocabulary` | `dev/shared-vocabulary` | `9c73d6a0af61f7b38e020200f9eb1c31b1a3aada` |

### 3.3 current_handoff_20260513.md is not in the audited branch trees

Commands:

```bash
git --git-dir=_repo.git log --all --format='%h %D %s' -- '01_ProjectControl/current_handoff_20260513.md'
git --git-dir=_repo.git ls-tree -r --name-only stable/mainline dev/bioinformatics dev/meta-analysis dev/integration dev/shared-vocabulary dev/ui-shell dev/labtools dev/ai-gateway dev/release-internal-test | rg '^01_ProjectControl/current_handoff_20260513\.md$'
```

Observed result: both commands produced no matching tracked file or historical commit for `01_ProjectControl/current_handoff_20260513.md`.

Finding: the current handoff file exists in the local root control layer, but it is not currently part of the audited branch histories.

## 4. Worktree Dirty State Audit

Command:

```bash
for d in MainLine Bioinformatics Meta Integration Vocabulary UIShell LabTools AI ReleaseBuild; do
  git -C "$d" branch --show-current
  git -C "$d" rev-parse --short HEAD
  git -C "$d" status --short
done
```

Live status at audit time:

| Worktree | Branch | HEAD | Dirty state |
| --- | --- | --- | --- |
| MainLine | `stable/mainline` | `4e5c4ac` | dirty before this report: `app/meta_analysis/workspace.py`, `tests/meta_analysis/test_mainline_meta_contract.py` |
| Bioinformatics | `dev/bioinformatics` | `f10d4a4` | clean |
| Meta | `dev/meta-analysis` | `76f9a0e` | clean |
| Integration | `dev/integration` | `ba41dca` | dirty: large staged Meta runtime integration set plus `app/shell/main_window.py`, `app/ui_style_tokens.py`, `tests/meta_analysis/test_mainline_meta_contract.py`, `tests/ui/test_module_selection.py` |
| Vocabulary | `dev/shared-vocabulary` | `9c73d6a` | clean |
| UIShell | `dev/ui-shell` | `391c882` | clean |
| LabTools | `dev/labtools` | `3ce03b9` | dirty: untracked `app/labtools/image_analysis/` |
| AI | `dev/ai-gateway` | `2a2d1da` | clean |
| ReleaseBuild | `dev/release-internal-test` | `c369b26` | clean |

The MainLine dirty files listed above existed before this audit report was created and were left untouched. This audit adds only:

```text
MainLine/docs/handoff/BioMedPilot_v1_project_control_handoff_strategy_20260513.md
```

## 5. Purpose Of current_handoff_20260513.md

`current_handoff_20260513.md` is a cross-session control document for reducing context loss. It records the current state of the major worktrees, including:

- current branch and HEAD commit,
- stage completion status,
- known blockers,
- recommended next steps,
- recent validation log references,
- dirty state warnings.

It is especially useful because the v1.0 local root contains several active worktrees, and the active state can diverge quickly across MainLine, module worktrees, Integration, and ReleaseBuild.

## 6. Current Non-Versioned Risk

Because `01_ProjectControl/current_handoff_20260513.md` is outside all audited worktrees, it currently has these risks:

- No branch history: changes to the file are not captured by `stable/mainline` or module branch commits.
- No commit diff: later agents cannot use Git history to see when the handoff changed or why.
- No review boundary: accidental edits may not be visible during ordinary worktree reviews.
- No recovery path through Git: accidental deletion or corruption would depend on filesystem backup rather than repository history.
- Snapshot drift: the handoff can become stale as worktree HEADs and dirty states change, as already observed during this audit.

This risk is about project governance traceability. It does not imply the handoff content is wrong, but it does mean the file is not protected by the current repository workflow.

## 7. Optional Management Schemes

### A. Keep as a root-level manually maintained file

Description: keep `01_ProjectControl/current_handoff_20260513.md` exactly where it is and update it manually when worktree state changes.

Advantages:

- Lowest operational friction.
- Preserves the current project-control layout.
- Avoids creating another repository or changing branch ownership.
- Clear separation between root governance and code worktrees.

Risks:

- No Git history unless another backup mechanism is used.
- Easy for updates to be missed after commits in individual worktrees.
- Easy for future agents to assume it is versioned when it is not.

Best use: short-term continuity while the project structure is still settling.

### B. Initialize `01_ProjectControl/` as an independent Git repository

Description: make `01_ProjectControl/` its own Git repository for local governance documents.

Advantages:

- Provides history, diffs, and rollback for control documents.
- Keeps governance documents separate from application code.
- Avoids coupling control updates to MainLine commits.

Risks:

- Adds another repository to manage.
- Requires a clear remote / backup decision if persistence beyond local disk is needed.
- Future agents must distinguish the project-control repository from `_repo.git` and worktrees.

Best use: medium-term if `01_ProjectControl/` remains the authoritative control layer and needs real version history.

### C. Maintain a read-only mirror summary in `MainLine/docs/handoff/`

Description: keep the authoritative handoff in `01_ProjectControl/`, and maintain a tracked MainLine summary snapshot under `MainLine/docs/handoff/`.

Advantages:

- Gives MainLine a versioned pointer to current governance state.
- Fits existing handoff-document conventions.
- Does not require creating a new repository.
- Makes later MainLine agents aware that root handoff exists and may be newer.

Risks:

- Mirror can drift from the root source unless update rules are explicit.
- MainLine is not the whole development management layer, so a mirror must not be treated as authoritative when the root file exists.
- Summaries may omit useful operational detail.

Best use: recommended short-term approach together with option A.

### D. Put `01_ProjectControl/` under a unified control repository

Description: create or designate a single governance repository that tracks `01_ProjectControl/`, selected root handoff material, migration records, and policy documents.

Advantages:

- Strongest long-term traceability.
- Can include governance history without mixing it into product code branches.
- Better suited for multi-worktree, multi-module coordination.

Risks:

- Requires a deliberate repository ownership decision.
- Requires migration planning for existing control docs, archive docs, and handoff copies.
- Requires clear policy for what remains local-only versus versioned.

Best use: long-term once the v1.0 governance layout is stable.

## 8. Recommendation

Short-term recommendation:

- Use option A as the authoritative source for the current root handoff.
- Add option C as a tracked MainLine read-only mirror summary for discoverability and Git traceability.
- Keep the mirror explicitly labeled as a snapshot and not authoritative over `01_ProjectControl/current_handoff_20260513.md`.

Long-term recommendation:

- Move toward option D or option B after a user-approved governance decision.
- If root project control documents remain central across all worktrees, option D is cleaner than tying them to MainLine.
- If the scope stays local-only and lightweight, option B is enough.

## 9. Operations Requiring User Approval

The following actions must not be performed without explicit user approval:

- Move, rename, delete, or rewrite `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/current_handoff_20260513.md`.
- Initialize a new Git repository under `01_ProjectControl/`.
- Add `01_ProjectControl/` to any existing worktree or repository.
- Create a unified control repository.
- Add remotes, push governance documents, or handle GitHub credentials.
- Convert the MainLine mirror summary into the authoritative source.
- Delete or archive existing handoff, migration, audit, or project-control documents.
- Commit unrelated dirty files in MainLine, Integration, LabTools, or any other worktree.

## 10. Verification Plan For This Audit

Required minimal verification for this documentation-only audit:

```bash
git -C MainLine diff --check
git -C MainLine status --short --branch
```

Full pytest is intentionally not required for this stage because the task only adds a governance audit document under `MainLine/docs/handoff/` and does not modify runtime code, tests, package scripts, UI behavior, data assets, or business module logic.

If `git diff --check` reports issues in pre-existing unrelated dirty files, those files should remain untouched in this stage and the failure should be reported instead of silently fixing unrelated work.

## 11. Verification Results

Command:

```bash
git diff --check
```

Run from:

```text
/Users/changdali/Developer/biomedpilot v1.0/MainLine
```

Result: PASS, no output.

Command:

```bash
git status --short --branch
```

Result before committing this report:

```text
## stable/mainline
 M app/meta_analysis/workspace.py
 M tests/meta_analysis/test_mainline_meta_contract.py
?? docs/handoff/BioMedPilot_v1_project_control_handoff_strategy_20260513.md
```

The two modified MainLine files were pre-existing unrelated dirty files and were left untouched. Only this audit report is in scope for the commit.
