# B73 Multi-factor DEG Result Schema Contract

## Audit

Multi-factor DEG readiness existed, but formal result schema validation did not require formula, contrast, covariates, batch variables, rank, degrees of freedom, contrast estimability, or backend method provenance.

## Implementation

- Added `biomedpilot.multifactor_deg_result_schema_gate.v1`.
- Added validation for:
  - `design_formula`
  - `contrast`
  - `covariates`
  - `batch_variables`
  - `design_rank`
  - `residual_degrees_of_freedom`
  - `contrast_estimability`
  - `backend_method`
- Added bundle and result index validators.

## Boundary

B73 does not execute multi-factor DEG. It only defines and validates result schema contracts.
