# B54 DEG Data Quality and Repair Guidance Gate

## Audit

DEG-ready and parameter gates verified contract metadata, but matrix content quality was not exposed as a formal pre-execution gate. Duplicate feature/sample IDs, non-numeric values, missing values, negative counts, zero-variance rows, low-count rows, extreme outliers, and mixed identifier patterns could be hard to distinguish from downstream execution failures.

## Implementation

- Added `biomedpilot.deg_data_quality_gate.v1`.
- The gate scans the standardized matrix asset read-only.
- It blocks duplicated sample IDs, duplicated gene IDs without an aggregation policy, missing values, non-numeric values, missing matrix assets, and negative counts for count-model DEG.
- It warns on all-zero features, low-count features, zero-variance features, extreme outliers, negative display values, and mixed feature identifier patterns.
- It reports repair guidance but sets `auto_repaired=false`; formal input must be repaired upstream and rebuilt.
- Analysis Center now shows a `DEG data quality / repair guidance` row and formal DEG actions include the gate in disabled reasons.

## Boundaries

- No in-place matrix repair was added.
- No formal execution or report-ready behavior was added.
- Data quality warnings do not become clinical interpretation.

## Stage Result

B54 makes matrix content quality explicit and auditable before formal DEG execution.
