# Integration -> MainLine Meta M10-M13 Scoped Carry-over Precheck - 2026-05-13

## Decision

`READY_FOR_MAINLINE_SCOPED_CARRYOVER_PREP`

Meta M10-M13 is now suitable to enter a MainLine scoped carry-over apply stage, provided the next stage applies only the approved M10-M13 runtime/UI/test set and does not merge either `dev/meta-analysis` or `dev/integration` wholesale.

This precheck did not modify MainLine, did not run packaging, did not overwrite `/Users/changdali/Desktop/BioMedPilot Dev.app`, did not overwrite any existing `BioMedPilot.app`, and did not push remote.

## Source and baseline

| Item | State |
| --- | --- |
| MainLine baseline | `stable/mainline` at `fd0b9a0` |
| Integration candidate | `dev/integration` at `ba58540` |
| Meta source validation | `dev/meta-analysis` at `5eaf2b1` |
| Meta dirty status | clean except untracked `docs/meta_dev_reports/Meta_handoff_report_20260513.md` |
| Preferred MainLine apply source | Integration `ba58540`, because its workspace wiring matches MainLine's current `statistics_analysis -> _statistics_analysis_page` route |

## Precheck result

Status: `PASS_FOR_SCOPED_APPLY`

The M10-M13 user flow has passed in both the Meta source branch and Integration candidate source:

`Meta entry -> analysis plan/statistics path -> effect size normalization preview -> pairwise fixed-effect executor -> computed -> user review -> report_ready -> report draft summary`

Confirmed behavior:

- active UI exposes `效应量标准化预检查`, `Pairwise executor`, `统计结果审核`, `运行 pairwise executor`, `接受进入报告草稿`, and `申请报告就绪`;
- confirmed plan state is present as `plan_state=confirmed`;
- M12 executor can reach `computed` from real confirmed plan and confirmed extraction rows;
- `computed` remains `report_ready=False` before user review;
- user review moves the result to `user_reviewed` while still keeping `report_ready=False`;
- explicit report-ready request/grant moves the result to `report_ready`;
- `report_ready` wording remains Developer Preview / testing and does not claim formal publication, clinical, regulatory, or production readiness;
- `failed_validation` is persisted and displayed without audit-event crash;
- report draft text does not include raw temporary project paths.

## Why this must remain scoped

`dev/meta-analysis` is not safe as a whole-branch MainLine input. Relative to `stable/mainline`, the branch contains broad Meta runtime changes:

- 96 Meta/UI/doc/test files in the compared scope;
- about 12,085 insertions and 1,277 deletions;
- M4-M14 reports and many earlier/later workflow surfaces beyond the M10-M13 user-flow fix.

`dev/integration` is also not a whole-branch MainLine input because it includes Integration-approved work beyond Meta, including LabTools and Bioinformatics scoped integrations.

Therefore the next stage must be a scoped apply, not a branch merge.

## MainLine route compatibility note

MainLine currently routes the `statistics_analysis` step to `_statistics_analysis_page`.

Meta `5eaf2b1` exposes M10-M13 through `_analysis_plan_page` / `_m10_m13_statistics_controls`, while Integration `ba58540` exposes the same user path through the MainLine-compatible `metaStatisticsAnalysisPage` route.

For MainLine carry-over, use the Integration `ba58540` workspace wiring as the route-compatible source, while preserving the semantics validated in Meta `5eaf2b1`.

## Approved scoped file set

Runtime/model files:

- `app/meta_analysis/models/analysis_result.py`
- `app/meta_analysis/models/statistical_result_state.py`
- `app/meta_analysis/models/effect_size_normalization.py`
- `app/meta_analysis/models/pairwise_meta_executor.py`
- `app/meta_analysis/models/result_review.py`
- `app/meta_analysis/services/analysis_plan_service.py`
- `app/meta_analysis/services/analysis_run_service.py`
- `app/meta_analysis/services/analysis_setup_service.py`
- `app/meta_analysis/services/audit_log_service.py`
- `app/meta_analysis/services/effect_size_normalization_service.py`
- `app/meta_analysis/services/figure_result_service.py`
- `app/meta_analysis/services/formal_report_service.py`
- `app/meta_analysis/services/meta_statistics_engine_service.py`
- `app/meta_analysis/services/pairwise_meta_executor_service.py`
- `app/meta_analysis/services/result_review_service.py`
- `app/meta_analysis/workspace.py`

