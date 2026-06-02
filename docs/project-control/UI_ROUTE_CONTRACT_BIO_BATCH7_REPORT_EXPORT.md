# UI Route Contract: Bio Batch 7 Result & Report / Report Export

- branch: `integration/release-bio-c1-ui-shell`
- head: `e837762525d2366934be6baf5ae9e730a1f8abaa`
- scope: Bioinformatics Result & Report and Report Export cross-result gate: Formal DEG positive path, report draft, report-ready package export, and ORA/GSEA/Survival boundary proof.
- rows: 13
- connected: 13
- disabled: 0
- broken: 0

## Screenshots

- `docs/ui/runtime_screenshots/20260602_bio_batch7_report_export/01_result_report_cross_gate.png`
- `docs/ui/runtime_screenshots/20260602_bio_batch7_report_export/02_report_export_formal_only_gate.png`

## Route Rows

| Contract | Object | Status | Behavior | Evidence | Observed |
| --- | --- | --- | --- | --- | --- |
| BIO-REPORT-X-FORMAL-DEG-CONFIRM | `analysisTaskConfirmFormalDegParametersButton` | connected | `writes_formal_deg_parameter_confirmation` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch7_report_export_gorvnjs9/project/bio_batch_4_formal_deg/manifests/formal_deg_parameter_confirmation.json | confirmation_exists=True; run_enabled=True |
| BIO-REPORT-X-FORMAL-DEG-RUN | `analysisTaskRunFormalControlledDegButton` | connected | `runs_formal_controlled_deg_when_gate_passes` | formal_entry_count=1 | result_ids=formal-deg-42517c8756 |
| BIO-REPORT-X-ENRICHMENT-PREFLIGHT-BOUNDARY | `EnrichmentService.create_preflight` | connected | `direct_service_call_boundary_fixture` | /var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch7_report_export_gorvnjs9/projects/bio_batch_4_formal_deg/bioinformatics/enrichment/geo_enrichment_preflight_83a0796640e5.json | enrichment_executed=False; database_download_executed=False |
| BIO-REPORT-X-SURVIVAL-PREFLIGHT-BOUNDARY | `SurvivalService.create_preflight` | connected | `direct_service_call_boundary_fixture` | /var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch7_report_export_gorvnjs9/projects/bio_batch_4_formal_deg/bioinformatics/survival/geo_survival_preflight_40309628dc20.json | survival_analysis_executed=False |
| BIO-RESULT-REPORT-REFRESH-CROSS-GATE | `resultReportRefreshButton` | connected | `calls_load_result_index_and_formal_deg_gates` | formal=1; enrichment=0; survival=0 | entry_count=1 |
| BIO-RESULT-FORMAL-DEG-REVIEW-TSV-EXPORT | `formalDegReviewExportTsvButton` | connected | `exports_formal_deg_review_table_when_gate_passes` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch7_report_export_gorvnjs9/project/bio_batch_4_formal_deg/results/exports/formal_deg_review/formal-deg-42517c8756_review.tsv | export_count=1 |
| BIO-RESULT-FORMAL-DEG-REVIEW-CSV-EXPORT | `formalDegReviewExportCsvButton` | connected | `exports_formal_deg_review_table_when_gate_passes` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch7_report_export_gorvnjs9/project/bio_batch_4_formal_deg/results/exports/formal_deg_review/formal-deg-42517c8756_review.csv | export_count=1 |
| BIO-RESULT-FORMAL-DEG-PLOT-GATE | `formalDegPlotButton` | connected | `creates_formal_deg_plot_artifact_when_gate_passes` | plot_artifact_count=1 | volcano_plot |
| BIO-RESULT-FORMAL-DEG-REPORT-READY-PACKAGE | `formalDegReportReadyButton` | connected | `creates_formal_deg_report_ready_package_when_gate_passes` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch7_report_export_gorvnjs9/project/bio_batch_4_formal_deg/report_package/formal_deg/formal-deg-42517c8756/20260602T142903Z/formal_deg_report_package_manifest.json | section_scope=formal_deg_only; gsea=False; survival=False; clinical=False |
| BIO-RESULT-CONTINUE-REPORT-EXPORT | `resultReportContinueReportExportButton` | connected | `opens_report_export_gate_when_result_exists` | signal=continue_requested | continue_signal=True |
| BIO-REPORT-EXPORT-DRAFT-CROSS-GATE | `reportExportRefreshDraftButton` | connected | `generates_markdown_report_draft_only` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch7_report_export_gorvnjs9/project/bio_batch_4_formal_deg/reports/project_analysis_report.md; /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch7_report_export_gorvnjs9/project/bio_batch_4_formal_deg/reports/project_report_manifest.json | included_result_ids=[] |
| BIO-REPORT-EXPORT-FORMAL-DEG-PACKAGE-GATE | `reportReadyExportButton` | connected | `exports_report_ready_package_when_gate_passes` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch7_report_export_gorvnjs9/project/bio_batch_4_formal_deg/report_package/formal_deg/formal-deg-42517c8756/20260602T142904Z/formal_deg_report_package_manifest.json | enabled=True; status_message=已导出 formal DEG report-ready package；输出位置：/private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch7_report_export_gorvnjs9/project/bio_batch_4_formal_deg/report_package/formal_deg/formal-deg-42517c8756/20260602T142904Z；GSEA、survival、clinical report-ready 仍保持 gate。 |
| BIO-REPORT-EXPORT-GENERIC-GATE-SNAPSHOT | `evaluate_report_ready_gate` | connected | `direct_gate_snapshot` | status=eligible_for_internal_report; included=['formal-deg-42517c8756'] | blockers=[] |
