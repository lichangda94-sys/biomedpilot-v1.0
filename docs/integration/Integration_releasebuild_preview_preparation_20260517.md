# Integration ReleaseBuild Preview Preparation - 2026-05-17

## Decision

Status: `READY_FOR_RELEASEBUILD_PREVIEW_PACKAGING_AFTER_COMMIT`.

The current Integration source was reviewed after the latest LabTools calculator
integration commit and now has a dedicated package switch for generating
`BioMedPilot Integration Preview.app` without overwriting the generic
`BioMedPilot.app` or `BioMedPilot Dev.app` entries.

This preparation is limited to packaging mechanics, metadata, validation, and
handoff evidence. It does not promote any module to public, production, clinical,
regulatory, or publication-grade status.

## Source Review

Latest Integration commit before this preparation:

```text
93dc1ef Integrate latest LabTools calculator updates
```

Latest commit summary:

- LabTools formula solver and result formatting were added.
- LabTools concentration, dilution, solution preparation, unit conversion, and
  reagent template logic were updated.
- LabTools preparation record storage and tests were added.
- LabTools audit and rectification reports were added.

The worktree was clean before this preparation began.

## Packaging Preparation Change

`scripts/package_app.py` now supports:

```bash
python3 scripts/package_app.py --integration-preview --smoke-test
```

Preview bundle identity:

| Field | Value |
| --- | --- |
| Bundle path | `dist/BioMedPilot Integration Preview.app` |
| `CFBundleName` | `BioMedPilot Integration Preview` |
| `CFBundleDisplayName` | `BioMedPilot Integration Preview / 医研智析` |
| `CFBundleExecutable` | `BioMedPilotIntegrationPreview` |

The default `python3 scripts/package_app.py --smoke-test` behavior remains
compatible with the existing generic `dist/BioMedPilot.app` local launcher.

## Validation Run

Passed:

```text
python3 -m pytest tests/test_package_app.py tests/test_versioned_packaged_entry.py tests/test_unified_entry.py -q
8 passed in 6.55s
```

```text
git diff --check
passed
```

```text
python3 -m app.main --smoke-test
app_version=0.1.0-internal-beta
app_channel=Developer Preview / testing
launch_mode=source
git_head=93dc1ef
bioinformatics_features=5
meta_analysis_features=7
pyside6_available=True
```

```text
python3 scripts/package_app.py --integration-preview --smoke-test
app_path=dist/BioMedPilot Integration Preview.app
git_head=93dc1ef
mode=local-python-launcher
executable=BioMedPilotIntegrationPreview
signing_status=ad_hoc_signed
standalone=false
network_downloads=false
```

```text
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot Integration Preview.app
passed
```

```text
dist/BioMedPilot Integration Preview.app/Contents/MacOS/BioMedPilotIntegrationPreview -psn_0_12345 --smoke-test
passed
```

```text
open -W -n dist/BioMedPilot Integration Preview.app --args --smoke-test
passed
```

Host/runtime architecture check:

```text
uname -m -> arm64
packaging Python -> universal x86_64/arm64
platform_machine -> arm64
Pillow import -> ok
PySide6 import -> ok
```

## ReleaseBuild Handoff Constraints

ReleaseBuild may package only the Integration-approved preview bundle:

- generate `BioMedPilot Integration Preview.app`;
- keep `CFBundleExecutable=BioMedPilotIntegrationPreview`;
- verify `BUILD_INFO.json`, `Info.plist`, codesign, direct packaged smoke,
  `-psn_*` handling, and `open -W -n`;
- do not overwrite `/Users/changdali/Desktop/BioMedPilot Dev.app`;
- do not overwrite any generic or formal `BioMedPilot.app`;
- do not treat ignored `dist/` artifacts as source-controlled release evidence;
- after this preparation commit lands, rebuild the preview bundle so
  `BUILD_INFO.git_head` matches the committed preparation HEAD.

The current sibling `ReleaseBuild` worktree is on `dev/release-internal-test` at
`0e158a2` and is not an ancestor of Integration `93dc1ef`. It also has an
untracked `docs/release/ReleaseBuild_handoff_report_20260513.md`. Do not package
from that existing ReleaseBuild checkout until it is deliberately synced to this
Integration-approved source and its local untracked report is handled.
