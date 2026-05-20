# B9.11 Formal DEG MVP MainLine / ReleaseBuild Carry-Over Planning

Date: 2026-05-20

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Branch: `dev/bioinformatics`

Baseline: `0f0e660 docs(bio): add formal DEG MVP release readiness audit`

## 1. Objective

Plan the carry-over of the bounded Formal DEG MVP from the Bioinformatics worktree into MainLine and ReleaseBuild without expanding the analysis surface.

This is a planning and release handoff stage. It does not move code into sibling worktrees, does not enable new analysis methods, and does not change runtime behavior.

Primary goal:

- Define the exact source commits, files, validation gates, package checks, release notes, and rollback criteria required before MainLine / ReleaseBuild intake.
- Preserve the B9.10 scope lock: formal DEG means two-group controlled DEG only.
- Keep the release path auditable across source runtime, controlled scipy/statsmodels runtime, packaged launcher, and LaunchServices `open -W` execution.
- Prevent imported, testing, exploratory, preflight, GSEA, survival, or report draft paths from being labeled as formal DEG.

Non-goals:

- Do not implement GSEA.
- Do not implement survival statistics, KM, Cox, log-rank, hazard ratio, or clinical association.
- Do not add DESeq2, edgeR, limma, R backend execution, or multi-factor design.
- Do not generate new report-ready sections beyond the formal DEG section.
- Do not convert table-only report mode into volcano or heatmap generation.
- Do not auto-install scipy, statsmodels, R, lifelines, or any optional dependency.

## 2. Source Documents

Must read before carry-over execution:

- `docs/bioinformatics/stage_B9_1_formal_deg_dependency_activation_planning_task_20260520.md`
- `docs/bioinformatics/stage_B9_2_formal_deg_dependency_activation_implementation_20260520.md`
- `docs/bioinformatics/stage_B9_3_audited_formal_deg_execution_activation_20260520.md`
- `docs/bioinformatics/stage_B9_3_formal_deg_runtime_dependency_packaging_validation_20260520.md`
- `docs/bioinformatics/stage_B9_3b_formal_deg_controlled_runtime_validation_20260520.md`
- `docs/bioinformatics/stage_B9_4_formal_deg_user_parameter_confirmation_flow_20260520.md`
- `docs/bioinformatics/stage_B9_5_formal_deg_result_review_interpretation_guard_20260520.md`
- `docs/bioinformatics/stage_B9_6_formal_deg_plot_artifact_activation_20260520.md`
- `docs/bioinformatics/stage_B9_7_formal_deg_report_ready_gate_20260520.md`
- `docs/bioinformatics/stage_B9_8_formal_deg_report_ready_package_ux_review_audit_20260520.md`
- `docs/bioinformatics/stage_B9_9_formal_deg_e2e_user_acceptance_audit_20260520.md`
- `docs/bioinformatics/stage_B9_10_formal_deg_mvp_release_readiness_regression_closure_audit_20260520.md`

## 3. Carry-Over Scope

Carry over as a bounded MVP:

- B8 analysis contracts required by formal DEG.
- B8.9 Analysis Center gate-driven UI state.
- B9.1 dependency, parameter, result schema, and UI execution gates.
- B9.2 two-group controlled formal DEG executor.
- B9.3 / B9.3b dependency and runtime validation commands.
- B9.4 parameter confirmation flow.
- B9.5 formal DEG result review and interpretation guard.
- B9.6 formal DEG plot artifact gate.
- B9.7 formal DEG report-ready gate.
- B9.8 report package UX and package inventory.
- B9.9 end-to-end acceptance audit helper.
- B9.10 release-readiness audit document.

Keep out of carry-over:

- `project_storage/bioinformatics/`
- local fixture outputs generated during manual tests unless explicitly committed as source fixtures under tests
- untracked handoff documents not part of the B9 line
- archived legacy runner code that has not been adapted into B8/B9 contracts
- any generated `dist/` artifacts unless ReleaseBuild has its own packaging artifact policy

## 4. MainLine Intake Plan

### B9.11.1 Pre-Intake Diff Audit

Before moving changes into MainLine:

