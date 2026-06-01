# UI Route Contract Bio Batch 1

- Created: `2026-06-01T14:52:18.300371+00:00`
- Branch: `integration/release-bio-c1-ui-shell`
- HEAD: `933c39b7a1d51a5c76d6824502b787d7d861efaa`
- Scope: Bioinformatics mature 7-step gated UI shell adapter and first-level runtime gate audit.

## Summary

- Rows: 27
- Connected: 22
- Disabled with reason: 5
- Broken: 0

## Screenshots

Runtime screenshots for this batch are stored under:

`docs/ui/runtime_screenshots/20260601_bio_batch1_route_contract/`

- `01_project_home.png`
- `02_data_source.png`
- `03_data_check_recognition.png`
- `04_group_design.png`
- `05_analysis_tasks.png`
- `06_result_report.png`
- `07_report_export.png`
- `08_settings_resources.png`
- `09_project_logs_technical_details.png`

## Rows

| Contract | Surface | Object | Status | Behavior | Evidence |
| --- | --- | --- | --- | --- | --- |
| BIO-IA-PROJECT_HOME | Bioinformatics Target IA | `bioinformaticsIANavItem` | connected | `navigates_to_bio_target_ia_page_project_home` | current_target_page_key=project_home |
| BIO-IA-DATA_SOURCE | Bioinformatics Target IA | `bioinformaticsIANavItem` | connected | `navigates_to_bio_target_ia_page_data_source` | current_target_page_key=data_source |
| BIO-IA-DATA_CHECK_PREPARATION | Bioinformatics Target IA | `bioinformaticsIANavItem` | connected | `navigates_to_bio_target_ia_page_data_check_preparation` | current_target_page_key=data_check_preparation |
| BIO-IA-GROUP_DESIGN | Bioinformatics Target IA | `bioinformaticsIANavItem` | connected | `navigates_to_bio_target_ia_page_group_design` | current_target_page_key=group_design |
| BIO-IA-ANALYSIS_TASKS | Bioinformatics Target IA | `bioinformaticsIANavItem` | connected | `navigates_to_bio_target_ia_page_analysis_tasks` | current_target_page_key=analysis_tasks |
| BIO-IA-RESULT_REPORT | Bioinformatics Target IA | `bioinformaticsIANavItem` | connected | `navigates_to_bio_target_ia_page_result_report` | current_target_page_key=result_report |
| BIO-IA-REPORT_EXPORT | Bioinformatics Target IA | `bioinformaticsIANavItem` | connected | `navigates_to_bio_target_ia_page_report_export` | current_target_page_key=report_export |
| BIO-IA-SETTINGS_RESOURCES | Bioinformatics Target IA | `bioinformaticsIANavItem` | connected | `navigates_to_bio_target_ia_page_settings_resources` | current_target_page_key=settings_resources |
| BIO-IA-PROJECT_LOGS_TECHNICAL_DETAILS | Bioinformatics Target IA | `bioinformaticsIANavItem` | connected | `navigates_to_bio_target_ia_page_project_logs_technical_details` | current_target_page_key=project_logs_technical_details |
| BIO-DATA-SOURCE-GEO | Data Source | `bioinformaticsDataSourceSelectPreviewButton` | connected | `creates_data_source_request_draft_when_project_open` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_7zzxemrb/project/bio_batch_1_contract/manifests/data_source_requests/dsr-d9dfe02ff4.json; status=draft; source=geo |
| BIO-DATA-SOURCE-TCGA | Data Source | `bioinformaticsDataSourceSelectPreviewButton` | connected | `creates_data_source_request_draft_when_project_open` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_7zzxemrb/project/bio_batch_1_contract/manifests/data_source_requests/dsr-06a4f3397c.json; status=draft; source=tcga |
| BIO-DATA-SOURCE-GTEX | Data Source | `bioinformaticsDataSourceSelectPreviewButton` | connected | `creates_data_source_request_draft_when_project_open` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_7zzxemrb/project/bio_batch_1_contract/manifests/data_source_requests/dsr-294d0b6285.json; status=draft; source=gtex |
| BIO-DATA-SOURCE-LOCAL_FILE | Data Source | `bioinformaticsDataSourceSelectPreviewButton` | connected | `creates_data_source_request_draft_when_project_open` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_7zzxemrb/project/bio_batch_1_contract/manifests/data_source_requests/dsr-220cd92829.json; status=draft; source=local_file |
| BIO-DATA-CHECK-RECOGNITION | Data Check & Preparation | `primaryButton` | connected | `runs_bio_preflight_or_gated_service` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_7zzxemrb/project/bio_batch_1_contract/logs/recognition/recognition_report.json |
| BIO-DATA-CHECK-READINESS | Data Check & Preparation | `bioinformaticsRunDataCheckButton` | connected | `runs_bio_preflight_or_gated_service` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_7zzxemrb/project/bio_batch_1_contract/logs/readiness/readiness_report.json |
| BIO-DATA-CHECK-STANDARDIZATION | Data Check & Preparation | `primaryButton` | connected | `writes_bio_project_draft_or_artifact` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_7zzxemrb/project/bio_batch_1_contract/manifests/standardized_assets_registry.json; /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_7zzxemrb/project/bio_batch_1_contract/standardized_data/analysis_ready_assets/analysis_ready_manifest.json; /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_7zzxemrb/project/bio_batch_1_contract/standardized_data/repositories/repository_manifest.json |
| BIO-ANALYSIS-FORMAL-DEG-CONFIRM | Analysis Tasks | `analysisTaskConfirmFormalDegParametersButton` | disabled | `writes_formal_deg_parameter_confirmation` | requires_formal_deg_parameter_manifest_and_dependency_snapshot |
| BIO-ANALYSIS-FORMAL-DEG-RUN | Analysis Tasks | `analysisTaskRunFormalControlledDegButton` | disabled | `runs_formal_controlled_deg_when_gate_passes` | requires_confirmed_formal_deg_gate |
| BIO-ANALYSIS-ENRICHMENT-OPEN | Analysis Tasks | `openEnrichmentGateButton` | connected | `opens_enrichment_preflight_gate_page` | current_page=bioinformaticsEnrichmentPage |
| BIO-ANALYSIS-ENRICHMENT-REPORT-GATE | Enrichment | `enrichmentNextDisabledButton` | disabled | `disabled_correlation_and_formal_gsea_not_connected` | formal_ora_gsea_execution_and_correlation_gate_not_enabled |
| BIO-ANALYSIS-ENRICHMENT-RUN | Enrichment | `runEnrichmentPreflightButton` | connected | `calls_enrichment_service_create_preflight_artifact` | /var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_7zzxemrb/projects/bio_batch_1_contract/bioinformatics/enrichment/geo_enrichment_preflight_ce7283fe7e0e.json |
| BIO-ANALYSIS-SURVIVAL-OPEN | Analysis Tasks | `openSurvivalClinicalGateButton` | connected | `opens_survival_clinical_preflight_gate_page` | current_page=bioinformaticsSurvivalPage |
| BIO-ANALYSIS-SURVIVAL-REPORT-GATE | Survival / Clinical | `survivalReportExportDisabledButton` | disabled | `disabled_survival_clinical_report_ready_not_connected` | km_cox_logrank_risk_score_and_clinical_report_ready_gate_not_enabled |
| BIO-ANALYSIS-SURVIVAL-RUN | Survival / Clinical | `runSurvivalPreflightButton` | connected | `calls_survival_service_create_preflight_artifact` | /var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_7zzxemrb/projects/bio_batch_1_contract/bioinformatics/survival/geo_survival_preflight_09e0a237e846.json |
| BIO-RESULT-REPORT-REFRESH | Result & Report | `resultReportRefreshButton` | connected | `calls_load_result_index_and_formal_deg_gates` | project_root=/private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_7zzxemrb/project/bio_batch_1_contract |
| BIO-REPORT-EXPORT-DRAFT | Report Export | `reportExportRefreshDraftButton` | connected | `generates_markdown_report_draft_only` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_7zzxemrb/project/bio_batch_1_contract/reports/project_analysis_report.md; /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_7zzxemrb/project/bio_batch_1_contract/reports/project_report_manifest.json |
| BIO-REPORT-EXPORT-REPORT-READY-GATE | Report Export | `reportReadyExportButton` | disabled | `exports_report_ready_package_when_gate_passes` | requires_report_ready_gate_passed |
