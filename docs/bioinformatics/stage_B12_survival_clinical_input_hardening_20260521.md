# Bioinformatics B12 Survival / Clinical Input Hardening

Date: 2026-05-21

Base HEAD: `a5b96314ab8c1802f482d76121ed0a93f88193d9` (`docs(bio): plan survival clinical contracts`)

## 1. Legacy / Existing Implementation Audit

Audited surfaces:

```text
app/bioinformatics/clinical_analysis/*
app/bioinformatics/services/survival_service.py
app/bioinformatics/pages/survival_page.py
app/bioinformatics/adapters/survival_adapter.py
app/bioinformatics/project_readiness.py
app/bioinformatics/project_standardization.py
app/bioinformatics/analysis_inputs/*
app/bioinformatics/analysis_ui/*
app/bioinformatics/workflow_pages.py
app/bioinformatics/results/*
app/bioinformatics/reports/*
config/bioinformatics/survival_defaults.yaml
config/bioinformatics/package_requirements.yaml
tests/bioinformatics/*survival*
tests/bioinformatics/*clinical*
tests/ui/test_bioinformatics_workflow_pages.py
```

Audit conclusion:

| Area | Decision | Reason |
|---|---|---|
| `app/bioinformatics/clinical_analysis/*` | 可复用 | Existing code is preflight/design-only and already blocks formal KM/Cox/log-rank outputs. |
| `services/survival_service.py` / `pages/survival_page.py` / `adapters/survival_adapter.py` | 不迁入 formal path | These are legacy/preflight surfaces tied to cleaning-plan JSON, not standardized B12 input contracts. |
| `project_readiness.py` / `project_standardization.py` | 可复用 | Clinical assets already standardize into `clinical_repository` and readiness text states no KM/Cox/log-rank execution. |
| `analysis_inputs/resolver.py` | 最小迁入 | Existing `tcga_clinical_survival_preflight` package is kept; B12 adds a dedicated hardening resolver without rewriting B8/B9/B10/B11 resolver behavior. |
| `analysis_ui/*` / `workflow_pages.py` | 最小迁入 | Added B12 preflight rows and disabled formal actions without enabling statistics. |
| Integration / archive survival logic | 不迁入 | Found Integration preflight/service/page surfaces; no direct copy of old KM/Cox preview or mapper was used. |
| DEG/ORA/GSEA reports/results | 不迁入 | Existing section-only packages remain unchanged and continue to exclude survival/clinical conclusions. |

## 2. B12.1 Clinical / Survival Input Resolver

Implemented:

```text
app/bioinformatics/survival_clinical/__init__.py
app/bioinformatics/survival_clinical/models.py
app/bioinformatics/survival_clinical/input_resolver.py
app/bioinformatics/survival_clinical/source_mapping.py
tests/bioinformatics/test_survival_clinical_input_resolver.py
```

The resolver reads only audited standardized sources:

```text
standardized_data/repositories/repository_manifest.json
manifests/standardized_assets_registry.json
standardized_data/repositories/analysis_input_repository/*.json
standardized_data/repositories/clinical_repository/*.json
standardized_data/repositories/validation_report.json
standardized_data/repositories/asset_lineage.jsonl
```

The resolver explicitly records forbidden sources:

```text
recognition_report.json
UI table contents
runner temp output
plot artifact
report package
unregistered raw clinical file
```

Output schema includes:

```text
schema_version
created_at
status
survival_clinical_input_id
source_dataset_id
project_root
clinical_asset
sample_metadata_asset
expression_asset
case_id_column
sample_id_column
patient_id_column
tcga_barcode_policy
case_sample_mapping_status
case_sample_mapping_table
available_time_fields
available_event_fields
available_clinical_variables
available_expression_grouping_candidates
sample_count
case_count
mapped_case_count
mapped_sample_count
duplicate_case_ids
duplicate_sample_ids
unmapped_cases
unmapped_samples
warnings
blockers
provenance
```

Blocking rules implemented:

```text
missing_clinical_asset
missing_case_or_sample_identifier
case_sample_mapping_failed
no_overlap_between_clinical_and_expression
duplicate_case_id_unresolved
duplicate_sample_id_unresolved
ambiguous_many_to_many_mapping
```

Warning rules implemented:

```text
partial_case_sample_mapping
clinical_only_cases_present
expression_only_samples_present
one_case_multiple_samples_detected
tcga_barcode_truncated_to_case_id
```

## 3. B12.2 OS_time / OS_event / Censoring Gate

Implemented:

```text
app/bioinformatics/survival_clinical/outcome_gate.py
app/bioinformatics/survival_clinical/censoring.py
tests/bioinformatics/test_survival_outcome_gate.py
config/bioinformatics/survival_defaults.yaml
```

Outcome gate supports:

```text
OS_time
OS_event
overall_survival_time
overall_survival_event
days_to_death
days_to_last_follow_up
vital_status
last_follow_up
follow_up_time
death_status
time
event
```

Derivation policy:

- OS time may be derived from `days_to_death` or `days_to_last_follow_up`.
- OS event may be derived from `vital_status` or `death_status`.
- Derived fields add warnings and provenance; no silent derivation.

Outcome gate outputs:

```text
schema_version
created_at
status
survival_outcome_gate_id
survival_clinical_input_id
time_field
event_field
time_unit
event_coding
censoring_policy
derived_os_time_policy
derived_os_event_policy
sample_count
event_count
censored_count
missing_time_count
missing_event_count
negative_time_count
zero_time_count
time_summary
event_summary
warnings
blockers
provenance
```

