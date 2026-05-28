# B94 Enrichment Background Universe and Identifier Compatibility Gate

## Scope

B94 adds a formal enrichment input contract for background universe, source gene derivation, ranking metric provenance, and identifier compatibility. It builds on B93 resource lock and library policy.

This stage does not add new ORA/GSEA algorithms, does not enable full GSEA modes, does not auto-map identifiers, does not generate interpretation, and does not change plot/report-ready boundaries.

## Gap Audit

Before B94, enrichment execution gates validated:

- source result id and semantics;
- selected gene-set resource;
- R backend capability;
- parameter confirmation.

Missing hardening:

- ORA background universe was not a first-class manifest;
- selected ORA genes were not derived through an audited policy;
- preranked GSEA ranking metric provenance was not separately checked;
- resource gene ID type and source DEG gene ID type were not compared through a dedicated gate;
- parameter manifest did not carry a background/identifier input contract snapshot.

## Implementation

Added `app/bioinformatics/enrichment_input_contract.py`.

New schema payloads:

- `biomedpilot.enrichment_background_universe.v1`
- `biomedpilot.enrichment_identifier_compatibility_gate.v1`
- `biomedpilot.enrichment_source_derivation_manifest.v1`
- `biomedpilot.enrichment_input_contract_gate.v1`

New functions:

- `build_enrichment_input_contract_gate(...)`
- `build_enrichment_background_universe(...)`
- `build_enrichment_source_derivation_manifest(...)`
- `build_enrichment_identifier_compatibility_gate(...)`

Updated `app/bioinformatics/enrichment_execution_gate.py`:

- parameter manifest now embeds:
  - `input_contract_gate`
  - `background_universe`
  - `identifier_compatibility_gate`
  - `source_derivation_manifest`
  - `resource_lock`
- execution blockers now include input contract blockers.

## Background Universe

B94 supports one explicit background strategy:

```text
formal_deg_result_table_all_features
```

This means all genes/features from the formal DEG result table are used as the ORA universe. It is explicit and provenance-bound to the formal source result. Unsupported strategies block.

Blockers:

- `unsupported_background_strategy:<strategy>`
- `background_universe_empty`
- `background_gene_id_type_unknown`

## Source Derivation

ORA selected genes use:

```text
deg_significant_genes_by_abs_log2fc_and_fdr
```

Required source columns:

- `gene_symbol` or `feature_id`
- `log2_fold_change`
- `adjusted_p_value`

GSEA preranked input uses:

```text
deg_result_table_preranked_metric
```

Supported ranking metrics:

- `statistic`
- `log2_fold_change`
- `p_value`
- `adjusted_p_value`

Blockers:

- `ora_selected_gene_set_empty`
- `unsupported_gsea_ranking_metric:<metric>`
- `gsea_ranking_metric_empty`

## Identifier Compatibility

The new gate compares:

- source DEG `gene_id_type`;
- selected resource lock `gene_id_type`;
- required enrichment `gene_id_type`.

No automatic mapping is performed. Mapping remains blocked until a later audited mapping manifest exists.

Blockers:

- `source_gene_id_type_unknown`
- `resource_gene_id_type_unknown`
- `source_gene_id_type_mismatch:<source>!=<required>`
- `source_resource_gene_id_type_mismatch:<source>!=<resource>`

Mapping policy:

```text
no_automatic_identifier_mapping_without_audited_mapping_manifest
```

## Source Result Rules

B94 source contract requires a formal DEG result:

- `result_semantics=formal_computed_result`
- `task_type=deg`
- `output_artifacts` includes `deg_result_table`

Blockers:

- `enrichment_source_result_id_missing`
- `enrichment_source_result_not_found`
- `enrichment_source_result_not_formal:<semantics>`
- `enrichment_source_result_not_deg:<task_type>`
- `enrichment_source_deg_table_missing`

## Tests

Added `tests/bioinformatics/test_enrichment_input_contract.py` covering:

- formal DEG ORA source passes;
- preranked GSEA metric passes;
- imported/preflight source blocks;
- source/resource identifier mismatch blocks;
- unsupported background strategy blocks;
- empty ORA selected genes blocks;
- unsupported GSEA ranking metric blocks;
- unknown identifier type blocks without mapping.

Updated `tests/bioinformatics/test_enrichment_execution_gate.py` so positive parameter/confirmation cases register a formal DEG source result before building enrichment gates.

## Boundaries Preserved

- No new formal execution mode beyond controlled ORA and controlled preranked GSEA.
- No automatic identifier mapping.
- No arbitrary visible-table background inference.
- No imported/testing/exploratory/preflight result promotion.
- No clinical or biological conclusion output.
- No report-ready bypass.

## Final Conclusion

B94 is complete as an additive input-contract hardening stage. The next safe stage is B95 Enrichment Statistical Policy and Result Schema Hardening.
