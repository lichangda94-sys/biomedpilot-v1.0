# Bioinformatics C1 Closure Matrix

- branch: `integration/release-bio-c1-ui-shell`
- head: `606bb2c7881a843d4e41e381116b120248b7877d`
- closure_status: `passed_with_documented_gaps`
- ui_page_count: `7`
- capability_row_count: `7`
- input_row_count: `192`
- connected_rows_from_inputs: `137`
- disabled_rows_with_reason: `55`
- broken_rows_from_inputs: `0`

## Inputs

| Batch | Report | Head | Rows | Connected | Disabled | Broken |
| --- | --- | --- | --- | --- | --- | --- |
| `batch4_formal_deg` | `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH4_FORMAL_DEG.json` | `8b20ac157f3c` | `8` | `8` | `0` | `0` |
| `batch5_enrichment` | `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH5_ENRICHMENT.json` | `396645e24b7f` | `9` | `4` | `5` | `0` |
| `batch6_survival` | `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH6_SURVIVAL.json` | `606bb2c7881a` | `9` | `4` | `5` | `0` |
| `batch7_report_export` | `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH7_REPORT_EXPORT.json` | `8b20ac157f3c` | `13` | `13` | `0` | `0` |
| `batch8_visible_buttons` | `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH8_VISIBLE_BUTTONS.json` | `b47d29ba66a4` | `94` | `56` | `38` | `0` |
| `batch9_data_prep_adapters` | `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH9_DATA_PREP_ADAPTERS.json` | `546e66394ef2` | `9` | `9` | `0` | `0` |
| `batch10_geo_online_retrieval` | `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH10_GEO_ONLINE_RETRIEVAL.json` | `dc55902228f5` | `18` | `18` | `0` | `0` |
| `batch11_tcga_gtex_adapters` | `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH11_TCGA_GTEX_ADAPTERS.json` | `c2f144f9f7b7` | `10` | `6` | `4` | `0` |
| `batch12_tcga_gtex_light_validation` | `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH12_TCGA_GTEX_LIGHT_VALIDATION.json` | `648ecbd9691d` | `10` | `10` | `0` | `0` |
| `batch13_tcga_gtex_data_check` | `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH13_TCGA_GTEX_DATA_CHECK.json` | `66e528d05d91` | `5` | `5` | `0` | `0` |
| `batch14_formal_ora` | `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH14_FORMAL_ORA.json` | `396645e24b7f` | `7` | `4` | `3` | `0` |

## Page Baseline Matrix

| UI page | Visual baseline | Source branch | Source commits | Visible button summary |
| --- | --- | --- | --- | --- |
| Project Home | UIShell 7-step Bio high-fidelity gated shell | `codex/integration-labtools-ui-c2-carryover` | `08e9bd1, 900ba60, 2063ce8, 74c19ad` | connected=9, disabled=4, total=13 |
| Data Source | UIShell 7-step Bio high-fidelity gated shell | `codex/integration-labtools-ui-c2-carryover` | `08e9bd1, 900ba60, 2063ce8, 74c19ad` | connected=7, disabled=10, total=17 |
| Data Check & Preparation | UIShell 7-step Bio high-fidelity gated shell | `codex/integration-labtools-ui-c2-carryover` | `08e9bd1, 62739aa, 2063ce8, 74c19ad` | connected=6, disabled=1, total=7 |
| Group & Design | UIShell 7-step Bio high-fidelity gated shell | `codex/integration-labtools-ui-c2-carryover` | `08e9bd1, 62739aa, 2063ce8, 74c19ad` | connected=6, disabled=10, total=16 |
| Analysis Tasks | UIShell 7-step Bio high-fidelity gated shell | `codex/integration-labtools-ui-c2-carryover` | `08e9bd1, 4061d72, 2063ce8, 74c19ad` | connected=11, disabled=4, total=15 |
| Result & Report | UIShell 7-step Bio high-fidelity gated shell | `codex/integration-labtools-ui-c2-carryover` | `08e9bd1, 2d5a560, 2063ce8, 74c19ad` | connected=11, disabled=8, total=19 |
| Report Export | UIShell 7-step Bio high-fidelity gated shell | `codex/integration-labtools-ui-c2-carryover` | `08e9bd1, 2d5a560, 2063ce8, 74c19ad` | connected=6, disabled=1, total=7 |

