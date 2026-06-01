# UI Route Contract Bio Batch 4: Formal DEG

- Created: `2026-06-01T15:57:12.231052+00:00`
- Branch: `integration/release-bio-c1-ui-shell`
- HEAD: `357576cb04a8a53c7e85557403c8710ab2021774`
- Scope: Bioinformatics Formal DEG positive runtime path: dependency detect, parameter confirmation, controlled run, result review, plot, report-ready package, and report export gate.

## Summary

- Rows: 8
- Connected: 8
- Disabled with reason: 0
- Broken: 0

## Rows

| Contract | Surface | Object | Status | Behavior | Evidence |
| --- | --- | --- | --- | --- | --- |
| BIO-FORMAL-DEG-DEPENDENCY-DETECT | Analysis Tasks | `check_deg_backend_dependencies` | connected | `detect_first_no_install` | status=passed; packages=numpy,pandas,scipy,statsmodels |
| BIO-FORMAL-DEG-PARAMETER-CONFIRM | Analysis Tasks | `analysisTaskConfirmFormalDegParametersButton` | connected | `writes_formal_deg_parameter_confirmation` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch4_formal_deg_ukerydp4/project/bio_batch_4_formal_deg/manifests/formal_deg_parameter_confirmation.json |
| BIO-FORMAL-DEG-CONTROLLED-RUN | Analysis Tasks | `analysisTaskRunFormalControlledDegButton` | connected | `runs_formal_controlled_deg_when_gate_passes` | result_id=formal-deg-da3531d4bf; result_table=/private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch4_formal_deg_ukerydp4/project/bio_batch_4_formal_deg/results/tables/formal-deg-da3531d4bf.tsv; result_index=/private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch4_formal_deg_ukerydp4/project/bio_batch_4_formal_deg/results/summaries/result_index.json |
| BIO-FORMAL-DEG-RESULT-REVIEW | Result & Report | `resultReportRefreshButton` | connected | `calls_load_result_index_and_formal_deg_gates` | selected_result_id=formal-deg-da3531d4bf |
| BIO-FORMAL-DEG-REVIEW-CSV-EXPORT | Result & Report | `formalDegReviewExportCsvButton` | connected | `exports_formal_deg_review_table_when_gate_passes` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch4_formal_deg_ukerydp4/project/bio_batch_4_formal_deg/results/exports/formal_deg_review/formal-deg-da3531d4bf_review.csv |
| BIO-FORMAL-DEG-PLOT-ARTIFACT | Result & Report | `formalDegPlotButton` | connected | `creates_formal_deg_plot_artifact_when_gate_passes` | formal-deg-da3531d4bf-volcano_plot-artifact |
| BIO-FORMAL-DEG-REPORT-READY-PACKAGE | Result & Report | `formalDegReportReadyButton` | connected | `creates_formal_deg_report_ready_package_when_gate_passes` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch4_formal_deg_ukerydp4/project/bio_batch_4_formal_deg/report_package/formal_deg/formal-deg-da3531d4bf/20260601T155709Z/formal_deg_report_package_manifest.json |
| BIO-FORMAL-DEG-REPORT-EXPORT-GATE | Report Export | `reportReadyExportButton` | connected | `exports_report_ready_package_when_gate_passes` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch4_formal_deg_ukerydp4/project/bio_batch_4_formal_deg/report_package/formal_deg/formal-deg-da3531d4bf/20260601T155709Z_2/formal_deg_report_package_manifest.json |

## Screenshots

- `01_analysis_tasks_formal_deg_ready.png`: bioinformatics
- `02_result_review_formal_deg.png`: bioinformatics
- `03_result_review_plot_gate.png`: bioinformatics
- `04_report_export_formal_deg_ready.png`: bioinformatics
