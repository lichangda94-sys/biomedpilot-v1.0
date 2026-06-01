# UI Route Contract: Bio Batch 5 Enrichment ORA/GSEA

- branch: `integration/release-bio-c1-ui-shell`
- head: `ff04c440a4c9ef108f2fbf9bf77fb7271e988d8a`
- scope: Bioinformatics ORA/GSEA enrichment input gate, R backend capability detection, formal execution disabled gates, result review, plot, and report-ready gates.
- rows: 9
- connected: 4
- disabled: 5
- broken: 0

## Screenshots

- `docs/ui/runtime_screenshots/20260602_bio_batch5_enrichment/01_enrichment_ora_gsea_gate.png`

## Route Rows

| Contract | Object | Status | Behavior | Evidence | Observed |
| --- | --- | --- | --- | --- | --- |
| BIO-ENRICHMENT-BACK | `enrichmentBackButton` | connected | `navigates_back_to_analysis_tasks` | signal=back_requested | back_signal=True |
| BIO-ENRICHMENT-CHOOSE-DEG-PREFLIGHT | `chooseEnrichmentPreflightButton` | connected | `selects_deg_preflight_manifest_json` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch5_enrichment_66iwymex/project/bio_batch_5_enrichment/analysis/deg/preflight/deg_preflight_manifest.json | path_input=/private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch5_enrichment_66iwymex/project/bio_batch_5_enrichment/analysis/deg/preflight/deg_preflight_manifest.json |
| BIO-ENRICHMENT-RUN-PREFLIGHT | `runEnrichmentPreflightButton` | connected | `calls_enrichment_service_create_preflight_artifact` | /var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch5_enrichment_66iwymex/projects/bio_batch_5_enrichment/bioinformatics/enrichment/geo_enrichment_preflight_c1c9baa43f04.json | enrichment_executed=False; database_download_executed=False |
| BIO-ENRICHMENT-DETECT-R-BACKEND | `detectBioEnrichmentRBackendButton` | connected | `calls_enrichment_service_detect_r_backend` | status=available; ReactomePA: available=True version=1.50.0 disabled_reason=none; msigdbr: available=True version=26.1.0 disabled_reason=none; blockers=none | status=available |
| BIO-ENRICHMENT-CONFIRM-ORA-GSEA-PARAMETERS-GATE | `confirmOraGseaParametersDisabledButton` | disabled | `disabled_ora_gsea_parameter_confirmation_not_ready` | formal_ora_gsea_parameter_confirmation_requires_backend_and_result_schema | enabled=False; disabledReason=formal_ora_gsea_parameter_confirmation_requires_backend_and_result_schema |
| BIO-ENRICHMENT-RUN-FORMAL-ORA-GSEA-GATE | `runFormalOraGseaDisabledButton` | disabled | `disabled_formal_ora_gsea_executor_not_connected` | formal_ora_gsea_executor_not_connected | enabled=False; disabledReason=formal_ora_gsea_executor_not_connected |
| BIO-ENRICHMENT-REVIEW-RESULTS-GATE | `reviewOraGseaResultsDisabledButton` | disabled | `disabled_ora_gsea_result_review_without_result_index` | ora_gsea_result_index_not_available | enabled=False; disabledReason=ora_gsea_result_index_not_available |
| BIO-ENRICHMENT-PLOT-REPORT-GATE | `oraGseaPlotReportDisabledButton` | disabled | `disabled_ora_gsea_plot_report_gate_not_enabled` | ora_gsea_plot_and_report_ready_gate_not_enabled | enabled=False; disabledReason=ora_gsea_plot_and_report_ready_gate_not_enabled |
| BIO-ENRICHMENT-CORRELATION-NEXT-GATE | `enrichmentNextDisabledButton` | disabled | `disabled_correlation_and_formal_gsea_not_connected` | formal_ora_gsea_execution_and_correlation_gate_not_enabled | enabled=False; disabledReason=formal_ora_gsea_execution_and_correlation_gate_not_enabled |
