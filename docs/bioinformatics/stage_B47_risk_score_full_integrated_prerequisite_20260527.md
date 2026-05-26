# B47 Risk Score Full Integrated Report Prerequisite

Date: 2026-05-27

## Scope

B47 makes the B46 risk score validation section package visible to the full integrated report gate as an optional, explicitly requested prerequisite.

The default full integrated report required set remains unchanged:

- formal DEG
- ORA enrichment
- preranked GSEA
- KM/log-rank survival
- Cox clinical association

Risk score validation is not required by default. It participates only when `risk_score_validation` is present in `include_sections` or when `section_result_ids` includes a `risk_score_validation` result id.

## Gate Behavior

When included, `risk_score_validation` must satisfy:

- `task_type=risk_score`
- `result_semantics=formal_computed_result`
- result index v2 fields, dependency snapshot, validation status, task-run log, and source table checks
- B46 `evaluate_risk_score_report_ready_gate`
- registered `risk_score_report_ready_package`
- section scope `risk_score_validation_only`
- package integrity validation, including stable tables / plots / manifests / logs / provenance paths

If the risk score result exists but the B46 section package has not been created, the full integrated gate remains blocked with:

- `full_integrated_prerequisite_survival_clinical_section_package_not_passed:risk_score_validation`
- `section_package_artifact_missing:risk_score_validation:risk_score_validation_only`

## Package Behavior

When all required sections and the optional risk score validation prerequisite pass, `create_full_integrated_report_package` includes the risk score result as an additional section artifact and writes:

- `sections/risk_score.md`
- copied risk score tables
- copied risk score plot artifacts
- copied task-run logs
- section manifest row for `risk_score_validation`

The package remains a statistical research package and continues to carry limitations that forbid clinical diagnosis, prognosis, treatment recommendation, and validated risk score interpretation.

## Boundaries

- No automatic risk score inclusion
- No clinical conclusion
- No prognosis label
- No treatment recommendation
- No risk group / cutoff generation
- No clinical validation claim
- No imported/testing/exploratory/preflight result upgrade
- No change to DOCX/PDF renderer policy

## Verification

- `python3 -m py_compile app/bioinformatics/reports/integrated.py`
- `python3 -m pytest -q tests/bioinformatics/test_integrated_report_package.py tests/bioinformatics/test_risk_score_report_ready_gate.py`
