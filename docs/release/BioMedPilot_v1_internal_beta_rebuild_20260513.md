# BioMedPilot v1.0 Internal Beta Package Rebuild

日期：2026-05-13

工作区：`/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`

分支：`dev/release-internal-test`

## 1. Build Source

- Build source worktree：`/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`
- Source root in package metadata：`/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`
- Git commit：`43c3cd0 fix(release): restore bioinformatics workspace ui compatibility`
- App version：`0.1.0-internal-beta`
- App channel：`Developer Preview / testing`
- Package mode：local Python macOS `.app` launcher
- Package artifact：`/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild/dist/BioMedPilot.app`

This package is an internal beta / Developer Preview testing artifact only. It is not production-ready, not clinical-grade, and not submission-grade.

## 2. Preflight Status

Initial checks:

```bash
pwd
git status --short
git rev-parse --short HEAD
git log -1 --oneline
```

Results:

- `pwd`：`/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`
- `git status --short`：clean
- `git rev-parse --short HEAD`：`43c3cd0`
- `git log -1 --oneline`：`43c3cd0 fix(release): restore bioinformatics workspace ui compatibility`
- ReleaseBuild worktree has no root `CODEX.md`; current task followed the global development manual and ReleaseBuild-local handoff / packaging docs.

## 3. Packaging Command

Existing ReleaseBuild packaging references:

- `README.md` documents `python3 scripts/package_app.py --smoke-test`.
- `docs/packaging.md` documents current local `.app` launcher mode and recommends internal beta acceptance with `--no-clean --smoke-test`.
- `scripts/package_app.py` writes `BUILD_INFO.json`, `Info.plist`, and prints `network_downloads=false`.

Command used:

```bash
QT_QPA_PLATFORM=offscreen python3 scripts/package_app.py --no-clean --smoke-test
```

No new packaging flow was invented. No external dependency was installed.

## 4. Validation Matrix

Packaging前验证：

| Command | Result |
| --- | --- |
| `git diff --check` | Passed |
| `python3 -m app.main --smoke-test` | Passed; source launch, `git_head=43c3cd0` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | `134 passed in 9.14s` |
| `python3 -m pytest tests/shared -q` | `225 passed in 25.79s` |
| `python3 -m pytest tests/bioinformatics -q` | `264 passed in 4.29s` |
| `python3 -m pytest tests/meta_analysis -q` | `3 passed in 0.46s` |
| `python3 -m pytest tests/test_package_app.py -q` | `2 passed in 1.84s` |

Package smoke:

| Check | Result |
| --- | --- |
| `QT_QPA_PLATFORM=offscreen python3 scripts/package_app.py --no-clean --smoke-test` | Passed |
| `dist/BioMedPilot.app/Contents/MacOS/BioMedPilot --smoke-test` | Passed |
| Packaged `app_version` | `0.1.0-internal-beta` |
| Packaged `app_channel` | `Developer Preview / testing` |
| Packaged `launch_mode` | `packaged-local-python` |
| Packaged `git_head` | `43c3cd0` |
| Packaged `app_root` | `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild/dist/BioMedPilot.app/Contents/Resources/app` |
| `network_downloads` | `false` |

## 5. Package Metadata

`BUILD_INFO.json`:

- `app_name`: `BioMedPilot`
- `version`: `0.1.0-internal-beta`
- `bundle_version`: `0.1.0`
- `channel`: `Developer Preview / testing`
- `launch_mode`: `packaged-local-python`
- `source_root`: `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`
- `git_head`: `43c3cd0`
- `built_at`: `2026-05-13T07:27:04.934010+00:00`

`Info.plist`:

- `BioMedPilotVersion`: `0.1.0-internal-beta`
- `BioMedPilotChannel`: `Developer Preview / testing`
- `BioMedPilotGitHead`: `43c3cd0`
- `CFBundleExecutable`: `BioMedPilot`
- `CFBundleShortVersionString`: `0.1.0`

## 6. Vocabulary Resource Strategy Status

Package resource check:

- `data/medical_terms/mini_medical_terms_index.json`：present
- `data/medical_terms/zh_term_overrides.json`：present
- `data/medical_terms/source_metadata.json`：present
- `data/medical_terms/license_attribution.md`：present
- `data/medical_terms/reference_checklists/`：present
- `data/medical_terms/medical_terms_index.sqlite`：absent
- `data/medical_terms/raw/`：absent

Vocabulary baseline was not modified. SQLite remains an optional derived resource and is not a runtime hard dependency.

## 7. Boundary Confirmation

- Modified other worktrees：No.
- Whole-branch merge：No.
- Changed `data/medical_terms`：No.
- Changed SQLite vocabulary strategy：No.
- Changed packaging vocabulary resource strategy：No.
- Real network download：No.
- AI / Ollama call：No.
- External dependency added：No.
- Git push：No.
- Desktop `/Users/changdali/Desktop/BioMedPilot v1.0 Dev.command` overwritten：No.
- Desktop `/Users/changdali/Desktop/BioMedPilot.app` overwritten：No.
- Build artifact generated under ReleaseBuild output directory：Yes, `dist/BioMedPilot.app`.

## 8. Compatibility Status

- UI tests are green.
- Bioinformatics workspace compatibility fix is present in packaged source.
- Packaged smoke reports `bioinformatics_features=5`.
- Meta basic tests are green.
- Shared tests are green.
- The package remains a local Python launcher and is not a standalone installer.

## 9. Development Entry Guidance

`/Users/changdali/Desktop/BioMedPilot v1.0 Dev.command` remains the recommended development test entry when testing directly from the active checkout.

`dist/BioMedPilot.app` is the rebuilt internal beta package artifact for packaged smoke and local tester handoff validation. The desktop app entry was not refreshed or overwritten in this stage.

## 10. Known Limitations

- This is Developer Preview / internal beta only.
- No clinical decision support claim is made.
- No production research result claim is made.
- The package is not a fully standalone distributable app; target machines still need a compatible Python runtime with PySide6.
- Bioinformatics preflight / dry-run records are not real DEG execution.
- Meta outputs remain testing-level unless separately confirmed by a later validated workflow.
- No automatic network retrieval, AI execution, screening, analysis, or final reporting was enabled.

## 11. Conclusion

ReleaseBuild HEAD `43c3cd0` was rebuilt into `dist/BioMedPilot.app` using the existing ReleaseBuild packaging flow. Source validation, package smoke, metadata checks, UI compatibility, shared tests, Bioinformatics tests, Meta tests, and package resource checks passed.

The package is suitable for internal beta / Developer Preview testing, not for production, clinical, or submission-grade use.
