# Bioinformatics Batch 10 GEO Online Retrieval Route Contract

- branch: `integration/release-bio-c1-ui-shell`
- head: `e837762525d2366934be6baf5ae9e730a1f8abaa`
- accessions: `GSE6004, GSE153659`
- row_count: `18`
- connected: `18`
- disabled: `0`
- broken: `0`

## Rows

| contract | accession | page | object | label | status | backend capability | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `BIO-B10-GSE6004-CONFIGURE-GEO-SOURCE` | `GSE6004` | `data_source` | `bioinformaticsDataSourceSelectPreviewButton` | 配置 GEO 来源 | `connected` | `app.bioinformatics.data_source_requests.create_data_source_request` | bio_batch_10_gse6004/manifests/data_source_requests.json |
| `BIO-B10-GSE6004-SEARCH-GEO-METADATA` | `GSE6004` | `data_source` | `bioinformaticsGeoSearchMetadataButton` | 检索元数据 | `connected` | `app.bioinformatics.legacy.geo_tool.geo_info_fetcher.GeoInfoFetcher.search_series` | GSE：GSE6004
标题：Gene Expression and Functional Evidence of Epithelial-to-Mesenchymal Transition in Papillary Thyroid Cancer Invasion
平台：570
样本数：18
下一步：加入项目后下载 GEO 元数据。 |
| `BIO-B10-GSE6004-ADD-GEO-ACCESSION` | `GSE6004` | `data_source` | `bioinformaticsGeoAddToProjectButton` | 加入项目 | `connected` | `app.bioinformatics.project_workspace_binding.register_acquisition` | acquisition/handoffs/acq-ed4c31a2.json; acquisition/handoffs/latest_acquisition_handoff.json; acquisition/plans/acq-ed4c31a2.json; acquisition/plans/latest_acquisition_plan.json; acquisition/records/acq-ed4c31a2.json; acquisition/records/latest_acquisition_record.json |
| `BIO-B10-GSE6004-DOWNLOAD-GEO-METADATA` | `GSE6004` | `data_source` | `bioinformaticsGeoDownloadMetadataButton` | 下载 GEO 元数据 | `connected` | `app.bioinformatics.download.DatasetDownloadService.create_candidate_download_task` | raw_data/geo/GSE6004/GSE6004_family.soft.gz; raw_data/geo/GSE6004/GSE6004_asset_manifest.json; acquisition/download_receipts/dl-5ea5f18c0e.json |
| `BIO-B10-GSE6004-DOWNLOAD-GEO-ASSETS` | `GSE6004` | `data_source` | `bioinformaticsGeoDownloadAssetsButton` | 下载候选资产 | `connected` | `app.bioinformatics.download.DatasetDownloadService.download_geo_manifest_assets` | raw_data/geo/GSE6004/GSE6004_family.soft.gz; raw_data/geo/GSE6004/matrix/GSE6004_series_matrix.txt.gz |
| `BIO-B10-GSE6004-CONTINUE-TO-RECOGNITION` | `GSE6004` | `data_source` | `bioinformaticsGeoContinueRecognitionButton` | 进入数据识别 | `connected` | `app.bioinformatics.workspace.BioinformaticsWorkspaceWidget.show_recognition` | route=recognition |
| `BIO-B10-GSE6004-RUN-RECOGNITION` | `GSE6004` | `data_check_preparation` | `bioinformaticsRunRecognitionButton` | 开始识别 | `connected` | `app.bioinformatics.project_recognition.run_project_recognition_for_paths` | logs/recognition/recognition_report.json; recognized_data/current.json; logs/recognition/group_preview_report.json |
| `BIO-B10-GSE6004-CONTINUE-TO-READINESS` | `GSE6004` | `data_check_preparation` | `bioinformaticsRecognitionContinueReadinessButton` | 继续：数据准备与标准化 | `connected` | `app.bioinformatics.workspace.BioinformaticsWorkspaceWidget.show_readiness` | route=readiness |
| `BIO-B10-GSE6004-RUN-READINESS` | `GSE6004` | `data_check_preparation` | `bioinformaticsRunDataCheckButton` | 重新运行数据检查 | `connected` | `app.bioinformatics.project_readiness.run_project_readiness` | logs/readiness/readiness_report.json; manifests/analysis_capability_matrix.json |
| `BIO-B10-GSE153659-CONFIGURE-GEO-SOURCE` | `GSE153659` | `data_source` | `bioinformaticsDataSourceSelectPreviewButton` | 配置 GEO 来源 | `connected` | `app.bioinformatics.data_source_requests.create_data_source_request` | bio_batch_10_gse153659/manifests/data_source_requests.json |
| `BIO-B10-GSE153659-SEARCH-GEO-METADATA` | `GSE153659` | `data_source` | `bioinformaticsGeoSearchMetadataButton` | 检索元数据 | `connected` | `app.bioinformatics.legacy.geo_tool.geo_info_fetcher.GeoInfoFetcher.search_series` | GSE：GSE153659
标题：Next Generation Sequencing Facilitates Quantitative Analysis of Papillary Thyroid Carcinoma
平台：24676
样本数：31
下一步：加入项目后下载 GEO 元数据。 |
| `BIO-B10-GSE153659-ADD-GEO-ACCESSION` | `GSE153659` | `data_source` | `bioinformaticsGeoAddToProjectButton` | 加入项目 | `connected` | `app.bioinformatics.project_workspace_binding.register_acquisition` | acquisition/handoffs/acq-9c6b577d.json; acquisition/handoffs/latest_acquisition_handoff.json; acquisition/plans/acq-9c6b577d.json; acquisition/plans/latest_acquisition_plan.json; acquisition/records/acq-9c6b577d.json; acquisition/records/latest_acquisition_record.json |
| `BIO-B10-GSE153659-DOWNLOAD-GEO-METADATA` | `GSE153659` | `data_source` | `bioinformaticsGeoDownloadMetadataButton` | 下载 GEO 元数据 | `connected` | `app.bioinformatics.download.DatasetDownloadService.create_candidate_download_task` | raw_data/geo/GSE153659/GSE153659_family.soft.gz; raw_data/geo/GSE153659/GSE153659_asset_manifest.json; acquisition/download_receipts/dl-a35eb6201c.json |
| `BIO-B10-GSE153659-DOWNLOAD-GEO-ASSETS` | `GSE153659` | `data_source` | `bioinformaticsGeoDownloadAssetsButton` | 下载候选资产 | `connected` | `app.bioinformatics.download.DatasetDownloadService.download_geo_manifest_assets` | raw_data/geo/GSE153659/GSE153659_family.soft.gz; raw_data/geo/GSE153659/matrix/GSE153659_series_matrix.txt.gz; raw_data/geo/GSE153659/supplementary/GSE153659_FPKM_Matrix.xlsx |
| `BIO-B10-GSE153659-CONTINUE-TO-RECOGNITION` | `GSE153659` | `data_source` | `bioinformaticsGeoContinueRecognitionButton` | 进入数据识别 | `connected` | `app.bioinformatics.workspace.BioinformaticsWorkspaceWidget.show_recognition` | route=recognition |
| `BIO-B10-GSE153659-RUN-RECOGNITION` | `GSE153659` | `data_check_preparation` | `bioinformaticsRunRecognitionButton` | 开始识别 | `connected` | `app.bioinformatics.project_recognition.run_project_recognition_for_paths` | logs/recognition/recognition_report.json; recognized_data/current.json; logs/recognition/group_preview_report.json |
| `BIO-B10-GSE153659-CONTINUE-TO-READINESS` | `GSE153659` | `data_check_preparation` | `bioinformaticsRecognitionContinueReadinessButton` | 继续：数据准备与标准化 | `connected` | `app.bioinformatics.workspace.BioinformaticsWorkspaceWidget.show_readiness` | route=readiness |
| `BIO-B10-GSE153659-RUN-READINESS` | `GSE153659` | `data_check_preparation` | `bioinformaticsRunDataCheckButton` | 重新运行数据检查 | `connected` | `app.bioinformatics.project_readiness.run_project_readiness` | logs/readiness/readiness_report.json; manifests/analysis_capability_matrix.json |

