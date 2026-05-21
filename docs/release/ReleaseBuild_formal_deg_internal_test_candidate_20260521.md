# ReleaseBuild Formal DEG Internal Test Candidate

Date: 2026-05-21

## Candidate

Candidate commit: `f06b8f6abe01d75ed2a0d316c5558e46bad5df9f`

Branch: `codex/releasebuild-formal-deg-carryover`

Status: accepted as the current ReleaseBuild formal DEG internal-test candidate, pending human decision on whether to merge into `dev/release-internal-test`.

This candidate includes:

- B9.14 Formal DEG MVP scoped carry-over from MainLine.
- Local integration-line carry-over from `dev/integration`, with Bioinformatics conflicts resolved in favor of the B9.14 ReleaseBuild formal DEG implementation.
- ReleaseBuild packaging/signing behavior preserved.

## Release Gate

The release gate is fixed in `scripts/releasebuild_formal_deg_gate.py`.

Required gate steps:

1. `scripts/run_tests.py`
2. Source smoke: `python3 -m app.main --smoke-test`
3. Default GUI package smoke: `python3 scripts/package_app.py --smoke-test`
4. LaunchServices smoke: `open -W -n dist/BioMedPilot.app --args --smoke-test`
5. Codesign verification: `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`
6. Finder argument smoke: `dist/BioMedPilot.app/Contents/MacOS/BioMedPilot -psn_0_12345 --smoke-test`
7. Default GUI package formal DEG runtime check, expected `blocked_missing_dependency`
8. Controlled DEG runtime package smoke using `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/.venv-b9-3b/bin/python`
9. Controlled package LaunchServices smoke
10. Controlled package codesign verification
11. Controlled packaged formal DEG runtime check, expected `passed`

Run:

```bash
python3 scripts/releasebuild_formal_deg_gate.py --json-output /tmp/biomedpilot_releasebuild_formal_deg_gate.json
```

## Package Difference

Default GUI package:

- Path: `dist/BioMedPilot.app`
- Python: default ReleaseBuild GUI Python
- PySide6: available
- GUI smoke, LaunchServices smoke, `-psn_*`, and codesign: required to pass
- Formal DEG runtime check: expected to return `blocked_missing_dependency` until the GUI runtime includes `scipy` and `statsmodels`

Controlled DEG runtime package:

- Path: `dist/deg-runtime-validation/BioMedPilot.app`
- Python: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/.venv-b9-3b/bin/python`
- Required formal DEG packages: `numpy`, `pandas`, `scipy`, `statsmodels`
- PySide6: not available, so this is not the full GUI package runtime
- Purpose: validate the formal DEG dependency stack and controlled fixture runner inside a packaged app

## Formal DEG Support Scope

Supported in this candidate:

- Two-group controlled DEG only
- Python scipy/statsmodels execution path
- Controlled dependency detection
- Parameter confirmation gate
- Formal DEG result schema
- Result review and report-ready gating
- Basic formal DEG plot/report artifacts under the controlled MVP boundary

Not supported:

- GSEA execution
- Survival analysis execution
- R backend execution
- DESeq2
- edgeR
- limma
- Clinical conclusion, diagnosis, treatment recommendation, publication claim, regulatory claim, or production clinical-readiness claim

## Release Notes

This is an internal-test candidate, not a public release.

The formal DEG feature is limited to a controlled two-group MVP. It validates dependency availability, parameters, result schema, and fixture execution. It does not provide broad bioinformatics workflow coverage, does not run enrichment or survival analysis, does not call R/Bioconductor engines, and must not be described as clinical, regulatory, or publication-ready.

The default GUI package is a valid UI smoke package and remains the package used for desktop manual inspection. Formal DEG computation is only proven in the controlled DEG runtime package until the default GUI Python runtime includes `scipy` and `statsmodels`.

## Branch Decision

Recommendation: keep `codex/releasebuild-formal-deg-carryover` as the candidate branch until the release gate passes from this fixed script and the user explicitly approves promotion.

Do not merge into `dev/release-internal-test` automatically. Merge locally into `dev/release-internal-test` only after approval, then rerun the same release gate from the target branch because package metadata must record the promoted commit.
