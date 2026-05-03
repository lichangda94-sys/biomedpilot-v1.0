# TCGA Standard Assets Contract

## Purpose

This contract defines the standard TCGA assets that future BioMedPilot TCGA modules should produce. It is a lightweight planning contract, not a runtime implementation. It does not introduce a Nextflow runner, new external dependencies, or GUI changes.

The contract is designed to align TCGA with the existing BioMedPilot direction:

- adapter-first source access
- manifest-first workflow state
- standard assets under stable roles
- report/package layers consuming artifacts without knowing the original downloader
- tests that can run without real GDC, recount3, R, or network access

## Common Rules

All TCGA standard assets should be described by `tcga_prepare_manifest`.

Common required metadata for every asset:

- `contract_version`
- `asset_role`
- `source_db`: `TCGA_GDC`, `recount3`, or `derived`
- `tcga_project_id`
- `dataset_id`
- `modality`
- `path`
- `format`
- `created_at`
- `generator`
- `input_assets`
- `parameters`
- `warnings`
- `row_count`
- `column_count`
- `checksum` when available

Common identifier policy:

- `tcga_project_id` should use canonical IDs such as `TCGA-THCA`.
- Sample-level assets should include `sample_id` as the primary sample key.
- Case-level assets should include `case_id` when available.
- TCGA submitter barcode should be retained as `tcga_barcode`.
- Participant/patient barcode should be retained as `participant_barcode` when derivable.
- Feature-level matrices should include a stable feature identifier column before sample columns.

Common matrix orientation:

- Expression matrices should be feature rows and sample columns.
- Mutation, CNV, and methylation matrices may be feature rows and sample columns for analysis consistency.
- If a source script naturally emits sample rows and feature columns, the manifest must declare `orientation`.
- Report and downstream analysis code must not infer orientation from file name alone.

## Asset: tcga_expression_matrix

Role: `tcga_expression_matrix`

Recommended path:

```text
organized/tcga/expression/tcga_expression_matrix.tsv.gz
```

Format:

- `tsv` or `tsv.gz`

Required columns:

- `feature_id`
- `gene_id`
- `gene_symbol`
- one dynamic column per `sample_id`

Required manifest fields:

- `expression_unit`: examples include `TPM`, `logTPM`, `CPM`, `logCPM`, `raw_count`
- `normalization_method`
- `is_log_scale`
- `matrix_level`: `gene`, `transcript`, or `unknown`
- `sample_id_order`
- `feature_id_type`: examples include `Ensembl`, `Entrez`, `gene_symbol`
- `source_expression_object` when generated from RDS or another structured object

Recommended provenance fields:

- `recount_project`
- `recount_project_home`
- `organism`
- `annotation`
- `expression_type`
- `min_expression_threshold`
- `min_sample_fraction`
- `tumor_purity_method`
- `tumor_purity_threshold`
- `tissue_filter`
- `batch_correction_method`
- `batch_variable`
- `adjustment_variables`

Validation requirements:

- Matrix must not be empty.
- Sample columns must match `tcga_sample_metadata.sample_id`.
- Duplicated sample IDs must be resolved or reported.
- Log scale and unit must be explicit.

## Asset: tcga_clinical_table

Role: `tcga_clinical_table`

Recommended path:

```text
organized/tcga/clinical/tcga_clinical_table.tsv
```

Format:

- `tsv`

Required columns:

- `case_id`
- `participant_barcode`
- `tcga_project_id`
- `source_submitter_id`

Recommended columns:

- `sample_id`
- `tcga_barcode`
- `disease_type`
- `primary_site`
- `gender`
- `age_at_diagnosis`
- `vital_status`
- `days_to_death`
- `days_to_last_follow_up`
- `overall_survival_time`
- `overall_survival_event`
- `tumor_stage`
- `pathologic_stage`
- `tnm_t`
- `tnm_n`
- `tnm_m`
- `histological_type`

Required manifest fields:

- `clinical_source_type`: examples include `BCR Biotab`, `GDC clinical JSON`, `XML supplement`
- `survival_fields_available`
- `field_mapping_version`

Validation requirements:

- Preserve raw source field names in provenance or sidecar metadata.
- Do not silently invent survival fields when dates are missing.
- Survival-ready fields must document event coding.

## Asset: tcga_sample_metadata

Role: `tcga_sample_metadata`

Recommended path:

```text
organized/tcga/metadata/tcga_sample_metadata.tsv
```

Format:

- `tsv`

Required columns:

- `sample_id`
- `tcga_barcode`
- `participant_barcode`
- `case_id`
- `tcga_project_id`
- `sample_type`
- `sample_type_code`
- `tissue_type`
- `source_db`

Recommended columns:

- `aliquot_id`
- `file_id`
- `platform`
- `workflow_type`
- `batch_id`
- `center`
- `is_tumor`
- `is_normal`
- `purity`
- `purity_method`
- `matched_normal_sample_id`
- `included_in_expression`
- `included_in_mutation`
- `included_in_cnv`
- `included_in_methylation`

Required manifest fields:

- `sample_id_policy`
- `barcode_parse_policy`
- `duplicate_resolution_policy`

Validation requirements:

- `sample_id` must be unique.
- TCGA barcode parsing rules must be explicit.
- Tumor/normal labels must come from sample type code or trusted metadata, not filename guessing alone.

## Asset: tcga_mutation_matrix

Role: `tcga_mutation_matrix`

Recommended path:

```text
organized/tcga/mutation/tcga_mutation_matrix.tsv.gz
```

