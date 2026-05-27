# B55 DEG Method Recommendation / Explanation Layer

## Audit

The UI could show whether gates passed, but it did not explain which DEG method families were appropriate for the current value type, design, quality status, and dependency state. This left method choice opaque and risked implying that every detected backend was equally appropriate.

## Implementation

- Added `biomedpilot.deg_method_recommendation_gate.v1`.
- The gate evaluates DESeq2, edgeR, limma, and Python Welch/Mann-Whitney options.
- Raw count inputs recommend DESeq2 and make edgeR/limma/Python available when dependencies and upstream gates pass.
- TPM/FPKM/log/display values disable count-model methods and recommend limma when available.
- Small sample size emits an explicit limitation warning.
- Upstream blockers from input adaptation, design QA, and data quality propagate into disabled reasons.
- Analysis Center now displays the method recommendation row and formal DEG actions include this gate in their conjunction.

## Boundaries

- Recommendations do not execute anything.
- Recommendations do not replace user parameter confirmation.
- No clinical interpretation, GSEA, survival, plotting, or report-ready behavior was added.

## Stage Result

B55 adds transparent, auditable method guidance while preserving all existing formal execution gates.