1. Record Bioinformatics source HEAD.
2. Record MainLine target branch and HEAD.
3. Compare file ownership under:
   - `app/bioinformatics/`
   - `tests/bioinformatics/`
   - `tests/ui/test_bioinformatics_workflow_pages.py`
   - `config/bioinformatics/`
   - `docs/bioinformatics/`
4. Identify any MainLine-only edits that touch the same files.
5. Preserve unrelated MainLine work and do not overwrite user changes.

Acceptance:

- Carry-over candidate file list is explicit.
- Conflicts are classified as blocker, manual merge required, or safe direct intake.
- No sibling worktree is modified during planning.

### B9.11.2 MainLine Scope Lock

MainLine release notes must state:

- Formal DEG MVP supports two-group controlled DEG only.
- Supported methods are only the audited Python methods present in B9.2.
- scipy and statsmodels are required for formal DEG.
- Result review and report package are statistical analysis outputs only.
- No clinical conclusions or treatment recommendations are provided.
- GSEA, survival, DESeq2, edgeR, limma, R backend, multi-factor design, and complex batch-aware design remain unsupported.

Acceptance:

- MainLine UI text does not imply broad DEG, GSEA, survival, or clinical analysis.
- Imported, testing, exploratory, and preflight outputs remain visually and semantically separate from formal DEG.

### B9.11.3 MainLine Validation Gate

Required checks after carry-over into MainLine:

```bash
git diff --check
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
```

If MainLine includes packaging in its normal gate, also run:

```bash
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

Acceptance:

- All required checks pass on MainLine.
- Any MainLine-specific failure is fixed in MainLine, not hidden by weakening B9 gates.

## 5. ReleaseBuild Intake Plan

### B9.11.4 ReleaseBuild Dependency Policy

ReleaseBuild must confirm one of two packaging modes before accepting formal DEG:

1. Local-python launcher mode:
   - packaged launcher detects source/runtime Python dependencies
   - scipy/statsmodels availability is checked at runtime
   - missing dependency blocks formal DEG gracefully

2. Frozen or embedded runtime mode:
   - numpy/pandas/scipy/statsmodels are bundled for macOS arm64
   - packaged executable imports them successfully
   - codesign remains valid after bundling native wheels

Acceptance:

- ReleaseBuild documents the selected dependency mode.
- Settings and Analysis Center remain detect-first.
- There is no install button or automatic dependency installation.
- Missing scipy/statsmodels produces a blocked UI state, not a traceback.

### B9.11.5 ReleaseBuild Runtime Validation

Required ReleaseBuild checks:

```bash
git diff --check
python3 -m pytest tests/bioinformatics -q -k "formal_controlled_deg or formal_deg_runtime or formal_deg_report or formal_deg_e2e or analysis_ui"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or results_browser or report or settings"
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

Controlled runtime check must also run in the environment selected for release:

```bash
python3 -m app.main --bio-formal-deg-runtime-check --bio-formal-deg-runtime-check-output /tmp/biomedpilot_release_formal_deg_runtime_check.json
```

Acceptance:

- Dependency check status is `passed` when required dependencies are present.
- numpy, pandas, scipy, and statsmodels import successfully.
- architecture is arm64 on macOS arm64 release builds.
- controlled DEG fixture produces numeric `p_value` and `adjusted_p_value`.
- result index v2 contains `result_semantics=formal_computed_result` only when all gates pass.
- formal DEG run itself still leaves `plot_artifacts=[]`, `report_artifacts=[]`, and `report_ready_eligible=False`.

### B9.11.6 LaunchServices Gate

ReleaseBuild must not rely only on direct launcher smoke. It must include a LaunchServices / Finder-style launch gate:

```bash
open -W -n dist/BioMedPilot.app --args --smoke-test
open -W -n dist/BioMedPilot.app --args --bio-formal-deg-runtime-check --bio-formal-deg-runtime-check-output /tmp/biomedpilot_release_open_runtime_check.json
```

Acceptance:

- `open -W -n` exits successfully.
- launcher ignores `-psn_*` arguments when launched by macOS.
- packaged process architecture is compatible with native dependencies.
- codesign verification passes after packaging.
- startup failure diagnostics are visible in launcher logs or app smoke output.

## 6. UX And Documentation Carry-Over

