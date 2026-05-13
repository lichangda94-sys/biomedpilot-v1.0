# Integration I-Meta-2 M10-M13 Carry-over User Flow Validation - 2026-05-13

## Decision

`I_META_2_USER_FLOW_VALIDATION_NOT_PASSED`

Current `dev/integration` HEAD `e86de13` contains the Meta M10-M13 carry-over code and component-level tests pass, but the real desktop user path is not ready for MainLine scoped carry-over precheck.

Do not start route A (`Integration -> MainLine scoped carry-over precheck`) from `e86de13` yet.

This validation did not add features, did not package, did not overwrite `/Users/changdali/Desktop/BioMedPilot Dev.app`, did not overwrite any existing `BioMedPilot.app`, and did not push remote.

## Current source state

| Item | Observed state |
| --- | --- |
| Worktree | `/Users/changdali/Developer/biomedpilot v1.0/Integration` |
| Branch | `dev/integration` |
| HEAD | `e86de13` |
| HEAD subject | `feat(integration): carry meta m10-m13 runtime` |
| Dirty status before report | clean |
| Packaging | not run |
| Scope | validation/report only |

## User flow under validation

Expected path:

`Meta 入口 -> 分析计划 -> 标准化效应量输入 -> pairwise fixed-effect executor -> computed 状态 -> 用户审核 -> report_ready -> 报告草稿摘要`

## Findings

### 1. Active desktop UI does not expose the full M10-M13 path

Status: `BLOCKED`

The active Meta workspace can be opened from the shell and the 8-step route is present, but the current user-facing `statistics_analysis` step does not expose:

- `效应量标准化预检查`
- `统计执行状态`
- `统计结果审核`
- `接受进入报告草稿`
- `申请报告就绪`
- `报告就绪`
- readable `failed_validation` / `输入校验失败` feedback

Evidence from offscreen MainWindow walk:

```text
current_workspace= meta_analysis
page_keys= ('workflow_home', 'pico_workspace', 'search_strategy', 'literature_import', 'screening_review', 'manual_extraction', 'statistics_analysis', 'report_export')
statistics_page_object= metaStatisticsAnalysisPage
contains[分析计划]= True
contains[效应量标准化预检查]= False
contains[统计执行状态]= False
contains[统计结果审核]= False
contains[接受进入报告草稿]= False
contains[申请报告就绪]= False
contains[报告就绪]= False
contains[failed_validation]= False
contains[输入校验失败]= False
```

Implementation evidence:

- `app/meta_analysis/workspace.py` routes the active 8-step user flow through `statistics_analysis`.
- `_statistics_analysis_page()` uses `MetaStatisticsEngineService`, shows `统计分析`, and provides `运行统计分析`.
- M11-M13 controls exist in `app/meta_analysis/pages/analysis_page.py`, but that widget is not the mounted page in the active 8-step Meta workspace path.

This means the path is currently validated only at component/service level, not as a real user journey.

### 2. Real confirmed analysis plan is not accepted by M12 executor gate

Status: `BLOCKED`

The service-chain probe created a real confirmed protocol, two confirmed structured extraction rows, a generated analysis plan draft, and a confirmed analysis plan. The confirmed plan payload did not contain `plan_state: confirmed`.

`PairwiseMetaExecutorService.execute_from_inputs()` currently requires:

```text
confirmed_plan.get("plan_state") == "confirmed"
```

Observed real service-chain result:

```text
confirmed_plan_state= None
normalized_statuses= [('Alpha 2026', 'MD', 'ready', True, True), ('Beta 2026', 'MD', 'ready', True, True)]
direct_result_state= failed_validation
direct_validation_errors= ['confirmed_analysis_plan_required', 'confirmed_analysis_plan_required_for_computed_state']
patched_result_state= computed
patched_validation_errors= []
```

The patched probe proves the executor can compute with the same normalized rows when `plan_state` is manually supplied, so the blocker is a schema/gate mismatch between `AnalysisPlanService.confirm_plan()` and `PairwiseMetaExecutorService`.

### 3. `failed_validation` can crash before reaching user-readable feedback

Status: `BLOCKED`

Calling `PairwiseMetaExecutorService.execute(project)` on the real project failed with:

```text
execute_exception= ValueError unsupported_audit_event_type:analysis_run_failed_validation
```

