# B84 Enrichment Execution Confirmation Gate

## Scope

B84 connects the enrichment resource gate, external R backend capability gate, parameter manifest, and user confirmation contract. It is a gate-hardening stage, not a UI activation stage.

## Implemented

Added `app/bioinformatics/enrichment_execution_gate.py`:

- `build_enrichment_parameter_manifest(...)`
- `build_enrichment_execution_gate(...)`
- `save_enrichment_parameter_confirmation(...)`
- `load_enrichment_parameter_confirmation(...)`
- `validate_enrichment_parameter_confirmation(...)`

The parameter manifest records:

- analysis type;
- source DEG result id and source result semantics;
- selected resource id and resource gate snapshot;
- backend gate and dependency snapshot;
- engine candidate;
- required backend capability;
- p-value/FDR thresholds;
- gene-set size limits;
- preranked GSEA ranking metric;
- manifest hash;
- blockers/warnings.

The confirmation gate requires:

- matching analysis type;
- matching source result;
- matching resource;
- matching engine candidate;
- matching manifest hash;
- explicit acknowledgement that output is statistical research only, no auto-install/download occurs, and plot/report-ready remain separate gates.

## Boundaries

- `formal_ui_button_enabled` remains false.
- Non-formal source results are blocked.
- ReactomePA/msigdbr-dependent capabilities remain blocked until their backend/resource gates pass.
- No automatic install or network download.
- No plot/report-ready activation.

## Validation

Focused tests cover:

- passed resource/backend gates still requiring user confirmation;
- saved confirmation passing;
- stale confirmation blocking;
- imported/non-formal source blocking;
- Reactome capability staying blocked while ReactomePA is missing.
