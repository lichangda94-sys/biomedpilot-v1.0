# B16.6 Legacy Asset Pipeline UI Operations

Date: 2026-05-22

## Scope

B16.6 connects the B16 legacy absorption gates to controlled Analysis Center operations:

- Build legacy standardized asset candidates.
- Materialize legacy candidates into isolated repository files.
- Merge materialized assets into the standardized repository manifest.
- Confirm legacy asset selection as repository default selection.

These operations are standardization-layer actions only.

## Boundaries

The UI operations do not:

- Run formal DEG, ORA, GSEA, KM, Cox, survival, or clinical analysis.
- Write `analysis_input_repository`.
- Write `result_index`.
- Create plot artifacts.
- Create report-ready packages.
- Upgrade legacy/preflight/testing/imported artifacts to `formal_computed_result`.

## UI Behavior

The Analysis Center now exposes one button per B16 gate. Each button is enabled only when the previous gate artifact is present:

- Adapter manifests enable candidate generation.
- Candidate bundle enables materialization.
- Materialization manifest enables repository merge.
- Repository merge manifest enables legacy asset selection confirmation.

The action matrix mirrors these operations with `controlled_standardization_artifact_write_no_formal_execution`.

## Validation

Tests cover:

- Analysis Center operation states and disabled reasons.
- Action matrix behavior.
- UI button enablement.
- End-to-end legacy UI operation flow.
- No `analysis_input_repository` or `result_index` side effects.