`PairwiseMetaExecutorService` records `analysis_run_failed_validation`, but `MetaAuditLogService.AUDIT_EVENT_TYPES` does not include that event type.

This prevents a normal failed-validation state from becoming understandable UI feedback in the real path.

### 4. `computed` before user review is blocked from formal reporting

Status: `PASS_AT_SERVICE_AND_REPORT_LAYER`

M10/M13 service and report tests verify that:

- computed results require user review before `report_ready`;
- computed-but-unreviewed results are described as not formal report conclusions;
- reviewed-but-not-ready results remain outside report-ready state;
- `report_ready` report wording remains Developer Preview / testing and does not claim publication-grade output.

Relevant report wording in the builder includes:

- `统计结果已计算但尚未完成用户审核，不能作为正式报告结论。`
- `统计结果已完成用户审核，但尚未标记为报告就绪。`
- `报告就绪统计结果（Developer Preview / testing）：可进入当前草稿报告工作流，但不代表生产、临床、监管、投稿或正式发表结论。`

This passes the semantic boundary requirement, but it is not enough to pass the user-flow validation because the active workspace does not expose the full flow.

### 5. Old `AnalysisRunService` does not bypass M10 gate

Status: `PASS`

The old `AnalysisRunService` writes testing-level result metadata:

- `result_state = testing_level`
- `testing_level = True`
- `blocks_formal_report_claim = True`

Targeted tests covering statistical result state gating passed. No evidence was found that the old service can move a result into `report_ready` or bypass the M10 gate.

### 6. Integration shell did not show a smoke/UI regression

Status: `PASS_FOR_CURRENT_INTEGRATION`, `NOT_A_MAINLINE_CARRY_OVER_APPROVAL`

The current Integration shell can launch, enter Meta, and pass current UI tests. However, `stable/mainline...HEAD` contains broad Meta workspace and shell/UI diffs, so this validation does not approve MainLine carry-over. A scoped carry-over precheck must wait until the I-Meta-2 blockers are fixed.

## Verification performed

| Check | Result |
| --- | --- |
| `python3 -m app.main --smoke-test` | passed, reported `git_head=e86de13` |
| M10-M13 targeted tests: `tests/meta_analysis/test_statistical_result_state_gating.py`, `test_effect_size_normalization_service.py`, `test_pairwise_meta_executor_service.py`, `test_result_review_service.py`, `tests/ui/test_meta_m13_result_review_ui.py` | `43 passed` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_module_boundary_contract.py -q` | `5 passed` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | `178 passed` |
| Meta workspace/MainLine contract targeted tests: `test_analysis_plan_builder_v1.py`, `test_meta_workspace_ui_navigation.py`, `test_mainline_meta_contract.py` | `16 passed` |
| Actual MainWindow user-flow probe | failed to find the required M11-M13 UI path in active workspace |
| Real service-chain probe | failed due confirmed-plan gate mismatch and unsupported failed-validation audit event |

## Required scoped fixes before re-validation

1. Wire the active 8-step Meta workspace `statistics_analysis` path to the M11-M13 user flow, or mount the M11-M13 `AnalysisPage` capabilities into the active workspace without opening unrelated legacy/runtime surfaces.
2. Align `AnalysisPlanService.confirm_plan()` and `PairwiseMetaExecutorService` on the confirmed plan contract. Either the confirmed plan must carry an explicit confirmed state accepted by M12, or M12 must recognize the current confirmed analysis plan schema safely.
3. Add a supported audit event or safe mapping for M12 failed validation so `failed_validation` does not raise before user feedback.
4. Add a user-flow UI test that walks the active workspace path from Meta entry through computed, review, report_ready request/grant, and report draft summary.
5. Ensure failed-validation blockers are shown in user-readable Chinese in the active workspace, not only in report-builder/component tests.

## Recommendation

Do not proceed to `Integration -> MainLine scoped carry-over precheck` from `e86de13`.

Do not package or promote the current Meta M10-M13 carry-over as a validated user-facing flow.

Recommended next step: perform a scoped I-Meta-2 fix pass limited to active workspace wiring, confirmed-plan gate alignment, failed-validation audit handling, and an active user-flow UI test. After that, rerun this validation before considering route A.
