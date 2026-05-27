# Bioinformatics B50 ReleaseBuild Internal-Test Gate Refresh

Date: 2026-05-27

## Scope

B50 refreshes the ReleaseBuild internal-test gate after B49. The key change is that the default GUI package now runs on a Python runtime where `numpy`, `pandas`, `scipy`, and `statsmodels` are available, so formal DEG runtime validation is expected to pass in the default packaged app instead of being gracefully blocked.

This stage covers:

- Refreshing `scripts/releasebuild_formal_deg_gate.py`.
- Auditing the stale `docs/release/ReleaseBuild_handoff_report_20260513.md` file.
- Running the full internal-test gate.
- Recording the current ReleaseBuild handoff recommendation.

This stage does not promote the branch, publish a release, notarize the app, change desktop entry ownership, add new analysis algorithms, or change clinical boundaries.

## Baseline

| Item | Value |
| --- | --- |
| Branch | `codex/releasebuild-formal-deg-carryover` |
| Baseline before B50 | `e39970e4526a6b30b4001504a31a618f4ad4f1e3` |
| Previous stage | B49 risk score / survival clinical integrated report release-readiness audit |
| Stale excluded file | `docs/release/ReleaseBuild_handoff_report_20260513.md` |

## Gate Refresh

`scripts/releasebuild_formal_deg_gate.py` is updated from schema v1 to v2.

Changed expectation:

- Before B50: default GUI package formal DEG runtime check expected `blocked_missing_dependency`.
- After B50: default GUI package formal DEG runtime check must return `passed`.

The refreshed gate still requires:

1. `scripts/run_tests.py`
2. Source smoke.
3. Default GUI package smoke.
4. `open -W` default GUI package smoke.
5. Default GUI package codesign verification.
6. `-psn_*` packaged executable smoke.
7. Default GUI package formal DEG runtime check, now expected `passed`.
8. Controlled runtime package smoke.
9. Controlled runtime `open -W` smoke.
10. Controlled runtime codesign verification.
11. Controlled packaged formal DEG runtime check, expected `passed`.

The default GUI runtime check records dependency versions:

- `numpy 2.4.4`
- `pandas 3.0.2`
- `scipy 1.17.1`
- `statsmodels 0.14.6`

## Stale Handoff Audit

`docs/release/ReleaseBuild_handoff_report_20260513.md` remains untracked and stale.

Reasons it is not included:

- It references `dev/release-internal-test`, not the current candidate branch.
- It references old HEAD `d6f8d25`.
- It describes pre-Bioinformatics analysis MVP state.
- It claims default GUI formal DEG dependency gaps that are no longer true in the current environment.

B50 therefore keeps the stale file excluded and records the current handoff state in the B50 docs instead.

## Current Capability Scope

Current candidate supports controlled statistical research workflows:

- two-group formal DEG with Python scipy/statsmodels runtime
- ORA section workflow
- preranked GSEA section workflow
- KM/log-rank controlled survival analysis
- Cox univariate and scoped Cox multivariate analysis paths
- risk score validation section package, optional in full integrated report only after explicit selection
- full integrated markdown package
- DOCX/PDF rendered exports as package artifacts under renderer gates

Current candidate still does not support:

- clinical diagnosis
- prognosis conclusion
- treatment recommendation
- risk group or cutoff recommendation
- validated clinical risk score interpretation
- automatic risk score inclusion in full integrated report
- legacy formal execution bypass
- public release / notarized distribution

## Validation

Commands run:

| Command | Result |
| --- | --- |
| `python3 -m py_compile scripts/releasebuild_formal_deg_gate.py` | Passed |
| `python3 scripts/releasebuild_formal_deg_gate.py --skip-full-tests --json-output /tmp/biomedpilot_releasebuild_b50_gate_skip_full.json` | Passed |
| `python3 scripts/releasebuild_formal_deg_gate.py --json-output /tmp/biomedpilot_releasebuild_b50_gate.json` | Passed |

Full B50 gate result:

- `schema_version=biomedpilot.releasebuild.formal_deg_gate.v2`
- `status=passed`
- `scripts/run_tests.py`: passed, `2397 passed, 1 warning`
- source smoke: passed, `git_head=e39970e`
- default package smoke: passed, `git_head=e39970e`
- default package `open -W`: passed
- default package codesign: passed
- packaged `-psn_*` smoke: passed
- default GUI formal DEG runtime check: `passed`
- default GUI dependency status: `passed`
- default GUI fixture status: `passed`
- controlled package smoke: passed
- controlled package `open -W`: passed
- controlled package codesign: passed
- controlled formal DEG runtime check: `passed`

Known warning:

- `tests/bioinformatics/test_geo_differential_expression_runner.py::test_geo_deg_runner_uses_explicit_gsm_group_assignments` emits a scipy precision-loss warning for nearly identical fixture values. This is not a B50 regression.

## Issues

### Blocker

- None.

### Major

- None.

### Minor

- The default packaged app uses the local system Python path and external site-packages; it is an internal-test candidate, not a standalone public distribution.
- The controlled runtime package still lacks PySide6 and is runtime-validation only.
- The stale 2026-05-13 handoff file remains untracked and must not be committed unless regenerated.

## Conclusion

B50 passes.

The internal-test gate is refreshed to match the current ReleaseBuild candidate: the default GUI package must now pass formal DEG runtime validation. The branch remains suitable as the current internal-test candidate snapshot, with Bioinformatics analysis capabilities bounded to statistical research workflows and without clinical-use claims.

## Recommendation

Recommended next step:

- Keep `codex/releasebuild-formal-deg-carryover` as the candidate branch.
- If the user wants promotion, perform a separate scoped promotion to `dev/release-internal-test` and rerun the same B50 gate from the target branch.
