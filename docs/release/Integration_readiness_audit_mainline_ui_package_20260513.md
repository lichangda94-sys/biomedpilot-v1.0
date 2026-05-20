# Integration Readiness Audit - MainLine Stable UI Package

Date: 2026-05-13

## Scope

- Audit target: first desktop entry check package, MainLine stable UI package.
- Package source: `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`
- Package branch: `dev/release-internal-test`
- Package source HEAD at final package time: the commit containing this report; confirm with packaged `BUILD_INFO.json`.
- Generated app: `/Users/changdali/Desktop/BioMedPilot Dev.app`
- Explicitly not used as package source: `Integration`, `LabTools`
- Explicitly not overwritten: old formal `BioMedPilot.app` desktop entry

## Readiness Decision

- UIShell: allowed into the first MainLine stable UI package.
- ReleaseBuild: allowed as the carrier worktree for the first Dev/Internal Test package.
- Bioinformatics: allowed only as the current MainLine testing-level UI flow; preflight and imported/test outputs remain non-scientific conclusions.
- Meta Analysis: allowed only as the current active runtime testing-level flow; PubMed, statistics, reporting, fulltext, and AI surfaces remain testing-level unless separately validated.
- LabTools: not included in this package. LabTools needs a scoped future integration after its current UI wording and minimal UI tests are complete.
- Integration: not used as package source because it is a comparison/risk-audit worktree with branch divergence from `stable/mainline`.

## Validation Results

| Check | Result |
| --- | --- |
| MainLine `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test` | Passed; `git_head=73d4cc7`, `workspace_entries=2` |
| MainLine `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | Passed; 170 passed |
| MainLine `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_module_boundary_contract.py -q` | Passed; 5 passed |
| ReleaseBuild `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test` | Passed before metadata fix at `git_head=d6f8d25`; passed again after the metadata fix commit; `workspace_entries=2` |
| ReleaseBuild `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_module_boundary_contract.py -q` | Passed; 5 passed |
| ReleaseBuild `git diff --check` | Passed |
| ReleaseBuild packaging metadata tests | Passed; 3 passed |
| ReleaseBuild `python3 scripts/run_tests.py` before metadata fix | Passed; 1147 passed |
| ReleaseBuild `python3 scripts/run_tests.py` after metadata fix | Passed; 1147 passed |
| ReleaseBuild package command | Passed; generated `/Users/changdali/Desktop/BioMedPilot Dev.app` |
| Packaged smoke | Passed; `launch_mode=packaged-local-python`; final `git_head` must match packaged `BUILD_INFO.json` |

## Package Metadata Check

The first package build exposed a metadata mismatch: the app bundle name was `BioMedPilot Dev`, but `BUILD_INFO.json` still wrote the default `BioMedPilot` app name. The packaging script now writes the actual requested `app_name` into `BUILD_INFO.json`, and tests assert this behavior.

Final package metadata:

```text
BUILD_INFO.app_name=BioMedPilot Dev
BUILD_INFO.version=0.1.0-internal-beta
BUILD_INFO.channel=Developer Preview / testing
BUILD_INFO.launch_mode=packaged-local-python
BUILD_INFO.source_root=/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild
BUILD_INFO.git_head=<current ReleaseBuild HEAD at packaging time>
Info.CFBundleName=BioMedPilot Dev
Info.CFBundleExecutable=BioMedPilot Dev
Info.BioMedPilotGitHead=<current ReleaseBuild HEAD at packaging time>
```

## Audit Gates

1. User-walkable loop: pass for UIShell MainLine entry and current Bioinformatics / Meta testing-level flows.
2. MainWindow startup: pass through source smoke and packaged smoke.
3. Cross-module pollution: pass through module boundary contract tests.
4. Raw path / manifest / JSON / schema / developer-only UI exposure: no blocker found for the first stable UI package; package metadata remains internal package metadata.
5. Testing/preflight/imported result scientific conclusion risk: allowed only with testing-level wording; no upgrade to formal Bioinformatics or Meta scientific conclusions.
6. Module tests: pass for selected package gate; ReleaseBuild full suite passed.
7. Package source: pass; generated from ReleaseBuild, not from Integration or LabTools.
8. Dev/Internal Test entry only: pass; generated `BioMedPilot Dev.app`, not the old formal `BioMedPilot.app`.

## Residual Notes

- `ReleaseBuild` had a pre-existing untracked `docs/release/ReleaseBuild_handoff_report_20260513.md`; this audit did not include it.
- `LabTools` had pre-existing uncommitted work and remains excluded from this package.
- The generated app is a local Python launcher, not a standalone installer.
