# Meta M10 Statistical Result State Gating Report - 2026-05-13

## Stage name

Meta M10 - Statistical Result State Gating

## Branch

- Worktree: `/Users/changdali/Developer/biomedpilot v1.0/Meta`
- Branch: `dev/meta-analysis`
- HEAD before work: `67d7f96` (`docs(meta): audit statistical executor integration`)

## Files changed

- `app/meta_analysis/models/statistical_result_state.py`
- `app/meta_analysis/models/analysis_result.py`
- `app/meta_analysis/services/analysis_run_service.py`
- `app/meta_analysis/services/analysis_setup_service.py`
- `app/meta_analysis/services/meta_statistics_engine_service.py`
- `app/meta_analysis/services/figure_result_service.py`
- `app/meta_analysis/services/advanced_analysis_service.py`
- `app/meta_analysis/services/formal_report_service.py`
- `app/meta_analysis/pages/analysis_page.py`
- `tests/meta_analysis/test_statistical_result_state_gating.py`
- `docs/meta_dev_reports/Meta_M10_statistical_result_state_gating_report_20260513.md`

## Behavior changed

- Added canonical statistical result states:
  - `not_run`
  - `configured_not_run`
  - `testing_level`
  - `failed_validation`
  - `computed`
  - `user_reviewed`
  - `report_ready`
- Added gating helpers for formal computed status, report-ready status, computed-state entry, report-ready entry, user-review requirement, and formal-report claim blocking.
- Added default testing-level metadata to the older `AnalysisResult` model and `AnalysisRunService` output.
- Preserved the older testing workflow, but made its outputs explicitly non-formal and blocked from report-ready status by default.
- Added result-state metadata to analysis result aliases, forest/funnel source summaries, and the newer `MetaStatisticsEngineService` standardized result.
- Updated report generation to summarize `not_run`, `configured_not_run`, `failed_validation`, and `testing_level` safely, and to require `report_ready` for any future formal statistical section.
- Updated analysis UI labels so testing-level results are shown as `测试级结果` / Developer Preview and no old-path output is presented as a formal computed result.

## Result semantics

- `testing_level` is never treated as `computed`.
- `configured_not_run` and `not_run` are not result outputs and do not support formal statistical claims.
- `failed_validation` preserves validation errors/warnings and blocks formal report claims.
- `computed` still requires user review before report-ready status.
- `report_ready` requires a computed/reviewed state and cannot be reached from testing-level output.
- Existing Developer Preview services continue to run, but they remain testing-level.
- M10 does not implement a real executor and does not upgrade any result to production, clinical, regulatory, publication-ready, or formal evidence status.

## Validation commands and exact results

```bash
git diff --check
# exit code 0; no output

python3 -m pytest tests/meta_analysis -q
# exit code 0
# 493 passed in 4.60s

QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
# exit code 0
# 154 passed in 10.12s

QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
# exit code 0
# BioMedPilot / 医研智析
# app_version=0.1.0-internal-beta
# app_channel=Developer Preview / testing
# launch_mode=source
# app_root=/Users/changdali/Developer/biomedpilot v1.0/Meta
# git_head=67d7f96
# workspace_entries=2
# bioinformatics_features=5
# meta_analysis_features=7
# pyside6_available=True
```

## Limitations

- No real statistical executor was implemented.
- No new pooled-effect, heterogeneity, p-value, forest plot, funnel plot, or final conclusion computation was added.
- Existing testing-level calculation helpers remain available for Developer Preview workflows.
- Future M11/M12 work still needs a validated executor, effect-size normalization, executor manifest, formal plot data contract, and parity validation.
- The untracked handoff input artifact remains intentionally uncommitted.

## Remaining dirty/untracked files before commit

```text
## dev/meta-analysis
 M app/meta_analysis/models/analysis_result.py
 M app/meta_analysis/pages/analysis_page.py
 M app/meta_analysis/services/advanced_analysis_service.py
 M app/meta_analysis/services/analysis_run_service.py
 M app/meta_analysis/services/analysis_setup_service.py
 M app/meta_analysis/services/figure_result_service.py
 M app/meta_analysis/services/formal_report_service.py
 M app/meta_analysis/services/meta_statistics_engine_service.py
?? app/meta_analysis/models/statistical_result_state.py
?? docs/meta_dev_reports/Meta_M10_statistical_result_state_gating_report_20260513.md
?? docs/meta_dev_reports/Meta_handoff_report_20260513.md
?? tests/meta_analysis/test_statistical_result_state_gating.py
```

Expected preserved untracked input artifact:

- `docs/meta_dev_reports/Meta_handoff_report_20260513.md`

## Commit hash if committed

Commit made with message:

`feat(meta): gate statistical result states`

The final commit hash is reported in the assistant handoff after commit creation. No remote push is in scope.
