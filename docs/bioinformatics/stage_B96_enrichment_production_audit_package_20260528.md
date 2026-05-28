# B96 Enrichment Production Audit Package

## Scope

B96 adds a production audit package for formal controlled ORA / preranked GSEA results. It packages provenance and validation artifacts only. It does not create report-ready output, does not enable full GSEA modes, and does not generate biological or clinical conclusions.

## Gap Audit

Before B96, enrichment had:

- B93 resource lock and library policy;
- B94 background universe and identifier compatibility gates;
- B95 statistical policy and result schema gate;
- section report package gate from B86.

Missing production hardening:

- a standalone audit package for formal enrichment results;
- explicit package layout with tables, plots, manifests, logs and limitations;
- copied result table / plot / log artifacts with checksums;
- result schema gate snapshot inside package;
- guard that imported/testing/exploratory/preflight results cannot enter the package.

## Implementation

Added `app/bioinformatics/enrichment_audit_package.py`.

New schema:

- `biomedpilot.enrichment_production_audit_package.v1`

New function:

- `create_enrichment_production_audit_package(project_root, result_id=...)`

The package is created under:

```text
audit_package/enrichment/<result_id>/<timestamp>/
```

## Package Layout

Created package layout:

```text
enrichment_audit_package_manifest.json
tables/
plots/
manifests/
logs/
README_limitations.md
```

Included manifests:

- `manifests/resource_lock.json`
- `manifests/background_universe.json`
- `manifests/identifier_compatibility.json`
- `manifests/statistical_policy.json`
- `manifests/parameter_confirmation.json`
- `manifests/parameters_manifest.json`
- `manifests/dependency_snapshot.json`
- `manifests/result_schema_gate.json`
- `manifests/result_index_snapshot.json`
- `manifests/enrichment_result_entry.json`
- `manifests/plot_artifacts.json`
- `manifests/checksums.json`

## Gate Rules

The audit package requires:

- result exists;
- `result_semantics=formal_computed_result`;
- `task_type` is `ora` or `gsea_preranked`;
- B95 `validate_enrichment_result_schema_gate(...)` passes.

The package blocks:

- missing formal result;
- imported/testing/exploratory/preflight result;
- missing B95 statistical policy;
- missing B94 input contract snapshots;
- missing B93 resource lock;
- invalid result table schema;
- failed dependency snapshot;
- result with blockers.

## Artifact Handling

B96 copies:

- result output table artifacts into `tables/`;
- formal enrichment plot image/table artifacts into `plots/`;
- run log artifacts into `logs/`;
- provenance and validation snapshots into `manifests/`.

It writes SHA256 checksums for copied tables, plots, logs and manifests.

## Boundaries Preserved

The package manifest records:

- `report_ready_eligible_changed=False`
- `section_report_created=False`
- `full_integrated_report_enabled=False`
- `clinical_interpretation_enabled=False`

It does not mutate the result index and does not set `report_ready_eligible=True`.

Limitations include:

- statistical research enrichment audit package only;
- no pathway biology conclusion;
- no clinical diagnosis, prognosis or treatment recommendation;
- audit package is not report-ready;
- imported/testing/exploratory/preflight results are excluded.

## Tests

Added `tests/bioinformatics/test_enrichment_audit_package.py` covering:

- imported result blocked;
- schema-gate failure blocked;
- formal GSEA package copies tables, plots, logs and manifests;
- checksums include copied artifacts and manifests;
- result index `report_ready_eligible` remains false.

## Final Conclusion

B96 is complete as an additive enrichment production audit package. The next safe stage is B97 Enrichment Cross-Library / Cross-Project Acceptance.
