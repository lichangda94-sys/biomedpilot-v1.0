# B88 Enrichment UI Execution Control

## Scope

B88 wires the B81-B87 enrichment contracts into the Analysis Center state and action matrix. It does not bypass the gates or add new analysis algorithms.

## Implemented

Analysis Center state now exposes:

- `enrichment_gate_rows`;
- `developer_diagnostics.enrichment_gate_state`;
- ORA execution gate snapshot;
- preranked GSEA execution gate snapshot;
- result review status;
- plot artifact gate status;
- section report gate status;
- ReactomePA/msigdbr blocked capability policy.

Action matrix now includes:

- `enrichment_parameter_confirmation`;
- `controlled_ora`;
- `controlled_gsea_preranked`;
- `enrichment_result_review`;
- `enrichment_plot_artifact`;
- `enrichment_section_report`.

Each action uses explicit state and disabled reasons from the underlying B84-B87 contracts.

## Boundaries

- Full GSEA modes beyond controlled preranked GSEA remain disabled.
- ReactomePA/msigdbr paths remain blocked until external backend/resource gates pass.
- UI `can_run` does not imply formal execution readiness.
- Plot/report actions still require formal enrichment source semantics.
- Section report remains `formal_enrichment_only`; it is not a full integrated report.
- No clinical interpretation, diagnosis, prognosis, or treatment recommendation is enabled.

## Side-Effect Guard

Analysis Center state remains read-only. If a gene-set registry is not present, the UI returns a blocked enrichment snapshot instead of initializing or writing a registry file.

## Validation

Focused tests cover:

- controlled ORA/GSEA actions enabling only when execution gates pass;
- resource/backend/confirmation disabled reasons;
- Analysis Center enrichment gate rows;
- workflow page action/gate table rendering.
