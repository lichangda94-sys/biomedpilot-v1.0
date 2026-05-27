# B78 Multi-factor DEG UI Execution Gate

## Audit

Analysis Center already showed two-group DEG gates, but multi-factor DEG readiness was not surfaced as a coherent UI state. Users could not see the combined design QA, contrast, method, dependency, confirmation, and result schema disabled reasons.

## Implementation

- Added `biomedpilot.multifactor_deg_ui_gate_state.v1`.
- Analysis Center now exposes multi-factor gate rows for:
  - resolver / DEG-ready package
  - design QA
  - contrast
  - method and value type policy
  - external R dependency
  - user confirmation
  - result schema
- Added a `multifactor_deg` action row. It is enabled only when the multi-factor gate state is fully passed.
- The existing Analysis Center gate table now includes both two-group and multi-factor DEG gate rows.

## Boundary

B78 adds UI execution control state only. It does not add a new GUI handler that runs arbitrary user-project multi-factor DEG, does not generate plots or reports, and does not add clinical interpretation.
