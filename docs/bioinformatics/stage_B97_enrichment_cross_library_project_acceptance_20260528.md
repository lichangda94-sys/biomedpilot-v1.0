# B97 Enrichment Cross-Library / Cross-Project Acceptance

## Scope

B97 adds a controlled acceptance gate for enrichment production hardening across supported resource libraries and failure scenarios. It validates the B93-B96 contracts using isolated temporary fixture projects.

This stage does not run real R ORA/GSEA execution, does not add algorithms, does not enable full GSEA modes, and does not generate biological or clinical conclusions.

## Gap Audit

Before B97, the enrichment layer had:

- B93 resource lock and library policy;
- B94 background universe and identifier compatibility gates;
- B95 statistical policy and result schema gate;
- B96 production audit package.

Missing acceptance coverage:

- cross-library positive fixtures for GO / KEGG / Reactome / MSigDB / custom GMT;
- negative fixtures for ID mismatch, missing background, missing backend and non-formal source;
- result schema positive fixtures for ORA and GSEA;
- a single payload usable by B99 closure audit.

## Implementation

Added `app/bioinformatics/enrichment_acceptance.py`.

New schema:

- `biomedpilot.enrichment_cross_library_acceptance.v1`

New function:

- `build_enrichment_cross_library_acceptance_gate(...)`

The gate runs all fixtures in an isolated temporary directory and returns only the acceptance payload. It does not write fixture files into the active project.

## Acceptance Matrix

Positive scenarios:

| Scenario | Purpose |
| --- | --- |
| `go_bp_ora_positive` | GO BP symbol ORA resource/input contract |
| `kegg_entrez_ora_positive` | KEGG Entrez ORA resource/input contract |
| `reactome_ora_positive` | Reactome ORA resource/input contract with detector capability present |
| `msigdb_hallmark_gsea_positive` | user-imported MSigDB Hallmark preranked GSEA contract |
| `custom_gmt_ora_positive` | custom GMT ORA contract |
| `ora_result_schema_positive` | ORA result schema gate |
| `gsea_result_schema_positive` | GSEA result schema gate |

Negative scenarios:

| Scenario | Expected blocker |
| --- | --- |
| `id_space_mismatch_negative` | `source_resource_gene_id_type_mismatch:symbol!=entrez` |
| `missing_background_negative` | `background_universe_empty` |
| `missing_backend_negative` | `external_enrichment_backend_detection_missing` |
| `preflight_source_negative` | `enrichment_source_result_not_formal:preflight_only` |
| `imported_source_negative` | `enrichment_source_result_not_formal:imported_external_result` |

## Payload

The acceptance gate returns:

- `schema_version`
- `created_at`
- `status`
- `scenario_count`
- `passed_scenario_count`
- `scenario_rows`
- `acceptance_matrix`
- `semantic_boundary`
- `blockers`
- `warnings`

`status=passed` only when every positive scenario passes and every negative scenario blocks with the expected stable blocker.

## Boundaries Preserved

- No real ORA/GSEA execution is added by this stage.
- No network download is triggered.
- No R/Bioconductor package install is triggered.
- No imported/testing/exploratory/preflight source is promoted.
- No report-ready package is created.
- No biological or clinical interpretation is generated.

## Tests

Added `tests/bioinformatics/test_enrichment_cross_library_acceptance.py` covering:

- full scenario matrix passes;
- every negative scenario records the expected stable blocker;
- semantic boundary remains acceptance-only.

## Final Conclusion

B97 is complete as an acceptance-gate layer for B93-B96 enrichment hardening. The next safe stage is B98 Enrichment UI Production Preview.
