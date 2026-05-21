# Bioinformatics B9.14 ReleaseBuild Formal DEG MVP Scoped Carry-over Execution

Date: 2026-05-21

## Scope

This execution carried over the Formal DEG MVP from MainLine baseline `be8c924336f42e92e89eb1d8d7710bed02d4cd99` onto ReleaseBuild baseline `2984d8e56ab531625bf2526e7eb9a63803376c6a`.

The carry-over was scoped. No fast-forward or broad merge was performed. LabTools, Meta, shared-engine, and unrelated test deletions from the MainLine comparison were not applied.

## Applied Changes

Included:

- Bioinformatics analysis input resolver and recognition / standardization convergence.
- Formal DEG dependency, parameter, runtime validation, result schema, review, and controlled runner modules.
- DEG-ready matrix gates.
- Analysis UI state and action rules.
- Formal plot artifact, result registry, report-ready gate, export package, and e2e audit modules.
- Bioinformatics workflow page wiring and the associated tests.
- Runtime dependency declarations for `scipy` and `statsmodels`.
- `app.main` formal DEG runtime-check CLI arguments.

Protected:

- `scripts/package_app.py` was not overwritten by the MainLine version.
- ReleaseBuild package/signing behavior was preserved, including stable `CFBundleExecutable=BioMedPilot`, `-psn_*` handling, arm64 launcher selection, Integration Preview options, and ad-hoc signing.
- Existing ReleaseBuild AI gateway role-routing tests were preserved; `app/bioinformatics/download/geo_text_summary_service.py` was kept on the ReleaseBuild-compatible implementation.

## Validation

Source and test validation:

- `git diff --check`: passed
- `python3 -m pytest tests/bioinformatics -q`: 420 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`: 263 passed
- `python3 scripts/run_tests.py`: 1794 passed
- `python3 -m app.main --smoke-test`: passed

Default GUI package validation:

- `python3 scripts/package_app.py --smoke-test`: passed
- `open -W -n dist/BioMedPilot.app --args --smoke-test`: passed
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`: passed
- `dist/BioMedPilot.app/Contents/MacOS/BioMedPilot -psn_0_12345 --smoke-test`: passed
- `CFBundleExecutable`: `BioMedPilot`
- `CFBundleDisplayName`: `BioMedPilot`

Formal DEG runtime validation:

- Default GUI package runtime check created `/tmp/biomedpilot_releasebuild_formal_deg_runtime_packaged.json` and returned `blocked_missing_dependency` because the default GUI Python lacks `scipy` and `statsmodels`.
- Controlled arm64 DEG runtime at `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/.venv-b9-3b/bin/python` has `numpy 2.4.6`, `pandas 3.0.3`, `scipy 1.17.1`, and `statsmodels 0.14.6`; source formal DEG runtime check passed.
- Separate controlled validation package was built at `dist/deg-runtime-validation/BioMedPilot.app`; package smoke, `open -W`, codesign, and packaged formal DEG runtime check passed.
- Controlled packaged runtime JSON: `/tmp/biomedpilot_releasebuild_formal_deg_runtime_controlled_packaged.json`

## Boundary

The default GUI package remains a valid smoke/open/codesign package, but formal DEG execution is dependency-blocked there until the GUI runtime also provides `scipy` and `statsmodels`. The controlled DEG validation package proves the carried-over Formal DEG MVP code path and fixture runner pass with the required scientific Python runtime, but that runtime does not include PySide6 and is not the full GUI package runtime.