## UI Page To Backend Capability Matrix

| UI page | Required connection | Status | Backend capability | Evidence batches | Current strategy | Remaining gap |
| --- | --- | --- | --- | --- | --- | --- |
| Project Home | Project shell, project create/open/current-project routing | `connected` | app.bioinformatics.project_home / BioinformaticsWorkspaceWidget route adapters | `batch8_visible_buttons` | Mature page retained; visible buttons live-clicked or explicitly disabled. | Project Center recent-project backend is still placeholder and must not be treated as connected. |
| Data Source | GEO / Local / TCGA / GTEx entry points connect to acquisition/retrieval/recognition, not direct analysis | `connected` | create_data_source_request; register_acquisition; local source manifest handoff; TCGAMetadataPreviewService; GTExMetadataPreviewService; TCGA/GTEx download plan draft writers; TCGADownloadPlanExecutor; GTExDownloadPlanExecutor; TCGA/GTEx expression builders | `batch8_visible_buttons, batch9_data_prep_adapters, batch10_geo_online_retrieval, batch11_tcga_gtex_adapters, batch12_tcga_gtex_light_validation, batch13_tcga_gtex_data_check` | All four source buttons write request drafts; Local has adapter proof into acquisition and recognition chain; visible GEO adapter live-click downloads GSE6004/GSE153659 metadata and assets; visible TCGA/GTEx adapter live-clicks metadata preview, download-plan artifacts, light-validation download receipts, expression build manifests, Data Check recognition, and readiness artifacts. | Full-scale TCGA/GTEx non-light downloads remain explicitly approval-gated and are not claimed as C1 production analysis inputs. |
| Data Check & Preparation | Data recognition, dependency/readiness detection, and preflight artifacts | `connected` | project_recognition; project_readiness; project_standardization | `batch8_visible_buttons, batch9_data_prep_adapters, batch13_tcga_gtex_data_check` | Buttons write recognition, readiness, capability matrix, standardized asset, analysis-ready, and repository manifests; TCGA/GTEx light-validation build outputs are live-clicked through recognition/readiness. | Full-scale TCGA/GTEx non-light assets remain outside this C1 live-click proof. |
| Group & Design | Group/comparison/covariate state and blocker handling | `connected` | group_comparison_design build/save adapters | `batch8_visible_buttons, batch9_data_prep_adapters` | Suggestion/save/continue buttons live-clicked and artifact-verified. | Expanded covariate modeling remains gate-scoped unless current design manifest proves the schema. |
| Analysis Tasks | Formal DEG, ORA/GSEA, survival/clinical task gates | `partial` | formal DEG executor; EnrichmentService preflight/detect/formal ORA; SurvivalService preflight/detect | `batch4_formal_deg, batch5_enrichment, batch6_survival, batch8_visible_buttons, batch14_formal_ora` | Formal DEG positive path is connected; enrichment preflight/R detect and local-GMT formal ORA are connected; survival preflight/detect is connected; formal GSEA and KM/Cox/risk-score remain disabled with reasons. | Formal GSEA executor and survival KM/log-rank/Cox/risk-score/report-ready execution are intentionally not enabled. |
| Result & Report | DEG review, plot, report draft, result index, artifact registry | `connected` | result index loader; formal DEG review/export/plot/report-ready adapters; formal ORA result index registration | `batch4_formal_deg, batch7_report_export, batch8_visible_buttons, batch14_formal_ora` | Formal DEG result review, table export, plot artifact, and report-ready package are live-click verified; formal ORA writes JSON/CSV and a result index entry from the mature Enrichment page. | Formal ORA plot/report-ready promotion, GSEA outputs, and survival outputs remain gated until their schemas are connected. |
| Report Export | Report-ready gate and export only after gate passes | `connected` | report draft manifest and formal DEG report-ready package export | `batch4_formal_deg, batch7_report_export, batch8_visible_buttons` | Formal DEG package export is live-click verified after report-ready gate; report draft stays separate from report-ready promotion. | Non-DEG report-ready exports remain closed until their formal result schemas are connected. |

