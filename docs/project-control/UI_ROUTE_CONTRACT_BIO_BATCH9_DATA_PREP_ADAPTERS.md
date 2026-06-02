# Bioinformatics Batch 9 Data-Prep Adapter Route Contract

- branch: `integration/release-bio-c1-ui-shell`
- head: `e837762525d2366934be6baf5ae9e730a1f8abaa`
- scope: Bioinformatics mature Data Source -> Data Check -> Standardization -> Group Design adapter chain with button-click artifact proof.
- row_count: `9`
- connected: `9`
- broken: `0`

## Rows

| contract | page | object | label | status | backend capability | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `BIO-B9-ACQUISITION-REGISTER-LOCAL` | `data_source` | `register_acquisition` | register local integrated RNA-seq file | `connected` | `app.bioinformatics.project_workspace_binding.register_acquisition` | acquisition/plans/latest_acquisition_plan.json; acquisition/records/latest_acquisition_record.json; acquisition/handoffs/latest_acquisition_handoff.json |
| `BIO-B9-DATA-SOURCE-LOCAL-DRAFT` | `data_source` | `bioinformaticsDataSourceSelectPreviewButton` | 配置本地导入 | `connected` | `app.bioinformatics.data_source_requests.create_data_source_request` | manifests/data_source_requests.json |
| `BIO-B9-DATA-CHECK-RUN-RECOGNITION` | `data_check_preparation` | `bioinformaticsRunRecognitionButton` | 开始识别 | `connected` | `app.bioinformatics.project_recognition.run_project_recognition_for_paths` | logs/recognition/recognition_report.json; recognized_data/current.json; logs/recognition/group_preview_report.json |
| `BIO-B9-DATA-CHECK-RUN-READINESS` | `data_check_preparation` | `bioinformaticsRunDataCheckButton` | 重新运行数据检查 | `connected` | `app.bioinformatics.project_readiness.run_project_readiness` | logs/readiness/readiness_report.json; manifests/analysis_capability_matrix.json |
| `BIO-B9-DATA-CHECK-OPEN-STANDARDIZATION` | `data_check_preparation` | `primaryButton` | 生成标准化数据 | `connected` | `app.bioinformatics.workspace.BioinformaticsWorkspaceWidget.show_standardization` | route_state_assertion |
| `BIO-B9-DATA-CHECK-GENERATE-STANDARDIZED-ASSETS` | `data_check_preparation` | `primaryButton` | 生成标准化数据 | `connected` | `app.bioinformatics.project_standardization.generate_standardized_assets` | manifests/standardized_assets_registry.json; standardized_data/analysis_ready_assets/analysis_ready_manifest.json; standardized_data/repositories/repository_manifest.json |
| `BIO-B9-GROUP-DESIGN-SUGGEST-COMPARISON` | `group_design` | `bioinformaticsGroupDesignSuggestionButton` | 从对照组生成比较 | `connected` | `app.bioinformatics.group_comparison_design.build_default_comparison_rows` | analysis/group_design/one_vs_control_suggestions_preview.json |
| `BIO-B9-GROUP-DESIGN-SAVE-CONFIRMED-DESIGN` | `group_design` | `bioinformaticsGroupDesignSaveButton` | 保存分组与比较设计 | `connected` | `app.bioinformatics.group_comparison_design.save_group_comparison_design` | manifests/group_comparison_design.json; manifests/analysis_task_center.json |
| `BIO-B9-GROUP-DESIGN-CONTINUE-ANALYSIS-TASKS` | `group_design` | `bioinformaticsGroupDesignContinueButton` | 继续：分析任务中心 | `connected` | `app.bioinformatics.workspace.BioinformaticsWorkspaceWidget.show_analysis_tasks` | route_state_assertion |

## Screenshots

- `01_data_source`: `docs/ui/runtime_screenshots/20260602_bio_batch9_data_prep_adapters/01_data_source.png`
- `02_recognition_before_click`: `docs/ui/runtime_screenshots/20260602_bio_batch9_data_prep_adapters/02_recognition_before_click.png`
- `03_recognition_after_click`: `docs/ui/runtime_screenshots/20260602_bio_batch9_data_prep_adapters/03_recognition_after_click.png`
- `04_readiness`: `docs/ui/runtime_screenshots/20260602_bio_batch9_data_prep_adapters/04_readiness.png`
- `05_standardization_before_click`: `docs/ui/runtime_screenshots/20260602_bio_batch9_data_prep_adapters/05_standardization_before_click.png`
- `06_standardization_after_click`: `docs/ui/runtime_screenshots/20260602_bio_batch9_data_prep_adapters/06_standardization_after_click.png`
- `07_group_design_prepared`: `docs/ui/runtime_screenshots/20260602_bio_batch9_data_prep_adapters/07_group_design_prepared.png`
