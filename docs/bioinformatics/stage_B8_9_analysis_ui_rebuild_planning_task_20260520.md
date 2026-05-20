# B8.9 Analysis UI Rebuild Planning / Task File

Date: 2026-05-20

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Branch: `dev/bioinformatics`

Baseline: `66d4cc3 fix(bio): close B8 analysis contract audit findings`

## 1. Objective

Rebuild the Bioinformatics Analysis UI around the B8 contracts without enabling new formal analysis capabilities.

This task file is for the next implementation pass. It converts B8.0.1 and B8.8 into concrete UI work items, acceptance rules, test expectations, and hard boundaries.

Primary goal:

- Replace the current fragmented Analysis Task Center / DEG config / result/report surfaces with a gate-driven Analysis Center experience that renders resolver packages, blockers, warnings, dependency state, preflight state, result semantics, plot/report eligibility, and disabled reasons in one coherent workflow.

Non-goal:

- Do not implement formal GSEA.
- Do not implement survival statistics.
- Do not implement formal plotting.
- Do not turn report drafts into report-ready output unless the existing B8.6 gate passes.
- Do not add scipy/statsmodels/R/lifelines dependencies in this UI rebuild task.

## 2. Source Documents

Must read before implementation:

- `docs/bioinformatics/stage_B8_analysis_readiness_and_standardization_audit_20260520.md`
- `docs/bioinformatics/stage_B8_0_1_analysis_ui_prebuild_supplemental_audit_20260520.md`
- `docs/bioinformatics/stage_B8_8_analysis_contract_closure_audit_20260520.md`
- `docs/bioinformatics/stage_B8_1_standardized_analysis_input_resolver_20260520.md`
- `docs/bioinformatics/stage_B8_2_deg_ready_matrix_and_preflight_20260520.md`
- `docs/bioinformatics/stage_B8_3_controlled_deg_backend_mvp_20260520.md`
- `docs/bioinformatics/stage_B8_4_result_index_and_browser_foundation_20260520.md`
- `docs/bioinformatics/stage_B8_5_plot_artifact_schema_and_basic_plots_20260520.md`
- `docs/bioinformatics/stage_B8_6_report_ready_gate_and_export_package_20260520.md`
- `docs/bioinformatics/stage_B8_7_survival_and_clinical_association_design_20260520.md`

## 3. Current Runtime Surfaces

Relevant code:

- `app/bioinformatics/workflow_pages.py`
  - `BioinformaticsAnalysisTaskCenterWidget`
  - `BioinformaticsDegConfigWidget`
  - `BioinformaticsImmuneInfiltrationWidget`
  - `BioinformaticsResultsBrowserWidget`
  - `BioinformaticsReportViewerWidget`
  - `BioinformaticsSettingsAndLocalAIWidget`
- `app/bioinformatics/analysis_inputs/*`
- `app/bioinformatics/deg_ready/*`
- `app/bioinformatics/deg_engine/dependency_check.py`
- `app/bioinformatics/results/*`
- `app/bioinformatics/plots/*`
- `app/bioinformatics/reports/*`
- `app/bioinformatics/clinical_analysis/*`
- `config/bioinformatics/package_requirements.yaml`
- `tests/ui/test_bioinformatics_workflow_pages.py`

Current UI limitation:

- `BioinformaticsAnalysisTaskCenterWidget` now shows resolver summary, but it still lacks a dedicated package table, action-state table, dependency panel, repair guidance, and result/report/plot gate details.
- `can_run` from readiness/task rows can still be confused with formal execution readiness. In the rebuild it must be rendered as `config_only`, `preflight_only`, or `exploratory`, never as formal run readiness.

## 4. Hard Boundaries

The rebuild must preserve these rules:

1. Formal analysis buttons stay disabled unless all B8 gates pass.
2. Analysis UI must not use `recognition_report.json` as a formal analysis input source.
3. Resolver output is the only normal Analysis Center input package source.
4. Multiple candidate matrices block formal analysis until explicit default selection exists.
5. GEO ID_REF / probe without mapping blocks formal DEG.
6. TPM / FPKM / FPKM-UQ must not enter count-model DEG.
7. GTEx must not be auto-used as TCGA normal control.
8. Missing scipy/statsmodels blocks formal DEG and must not produce fallback p-values.
9. Imported DEG stays `imported_external_result`, not BioMedPilot recomputed DEG.
10. Testing/developer/preview/exploratory/preflight output must not be promoted to `formal_computed_result`.
11. Plot actions must be source-result-driven and inherit result semantics.
12. Report-ready export is disabled unless B8.6 gate passes.
13. Survival and clinical association remain design/preflight; KM/Cox/log-rank/HR/formal p-value/KM plot remain disabled.
14. Settings/dependency checks must detect and report; no auto-install, no traceback.
15. Legacy / Integration / ReleaseBuild code can be referenced only after audit and adaptation; no direct copy into formal runtime.

## 5. Target UX Shape

Recommended first-screen order:

