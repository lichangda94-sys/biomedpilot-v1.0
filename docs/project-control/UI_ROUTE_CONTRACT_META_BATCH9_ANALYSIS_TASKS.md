# UI Route Contract - Meta Batch 9 Analysis Tasks

- branch: `integration/release-bio-c1-ui-shell`
- head: `fc2cdb2028d6d01d1ccdac1906b3d5b2dbc66881`
- scope: Meta mature UIShell Analysis Tasks page: analysis plan draft, preflight/applicability artifacts, and formal executor gate.
- rows: `3`
- connected: `2`
- disabled: `1`
- broken: `0`

## Matrix

| contract | UI page | capability | object | status | observed |
| --- | --- | --- | --- | --- | --- |
| `META-ANALYSIS-PLAN-DRAFT` | Analysis Tasks | AnalysisSetupService.create_plan/save_analysis_plan | `metaBuildAnalysisPlanDraftButton` | `connected` | analysis_plan_draft_written={"analysis_profile_type": "TREATMENT_EFFECT_META", "errors": [], "report_ready": false, "warnings": ["developer_preview_analysis_plan"]} |
| `META-ANALYSIS-PREFLIGHT` | Analysis Tasks | AnalysisSetupService.run_preflight | `metaRunAnalysisPreflightButton` | `connected` | analysis_preflight_artifacts_written={"analysis_profile_type": "TREATMENT_EFFECT_META", "analysis_result_created": false, "dataset_created": true, "errors": ["extraction_records_missing", "extraction_records_empty", "analysis_ready_dataset_has_no_included_studies"], "formal_statistics_run": false, "report_ready": false, "success": false, "warnings": ["developer_preview_analysis_plan", "random_effects_tau_squared_unstable_with_fewer_than_three_studies", "or_rr_zero_event_continuity_correction_will_be_reported_when_applied"]} |
| `META-ANALYSIS-FORMAL-RUN-GATE` | Analysis Tasks | formal statistics execution disabled reason | `metaTargetBoundaryDisabledAction` | `disabled` | disabled_with_reason |

## Screenshots

- `analysis_tasks`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_meta_batch9_analysis_tasks/01_analysis_tasks.png`
- `analysis_after_preflight`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_meta_batch9_analysis_tasks/02_analysis_after_preflight.png`
