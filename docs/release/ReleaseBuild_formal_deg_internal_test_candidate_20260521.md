# ReleaseBuild Formal DEG Internal Test Candidate

Date: 2026-05-21

## Candidate

Candidate commit: `ad394bd923de02247cc41ca93b9f9665a1dd31ab`

Branch: `codex/releasebuild-formal-deg-carryover`

Status: accepted as the current ReleaseBuild Bioinformatics analysis internal-test candidate, pending human decision on whether to merge into `dev/release-internal-test`.

This candidate includes:

- B9.14 Formal DEG MVP scoped carry-over from MainLine.
- B10/B11 ORA and GSEA enrichment layer gates already present in ReleaseBuild.
- B12/B13/B14/B14.8/B14.9 survival/clinical input, controlled KM/log-rank, and controlled Cox univariate closure gates.
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

B14.9 closure additionally requires:

- ReleaseBuild UI distinguishes DEG / ORA / GSEA / KM / Cox / Cox multivariate disabled / survival report-ready disabled.
- KM and Cox result semantics remain `formal_computed_result` only when controlled gates pass.
- KM and Cox plot artifacts remain spec-only and source-result driven.
- KM and Cox result/report state keeps `report_ready_eligible=False`.
- Cox multivariate remains design audit only.
- Survival/clinical report-ready remains disabled.

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

## Analysis Support Scope

Supported in this candidate:

- Two-group controlled DEG only
- Python scipy/statsmodels execution path
- Controlled dependency detection
- Parameter confirmation gate
- Formal DEG result schema
- Result review and report-ready gating
- Basic formal DEG plot/report artifacts under the controlled MVP boundary
- Controlled ORA section-only enrichment layer
- Controlled preranked GSEA section-only enrichment layer
- Controlled two-group KM/log-rank MVP
- Controlled single-variable Cox MVP

Not supported:

- Cox multivariate execution
- Survival/clinical report-ready package
- Real rendered KM/Cox PNG/SVG/PDF plots
- R backend execution
- DESeq2
- edgeR
- limma
- Clinical conclusion, prognosis, diagnosis, treatment recommendation, publication claim, regulatory claim, or production clinical-readiness claim

## Release Notes

This is an internal-test candidate, not a public release.

The Bioinformatics analysis surface is limited to controlled MVP paths: two-group DEG, ORA, preranked GSEA, two-group KM/log-rank, and single-variable Cox. It validates dependency availability, parameters, result schema, fixture execution, result review, and section/package gates. It does not call R/Bioconductor engines and must not be described as clinical, regulatory, production, or publication-ready.

The default GUI package is a valid UI smoke package and remains the package used for desktop manual inspection. Formal DEG computation is only proven in the controlled DEG runtime package until the default GUI Python runtime includes `scipy` and `statsmodels`.

Survival/clinical notes:

- KM/log-rank and Cox univariate are controlled MVP analysis outputs only.
- Cox multivariate remains disabled/design audit only.
- KM/Cox plot artifacts are spec-only.
- Survival/clinical report-ready is disabled.
- No clinical conclusion, prognosis, or treatment recommendation is generated.

B14.9 closure evidence is recorded in:

- `docs/bioinformatics/stage_B14_9_releasebuild_survival_clinical_closure_gate_20260521.md`

## Branch Decision

Recommendation: keep `codex/releasebuild-formal-deg-carryover` as the candidate branch until the release gate passes from this fixed script and the user explicitly approves promotion.

Do not merge into `dev/release-internal-test` automatically. Merge locally into `dev/release-internal-test` only after approval, then rerun the same release gate from the target branch because package metadata must record the promoted commit.