Tests:

- `tests/meta_analysis/test_analysis_plan_builder_v1.py`
- `tests/meta_analysis/test_statistical_result_state_gating.py`
- `tests/meta_analysis/test_effect_size_normalization_service.py`
- `tests/meta_analysis/test_pairwise_meta_executor_service.py`
- `tests/meta_analysis/test_result_review_service.py`
- `tests/meta_analysis/test_meta_workspace_ui_navigation.py`
- `tests/ui/test_meta_m13_result_review_ui.py`

Optional documentation for traceability:

- `docs/meta_dev_reports/Meta_M10_statistical_result_state_gating_report_20260513.md`
- `docs/meta_dev_reports/Meta_M11_effect_size_normalization_report_20260513.md`
- `docs/meta_dev_reports/Meta_M12_pairwise_meta_executor_mvp_report_20260513.md`
- `docs/meta_dev_reports/Meta_M13_result_review_report_ready_transition_20260513.md`
- `docs/meta_dev_reports/Meta_integration_backfill_m10_m13_user_path_fix_20260513.md`
- `docs/integration/Integration_i_meta_2_m10_m13_user_flow_validation_20260513.md`
- `docs/integration/Integration_j_meta_m10_m13_user_path_fix_20260513.md`
- this precheck report

## Explicit exclusions

Do not carry over in the next scoped apply:

- whole `dev/meta-analysis`;
- whole `dev/integration`;
- unrelated M4-M9/M14+ Meta runtime changes not needed by M10-M13;
- Bioinformatics, LabTools, UIShell, ReleaseBuild business code;
- real DEG executor, volcano plot, heatmap, enrichment, GSEA, survival, correlation new functions;
- network search/download, AI/model calls, database, batch export, packaging, autosave/history systems;
- any release packaging or desktop app overwrite.

## Validation performed

MainLine baseline:

- `python3 -m app.main --smoke-test`: passed, `git_head=fd0b9a0`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_module_boundary_contract.py -q`: `5 passed`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`: `171 passed`
- `git diff --check`: passed

Meta source branch:

- `git diff --check`: passed
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`: passed, `git_head=5eaf2b1`
- `python3 -m pytest tests/meta_analysis -q`: `529 passed`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`: `155 passed`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_module_boundary_contract.py -q`: `5 passed`
- real user-flow probe: passed through computed, user_reviewed, report_ready, report draft, and failed_validation paths

Integration candidate:

- `python3 -m app.main --smoke-test`: passed, `git_head=ba58540`
- M10-M13 targeted tests: `59 passed`
- real user-flow probe: passed on `metaStatisticsAnalysisPage`
- `git diff --check`: passed

## Required next-stage validation after scoped apply to MainLine

After applying the approved scoped set onto MainLine, run at minimum:

- `git diff --check`
- `python3 -m app.main --smoke-test`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_module_boundary_contract.py -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis/test_statistical_result_state_gating.py tests/meta_analysis/test_effect_size_normalization_service.py tests/meta_analysis/test_pairwise_meta_executor_service.py tests/meta_analysis/test_result_review_service.py tests/meta_analysis/test_analysis_plan_builder_v1.py tests/meta_analysis/test_meta_workspace_ui_navigation.py tests/ui/test_meta_m13_result_review_ui.py -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
- a real offscreen MainWindow user-flow probe that verifies computed -> user_reviewed -> report_ready and failed_validation user feedback on MainLine

## Recommendation

Proceed to a MainLine scoped apply stage for Meta M10-M13 only.

Do not package after this precheck. ReleaseBuild remains out of scope until MainLine scoped apply has been completed and validated in a separate MainLine report.
