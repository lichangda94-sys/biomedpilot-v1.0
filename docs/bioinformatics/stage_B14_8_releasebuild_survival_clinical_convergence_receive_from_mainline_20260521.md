# Bioinformatics B14.8 ReleaseBuild Survival Clinical Convergence Receive-from-MainLine

Date: 2026-05-21

## Scope

This stage receives the MainLine survival/clinical convergence result from:

`6779f3e22a6e197bf0417a2aa35c372c47774786`

The receive was scoped. ReleaseBuild did not directly consume the Bioinformatics source tree, and it did not replace the ReleaseBuild B12 `survival_clinical` input hardening modules.

## Baselines

| Worktree | Branch | Baseline |
| --- | --- | --- |
| ReleaseBuild | `codex/releasebuild-formal-deg-carryover` | `d074172e513e3e599e16ba342f33d90309e9041b` |
| MainLine source | `codex/mainline-survival-clinical-carryover` | `6779f3e22a6e197bf0417a2aa35c372c47774786` |

Unrelated untracked file preserved and excluded:

- `docs/release/ReleaseBuild_handoff_report_20260513.md`

## Receive Strategy

Applied:

- Add B13 KM/log-rank controlled runtime modules.
- Add B14 Cox univariate controlled runtime modules.
- Add KM/Cox spec-only plot artifact modules.
- Add B13/B14/B14.5/B14.7 docs from MainLine.
- Add B13/B14 tests from MainLine.
- Merge ReleaseBuild Analysis UI gates without removing ORA/GSEA UI actions.
- Merge ReleaseBuild plot model/export updates without removing ORA/GSEA plot modules.
- Update dependency detection to detect-first `lifelines` status with no install action.

Preserved:

- ReleaseBuild B12 files:
  - `input_resolver.py`
  - `outcome_gate.py`
  - `clinical_variables.py`
  - `missingness.py`
  - `censoring.py`
  - `source_mapping.py`
  - `models.py`
- ReleaseBuild B10 ORA implementation and tests.
- ReleaseBuild B11 GSEA implementation and tests.
- ReleaseBuild formal DEG package/runtime behavior.
- ReleaseBuild recognition, standardization, resolver, result, plot, report, package, and desktop entry behavior.

Not applied:

- No direct checkout of the Bioinformatics source tree.
- No whole-directory replacement of `app/bioinformatics/survival_clinical`.
- No deletion of ORA/GSEA files.
- No ReleaseBuild publication.

## Capability Boundary

Now present in ReleaseBuild:

- B12 survival/clinical input resolver and outcome/clinical variable gates.
- B13 controlled two-group KM/log-rank MVP.
- B14 controlled single-variable Cox MVP.
- Cox multivariate design audit only.
- KM/Cox plot artifact spec gates only.

Still not implemented:

- Cox multivariate execution.
- Risk score / nomogram.
- Clinical conclusion, prognosis, or treatment recommendation.
- Real KM/Cox PNG/SVG/PDF plot rendering.
- Survival/clinical report-ready package.
- Full integrated report.

## UI Changes

ReleaseBuild Analysis Center now shows:

- Survival/clinical input resolver.
- Case/sample mapping.
- OS_time / OS_event / censoring gate.
- Clinical variable typing / missingness.
- Two-group KM/log-rank gate.
- KM plot artifact/spec.
- Single-variable Cox gate.
- Cox forest plot artifact/spec.
- Multivariate Cox design audit.
- Risk score / nomogram disabled.

ORA and GSEA action rows remain present and gate-controlled.

## Tests

| Command | Result |
| --- | --- |
| `git diff --check` | Passed |
| Targeted B12/B13/B14 tests | Passed: 39 passed |
| `python3 -m pytest tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py -q` | Passed: 16 passed |
| `python3 -m pytest tests/bioinformatics -q -k "survival or clinical or cox or km or logrank or analysis_ui"` | Passed: 87 passed, 478 deselected |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q -k "bioinformatics"` | Passed: 131 passed, 137 deselected |
| `python3 -m pytest tests/bioinformatics -q` | Passed: 565 passed |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | Passed: 268 passed |

Package/open/codesign validation is recorded after the final commit so the packaged smoke output can report the final ReleaseBuild commit hash.

## Blockers / Major / Minor

### Blockers

None.

### Major

None after scoped receive.

### Minor

1. `lifelines` remains detect-first. Missing `lifelines` blocks controlled KM/Cox gracefully rather than installing automatically.
2. KM/Cox plot artifacts remain spec-only.
3. Survival/clinical report-ready remains disabled.

## Rollback Plan

If ReleaseBuild carry-over needs rollback:

1. Revert the B14.8 receive commit.
2. Do not reset the worktree or delete unrelated untracked files.
3. Re-run ReleaseBuild bioinformatics/UI/smoke/package/open-W/codesign gates after rollback.

## Conclusion

ReleaseBuild can receive the MainLine `6779f3e` survival/clinical convergence result through this scoped patch. The existing B12 input hardening files were preserved, and ORA/GSEA enrichment layer files were not removed or downgraded.
