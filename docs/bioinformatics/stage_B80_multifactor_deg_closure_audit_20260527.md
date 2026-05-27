# B80 Multi-factor DEG Closure Audit

## Scope

This audit closes B73-B80 multi-factor DEG activation work. The supported scope is controlled multi-factor DEG only:

- result schema and provenance contract
- user parameter confirmation manifest
- real Rscript fixture execution for limma, DESeq2, and edgeR
- Analysis UI gate visibility and disabled reasons
- DEG plot artifact, audit package, and DEG section report integration

## Stage Acceptance

| Stage | Result | Evidence |
|---|---:|---|
| B73 result schema contract | passed | `05d96dd`; formula, contrast, covariates, batch, rank/df, estimability, backend method required |
| B74 confirmation manifest | passed | `0c7ee69`; formula/contrast/method/value type/dependency/output confirmation |
| B75 limma fixture execution | passed | `735892d`; real Rscript limma, result index v2, task log, dependency snapshot |
| B76 DESeq2 fixture execution | passed | `ece216f`; raw-count only, TPM/FPKM/log blocked |
| B77 edgeR fixture execution | passed | `da947c6`; raw-count only, result schema aligned |
| B78 UI execution gate | passed | `4288530`; design/contrast/method/dependency/confirmation/schema disabled reasons visible |
| B79 plot/report/audit integration | passed | `95a3e88`; multi-factor provenance preserved in plot, audit package, and DEG section report |

## Supported Range

- Controlled multi-factor DEG fixtures using `~ batch + group`.
- limma on controlled display/log-like expression fixture.
- DESeq2 on controlled raw-count fixture only.
- edgeR on controlled raw-count fixture only.
- Result semantics: `formal_computed_result` only when dependency, parameter, confirmation, and result schema gates pass.
- Plot/report/audit integration is limited to formal DEG section artifacts and formal DEG audit packages.

## Not Supported

- Automatic model selection.
- Arbitrary user-project multi-factor execution without gate review.
- Clinical interpretation, prognosis, diagnosis, or treatment recommendation.
- Public-release medical report claims.
- GSEA/survival activation through this work.
- Report-ready upgrade for imported/testing/exploratory/preflight results.

## Package / Runtime / Codesign

- Source smoke: passed, git head `95a3e88`.
- Package smoke: passed, `dist/BioMedPilot.app`, git head `95a3e88`.
- `open -W -n dist/BioMedPilot.app --args --smoke-test`: passed.
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`: passed.
- ReleaseBuild formal DEG gate: passed, `/tmp/biomedpilot_multifactor_deg_gate.json`.
- Runtime architecture from gate: `arm64`.

## Test Results

- `git diff --check`: passed.
- `python3 -m pytest tests/bioinformatics -q`: 484 passed, 1 existing scipy precision warning.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`: 177 passed.
- `python3 -m app.main --smoke-test`: passed.
- `python3 scripts/package_app.py --smoke-test`: passed.
- `open -W -n dist/BioMedPilot.app --args --smoke-test`: passed.
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`: passed.
- `python3 scripts/releasebuild_formal_deg_gate.py --skip-full-tests --json-output /tmp/biomedpilot_multifactor_deg_gate.json`: passed.

## Issues

- Blocker: none.
- Major: none.
- Minor: the ReleaseBuild formal DEG gate still validates the existing two-group formal DEG runtime; multi-factor R fixtures are covered by focused and full bioinformatics tests, not by that release gate script.

## Conclusion

Result: passed as a controlled multi-factor DEG production-readiness candidate.

This is not clinical-grade and not public-release medical reporting. The next hardening step should align ReleaseBuild gate scripts with the new multi-factor R fixture checks before claiming ReleaseBuild-level multi-factor DEG coverage.
