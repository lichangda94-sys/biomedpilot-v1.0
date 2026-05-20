# ReleaseBuild sync from MainLine pre-package validation - 2026-05-13

## Scope

- Worktree: `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`
- Branch: `dev/release-internal-test`
- Stage: ReleaseBuild sync from MainLine pre-package validation
- Source commit: `73d4cc78c358192a2371eab0e866d26af98fba11` (`stable/mainline`, `feat(mainline): apply meta active runtime`)
- Pre-sync ReleaseBuild HEAD: `7b6cd0a43fc421f493ce739e0dd04ebc0793992b`
- Pre-sync dirty state: clean

## Required Reading And Environment Notes

- Read `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`.
- Read `/Users/changdali/Developer/biomedpilot v1.0/README_总说明.md`.
- Checked ReleaseBuild for a root `CODEX.md` before syncing; no ReleaseBuild-local `CODEX.md` existed at the pre-sync HEAD.
- Confirmed the v1.0 worktree list and kept all modifications inside ReleaseBuild.

## Synchronization Strategy

ReleaseBuild and MainLine were divergent from common ancestor `67e5b138ae38c2350caf7d19d7724f018653f92b`; neither HEAD was an ancestor of the other.

To avoid unnecessary merge history and avoid manual modify/delete conflict choices, this stage used a full-tree checkout/read-tree synchronization to the confirmed MainLine source commit:

```bash
git read-tree --reset -u 73d4cc78c358192a2371eab0e866d26af98fba11
```

After synchronization and before adding this report, `git diff --quiet 73d4cc78c358192a2371eab0e866d26af98fba11 -- .` returned success, confirming the ReleaseBuild working tree matched the MainLine source tree.

One ReleaseBuild-local governance adjustment was then made to the newly added root `CODEX.md`: its worktree name, path, branch, duties, prohibitions, and test list were changed from MainLine wording to ReleaseBuild wording. This avoids future boundary confusion in the ReleaseBuild worktree and removes trailing whitespace flagged by `git diff --check`.

## Inclusion And Exclusion Checks

- Meta active runtime: included from MainLine `73d4cc7`; key active runtime paths now include `app/meta_analysis/workspace.py`, `app/meta_analysis/workflow_pages.py`, `app/meta_analysis/pages/**`, `app/meta_analysis/services/**`, `app/meta_analysis/search/**`, `app/meta_analysis/stats/**`, and `app/meta_analysis/ui_text.py`.
- Meta tests: included from MainLine `73d4cc7`; `tests/meta_analysis` now contains the active runtime, service, workflow, M2/M3, internal beta, UI, report, and regression coverage.
- Shared UI helper latest state: included from MainLine `73d4cc7`; `app/shared/ui/__init__.py`, `app/shared/ui/theme.py`, `app/ui_style_tokens.py`, and `tests/ui/test_shared_ui_theme.py` are present.
- Current MainLine governance/audit documents: included from MainLine `73d4cc7`; current docs include `docs/audit/**`, `docs/handoff/**`, `docs/integration/**`, `docs/ui/**`, `docs/architecture/**`, and `docs/cleanup/**`.
- ReleaseBuild-local root governance: `CODEX.md` is present and now identifies `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild` and `dev/release-internal-test`.
- Legacy Meta runtime exclusion: `app/meta_analysis/legacy/**` is not present after sync.
- Dist/app safety: no tracked `dist/**`, `BioMedPilot.app`, or `Dev.command` paths were part of the source or target tree sync.

## Explicit Non-Actions

- Did not modify Bioinformatics, Meta, LabTools, MainLine, Integration, UIShell, Vocabulary, or AI independent worktrees.
- Did not run formal packaging.
- Did not overwrite `dist/BioMedPilot.app`.
- Did not modify `/Users/changdali/Desktop/BioMedPilot v1.0 Dev.command`.
- Did not push to any remote.
- Did not run `python3 scripts/package_app.py --smoke-test` because that command writes `dist/BioMedPilot.app`; package-smoke behavior was covered by `tests/test_package_app.py` in temporary directories through `scripts/run_tests.py`.

## Validation Results

| Command | Result |
| --- | --- |
| `git diff --check` | passed |
| `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test` | passed; `app_version=0.1.0-internal-beta`, `app_channel=Developer Preview / testing`, `launch_mode=source`, `workspace_entries=2`, `bioinformatics_features=5`, `meta_analysis_features=7`, `pyside6_available=True` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q` | passed; 465 passed |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | passed; 170 passed |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/shared -q` | passed; 225 passed |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q` | passed; 264 passed |
| `python3 scripts/run_tests.py` | passed; 1147 passed |

## Stage Assessment

ReleaseBuild has been synchronized to the MainLine `73d4cc7` pre-package source state, with this ReleaseBuild-specific validation report added afterward. The source tree includes the MainLine Meta active runtime and excludes `app/meta_analysis/legacy/**`.

Based on the completed validation, ReleaseBuild can proceed to the next human-confirmed stage: actual packaging pre-confirmation. Formal packaging and desktop entry refresh remain intentionally unperformed in this stage.
