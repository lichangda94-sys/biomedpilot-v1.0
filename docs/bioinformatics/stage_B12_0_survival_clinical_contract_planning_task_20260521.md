# Bioinformatics B12.0 Survival / Clinical Contract Planning Task

Date: 2026-05-21

Base branch: `codex/releasebuild-formal-deg-carryover`

Base HEAD: `3f416ad11db5947c6bcc7886c2c5b04c22366bf9` (`docs(bio): plan enrichment layer release readiness`)

## 1. Goal

Define the B12 Survival / Clinical analysis contract line before any formal KM, Cox, log-rank, HR, clinical association statistics, plot, or report-ready implementation is enabled.

This stage is planning-only. It must preserve the closed B9-B11 formal DEG / ORA / GSEA MVP and prevent future Survival / Clinical work from causing rollback, semantic drift, or accidental report/report-ready expansion.

## 2. Non-Goals

B12.0 must not implement or enable:

```text
formal KM curve
formal Cox model
formal log-rank p-value
hazard ratio / HR
multivariate Cox
clinical association p-value
clinical diagnosis / treatment recommendation
clinical conclusion
survival plot artifact
survival report-ready package
full integrated report
automatic GSEA / ORA / DEG rerouting
lifelines / R survival auto-install
```

B12.0 must not modify:

```text
app/bioinformatics/enrichment/*
app/bioinformatics/gsea/*
app/bioinformatics/reports/ora.py
app/bioinformatics/reports/gsea.py
app/bioinformatics/reports/formal_deg.py
```

except for later explicit cross-contract audit fixes that preserve B9-B11 behavior.

## 3. Current Pre-B12 State

Existing surfaces:

```text
app/bioinformatics/clinical_analysis/__init__.py
app/bioinformatics/clinical_analysis/dependency_check.py
app/bioinformatics/clinical_analysis/models.py
app/bioinformatics/clinical_analysis/preflight.py
app/bioinformatics/clinical_analysis/survival_design.py
app/bioinformatics/adapters/survival_adapter.py
app/bioinformatics/pages/survival_page.py
app/bioinformatics/services/survival_service.py
tests/bioinformatics/test_survival_input_preflight.py
tests/bioinformatics/test_clinical_association_preflight.py
tests/bioinformatics/test_survival_service.py
```

Existing Analysis UI state:

- `survival_preflight` is shown as preflight/design only.
- `survival_formal` is disabled / hidden until a later audited stage.
- `km_cox_logrank` is disabled / hidden.
- dependency rows are detect-first and show no install action.
- report package surfaces explicitly exclude survival and clinical conclusions.

Existing B9-B11 freeze point:

- formal DEG: two-group controlled DEG MVP only.
- ORA: controlled ORA from formal/imported DEG result index.
- GSEA: controlled preranked GSEA from formal/imported DEG result index.
- plot artifacts: DEG/ORA/GSEA only; ORA/GSEA are spec-only.
- report packages: DEG/ORA/GSEA section-only; no full integrated report.

## 4. B12 Contract Principles

All Survival / Clinical work must obey these rules:

1. Additive-only development: new modules, new tests, and UI rows may be added; B9-B11 contracts must not be rewritten.
2. Source-of-truth inputs must come from standardized assets, clinical manifests, sample alignment manifests, and result index references, not from ad hoc UI tables.
3. Preflight/design outputs are not formal computed results.
4. Survival / Clinical results must never be inserted into DEG/ORA/GSEA report packages.
5. Plot/report-ready activation requires later dedicated gates.
6. Dependency detection is detect-first; no automatic installation.
7. UI must show blocked/disabled reasons before any formal execution is available.
8. No output text may provide clinical advice, diagnosis, treatment recommendation, or treatment prioritization.

## 5. Proposed B12 Stage Sequence

### B12.1 Clinical Input Resolver / Sample Alignment Gate

Goal: define and validate clinical input packages.

Suggested files:

```text
app/bioinformatics/clinical_analysis/input_resolver.py
app/bioinformatics/clinical_analysis/sample_alignment.py
tests/bioinformatics/test_clinical_input_resolver.py
tests/bioinformatics/test_clinical_sample_alignment_gate.py
docs/bioinformatics/stage_B12_1_clinical_input_resolver_sample_alignment_20260521.md
```

Required manifest fields:

```text
schema_version
clinical_input_package_id
source_dataset_id
clinical_asset_id
clinical_table_path
clinical_manifest_path
sample_id_column
patient_id_column
expression_sample_id_column
case_id_column
time_fields
event_fields
candidate_group_fields
candidate_covariates
missing_value_policy
censoring_policy
sample_alignment_policy
matched_sample_count
unmatched_expression_samples
unmatched_clinical_samples
warnings
blockers
created_at
```