1. Project and dataset summary.
2. Standardized asset status.
3. Analysis input package status.
4. Analysis capability/action matrix.
5. Blockers, warnings, and repair actions.
6. Dependency status.
7. Task configuration / preflight entry.
8. Formal run entry, disabled until all gates pass.
9. Result index and plot/report eligibility.
10. Developer diagnostics, collapsed by default.

Status vocabulary:

- `available`: stable artifact can be browsed.
- `config_only`: configuration can be saved; no execution.
- `preflight_only`: input checks can run; no formal result.
- `exploratory`: B7 immune/TME and similar exploratory outputs.
- `developer_preview`: internal/testing runner output, hidden behind developer diagnostics.
- `blocked_missing_resolver`: no resolver package.
- `blocked_missing_input_package`: package missing required assets.
- `blocked_missing_mapping`: gene/probe mapping missing.
- `blocked_value_type`: value type is incompatible with requested method.
- `blocked_missing_backend`: required dependency/backend missing.
- `blocked_missing_result_schema`: plot/report/formal task blocked by result schema.
- `blocked_report_ready_gate`: report export blocked by provenance/validation/semantics.
- `hidden_until_ready`: do not render in normal user flow.

## 6. Proposed Implementation Slices

### B8.9.1 Analysis Center State Builder

Add a small state builder rather than putting more logic directly in Qt widget methods.

Suggested files:

```text
app/bioinformatics/analysis_ui/__init__.py
app/bioinformatics/analysis_ui/state.py
app/bioinformatics/analysis_ui/action_rules.py
app/bioinformatics/analysis_ui/labels.py
tests/bioinformatics/test_analysis_ui_state.py
tests/bioinformatics/test_analysis_ui_action_rules.py
```

State input sources:

- `resolve_analysis_inputs(project_root)`
- `load_analysis_task_center(project_root)`
- `load_task_records(project_root)`
- `load_result_index(project_root)`
- `check_deg_backend_dependencies()`
- `check_survival_backend_dependencies()`
- `evaluate_report_ready_gate(project_root)`
- existing standardization/readiness artifacts for display only

State output should include:

- project summary
- standardized asset summary
- resolver package rows
- action rows
- dependency rows
- result rows
- plot/report readiness rows
- top blockers
- top warnings
- developer diagnostics payload

Acceptance:

- No formal action row is enabled by readiness `can_run` alone.
- Missing resolver or missing package produces a visible disabled reason.
- State builder has no side effects and does not execute analysis.

### B8.9.2 Package Table and Repair Guidance

Update `BioinformaticsAnalysisTaskCenterWidget` to render a resolver package table.

Suggested UI elements:

- Package type
- Status / semantics
- Source dataset id
- Value type
- Gene id type
- Allowed downstream tasks
- Blockers
- Warnings
- Next repair action

Repair examples:

- `multiple_candidate_matrices_without_default_selection` -> return to standardization and select default expression matrix.
- `geo_probe_or_id_ref_requires_platform_mapping` -> confirm/import platform mapping before DEG.
- `display_value_type_not_allowed_for_count_model_deg` -> use display/correlation/immune route or provide raw count matrix.
- `gtex_must_not_auto_fill_tcga_normal_control` -> use TCGA normal samples or explicit batch-aware design later.
- `missing_clinical_asset` -> build/import TCGA clinical metadata before survival preflight.

Acceptance:

- UI table shows package blockers/warnings without opening developer diagnostics.
- Formal disabled reasons are clear at row level.
- Existing developer JSON remains available but is no longer the only place to inspect package details.

### B8.9.3 Action Matrix and Button Gate Rules

Replace ambiguous action text with gate-specific rows.

Normal user actions:

| Action | State now | Button behavior |
| --- | --- | --- |
| Configure DEG / Run DEG preflight | `config_only` / `preflight_only` | enabled only when minimum config inputs exist |
| Run formal DEG | `blocked_missing_backend` or other blocker | disabled or hidden |
| Review imported DEG | `available` if imported package exists | enabled |
| Immune / TME scoring | `exploratory` | enabled only as exploratory if B7 readiness passes |
| Survival preflight | `preflight_only` | enabled only for design/preflight, no KM/Cox/log-rank |
| Generate plot spec | `blocked_missing_result_schema` unless source result is eligible | disabled until result entry supports plot |
| Generate Markdown draft | `draft_only` | enabled as draft |
| Export report-ready package | `blocked_report_ready_gate` | disabled until B8.6 gate passes |

Developer-only actions:

- Testing GEO DEG runner remains behind developer diagnostics.
- Any developer preview action must display `developer_preview` and `testing_level`.

Acceptance:

- No button text says or implies "Run formal DEG", "Run GSEA", "Run Survival", "Generate formal plot", or "Export report-ready" when the gate is blocked.
- Tests assert disabled/hidden state for formal DEG, GSEA, KM/Cox/log-rank, KM plot, and report-ready export.

### B8.9.4 Dependency Status Panel

Add analysis dependency detection to Settings or Analysis Center diagnostics.

Source contracts:

- `app/bioinformatics/deg_engine/dependency_check.py`
- `app/bioinformatics/clinical_analysis/dependency_check.py`
- `config/bioinformatics/package_requirements.yaml`

Display:

