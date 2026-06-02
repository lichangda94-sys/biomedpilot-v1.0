# UI Route Contract: Bio Batch 14 Formal ORA

- branch: `integration/release-bio-c1-ui-shell`
- head: `4a0577982b6c87645f6d1a0bac0adbd56728f7b0`
- scope: Bioinformatics formal ORA positive runtime path from mature Enrichment page: DEG preflight selection, GMT selection, local ORA execution, result review, artifact registry, and GSEA/report gates.
- rows: 7
- connected: 4
- disabled: 3
- broken: 0

## Screenshots

- `docs/ui/runtime_screenshots/20260602_bio_batch14_formal_ora/01_formal_ora_inputs_ready.png`
- `docs/ui/runtime_screenshots/20260602_bio_batch14_formal_ora/02_formal_ora_result_review.png`

## Route Rows

| Contract | Object | Status | Behavior | Evidence | Observed |
| --- | --- | --- | --- | --- | --- |
| BIO-FORMAL-ORA-CHOOSE-DEG-PREFLIGHT | `chooseEnrichmentPreflightButton` | connected | `selects_deg_preflight_manifest_json` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch14_formal_ora_s3luhbwx/project/bio_batch_14_formal_ora/analysis/deg/preflight/deg_preflight_manifest.json | path_input=/private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch14_formal_ora_s3luhbwx/project/bio_batch_14_formal_ora/analysis/deg/preflight/deg_preflight_manifest.json |
| BIO-FORMAL-ORA-CHOOSE-GMT | `chooseFormalOraGeneSetButton` | connected | `selects_local_gmt_gene_set_for_formal_ora` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch14_formal_ora_s3luhbwx/project/bio_batch_14_formal_ora/user_data/bioinformatics/gene_sets/batch14_pathways.gmt | gene_set_input=/private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch14_formal_ora_s3luhbwx/project/bio_batch_14_formal_ora/user_data/bioinformatics/gene_sets/batch14_pathways.gmt |
| BIO-FORMAL-ORA-RUN | `runFormalOraButton` | connected | `calls_enrichment_service_run_formal_ora_with_local_gmt` | json=/private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch14_formal_ora_s3luhbwx/project/bio_batch_14_formal_ora/results/enrichment/formal-ora-f883281e48.json; csv=/private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch14_formal_ora_s3luhbwx/project/bio_batch_14_formal_ora/results/enrichment/formal-ora-f883281e48.csv; result_index=/private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch14_formal_ora_s3luhbwx/project/bio_batch_14_formal_ora/results/summaries/result_index.json | formal_ora_executed=True; term_count=3 |
| BIO-FORMAL-ORA-REVIEW-AND-REGISTRY | `formalOraResultReviewText` | connected | `renders_formal_ora_result_review_after_run` | tasks=/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch14_formal_ora_s3luhbwx/formal_ora_tasks.json; assets=/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch14_formal_ora_s3luhbwx/formal_ora_assets.json | result_id=formal-ora-f883281e48 |
| BIO-FORMAL-GSEA-RUN-GATE | `runFormalOraGseaDisabledButton` | disabled | `disabled_formal_gsea_executor_not_connected` | formal_gsea_executor_requires_fgsea_or_clusterprofiler_ranked_gene_list_and_gene_set_schema | enabled=False; disabledReason=formal_gsea_executor_requires_fgsea_or_clusterprofiler_ranked_gene_list_and_gene_set_schema |
| BIO-FORMAL-ORA-PLOT-REPORT-GATE | `oraGseaPlotReportDisabledButton` | disabled | `disabled_ora_gsea_plot_report_gate_not_enabled` | ora_plot_gsea_plot_and_report_ready_gate_not_enabled | enabled=False; disabledReason=ora_plot_gsea_plot_and_report_ready_gate_not_enabled |
| BIO-FORMAL-ORA-CORRELATION-NEXT-GATE | `enrichmentNextDisabledButton` | disabled | `disabled_correlation_and_formal_gsea_not_connected` | formal_gsea_execution_and_correlation_gate_not_enabled | enabled=False; disabledReason=formal_gsea_execution_and_correlation_gate_not_enabled |
