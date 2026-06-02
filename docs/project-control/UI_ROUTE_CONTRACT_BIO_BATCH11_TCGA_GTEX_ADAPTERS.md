# Bio C1 Batch 11 TCGA/GTEx Adapter Route Contract

- branch: `integration/release-bio-c1-ui-shell`
- head: `4a0577982b6c87645f6d1a0bac0adbd56728f7b0`
- scope: Bioinformatics mature Data Source visible TCGA/GTEx adapters: source request, metadata preview, download-plan artifact, and explicit disabled gates for download/build.
- rows: 10; connected: 6; disabled: 4; broken: 0

## Screenshots

- `01_tcga_adapter_ready`: `docs/ui/runtime_screenshots/20260602_bio_batch11_tcga_gtex_adapters/01_tcga_adapter_ready.png`
- `02_tcga_metadata_preview`: `docs/ui/runtime_screenshots/20260602_bio_batch11_tcga_gtex_adapters/02_tcga_metadata_preview.png`
- `03_tcga_download_plan`: `docs/ui/runtime_screenshots/20260602_bio_batch11_tcga_gtex_adapters/03_tcga_download_plan.png`
- `03a_tcga_light_download`: `docs/ui/runtime_screenshots/20260602_bio_batch11_tcga_gtex_adapters/03a_tcga_light_download.png`
- `03b_tcga_expression_build`: `docs/ui/runtime_screenshots/20260602_bio_batch11_tcga_gtex_adapters/03b_tcga_expression_build.png`
- `04_gtex_adapter_ready`: `docs/ui/runtime_screenshots/20260602_bio_batch11_tcga_gtex_adapters/04_gtex_adapter_ready.png`
- `05_gtex_metadata_preview`: `docs/ui/runtime_screenshots/20260602_bio_batch11_tcga_gtex_adapters/05_gtex_metadata_preview.png`
- `06_gtex_download_plan`: `docs/ui/runtime_screenshots/20260602_bio_batch11_tcga_gtex_adapters/06_gtex_download_plan.png`
- `06a_gtex_light_download`: `docs/ui/runtime_screenshots/20260602_bio_batch11_tcga_gtex_adapters/06a_gtex_light_download.png`
- `06b_gtex_expression_build`: `docs/ui/runtime_screenshots/20260602_bio_batch11_tcga_gtex_adapters/06b_gtex_expression_build.png`

## Rows

| contract | source | button | status | backend | evidence | disabled reason |
| --- | --- | --- | --- | --- | --- | --- |
| BIO-B11-TCGA-SOURCE-REQUEST | TCGA | `bioinformaticsDataSourceSelectPreviewButton` | connected | app.bioinformatics.data_source_requests.create_data_source_request | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch11_tcga_gtex_nlk9fmht/project/bio_batch_11_tcga_gtex_adapters/manifests/data_source_requests.json; request_id=dsr-a8fff7bde2; status=draft; so |  |
| BIO-B11-TCGA-METADATA-PREVIEW | TCGA | `bioinformaticsTcgaPreviewButton` | connected | app.bioinformatics.data_sources.tcga_preview.TCGAMetadataPreviewService.build_preview | TCGA preview：TCGA-THCA | case=507; sample=1562; file=564; size=2.23 GB | 下一步：生成下载计划草案。TCGA+GTEx 自动合并仍禁用。 |  |
| BIO-B11-TCGA-DOWNLOAD-PLAN | TCGA | `bioinformaticsTcgaCreatePlanButton` | connected | app.bioinformatics.data_sources.tcga_preview.write_tcga_download_plan_draft | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch11_tcga_gtex_nlk9fmht/project/bio_batch_11_tcga_gtex_adapters/acquisition/tcga_download_plans/tcga-plan-c97f53bb9a.json |  |
| BIO-B11-TCGA-LIGHT-DOWNLOAD-GATE | TCGA | `bioinformaticsTcgaDownloadRawButton` | disabled | app.bioinformatics.data_sources.tcga_download_executor.TCGADownloadPlanExecutor.execute_plan | requires_tcga_download_plan_and_light_validation_gate | requires_tcga_download_plan_and_light_validation_gate |
| BIO-B11-TCGA-EXPRESSION-BUILD-GATE | TCGA | `bioinformaticsTcgaBuildExpressionButton` | disabled | app.bioinformatics.data_sources.tcga_expression_builder.TCGAExpressionQuantificationBuilder.build_from_record | requires_tcga_raw_download_receipt | requires_tcga_raw_download_receipt |
| BIO-B11-GTEX-SOURCE-REQUEST | GTEx | `bioinformaticsDataSourceSelectPreviewButton` | connected | app.bioinformatics.data_source_requests.create_data_source_request | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch11_tcga_gtex_nlk9fmht/project/bio_batch_11_tcga_gtex_adapters/manifests/data_source_requests.json; request_id=dsr-78a6845a58; status=draft; so |  |
| BIO-B11-GTEX-METADATA-PREVIEW | GTEx | `bioinformaticsGtexPreviewButton` | connected | app.bioinformatics.data_sources.gtex_preview.GTExMetadataPreviewService.build_preview | GTEx preview：甲状腺 (Thyroid) | donor=574; sample=653; file=0 | GTEx 不自动作为 TCGA normal control。 |  |
| BIO-B11-GTEX-DOWNLOAD-PLAN | GTEx | `bioinformaticsGtexCreatePlanButton` | connected | app.bioinformatics.data_sources.gtex_preview.write_gtex_download_plan_draft | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch11_tcga_gtex_nlk9fmht/project/bio_batch_11_tcga_gtex_adapters/acquisition/gtex_download_plans/gtex-plan-b71bc2f23e.json |  |
| BIO-B11-GTEX-LIGHT-DOWNLOAD-GATE | GTEx | `bioinformaticsGtexDownloadRawButton` | disabled | app.bioinformatics.data_sources.gtex_download_executor.GTExDownloadPlanExecutor.execute_plan | requires_gtex_download_plan_and_light_validation_gate | requires_gtex_download_plan_and_light_validation_gate |
| BIO-B11-GTEX-EXPRESSION-BUILD-GATE | GTEx | `bioinformaticsGtexBuildExpressionButton` | disabled | app.bioinformatics.data_sources.gtex_expression_builder.GTExExpressionMatrixBuilder.build_from_record | requires_gtex_raw_download_receipt | requires_gtex_raw_download_receipt |
