# UI Route Contract Phase 1 Batch 0 Report

- created_at: `2026-06-02T14:25:47.644080+00:00`
- branch: `integration/release-bio-c1-ui-shell`
- head: `f650bfde88b33af780c547bb1b98f41341d05232`
- scope: Shell freeze route and live-click audit for Welcome, Home, Sidebar, and Centers.

## Summary

- row_count: `28`
- connected: `23`
- disabled: `5`
- broken: `0`

## Contract Rows

| Contract ID | Module | Surface | Object | Behavior | Runtime Effect | Status | Observed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SHELL-WELCOME-ENTER | Shell | Welcome | `primaryButton` | `navigates_to_shell_route_dashboard` | navigates to Dashboard from Welcome | `connected` | expected=dashboard; observed=dashboard |
| SHELL-WELCOME-ABOUT | Shell | Welcome | `aboutButton` | `navigates_to_shell_route_about` | navigates to About from Welcome | `connected` | expected=about; observed=about |
| SHELL-WELCOME-SETTINGS | Shell | Welcome | `loginTopIconButton` | `navigates_to_shell_route_settings` | navigates to Settings from Welcome | `connected` | expected=settings; observed=settings |
| SHELL-HOME-BIO | Shell | Home / Dashboard | `bioModuleButton` | `navigates_to_module_workspace_nav.bioinformatics` | navigates to Bioinformatics adapter | `connected` | expected=bioinformatics; observed=bioinformatics |
| SHELL-HOME-META | Shell | Home / Dashboard | `metaModuleButton` | `navigates_to_module_workspace_nav.meta_analysis` | navigates to Meta Analysis adapter | `connected` | expected=meta_analysis; observed=meta_analysis |
| SHELL-HOME-LABTOOLS | Shell | Home / Dashboard | `labtoolsModuleButton` | `navigates_to_module_workspace_nav.labtools` | navigates to LabTools adapter | `connected` | expected=labtools; observed=labtools |
| SHELL-HOME-dashboardHeaderIconButton-通知 | Shell | Home / Dashboard | `dashboardHeaderIconButton` | `disabled_dashboard_header_developer_preview_not_connected` | disabled placeholder with explicit reason | `disabled` | disabled_reason_present |
| SHELL-HOME-dashboardHeaderIconButton-帮助 | Shell | Home / Dashboard | `dashboardHeaderIconButton` | `disabled_dashboard_header_settings_not_connected` | disabled placeholder with explicit reason | `disabled` | disabled_reason_present |
| SHELL-HOME-dashboardOpenMoreProjectsButton-打开更多项目... | Shell | Home / Dashboard | `dashboardOpenMoreProjectsButton` | `disabled_project_center_open_more_not_connected` | disabled placeholder with explicit reason | `disabled` | disabled_reason_present |
| SHELL-HOME-dashboardViewAllProjectsButton-查看全部项目（12） | Shell | Home / Dashboard | `dashboardViewAllProjectsButton` | `disabled_project_center_open_all_not_connected` | disabled placeholder with explicit reason | `disabled` | disabled_reason_present |
| SHELL-SIDEBAR-DASHBOARD | Shell | Sidebar | `appSidebarButton` | `navigates_to_shell_route_dashboard` | navigates to dashboard | `connected` | expected=dashboard; observed=dashboard |
| SHELL-SIDEBAR-BIOINFORMATICS | Shell | Sidebar | `appSidebarButton` | `navigates_to_shell_route_bioinformatics` | navigates to bioinformatics | `connected` | expected=bioinformatics; observed=bioinformatics |
| SHELL-SIDEBAR-META_ANALYSIS | Shell | Sidebar | `appSidebarButton` | `navigates_to_shell_route_meta_analysis` | navigates to meta_analysis | `connected` | expected=meta_analysis; observed=meta_analysis |
| SHELL-SIDEBAR-LABTOOLS | Shell | Sidebar | `appSidebarButton` | `navigates_to_shell_route_labtools` | navigates to labtools | `connected` | expected=labtools; observed=labtools |
| SHELL-SIDEBAR-CENTERS | Shell | Sidebar | `appSidebarButton` | `navigates_to_shell_route_centers` | navigates to centers | `connected` | expected=centers; observed=centers |
| SHELL-SIDEBAR-SETTINGS | Shell | Sidebar | `appSidebarAuxButton` | `navigates_to_shell_route_settings` | navigates to settings | `connected` | expected=settings; observed=settings |
| SHELL-SIDEBAR-TEST_FEEDBACK | Shell | Sidebar | `appSidebarAuxButton` | `navigates_to_shell_route_test_feedback` | navigates to test_feedback | `connected` | expected=test_feedback; observed=test_feedback |
| SHELL-SIDEBAR-ABOUT | Shell | Sidebar | `appSidebarAuxButton` | `navigates_to_shell_route_about` | navigates to about | `connected` | expected=about; observed=about |
| SHELL-CENTERS-REFRESHPROJECTS | Centers | Centers | `centersRefreshProjectsButton` | `calls_project_center_recent_projects` | calls ProjectCenter recent projects | `connected` | artifact_or_service_verified |
| SHELL-CENTERS-CREATEPROJECTRECORD | Centers | Centers | `centersCreateProjectRecordButton` | `calls_project_center_create_project_and_writes_projects_index` | writes ProjectCenter index | `connected` | artifact_or_service_verified |
| SHELL-CENTERS-REFRESHDATA | Centers | Centers | `centersRefreshDataButton` | `calls_data_center_list_assets` | calls DataCenter list assets | `connected` | artifact_or_service_verified |
| SHELL-CENTERS-EXPORTDATAINDEX | Centers | Centers | `centersExportDataIndexButton` | `writes_data_center_index_summary_artifact` | writes data center index summary artifact | `connected` | artifact_or_service_verified |
| SHELL-CENTERS-REFRESHTASKS | Centers | Centers | `centersRefreshTasksButton` | `calls_task_center_list_tasks` | calls TaskCenter list tasks | `connected` | artifact_or_service_verified |
| SHELL-CENTERS-CREATETASK | Centers | Centers | `centersCreateTaskButton` | `calls_task_center_register_testing_task` | writes TaskCenter index | `connected` | artifact_or_service_verified |
| SHELL-CENTERS-BUILDREPORTINDEX | Centers | Centers | `centersBuildReportIndexButton` | `writes_report_center_index_summary_artifact` | writes report center index artifact | `connected` | artifact_or_service_verified |
| SHELL-CENTERS-RUNENVIRONMENTCHECK | Centers | Centers | `centersRunEnvironmentCheckButton` | `calls_check_local_environment_and_writes_status_artifact` | writes environment status artifact | `connected` | artifact_or_service_verified |
| SHELL-CENTERS-BUILDPACKAGINGPREFLIGHT | Centers | Centers | `centersBuildPackagingPreflightButton` | `writes_packaging_preflight_artifact` | writes packaging preflight artifact | `connected` | artifact_or_service_verified |
| SHELL-CENTERS-centersRunReleaseBuildButton-执行 release build | Shell | Centers | `centersRunReleaseBuildButton` | `disabled_release_build_requires_explicit_release_build_command` | disabled placeholder with explicit reason | `disabled` | disabled_reason_present |
