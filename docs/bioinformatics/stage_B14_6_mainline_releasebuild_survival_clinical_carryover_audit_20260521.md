# Bioinformatics B14.6 MainLine / ReleaseBuild Survival Clinical Carry-over Audit

Date: 2026-05-21

## 1. Audit Scope

This audit checks whether the Bioinformatics survival and clinical controlled MVP line can be carried over into MainLine and ReleaseBuild without regressing the already submitted DEG, ORA, GSEA, recognition, standardization, plot, report, and packaging contracts.

This is a carry-over readiness audit only. It does not merge, publish, release, replace desktop entry points, or expand formal analysis scope.

In scope:

- B12 survival / clinical input and contract hardening readiness.
- B13 controlled KM / log-rank MVP readiness.
- B14 controlled Cox univariate MVP readiness.
- B14.5 closure audit findings and boundary preservation.
- MainLine and ReleaseBuild file coverage, branch state, and test preflight.
- Carry-over strategy, blockers, risks, and rollback plan.

Out of scope:

- New survival statistics beyond the controlled B13/B14 scope.
- Cox multivariate execution.
- Clinical conclusion, prognosis, treatment advice, or treatment recommendation.
- Real KM/Cox plot rendering. Current B13/B14 plot artifacts are spec/manifest driven.
- Report-ready activation for survival/clinical.
- GSEA/ORA/DEG behavior changes.
- ReleaseBuild publication.

## 2. Baselines

| Worktree | Branch | HEAD | State |
| --- | --- | --- | --- |
| Bioinformatics source | `dev/bioinformatics` | `62600c0d1fbea84da2d1da61c9de3645bd66504c` | Source of B13/B14/B14.5 survival clinical changes. Worktree has unrelated untracked `docs/bioinformatics/Bioinformatics_handoff_report_20260513.md` and `project_storage/bioinformatics/`, excluded from this audit. |
| MainLine target | `stable/mainline` | `be8c924336f42e92e89eb1d8d7710bed02d4cd99` | Clean worktree. Existing formal DEG MainLine baseline. |
| ReleaseBuild target | `codex/releasebuild-formal-deg-carryover` | `d074172e513e3e599e16ba342f33d90309e9041b` | Has unrelated untracked `docs/release/ReleaseBuild_handoff_report_20260513.md`, excluded from this audit. |

Commit distance:

| Comparison | Ahead/behind from target to Bioinformatics source |
| --- | --- |
| MainLine `HEAD...62600c0` | `92 3` |
| ReleaseBuild `HEAD...62600c0` | `350 20` |

Conclusion: neither target is a fast-forward candidate.

## 3. Current Capability Boundary

The Bioinformatics source line currently contains:

- Controlled KM / log-rank execution MVP gated by survival input, parameter, dependency, and result schema contracts.
- Controlled Cox univariate execution MVP gated by clinical covariate, outcome, parameter, dependency, and result schema contracts.
- Cox multivariate design audit only, with execution disabled.
- KM/Cox plot artifact specification gates only, not real PNG/SVG/PDF renderers.
- `report_ready_eligible=False` for survival/clinical outputs.
- UI rows that distinguish KM/log-rank, Cox univariate, Cox multivariate disabled state, and clinical boundary copy.
- E2E audit coverage for missing dependency, invalid covariate, low event count, and preflight-source blocked cases.

The source line deliberately does not contain:

- Clinical conclusion, prognosis, treatment advice, or survival interpretation as a medical conclusion.
- Cox multivariate execution.
- Formal survival report-ready package.
- Survival/GSEA/ORA/DEG cross-upgrade of imported/testing/exploratory/preflight outputs.

## 4. MainLine Coverage Check

MainLine `be8c924` is clean but does not yet include the B13/B14 controlled survival clinical runtime surface from Bioinformatics source.

Files that would need scoped carry-over or equivalent implementation:

| Area | MainLine status | Carry-over need |
| --- | --- | --- |
| `app/bioinformatics/survival_clinical/` B13/B14 modules | Missing | Add controlled KM/Cox modules and schemas. |
| `app/bioinformatics/plots/survival.py` and `plots/cox.py` | Missing | Add spec-only plot artifact gates. |
| `app/bioinformatics/plots/models.py` and `plots/__init__.py` | Diverged | Merge without disrupting existing DEG/ORA/GSEA plot contracts. |
| `app/bioinformatics/analysis_ui/*` | Present but older | Merge survival/clinical rows and disabled reasons. |
| `app/bioinformatics/workflow_pages.py` | Present but older | Merge UI status rows and labels only. |
| `config/bioinformatics/package_requirements.yaml` | Present but older | Merge detect-first survival dependency metadata only. No auto-install. |
| `tests/bioinformatics/test_km_*` | Missing | Add B13 tests. |
| `tests/bioinformatics/test_cox_*` | Missing | Add B14 tests. |
| `tests/bioinformatics/test_survival_e2e_acceptance_audit.py` | Missing | Add closure failure-mode audit. |
| B13/B14/B14.5 docs | Missing | Add audit and implementation documents. |

