# B93 Enrichment Resource Version Lock and Library Policy

## Scope

B93 hardens the B81 enrichment resource gate with an immutable resource lock and an explicit library policy matrix. It is a contract hardening stage only.

This stage does not run ORA/GSEA, does not enable full GSEA modes, does not download resources automatically, does not install R/Bioconductor packages, and does not add biological or clinical interpretation.

## Gap Audit

B81 already recorded resource metadata:

- resource id;
- collection type;
- species;
- gene id type;
- source name/url;
- license note;
- version;
- checksum;
- gene set count;
- local path.

The missing production-hardening layer was:

- a reusable immutable lock payload for downstream parameter/result/report gates;
- a library policy matrix for GO / KEGG / Reactome / MSigDB Hallmark / custom GMT;
- explicit acquisition policy and license policy per library;
- stable blockers for unknown version, missing checksum, missing license policy and unselected resource.

## Implementation

Updated `app/bioinformatics/enrichment_resources.py`.

New schema constants:

- `biomedpilot.enrichment_library_policy.v1`
- `biomedpilot.enrichment_resource_lock.v1`

New functions:

- `build_enrichment_library_policy(...)`
- `build_enrichment_resource_lock(...)`
- `write_enrichment_resource_lock_manifest(...)`

The library policy matrix now covers:

| Collection | Family | Supported modes | Acquisition policy |
| --- | --- | --- | --- |
| `GO_BP` | Gene Ontology | ORA, preranked GSEA | user-triggered download or existing cache |
| `GO_CC` | Gene Ontology | ORA, preranked GSEA | user-triggered download or existing cache |
| `GO_MF` | Gene Ontology | ORA, preranked GSEA | user-triggered download or existing cache |
| `KEGG` | KEGG | ORA, preranked GSEA | user-triggered download or existing cache |
| `Reactome` | Reactome | ORA, preranked GSEA | user-triggered download or existing cache |
| `Hallmark` | MSigDB | ORA, preranked GSEA | user-provided licensed GMT only |
| `Custom` | Custom GMT | ORA, preranked GSEA | user-provided GMT only |
| `Unknown` | Unknown | none | unsupported until metadata fixed |

## Resource Lock Fields

`build_enrichment_resource_lock(...)` returns:

- `schema_version`
- `created_at`
- `status`
- `lock_id`
- `analysis_type`
- `resource_id`
- `name`
- `collection_type`
- `library_family`
- `species`
- `gene_id_type`
- `source_type`
- `source_name`
- `source_url`
- `source_version`
- `license_note`
- `license_policy`
- `acquisition_policy`
- `checksum_algorithm`
- `checksum`
- `file_size`
- `gene_set_count`
- `local_path`
- `allowed_analysis_types`
- `backend_capability_requirements`
- `immutable_fields`
- `resource_gate`
- `library_policy`
- `semantic_boundary`
- `network_downloads`
- `auto_install`
- `blockers`
- `warnings`

## Blockers

B93 preserves existing B81 blockers and adds stable lock/policy blockers:

- `enrichment_resource_not_selected`
- `resource_version_missing`
- `resource_checksum_missing`
- `resource_license_note_missing`
- `resource_source_version_unknown`
- `resource_immutable_checksum_missing`
- `resource_license_policy_not_recorded`
- `resource_requires_user_import:<collection>`
- `library_not_allowed_for:<analysis_type>`
- `unsupported_enrichment_library:<collection>`
- `unsupported_enrichment_analysis_type:<analysis_type>`

## Manifest Write Boundary

`build_enrichment_resource_lock(...)` is read-only.

`write_enrichment_resource_lock_manifest(...)` writes only when explicitly called and stores the manifest under:

```text
manifests/enrichment/<analysis_type>_<resource_id>_resource_lock.json
```

Analysis Center state construction remains read-only.

## Tests

Added coverage in `tests/bioinformatics/test_enrichment_resource_gate.py`:

- library policy matrix has GO/Reactome/Hallmark capabilities and acquisition rules;
- immutable selected GO resource lock passes;
- missing version/license blocks lock readiness;
- Hallmark/MSigDB requires user import;
- explicit writer creates the manifest only when called;
- pure lock builder does not write files.

## Boundaries Preserved

- No automatic MSigDB download.
- No silent Reactome/GO/KEGG download during formal execution.
- No R package install action.
- No execution readiness implied by resource lock alone.
- No imported/testing/exploratory/preflight promotion.
- No clinical or biological conclusion generation.

## Final Conclusion

B93 is complete as an additive production-hardening contract. The next safe stage is B94 Enrichment Background Universe and Identifier Compatibility Gate.
