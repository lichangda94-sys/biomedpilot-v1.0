# UI Route Contract: Bio Batch 6 Survival/Clinical

- branch: `integration/release-bio-c1-ui-shell`
- head: `8b20ac157f3c582381cedc2690293327fc5c64f3`
- scope: Bioinformatics survival/clinical input gate, backend dependency detection, KM/log-rank/Cox/risk score disabled gates, and clinical report-ready gate.
- rows: 9
- connected: 4
- disabled: 5
- broken: 0

## Screenshots

- `docs/ui/runtime_screenshots/20260602_bio_batch6_survival/01_survival_clinical_gate.png`

## Route Rows

| Contract | Object | Status | Behavior | Evidence | Observed |
| --- | --- | --- | --- | --- | --- |
| BIO-SURVIVAL-BACK | `survivalBackButton` | connected | `navigates_back_to_analysis_tasks` | signal=back_requested | back_signal=True |
| BIO-SURVIVAL-CHOOSE-CLEANING-PLAN | `chooseSurvivalCleaningPlanButton` | connected | `selects_cleaning_plan_json` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch6_survival_zyhaefb_/project/bio_batch_6_survival/analysis/cleaning/geo_cleaning_plan.json | path_input=/private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch6_survival_zyhaefb_/project/bio_batch_6_survival/analysis/cleaning/geo_cleaning_plan.json |
| BIO-SURVIVAL-RUN-PREFLIGHT | `runSurvivalPreflightButton` | connected | `calls_survival_service_create_preflight_artifact` | /var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_bio_batch6_survival_zyhaefb_/projects/bio_batch_6_survival/bioinformatics/survival/geo_survival_preflight_fa5b2bf7522e.json | survival_analysis_executed=False |
| BIO-SURVIVAL-DETECT-BACKEND | `detectSurvivalBackendButton` | connected | `calls_survival_service_detect_backend_dependencies` | status=preflight_only; lifelines: available=False version=-; blockers=lifelines_missing_formal_survival_disabled; warnings=survival_backend_detection_only_no_km_cox_logrank_execution | status=preflight_only |
| BIO-SURVIVAL-KM-CURVE-GATE | `runKmCurveDisabledButton` | disabled | `disabled_km_curve_executor_not_connected` | km_curve_executor_not_connected | enabled=False; disabledReason=km_curve_executor_not_connected |
| BIO-SURVIVAL-LOGRANK-GATE | `runLogRankDisabledButton` | disabled | `disabled_logrank_executor_not_connected` | logrank_executor_not_connected | enabled=False; disabledReason=logrank_executor_not_connected |
| BIO-SURVIVAL-COX-MODEL-GATE | `runCoxModelDisabledButton` | disabled | `disabled_cox_model_executor_not_connected` | cox_model_executor_not_connected | enabled=False; disabledReason=cox_model_executor_not_connected |
| BIO-SURVIVAL-RISK-SCORE-GATE | `generateRiskScoreDisabledButton` | disabled | `disabled_risk_score_model_not_connected` | risk_score_model_not_connected | enabled=False; disabledReason=risk_score_model_not_connected |
| BIO-SURVIVAL-CLINICAL-REPORT-READY-GATE | `survivalReportExportDisabledButton` | disabled | `disabled_survival_clinical_report_ready_not_connected` | km_cox_logrank_risk_score_and_clinical_report_ready_gate_not_enabled | enabled=False; disabledReason=km_cox_logrank_risk_score_and_clinical_report_ready_gate_not_enabled |