MainLine diff also shows unrelated historical file differences outside the survival/clinical scope. Those should not be bulk-applied as part of survival carry-over.

MainLine recommendation:

- Do not fast-forward.
- Do not wholesale merge from Bioinformatics source.
- Use scoped carry-over after first confirming the survival input contract shape that MainLine should accept.
- Preserve MainLine formal DEG, ORA/GSEA, result index, report, and packaging behavior.

## 5. ReleaseBuild Coverage Check

ReleaseBuild `d074172` is not a simple receiver for Bioinformatics source. It already contains a B12 survival/clinical input hardening package that is not present in the current Bioinformatics source line.

ReleaseBuild B12 files that must be preserved:

- `app/bioinformatics/survival_clinical/input_resolver.py`
- `app/bioinformatics/survival_clinical/outcome_gate.py`
- `app/bioinformatics/survival_clinical/clinical_variables.py`
- `app/bioinformatics/survival_clinical/missingness.py`
- `app/bioinformatics/survival_clinical/censoring.py`
- `app/bioinformatics/survival_clinical/source_mapping.py`
- `app/bioinformatics/survival_clinical/models.py`
- Existing B12 tests such as `test_survival_clinical_input_resolver.py`, `test_survival_outcome_gate.py`, `test_clinical_variable_typing.py`, and `test_clinical_missingness_audit.py`.

Direct diff from ReleaseBuild to Bioinformatics source shows that a direct checkout or replacement would delete those B12 files while adding B13/B14 files. That is unsafe.

ReleaseBuild needs:

| Area | ReleaseBuild status | Required action |
| --- | --- | --- |
| B12 survival input hardening | Present | Preserve and converge with B13/B14 gate inputs. |
| B13 KM/log-rank controlled runtime | Missing | Add only after adapter compatibility with B12 outputs is verified. |
| B14 Cox univariate controlled runtime | Missing | Add only after clinical variable and outcome gate compatibility is verified. |
| Cox multivariate | Design only | Keep disabled. |
| KM/Cox plot artifacts | Missing | Add spec-only gate if B13/B14 runtime is carried over. |
| Report-ready | Disabled | Keep disabled. |
| GSEA/ORA/DEG | Existing ReleaseBuild state | Do not change in this survival/clinical carry-over. |

ReleaseBuild recommendation:

- Do not direct merge or direct checkout Bioinformatics source paths.
- Do not replace `app/bioinformatics/survival_clinical/`.
- Carry over B13/B14 as a scoped additive patch that preserves ReleaseBuild B12 modules.
- Prefer carrying over from an audited MainLine convergence commit instead of directly from Bioinformatics source.

## 6. Formal Result Semantics Check

Survival/clinical carry-over must preserve these semantics:

| Result type | Allowed state |
| --- | --- |
| KM/log-rank controlled output | Formal only when B12/B13 gates pass and source is not preflight/testing/imported/exploratory. |
| Cox univariate output | Formal only when B12/B14 gates pass and source is not preflight/testing/imported/exploratory. |
| Cox multivariate | Design audit only, no formal execution. |
| HR / CI / p-value | Only in Cox univariate result bundles. |
| KM/log-rank p-value | Only in B13 KM/log-rank result bundles. |
| Plot artifacts | Spec-only, semantics inherited from source result, no real plot rendering in this line. |
| Report-ready | Always false for survival/clinical in this line. |
| Clinical conclusion | Not allowed. |

## 7. UI Boundary Check

Carry-over must keep the Analysis UI explicit about:

- Survival/KM/log-rank state and disabled reasons.
- Cox univariate state and disabled reasons.
- Cox multivariate disabled state.
- Dependency status as detect-first, with no install action.
- Preflight/testing/imported/exploratory sources blocked from formal survival/clinical execution.
- Plot artifacts as spec-only until a later audited plot activation stage.
- Report-ready blocked until a later audited report gate stage.

The UI must not imply that:

- Cox multivariate has been executed.
- KM/Cox plots are real rendered images.
- Survival/clinical outputs are clinical conclusions.
- Report-ready has been activated.

## 8. Package / Runtime / Codesign Risk

This audit did not package ReleaseBuild because it made no code changes in the target worktrees. Packaging should be re-run during carry-over execution.

Known carry-over risks:

- ReleaseBuild has a separate B12 survival input hardening surface. Direct replacement would delete it.
- MainLine lacks the current B13/B14 runtime surface and may need input-contract convergence before execution tests can pass.
- Survival runtime depends on detect-first dependency behavior. No auto-install should be introduced.
- Existing DEG/ORA/GSEA package and report behavior must not be touched.
- Native dependency packaging checks should be repeated if survival/clinical runtime dependency metadata changes.

Required package validation during execution:

