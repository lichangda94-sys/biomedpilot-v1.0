# B100a ReleaseBuild Enrichment Scoped Convergence

## Scope

B100a receives the B92-B99 enrichment production-hardening intent into ReleaseBuild without copying the Bioinformatics source tree. It adapts the hardening layer to ReleaseBuild's existing ORA/GSEA architecture and result schemas.

This stage does not publish ReleaseBuild, does not replace desktop entrypoints, does not install R/Bioconductor packages, and does not enable clinical or biological conclusion generation.

## Pre-Implementation Audit

ReleaseBuild already had:

- controlled ORA execution and result review;
- controlled preranked GSEA execution and result review;
- real SVG ORA/GSEA plot artifacts;
- ORA/GSEA section report packages;
- full integrated report gates;
- external R enrichment backend detection in the local engine registry.

B100 preflight found that direct Bioinformatics B92-B99 copy was unsafe because ReleaseBuild uses different ORA/GSEA table schemas and UI action ids.

## Implemented Convergence

Added a ReleaseBuild-native enrichment production hardening layer:

- `build_enrichment_resource_lock(...)`
- `build_enrichment_background_identifier_gate(...)`
- `build_enrichment_statistical_policy(...)`
- `build_enrichment_production_result_schema_gate(...)`
- `build_enrichment_production_preview(...)`
- `create_enrichment_production_audit_package(...)`

The layer reuses existing ReleaseBuild ORA/GSEA gates:

- `build_ora_input_gate`
- `build_ora_gene_set_resource_gate`
- `build_ora_parameter_manifest`
- `validate_ora_result_index_entry`
- `validate_ora_result_table_row`
- `build_gsea_preranked_input_gate`
- `build_gsea_gene_set_resource_gate`
- `build_gsea_parameter_manifest`
- `validate_gsea_result_index_entry`
- `validate_gsea_result_table_row`

## Resource Lock

The resource lock checks:

- resource id;
- resource path;
- checksum;
- file size;
- source;
- species;
- gene ID type;
- term count;
- license note/warning.

`import_gmt_file(...)` now records `file_size` and `checksum` for imported GMT resources, matching the existing downloaded resource metadata behavior.

## Background / Identifier Gate

For ORA, the gate validates:

- selected gene count;
- background universe count;
- source DEG semantics;
- source/resource gene ID compatibility.

For preranked GSEA, the gate validates:

- ranked gene count;
- gene-set overlap;
- source/resource gene ID compatibility.

## Statistical Policy

The statistical policy requires:

- FDR policy in `BH`, `fdr_bh`, or `Benjamini-Hochberg`;
- valid p-value and FDR thresholds;
- ORA method in `hypergeometric` or `fisher_exact`;
- valid GSEA rank metric and permutation count.

The policy is explicitly statistical research only and does not create pathway activation, prognosis, diagnosis, or treatment conclusions.

## Result Schema / Audit Package

The production result schema gate accepts only `formal_computed_result` ORA/GSEA entries and validates the ReleaseBuild-native result table columns.

The production audit package writes:

- `enrichment_production_audit_package_manifest.json`
- `tables/`
- `manifests/result_index_snapshot.json`
- `manifests/parameters_manifest.json`
- `manifests/dependency_snapshot.json`
- `manifests/schema_gate_snapshot.json`
- `logs/`
- `README_limitations.md`

It does not set `report_ready_eligible=True`.

## UI Preview

Analysis Center now exposes `enrichment_production_gate_rows` and the `enrichment_production_preview` action.

The UI action is review-only:

- `button_behavior=enabled_review_only_no_package_write` when all preview gates pass;
- `blocked_enrichment_production_gate` with explicit disabled reasons when blocked;
- no package write during UI state construction;
- no report-ready upgrade.

## Dirty Worktree Boundary

B100a preserves the pre-existing uncommitted DEG input-adaptation work in:

- `app/bioinformatics/analysis_ui/state.py`
- `app/bioinformatics/deg_engine/__init__.py`
- `tests/bioinformatics/test_analysis_ui_state.py`
- `app/bioinformatics/deg_engine/input_adaptation.py`
- `tests/bioinformatics/test_deg_input_adaptation_gate.py`

The B100a commit must stage only scoped enrichment convergence hunks and avoid committing unrelated `project_storage` or release handoff files.

## Boundary

B100a does not:

- auto-install R/Bioconductor packages;
- download MSigDB automatically;
- enable phenotype-permutation GSEA;
- create clinical interpretation;
- bypass existing ORA/GSEA result/report gates;
- convert imported/testing/preflight outputs into formal enrichment results;
- claim public-release or clinical-grade readiness.

## Result

B100a completes scoped ReleaseBuild convergence for enrichment production-hardening preview and audit package primitives. The next stage should run full ReleaseBuild regression and decide whether to expose the audit package export in the UI as a separate explicit operation.
