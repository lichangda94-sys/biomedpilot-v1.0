# ReleaseBuild Analysis Internal-Test Handoff - 2026-05-27

## Candidate

| Item | Value |
| --- | --- |
| Branch | `codex/releasebuild-formal-deg-carryover` |
| Handoff baseline | `e39970e4526a6b30b4001504a31a618f4ad4f1e3` |
| Gate script | `scripts/releasebuild_formal_deg_gate.py` |
| Gate schema | `biomedpilot.releasebuild.formal_deg_gate.v2` |
| Gate output | `/tmp/biomedpilot_releasebuild_b50_gate.json` |
| Status | Internal-test candidate accepted, pending explicit promotion decision |

This handoff supersedes the stale untracked `docs/release/ReleaseBuild_handoff_report_20260513.md` for the current Bioinformatics analysis candidate. The stale file is intentionally not committed because it describes an old branch, old HEAD, and old dependency state.

## Included Analysis Surface

Current internal-test scope:

- Controlled two-group formal DEG using the Python scipy/statsmodels backend.
- ORA section workflow.
- Preranked GSEA section workflow.
- KM/log-rank controlled survival workflow.
- Cox univariate and scoped Cox multivariate clinical association workflows.
- Risk score validation package and optional full integrated inclusion after explicit user selection.
- Full integrated markdown package.
- DOCX/PDF rendered exports as package artifacts behind renderer gates.

The package is for statistical research workflows only.

## Not Included

The candidate still does not provide:

- clinical diagnosis
- prognosis conclusion
- treatment recommendation
- risk group recommendation
- cutoff recommendation
- validated clinical risk score interpretation
- automatic risk score inclusion in full integrated report
- legacy bypass execution
- notarized public distribution

## Runtime State

Default GUI package:

- App path: `dist/BioMedPilot.app`
- Python: `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3`
- PySide6: available
- Formal DEG runtime check: `passed`
- Dependency versions: `numpy 2.4.4`, `pandas 3.0.2`, `scipy 1.17.1`, `statsmodels 0.14.6`
- Formal DEG fixture: passed with numeric p-value and FDR

Controlled runtime package:

- App path: `dist/deg-runtime-validation/BioMedPilot.app`
- Python: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/.venv-b9-3b/bin/python`
- PySide6: unavailable
- Formal DEG runtime check: `passed`
- Purpose: dependency/runtime validation package, not manual GUI inspection package

## Required Internal-Test Gate

Run this before any promotion:

```bash
python3 scripts/releasebuild_formal_deg_gate.py --json-output /tmp/biomedpilot_releasebuild_b50_gate.json
```

The gate must pass these checks:

1. `scripts/run_tests.py`
2. Source smoke
3. Default GUI package smoke
4. Default GUI package `open -W`
5. Default GUI package codesign
6. Packaged executable `-psn_*` smoke
7. Default GUI formal DEG runtime check, expected `passed`
8. Controlled runtime package smoke
9. Controlled runtime package `open -W`
10. Controlled runtime package codesign
11. Controlled formal DEG runtime check, expected `passed`

Observed B50 result:

- Gate status: `passed`
- Tests: `2397 passed, 1 warning`
- Default GUI formal DEG runtime: `passed`
- Controlled formal DEG runtime: `passed`
- Source/package/open-W/codesign: passed

## Handoff Boundaries

Do:

- Keep this branch as the current candidate snapshot unless explicitly promoted.
- Use the B50 gate script as the single internal-test acceptance command.
- Preserve detect-first dependency policy.
- Preserve report package provenance and non-clinical limitations.
- Keep stale handoff files out of commits unless regenerated.

Do not:

- Merge automatically into `dev/release-internal-test`.
- Push or publish without explicit instruction.
- Treat the local-python package as a notarized standalone public app.
- Claim clinical, regulatory, prognosis, treatment, or production medical readiness.

## Promotion Plan

If promotion is requested:

1. Confirm target branch, likely `dev/release-internal-test`.
2. Merge or scoped carry over from `codex/releasebuild-formal-deg-carryover`.
3. Rebuild `dist/BioMedPilot.app` from the target branch.
4. Rerun `python3 scripts/releasebuild_formal_deg_gate.py --json-output /tmp/biomedpilot_releasebuild_b50_gate_after_promotion.json`.
5. Only then refresh any desktop entry or release note.

## Rollback Plan

If the B50 gate regresses:

1. Keep the candidate branch unpromoted.
2. Inspect the failed step in the JSON gate output.
3. For runtime dependency failures, verify source and packaged `--bio-formal-deg-runtime-check` outputs.
4. For package launch failures, inspect `BUILD_INFO.json`, `Info.plist`, `CFBundleExecutable`, and `/tmp` launcher logs.
5. For UI/report gate failures, rerun the focused Bioinformatics tests before any revert.
