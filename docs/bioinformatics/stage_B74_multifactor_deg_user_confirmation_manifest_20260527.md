# B74 Multi-factor DEG User Confirmation Manifest

## Audit

Multi-factor DEG had readiness and result schema gates, but no user confirmation manifest equivalent to the two-group formal DEG confirmation flow.

## Implementation

- Added `biomedpilot.multifactor_deg_parameter_confirmation.v1`.
- The confirmation records:
  - design formula
  - contrast
  - covariates
  - batch variables
  - backend method
  - value type compatibility policy
  - dependency versions
  - output paths and task-run id
- The confirmation can be saved, loaded, and validated.

## Boundary

B74 does not execute multi-factor DEG. It records explicit user confirmation only.
