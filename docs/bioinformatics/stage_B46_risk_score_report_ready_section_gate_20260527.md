# B46 Risk Score Report-Ready Section Gate

Date: 2026-05-27

## Scope

B46 adds a report-ready section gate and export package for controlled risk score validation outputs. It consumes only already registered formal risk score result index entries plus the B42 nomogram plot artifact, B44 calibration / decision curve statistics tables, and B45 calibration / decision curve plot artifacts.

This stage does not create a full integrated report, clinical conclusion, prognosis label, treatment recommendation, risk group, cutoff, or validated clinical risk score claim.

## Gate Inputs

- `task_type=risk_score`
- `result_semantics=formal_computed_result`
- result index v2 entry with passed dependency snapshot, validation status, parameters manifest, task-run log, and risk score result table
- B42 `risk_score_nomogram` formal plot artifact
- B44 `risk_score_calibration_statistics_table`
- B44 `risk_score_decision_curve_statistics_table`
- B45 `risk_score_calibration_curve` and `risk_score_decision_curve` formal plot artifacts, unless explicit table-only mode is selected

## Blocking Rules

The gate blocks when the risk score result is missing, non-formal, has blockers, lacks dependency / parameter / validation provenance, lacks task-run log, lacks required B42/B44/B45 artifacts, contains invalid risk score table rows, or contains clinical conclusion / diagnosis / prognosis / treatment recommendation fields.

Table-only mode remains explicit. It can waive B45 calibration / decision plot artifacts, but it still requires the formal risk score table, B42 nomogram artifact, B44 statistics tables, provenance, dependency snapshot, and result schema validation.

## Export Package

`create_risk_score_report_ready_package` writes a timestamped package under:

- `survival_clinical_report_package/risk_score_validation_only/`

Package contents include:

- `risk_score_validation_report.md`
- `README_limitations.md`
- `tables/`
- `plots/`
- `manifests/gate_snapshot.json`
- `manifests/result_index_snapshot.json`
- `manifests/source_result_entry.json`
- `manifests/parameters_manifest.json`
- `manifests/dependency_snapshot.json`
- `manifests/table_validation.json`
- `manifests/plot_artifacts.json`
- `manifests/warnings_limitations.json`
- `provenance/provenance.json`
- `logs/`

The source result is updated with `report_ready_eligible=True` only after package creation and only with a `risk_score_report_ready_package` artifact scoped to `risk_score_validation_only`.

## UI Wiring

Analysis Center now shows:

- Risk score validation section report-ready gate preview
- Risk score validation section package row in Survival / Clinical rows
- `survival_report_ready` action can export KM, Cox, or risk score validation section-only packages when the corresponding gate passes
- disabled reasons include `missing_risk_score_result` and artifact-specific B42/B44/B45 blockers

The action copy explicitly states that the package is section-only and does not create a full integrated report, prognosis label, treatment recommendation, or validated clinical risk score.

## Boundaries

- No full integrated report unlock
- No clinical conclusion
- No treatment recommendation
- No prognosis label
- No risk group or cutoff generation
- No new risk score model training
- No imported/testing/exploratory/preflight source upgrade

## Verification

Focused verification:

- `python3 -m py_compile app/bioinformatics/reports/survival_clinical.py app/bioinformatics/reports/__init__.py app/bioinformatics/survival_clinical/risk_score_result_schema.py app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py`
- `python3 -m pytest -q tests/bioinformatics/test_risk_score_report_ready_gate.py tests/bioinformatics/test_risk_score_result_schema.py tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py`
