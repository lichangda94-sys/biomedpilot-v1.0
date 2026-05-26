# Bioinformatics B35 Risk Score Result Review / Table Export

Date: 2026-05-26

Branch: `codex/releasebuild-formal-deg-carryover`

Baseline: `5846b63 add Bioinformatics controlled risk score MVP`

## Scope

B35 adds review and table export for B34 controlled risk score results.

This stage does not compute new risk scores, does not create risk groups, does not render nomograms, does not generate plot artifacts, does not create report-ready packages, and does not output clinical diagnosis, prognosis, treatment recommendation, or validated clinical risk stratification.

## Review Contract

New module:

- `app/bioinformatics/survival_clinical/risk_score_review.py`

New exported APIs:

- `build_risk_score_result_review(...)`
- `export_risk_score_review_table(...)`

Review schema:

- `biomedpilot.risk_score_result_review.v1`

Accepted source:

- `task_type=risk_score`
- `result_semantics=formal_computed_result`
- `risk_score_result_table` output artifact exists
- `plot_artifacts=[]`
- `report_artifacts=[]`
- `report_ready_eligible=False`

Rejected sources:

- imported/testing/exploratory/preflight/non-formal risk score entries
- risk score entries that already contain plot/report artifacts
- risk score entries marked report-ready
- non-risk-score task types

## Review UI

Results Browser now includes a `Controlled risk score result review` section with:

- guard copy
- sort by risk score, sample id, or input order
- filter all / positive score / negative score
- result summary
- risk score table preview
- provenance table
- TSV/CSV export buttons

The provenance panel shows:

- input package id
- source Cox multivariate result id
- parameter confirmation schema and timestamp
- dependency snapshot presence
- task-run log
- result index path
- result table path
- plot artifacts
- report artifacts
- report-ready eligibility

## Export

Export path:

- `results/exports/risk_score_review/<result_id>_review.tsv`
- `results/exports/risk_score_review/<result_id>_review.csv`

Exported columns:

- `sample_id`
- `case_id`
- `risk_score`
- `source_cox_multivariate_result_id`
- `model_formula`
- `coefficient_source`
- `missingness_policy`
- `scaling_policy`
- `warnings`

Export metadata keeps:

- `report_ready_eligible=False`
- `plot_artifacts=[]`
- `report_artifacts=[]`

## Boundaries Preserved

B35 does not:

- compute or recompute risk scores
- create high/low risk groups
- apply cutoff-derived risk labels
- render nomogram, calibration curve, or decision curve
- create risk score plot artifacts
- create risk score report-ready packages
- unlock full integrated report
- output clinical prognosis, diagnosis, treatment recommendation, or validated stratification
- include imported/testing/exploratory/preflight risk score entries in formal review

## Verification

Commands intended for this stage:

- `python3 -m py_compile app/bioinformatics/survival_clinical/risk_score_review.py app/bioinformatics/survival_clinical/__init__.py app/bioinformatics/workflow_pages.py`
- `python3 -m pytest -q tests/bioinformatics/test_risk_score_result_review.py tests/bioinformatics/test_risk_score_execution.py tests/bioinformatics/test_risk_score_result_schema.py`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "risk or results_browser"`
- `python3 -m pytest tests/bioinformatics -q -k "risk_score or survival_clinical"`
- `git diff --check`
- `python3 -m app.main --smoke-test`
- `python3 scripts/package_app.py --smoke-test`
- `open -W -n dist/BioMedPilot.app --args --smoke-test`
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`

Observed results:

- py_compile: passed
- risk score focused tests: 10 passed
- UI results browser focused tests: 13 passed, 107 deselected
- broader Bioinformatics filtered tests: 43 passed, 696 deselected
- `git diff --check`: passed
- source smoke: passed
- package smoke: passed
- open-W smoke: passed
- codesign: passed

## Issues

Blocker: none at implementation start.

Major: none.

Minor: B35 is table review/export only. Risk group, nomogram, plot artifact, report-ready, and clinical interpretation remain future gated stages.

## Conclusion

B35 adds controlled risk score result review and table-only export while preserving all risk group, nomogram, plotting, report-ready, and clinical interpretation boundaries.
