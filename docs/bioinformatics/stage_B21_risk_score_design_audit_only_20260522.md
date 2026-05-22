# B21 Risk Score Design Audit Only

Date: 2026-05-22

Scope: ReleaseBuild candidate branch. This stage adds a risk score / nomogram / clinical risk grouping design audit only. It does not execute a risk score model and does not create formal risk-score results.

## Implementation Summary

- Added `app/bioinformatics/survival_clinical/risk_score_design.py`.
- Added design audit schema: `biomedpilot.risk_score_design_audit.v1`.
- Updated Analysis Center survival/clinical state to expose `risk_score_design`.
- Updated survival/clinical UI rows so `Risk score / nomogram` shows B21 design-audit blockers and warnings.
- Updated action matrix so `Generate risk score` remains disabled but explains the B21 prerequisite audit.

## Audited Prerequisites

B21 records and checks:

- training set / validation set plan
- variable source
- model formula
- coefficient source and provenance
- cutoff strategy
- overfitting protection
- cross-validation or external validation
- provenance
- interpretation boundary

## Hard Boundaries

- `formal_execution_enabled=False`
- `writes_result_index=False`
- `result_semantics=design_audit_only`
- `report_ready_eligible=False`
- no risk score result
- no high-risk / low-risk grouping
- no nomogram
- no clinical prognosis conclusion
- no treatment recommendation
- no survival report-ready package

## UI Behavior

Analysis Center continues to show risk score / nomogram as disabled/design-audit. The action matrix has no executable risk score button. It only explains which design prerequisites are missing or reviewable.

## Tests

Added:

- `tests/bioinformatics/test_risk_score_design_audit.py`

Updated:

- `tests/bioinformatics/test_analysis_ui_state.py`
- `tests/bioinformatics/test_analysis_ui_action_rules.py`

Covered cases:

- complete design spec becomes `design_audit_ready` but remains non-executable
- missing training/validation, formula, coefficient source, cutoff, overfitting protection and validation plan block the audit
- unknown variables and wrong source result type are blocked
- audit has no result-index side effect
- UI action remains disabled/design-audit only

## Next Stage

Recommended next stage: B22 Real KM/Cox Plot Artifact Renderer. B22 should read only formal KM/Cox result sources, generate real plot artifact files with renderer dependency provenance and must not change result semantics or create survival report-ready output.