- Python packages: numpy, pandas, scipy, statsmodels.
- Optional survival backend: lifelines.
- Optional R backend packages: limma, DESeq2, edgeR, survival, survminer.
- Status: installed/version, missing, optional-not-configured.
- Action: detect only; do not install.

Acceptance:

- Missing dependency shows blocker message, not traceback.
- UI contains no auto-install button.
- DEG formal action remains blocked when scipy/statsmodels are missing.
- Survival formal action remains blocked when lifelines/R backend is missing or not enabled.

### B8.9.5 Result / Plot / Report Gate Preview

Update result/report surfaces to expose B8.4-B8.6 gates.

Result browser should show:

- canonical semantics
- input package id
- engine/version
- dependency snapshot status
- validation status
- warnings/blockers
- plot artifact availability
- report-ready eligibility

Report viewer should show:

- draft-only status
- report-ready gate status
- blockers and warnings
- export package disabled reason
- included result semantics

Plot preview should show:

- source result id
- source semantics
- plot type
- why plot action is available/blocked

Acceptance:

- Testing/exploratory/imported/preflight results cannot appear report-ready unless explicit test-report mode is displayed.
- Plot action cannot be enabled for preflight-only source.
- Report-ready export cannot be enabled when dependency snapshot, validation, provenance, or plot artifact requirements are missing.

### B8.9.6 Survival / Clinical UI Preflight Rows

Add or update Analysis Center rows for clinical/survival.

Display:

- clinical asset present/missing
- expression asset present/missing
- time field
- event field
- event coding status
- event count
- missingness
- grouping policy
- backend detection
- disabled KM/Cox/log-rank reasons

Acceptance:

- UI says "仅预检查" or equivalent.
- No KM/Cox/log-rank/HR/formal p-value output action exists.
- KM plot remains hidden/disabled.
- Missing event field, ambiguous event coding, low event count, and missing grouping policy are visible.

## 7. Suggested File-Level Change Plan

Primary code edits:

```text
app/bioinformatics/analysis_ui/__init__.py
app/bioinformatics/analysis_ui/state.py
app/bioinformatics/analysis_ui/action_rules.py
app/bioinformatics/analysis_ui/labels.py
app/bioinformatics/workflow_pages.py
```

Optional docs:

```text
docs/bioinformatics/stage_B8_10_analysis_ui_rebuild_implementation_20260520.md
```

Tests:

```text
tests/bioinformatics/test_analysis_ui_state.py
tests/bioinformatics/test_analysis_ui_action_rules.py
tests/ui/test_bioinformatics_workflow_pages.py
```

Do not modify unless the implementation genuinely needs it:

- `pyproject.toml`
- statistical runner modules
- legacy directories
- ReleaseBuild / Integration worktrees

## 8. Minimum Test Matrix

Required after implementation:

```bash
git diff --check
python3 -m pytest tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py -q
python3 -m pytest tests/bioinformatics -q -k "analysis_input or resolver or task_run or deg_ready or deg_engine or dependency or result_index or result_registry or result_semantics or plot or report or survival or clinical or analysis_ui"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or results_browser or report or settings"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
```

If UI code changes are substantial, also run:

```bash
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

## 9. Acceptance Criteria

The Analysis UI rebuild passes only if all of the following are true:

1. Analysis Center state is built from B8 contracts, not ad hoc UI table scraping.
2. Resolver package table is visible and includes blockers/warnings.
3. Action matrix uses explicit states and disabled reasons.
4. DEG formal run is disabled unless resolver, DEG-ready, dependency, parameters, and result schema gates pass.
5. GSEA formal run remains disabled/hidden.
6. Survival formal run and KM/Cox/log-rank remain disabled/hidden.
7. Plot actions remain source-result-driven and preflight-only sources are blocked.
8. Report-ready export remains blocked unless B8.6 gate passes.
9. Settings/dependency status is detect-first and has no install action.
10. Developer preview/testing actions remain separated from normal user actions.
11. UI wording does not imply formal analysis is complete when state is config/preflight/exploratory/testing/imported.
12. Existing imported DEG, B7 immune score, report draft, and result browser tests continue to pass.

## 10. Out of Scope for This Rebuild

Out of scope:

- Installing scipy/statsmodels.
- Enabling formal DEG execution by default.
- R backend, rpy2, limma, DESeq2, edgeR.
- GSEA executor.
- Survival KM/Cox/log-rank executor.
- Clinical association statistical tests.
- Rendering bitmap/SVG/PDF plot outputs as formal figures.
- DOCX/PDF report generation.
- Legacy code migration beyond audited concepts.

## 11. Hand-off Summary

Recommended next implementation commit:

```bash
git commit -m "rebuild Bioinformatics analysis center gates"
```

Recommended final report for implementation:

- changed files
- screenshots or UI test evidence if available
- action state table before/after
- dependency panel behavior
- disabled formal analysis reasons
- tests run
- remaining blockers for B9.1 formal DEG dependency activation

Next milestone after successful UI rebuild:

- B9.1 formal DEG dependency activation planning, limited to scipy/statsmodels dependency audit, Settings status, packaging impact, and gate-controlled formal DEG enablement.
