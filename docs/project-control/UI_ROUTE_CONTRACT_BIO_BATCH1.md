# UI Route Contract Bio Batch 1

- Created: `2026-06-02T14:28:23.909952+00:00`
- Branch: `integration/release-bio-c1-ui-shell`
- HEAD: `e837762525d2366934be6baf5ae9e730a1f8abaa`
- Scope: Bioinformatics mature 7-step gated UI shell adapter and first-level runtime gate audit.

## Summary

- Rows: 27
- Connected: 22
- Disabled with reason: 5
- Broken: 0

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
| BIO-DATA-SOURCE-GEO | Data Source | `bioinformaticsDataSourceSelectPreviewButton` | connected | `creates_data_source_request_draft_when_project_open` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_sheekm0r/project/bio_batch_1_contract/manifests/data_source_requests/dsr-7ab079ca85.json; status=draft; source=geo |
| BIO-DATA-SOURCE-TCGA | Data Source | `bioinformaticsDataSourceSelectPreviewButton` | connected | `creates_data_source_request_draft_when_project_open` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_sheekm0r/project/bio_batch_1_contract/manifests/data_source_requests/dsr-a5c0142373.json; status=draft; source=tcga |
| BIO-DATA-SOURCE-GTEX | Data Source | `bioinformaticsDataSourceSelectPreviewButton` | connected | `creates_data_source_request_draft_when_project_open` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_sheekm0r/project/bio_batch_1_contract/manifests/data_source_requests/dsr-cda835c8be.json; status=draft; source=gtex |
| BIO-DATA-SOURCE-LOCAL_FILE | Data Source | `bioinformaticsDataSourceSelectPreviewButton` | connected | `creates_data_source_request_draft_when_project_open` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_sheekm0r/project/bio_batch_1_contract/manifests/data_source_requests/dsr-2a9ec4514c.json; status=draft; source=local_file |
| BIO-DATA-CHECK-RECOGNITION | Data Check & Preparation | `bioinformaticsRunRecognitionButton` | connected | `runs_bio_preflight_or_gated_service` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_sheekm0r/project/bio_batch_1_contract/logs/recognition/recognition_report.json |
| BIO-DATA-CHECK-READINESS | Data Check & Preparation | `bioinformaticsRunDataCheckButton` | connected | `runs_bio_preflight_or_gated_service` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_sheekm0r/project/bio_batch_1_contract/logs/readiness/readiness_report.json |
| BIO-DATA-CHECK-STANDARDIZATION | Data Check & Preparation | `primaryButton` | connected | `writes_bio_project_draft_or_artifact` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_sheekm0r/project/bio_batch_1_contract/manifests/standardized_assets_registry.json; /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_sheekm0r/project/bio_batch_1_contract/standardized_data/analysis_ready_assets/analysis_ready_manifest.json; /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_sheekm0r/project/bio_batch_1_contract/standardized_data/repositories/repository_manifest.json |
| BIO-ANALYSIS-FORMAL-DEG-CONFIRM | Analysis Tasks | `analysisTaskConfirmFormalDegParametersButton` | disabled | `writes_formal_deg_parameter_confirmation` | requires_formal_deg_parameter_manifest_and_dependency_snapshot |
| BIO-ANALYSIS-FORMAL-DEG-RUN | Analysis Tasks | `analysisTaskRunFormalControlledDegButton` | disabled | `runs_formal_controlled_deg_when_gate_passes` | requires_confirmed_formal_deg_gate |
| BIO-ANALYSIS-ENRICHMENT-OPEN | Analysis Tasks | `openEnrichmentGateButton` | connected | `opens_enrichment_preflight_gate_page` | current_page=bioinformaticsEnrichmentPage |
| BIO-ANALYSIS-ENRICHMENT-REPORT-GATE | Enrichment | `enrichmentNextDisabledButton` | disabled | `disabled_correlation_and_formal_gsea_not_connected` | formal_gsea_execution_and_correlation_gate_not_enabled |
| BIO-ANALYSIS-ENRICHMENT-RUN | Enrichment | `runEnrichmentPreflightButton` | connected | `calls_enrichment_service_create_preflight_artifact` | /var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_sheekm0r/projects/bio_batch_1_contract/bioinformatics/enrichment/geo_enrichment_preflight_145dfdca04c8.json |
| BIO-ANALYSIS-SURVIVAL-OPEN | Analysis Tasks | `openSurvivalClinicalGateButton` | connected | `opens_survival_clinical_preflight_gate_page` | current_page=bioinformaticsSurvivalPage |
| BIO-ANALYSIS-SURVIVAL-REPORT-GATE | Survival / Clinical | `survivalReportExportDisabledButton` | disabled | `disabled_survival_clinical_report_ready_not_connected` | survival_clinical_report_ready_requires_km_logrank_cox_risk_score_results_and_gate |
| BIO-ANALYSIS-SURVIVAL-RUN | Survival / Clinical | `runSurvivalPreflightButton` | connected | `calls_survival_service_create_preflight_artifact` | /var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_sheekm0r/projects/bio_batch_1_contract/bioinformatics/survival/geo_survival_preflight_0479ea635736.json |
| BIO-RESULT-REPORT-REFRESH | Result & Report | `resultReportRefreshButton` | connected | `calls_load_result_index_and_formal_deg_gates` | project_root=/private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_sheekm0r/project/bio_batch_1_contract |
| BIO-REPORT-EXPORT-DRAFT | Report Export | `reportExportRefreshDraftButton` | connected | `generates_markdown_report_draft_only` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_sheekm0r/project/bio_batch_1_contract/reports/project_analysis_report.md; /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch1_sheekm0r/project/bio_batch_1_contract/reports/project_report_manifest.json |
| BIO-REPORT-EXPORT-REPORT-READY-GATE | Report Export | `reportReadyExportButton` | disabled | `exports_report_ready_package_when_gate_passes` | requires_report_ready_gate_passed |
