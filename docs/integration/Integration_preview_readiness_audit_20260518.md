# Integration Preview Readiness Audit - 2026-05-18

Branch: `dev/integration`

HEAD at audit: `8d83bb6 feat(bioinformatics): route AI drafts through role-based gateway`

## Scope

This audit checked whether Meta work after the prior integration handoff still needed to be submitted before building the next Integration Preview.

Relevant Meta-side commits reviewed:

- `c1c89d9` Add Meta OCR fulltext worker skeleton
- `4b0b292` Add PaddleOCR subprocess runner
- `ef868e1` Fix meta workspace refresh and review UX
- `ac25941` Add Meta PaddleOCR fulltext integration
- `77e6145` Package Meta OCR worker with app bundle
- `39a2191` Re-sign app bundle after package smoke
- `2fcc39a` Clear macOS metadata before app signing
- `3aad58a` Handle LaunchServices psn arguments

## Integration Status

The current `dev/integration` branch already contains the required runtime equivalents for the latest preview path:

- Meta OCR / PaddleOCR runtime bridge is present in the integration worktree.
- `biomedpilot_ocr_worker` is included in packaged app resources.
- `scripts/package_app.py` clears extended attributes before ad-hoc signing.
- Integration Preview uses a stable space-free `CFBundleExecutable`: `BioMedPilotIntegrationPreview`.
- `app.main` ignores LaunchServices `-psn_*` arguments.
- Integration Preview smoke reports 3 workspaces: Bioinformatics, Meta Analysis, and LabTools.

No broad merge from `dev/meta-analysis` was performed because `dev/integration` carries newer Bioinformatics and LabTools preview work. A full branch merge would risk reverting integration-specific content.

## Validation

Passed:

```text
python3 -m pytest \
  tests/test_unified_entry.py \
  tests/test_package_app.py \
  tests/test_versioned_packaged_entry.py \
  tests/shared/test_biomedpilot_ocr_worker.py \
  tests/shared/test_local_engines_paddleocr.py \
  tests/meta_analysis/test_paddleocr_subprocess_runner.py \
  tests/meta_analysis/test_ocr_fulltext_workers.py \
  tests/meta_analysis/test_fulltext_parsing_service.py -q

36 passed
```

Passed:

```text
python3 -m app.main --smoke-test -psn_0_12345
```

The command reported:

```text
workspace_entries=3
bioinformatics_features=5
meta_analysis_features=7
labtools_features=5
pyside6_available=True
```

Passed from a non-FileProvider local output directory:

```text
python3 scripts/package_app.py \
  --integration-preview \
  --output-dir "/Users/changdali/Developer/biomedpilot v1.0/PreviewBuild" \
  --smoke-test

codesign --verify --deep --strict --verbose=2 \
  "/Users/changdali/Developer/biomedpilot v1.0/PreviewBuild/BioMedPilot Integration Preview.app"

open -W -n \
  "/Users/changdali/Developer/biomedpilot v1.0/PreviewBuild/BioMedPilot Integration Preview.app" \
  --args --smoke-test

codesign --verify --deep --strict --verbose=2 \
  "/Users/changdali/Developer/biomedpilot v1.0/PreviewBuild/BioMedPilot Integration Preview.app"
```

The packaged app reported `git_head=8d83bb6`, `signing_status=ad_hoc_signed`, and `post_smoke_signing_status=ad_hoc_signed`.

## Preview Artifact

Validated preview artifact:

```text
/Users/changdali/Developer/biomedpilot v1.0/PreviewBuild/BioMedPilot Integration Preview.app
```

A Desktop copy was also built at:

```text
/Users/changdali/Desktop/BioMedPilot Integration Preview.app
```

Desktop is managed by macOS FileProvider on this machine. After LaunchServices opens the app from Desktop, FileProvider may reattach root-level `com.apple.FinderInfo` / `com.apple.fileprovider.fpfs#P` xattrs. That can make a strict post-launch `codesign --verify --deep --strict` fail even though the same app passes strict signing in the local PreviewBuild directory and launches successfully.

For preview signing validation, use the local PreviewBuild artifact. Use the Desktop copy for convenience launch testing only.

## Decision

`dev/integration` is ready for the next local Integration Preview build from the validated PreviewBuild artifact. No remote push was performed.
