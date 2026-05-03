# TCGA Nextflow Reference Assessment

## Scope

This document evaluates the external project at `/Users/changdali/Downloads/tcga-data-nf-main` as a reference for BioMedPilot TCGA functionality. The assessment is intentionally non-invasive: the Nextflow pipeline should not be copied, vendored, or launched from the desktop app at this stage.

Reviewed external files:

- `main.nf`
- `nextflow.config`
- `modules/download.nf`
- `modules/prepare.nf`
- `modules/tcga_wfs.nf` for downstream reporting and analysis context
- `bin/r/download_expression_recount.R`
- `bin/r/download_clinical_tcga.R`
- `bin/r/download_mutation_tcga.R`
- `bin/r/download_cnv_tcga.R`
- `bin/r/download_methylation_gdc.R`
- `bin/r/prepare_expression_recount.R`
- `bin/r/get_gene_level_methylation.r`
- `bin/r/clean_methylation_data.r`
- `bin/r/prepare_cnv.r`
- `bin/bash/join_methylation_gdc.sh`
- `bin/bash/remove_dot_ensembl.sh`
- `bin/fit.py`

Current BioMedPilot context:

- TCGA/GTEx support currently lives under `app/bioinformatics/legacy/tcga_gtex/`.
- Existing TCGA/GTEx adapters are concept-driven study and file candidate resolvers, not real GDC/recount3 downloaders.
- Existing download runtime supports local files and mocked HTTP locators and writes `download_manifest.json`.
- Existing bundle builder infers roles from local files and writes `analysis_bundle.json`, `bundle_manifest.json`, and `bundle_summary.json`.
- Existing GEO standard asset contract is `app/bioinformatics/legacy/configs/standards/asset_contract_v1.yaml`.
- Standard report v1 accepts already-produced artifacts and reproducibility metadata; it does not execute analyses.

## External Data Type Coverage

| Data type | Source | External process or script | Main inputs | Main outputs |
|---|---|---|---|---|
| expression | recount3 | `downloadRecount` in `modules/download.nf`; `bin/r/download_expression_recount.R` | `project`, `project_home`, `organism`, `annotation`, `type`, optional sample list | recount3 `RangedSummarizedExperiment` RDS and `downloaded_recount_metadata.csv` |
| expression prepared | recount3 RDS | `prepareTCGARecount` in `modules/prepare.nf`; `bin/r/prepare_expression_recount.R` | recount3 RDS, normalization, TPM/CPM/count choice, `min_tpm`, `frac_samples`, tumor purity threshold, tissue type, batch variable | standardized expression matrix `.txt`, prepared RDS, PCA diagnostic PNG, log |
| clinical | GDC via TCGAbiolinks | `downloadClinical` in `modules/download.nf`; `bin/r/download_clinical_tcga.R` | TCGA project, data category, data type, data format, download directory | one CSV per clinical BCR Biotab file |
| mutation | GDC via TCGAbiolinks | `downloadMutations` in `modules/download.nf`; `bin/r/download_mutation_tcga.R` | TCGA project, data category, data type, optional sample list | mutation table and gene-by-sample pivot matrix; `downloaded_mutation_metadata.csv` |
| CNV | GDC via TCGAbiolinks | `downloadCNV` in `modules/download.nf`; `bin/r/download_cnv_tcga.R`; `bin/r/prepare_cnv.r` | TCGA project, workflow type, optional sample list, optional TF list | raw CNV RDS/CSV, cleaned CNV matrix, clean log, removed feature list; `downloaded_cnv_metadata.csv` |
| methylation | GDC via GenomicDataCommons | `downloadMethylation` in `modules/download.nf`; `bin/r/download_methylation_gdc.R`; `bin/bash/join_methylation_gdc.sh` | TCGA project, GDC type, platform, optional sample list | manifest, probe-level beta matrix, `downloaded_methylation_metadata.csv` |
| methylation prepared | GDC methylation beta matrix | `GetGeneLevelPromoterMethylation` and `CleanMethylationData` in `modules/prepare.nf`; `bin/r/get_gene_level_methylation.r`; `bin/r/clean_methylation_data.r` | methylation table, promoter probe map, optional TF list, tissue type, missingness threshold | raw gene-level promoter methylation CSV, cleaned methylation matrix, PCA diagnostics, log |

## External Workflow Shape

The external project is organized around Nextflow channels and process outputs:

