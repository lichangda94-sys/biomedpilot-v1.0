# Release Preview UI Shell and Live Function Validation

- created_at: `2026-06-01T09:54:10+00:00`
- run_root: `/Users/changdali/Developer/biomedpilot v1.0/Integration/logs/validation/release_preview_validation_20260601_175254`
- screenshot_dir: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation`

## UI Shell Baseline Restore

- Welcome/Login: matches UIShell runtime baseline in current source.
- Dashboard/Home: UIShell runtime baseline retained; Integration Centers entry is preserved.
- About: restored to UIShell mature dark text page baseline.
- Settings: UIShell settings shell retained with Integration R enrichment backend detect-only gate.
- Sidebar: UIShell AppSidebar visual structure retained with current Integration routes.

## Live Bioinformatics Validation

| Dataset | Search | Download | Recognition | Readiness | Project |
| --- | --- | --- | --- | --- | --- |
| GSE6004 | completed ['GSE6004'] | geo_metadata_downloaded; geo_assets_downloaded | current; files=2 | ready_with_warnings | `/Users/changdali/Developer/biomedpilot v1.0/Integration/logs/validation/release_preview_validation_20260601_175254/bioinformatics/GSE6004` |
| GSE153659 | completed ['GSE153659'] | geo_metadata_downloaded; geo_assets_downloaded | current; files=2 | not_ready | `/Users/changdali/Developer/biomedpilot v1.0/Integration/logs/validation/release_preview_validation_20260601_175254/bioinformatics/GSE153659` |

## Live Meta Analysis PubMed Validation

- query: `("thyroid cancer" OR "thyroid carcinoma" OR 甲状腺癌) AND (adiponectin OR 脂联素)`
- search_success: `True`
- result_count: `26`
- returned_count: `8`
- preview_candidate_count: `8`
- handoff_success: `True`
- imported_count: `3`
- screening_queue_success: `True`
- screening_record_count: `3`
- project_dir: `/Users/changdali/Developer/biomedpilot v1.0/Integration/logs/validation/release_preview_validation_20260601_175254/meta_analysis/thyroid_cancer_adiponectin`

## Screenshot Evidence

### shell_welcome

![shell_welcome](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/shell_welcome.png)

### shell_about

![shell_about](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/shell_about.png)

### shell_dashboard

![shell_dashboard](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/shell_dashboard.png)

### shell_settings_general

![shell_settings_general](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/shell_settings_general.png)

### shell_settings_tab_0_general

![shell_settings_tab_0_general](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/shell_settings_tab_0_general.png)

### shell_settings_tab_1_external_capabilities

![shell_settings_tab_1_external_capabilities](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/shell_settings_tab_1_external_capabilities.png)

### shell_settings_tab_2_analysis_resources

![shell_settings_tab_2_analysis_resources](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/shell_settings_tab_2_analysis_resources.png)

### shell_settings_tab_3_model_engine

![shell_settings_tab_3_model_engine](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/shell_settings_tab_3_model_engine.png)

### shell_settings_tab_4_developer_diagnostics

![shell_settings_tab_4_developer_diagnostics](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/shell_settings_tab_4_developer_diagnostics.png)

### shell_centers

![shell_centers](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/shell_centers.png)

### shell_centers_tab_0_project

![shell_centers_tab_0_project](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/shell_centers_tab_0_project.png)

### shell_centers_tab_1_data

![shell_centers_tab_1_data](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/shell_centers_tab_1_data.png)

### shell_centers_tab_2_task

![shell_centers_tab_2_task](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/shell_centers_tab_2_task.png)

### shell_centers_tab_3_report

![shell_centers_tab_3_report](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/shell_centers_tab_3_report.png)

### shell_centers_tab_4_environment

![shell_centers_tab_4_environment](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/shell_centers_tab_4_environment.png)

### shell_centers_tab_5_packaging

![shell_centers_tab_5_packaging](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/shell_centers_tab_5_packaging.png)

### bio_project_home

![bio_project_home](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/bio_project_home.png)

### bio_data_source

![bio_data_source](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/bio_data_source.png)

### bio_data_check_recognition

![bio_data_check_recognition](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/bio_data_check_recognition.png)

### bio_data_check_readiness

![bio_data_check_readiness](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/bio_data_check_readiness.png)

### bio_group_design

![bio_group_design](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/bio_group_design.png)

### bio_analysis_tasks

![bio_analysis_tasks](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/bio_analysis_tasks.png)

### bio_result_report

![bio_result_report](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/bio_result_report.png)

### bio_report_export

![bio_report_export](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/bio_report_export.png)

### bio_settings_resources

![bio_settings_resources](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/bio_settings_resources.png)

### meta_project_home

![meta_project_home](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/meta_project_home.png)

### meta_question_meta_type

![meta_question_meta_type](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/meta_question_meta_type.png)

### meta_search_strategy

![meta_search_strategy](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/meta_search_strategy.png)

### meta_import_dedup

![meta_import_dedup](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/meta_import_dedup.png)

### meta_screening

![meta_screening](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/meta_screening.png)

### meta_fulltext_extraction

![meta_fulltext_extraction](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/meta_fulltext_extraction.png)

### meta_quality_assessment

![meta_quality_assessment](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/meta_quality_assessment.png)

### meta_analysis_tasks

![meta_analysis_tasks](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/meta_analysis_tasks.png)

### meta_result_report

![meta_result_report](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/meta_result_report.png)

### meta_report_export

![meta_report_export](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/meta_report_export.png)

### meta_meta_settings

![meta_meta_settings](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/meta_meta_settings.png)

### labtools_home

![labtools_home](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/labtools_home.png)

### labtools_general_calculators

![labtools_general_calculators](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/labtools_general_calculators.png)

### labtools_reagent_preparation

![labtools_reagent_preparation](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/labtools_reagent_preparation.png)

### labtools_experiment_modules

![labtools_experiment_modules](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/labtools_experiment_modules.png)

### labtools_cell_experiments

![labtools_cell_experiments](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/labtools_cell_experiments.png)

### labtools_protein_experiments

![labtools_protein_experiments](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/labtools_protein_experiments.png)

### labtools_nucleic_acid_experiments

![labtools_nucleic_acid_experiments](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/labtools_nucleic_acid_experiments.png)

### labtools_immuno_absorbance

![labtools_immuno_absorbance](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/labtools_immuno_absorbance.png)

### labtools_ihc

![labtools_ihc](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/labtools_ihc.png)

### shell_test_feedback

![shell_test_feedback](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260601_release_preview_validation/shell_test_feedback.png)

## Click Audit Summary

| Scope | Object | Text | Enabled | Click Result | Disabled Reason |
| --- | --- | --- | --- | --- | --- |
| welcome | `primaryButton` | 进入本地工作台 | True | not_clicked_safety_gate |  |
| welcome | `aboutButton` | 关于 | True | not_clicked_safety_gate |  |
| welcome | `aboutButton` | 关于 | True | about |  |
| welcome | `primaryButton` | 进入本地工作台 | True | dashboard |  |
| dashboard | `appSidebarButton` | 工作台 / Dashboard | True | not_clicked_safety_gate |  |
| dashboard | `appSidebarButton` | 生信分析 / Bioinformatics | True | not_clicked_safety_gate |  |
| dashboard | `appSidebarButton` | Meta 分析 / Meta Analysis | True | not_clicked_safety_gate |  |
| dashboard | `appSidebarButton` | 实验工具 / LabTools | True | not_clicked_safety_gate |  |
| dashboard | `appSidebarButton` | 管理中心 / Centers | True | not_clicked_safety_gate |  |
| dashboard | `appSidebarAuxButton` | 设置中心 / Settings | True | not_clicked_safety_gate |  |
| dashboard | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | not_clicked_safety_gate |  |
| dashboard | `appSidebarAuxButton` | 关于 / About | True | not_clicked_safety_gate |  |
| dashboard | `dashboardHeaderIconButton` |  | True | not_clicked_safety_gate |  |
| dashboard | `dashboardHeaderIconButton` |  | True | not_clicked_safety_gate |  |
| dashboard | `bioModuleButton` | 进入模块 | True | not_clicked_safety_gate |  |
| dashboard | `metaModuleButton` | 进入模块 | True | not_clicked_safety_gate |  |
| dashboard | `labtoolsModuleButton` | 进入模块 | True | not_clicked_safety_gate |  |
| dashboard | `dashboardOpenMoreProjectsButton` | 打开更多项目... | False | disabled_with_reason | Project Center 尚未作为正式项目中心开放。 |
| dashboard | `dashboardViewAllProjectsButton` | 查看全部项目（12） | False | disabled_without_reason |  |
| sidebar | `appSidebarAuxButton` | 设置中心 / Settings | True | settings |  |
| settings | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace settings->dashboard |  |
| settings | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| settings | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| settings | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| settings | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| settings | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| settings | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| settings | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
| sidebar | `appSidebarButton` | 管理中心 / Centers | True | centers |  |
| centers | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace centers->dashboard |  |
| centers | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| centers | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| centers | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| centers | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| centers | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| centers | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| centers | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
| sidebar | `appSidebarButton` | 生信分析 / Bioinformatics | True | bioinformatics |  |
| bio_project_home | `appSidebarButton` | 工作台 / Dashboard | True | not_clicked_safety_gate |  |
| bio_project_home | `appSidebarButton` | 生信分析 / Bioinformatics | True | not_clicked_safety_gate |  |
| bio_project_home | `appSidebarButton` | Meta 分析 / Meta Analysis | True | not_clicked_safety_gate |  |
| bio_project_home | `appSidebarButton` | 实验工具 / LabTools | True | not_clicked_safety_gate |  |
| bio_project_home | `appSidebarButton` | 管理中心 / Centers | True | not_clicked_safety_gate |  |
| bio_project_home | `appSidebarAuxButton` | 设置中心 / Settings | True | not_clicked_safety_gate |  |
| bio_project_home | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | not_clicked_safety_gate |  |
| bio_project_home | `appSidebarAuxButton` | 关于 / About | True | not_clicked_safety_gate |  |
| bio_project_home | `bioinformaticsIANavItem` | 01 / 项目首页 / Project Home / 管理项目与团队 / 查看进度与关键状态 | False | disabled_without_reason |  |
| bio_project_home | `bioinformaticsIANavItem` | 02 / 数据来源 / Data Source / 连接并获取数据 / 支持多种来源检索 | False | disabled_without_reason |  |
| bio_project_home | `bioinformaticsIANavItem` | 03 / 数据检查与准备 / Data Check & Prep / 完成质量检查与预处理 / 构建分析数据集 | False | disabled_without_reason |  |
| bio_project_home | `bioinformaticsIANavItem` | 04 / 分组与分析设计 / Group & Design / 定义分组与比较方案 / 设置协变量设计 | False | disabled_without_reason |  |
| bio_project_home | `bioinformaticsIANavItem` | 05 / 分析任务 / Analysis Tasks / 配置任务并查看 gate / 管理执行状态 | False | disabled_without_reason |  |
| bio_project_home | `bioinformaticsIANavItem` | 06 / 结果与报告 / Result & Report / 审阅结果与报告草稿 / 区分结果语义 | False | disabled_without_reason |  |
| bio_project_home | `bioinformaticsIANavItem` | 07 / 报告导出 / Report Export / 检查 report-ready gate / 导出受控报告包 | False | disabled_without_reason |  |
| bio_project_home | `bioinformaticsIANavItem` | 生信分析设置 / Resources / 管理资源、参数配置与外部工具连接。 | False | disabled_without_reason |  |
| bio_project_home | `bioinformaticsIANavItem` | 项目日志与技术详情 / Project Logs & Details / 查看运行记录与技术细节。 | False | disabled_without_reason |  |
| bio_project_home | `quickAccessButton` | 最近使用 / 快速访问最近项目或流程 | False | disabled_without_reason |  |
| bio_project_home | `quickAccessButton` | 使用指南 / 查看流程说明与示例 | False | disabled_without_reason |  |
| bio_project_home | `quickAccessButton` | 常见问题 / 查看常见问题与解决方案 | False | disabled_without_reason |  |
| bio_project_home | `quickAccessButton` | 意见反馈 / 提出建议或报告问题 | False | disabled_without_reason |  |
| bio_data_source | `appSidebarButton` | 工作台 / Dashboard | True | not_clicked_safety_gate |  |
| bio_data_source | `appSidebarButton` | 生信分析 / Bioinformatics | True | not_clicked_safety_gate |  |
| bio_data_source | `appSidebarButton` | Meta 分析 / Meta Analysis | True | not_clicked_safety_gate |  |
| bio_data_source | `appSidebarButton` | 实验工具 / LabTools | True | not_clicked_safety_gate |  |
| bio_data_source | `appSidebarButton` | 管理中心 / Centers | True | not_clicked_safety_gate |  |
| bio_data_source | `appSidebarAuxButton` | 设置中心 / Settings | True | not_clicked_safety_gate |  |
| bio_data_source | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | not_clicked_safety_gate |  |
| bio_data_source | `appSidebarAuxButton` | 关于 / About | True | not_clicked_safety_gate |  |
| bio_data_source | `secondaryButton` | 返回项目首页 | True | not_clicked_safety_gate |  |
| bio_data_source | `dataSourceTabButton` | 数据来源选择 | False | disabled_with_reason | disabled_pending_data_source_tab_router |
| bio_data_source | `dataSourceTabButton` | 已获取数据 | False | disabled_with_reason | disabled_pending_data_source_tab_router |
| bio_data_source | `dataSourceTabButton` | 检索记录 | False | disabled_with_reason | disabled_pending_data_source_tab_router |
| bio_data_source | `dataSourceTabButton` | 数据连接管理 | False | disabled_with_reason | disabled_pending_data_source_tab_router |
| bio_data_source | `bioinformaticsDataSourceSelectPreviewButton` | 配置 GEO 来源 | True | not_clicked_safety_gate |  |
| bio_data_source | `bioinformaticsDataSourceSelectPreviewButton` | 配置 TCGA 来源 | True | not_clicked_safety_gate |  |
| bio_data_source | `bioinformaticsDataSourceSelectPreviewButton` | 配置 GTEx 来源 | True | not_clicked_safety_gate |  |
| bio_data_source | `bioinformaticsDataSourceSelectPreviewButton` | 配置本地导入 | True | not_clicked_safety_gate |  |
| bio_data_source | `dataSourceResearchSearchButton` | 进入检索 | True | not_clicked_safety_gate |  |
| bio_data_source | `secondaryButton` | 下载所选 | False | disabled_with_reason | disabled_until_data_source_project_gate_passes |
| bio_data_source | `secondaryButton` | 删除所选 | False | disabled_with_reason | disabled_until_data_source_project_gate_passes |
| bio_data_source | `dataSourceQuickAccessButton` | 最近使用 / 快速访问最近使用的数据项目 | False | disabled_with_reason | disabled_pending_project_help_center |
| bio_data_source | `dataSourceQuickAccessButton` | 使用指南 / 查看数据来源与导入说明 | False | disabled_with_reason | disabled_pending_project_help_center |
| bio_data_source | `dataSourceQuickAccessButton` | 常见问题 / 查看常见问题与解决方案 | False | disabled_with_reason | disabled_pending_project_help_center |
| bio_data_source | `dataSourceQuickAccessButton` | 意见反馈 / 提出建议或报告问题 | False | disabled_with_reason | disabled_pending_project_help_center |
| bio_data_check_recognition | `appSidebarButton` | 工作台 / Dashboard | True | not_clicked_safety_gate |  |
| bio_data_check_recognition | `appSidebarButton` | 生信分析 / Bioinformatics | True | not_clicked_safety_gate |  |
| bio_data_check_recognition | `appSidebarButton` | Meta 分析 / Meta Analysis | True | not_clicked_safety_gate |  |
| bio_data_check_recognition | `appSidebarButton` | 实验工具 / LabTools | True | not_clicked_safety_gate |  |
| bio_data_check_recognition | `appSidebarButton` | 管理中心 / Centers | True | not_clicked_safety_gate |  |
| bio_data_check_recognition | `appSidebarAuxButton` | 设置中心 / Settings | True | not_clicked_safety_gate |  |
| bio_data_check_recognition | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | not_clicked_safety_gate |  |
| bio_data_check_recognition | `appSidebarAuxButton` | 关于 / About | True | not_clicked_safety_gate |  |
| bio_data_check_recognition | `secondaryButton` | 返回数据导入与检索 | True | not_clicked_safety_gate |  |
| bio_data_check_recognition | `secondaryButton` | 删除所选 | False | disabled_with_reason | disabled_until_recognition_input_selected |
| bio_data_check_recognition | `primaryButton` | 开始识别 | True | not_clicked_safety_gate |  |
| bio_data_check_recognition | `secondaryButton` | 刷新 | True | not_clicked_safety_gate |  |
| bio_data_check_recognition | `secondaryButton` | 技术详情 | True | not_clicked_safety_gate |  |
| bio_data_check_recognition | `secondaryButton` | 技术操作 | True | not_clicked_safety_gate |  |
| bio_data_check_recognition | `primaryButton` | 继续：数据准备与标准化 | True | not_clicked_safety_gate |  |
| bio_data_check_readiness | `appSidebarButton` | 工作台 / Dashboard | True | not_clicked_safety_gate |  |
| bio_data_check_readiness | `appSidebarButton` | 生信分析 / Bioinformatics | True | not_clicked_safety_gate |  |
| bio_data_check_readiness | `appSidebarButton` | Meta 分析 / Meta Analysis | True | not_clicked_safety_gate |  |
| bio_data_check_readiness | `appSidebarButton` | 实验工具 / LabTools | True | not_clicked_safety_gate |  |
| bio_data_check_readiness | `appSidebarButton` | 管理中心 / Centers | True | not_clicked_safety_gate |  |
| bio_data_check_readiness | `appSidebarAuxButton` | 设置中心 / Settings | True | not_clicked_safety_gate |  |
| bio_data_check_readiness | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | not_clicked_safety_gate |  |
| bio_data_check_readiness | `appSidebarAuxButton` | 关于 / About | True | not_clicked_safety_gate |  |
| bio_data_check_readiness | `secondaryButton` | 返回数据来源 | True | not_clicked_safety_gate |  |
| bio_data_check_readiness | `dataCheckTabButton` | 文件级识别与状态 | False | disabled_with_reason | disabled_pending_data_check_tab_router |
| bio_data_check_readiness | `dataCheckTabButton` | 表达矩阵检查 | False | disabled_with_reason | disabled_pending_data_check_tab_router |
| bio_data_check_readiness | `dataCheckTabButton` | 样本信息检查 | False | disabled_with_reason | disabled_pending_data_check_tab_router |
| bio_data_check_readiness | `dataCheckTabButton` | 基因注释匹配 | False | disabled_with_reason | disabled_pending_data_check_tab_router |
| bio_data_check_readiness | `dataCheckTabButton` | 临床信息检查 | False | disabled_with_reason | disabled_pending_data_check_tab_router |
| bio_data_check_readiness | `dataCheckTabButton` | 预处理设置 | False | disabled_with_reason | disabled_pending_data_check_tab_router |
| bio_data_check_readiness | `dataCheckTabButton` | 整体结论 | False | disabled_with_reason | disabled_pending_data_check_tab_router |
| bio_data_check_readiness | `dataCheckReportButton` | 查看详细报告  → | False | disabled_with_reason | disabled_until_data_check_artifact_exists |
| bio_data_check_readiness | `secondaryButton` | 复制检查摘要 | True | not_clicked_safety_gate |  |
| bio_data_check_readiness | `bioinformaticsDataCheckSaveReportDisabledButton` | Save Report - file picker required | False | disabled_with_reason | disabled_until_data_check_artifact_exists |
| bio_data_check_readiness | `secondaryButton` | 确认推荐分组 | True | not_clicked_safety_gate |  |
| bio_data_check_readiness | `secondaryButton` | 修改分组 | True | not_clicked_safety_gate |  |
| bio_data_check_readiness | `secondaryButton` | 拒绝推荐分组 | True | not_clicked_safety_gate |  |
| bio_data_check_readiness | `secondaryButton` | 稍后处理 | True | not_clicked_safety_gate |  |
| bio_data_check_readiness | `secondaryButton` | 选择 GSEA 基因集 | True | not_clicked_safety_gate |  |
| bio_data_check_readiness | `secondaryButton` | 技术详情 | True | not_clicked_safety_gate |  |
| bio_data_check_readiness | `bioinformaticsRunDataCheckButton` | 运行数据检查 | True | not_clicked_safety_gate |  |
| bio_data_check_readiness | `primaryButton` | 继续：标准化数据 | True | not_clicked_safety_gate |  |
| bio_group_design | `appSidebarButton` | 工作台 / Dashboard | True | not_clicked_safety_gate |  |
| bio_group_design | `appSidebarButton` | 生信分析 / Bioinformatics | True | not_clicked_safety_gate |  |
| bio_group_design | `appSidebarButton` | Meta 分析 / Meta Analysis | True | not_clicked_safety_gate |  |
| bio_group_design | `appSidebarButton` | 实验工具 / LabTools | True | not_clicked_safety_gate |  |
| bio_group_design | `appSidebarButton` | 管理中心 / Centers | True | not_clicked_safety_gate |  |
| bio_group_design | `appSidebarAuxButton` | 设置中心 / Settings | True | not_clicked_safety_gate |  |
| bio_group_design | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | not_clicked_safety_gate |  |
| bio_group_design | `appSidebarAuxButton` | 关于 / About | True | not_clicked_safety_gate |  |
| bio_group_design | `secondaryButton` | 返回数据检查 | True | not_clicked_safety_gate |  |
| bio_group_design | `groupDesignTabButton` | 分组设置 | False | disabled_with_reason | disabled_pending_group_design_tab_router |
| bio_group_design | `groupDesignTabButton` | 对比关系 | False | disabled_with_reason | disabled_pending_group_design_tab_router |
| bio_group_design | `groupDesignTabButton` | 协变量设置 | False | disabled_with_reason | disabled_pending_group_design_tab_router |
| bio_group_design | `groupDesignTabButton` | 分析策略 | False | disabled_with_reason | disabled_pending_group_design_tab_router |
| bio_group_design | `groupDesignTabButton` | 多因素设计 | False | disabled_with_reason | disabled_pending_group_design_tab_router |
| bio_group_design | `groupDesignPrimaryButton` | +  新建分组 | False | disabled_with_reason | disabled_manual_design_editor_not_connected |
| bio_group_design | `groupDesignGhostButton` | 下载模板 | False | disabled_with_reason | disabled_manual_design_aux_action_not_connected |
| bio_group_design | `groupDesignPrimaryButton` | +  新建对比 | False | disabled_with_reason | disabled_manual_design_editor_not_connected |
| bio_group_design | `groupDesignGhostButton` | 查看详情 | False | disabled_with_reason | disabled_manual_design_aux_action_not_connected |
| bio_group_design | `bioinformaticsGroupDesignRefreshButton` | 刷新分组设计 | True | not_clicked_safety_gate |  |
| bio_group_design | `bioinformaticsGroupDesignSuggestionButton` | 从对照组生成比较 | True | not_clicked_safety_gate |  |
| bio_group_design | `bioinformaticsGroupDesignSaveButton` | 保存分组与比较设计 | True | not_clicked_safety_gate |  |
| bio_group_design | `bioinformaticsRunPreflightGatedButton` | Run Preflight - gated preview | False | disabled_with_reason | disabled_preflight_preview_only_no_formal_model_run |
| bio_group_design | `secondaryButton` | 展开技术详情 | True | not_clicked_safety_gate |  |
| bio_group_design | `bioinformaticsGroupDesignContinueButton` | 继续：分析任务中心 | True | not_clicked_safety_gate |  |
| bio_analysis_tasks | `appSidebarButton` | 工作台 / Dashboard | True | not_clicked_safety_gate |  |
| bio_analysis_tasks | `appSidebarButton` | 生信分析 / Bioinformatics | True | not_clicked_safety_gate |  |
| bio_analysis_tasks | `appSidebarButton` | Meta 分析 / Meta Analysis | True | not_clicked_safety_gate |  |
| bio_analysis_tasks | `appSidebarButton` | 实验工具 / LabTools | True | not_clicked_safety_gate |  |
| bio_analysis_tasks | `appSidebarButton` | 管理中心 / Centers | True | not_clicked_safety_gate |  |
| bio_analysis_tasks | `appSidebarAuxButton` | 设置中心 / Settings | True | not_clicked_safety_gate |  |
| bio_analysis_tasks | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | not_clicked_safety_gate |  |
| bio_analysis_tasks | `appSidebarAuxButton` | 关于 / About | True | not_clicked_safety_gate |  |
| bio_analysis_tasks | `analysisTaskPrimaryButton` | 参数总览 | False | disabled_with_reason | disabled_analysis_overview_placeholder |
| bio_analysis_tasks | `analysisTaskGhostButton` | 分析文档 | False | disabled_with_reason | disabled_analysis_documentation_placeholder |
| bio_analysis_tasks | `bioinformaticsAnalysisRefreshButton` | 刷新任务状态 | True | not_clicked_safety_gate |  |
| bio_analysis_tasks | `bioinformaticsAnalysisComparisonConfigButton` | 确认分组与比较设计 | True | not_clicked_safety_gate |  |
| bio_analysis_tasks | `bioinformaticsAnalysisOpenDegConfigButton` | 进入差异分析配置 | True | not_clicked_safety_gate |  |
| bio_analysis_tasks | `analysisTaskConfirmFormalDegParametersButton` | 确认 formal DEG 参数 | False | disabled_with_reason | requires_formal_deg_parameter_manifest_and_dependency_snapshot |
| bio_analysis_tasks | `analysisTaskRunFormalControlledDegButton` | 运行两组 controlled DEG | False | disabled_with_reason | requires_confirmed_formal_deg_gate |
| bio_analysis_tasks | `openImmuneScoringGateButton` | 免疫浸润 / TME评分 | True | not_clicked_safety_gate |  |
| bio_analysis_tasks | `openEnrichmentGateButton` | 富集 ORA/GSEA gate | True | not_clicked_safety_gate |  |
| bio_analysis_tasks | `openSurvivalClinicalGateButton` | Survival / clinical gate | True | not_clicked_safety_gate |  |
| bio_analysis_tasks | `openImportedDegBrowserButton` | 查看已导入差异分析结果 | True | not_clicked_safety_gate |  |
| bio_analysis_tasks | `analysisTaskToggleDeveloperDiagnosticsButton` | 展开技术细节 | True | not_clicked_safety_gate |  |
| bio_analysis_tasks | `analysisTaskCreateTaskRecordButton` | 创建指定任务记录 | True | not_clicked_safety_gate |  |
| bio_analysis_tasks | `analysisTaskRunTestingGeoDegButton` | 生成测试级 GEO 差异结果 | True | not_clicked_safety_gate |  |
| bio_analysis_tasks | `analysisTaskContinueResultsButton` | 继续：结果浏览 | True | not_clicked_safety_gate |  |
| bio_result_report | `appSidebarButton` | 工作台 / Dashboard | True | not_clicked_safety_gate |  |
| bio_result_report | `appSidebarButton` | 生信分析 / Bioinformatics | True | not_clicked_safety_gate |  |
| bio_result_report | `appSidebarButton` | Meta 分析 / Meta Analysis | True | not_clicked_safety_gate |  |
| bio_result_report | `appSidebarButton` | 实验工具 / LabTools | True | not_clicked_safety_gate |  |
| bio_result_report | `appSidebarButton` | 管理中心 / Centers | True | not_clicked_safety_gate |  |
| bio_result_report | `appSidebarAuxButton` | 设置中心 / Settings | True | not_clicked_safety_gate |  |
| bio_result_report | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | not_clicked_safety_gate |  |
| bio_result_report | `appSidebarAuxButton` | 关于 / About | True | not_clicked_safety_gate |  |
| bio_result_report | `resultReportGhostButton` | 返回分析任务 | True | not_clicked_safety_gate |  |
| bio_result_report | `resultReportGhostButton` | 刷新 | True | not_clicked_safety_gate |  |
| bio_result_report | `resultReportTabButton` | 结果预览 / Result Preview | False | disabled_with_reason | disabled_pending_result_report_tab_router |
| bio_result_report | `resultReportTabButton` | 报告草稿 / Report Draft | False | disabled_with_reason | disabled_pending_result_report_tab_router |
| bio_result_report | `resultReportTabButton` | 导出管理 / Export Mgmt | False | disabled_with_reason | disabled_pending_result_report_tab_router |
| bio_result_report | `resultReportTabButton` | 历史记录 / History | False | disabled_with_reason | disabled_pending_result_report_tab_router |
| bio_result_report | `resultReportPrimaryButton` | 生成报告草稿 | False | disabled_with_reason | requires_formal_result_for_report_draft |
| bio_result_report | `resultReportGhostButton` | 准备导出 | False | disabled_with_reason | requires_existing_result_or_route_context |
| bio_result_report | `resultReportRefreshButton` | 刷新结果 | True | not_clicked_safety_gate |  |
| bio_result_report | `resultReportOpenImportedDegButton` | 导入结果浏览 | True | not_clicked_safety_gate |  |
| bio_result_report | `resultReportOpenDraftButton` | 查看报告草稿 | True | not_clicked_safety_gate |  |
| bio_result_report | `formalDegReviewExportTsvButton` | 导出 DEG TSV | True | not_clicked_safety_gate |  |
| bio_result_report | `formalDegReviewExportCsvButton` | 导出 DEG CSV | True | not_clicked_safety_gate |  |
| bio_result_report | `formalDegPlotButton` | 生成 formal DEG plot artifact | False | disabled_with_reason | requires_formal_computed_deg_result |
| bio_result_report | `formalDegReportReadyButton` | 生成 formal DEG report-ready package | False | disabled_with_reason | requires_formal_deg_plot_or_table_only_gate |
| bio_result_report | `resultReportToggleDeveloperDiagnosticsButton` | 展开技术细节 | True | not_clicked_safety_gate |  |
| bio_result_report | `resultReportOpenResultsFolderButton` | 打开结果文件夹 | True | not_clicked_safety_gate |  |
| bio_result_report | `resultReportOpenParamsJsonButton` | 打开参数 JSON | True | not_clicked_safety_gate |  |
| bio_result_report | `resultReportContinueReportExportButton` | 继续：报告查看 | True | not_clicked_safety_gate |  |
| bio_report_export | `appSidebarButton` | 工作台 / Dashboard | True | not_clicked_safety_gate |  |
| bio_report_export | `appSidebarButton` | 生信分析 / Bioinformatics | True | not_clicked_safety_gate |  |
| bio_report_export | `appSidebarButton` | Meta 分析 / Meta Analysis | True | not_clicked_safety_gate |  |
| bio_report_export | `appSidebarButton` | 实验工具 / LabTools | True | not_clicked_safety_gate |  |
| bio_report_export | `appSidebarButton` | 管理中心 / Centers | True | not_clicked_safety_gate |  |
| bio_report_export | `appSidebarAuxButton` | 设置中心 / Settings | True | not_clicked_safety_gate |  |
| bio_report_export | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | not_clicked_safety_gate |  |
| bio_report_export | `appSidebarAuxButton` | 关于 / About | True | not_clicked_safety_gate |  |
| bio_report_export | `resultReportGhostButton` | 返回 Result & Report | True | not_clicked_safety_gate |  |
| bio_report_export | `reportExportRefreshDraftButton` | 刷新报告草稿 | True | not_clicked_safety_gate |  |
| bio_report_export | `reportExportOpenDraftFolderButton` | 打开报告草稿文件夹 | True | not_clicked_safety_gate |  |
| bio_report_export | `reportExportCopySummaryButton` | 复制报告摘要 | True | not_clicked_safety_gate |  |
| bio_report_export | `reportReadyExportButton` | 导出 report-ready package | False | disabled_with_reason | requires_report_ready_gate_passed |
| bio_report_export | `reportExportToggleDeveloperDiagnosticsButton` | 展开技术细节 | True | not_clicked_safety_gate |  |
| bio_report_export | `reportExportDeveloperOpenDraftFolderButton` | 打开报告草稿文件夹 | True | not_clicked_safety_gate |  |
| bio_settings_resources | `appSidebarButton` | 工作台 / Dashboard | True | not_clicked_safety_gate |  |
| bio_settings_resources | `appSidebarButton` | 生信分析 / Bioinformatics | True | not_clicked_safety_gate |  |
| bio_settings_resources | `appSidebarButton` | Meta 分析 / Meta Analysis | True | not_clicked_safety_gate |  |
| bio_settings_resources | `appSidebarButton` | 实验工具 / LabTools | True | not_clicked_safety_gate |  |
| bio_settings_resources | `appSidebarButton` | 管理中心 / Centers | True | not_clicked_safety_gate |  |
| bio_settings_resources | `appSidebarAuxButton` | 设置中心 / Settings | True | not_clicked_safety_gate |  |
| bio_settings_resources | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | not_clicked_safety_gate |  |
| bio_settings_resources | `appSidebarAuxButton` | 关于 / About | True | not_clicked_safety_gate |  |
| bio_settings_resources | `secondaryButton` | 返回项目首页 | True | not_clicked_safety_gate |  |
| bio_settings_resources | `secondaryButton` | 运行 GEO 环境检查 | True | not_clicked_safety_gate |  |
| bio_settings_resources | `secondaryButton` | 保存 AI 设置 | True | not_clicked_safety_gate |  |
| bio_settings_resources | `secondaryButton` | 测试连接 | True | not_clicked_safety_gate |  |
| bio_settings_resources | `secondaryButton` | 生成本地词库草稿 | True | not_clicked_safety_gate |  |
| sidebar | `appSidebarButton` | Meta 分析 / Meta Analysis | True | meta_analysis |  |
| meta_project_home | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace meta_analysis->dashboard |  |
| meta_project_home | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| meta_project_home | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| meta_project_home | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| meta_project_home | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| meta_project_home | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| meta_project_home | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| meta_project_home | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
| meta_question_meta_type | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace about->dashboard |  |
| meta_question_meta_type | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| meta_question_meta_type | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| meta_question_meta_type | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| meta_question_meta_type | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| meta_question_meta_type | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| meta_question_meta_type | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| meta_question_meta_type | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
| meta_search_strategy | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace about->dashboard |  |
| meta_search_strategy | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| meta_search_strategy | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| meta_search_strategy | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| meta_search_strategy | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| meta_search_strategy | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| meta_search_strategy | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| meta_search_strategy | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
| meta_import_dedup | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace about->dashboard |  |
| meta_import_dedup | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| meta_import_dedup | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| meta_import_dedup | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| meta_import_dedup | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| meta_import_dedup | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| meta_import_dedup | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| meta_import_dedup | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
| meta_screening | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace about->dashboard |  |
| meta_screening | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| meta_screening | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| meta_screening | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| meta_screening | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| meta_screening | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| meta_screening | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| meta_screening | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
| meta_fulltext_extraction | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace about->dashboard |  |
| meta_fulltext_extraction | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| meta_fulltext_extraction | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| meta_fulltext_extraction | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| meta_fulltext_extraction | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| meta_fulltext_extraction | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| meta_fulltext_extraction | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| meta_fulltext_extraction | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
| meta_quality_assessment | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace about->dashboard |  |
| meta_quality_assessment | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| meta_quality_assessment | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| meta_quality_assessment | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| meta_quality_assessment | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| meta_quality_assessment | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| meta_quality_assessment | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| meta_quality_assessment | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
| meta_analysis_tasks | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace about->dashboard |  |
| meta_analysis_tasks | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| meta_analysis_tasks | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| meta_analysis_tasks | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| meta_analysis_tasks | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| meta_analysis_tasks | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| meta_analysis_tasks | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| meta_analysis_tasks | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
| meta_result_report | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace about->dashboard |  |
| meta_result_report | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| meta_result_report | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| meta_result_report | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| meta_result_report | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| meta_result_report | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| meta_result_report | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| meta_result_report | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
| meta_report_export | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace about->dashboard |  |
| meta_report_export | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| meta_report_export | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| meta_report_export | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| meta_report_export | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| meta_report_export | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| meta_report_export | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| meta_report_export | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
| meta_meta_settings | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace about->dashboard |  |
| meta_meta_settings | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| meta_meta_settings | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| meta_meta_settings | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| meta_meta_settings | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| meta_meta_settings | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| meta_meta_settings | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| meta_meta_settings | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
| sidebar | `appSidebarButton` | 实验工具 / LabTools | True | labtools |  |
| labtools_home | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace labtools->dashboard |  |
| labtools_home | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| labtools_home | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| labtools_home | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| labtools_home | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| labtools_home | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| labtools_home | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| labtools_home | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
| labtools_general_calculators | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace about->dashboard |  |
| labtools_general_calculators | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| labtools_general_calculators | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| labtools_general_calculators | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| labtools_general_calculators | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| labtools_general_calculators | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| labtools_general_calculators | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| labtools_general_calculators | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
| labtools_reagent_preparation | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace about->dashboard |  |
| labtools_reagent_preparation | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| labtools_reagent_preparation | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| labtools_reagent_preparation | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| labtools_reagent_preparation | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| labtools_reagent_preparation | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| labtools_reagent_preparation | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| labtools_reagent_preparation | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
| labtools_experiment_modules | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace about->dashboard |  |
| labtools_experiment_modules | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| labtools_experiment_modules | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| labtools_experiment_modules | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| labtools_experiment_modules | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| labtools_experiment_modules | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| labtools_experiment_modules | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| labtools_experiment_modules | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
| labtools_cell_experiments | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace about->dashboard |  |
| labtools_cell_experiments | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| labtools_cell_experiments | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| labtools_cell_experiments | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| labtools_cell_experiments | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| labtools_cell_experiments | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| labtools_cell_experiments | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| labtools_cell_experiments | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
| labtools_protein_experiments | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace about->dashboard |  |
| labtools_protein_experiments | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| labtools_protein_experiments | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| labtools_protein_experiments | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| labtools_protein_experiments | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| labtools_protein_experiments | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| labtools_protein_experiments | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| labtools_protein_experiments | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
| labtools_nucleic_acid_experiments | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace about->dashboard |  |
| labtools_nucleic_acid_experiments | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| labtools_nucleic_acid_experiments | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| labtools_nucleic_acid_experiments | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| labtools_nucleic_acid_experiments | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| labtools_nucleic_acid_experiments | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| labtools_nucleic_acid_experiments | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| labtools_nucleic_acid_experiments | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
| labtools_immuno_absorbance | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace about->dashboard |  |
| labtools_immuno_absorbance | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| labtools_immuno_absorbance | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| labtools_immuno_absorbance | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| labtools_immuno_absorbance | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| labtools_immuno_absorbance | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| labtools_immuno_absorbance | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| labtools_immuno_absorbance | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
| labtools_ihc | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace about->dashboard |  |
| labtools_ihc | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| labtools_ihc | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| labtools_ihc | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| labtools_ihc | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| labtools_ihc | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| labtools_ihc | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| labtools_ihc | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
| sidebar | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | test_feedback |  |
| test_feedback | `appSidebarButton` | 工作台 / Dashboard | True | clicked; workspace test_feedback->dashboard |  |
| test_feedback | `appSidebarButton` | 生信分析 / Bioinformatics | True | clicked; workspace dashboard->bioinformatics |  |
| test_feedback | `appSidebarButton` | Meta 分析 / Meta Analysis | True | clicked; workspace bioinformatics->meta_analysis |  |
| test_feedback | `appSidebarButton` | 实验工具 / LabTools | True | clicked; workspace meta_analysis->labtools |  |
| test_feedback | `appSidebarButton` | 管理中心 / Centers | True | clicked; workspace labtools->centers |  |
| test_feedback | `appSidebarAuxButton` | 设置中心 / Settings | True | clicked; workspace centers->settings |  |
| test_feedback | `appSidebarAuxButton` | 测试反馈 / Test Feedback | True | clicked; workspace settings->test_feedback |  |
| test_feedback | `appSidebarAuxButton` | 关于 / About | True | clicked; workspace test_feedback->about |  |