- `python3 scripts/package_app.py --smoke-test`
- `open -W -n dist/BioMedPilot.app --args --smoke-test`
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`

## 9. Test Commands and Results

Bioinformatics source:

| Command | Result |
| --- | --- |
| `git diff --check` | Passed |
| `python3 -m pytest tests/bioinformatics -q -k "survival or clinical or cox or km or logrank or analysis_ui"` | Passed: 69 passed, 337 deselected |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or survival or clinical or results_browser"` | Passed: 12 passed, 97 deselected |
| `python3 -m app.main --smoke-test` | Passed, `git_head=62600c0` |

MainLine target:

| Command | Result |
| --- | --- |
| `git diff --check` | Passed |
| `python3 -m pytest tests/bioinformatics -q -k "survival or clinical or cox or km or logrank or analysis_ui"` | Passed: 43 passed, 371 deselected |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or survival or clinical or results_browser"` | Passed: 12 passed, 97 deselected |
| `python3 -m app.main --smoke-test` | Passed, `git_head=be8c924` |

ReleaseBuild target:

| Command | Result |
| --- | --- |
| `git diff --check` | Passed |
| `python3 -m pytest tests/bioinformatics -q -k "survival or clinical or cox or km or logrank or analysis_ui"` | Passed: 58 passed, 478 deselected |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or survival or clinical or results_browser"` | Passed: 14 passed, 97 deselected |
| `python3 -m app.main --smoke-test` | Passed, `git_head=d074172` |

## 10. Blockers / Major / Minor

### Blocker

1. ReleaseBuild cannot directly accept Bioinformatics `62600c0` survival/clinical paths because the direct diff deletes ReleaseBuild's B12 input hardening modules. Carry-over must be scoped and convergent.

### Major

1. MainLine lacks B13/B14 controlled survival clinical runtime files and tests. A scoped carry-over is needed before MainLine can validate KM/log-rank and Cox univariate MVP behavior.
2. MainLine and ReleaseBuild have different survival/clinical contract shapes. B12 input/output contracts must be converged before B13/B14 execution is enabled on either target.
3. ReleaseBuild should consume an audited MainLine convergence commit or a carefully scoped patch, not the current Bioinformatics source tree wholesale.

### Minor

1. B14.5 wording should continue to avoid treating p-values, HR, CI, or survival curves as clinical conclusions.
2. Package/open-W/codesign were not re-run in this audit because no target code changed. They are mandatory for carry-over execution.
3. Existing untracked handoff/project storage files in Bioinformatics and ReleaseBuild remain excluded from commits.

## 11. Carry-over Plan

Recommended sequence:

1. Create a MainLine carry-over branch from `stable/mainline`.
2. First converge B12 survival/clinical input contracts. Reconcile ReleaseBuild's `survival_clinical` input resolver/outcome/clinical variable modules with Bioinformatics B13/B14 gate expectations.
3. Add B13 KM/log-rank controlled MVP modules and tests as scoped files only.
4. Add B14 Cox univariate controlled MVP modules and tests as scoped files only.
5. Add UI disabled rows and labels without changing DEG/ORA/GSEA/report behavior.
6. Run MainLine survival/clinical test gates, full bioinformatics tests if feasible, UI tests, smoke, package smoke, open-W smoke, and codesign.
7. After MainLine passes, carry the audited MainLine convergence into ReleaseBuild.
8. In ReleaseBuild, preserve B12 input hardening modules and add B13/B14 adapters/additive modules only.
9. Re-run ReleaseBuild package/open-W/codesign gates.

Recommended carry-over mode:

| Target | Recommendation |
| --- | --- |
| MainLine | Scoped carry-over after B12 input contract convergence. |
| ReleaseBuild | Wait for audited MainLine convergence, or do a scoped additive carry-over preserving ReleaseBuild B12 files. |

Not recommended:

- Fast-forward.
- Bulk merge.
- Direct path checkout from Bioinformatics source into ReleaseBuild.
- Any carry-over that deletes ReleaseBuild B12 modules.

## 12. Rollback Plan

No target worktree code was changed during this audit.

If carry-over execution is attempted later:

1. Work on a dedicated branch.
2. Commit B12 convergence separately from B13/B14 runtime additions.
3. Commit UI changes separately from runtime changes where practical.
4. If a stage fails, revert the scoped carry-over commits rather than resetting or deleting user work.
5. Keep unrelated untracked handoff/project storage files out of commits.
6. Do not use destructive reset/checkout commands against dirty worktrees.

## 13. Final Recommendation

Current conclusion: conditional carry-over readiness.

MainLine can enter scoped carry-over only after B12 survival/clinical input contract convergence is planned and applied. ReleaseBuild should not receive the Bioinformatics source tree directly. It should receive either the audited MainLine convergence or a scoped additive patch that preserves its existing B12 input hardening modules.

Next recommended stage:

`B14.7 MainLine Survival Clinical Contract Convergence and Scoped Carry-over`

ReleaseBuild carry-over should wait until MainLine convergence has passed tests and package/open-W/codesign validation.
