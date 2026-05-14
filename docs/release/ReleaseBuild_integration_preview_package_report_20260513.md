# ReleaseBuild Integration Preview Package Report - 2026-05-13

## Decision

`INTEGRATION_PREVIEW_PACKAGE_BUILT`

ReleaseBuild generated a separate desktop app bundle from Integration-approved source `7dd4256`.

No MainLine source was modified. No module branch was merged. No remote push was performed.

## Package

| Item | Result |
| --- | --- |
| Package path | `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild/dist/BioMedPilot Integration Preview.app` |
| App name | `BioMedPilot Integration Preview` |
| Integration source commit | `7dd4256` |
| Integration readiness report | `docs/integration/Integration_package_readiness_audit_rerun_20260513.md` |
| ReleaseBuild executor base commit | `d2bc191` |
| Packaging mode | `local-python-launcher` |
| Network downloads | not used |
| Packaging command path | ReleaseBuild packaging executor, with Integration worktree as package `repo_root` |

## Scope

Packaged source is limited to current Integration-approved source:

- Bioinformatics: B5 result/report loop only.
- Meta: M10-M13 Developer Preview/testing only.
- LabTools: L6A.1 ROI export hardening only.
- UIShell: not used as preview source.
- ReleaseBuild: packaging executor only.

The package is not a formal release and does not imply scientific, clinical, regulatory, production, or publication readiness.

## Preflight

| Check | Result |
| --- | --- |
| ReleaseBuild branch | `dev/release-internal-test` |
| ReleaseBuild HEAD before package/report changes | `d2bc191` |
| ReleaseBuild dirty status before task | untracked `docs/release/ReleaseBuild_handoff_report_20260513.md` only |
| Integration commit availability | `7dd4256` resolved and was current in `/Users/changdali/Developer/biomedpilot v1.0/Integration` |
| Output path preflight | `dist/BioMedPilot Integration Preview.app` did not exist before packaging |
| Desktop Dev app | `/Users/changdali/Desktop/BioMedPilot Dev.app` existed but was not targeted or overwritten |
| Old formal app | `/Users/changdali/Desktop/BioMedPilot.app` was absent and was not targeted |

## Tests

Preflight and package validation:

- `git diff --check`: passed
- `python3 -m app.main --smoke-test`: passed from ReleaseBuild source, `git_head=d2bc191`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_module_boundary_contract.py -q`: `5 passed`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_package_app.py tests/test_versioned_packaged_entry.py -q`: `3 passed`

Packaged app smoke:

```text
BioMedPilot / 医研智析
app_version=0.1.0-internal-beta
app_channel=Developer Preview / testing
launch_mode=packaged-local-python
app_root=/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild/dist/BioMedPilot Integration Preview.app/Contents/Resources/app
git_head=7dd4256
workspace_entries=3
bioinformatics_features=5
meta_analysis_features=7
labtools_features=4
pyside6_available=True
```

## Metadata verification

| Field | Value |
| --- | --- |
| `BUILD_INFO.app_name` | `BioMedPilot Integration Preview` |
| `BUILD_INFO.git_head` | `7dd4256` |
| `BUILD_INFO.channel` | `Developer Preview / testing` |
| `BUILD_INFO.launch_mode` | `packaged-local-python` |
| `CFBundleName` | `BioMedPilot Integration Preview` |
| `CFBundleDisplayName` | `BioMedPilot Integration Preview` |
| `CFBundleExecutable` | `BioMedPilot Integration Preview` |
| `BioMedPilotGitHead` | `7dd4256` |

ReleaseBuild metadata logic was tightened so `CFBundleDisplayName` also follows the requested app name. The generated Integration Preview bundle was corrected in place; no other app bundle was modified.

## Overwrite confirmation

- Did not overwrite `/Users/changdali/Desktop/BioMedPilot Dev.app`.
- Did not overwrite `/Users/changdali/Desktop/BioMedPilot.app`.
- Did not overwrite any pre-existing `BioMedPilot Integration Preview.app`; the output path was clear before packaging.
- Existing ignored `dist/BioMedPilot.app` in ReleaseBuild was not the target and was not used as the Integration Preview app.

## Manual inspection readiness

`BioMedPilot Integration Preview.app` is ready for manual inspection as an Integration Preview desktop test package.

Manual inspection should verify launch, module visibility, and the approved Integration Preview surfaces only. Any next promotion to MainLine or a formal desktop app must be covered by a separate scoped validation report.
