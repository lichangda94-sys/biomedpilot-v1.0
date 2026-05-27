# B61 Multi-Factor DEG Production QA Planning

## Scope

B61 defines the production QA contract for future multi-factor DEG. It does not enable formal multi-factor execution.

## Current State Audit

- Two-group controlled DEG has resolver, DEG-ready, dependency, parameter confirmation, result schema, input adaptation, design QA, data quality, method recommendation, runtime validation, audit package, and cross-project acceptance gates.
- Multi-factor DEG exists only as preflight/design logic in the Analysis Center and must remain disabled until a dedicated contract passes.

## Required Multi-Factor Gate Inputs

- standardized DEG recompute input package
- DEG-ready package
- design formula
- contrast manifest
- covariate manifest
- batch manifest
- method family: `limma`, `DESeq2`, or `edgeR`
- dependency snapshot
- result schema target
- user confirmation manifest

## Required Blockers

- missing design formula
- missing contrast manifest
- unknown or non-estimable contrast
- rank-deficient design matrix
- group/covariate or group/batch full confounding
- covariate with a single usable value
- insufficient residual degrees of freedom
- unsupported value type for selected backend
- missing R/Bioconductor backend package
- result schema not prepared for multi-factor DEG

## UI Boundary

The Analysis UI may show a multi-factor DEG readiness preview and disabled reasons. It must not expose a formal run button until B62/B63+ result schema and runtime evidence pass. Existing two-group formal DEG controls must remain separate.

## Result Boundary

Multi-factor outputs must not reuse two-group result semantics unless the result index entry explicitly records multi-factor design, contrast, covariates, batch variables, engine/version, dependency snapshot, parameter confirmation, warnings, blockers, and validation status.

## Recommendation

Proceed to B62 only as a controlled gate/MVP readiness layer. Do not claim full multi-factor DEG production support until real limma/DESeq2/edgeR fixtures and report/audit packages pass.
