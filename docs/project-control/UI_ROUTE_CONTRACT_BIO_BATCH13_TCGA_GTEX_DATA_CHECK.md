# Bio C1 Batch 13 TCGA/GTEx Data Check Route Contract

- branch: `integration/release-bio-c1-ui-shell`
- head: `e837762525d2366934be6baf5ae9e730a1f8abaa`
- scope: Bioinformatics TCGA/GTEx light-validation build outputs into mature Data Check page: pre-recognition selection, recognition report, readiness report, and analysis capability matrix.
- rows: 5; connected: 5; disabled: 0; broken: 0

## Screenshots

- `01_tcga_built_source_ready`: `docs/ui/runtime_screenshots/20260602_bio_batch13_tcga_gtex_data_check/01_tcga_built_source_ready.png`
- `01_gtex_built_source_ready`: `docs/ui/runtime_screenshots/20260602_bio_batch13_tcga_gtex_data_check/01_gtex_built_source_ready.png`
- `02_data_check_tcga_gtex_selected`: `docs/ui/runtime_screenshots/20260602_bio_batch13_tcga_gtex_data_check/02_data_check_tcga_gtex_selected.png`
- `03_data_check_recognition_done`: `docs/ui/runtime_screenshots/20260602_bio_batch13_tcga_gtex_data_check/03_data_check_recognition_done.png`
- `04_readiness_before_run`: `docs/ui/runtime_screenshots/20260602_bio_batch13_tcga_gtex_data_check/04_readiness_before_run.png`
- `05_readiness_after_run`: `docs/ui/runtime_screenshots/20260602_bio_batch13_tcga_gtex_data_check/05_readiness_after_run.png`

## Rows

| contract | page | button | status | backend | evidence |
| --- | --- | --- | --- | --- | --- |
| BIO-B13-SETUP-TCGA-BUILD-SOURCE | data_source | `bioinformaticsTcgaBuildExpressionButton` | connected | app.bioinformatics.data_sources.tcga_expression_builder.TCGAExpressionQuantificationBuilder.build_from_record | standardized_data/tcga/tcga_thca/tcga_b64_48ece94a90/data_prepared/tcga/tcga_expression_build_manifest.json |
| BIO-B13-SETUP-GTEX-BUILD-SOURCE | data_source | `bioinformaticsGtexBuildExpressionButton` | connected | app.bioinformatics.data_sources.gtex_expression_builder.GTExExpressionMatrixBuilder.build_from_record | standardized_data/gtex/gtex_thyroid/gtex-g63-3d22b5ceb3/data_prepared/gtex/gtex_expression_build_manifest.json |
| BIO-B13-DATA-CHECK-PRE-INPUT-LIST | data_check_preparation | `preRecognitionInputList` | connected | app.bioinformatics.workflow_pages._pending_data_check_rows | preRecognitionInputList rows=2; contains TCGA and GTEx |
| BIO-B13-DATA-CHECK-RUN-RECOGNITION-TCGA-GTEX | data_check_preparation | `bioinformaticsRunRecognitionButton` | connected | app.bioinformatics.project_recognition.run_project_recognition_for_paths | logs/recognition/recognition_report.json; recognized_data/current.json; logs/recognition/group_preview_report.json; selected_input_count=12 |
| BIO-B13-DATA-CHECK-RUN-READINESS-TCGA-GTEX | data_check_preparation | `bioinformaticsRunDataCheckButton` | connected | app.bioinformatics.project_readiness.run_project_readiness | logs/readiness/readiness_report.json; manifests/analysis_capability_matrix.json; overall_status=ready_with_warnings |