## Screenshots

- `GSE6004_01_geo_adapter_ready`: `docs/ui/runtime_screenshots/20260602_bio_batch10_geo_online_retrieval/GSE6004_01_geo_adapter_ready.png`
- `GSE6004_02_geo_metadata_downloaded`: `docs/ui/runtime_screenshots/20260602_bio_batch10_geo_online_retrieval/GSE6004_02_geo_metadata_downloaded.png`
- `GSE6004_03_geo_assets_downloaded`: `docs/ui/runtime_screenshots/20260602_bio_batch10_geo_online_retrieval/GSE6004_03_geo_assets_downloaded.png`
- `GSE6004_04_recognition_complete`: `docs/ui/runtime_screenshots/20260602_bio_batch10_geo_online_retrieval/GSE6004_04_recognition_complete.png`
- `GSE6004_05_readiness_complete`: `docs/ui/runtime_screenshots/20260602_bio_batch10_geo_online_retrieval/GSE6004_05_readiness_complete.png`
- `GSE153659_01_geo_adapter_ready`: `docs/ui/runtime_screenshots/20260602_bio_batch10_geo_online_retrieval/GSE153659_01_geo_adapter_ready.png`
- `GSE153659_02_geo_metadata_downloaded`: `docs/ui/runtime_screenshots/20260602_bio_batch10_geo_online_retrieval/GSE153659_02_geo_metadata_downloaded.png`
- `GSE153659_03_geo_assets_downloaded`: `docs/ui/runtime_screenshots/20260602_bio_batch10_geo_online_retrieval/GSE153659_03_geo_assets_downloaded.png`
- `GSE153659_04_recognition_complete`: `docs/ui/runtime_screenshots/20260602_bio_batch10_geo_online_retrieval/GSE153659_04_recognition_complete.png`
- `GSE153659_05_readiness_complete`: `docs/ui/runtime_screenshots/20260602_bio_batch10_geo_online_retrieval/GSE153659_05_readiness_complete.png`