Must block:

```text
missing clinical table
missing sample/patient id mapping
no expression-clinical overlap
duplicate sample or patient ids without policy
ambiguous time/event fields without user confirmation
clinical data used as DEG/ORA/GSEA source
```

### B12.2 Survival Design Preflight Gate

Goal: evaluate whether survival analysis is design-ready without producing statistics.

Suggested files:

```text
app/bioinformatics/clinical_analysis/survival_preflight.py
tests/bioinformatics/test_survival_design_preflight_gate.py
docs/bioinformatics/stage_B12_2_survival_design_preflight_gate_20260521.md
```

Allowed output semantics:

```text
task_type=survival_design_preflight
result_semantics=preflight_only
```

Allowed outputs:

```text
endpoint availability
time/event field mapping
candidate grouping variables
event count
group sample count
missingness summary
blocked/ready design state
warnings and limitations
```

Forbidden outputs:

```text
KM curve
log-rank p-value
HR
Cox coefficient
Cox p-value
survival plot artifact
survival report-ready package
clinical interpretation
```

Must block:

```text
missing time field
missing event field
invalid event coding
no grouping variable
single group only
low event count for formal analysis
sample alignment mismatch
dependency snapshot not detectable
```

### B12.3 Clinical Association Preflight Gate

Goal: classify variables and evaluate feasibility without formal statistics.

Suggested files:

```text
app/bioinformatics/clinical_analysis/association_preflight.py
tests/bioinformatics/test_clinical_association_preflight_gate.py
docs/bioinformatics/stage_B12_3_clinical_association_preflight_gate_20260521.md
```

Allowed output semantics:

```text
task_type=clinical_association_preflight
result_semantics=preflight_only
```

Allowed outputs:

```text
variable type detection
candidate outcome/covariate classification
missingness summary
sample count
group count
recommended design checks
warnings and blockers
```

Forbidden outputs:

```text
formal p-value
odds ratio
hazard ratio
regression coefficient
clinical conclusion
treatment recommendation
```

### B12.4 Survival / Clinical Result Schema Gate

Goal: define future formal result index requirements before formal execution.

Suggested files:

```text
app/bioinformatics/clinical_analysis/result_schema.py
tests/bioinformatics/test_survival_clinical_result_schema_gate.py
docs/bioinformatics/stage_B12_4_survival_clinical_result_schema_gate_20260521.md
```

Future formal result entries must include:

```text
result_id
task_run_id
task_type
result_semantics
clinical_input_package_id
sample_alignment_manifest
parameters_manifest
dependency_snapshot
engine_name
engine_version
output_artifacts
plot_artifacts
report_artifacts
validation_status
warnings
blockers
log_artifacts
created_at
updated_at
schema_version
clinical_conclusion_enabled=false
report_ready_eligible=false by default
```

Must block:

```text
formal result without clinical_input_package_id
formal result without sample_alignment_manifest
formal result without parameters_manifest
formal result without dependency_snapshot
formal result with clinical conclusion enabled
preflight/testing/exploratory marked formal
survival/clinical result inserted into DEG/ORA/GSEA report package
```

### B12.5 Analysis UI Survival / Clinical Gate Integration

Goal: show contract state in Analysis Center without enabling formal execution.

Suggested files:

```text
app/bioinformatics/analysis_ui/state.py
app/bioinformatics/analysis_ui/action_rules.py
tests/bioinformatics/test_analysis_ui_survival_clinical_contract.py
tests/ui/test_bioinformatics_workflow_pages.py
docs/bioinformatics/stage_B12_5_survival_clinical_analysis_ui_gates_20260521.md
```

UI requirements:

```text
Clinical input package visible
sample alignment visible
survival endpoint fields visible
candidate covariates visible
blockers/warnings visible
dependency status visible
formal KM/Cox/log-rank buttons disabled or hidden
disabled reasons visible
preflight-only wording visible
no report-ready wording
no clinical advice wording
```

Must keep enabled:

```text
existing DEG/ORA/GSEA buttons when their own gates pass
existing imported DEG review
existing result browser
existing section-only report package exports
```

Must keep disabled:

```text
formal survival run
KM plot
Cox model
log-rank p-value
HR output
clinical association statistics
survival/clinical report-ready package
full integrated report
```

### B12.6 Survival Runtime Dependency Policy

Goal: decide dependency strategy before formal runtime execution.

Suggested files:

