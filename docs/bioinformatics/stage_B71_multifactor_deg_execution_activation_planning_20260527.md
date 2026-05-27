# B71 Multi-Factor DEG Execution Activation Planning

## Audit

B62 added a controlled multi-factor readiness gate. It still does not execute limma, DESeq2, or edgeR multi-factor models. This is intentional because execution activation requires real runtime fixtures, result schema expansion, user confirmation, and report/audit coverage.

## Activation Preconditions

Before formal multi-factor DEG execution can be enabled, all of the following must pass:

1. Resolver and DEG-ready package pass.
2. B52 input adaptation passes.
3. B53 design QA passes with a multi-factor design manifest.
4. B54 data quality passes.
5. B55 method recommendation does not block the selected backend.
6. B62 multi-factor controlled gate passes.
7. R backend dependency detection passes for the selected method.
8. User confirmation records design formula, contrast, covariates, batch variables, method, thresholds, value type policy, dependency versions, and output plan.
9. Result index v2 schema includes multi-factor design and contrast provenance.
10. Real fixture execution passes for at least one limma, one DESeq2, and one edgeR controlled multi-factor fixture.
11. Plot/report/audit packages preserve multi-factor provenance and do not produce clinical interpretation.

## Required Future Blockers

- `multifactor_runtime_not_activated`
- `multifactor_result_schema_not_activated`
- `multifactor_user_confirmation_missing`
- `multifactor_real_fixture_missing`
- `multifactor_report_audit_not_ready`

## UI Boundary

The UI may show readiness preview and disabled reasons. It must not expose a formal multi-factor run button until the future activation stage clears all blockers.

## Recommendation

Next multi-factor work should be a dedicated activation phase with real R fixtures. Do not merge it into DEG plot/report polishing.
