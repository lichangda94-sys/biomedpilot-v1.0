# B53 DEG Batch / Design QA Gate

## Audit

Formal DEG had parameter confirmation and DEG-ready gates, but no dedicated design QA snapshot for batch/covariate manifests, contrast estimability, rank deficiency, confounding, group size, or residual freedom degree.

## Implementation

- Added `biomedpilot.deg_design_quality_gate.v1`.
- The gate produces a unified design readiness snapshot for Python, limma, DESeq2, and edgeR candidates.
- It blocks fully confounded group/covariate or batch assignments, single-value covariates, rank-deficient design matrices, non-estimable contrasts, group size failures, and insufficient residual degrees of freedom.
- Simple two-group designs without batch metadata can pass, but emit `batch_covariate_manifest_missing` as a review warning.
- Analysis Center now shows a `DEG batch/design QA` row and formal DEG actions include this gate in their disabled-reason conjunction.

## Boundaries

- No execution engine was added or activated.
- No automatic design repair is performed.
- Covariate and batch guidance is advisory; repaired inputs must be regenerated through the standardized input pipeline.

## Stage Result

B53 hardens formal DEG readiness by making design quality explicit and auditable before execution.
