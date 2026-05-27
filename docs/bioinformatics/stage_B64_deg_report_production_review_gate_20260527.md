# B64 DEG Report Production Review Gate

## Audit

Formal DEG had report-ready and audit package paths, but no single production review gate that checked report-ready eligibility, audit package presence, plot production readiness, limitations, and provenance together.

## Implementation

- Added `biomedpilot.formal_deg_report_production_review_gate.v1`.
- The gate wraps the existing formal DEG report-ready gate.
- It requires a DEG production audit package manifest.
- It requires a passed plot production gate unless table-only mode is explicitly allowed.
- It keeps scope as `formal_deg_only` and disables full integrated report, GSEA, survival, and clinical conclusions.

## Boundary

B64 does not create a new report package and does not upgrade section-only DEG output into full integrated medical interpretation.
