# Bioinformatics B14.9 ReleaseBuild Survival / Clinical Closure Gate

Date: 2026-05-21

## Scope

This closure gate validates ReleaseBuild after receiving MainLine survival/clinical convergence through B14.8.

Validated areas:

- DEG / ORA / GSEA / KM / Cox UI separation.
- KM / Cox result semantics and plot artifact boundaries.
- Cox multivariate disabled/design-only boundary.
- Survival/clinical report-ready disabled boundary.
- Default GUI package versus controlled runtime package behavior.
- Package smoke, LaunchServices `open -W`, direct `-psn_*` smoke, and codesign.
- ReleaseBuild internal-test gate and release notes.

Out of scope:

- Public release.
- Promotion to `dev/release-internal-test`.
- Real KM/Cox PNG/SVG/PDF rendering.
- Survival/clinical report-ready package.
- Clinical conclusion, prognosis, or treatment recommendation.

## Baseline

| Item | Value |
| --- | --- |
| ReleaseBuild branch | `codex/releasebuild-formal-deg-carryover` |
| Closure baseline | `ad394bd923de02247cc41ca93b9f9665a1dd31ab` |
| MainLine convergence source | `6779f3e22a6e197bf0417a2aa35c372c47774786` |
| Untracked excluded file | `docs/release/ReleaseBuild_handoff_report_20260513.md` |

## UI Separation Gate

ReleaseBuild Analysis Center now distinguishes:

| Layer | UI action / row evidence | Gate behavior |
| --- | --- | --- |
| DEG | `formal_deg`, `formal_deg_parameter_confirmation`, formal DEG gate rows | Controlled two-group DEG only; blocked unless resolver, DEG-ready, dependency, parameter, confirmation, and result schema gates pass. |
| ORA | `ora_readiness_review`, `run_ora_enrichment`, `ora_plot`, `ora_report_ready` | ORA has its own source/input/resource/parameter/result/plot/report gates. |
| GSEA | `gsea_preranked_readiness_review`, `formal_gsea`, `gsea_plot`, `gsea_report_ready` | GSEA has its own preranked source/rank/gene-set/parameter/result/plot/report gates. |
| KM/log-rank | `km_logrank_parameter_confirmation`, `km_cox_logrank`, `km_plot_artifact` row | Controlled two-group KM/log-rank only; no report-ready. |
| Cox univariate | `cox_univariate_parameter_confirmation`, `cox_univariate`, `cox_forest_plot` row | Controlled single-variable Cox only; HR/CI/p-value only in Cox univariate result. |
| Cox multivariate | `cox_multivariate`, `cox_multivariate_design` row | Disabled/design audit only. |
| Survival report | `survival_report_ready`, `survival_formal` | Disabled. |
| Risk score | `risk_score` | Disabled. |

The UI does not collapse DEG, ORA, GSEA, KM, or Cox into one generic "analysis done" state.

## KM / Cox Result Semantics Gate

KM/log-rank runtime writes:

- `task_type=survival_km_logrank`
- `result_semantics=formal_computed_result` only after all gates pass
- `plot_artifacts=[]` at execution time
- `report_artifacts=[]`
- `report_ready_eligible=False`

Cox univariate runtime writes:

- `task_type=cox_univariate`
- `result_semantics=formal_computed_result` only after all gates pass
- HR / CI / p-value only in Cox univariate result tables
- `plot_artifacts=[]` at execution time
- `report_artifacts=[]`
- `report_ready_eligible=False`

KM/Cox plot artifact gates:

- Require a `formal_computed_result` source.
- Reject `preflight_only` sources.
- Register spec-only plot artifacts into the result index.
- Preserve `report_ready_eligible=False`.
- Do not produce rendered PNG/SVG/PDF plot images.

## Cox Multivariate and Clinical Boundary Gate

Validated boundary:

- Cox multivariate remains `cox_multivariate_design_audit.v1`.
- No multivariate model execution is exposed.
- No adjusted HR model output is produced.
- No variable selection, risk score, nomogram, prognosis, treatment advice, or clinical conclusion is produced.

## Survival / Clinical Report-ready Gate

Survival/clinical report-ready remains disabled:

