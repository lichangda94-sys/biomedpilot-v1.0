# Bioinformatics B36 Risk Score Plot / Nomogram Gate Planning

Date: 2026-05-26

Branch: `codex/releasebuild-formal-deg-carryover`

Baseline: `2b0e89a add Bioinformatics risk score result review`

## Scope

B36 defines a planning-only gate for future risk score visualization and nomogram work.

This stage does not generate risk score plots, nomograms, calibration curves, decision curves, plot artifacts, report artifacts, report-ready packages, risk groups, clinical prognosis, diagnosis, treatment recommendation, or clinical conclusions.

## Gate

New module:

- `app/bioinformatics/survival_clinical/risk_score_plot_gate.py`

New API:

- `build_risk_score_plot_nomogram_gate(project_root, result_id=None)`

Schema:

- `biomedpilot.risk_score_plot_nomogram_gate.v1`

Status:

- `blocked_planning_only`

The gate always includes:

- `b37_risk_score_renderer_activation_required`

This activation blocker is intentional. B36 may show prerequisites and planned artifacts, but it cannot create artifacts.

## Accepted Source

The source must be a formal B34 risk score result:

- `task_type=risk_score`
- `result_semantics=formal_computed_result`
- validation status `passed` or `warning`
- dependency snapshot status `passed`
- parameter confirmation present
- `risk_score_result_table` output artifact present
- `plot_artifacts=[]`
- `report_artifacts=[]`
- `report_ready_eligible=False`

## Planned Artifacts

B36 records planned artifact descriptors only:

- `risk_score_distribution_plot`
- `risk_score_nomogram`
- `risk_score_calibration_curve`
- `risk_score_decision_curve`

All planned artifacts use:

- `activation_status=planned_disabled`

No image, spec, registry artifact, or result index update is written in B36.

## UI Integration

Analysis Center now includes:

- survival/clinical gate row: `B36 Risk score plot / nomogram gate`
- survival/clinical status row: `Risk score plot / nomogram planning`
- action row: `risk_score_plot_nomogram`

The action remains disabled with state:

- `blocked_planning_only`

Disabled reason includes:

- `b37_risk_score_renderer_activation_required`

## Boundaries Preserved

B36 does not:

- create plot artifacts
- create report artifacts
- write result index v2
- render nomogram
- render calibration or decision curve
- create high/low-risk groups
- apply cutoff-derived risk labels
- unlock report-ready
- unlock full integrated report
- output clinical prognosis, diagnosis, treatment recommendation, or clinical conclusion

## Verification

Commands intended for this stage:

- `python3 -m py_compile app/bioinformatics/survival_clinical/risk_score_plot_gate.py app/bioinformatics/survival_clinical/__init__.py app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py`
- `python3 -m pytest -q tests/bioinformatics/test_risk_score_plot_gate.py tests/bioinformatics/test_risk_score_result_review.py tests/bioinformatics/test_risk_score_result_schema.py`
- `python3 -m pytest -q tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_capability_map.py`
- `python3 -m pytest tests/bioinformatics -q -k "risk_score or survival_clinical or analysis_ui"`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "risk or analysis_task"`
- `git diff --check`
- `python3 -m app.main --smoke-test`
- `python3 scripts/package_app.py --smoke-test`
- `open -W -n dist/BioMedPilot.app --args --smoke-test`
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`

Observed results:

- py_compile: passed
- risk score plot/review/schema focused tests: 9 passed
- Analysis UI / capability focused tests: 30 passed
- broader Bioinformatics filtered tests: 70 passed, 671 deselected
- focused UI workflow tests: 8 passed, 112 deselected
- `git diff --check`: passed
- source smoke: passed
- package smoke: passed
- open-W smoke: passed
- codesign: passed

## Issues

Blocker: none at implementation start.

Major: none.

Minor: B36 is intentionally planning-only. Real risk score visualization and nomogram rendering require a later renderer/schema activation stage.

## Conclusion

B36 adds a strict planning gate for future risk score visualization while preserving all artifact, report-ready, risk-group, and clinical interpretation boundaries.
