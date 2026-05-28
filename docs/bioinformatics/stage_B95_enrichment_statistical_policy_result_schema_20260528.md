# B95 Enrichment Statistical Policy and Result Schema Hardening

## Scope

B95 hardens controlled ORA / preranked GSEA statistical policy and result schema validation. It builds on B93 resource lock and B94 input contract.

This stage does not add new enrichment algorithms, does not enable full GSEA modes, does not generate biological interpretation, and does not change report-ready boundaries.

## Gap Audit

Before B95, enrichment result review could read formal ORA/GSEA tables, but the production-readiness contract lacked:

- a reusable statistical policy snapshot;
- explicit multiple-testing policy;
- result table probability and numeric validation;
- result index v2 completeness checks specialized for enrichment;
- required parameter snapshots tying results back to resource lock, background universe and identifier compatibility.

## Implementation

Added `app/bioinformatics/enrichment_result_schema.py`.

New schema payloads:

- `biomedpilot.enrichment_statistical_policy.v1`
- `biomedpilot.enrichment_result_schema_gate.v1`

New functions:

- `build_enrichment_statistical_policy(...)`
- `validate_enrichment_result_schema_gate(...)`

Updated:

- `app/bioinformatics/enrichment_execution_gate.py`
- `app/bioinformatics/enrichment_r_adapter.py`

The enrichment parameter manifest now includes `statistical_policy`.

## Statistical Policy

Default policy:

- p-value cutoff: `0.05`
- FDR cutoff: `0.25`
- min gene-set size: `1`
- max gene-set size: `500`
- multiple testing: Benjamini-Hochberg FDR
- q-value: optional but validated when present

Blockers:

- `unsupported_enrichment_analysis_type:<type>`
- `unsupported_multiple_testing_method:<method>`
- `invalid_enrichment_p_value_cutoff`
- `invalid_enrichment_fdr_cutoff`
- `invalid_min_gene_set_size`
- `invalid_max_gene_set_size`

## Result Schema Gate

`validate_enrichment_result_schema_gate(...)` requires:

- `result_semantics=formal_computed_result`
- `task_type` in `ora` / `gsea_preranked`
- result index fields:
  - `result_id`
  - `task_run_id`
  - `input_package_id`
  - `parameters_manifest`
  - `engine_name`
  - `engine_version`
  - `dependency_snapshot`
  - `output_artifacts`
  - `validation_status`
- parameter snapshots:
  - `statistical_policy`
  - `input_contract_gate`
  - `background_universe`
  - `identifier_compatibility_gate`
  - `resource_lock`

ORA table required columns:

- `ID`
- `Description`
- `GeneRatio`
- `BgRatio`
- `pvalue`
- `p.adjust`
- `qvalue`
- `geneID`
- `Count`

GSEA table required columns:

- `pathway`
- `ES`
- `NES`
- `pval`
- `padj`
- `leadingEdge`
- `size`

## Table Validation

The gate validates:

- p-values / adjusted p-values are numeric and within `[0, 1]`;
- optional q-values are numeric and within `[0, 1]` when present;
- ORA `Count` is a non-negative integer;
- GSEA `ES` and `NES` are numeric;
- GSEA `size` is a non-negative integer;
- result table is non-empty.

## Blockers

Key new blockers:

- `enrichment_statistical_policy_missing`
- `enrichment_statistical_policy_not_passed`
- `enrichment_parameters_missing:<field>`
- `enrichment_result_not_formal:<semantics>`
- `unsupported_enrichment_result_task_type:<task_type>`
- `enrichment_dependency_snapshot_not_passed`
- `enrichment_result_validation_not_passed`
- `enrichment_result_has_blockers`
- `enrichment_result_table_missing_column:<column>`
- `enrichment_result_invalid_probability:<field>:row_<n>`
- `ora_result_invalid_count:row_<n>`
- `gsea_result_invalid_numeric:<field>:row_<n>`
- `gsea_result_invalid_size:row_<n>`

## Tests

Added `tests/bioinformatics/test_enrichment_result_schema_gate.py` covering:

- invalid statistical policy thresholds;
- complete ORA result schema pass;
- complete GSEA result schema pass;
- missing statistical policy and invalid probabilities;
- imported/non-formal result blocking;
- parameter manifest embedding statistical policy.

Focused regression:

- B83 adapter tests still pass.
- B84 execution gate tests still pass.

## Boundaries Preserved

- No new ORA/GSEA execution mode.
- No automatic biological conclusion.
- No clinical interpretation.
- No report-ready bypass.
- No imported/testing/exploratory/preflight result promotion.

## Final Conclusion

B95 is complete as an additive statistical policy and result schema hardening stage. The next safe stage is B96 Enrichment Production Audit Package.