## Remaining Gaps

- `Analysis Tasks`: Formal GSEA executor and survival KM/log-rank/Cox/risk-score/report-ready execution are intentionally not enabled.

## Screenshot Evidence

- `batch4_formal_deg` / `01_analysis_tasks_formal_deg_ready`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_bio_batch4_formal_deg/01_analysis_tasks_formal_deg_ready.png`
- `batch4_formal_deg` / `02_result_review_formal_deg`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_bio_batch4_formal_deg/02_result_review_formal_deg.png`
- `batch4_formal_deg` / `03_result_review_plot_gate`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_bio_batch4_formal_deg/03_result_review_plot_gate.png`
- `batch4_formal_deg` / `04_report_export_formal_deg_ready`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_bio_batch4_formal_deg/04_report_export_formal_deg_ready.png`
- `batch5_enrichment` / `Bio Enrichment ORA/GSEA gate`: `docs/ui/runtime_screenshots/20260602_bio_batch5_enrichment/01_enrichment_ora_gsea_gate.png`
- `batch6_survival` / `Bio Survival/Clinical gate`: `docs/ui/runtime_screenshots/20260602_bio_batch6_survival/01_survival_clinical_gate.png`
- `batch7_report_export` / `Result & Report`: `docs/ui/runtime_screenshots/20260602_bio_batch7_report_export/01_result_report_cross_gate.png`
- `batch7_report_export` / `Report Export`: `docs/ui/runtime_screenshots/20260602_bio_batch7_report_export/02_report_export_formal_only_gate.png`
- `batch8_visible_buttons` / `project_home`: `docs/ui/runtime_screenshots/20260602_bio_batch8_visible_buttons/01_project_home.png`
- `batch8_visible_buttons` / `data_source`: `docs/ui/runtime_screenshots/20260602_bio_batch8_visible_buttons/02_data_source.png`
- `batch8_visible_buttons` / `data_check_preparation`: `docs/ui/runtime_screenshots/20260602_bio_batch8_visible_buttons/03_data_check_preparation.png`
- `batch8_visible_buttons` / `group_design`: `docs/ui/runtime_screenshots/20260602_bio_batch8_visible_buttons/04_group_design.png`
- `batch8_visible_buttons` / `analysis_tasks`: `docs/ui/runtime_screenshots/20260602_bio_batch8_visible_buttons/05_analysis_tasks.png`
- `batch8_visible_buttons` / `result_report`: `docs/ui/runtime_screenshots/20260602_bio_batch8_visible_buttons/06_result_report.png`
- `batch8_visible_buttons` / `report_export`: `docs/ui/runtime_screenshots/20260602_bio_batch8_visible_buttons/07_report_export.png`
- `batch9_data_prep_adapters` / `01_data_source`: `docs/ui/runtime_screenshots/20260602_bio_batch9_data_prep_adapters/01_data_source.png`
- `batch9_data_prep_adapters` / `02_recognition_before_click`: `docs/ui/runtime_screenshots/20260602_bio_batch9_data_prep_adapters/02_recognition_before_click.png`
- `batch9_data_prep_adapters` / `03_recognition_after_click`: `docs/ui/runtime_screenshots/20260602_bio_batch9_data_prep_adapters/03_recognition_after_click.png`
- `batch9_data_prep_adapters` / `04_readiness`: `docs/ui/runtime_screenshots/20260602_bio_batch9_data_prep_adapters/04_readiness.png`
- `batch9_data_prep_adapters` / `05_standardization_before_click`: `docs/ui/runtime_screenshots/20260602_bio_batch9_data_prep_adapters/05_standardization_before_click.png`
- `batch9_data_prep_adapters` / `06_standardization_after_click`: `docs/ui/runtime_screenshots/20260602_bio_batch9_data_prep_adapters/06_standardization_after_click.png`
- `batch9_data_prep_adapters` / `07_group_design_prepared`: `docs/ui/runtime_screenshots/20260602_bio_batch9_data_prep_adapters/07_group_design_prepared.png`
- `batch10_geo_online_retrieval` / `GSE6004_01_geo_adapter_ready`: `docs/ui/runtime_screenshots/20260602_bio_batch10_geo_online_retrieval/GSE6004_01_geo_adapter_ready.png`
- `batch10_geo_online_retrieval` / `GSE6004_02_geo_metadata_downloaded`: `docs/ui/runtime_screenshots/20260602_bio_batch10_geo_online_retrieval/GSE6004_02_geo_metadata_downloaded.png`
- `batch10_geo_online_retrieval` / `GSE6004_03_geo_assets_downloaded`: `docs/ui/runtime_screenshots/20260602_bio_batch10_geo_online_retrieval/GSE6004_03_geo_assets_downloaded.png`
- `batch10_geo_online_retrieval` / `GSE6004_04_recognition_complete`: `docs/ui/runtime_screenshots/20260602_bio_batch10_geo_online_retrieval/GSE6004_04_recognition_complete.png`
- `batch10_geo_online_retrieval` / `GSE6004_05_readiness_complete`: `docs/ui/runtime_screenshots/20260602_bio_batch10_geo_online_retrieval/GSE6004_05_readiness_complete.png`
- `batch10_geo_online_retrieval` / `GSE153659_01_geo_adapter_ready`: `docs/ui/runtime_screenshots/20260602_bio_batch10_geo_online_retrieval/GSE153659_01_geo_adapter_ready.png`
- `batch10_geo_online_retrieval` / `GSE153659_02_geo_metadata_downloaded`: `docs/ui/runtime_screenshots/20260602_bio_batch10_geo_online_retrieval/GSE153659_02_geo_metadata_downloaded.png`
- `batch10_geo_online_retrieval` / `GSE153659_03_geo_assets_downloaded`: `docs/ui/runtime_screenshots/20260602_bio_batch10_geo_online_retrieval/GSE153659_03_geo_assets_downloaded.png`
- `batch10_geo_online_retrieval` / `GSE153659_04_recognition_complete`: `docs/ui/runtime_screenshots/20260602_bio_batch10_geo_online_retrieval/GSE153659_04_recognition_complete.png`
- `batch10_geo_online_retrieval` / `GSE153659_05_readiness_complete`: `docs/ui/runtime_screenshots/20260602_bio_batch10_geo_online_retrieval/GSE153659_05_readiness_complete.png`
- `batch11_tcga_gtex_adapters` / `01_tcga_adapter_ready`: `docs/ui/runtime_screenshots/20260602_bio_batch11_tcga_gtex_adapters/01_tcga_adapter_ready.png`
- `batch11_tcga_gtex_adapters` / `02_tcga_metadata_preview`: `docs/ui/runtime_screenshots/20260602_bio_batch11_tcga_gtex_adapters/02_tcga_metadata_preview.png`
- `batch11_tcga_gtex_adapters` / `03_tcga_download_plan`: `docs/ui/runtime_screenshots/20260602_bio_batch11_tcga_gtex_adapters/03_tcga_download_plan.png`
- `batch11_tcga_gtex_adapters` / `04_gtex_adapter_ready`: `docs/ui/runtime_screenshots/20260602_bio_batch11_tcga_gtex_adapters/04_gtex_adapter_ready.png`
- `batch11_tcga_gtex_adapters` / `05_gtex_metadata_preview`: `docs/ui/runtime_screenshots/20260602_bio_batch11_tcga_gtex_adapters/05_gtex_metadata_preview.png`
- `batch11_tcga_gtex_adapters` / `06_gtex_download_plan`: `docs/ui/runtime_screenshots/20260602_bio_batch11_tcga_gtex_adapters/06_gtex_download_plan.png`
- `batch12_tcga_gtex_light_validation` / `01_tcga_adapter_ready`: `docs/ui/runtime_screenshots/20260602_bio_batch12_tcga_gtex_light_validation/01_tcga_adapter_ready.png`
- `batch12_tcga_gtex_light_validation` / `02_tcga_metadata_preview`: `docs/ui/runtime_screenshots/20260602_bio_batch12_tcga_gtex_light_validation/02_tcga_metadata_preview.png`
- `batch12_tcga_gtex_light_validation` / `03_tcga_download_plan`: `docs/ui/runtime_screenshots/20260602_bio_batch12_tcga_gtex_light_validation/03_tcga_download_plan.png`
- `batch12_tcga_gtex_light_validation` / `03a_tcga_light_download`: `docs/ui/runtime_screenshots/20260602_bio_batch12_tcga_gtex_light_validation/03a_tcga_light_download.png`
- `batch12_tcga_gtex_light_validation` / `03b_tcga_expression_build`: `docs/ui/runtime_screenshots/20260602_bio_batch12_tcga_gtex_light_validation/03b_tcga_expression_build.png`
- `batch12_tcga_gtex_light_validation` / `04_gtex_adapter_ready`: `docs/ui/runtime_screenshots/20260602_bio_batch12_tcga_gtex_light_validation/04_gtex_adapter_ready.png`
- `batch12_tcga_gtex_light_validation` / `05_gtex_metadata_preview`: `docs/ui/runtime_screenshots/20260602_bio_batch12_tcga_gtex_light_validation/05_gtex_metadata_preview.png`
- `batch12_tcga_gtex_light_validation` / `06_gtex_download_plan`: `docs/ui/runtime_screenshots/20260602_bio_batch12_tcga_gtex_light_validation/06_gtex_download_plan.png`
- `batch12_tcga_gtex_light_validation` / `06a_gtex_light_download`: `docs/ui/runtime_screenshots/20260602_bio_batch12_tcga_gtex_light_validation/06a_gtex_light_download.png`
- `batch12_tcga_gtex_light_validation` / `06b_gtex_expression_build`: `docs/ui/runtime_screenshots/20260602_bio_batch12_tcga_gtex_light_validation/06b_gtex_expression_build.png`
- `batch13_tcga_gtex_data_check` / `01_tcga_built_source_ready`: `docs/ui/runtime_screenshots/20260602_bio_batch13_tcga_gtex_data_check/01_tcga_built_source_ready.png`
- `batch13_tcga_gtex_data_check` / `01_gtex_built_source_ready`: `docs/ui/runtime_screenshots/20260602_bio_batch13_tcga_gtex_data_check/01_gtex_built_source_ready.png`
- `batch13_tcga_gtex_data_check` / `02_data_check_tcga_gtex_selected`: `docs/ui/runtime_screenshots/20260602_bio_batch13_tcga_gtex_data_check/02_data_check_tcga_gtex_selected.png`
- `batch13_tcga_gtex_data_check` / `03_data_check_recognition_done`: `docs/ui/runtime_screenshots/20260602_bio_batch13_tcga_gtex_data_check/03_data_check_recognition_done.png`
- `batch13_tcga_gtex_data_check` / `04_readiness_before_run`: `docs/ui/runtime_screenshots/20260602_bio_batch13_tcga_gtex_data_check/04_readiness_before_run.png`
- `batch13_tcga_gtex_data_check` / `05_readiness_after_run`: `docs/ui/runtime_screenshots/20260602_bio_batch13_tcga_gtex_data_check/05_readiness_after_run.png`
- `batch14_formal_ora` / `01_formal_ora_inputs_ready`: `docs/ui/runtime_screenshots/20260602_bio_batch14_formal_ora/01_formal_ora_inputs_ready.png`
- `batch14_formal_ora` / `02_formal_ora_result_review`: `docs/ui/runtime_screenshots/20260602_bio_batch14_formal_ora/02_formal_ora_result_review.png`
