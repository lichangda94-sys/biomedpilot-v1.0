# Integration J - Meta M10-M13 User Path Fix

## Scope

- Worktree: `/Users/changdali/Developer/biomedpilot v1.0/Integration`
- Branch: `dev/integration`
- HEAD before work: `141429c`
- Scope: Meta Integration corrective fix only.

## Issues addressed

1. The active 8-step Meta workspace statistics page did not expose the M10-M13 user path. It still showed the older statistics runner surface and a raw JSON-style result preview.
2. `AnalysisPlanService.confirm_plan()` did not write `plan_state=confirmed`, while the M12 pairwise executor gate required a confirmed plan state.
3. M12 `failed_validation` execution attempted to write an `analysis_run_failed_validation` audit event that was not registered in `AUDIT_EVENT_TYPES`.

## Changes made

- Updated active `MetaAnalysisWorkspaceWidget` statistics page to expose:
  - `效应量标准化预检查`
  - `Pairwise executor`
  - `统计结果审核`
  - `已确认查看警告`
  - `接受进入报告草稿`
  - `标记需要修订`
  - `不纳入报告`
  - `申请报告就绪`
- Removed the raw JSON result preview from the main statistics UI and replaced it with Chinese user-facing summary cards.
- Kept internal paths in collapsed developer diagnostics only.
- Added `plan_state=confirmed` to confirmed analysis plan payloads.
- Added backward-compatible M12 plan readiness logic for existing confirmed plans that have `confirmed_analysis_plan_id` and `locked_for_analysis_run`.
- Registered `analysis_run_failed_validation` as an audit event.
- Added regressions covering active workspace UI exposure, confirmed plan schema, real confirmed-plan M12 execution, and failed-validation audit persistence.

## Result semantics

- M12 computed outputs remain Developer Preview / testing.
- `computed` is not automatically `report_ready`.
- `report_ready` remains a draft report workflow state only; it is not production, clinical, regulatory, submission-ready, publication-ready, or formal evidence status.
- Failed validation is now persisted and auditable as user-understandable state instead of throwing from audit logging.

## Validation

- `git diff --check`
  - Result: passed with no output.
- Targeted regression:
  - `python3 -m pytest tests/meta_analysis/test_pairwise_meta_executor_service.py::test_m12_execute_accepts_real_confirmed_plan_from_analysis_plan_service tests/meta_analysis/test_pairwise_meta_executor_service.py::test_m12_execute_failed_validation_persists_and_audits_without_exception tests/meta_analysis/test_meta_workspace_ui_navigation.py::test_meta_workspace_statistics_step_exposes_m10_m13_user_path -q`
  - Result: `3 passed in 0.88s`
- `python3 -m pytest tests/meta_analysis -q`
  - Result: `517 passed in 8.08s`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - Result: `178 passed in 13.70s`
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`
  - Result:

```text
BioMedPilot / 医研智析
app_version=0.1.0-internal-beta
app_channel=Developer Preview / testing
launch_mode=source
app_root=/Users/changdali/Developer/biomedpilot v1.0/Integration
git_head=141429c
workspace_entries=3
bioinformatics_features=5
meta_analysis_features=7
labtools_features=4
pyside6_available=True
```

## Files changed

- `app/meta_analysis/services/analysis_plan_service.py`
- `app/meta_analysis/services/audit_log_service.py`
- `app/meta_analysis/services/pairwise_meta_executor_service.py`
- `app/meta_analysis/workspace.py`
- `tests/meta_analysis/test_analysis_plan_builder_v1.py`
- `tests/meta_analysis/test_meta_workspace_ui_navigation.py`
- `tests/meta_analysis/test_pairwise_meta_executor_service.py`
- `docs/integration/Integration_j_meta_m10_m13_user_path_fix_20260513.md`

## Limitations

- This stage does not apply the fix to MainLine.
- This stage does not add new statistical models, random effects, network meta-analysis, diagnostic meta-analysis, plots, subgroup automation, sensitivity automation, publication-bias automation, or formal conclusions.
