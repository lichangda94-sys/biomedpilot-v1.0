# B44 Risk Score Calibration / Decision Curve Statistics Execution Audit

Date: 2026-05-27

## Scope

B44 activates a controlled statistics-table execution path for risk score calibration and decision curve analysis.

This stage computes real tabular statistics from a validation probability table:

- observed-vs-predicted calibration table
- decision-curve net-benefit table

B44 does not create calibration curve plots, decision curve plots, report-ready packages, risk groups, clinical conclusions, prognosis labels, or treatment recommendations.

## Implemented Changes

Updated:

- `app/bioinformatics/survival_clinical/risk_score_plot_schema.py`
- `app/bioinformatics/survival_clinical/__init__.py`
- `app/bioinformatics/analysis_ui/state.py`
- `app/bioinformatics/analysis_ui/action_rules.py`
- `tests/bioinformatics/test_risk_score_plot_gate.py`
- `tests/bioinformatics/test_analysis_ui_state.py`
- `tests/bioinformatics/test_analysis_ui_action_rules.py`

## New Gate And Executor

Public functions:

- `build_risk_score_calibration_decision_curve_statistics_gate(project_root, result_id=None, planning_config=None)`
- `run_risk_score_calibration_decision_curve_statistics(project_root, result_id=None, planning_config=None)`

Schemas:

- `biomedpilot.risk_score_calibration_decision_curve_statistics_gate.v1`
- `biomedpilot.risk_score_calibration_decision_curve_statistics_manifest.v1`

## Input Requirements

B44 requires:

- B43 input gate status `ready_for_future_artifact_gate`
- validation probability table path
- numeric predicted probability column
- probability scale in `[0, 1]`
- observed event mapping
- minimum event count
- calibration bin count
- threshold probability grid
- net-benefit formula policy
- treat-all / treat-none baseline policy

## Statistics Outputs

B44 writes table artifacts only:

- `risk_score_calibration_statistics_table`
- `risk_score_decision_curve_statistics_table`
- `risk_score_calibration_decision_curve_statistics_manifest`

The calibration table contains:

- `bin`
- `n`
- `mean_predicted_probability`
- `observed_event_rate`
- `event_count`

The decision curve table contains:

- `threshold_probability`
- `net_benefit_model`
- `net_benefit_treat_all`
- `net_benefit_treat_none`
- `true_positive`
- `false_positive`
- `n`

## Result Index Boundary

B44 attaches statistics-table artifacts to the source formal risk score result in result index v2.

It still enforces:

- `creates_plot_artifact=False`
- `creates_report_artifact=False`
- `report_ready_eligible=False`

## UI Behavior

Analysis Center now exposes:

- `Risk score calibration / decision curve statistics`

Action matrix now exposes:

- `risk_score_calibration_decision_curve_statistics`

When the statistics gate passes, the action is enabled only for table artifacts:

- `button_behavior=enabled_statistics_table_artifacts_only`

When blocked, disabled reasons include missing validation probability table, B43 input blockers, invalid rows, probability range failures, or insufficient event count.

## Still Blocked

B44 does not enable:

- calibration curve plot artifact
- decision curve plot artifact
- report-ready unlock
- risk group generation
- clinical interpretation
- treatment recommendation

## Verification

Commands run:

- `python3 -m py_compile app/bioinformatics/survival_clinical/risk_score_plot_schema.py app/bioinformatics/survival_clinical/__init__.py app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py`
- `python3 -m pytest -q tests/bioinformatics/test_risk_score_plot_gate.py tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py`

Additional broader regression, app smoke, package smoke, open-W, and codesign results are recorded in the final task handoff.

## Conclusion

B44 permits real calibration and decision-curve statistics tables while preserving the plot/report/clinical boundaries. Calibration and decision curve plot artifact activation remains a later gated stage.