### B9.11.7 User-Facing Copy Lock

Required wording boundaries:

- "Formal DEG" must be described as statistical two-group controlled DEG.
- Result review must say statistical result only.
- Report package must say formal DEG section only.
- Table-only report mode must say that no plot artifact was included by explicit mode and does not imply volcano/heatmap generation.
- Plot/report disabled states must mention B9.6 / B9.7 gates where useful.

Disallowed wording:

- any claim of clinical conclusion
- any claim of treatment recommendation
- any claim that GSEA or survival has run
- any claim that imported DEG is BioMedPilot recomputed formal DEG
- any claim that preflight or testing output is report-ready

### B9.11.8 Release Notes Checklist

Release notes must include:

- supported scope
- unsupported scope
- dependency requirements
- packaging mode
- known limitations
- validation summary
- rollback procedure

Minimum known limitations:

- two-group controlled DEG only
- no broad omics workflow automation
- no GSEA/survival/clinical statistics
- no R-based DEG methods
- no multi-factor design
- no clinical recommendations

## 7. Rollback Plan

Rollback must be possible at three layers:

1. UI gating rollback:
   - disable formal DEG action row
   - keep review/report of existing formal results read-only

2. Runtime dependency rollback:
   - mark formal DEG dependency status as blocked
   - preserve Settings detect-first display

3. Release package rollback:
   - remove release exposure of formal DEG
   - keep B8 resolver and result browser unaffected

Rollback must not delete user project results without an explicit migration or archival step.

## 8. Blockers / Major / Minor For Carry-Over

Blockers:

- MainLine or ReleaseBuild has conflicting analysis UI/result index code that bypasses B8/B9 gates.
- ReleaseBuild cannot import scipy/statsmodels in the selected packaging mode.
- `open -W` smoke or runtime check fails.
- formal DEG button can be enabled without resolver, DEG-ready, dependency, parameter confirmation, result schema, and B9 activation gates.
- imported/testing/exploratory/preflight output can become `formal_computed_result` or report-ready.

Major:

- UI copy suggests broad DEG, GSEA, survival, or clinical conclusions.
- report package omits provenance, dependency snapshot, parameter confirmation, gate snapshot, warnings, or limitations.
- table-only report mode implies plot generation failure or hidden volcano/heatmap output.
- ReleaseBuild package size or startup time changes materially without documentation.

Minor:

- release notes omit exact dependency versions but dependency detection remains visible.
- package output path wording could be clearer while still preventing overwrite.
- MainLine docs lag behind implementation by one stage but runtime gates remain correct.

## 9. Carry-Over Acceptance Table

| Area | Required result |
| --- | --- |
| Source scope | Only B8/B9 formal DEG MVP files are selected |
| MainLine diff | Conflicts audited before merge |
| Dependency policy | detect-first, scipy/statsmodels required, no auto-install |
| Formal DEG execution | two-group controlled only |
| Result semantics | formal only when all gates pass |
| Plot artifact | only from formal DEG source result |
| Report package | formal DEG section only |
| UI copy | no broad DEG/GSEA/survival/clinical claims |
| Runtime check | source and packaged checks pass |
| LaunchServices | `open -W -n` smoke and runtime check pass |
| Codesign | strict deep verify passes |
| Untracked files | `project_storage/` and unrelated handoff docs excluded |

## 10. Suggested Next Stage

Suggested next stage: **B9.12 MainLine Formal DEG MVP Carry-Over Execution Audit**.

Recommended B9.12 scope:

1. audit MainLine target branch state
2. carry over only scoped B8/B9 formal DEG MVP files
3. resolve conflicts without weakening gates
4. run MainLine source tests and smoke
5. document MainLine intake result
6. do not package ReleaseBuild yet unless B9.12 explicitly expands scope

Suggested B9.12 output file:

```text
docs/bioinformatics/stage_B9_12_formal_deg_mvp_mainline_carryover_execution_audit_20260520.md
```

Suggested B9.12 commit message:

```text
carry over Bioinformatics formal DEG MVP to MainLine
```

ReleaseBuild should remain a separate stage after MainLine acceptance:

```text
B9.13 ReleaseBuild Formal DEG MVP Packaging Carry-Over Audit
```
