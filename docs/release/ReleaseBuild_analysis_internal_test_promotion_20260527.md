# ReleaseBuild Analysis Internal-Test Promotion Closure - 2026-05-27

## Scope

This closure records the scoped promotion of the Bioinformatics analysis ReleaseBuild candidate from `codex/releasebuild-formal-deg-carryover` to `dev/release-internal-test`.

This stage performs a branch promotion and validation only. It does not publish a public release, notarize the app, push to a remote, replace a desktop entry, or expand analysis capabilities.

## Promotion

| Item | Value |
| --- | --- |
| Source branch | `codex/releasebuild-formal-deg-carryover` |
| Target branch | `dev/release-internal-test` |
| Source commit | `a8adc29a1bc209461a70f296187eaece1565f141` |
| Promotion method | `git merge --ff-only codex/releasebuild-formal-deg-carryover` |
| Target HEAD after promotion | `a8adc29a1bc209461a70f296187eaece1565f141` |

Pre-promotion relation:

- `git rev-list --left-right --count dev/release-internal-test...codex/releasebuild-formal-deg-carryover`: `0 350`
- The target branch was an ancestor of the candidate branch.
- The promotion was a clean fast-forward and did not create a merge commit.

## Gate Result On Target Branch

Command:

```bash
python3 scripts/releasebuild_formal_deg_gate.py --json-output /tmp/biomedpilot_releasebuild_b51_promoted_gate.json
```

Result:

- Gate schema: `biomedpilot.releasebuild.formal_deg_gate.v2`
- Gate status: `passed`
- `scripts/run_tests.py`: passed
- Full test count: `2397 passed, 1 warning`
- Source smoke: passed, `git_head=a8adc29`
- Default GUI package smoke: passed, `git_head=a8adc29`
- Default GUI package `open -W`: passed
- Default GUI package codesign: passed
- Packaged executable `-psn_*` smoke: passed
- Default GUI formal DEG runtime check: `passed`
- Default GUI dependency status: `passed`
- Default GUI formal DEG fixture status: `passed`
- Controlled runtime package smoke: passed
- Controlled runtime package `open -W`: passed
- Controlled runtime package codesign: passed
- Controlled formal DEG runtime check: `passed`

Default GUI formal DEG dependency versions:

- `numpy 2.4.4`
- `pandas 3.0.2`
- `scipy 1.17.1`
- `statsmodels 0.14.6`

Known warning:

- `tests/bioinformatics/test_geo_differential_expression_runner.py::test_geo_deg_runner_uses_explicit_gsm_group_assignments` emitted a scipy precision-loss warning for nearly identical fixture values. This is not a promotion regression.

## Analysis Scope Preserved

Promoted internal-test scope:

- controlled two-group formal DEG
- ORA section workflow
- preranked GSEA section workflow
- KM/log-rank controlled survival workflow
- Cox univariate and scoped Cox multivariate workflows
- risk score validation section package with optional full integrated inclusion
- full integrated markdown package
- DOCX/PDF rendered exports as package artifacts behind renderer gates

Still excluded:

- clinical diagnosis
- prognosis conclusion
- treatment recommendation
- risk group or cutoff recommendation
- validated clinical risk score interpretation
- automatic risk score inclusion in full integrated report
- legacy formal execution bypass
- public release / notarized distribution

## Stale File Boundary

The stale untracked file remains excluded:

- `docs/release/ReleaseBuild_handoff_report_20260513.md`

It was not committed because it describes an old branch, old HEAD, old package state, and old dependency state.

## Conclusion

Promotion to `dev/release-internal-test` is complete and validated.

The target branch is now the current Bioinformatics analysis internal-test candidate at `a8adc29a1bc209461a70f296187eaece1565f141`.

## Next Step

If the user wants a desktop artifact handoff, perform a separate step to decide whether to refresh the desktop app entry or produce an external distribution artifact. That step must not change the statistical-research-only and non-clinical boundaries.