- `survival_report_ready` action is disabled.
- `survival_formal` remains a disabled report-ready boundary row.
- KM/Cox outputs do not become full integrated report inputs.
- ORA/GSEA/DEG report gates remain section-specific and do not upgrade survival/clinical results.

## Package Difference Gate

Default GUI package:

- Path: `dist/BioMedPilot.app`
- Size: `33M`
- `CFBundleExecutable=BioMedPilot`
- Launcher executable is a shell script wrapper.
- PySide6 is available.
- Package smoke passed with `git_head=ad394bd`.
- Formal DEG runtime check is expected to be `blocked_missing_dependency` because `scipy` and `statsmodels` are not present in the default GUI Python runtime.
- This is the manual GUI inspection package.

Controlled runtime package:

- Path: `dist/deg-runtime-validation/BioMedPilot.app`
- Size: `33M`
- Python: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/.venv-b9-3b/bin/python`
- PySide6 is not available.
- Package smoke passed with `git_head=ad394bd`.
- Formal DEG runtime check passed with numpy/pandas/scipy/statsmodels importable.
- Controlled fixture produced numeric p-value and FDR and registered result index v2.
- This package proves the controlled dependency/runtime stack, not the full GUI runtime.

## Runtime Gate Evidence

Default GUI runtime check:

- Status: `blocked_missing_dependency`
- Missing packages: `scipy`, `statsmodels`
- Behavior: graceful dependency block, no traceback.

Controlled runtime check:

- Status: `passed`
- Dependency status: `passed`
- Fixture status: `passed`
- Fixture result semantics: `formal_computed_result`
- Result index path: `results/summaries/result_index.json`
- `plot_artifacts=[]`
- `report_artifacts=[]`
- `report_ready_eligible=false`

## Test and Package Commands

| Command | Result |
| --- | --- |
| `git diff --check` | Passed |
| `python3 -m pytest tests/bioinformatics -q -k "formal_deg or ora or gsea or survival or clinical or cox or km or logrank or analysis_ui"` | Passed: 208 passed, 357 deselected |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q -k "bioinformatics"` | Passed: 131 passed, 137 deselected |
| `python3 -m pytest tests/bioinformatics -q` | Passed: 565 passed |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | Passed: 268 passed |
| `python3 scripts/releasebuild_formal_deg_gate.py --json-output /tmp/biomedpilot_releasebuild_b14_9_formal_deg_gate.json` | Passed |

The release gate script additionally ran:

- `scripts/run_tests.py`: 2167 passed
- Source smoke
- Default GUI package smoke
- `open -W -n dist/BioMedPilot.app --args --smoke-test`
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`
- `dist/BioMedPilot.app/Contents/MacOS/BioMedPilot -psn_0_12345 --smoke-test`
- Default GUI formal DEG runtime check: `blocked_missing_dependency`
- Controlled runtime package smoke
- Controlled runtime `open -W`
- Controlled runtime codesign
- Controlled runtime formal DEG check: `passed`

## Blockers / Major / Minor

### Blockers

None.

### Major

None.

### Minor

1. Default GUI package does not include `scipy`/`statsmodels`; formal DEG runtime remains gracefully blocked there.
2. Controlled runtime package is not the full GUI package because PySide6 is unavailable in that controlled Python environment.
3. KM/Cox plot artifacts remain spec-only.
4. Survival/clinical report-ready remains disabled.

## Release Notes / Internal-test Gate

ReleaseBuild internal-test notes are updated in:

- `docs/release/ReleaseBuild_formal_deg_internal_test_candidate_20260521.md`

The fixed internal-test gate remains:

```bash
python3 scripts/releasebuild_formal_deg_gate.py --json-output /tmp/biomedpilot_releasebuild_formal_deg_gate.json
```

B14.9 adds survival/clinical closure expectations to that gate record. The gate must pass before any local promotion to `dev/release-internal-test`.

## Conclusion

B14.9 ReleaseBuild Survival / Clinical Closure Gate passes.

ReleaseBuild can be treated as an internal-test candidate for the current scoped analysis surface:

- controlled DEG
- controlled ORA
- controlled preranked GSEA
- controlled two-group KM/log-rank
- controlled single-variable Cox

The candidate remains not public-release ready and not clinical-use ready.