Blocking rules implemented:

```text
missing_time_field
missing_event_field
ambiguous_event_coding
missing_time_unit
negative_survival_time
all_time_missing
all_event_missing
no_events
case_sample_mapping_failed
```

Configured thresholds added:

```text
minimum_event_count: 5
maximum_missing_rate_warning: 0.3
maximum_missing_rate_blocker: 0.5
formal_execution_enabled: false
```

## 4. B12.3 Clinical Variable Typing / Missingness Audit

Implemented:

```text
app/bioinformatics/survival_clinical/clinical_variables.py
app/bioinformatics/survival_clinical/missingness.py
tests/bioinformatics/test_clinical_variable_typing.py
tests/bioinformatics/test_clinical_missingness_audit.py
```

Variable types:

```text
binary
categorical
ordinal
continuous
time_to_event
identifier
date
text
unknown
```

Variable audit schema:

```text
variable_name
variable_type
semantic_hint
unique_count
missing_count
missing_rate
non_missing_count
example_values
numeric_summary
category_summary
allowed_analysis_candidates
warnings
blockers
```

Candidate labels:

```text
km_grouping_candidate
logrank_grouping_candidate
cox_covariate_candidate
clinical_association_candidate
identifier_only
not_for_formal_statistics
```

Blocking rules implemented:

```text
all_missing
constant_variable
identifier_not_allowed_for_statistics
unknown_variable_type
too_few_non_missing_values
high_missing_rate when missing_rate > 0.5
```

Warning rules implemented:

```text
high_missing_rate when 0.3 < missing_rate <= 0.5
too_many_categories_for_cox
rare_category_detected
ordinal_order_needs_confirmation
date_requires_transformation
```

## 5. UI Changes

Updated:

```text
app/bioinformatics/analysis_ui/state.py
app/bioinformatics/analysis_ui/action_rules.py
app/bioinformatics/analysis_ui/labels.py
app/bioinformatics/workflow_pages.py
tests/bioinformatics/test_analysis_ui_state.py
tests/ui/test_bioinformatics_workflow_pages.py
```

Analysis Center now shows:

```text
Survival / clinical input resolver
Case/sample mapping
OS_time / OS_event / censoring gate
Clinical variable typing / missingness
Survival design preflight
KM/Cox/log-rank/HR disabled row
Clinical association preflight
```

Action matrix now includes:

```text
Review survival/clinical input readiness
Run survival outcome preflight
Review clinical variables
Run KM/log-rank disabled until B13
Run Cox model disabled until B14
Generate KM plot disabled
Export survival report-ready package disabled
Run clinical association statistics disabled
```

UI copy remains explicit:

```text
当前仅进行 survival / clinical 输入预检查。
尚未运行 KM/log-rank/Cox。
尚未生成 HR 或 survival p-value。
结果不是临床结论或治疗建议。
```

## 6. Result Semantics Boundary

B12 input hardening does not register formal result index entries.

Allowed output type:

```text
preflight artifact / gate manifest / developer diagnostics
```

If a future stage registers B12 output in result index, it must use:

```text
task_type=survival_clinical_preflight
result_semantics=preflight_only
report_ready_eligible=false
plot_artifacts=[]
report_artifacts=[]
```

Forbidden in this stage:

```text
formal_computed_result
survival_result
cox_result
clinical_association_result
HR / CI / p-value
KM plot
survival report-ready package
clinical conclusion
treatment recommendation
```

## 7. Tests and Validation

Focused tests:

```text
python3 -m pytest tests/bioinformatics/test_survival_clinical_input_resolver.py tests/bioinformatics/test_survival_outcome_gate.py tests/bioinformatics/test_clinical_variable_typing.py tests/bioinformatics/test_clinical_missingness_audit.py -q
```

Result: `10 passed`.

UI/state focused tests:

```text
python3 -m pytest tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or survival or clinical"
```

Results:

```text
16 passed
9 passed, 102 deselected
```

Full required validation is recorded in the task completion report.

Full required validation:

```text
git diff --check
```

Result: passed.

```text
python3 -m pytest tests/bioinformatics -q -k "survival or clinical or analysis_ui or result_semantics"
```

Result: `54 passed, 482 deselected`.

```text
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or survival or clinical"
```

Result: `9 passed, 102 deselected`.

```text
python3 -m pytest tests/bioinformatics -q
```

Result: `536 passed`.

```text
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

Result: `268 passed`.

```text
python3 -m app.main --smoke-test
```

Result: passed.

Package/open-W/codesign were not rerun because this stage did not modify package, runtime, launcher, or signing files.

## 8. Preserved Boundaries

Still disabled:

```text
KM
log-rank
Cox
HR / CI / survival p-value
KM plot
survival report-ready
clinical association p-value
automatic best cutoff
risk score generation
prognosis / clinical conclusion / treatment recommendation
```

Existing B9-B11 closure remains protected:

```text
formal DEG two-group MVP
ORA controlled path
GSEA controlled preranked path
DEG/ORA/GSEA plot artifacts
DEG/ORA/GSEA section-only report packages
enrichment layer closure audit
```

## 9. Next Recommendation

Proceed to:

```text
B13.1 KM / log-rank parameter gate
```

B13.1 should define KM/log-rank parameters, dependency policy, result schema, UI confirmation, and formal activation blockers. It should still not run Cox or clinical association statistics.
