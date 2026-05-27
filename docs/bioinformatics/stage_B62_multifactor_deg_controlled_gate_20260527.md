# B62 Multi-Factor DEG Controlled Gate

## Audit

B61 defined the multi-factor DEG QA requirements. The missing implementation was a contract object that can be evaluated without enabling formal execution.

## Implementation

- Added `biomedpilot.multifactor_deg_controlled_gate.v1`.
- The gate validates design formula, contrast manifest, method family, value type compatibility, design QA, dependency status, and R backend package availability.
- It blocks missing formula/contrast, unsupported method, display values for DESeq2/edgeR, design confounding/rank/df blockers, dependency failures, and missing R backend packages.
- `formal_execution_enabled` is always `false`.

## Boundary

B62 does not run limma/DESeq2/edgeR multi-factor models and does not write formal results. It is a readiness gate only.
