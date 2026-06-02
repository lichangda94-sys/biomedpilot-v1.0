# Bio C1 Batch 11 TCGA/GTEx Adapter Route Contract

- branch: `integration/release-bio-c1-ui-shell`
- head: `648ecbd9691d43d9114eb2056f358f5fc831bbb4`
- scope: Bioinformatics TCGA/GTEx light-validation Data Source adapter: visible source request, metadata preview, download-plan, limited download receipt, and expression build manifest.
- rows: 10; connected: 10; disabled: 0; broken: 0

## Screenshots

- `01_tcga_adapter_ready`: `docs/ui/runtime_screenshots/20260602_bio_batch12_tcga_gtex_light_validation/01_tcga_adapter_ready.png`
- `02_tcga_metadata_preview`: `docs/ui/runtime_screenshots/20260602_bio_batch12_tcga_gtex_light_validation/02_tcga_metadata_preview.png`
- `03_tcga_download_plan`: `docs/ui/runtime_screenshots/20260602_bio_batch12_tcga_gtex_light_validation/03_tcga_download_plan.png`
- `03a_tcga_light_download`: `docs/ui/runtime_screenshots/20260602_bio_batch12_tcga_gtex_light_validation/03a_tcga_light_download.png`
- `03b_tcga_expression_build`: `docs/ui/runtime_screenshots/20260602_bio_batch12_tcga_gtex_light_validation/03b_tcga_expression_build.png`
- `04_gtex_adapter_ready`: `docs/ui/runtime_screenshots/20260602_bio_batch12_tcga_gtex_light_validation/04_gtex_adapter_ready.png`
- `05_gtex_metadata_preview`: `docs/ui/runtime_screenshots/20260602_bio_batch12_tcga_gtex_light_validation/05_gtex_metadata_preview.png`
- `06_gtex_download_plan`: `docs/ui/runtime_screenshots/20260602_bio_batch12_tcga_gtex_light_validation/06_gtex_download_plan.png`
- `06a_gtex_light_download`: `docs/ui/runtime_screenshots/20260602_bio_batch12_tcga_gtex_light_validation/06a_gtex_light_download.png`
- `06b_gtex_expression_build`: `docs/ui/runtime_screenshots/20260602_bio_batch12_tcga_gtex_light_validation/06b_gtex_expression_build.png`

## Rows

| contract | source | button | status | backend | evidence | disabled reason |
| --- | --- | --- | --- | --- | --- | --- |
| BIO-B12-LIGHT-TCGA-SOURCE-REQUEST | TCGA | `bioinformaticsDataSourceSelectPreviewButton` | connected | app.bioinformatics.data_source_requests.create_data_source_request | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch11_tcga_gtex_yjpg7yqf/project/bio_batch_11_tcga_gtex_adapters/manifests/data_source_requests.json; request_id=dsr-447a126aaf; status=draft; so |  |
| BIO-B12-LIGHT-TCGA-METADATA-PREVIEW | TCGA | `bioinformaticsTcgaPreviewButton` | connected | app.bioinformatics.data_sources.tcga_preview.TCGAMetadataPreviewService.build_preview | TCGA preview：TCGA-THCA | case=507; sample=1562; file=564; size=2.23 GB | 下一步：生成下载计划草案。TCGA+GTEx 自动合并仍禁用。 |  |
| BIO-B12-LIGHT-TCGA-DOWNLOAD-PLAN | TCGA | `bioinformaticsTcgaCreatePlanButton` | connected | app.bioinformatics.data_sources.tcga_preview.write_tcga_download_plan_draft | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch11_tcga_gtex_yjpg7yqf/project/bio_batch_11_tcga_gtex_adapters/acquisition/tcga_download_plans/tcga-plan-1ada70992d.json |  |
| BIO-B12-LIGHT-TCGA-LIGHT-DOWNLOAD-GATE | TCGA | `bioinformaticsTcgaDownloadRawButton` | connected | app.bioinformatics.data_sources.tcga_download_executor.TCGADownloadPlanExecutor.execute_plan | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch11_tcga_gtex_yjpg7yqf/project/bio_batch_11_tcga_gtex_adapters/acquisition/download_receipts/tcga-dl-d8b2d7f3ed.json |  |
| BIO-B12-LIGHT-TCGA-EXPRESSION-BUILD-GATE | TCGA | `bioinformaticsTcgaBuildExpressionButton` | connected | app.bioinformatics.data_sources.tcga_expression_builder.TCGAExpressionQuantificationBuilder.build_from_record | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch11_tcga_gtex_yjpg7yqf/project/bio_batch_11_tcga_gtex_adapters/standardized_data/tcga/tcga_thca/tcga_b64_fb8ac713a4/data_prepared/tcga/tcga_exp |  |
| BIO-B12-LIGHT-GTEX-SOURCE-REQUEST | GTEx | `bioinformaticsDataSourceSelectPreviewButton` | connected | app.bioinformatics.data_source_requests.create_data_source_request | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch11_tcga_gtex_yjpg7yqf/project/bio_batch_11_tcga_gtex_adapters/manifests/data_source_requests.json; request_id=dsr-a7675f10f9; status=draft; so |  |
| BIO-B12-LIGHT-GTEX-METADATA-PREVIEW | GTEx | `bioinformaticsGtexPreviewButton` | connected | app.bioinformatics.data_sources.gtex_preview.GTExMetadataPreviewService.build_preview | GTEx preview：甲状腺 (Thyroid) | donor=574; sample=653; file=1 | GTEx 不自动作为 TCGA normal control。 |  |
| BIO-B12-LIGHT-GTEX-DOWNLOAD-PLAN | GTEx | `bioinformaticsGtexCreatePlanButton` | connected | app.bioinformatics.data_sources.gtex_preview.write_gtex_download_plan_draft | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch11_tcga_gtex_yjpg7yqf/project/bio_batch_11_tcga_gtex_adapters/acquisition/gtex_download_plans/gtex-plan-0dae0b5a7c.json |  |
| BIO-B12-LIGHT-GTEX-LIGHT-DOWNLOAD-GATE | GTEx | `bioinformaticsGtexDownloadRawButton` | connected | app.bioinformatics.data_sources.gtex_download_executor.GTExDownloadPlanExecutor.execute_plan | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch11_tcga_gtex_yjpg7yqf/project/bio_batch_11_tcga_gtex_adapters/acquisition/download_receipts/gtex-dl-3b4867883e.json |  |
| BIO-B12-LIGHT-GTEX-EXPRESSION-BUILD-GATE | GTEx | `bioinformaticsGtexBuildExpressionButton` | connected | app.bioinformatics.data_sources.gtex_expression_builder.GTExExpressionMatrixBuilder.build_from_record | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch11_tcga_gtex_yjpg7yqf/project/bio_batch_11_tcga_gtex_adapters/standardized_data/gtex/gtex_thyroid/gtex-g63-810abcd0d1/data_prepared/gtex/gtex_ |  |
