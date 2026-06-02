# UI Route Contract: Bio Batch 5 Enrichment ORA/GSEA

- branch: `integration/release-bio-c1-ui-shell`
- head: `e837762525d2366934be6baf5ae9e730a1f8abaa`
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
| BIO-ENRICHMENT-CHOOSE-DEG-PREFLIGHT | `chooseEnrichmentPreflightButton` | connected | `selects_deg_preflight_manifest_json` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch5_enrichment_x29ucphz/project/bio_batch_5_enrichment/analysis/deg/preflight/deg_preflight_manifest.json | path_input=/private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch5_enrichment_x29ucphz/project/bio_batch_5_enrichment/analysis/deg/preflight/deg_preflight_manifest.json |
| BIO-ENRICHMENT-RUN-PREFLIGHT | `runEnrichmentPreflightButton` | connected | `calls_enrichment_service_create_preflight_artifact` | /var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch5_enrichment_x29ucphz/projects/bio_batch_5_enrichment/bioinformatics/enrichment/geo_enrichment_preflight_c93c01d9ed2f.json | enrichment_executed=False; database_download_executed=False |
| BIO-ENRICHMENT-DETECT-R-BACKEND | `detectBioEnrichmentRBackendButton` | connected | `calls_enrichment_service_detect_r_backend` | status=available; ReactomePA: available=True version=1.50.0 disabled_reason=none; msigdbr: available=True version=26.1.0 disabled_reason=none; blockers=none | status=available |
| BIO-ENRICHMENT-CONFIRM-GSEA-PARAMETERS-GATE | `confirmOraGseaParametersDisabledButton` | disabled | `disabled_gsea_parameter_confirmation_not_ready` | formal_gsea_parameter_confirmation_requires_ranked_gene_list_gene_set_backend_and_result_schema | enabled=False; disabledReason=formal_gsea_parameter_confirmation_requires_ranked_gene_list_gene_set_backend_and_result_schema |
| BIO-ENRICHMENT-RUN-FORMAL-GSEA-GATE | `runFormalOraGseaDisabledButton` | disabled | `disabled_formal_gsea_executor_not_connected` | formal_gsea_executor_requires_fgsea_or_clusterprofiler_ranked_gene_list_and_gene_set_schema | enabled=False; disabledReason=formal_gsea_executor_requires_fgsea_or_clusterprofiler_ranked_gene_list_and_gene_set_schema |
| BIO-ENRICHMENT-REVIEW-GSEA-RESULTS-GATE | `reviewOraGseaResultsDisabledButton` | disabled | `disabled_gsea_result_review_without_result_index` | gsea_result_index_not_available | enabled=False; disabledReason=gsea_result_index_not_available |
| BIO-ENRICHMENT-PLOT-REPORT-GATE | `oraGseaPlotReportDisabledButton` | disabled | `disabled_ora_gsea_plot_report_gate_not_enabled` | ora_plot_gsea_plot_and_report_ready_gate_not_enabled | enabled=False; disabledReason=ora_plot_gsea_plot_and_report_ready_gate_not_enabled |
| BIO-ENRICHMENT-CORRELATION-NEXT-GATE | `enrichmentNextDisabledButton` | disabled | `disabled_correlation_and_formal_gsea_not_connected` | formal_gsea_execution_and_correlation_gate_not_enabled | enabled=False; disabledReason=formal_gsea_execution_and_correlation_gate_not_enabled |