1. `main.nf` dispatches by `params.pipeline`: `download`, `prepare`, `analyze`, or `full`.
2. Download workflows read JSON metadata, run one process per data modality, then merge per-run metadata tables through `fit.py merge-tables`.
3. Prepare workflows read downloaded metadata CSVs or direct full-pipeline channels and produce prepared matrices under `results/<batchName>/<uuid>/data_prepared/`.
4. Analysis workflows run netZoo-style PANDA, LIONESS, DRAGON, ALPACA, GENIE3, or WGCNA from prepared matrices.
5. Reproducibility comes from Nextflow config snapshots, logs, process reports, timeline, trace, DAG, and parameterized file names.

This is useful as a reference for BioMedPilot standard asset design, but it is not a good direct runtime dependency for a desktop-first app.

## Can Be Directly Migrated

These items are small enough and generic enough to copy conceptually into BioMedPilot documentation or future contracts. Direct migration here means reusing the idea or schema shape, not copying full scripts.

- Data type inventory: expression, clinical, mutation, CNV, methylation.
- Batch manifest pattern: each modality should write paths, parameters, source project, and sample list into a machine-readable manifest.
- Output role naming: expression matrix, clinical table, sample metadata, mutation matrix, CNV matrix, methylation matrix, prepare manifest.
- Reproducibility fields: source project, data source, query parameters, normalization method, filters, output paths, warnings, software/runtime information.
- Prepared expression file-name parameterization: normalization, expression filter, tissue filter, purity filter, and batch correction should be captured in metadata.
- Diagnostic artifact classes: logs, PCA plots, removed sample/feature lists, and warning messages.

## Needs Rewrite Before Migration

These capabilities are scientifically useful but should be rewritten behind BioMedPilot adapters and standard assets.

- recount3 expression download:
  - Keep the source choice and key inputs.
  - Rewrite as a TCGA expression acquisition adapter or an external R task specification that returns BioMedPilot manifests.
  - Do not expose recount3 RDS internals directly to the GUI.

- TCGA expression preparation:
  - Reuse the processing requirements: normalization, duplicate sample handling, low-expression filtering, purity filtering, tissue selection, and optional batch correction.
  - Rewrite outputs to `tcga_expression_matrix`, `tcga_sample_metadata`, and `tcga_prepare_manifest`.
  - Make clinical/purity provenance explicit instead of relying on package internals.

- TCGAbiolinks clinical/mutation/CNV download:
  - Reuse the GDC query categories and sample filtering logic.
  - Rewrite with explicit downloader request objects, retry policy, progress reporting, and manifest output.
  - Keep mutation pivot generation, but define exact orientation and identifiers in the asset contract.

- GDC methylation download and preparation:
  - Reuse manifest-driven download, UUID-to-TCGA barcode mapping, probe-to-promoter aggregation, missingness filtering, and beta-to-M-value option.
  - Rewrite shell table joining with a structured, tested parser.
  - Make probe map and TF list standard assets or configurable resources.

- CNV preparation:
  - Reuse tumor-sample selection, duplicate sample averaging, missing feature removal, low-variance removal, and optional nonparanormal transformation.
  - Rewrite sample barcode parsing and removed-feature reporting as pure, testable functions.

- Metadata merging:
  - Reuse the idea of one consolidated modality manifest.
  - Replace ad hoc CSV concatenation with a typed JSON manifest plus optional TSV export.

## Temporarily Do Not Integrate

These pieces should not be connected to BioMedPilot now.

- Nextflow runner integration.
- The full `download -> prepare -> analyze` orchestration.
- HPC profiles, SGE/SLURM configs, conda environment activation, and Nextflow trace/report/DAG output as runtime dependencies.
- netZoo analysis processes: PANDA, LIONESS, DRAGON, ALPACA, GENIE3, and WGCNA.
- `NetworkDataCompanion`-specific object assumptions.
- Direct use of external shell scripts for matrix construction in the desktop workflow.
- Tuple-index-dependent Nextflow channel wiring from the full pipeline.

## Why Not Directly Migrate the Nextflow Pipeline

