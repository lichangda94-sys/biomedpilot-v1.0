# B20 Multivariate Cox Contract and Gated Execution

Date: 2026-05-22

Scope: ReleaseBuild candidate branch. This stage promotes Cox multivariate from B14 design audit into a gated controlled MVP while preserving the existing boundaries: no risk score, no nomogram, no clinical prognosis conclusion, no treatment recommendation, no survival report-ready package and no real KM/Cox plot rendering.

## Implementation Summary

- Added `app/bioinformatics/survival_clinical/cox_multivariate_parameter_gate.py`.
- Added `app/bioinformatics/survival_clinical/cox_multivariate_confirmation.py`.
- Added `app/bioinformatics/survival_clinical/cox_multivariate_result_schema.py`.
- Added `app/bioinformatics/survival_clinical/cox_multivariate_executor.py`.
- Updated Analysis Center state and action rules so Cox multivariate is now a gated action, not a permanently disabled B14 design-only row.
- Updated capability map status to `b20_gated_execution_contract`.

## Gates

B20 multivariate Cox requires:

- B12 survival/clinical input package.
- Outcome/time/event gate.
- Event coding gate.
- Selected covariates.
- At least two covariates.
- Minimum sample count.
- Minimum event count.
- Minimum events per variable.
- Variable type validation.
- Missingness policy.
- Collinearity check.
- Model formula manifest.
- Dependency snapshot passed.
- User parameter confirmation.

## Result Schema

The multivariate Cox result table is separate from Cox univariate and requires:

- `covariate`
- `covariate_label`
- `covariate_type`
- `hazard_ratio`
- `ci_lower`
- `ci_upper`
- `p_value`
- `z_statistic`
- `sample_count`
- `event_count`
- `non_missing_count`
- `missing_count`
- `adjusted_for`
- `method`
- `warnings`

The result index task type is `cox_multivariate`, not `cox_univariate`.

## Runtime Boundary

Execution is allowed only when all B20 gates pass. Blocked runs write a task-run log but do not write a result index entry. Passing runs register `result_semantics=formal_computed_result` with:

- `plot_artifacts=[]`
- `report_artifacts=[]`
- `report_ready_eligible=False`

The controlled MVP uses an internal Cox partial-likelihood implementation with Breslow ties and small diagonal numerical stabilization for singularity resistance. It is statistical output only and does not produce clinical advice.

## UI Behavior

Analysis Center now displays:

- `B20 Cox multivariate parameters`
- `B20 Cox multivariate user confirmation`
- `Run multivariate Cox`
- `Multivariate Cox gated execution`

The button remains disabled when input, parameter, confirmation or dependency gates are blocked. Risk score and survival report-ready remain disabled.

## Tests

Added:

- `tests/bioinformatics/test_cox_multivariate_parameter_gate.py`
- `tests/bioinformatics/test_cox_multivariate_execution.py`
- `tests/bioinformatics/test_cox_multivariate_result_schema.py`

Updated:

- `tests/bioinformatics/test_analysis_ui_action_rules.py`
- `tests/bioinformatics/test_analysis_capability_map.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

Covered cases:

- Cox univariate remains intact.
- Low event count blocks.
- Too many variables for events blocks.
- High missingness blocks.
- Collinearity is recorded and blocks high-correlation designs.
- Missing dependency blocks.
- Missing confirmation blocks without result index registration.
- Passing gated run registers formal `cox_multivariate` result.
- No risk score, clinical risk group, treatment recommendation, plot artifact, report artifact or report-ready package is generated.

## Next Stage

Recommended next stage: B21 Risk Score Design Audit Only. B21 should remain design/audit only and must not execute risk score, nomogram, prognosis grouping or clinical recommendation logic.
