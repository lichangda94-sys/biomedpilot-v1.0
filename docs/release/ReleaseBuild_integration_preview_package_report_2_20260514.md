# ReleaseBuild Integration Preview Package Report 2 - 2026-05-14

## Decision

Status: `PACKAGED_AND_SMOKE_PASSED`.

ReleaseBuild generated the second `BioMedPilot Integration Preview.app` package from the Integration-approved source after the Bioinformatics B5.6-B5.11 scoped carry-over readiness rerun passed.

## Package

| Field | Value |
| --- | --- |
| Package path | `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild/dist/integration-preview-20260514-5c14f22/BioMedPilot Integration Preview.app` |
| App name | `BioMedPilot Integration Preview` |
| Source root | `/Users/changdali/Developer/biomedpilot v1.0/Integration` |
| Source git head | `5c14f22` |
| ReleaseBuild branch | `dev/release-internal-test` |
| ReleaseBuild HEAD | `077f1b4` |
| Launch mode | `packaged-local-python` |
| Channel | `Developer Preview / testing` |

The previous ignored package at `dist/BioMedPilot Integration Preview.app` was not overwritten. This second package was written to a new dist subdirectory.

## Metadata

`BUILD_INFO.json`:

```json
{
  "app_name": "BioMedPilot Integration Preview",
  "version": "0.1.0-internal-beta",
  "bundle_version": "0.1.0",
  "channel": "Developer Preview / testing",
  "launch_mode": "packaged-local-python",
  "source_root": "/Users/changdali/Developer/biomedpilot v1.0/Integration",
  "git_head": "5c14f22"
}
```

`Info.plist` key checks:

- `CFBundleName`: `BioMedPilot Integration Preview`
- `CFBundleDisplayName`: `BioMedPilot Integration Preview`
- `CFBundleExecutable`: `BioMedPilotIntegrationPreview`
- `BioMedPilotGitHead`: `5c14f22`
- `BioMedPilotChannel`: `Developer Preview / testing`

## Validation

Passed:

```text
codesign --verify --deep --strict --verbose=2 dist/integration-preview-20260514-5c14f22/BioMedPilot\ Integration\ Preview.app
valid on disk; satisfies its Designated Requirement

dist/integration-preview-20260514-5c14f22/BioMedPilot\ Integration\ Preview.app/Contents/MacOS/BioMedPilotIntegrationPreview --smoke-test
launch_mode=packaged-local-python
git_head=5c14f22
pyside6_available=True

dist/integration-preview-20260514-5c14f22/BioMedPilot\ Integration\ Preview.app/Contents/MacOS/BioMedPilotIntegrationPreview -psn_0_12345 --smoke-test
launch_mode=packaged-local-python
git_head=5c14f22
pyside6_available=True

python3 -m pytest tests/test_package_app.py tests/test_versioned_packaged_entry.py -q
5 passed in 5.97s
```

## Safety Boundaries

- Did not package from `dev/bioinformatics` or any other module branch.
- Did not whole-branch merge Bioinformatics, Meta, LabTools, UIShell, or ReleaseBuild.
- Did not overwrite `/Users/changdali/Desktop/BioMedPilot Dev.app`.
- Did not create or overwrite `/Users/changdali/Desktop/BioMedPilot.app`.
- Did not overwrite the first ignored `dist/BioMedPilot Integration Preview.app`.
- Did not promote this package to MainLine, stable, production, clinical, regulatory, or publication-grade status.

## Result

The second `BioMedPilot Integration Preview.app` is ready for manual desktop inspection from the package path above.