```text
app/bioinformatics/clinical_analysis/dependency_policy.py
tests/bioinformatics/test_survival_clinical_dependency_policy.py
docs/bioinformatics/stage_B12_6_survival_runtime_dependency_policy_20260521.md
```

Dependency policy questions:

```text
Should lifelines be required for formal survival?
Should scipy/statsmodels be enough for limited tests?
Should R survival/survminer be optional only?
How are dependencies packaged in macOS arm64 app?
How is missing dependency shown in Settings and Analysis Center?
What package-size and startup impact is acceptable?
```

No automatic installation is allowed.

## 6. Result Semantics Policy

Allowed during B12.1-B12.5:

```text
preflight_only
configured_not_run
blocked
failed
```

Reserved for later audited activation only:

```text
formal_computed_result
```

Explicitly forbidden:

```text
testing_level -> formal_computed_result upgrade
exploratory -> formal_computed_result upgrade
preflight_only -> formal_computed_result upgrade
imported_external_result -> formal_computed_result upgrade
```

Survival/clinical tasks should use distinct task types:

```text
clinical_input_preflight
survival_design_preflight
clinical_association_preflight
survival_analysis
clinical_association
```

Formal `survival_analysis` and `clinical_association` are future-only until B12 formal activation tasks pass.

## 7. Report / Plot Boundary

B12.1-B12.6 must not create:

```text
survival plot artifact
clinical association plot artifact
survival report-ready package
clinical report-ready package
full integrated report
```

Existing DEG/ORA/GSEA packages must continue to include:

```text
survival_enabled=false
clinical_conclusion_enabled=false
no clinical interpretation
no treatment recommendation
section_scope=formal_deg_only / formal_ora_only / formal_gsea_only / imported_derived_*_only
```

Any future survival/clinical report package must be a separate B12.x task and must not change existing B9-B11 package semantics.

## 8. File Isolation Plan

Prefer new code under:

```text
app/bioinformatics/clinical_analysis/
tests/bioinformatics/test_survival_*.py
tests/bioinformatics/test_clinical_*.py
docs/bioinformatics/stage_B12_*.md
```

Allowed additive edits:

```text
app/bioinformatics/analysis_ui/state.py
app/bioinformatics/analysis_ui/action_rules.py
app/bioinformatics/workflow_pages.py
app/bioinformatics/clinical_analysis/__init__.py
```

Do not touch unless a task explicitly requires and B9-B11 regression gates pass:

```text
app/bioinformatics/enrichment/
app/bioinformatics/gsea/
app/bioinformatics/reports/ora.py
app/bioinformatics/reports/gsea.py
app/bioinformatics/reports/formal_deg.py
app/bioinformatics/plots/ora.py
app/bioinformatics/plots/gsea.py
```

## 9. Regression Gates to Protect B9-B11

Every B12 implementation task must run:

```text
git diff --check
python3 -m pytest tests/bioinformatics/test_survival_input_preflight.py tests/bioinformatics/test_clinical_association_preflight.py -q
python3 -m pytest tests/bioinformatics/test_enrichment_layer_closure_audit.py -q
python3 -m pytest tests/bioinformatics -q -k "formal_deg or ora or gsea or enrichment or result_semantics or plot or report or e2e or analysis_ui or survival or clinical"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or results_browser or report or survival or clinical"
python3 -m app.main --smoke-test
```

Before a release candidate:

```text
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

## 10. Rollback Avoidance Rules

Use these rules to avoid rollback or regression:

1. Create one B12 commit per bounded stage.
2. Keep each commit additive and scoped.
3. Run B9-B11 closure tests on every B12 stage.
4. Do not reuse DEG/ORA/GSEA report package fields for survival/clinical results.
5. Do not overload `report_ready_eligible`.
6. Do not introduce new dependency requirements into package config until dependency policy is approved.
7. Do not remove disabled UI states until formal activation task passes.
8. If a B12 task fails, revert only that B12 commit; B9-B11 should remain intact.

Recommended branch strategy:

```text
codex/b12-survival-clinical-contract
```

Carry-over should be scoped by B12 stage, not by broad branch merge.

## 11. B12.0 Acceptance Criteria

B12.0 is complete when:

```text
contract boundaries are documented
B12.1-B12.6 execution sequence is documented
formal survival/clinical activation remains disabled
B9-B11 regression gates are listed
file isolation and rollback rules are listed
no feature code is changed
docs/release/ReleaseBuild_handoff_report_20260513.md remains excluded
```

## 12. Recommended Next Task

Proceed to:

```text
B12.1 Clinical Input Resolver / Sample Alignment Gate
```

Do not start KM/Cox/log-rank runtime execution until B12.1-B12.6 pass and a separate formal activation task is created.
