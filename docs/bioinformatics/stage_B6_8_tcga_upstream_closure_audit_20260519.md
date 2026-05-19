# Bioinformatics B6.8 TCGA Upstream Closure Audit

Date: 2026-05-19

## Scope

B6.8 audits the TCGA upstream chain from B6.1 through B6.7:

1. B6.1 static TCGA project/request entry
2. B6.2 GDC metadata preview and download plan draft
3. B6.3 real GDC raw file download executor
4. B6.4 expression quantification parsing and matrix build
5. B6.5 readiness integration
6. B6.6 clinical metadata acquisition and expression-clinical mapping
7. B6.7 consolidated TCGA workflow UI

This audit does not add new GDC data types, does not execute DEG/GSEA/survival analyses, does not merge TCGA with GTEx, and does not advance B5.19.

## Closure Findings

| Area | Result | Notes |
| --- | --- | --- |
| Status flow | Pass after B6.8 fix | Plan, raw download, expression build, clinical build, and data check transitions are explicit and recoverable from project artifacts. |
| Artifact naming | Pass | B6.2 plans, B6.3 receipts/manifests, B6.4 expression build outputs, and B6.6 clinical outputs use stable TCGA-prefixed names. |
| Readiness | Pass | B6.3 raw files are not counted ready; B6.4 expression outputs enter data check/preflight readiness; B6.6 clinical outputs enter clinical/survival preflight readiness only. |
| UI copy | Pass after B6.8 fix | User-facing copy avoids raw file UUIDs and filters, preserves "waiting" states, and keeps analysis boundaries visible. |
| Developer diagnostics | Pass | GDC filters, manifest paths, receipt paths, raw paths, and workflow state stay in the collapsed developer diagnostics panel. |
| Boundary prompts | Pass | UI/readiness consistently state no automatic TCGA+GTEx merge, no GTEx default normal control, no DEG/GSEA execution, and no KM/Cox/log-rank execution. |

## B6.8 Fixes Applied

The audit found one consistency risk in multi-project workspaces:

- Several workflow/UI lookups used the latest TCGA artifact in the project, rather than the artifact for the currently selected TCGA project.
- This could make a TCGA-LUAD expression or clinical build unlock buttons while the TCGA page was showing TCGA-THCA.

Fixes:

- `latest_tcga_download_plan_path(project_root, project_id=...)`
- `latest_tcga_raw_expression_record_path(project_root, project_id=...)`
- `latest_tcga_expression_build_manifest_path(project_root, project_id=...)`
- `latest_tcga_clinical_build_manifest_path(project_root, project_id=...)`
- TCGA workflow state now scopes plan/raw/build/clinical discovery to the selected project.
- TCGA UI buttons now use selected-project scoped lookup for download, expression build, and clinical metadata actions.
- Clinical status text now shows the user-facing blocked summary plus the technical blocking reason.

## Status Contract

| Stage | Primary status | Gate status | User meaning |
| --- | --- | --- | --- |
| B6.1 request | `registered_pending_tcga_build` | `pending_download` | Planned TCGA source only. |
| B6.2 plan | `tcga_gdc_download_plan_draft_created` | `pending_download` | Metadata preview and plan exist; no source files. |
| B6.3 raw files | `tcga_gdc_raw_files_acquired` or warning/failure variants | `waiting_b6_4_expression_matrix_build` | Raw GDC files acquired; not DEG/GSEA ready. |
| B6.4 expression build | `tcga_expression_matrix_built` | `pending_data_check` | Expression matrices and sample metadata built; enter unified data check/preflight. |
| B6.5 readiness | `tcga_readiness` | preflight only | Raw counts are DEG candidate input; TPM/FPKM/FPKM-UQ are display assets. |
| B6.6 clinical build | `tcga_clinical_metadata_built` | `clinical_ready/partial`, `survival_ready_basic/partial/unavailable` | Clinical and basic OS metadata are available for preflight, not execution. |
| B6.7 workflow | `TCGAWorkflowState` | UI state only | One five-step path controls the upstream user journey. |

## Artifact Contract

| Stage | Artifacts |
| --- | --- |
| B6.2 | `acquisition/tcga_download_plans/*.json` with `file_manifest_entries` and GDC filters. |
| B6.3 | `acquisition/download_requests/*.json`, `acquisition/download_receipts/*.json`, `raw_data/tcga/<project_id>/<download_id>/<project_id>_gdc_download_manifest.json`, source manifest, raw source files. |
| B6.4 | `tcga_expression_matrix.csv`, `tcga_tpm_matrix.csv`, `tcga_fpkm_matrix.csv`, `tcga_fpkm_uq_matrix.csv`, `tcga_sample_metadata.csv`, `tcga_sample_file_mapping.csv`, `tcga_gene_annotation.csv`, `tcga_expression_build_manifest.json`, `tcga_prepare_manifest.json`. |
| B6.6 | `tcga_clinical_raw_cases.json`, case/diagnosis/follow-up/survival/mapping TSVs, `tcga_clinical_build_manifest.json`, `acquisition/clinical_receipts/*.json`, `acquisition/clinical_manifests/*.json`. |

## Readiness Boundary

- B6.3 raw files keep `ready_for_recognition=pending_expression_matrix_build`.
- B6.4 expression build uses `ready_for_recognition=pending_data_check` and `analysis_gate_status=pending_data_check`.
- B6.5 can expose TCGA expression assets to data check and DEG preflight, but comparison confirmation is still required.
- B6.6 clinical metadata contributes `tcga_clinical_metadata`, `tcga_expression_clinical_mapping`, and `basic_survival_metadata` where available.
- Survival readiness remains preflight-only. The app does not run KM, Cox, or log-rank and does not create clinical conclusions.
- TCGA+GTEx remains blocked until an explicit joint configuration and batch correction plan exist.

## Developer Diagnostics

The TCGA page keeps these in collapsed diagnostics:

- GDC `/files` and `/cases` filters
- selected file UUID previews
- pagination counts
- download plan path
- receipt path
- source manifest path
- raw cache path
- expression build manifest path
- clinical build manifest path
- highest-stage record

Primary user panels show counts, status, warnings, and next actions instead of raw filters or full file UUID lists.

## Validation Coverage

Added/updated coverage:

- Project-scoped workflow recovery: artifacts from TCGA-LUAD do not unlock TCGA-THCA.
- Project-scoped UI buttons: current project selection controls clinical button enablement.
- Existing B6.2-B6.7 unit/UI tests continue to cover preview, plan, download, expression build, clinical build, readiness, and boundary messaging.

## Handoff

B6.1-B6.7 upstream TCGA flow is closed for the current implementation level. The next useful work is downstream data-check/preflight UX: value type confirmation, comparison confirmation, clinical/survival preflight configuration, and only then explicit analysis execution stages.
