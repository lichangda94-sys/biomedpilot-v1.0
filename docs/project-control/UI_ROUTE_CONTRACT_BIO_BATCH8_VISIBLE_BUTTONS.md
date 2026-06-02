# Bioinformatics Batch 8 Visible Button Route Contract

- branch: `integration/release-bio-c1-ui-shell`
- head: `b47d29ba66a4395cf0ab7324df9d8cd42adccd41`
- scope: Bioinformatics C1 mature 7-step visible-button closure: every visible button is live-clicked or verified disabled with reason.
- row_count: `94`
- connected: `56`
- disabled: `38`
- broken: `0`
- external_open_calls: `4`

## Rows

| page | object | label | status | behavior | evidence |
| --- | --- | --- | --- | --- | --- |
| `project_home` | `bioinformaticsIANavItem` | 01 / 项目首页 / Project Home / 管理项目与团队 / 查看进度与关键状态 | `connected` | `navigates_to_bio_target_ia_page_project_home` | already_on=project_home |
| `project_home` | `bioinformaticsIANavItem` | 02 / 数据来源 / Data Source / 连接并获取数据 / 支持多种来源检索 | `connected` | `navigates_to_bio_target_ia_page_data_source` | project_home/project_home -> data_source/data_source |
| `project_home` | `bioinformaticsIANavItem` | 03 / 数据检查与准备 / Data Check & Prep / 完成质量检查与预处理 / 构建分析数据集 | `connected` | `navigates_to_bio_target_ia_page_data_check_preparation` | project_home/project_home -> recognition/data_check_preparation |
| `project_home` | `bioinformaticsIANavItem` | 04 / 分组与分析设计 / Group & Design / 定义分组与比较方案 / 设置协变量设计 | `connected` | `navigates_to_bio_target_ia_page_group_design` | project_home/project_home -> group_design/group_design |
| `project_home` | `bioinformaticsIANavItem` | 05 / 分析任务 / Analysis Tasks / 配置任务并查看 gate / 管理执行状态 | `connected` | `navigates_to_bio_target_ia_page_analysis_tasks` | manifests/analysis_task_center.json; results/summaries/result_index.json |
| `project_home` | `bioinformaticsIANavItem` | 06 / 结果与报告 / Result & Report / 审阅结果与报告草稿 / 区分结果语义 | `connected` | `navigates_to_bio_target_ia_page_result_report` | project_home/project_home -> results_browser/result_report |
| `project_home` | `bioinformaticsIANavItem` | 07 / 报告导出 / Report Export / 检查 report-ready gate / 导出受控报告包 | `connected` | `navigates_to_bio_target_ia_page_report_export` | project_home/project_home -> report_viewer/report_export |
| `project_home` | `bioinformaticsIANavItem` | 生信分析设置 / Resources / 管理资源、参数配置与外部工具连接。 | `connected` | `navigates_to_bio_target_ia_page_settings_resources` | project_home/project_home -> settings/settings_resources |
| `project_home` | `bioinformaticsIANavItem` | 项目日志与技术详情 / Project Logs & Details / 查看运行记录与技术细节。 | `connected` | `navigates_to_bio_target_ia_page_project_logs_technical_details` | project_home/project_home -> workflow_status/project_logs_technical_details |
| `project_home` | `quickAccessButton` | 最近使用 / 快速访问最近项目或流程 | `disabled` | `disabled_bio_quick_access_project_center_pending` | Bioinformatics quick access center is planned for Project Center remediation. |
| `project_home` | `quickAccessButton` | 使用指南 / 查看流程说明与示例 | `disabled` | `disabled_bio_quick_access_project_center_pending` | Bioinformatics quick access center is planned for Project Center remediation. |
| `project_home` | `quickAccessButton` | 常见问题 / 查看常见问题与解决方案 | `disabled` | `disabled_bio_quick_access_project_center_pending` | Bioinformatics quick access center is planned for Project Center remediation. |
| `project_home` | `quickAccessButton` | 意见反馈 / 提出建议或报告问题 | `disabled` | `disabled_bio_quick_access_project_center_pending` | Bioinformatics quick access center is planned for Project Center remediation. |
| `data_source` | `secondaryButton` | 返回项目首页 | `connected` | `navigates_back_to_previous_bio_page` | data_source/data_source -> project_home/project_home |
| `data_source` | `dataSourceTabButton` | 数据来源选择 | `disabled` | `disabled_until_tab_router_connected` | disabled_pending_data_source_tab_router |
| `data_source` | `dataSourceTabButton` | 已获取数据 | `disabled` | `disabled_until_tab_router_connected` | disabled_pending_data_source_tab_router |
| `data_source` | `dataSourceTabButton` | 检索记录 | `disabled` | `disabled_until_tab_router_connected` | disabled_pending_data_source_tab_router |
| `data_source` | `dataSourceTabButton` | 数据连接管理 | `disabled` | `disabled_until_tab_router_connected` | disabled_pending_data_source_tab_router |
| `data_source` | `bioinformaticsDataSourceSelectPreviewButton` | 配置 GEO 来源 | `connected` | `creates_data_source_request_draft_when_project_open` | manifests/data_source_requests.json; manifests/data_source_requests/dsr-672c2ce42f.json |
| `data_source` | `bioinformaticsDataSourceSelectPreviewButton` | 配置 TCGA 来源 | `connected` | `creates_data_source_request_draft_when_project_open` | manifests/data_source_requests/dsr-cb1c7d1d24.json |
| `data_source` | `bioinformaticsDataSourceSelectPreviewButton` | 配置 GTEx 来源 | `connected` | `creates_data_source_request_draft_when_project_open` | manifests/data_source_requests/dsr-fbc79db66b.json |
| `data_source` | `bioinformaticsDataSourceSelectPreviewButton` | 配置本地导入 | `connected` | `creates_data_source_request_draft_when_project_open` | manifests/data_source_requests/dsr-862917a8f0.json |
| `data_source` | `dataSourceResearchSearchButton` | 进入检索 | `connected` | `calls_bio_search_or_preview_service` | data_source/data_source -> chinese_search/data_source |
| `data_source` | `` | 查看详情 | `connected` | `toggles_or_opens_bio_diagnostics` | page text digest changed |
| `data_source` | `secondaryButton` | 下载所选 | `disabled` | `exports_opens_or_copies_existing_bio_artifact` | disabled_until_data_source_project_gate_passes |
| `data_source` | `secondaryButton` | 删除所选 | `disabled` | `removes_selected_bio_project_binding_after_gate` | disabled_until_data_source_project_gate_passes |
| `data_source` | `dataSourceQuickAccessButton` | 最近使用 / 快速访问最近使用的数据项目 | `disabled` | `disabled_until_project_help_center_connected` | disabled_pending_project_help_center |
| `data_source` | `dataSourceQuickAccessButton` | 使用指南 / 查看数据来源与导入说明 | `disabled` | `disabled_until_project_help_center_connected` | disabled_pending_project_help_center |
| `data_source` | `dataSourceQuickAccessButton` | 常见问题 / 查看常见问题与解决方案 | `disabled` | `disabled_until_project_help_center_connected` | disabled_pending_project_help_center |
| `data_source` | `dataSourceQuickAccessButton` | 意见反馈 / 提出建议或报告问题 | `disabled` | `disabled_until_project_help_center_connected` | disabled_pending_project_help_center |
| `data_check_preparation` | `secondaryButton` | 返回数据导入与检索 | `connected` | `navigates_back_to_previous_bio_page` | recognition/data_check_preparation -> data_source/data_source |
| `data_check_preparation` | `secondaryButton` | 删除所选 | `disabled` | `removes_selected_bio_project_binding_after_gate` | disabled_until_recognition_input_selected |
| `data_check_preparation` | `primaryButton` | 开始识别 | `connected` | `runs_bio_preflight_or_gated_service` | page text digest changed |
| `data_check_preparation` | `secondaryButton` | 刷新 | `connected` | `reloads_current_bio_project_artifacts` | refresh completed without exception |
| `data_check_preparation` | `secondaryButton` | 技术详情 | `connected` | `toggles_or_opens_bio_diagnostics` | page text digest changed |
| `data_check_preparation` | `secondaryButton` | 技术操作 | `connected` | `toggles_or_opens_bio_diagnostics` | page text digest changed |
| `data_check_preparation` | `primaryButton` | 继续：数据准备与标准化 | `connected` | `navigates_to_next_bio_gate_after_validation` | logs/readiness/readiness_report.json; manifests/analysis_capability_matrix.json; user_data/bioinformatics/gene_sets/gene_set_registry.json |
| `group_design` | `secondaryButton` | 返回数据检查 | `connected` | `navigates_back_to_previous_bio_page` | group_design/group_design -> readiness/data_check_preparation |
| `group_design` | `groupDesignTabButton` | 分组设置 | `disabled` | `disabled_until_tab_router_connected` | disabled_pending_group_design_tab_router |
| `group_design` | `groupDesignTabButton` | 对比关系 | `disabled` | `disabled_until_tab_router_connected` | disabled_pending_group_design_tab_router |
| `group_design` | `groupDesignTabButton` | 协变量设置 | `disabled` | `disabled_until_tab_router_connected` | disabled_pending_group_design_tab_router |
| `group_design` | `groupDesignTabButton` | 分析策略 | `disabled` | `disabled_until_tab_router_connected` | disabled_pending_group_design_tab_router |
| `group_design` | `groupDesignTabButton` | 多因素设计 | `disabled` | `disabled_until_tab_router_connected` | disabled_pending_group_design_tab_router |
| `group_design` | `groupDesignPrimaryButton` | +  新建分组 | `disabled` | `disabled_group_creation_preview` | disabled_manual_design_editor_not_connected |
| `group_design` | `groupDesignGhostButton` | 下载模板 | `disabled` | `disabled_template_export_preview` | disabled_manual_design_aux_action_not_connected |
| `group_design` | `groupDesignPrimaryButton` | +  新建对比 | `disabled` | `disabled_manual_comparison_preview` | disabled_manual_design_editor_not_connected |
| `group_design` | `groupDesignGhostButton` | 查看详情 | `disabled` | `toggles_or_opens_bio_diagnostics` | disabled_manual_design_aux_action_not_connected |
| `group_design` | `bioinformaticsGroupDesignRefreshButton` | 刷新分组设计 | `connected` | `reloads_current_bio_project_artifacts` | refresh completed without exception |
| `group_design` | `bioinformaticsGroupDesignSuggestionButton` | 从对照组生成比较 | `connected` | `writes_bio_project_draft_or_artifact` | analysis/group_design/one_vs_control_suggestions_preview.json |
| `group_design` | `bioinformaticsGroupDesignSaveButton` | 保存分组与比较设计 | `connected` | `writes_bio_project_draft_or_artifact` | manifests/group_comparison_design.json |
| `group_design` | `bioinformaticsRunPreflightGatedButton` | Run Preflight - gated preview | `disabled` | `disabled_gated_preflight_preview` | disabled_preflight_preview_only_no_formal_model_run |
| `group_design` | `secondaryButton` | 展开技术详情 | `connected` | `toggles_or_opens_bio_diagnostics` | page text digest changed |
| `group_design` | `bioinformaticsGroupDesignContinueButton` | 继续：分析任务中心 | `connected` | `navigates_to_next_bio_gate_after_validation` | group_design/group_design -> analysis_tasks/analysis_tasks |
| `analysis_tasks` | `analysisTaskPrimaryButton` | 参数总览 | `disabled` | `disabled_analysis_parameter_overview_placeholder` | disabled_analysis_overview_placeholder |
| `analysis_tasks` | `analysisTaskGhostButton` | 分析文档 | `disabled` | `disabled_analysis_documentation_placeholder` | disabled_analysis_documentation_placeholder |
| `analysis_tasks` | `bioinformaticsAnalysisRefreshButton` | 刷新任务状态 | `connected` | `calls_load_analysis_task_center` | refresh completed without exception |
| `analysis_tasks` | `bioinformaticsAnalysisComparisonConfigButton` | 确认分组与比较设计 | `connected` | `writes_manual_comparison_config_and_reruns_readiness` | acquisition/handoffs/acq-0713914b.json; acquisition/plans/acq-0713914b.json; acquisition/records/acq-0713914b.json; acquisition/source_manifests/acq-0713914b_source_manifest.json; raw_data/local_import/manual_supplements/comparison_config_manual.tsv |
| `analysis_tasks` | `bioinformaticsAnalysisOpenDegConfigButton` | 进入差异分析配置 | `connected` | `opens_deg_config_preflight_page` | analysis_tasks/analysis_tasks -> deg_config/analysis_tasks |
| `analysis_tasks` | `analysisTaskConfirmFormalDegParametersButton` | 确认 formal DEG 参数 | `disabled` | `writes_formal_deg_parameter_confirmation` | requires_formal_deg_parameter_manifest_and_dependency_snapshot |
| `analysis_tasks` | `analysisTaskRunFormalControlledDegButton` | 运行两组 controlled DEG | `disabled` | `runs_formal_controlled_deg_when_gate_passes` | requires_confirmed_formal_deg_gate |
| `analysis_tasks` | `openImmuneScoringGateButton` | 免疫浸润 / TME评分 | `connected` | `opens_immune_scoring_exploratory_page` | analysis_tasks/analysis_tasks -> immune_scoring/analysis_tasks |
| `analysis_tasks` | `openEnrichmentGateButton` | 富集 ORA/GSEA gate | `connected` | `opens_enrichment_preflight_gate_page` | analysis_tasks/analysis_tasks -> enrichment/analysis_tasks |
| `analysis_tasks` | `openSurvivalClinicalGateButton` | Survival / clinical gate | `connected` | `opens_survival_clinical_preflight_gate_page` | analysis_tasks/analysis_tasks -> survival/analysis_tasks |
| `analysis_tasks` | `openImportedDegBrowserButton` | 查看已导入差异分析结果 | `connected` | `opens_imported_external_result_browser` | analysis_tasks/analysis_tasks -> imported_deg/result_report |
| `analysis_tasks` | `analysisTaskToggleDeveloperDiagnosticsButton` | 展开技术细节 | `connected` | `toggles_developer_diagnostics` | page text digest changed |
| `analysis_tasks` | `analysisTaskCreateTaskRecordButton` | 创建指定任务记录 | `connected` | `writes_task_record_draft` | page text digest changed |
| `analysis_tasks` | `analysisTaskRunTestingGeoDegButton` | 生成测试级 GEO 差异结果 | `connected` | `developer_testing_geo_deg_runner` | page text digest changed |
| `analysis_tasks` | `analysisTaskContinueResultsButton` | 继续：结果浏览 | `connected` | `opens_result_report_after_task_record_exists` | page text digest changed |
| `result_report` | `resultReportGhostButton` | 返回分析任务 | `connected` | `navigates_back_to_previous_bio_page` | results_browser/result_report -> analysis_tasks/analysis_tasks |
| `result_report` | `resultReportGhostButton` | 刷新 | `connected` | `calls_load_result_index` | refresh completed without exception |
| `result_report` | `resultReportTabButton` | 结果预览 / Result Preview | `disabled` | `disabled_until_tab_router_connected` | disabled_pending_result_report_tab_router |
| `result_report` | `resultReportTabButton` | 报告草稿 / Report Draft | `disabled` | `disabled_until_tab_router_connected` | disabled_pending_result_report_tab_router |
| `result_report` | `resultReportTabButton` | 导出管理 / Export Mgmt | `disabled` | `disabled_until_tab_router_connected` | disabled_pending_result_report_tab_router |
| `result_report` | `resultReportTabButton` | 历史记录 / History | `disabled` | `disabled_until_tab_router_connected` | disabled_pending_result_report_tab_router |
| `result_report` | `resultReportPrimaryButton` | 生成报告草稿 | `disabled` | `disabled_report_draft_missing_formal_result` | requires_formal_result_for_report_draft |
| `result_report` | `resultReportGhostButton` | 准备导出 | `disabled` | `disabled_missing_report_ready` | requires_existing_result_or_route_context |
| `result_report` | `resultReportRefreshButton` | 刷新结果 | `connected` | `calls_load_result_index_and_formal_deg_gates` | refresh completed without exception |
| `result_report` | `resultReportOpenImportedDegButton` | 导入结果浏览 | `connected` | `opens_imported_external_result_browser` | results_browser/result_report -> imported_deg/result_report |
| `result_report` | `resultReportOpenDraftButton` | 查看报告草稿 | `connected` | `opens_report_export_gate_when_result_exists` | page text digest changed |
| `result_report` | `formalDegReviewExportTsvButton` | 导出 DEG TSV | `connected` | `exports_formal_deg_review_table_when_gate_passes` | page text digest changed |
| `result_report` | `formalDegReviewExportCsvButton` | 导出 DEG CSV | `connected` | `exports_formal_deg_review_table_when_gate_passes` | page text digest changed |
| `result_report` | `formalDegPlotButton` | 生成 formal DEG plot artifact | `disabled` | `creates_formal_deg_plot_artifact_when_gate_passes` | requires_formal_computed_deg_result |
| `result_report` | `formalDegReportReadyButton` | 生成 formal DEG report-ready package | `disabled` | `creates_formal_deg_report_ready_package_when_gate_passes` | requires_formal_deg_plot_or_table_only_gate |
| `result_report` | `resultReportToggleDeveloperDiagnosticsButton` | 展开技术细节 | `connected` | `toggles_developer_diagnostics` | page text digest changed |
| `result_report` | `resultReportOpenResultsFolderButton` | 打开结果文件夹 | `connected` | `opens_results_folder` | file:///private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch8_ookgzbgz/project/bio_batch_8_visible_buttons/results |
| `result_report` | `resultReportOpenParamsJsonButton` | 打开参数 JSON | `connected` | `opens_result_manager_json` | file:///private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch8_ookgzbgz/project/bio_batch_8_visible_buttons/manifests/result_manager.json |
| `result_report` | `resultReportContinueReportExportButton` | 继续：报告查看 | `connected` | `opens_report_export_gate_when_result_exists` | page text digest changed |
| `report_export` | `resultReportGhostButton` | 返回 Result & Report | `connected` | `navigates_back_to_previous_bio_page` | report_viewer/report_export -> results_browser/result_report |
| `report_export` | `reportExportRefreshDraftButton` | 刷新报告草稿 | `connected` | `generates_markdown_report_draft_only` | logs/reports/project_report_builder_report.json; reports/project_analysis_report.md; reports/project_report_manifest.json |
| `report_export` | `reportExportOpenDraftFolderButton` | 打开报告草稿文件夹 | `connected` | `opens_report_draft_folder` | file:///private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch8_ookgzbgz/project/bio_batch_8_visible_buttons/reports |
| `report_export` | `reportExportCopySummaryButton` | 复制报告摘要 | `connected` | `copies_report_draft_summary` | page text digest changed |
| `report_export` | `reportReadyExportButton` | Export report-ready package | `disabled` | `exports_report_ready_package_when_gate_passes` | requires_report_ready_gate_passed |
| `report_export` | `reportExportToggleDeveloperDiagnosticsButton` | 展开技术细节 | `connected` | `toggles_developer_diagnostics` | page text digest changed |
| `report_export` | `reportExportDeveloperOpenDraftFolderButton` | 打开报告草稿文件夹 | `connected` | `opens_report_draft_folder` | file:///private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch8_ookgzbgz/project/bio_batch_8_visible_buttons/reports |

## Screenshots

- `project_home`: `docs/ui/runtime_screenshots/20260602_bio_batch8_visible_buttons/01_project_home.png`
- `data_source`: `docs/ui/runtime_screenshots/20260602_bio_batch8_visible_buttons/02_data_source.png`
- `data_check_preparation`: `docs/ui/runtime_screenshots/20260602_bio_batch8_visible_buttons/03_data_check_preparation.png`
- `group_design`: `docs/ui/runtime_screenshots/20260602_bio_batch8_visible_buttons/04_group_design.png`
- `analysis_tasks`: `docs/ui/runtime_screenshots/20260602_bio_batch8_visible_buttons/05_analysis_tasks.png`
- `result_report`: `docs/ui/runtime_screenshots/20260602_bio_batch8_visible_buttons/06_result_report.png`
- `report_export`: `docs/ui/runtime_screenshots/20260602_bio_batch8_visible_buttons/07_report_export.png`