- Desktop UX needs progress, cancellation, validation, resumability, and friendly errors at the task level. Nextflow process logs are not enough for the current app state model.
- The current BioMedPilot TCGA/GTEx module is adapter-first and manifest-first; the external project is pipeline-first.
- External scripts assume a heavy R/Bioconductor stack: `recount3`, `TCGAbiolinks`, `GenomicDataCommons`, `SummarizedExperiment`, `limma`, `huge`, and `NetworkDataCompanion`.
- The external project writes RDS and process-specific files; BioMedPilot needs stable cross-source assets that reporting and later analysis modules can consume without knowing the source runner.
- The external pipeline includes network inference analyses that are outside the immediate TCGA ingestion and standardization scope.
- Some configuration fields are not fully wired: for example methylation `to_npn` and `to_mval` are defined in config but not passed by the Nextflow clean process, and expression adjustment appears to mirror batch correction.
- Clinical download is present, but clinical data is not integrated into the expression preparation step despite script-level support for a clinical input.

## Current BioMedPilot TCGA Gap

| Capability | Current BioMedPilot status | Gap exposed by external project |
|---|---|---|
| TCGA project search | Present as concept-driven local adapter | Needs real GDC request construction and available-file resolution |
| TCGA file candidates | Present as template-based file records | Needs live GDC manifest/file UUID resolution |
| Download runtime | Local/mock HTTP copy runtime exists | Needs authenticated/large-file GDC downloader behavior, retries, checksums, and progress |
| Expression standardization | Not implemented for real TCGA matrices | Needs expression matrix writer, sample metadata writer, normalization metadata, tissue/purity filters |
| Clinical asset | Not implemented as a standard TCGA asset | Needs harmonized clinical table and survival-ready fields |
| Mutation matrix | Candidate role exists | Needs MAF parsing and gene-by-sample mutation count matrix |
| CNV matrix | Not in current default TCGA file templates | Needs GDC CNV query, gene-level matrix, tumor-sample handling |
| Methylation matrix | Not in current default TCGA file templates | Needs GDC methylation query, probe manifest, gene-level aggregation, missingness policy |
| Standard assets | GEO contract exists; TCGA-specific contract absent | Needs explicit TCGA standard asset contract |
| Reporting | Markdown report can summarize existing artifacts | Needs TCGA prepare manifest fields for report sections |
| Workflow state | Current app has task/report centers and testing mode | Needs task-level statuses for TCGA download, parse, clean, validate, and package |

## Recommended Phased Integration Route

### Phase 0: Contract and fixtures

- Add TCGA standard asset contract.
- Add tiny local fixture files for expression, clinical, mutation, CNV, methylation, and sample metadata.
- Extend tests around manifest validation without network, R, or Nextflow.

### Phase 1: Manifest-first TCGA bundle

- Extend the current `FileRecord` roles to include CNV and methylation.
- Write a `tcga_prepare_manifest` schema and validator.
- Allow local fixture bundles to produce all TCGA asset roles.
- Feed the manifest into the standard report as input artifacts only.

### Phase 2: Real GDC/recount3 request planning

- Add a request planner that emits GDC/recount3 task specs without executing them.
- Capture project ID, data category, data type, workflow type, platform, access level, and sample filters.
- Validate planned outputs against the asset contract.

### Phase 3: Controlled runner adapters

- Add isolated task runners for one modality at a time.
- Start with clinical and mutation because their outputs are simpler table assets.
- Add expression after clinical/sample metadata rules are stable.
- Add CNV and methylation after matrix orientation and identifier policy are tested.

### Phase 4: Desktop workflow integration

- Surface TCGA tasks in workflow state only after the contract validators and fixture tests pass.
- Add GUI affordances for project, modality, tissue/sample filters, and output destination.
- Keep Nextflow as an optional external export target, not the default app runtime.

### Phase 5: Advanced analysis

- Consider PANDA/DRAGON/WGCNA only after TCGA standard assets are stable.
- Treat network analysis as a separate analysis module, not part of ingestion.

## Migration Classification Summary

| Classification | Items |
|---|---|
| Can be directly migrated | Data type coverage list; standard modality names; manifest pattern; diagnostic artifact categories; reproducibility field requirements |
| Needs rewrite before migration | recount3 downloader; TCGAbiolinks/GDC downloaders; expression preparation; mutation pivot; CNV preparation; methylation preparation; metadata merging |
| Temporarily do not integrate | Nextflow runner; HPC/conda configs; netZoo analysis workflows; `NetworkDataCompanion` object assumptions; shell-based matrix joins; tuple-index channel contracts |

## Decision

The external project can serve as a strong reference for BioMedPilot TCGA data coverage and processing requirements. It should not be merged as a pipeline. The next concrete BioMedPilot step should be a TCGA standard asset contract and manifest validator, followed by small fixture-backed adapters that produce those assets without requiring Nextflow, R, network access, or new desktop dependencies.