Format:

- `tsv` or `tsv.gz`

Required columns:

- `feature_id`
- `entrez_gene_id`
- `gene_symbol`
- one dynamic column per `sample_id`

Required manifest fields:

- `mutation_source_type`: example `Masked Somatic Mutation`
- `mutation_value_semantic`: example `mutation_count`
- `maf_source_path` when available
- `sample_id_order`

Recommended sidecar:

```text
organized/tcga/mutation/tcga_mutation_events.tsv.gz
```

Recommended event columns:

- `sample_id`
- `tcga_barcode`
- `gene_symbol`
- `entrez_gene_id`
- `variant_classification`
- `chromosome`
- `start_position`
- `end_position`
- `reference_allele`
- `tumor_seq_allele`

Validation requirements:

- Matrix values must be numeric.
- Missing gene/sample combinations should be represented as zero when using count matrices.
- Pivot rules must be recorded.

## Asset: tcga_cnv_matrix

Role: `tcga_cnv_matrix`

Recommended path:

```text
organized/tcga/cnv/tcga_cnv_matrix.tsv.gz
```

Format:

- `tsv` or `tsv.gz`

Required columns:

- `feature_id`
- `gene_id`
- `gene_symbol`
- one dynamic column per `sample_id`

Required manifest fields:

- `cnv_source_type`: example `Gene Level Copy Number`
- `workflow_type`: example `ASCAT3`
- `cnv_value_semantic`: examples include `copy_number`, `segment_mean`, `transformed_copy_number`
- `sample_id_order`
- `tumor_sample_filter`
- `duplicate_resolution_policy`

Recommended sidecars:

```text
organized/tcga/cnv/tcga_cnv_removed_features.tsv
organized/tcga/cnv/tcga_cnv_removed_samples.tsv
```

Validation requirements:

- Declare whether normal samples are excluded.
- Declare whether low-variance genes are removed.
- Declare whether nonparanormal or other transformations were applied.

## Asset: tcga_methylation_matrix

Role: `tcga_methylation_matrix`

Recommended path:

```text
organized/tcga/methylation/tcga_methylation_matrix.tsv.gz
```

Format:

- `tsv` or `tsv.gz`

Required columns:

- `feature_id`
- `gene_id`
- `gene_symbol`
- one dynamic column per `sample_id`

Required manifest fields:

- `methylation_source_type`: example `methylation_beta_value`
- `platform`: examples include `Illumina Human Methylation 450`, `EPIC`
- `methylation_value_semantic`: examples include `beta_value`, `m_value`, `npn_m_value`
- `feature_level`: examples include `probe`, `promoter_gene`
- `probe_map_asset`
- `missingness_threshold`
- `imputation_method`
- `sample_id_order`

Recommended sidecars:

```text
organized/tcga/methylation/tcga_methylation_probe_manifest.tsv
organized/tcga/methylation/tcga_methylation_removed_features.tsv
```

Validation requirements:

- Declare whether beta values were converted to M-values.
- Declare whether nonparanormal transformation was applied.
- Probe-to-gene aggregation method must be explicit.
- Removed probes or genes should be reported.

## Asset: tcga_prepare_manifest

Role: `tcga_prepare_manifest`

Recommended path:

```text
organized/tcga/tcga_prepare_manifest.json
```

Format:

- `json`

Required top-level fields:

- `contract_version`
- `manifest_role`
- `dataset_id`
- `tcga_project_id`
- `created_at`
- `status`
- `source_requests`
- `assets`
- `sample_id_order`
- `parameters`
- `software`
- `warnings`
- `errors`

Required `assets` entries:

- `asset_role`
- `path`
- `format`
- `status`
- `row_count`
- `column_count`
- `orientation`
- `id_policy`
- `parameters`
- `source_paths`
- `warnings`

Recommended `source_requests` fields:

- `source_db`
- `data_category`
- `data_type`
- `workflow_type`
- `platform`
- `access`
- `sample_filter_path`
- `request_status`
- `download_manifest_path`

Recommended `software` fields:

- `biomedpilot_version`
- `runner_kind`
- `runner_version`
- `external_packages`
- `container_or_environment`

Validation requirements:

- Every produced TCGA asset must be listed in the manifest.
- Manifest paths must be relative to the dataset root when possible.
- Missing optional modalities should be represented as absent assets, not empty placeholder files.
- Warnings must preserve data loss decisions such as sample removal, feature removal, missingness filtering, failed downloads, and unsupported source fields.

## Minimal Complete TCGA Bundle

A minimal expression-only TCGA bundle should include:

- `tcga_expression_matrix`
- `tcga_sample_metadata`
- `tcga_prepare_manifest`

A clinical/survival-ready TCGA bundle should include:

- `tcga_expression_matrix`
- `tcga_clinical_table`
- `tcga_sample_metadata`
- `tcga_prepare_manifest`

A multi-omics TCGA bundle may include:

- `tcga_expression_matrix`
- `tcga_clinical_table`
- `tcga_sample_metadata`
- `tcga_mutation_matrix`
- `tcga_cnv_matrix`
- `tcga_methylation_matrix`
- `tcga_prepare_manifest`

## Integration Notes

- The GUI should consume only validated manifests and standard assets.
- Real GDC/recount3 downloaders should be introduced behind task adapters, not inside report generation.
- Nextflow can be revisited later as an optional export or advanced backend, but it should not be a required desktop dependency.
- Current GEO/GSE33630 regression behavior should remain independent of this TCGA contract.
