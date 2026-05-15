# Meta M13 Result Review and Report-Ready Transition Report

## Stage

Meta M13 — Result Review and Report-Ready Transition

## Branch

`dev/meta-analysis`

## HEAD Before Work

`ea7d203`

## Files Changed

- `app/meta_analysis/models/result_review.py`
- `app/meta_analysis/models/pairwise_meta_executor.py`
- `app/meta_analysis/services/result_review_service.py`
- `app/meta_analysis/services/pairwise_meta_executor_service.py`
- `app/meta_analysis/pages/analysis_page.py`
- `app/meta_analysis/services/formal_report_service.py`
- `tests/meta_analysis/test_result_review_service.py`
- `tests/meta_analysis/test_pairwise_meta_executor_service.py`
- `tests/ui/test_meta_m13_result_review_ui.py`
- `docs/meta_dev_reports/Meta_M13_result_review_report_ready_transition_20260513.md`

## M13 Behavior Added

- Added a statistical result review model with safe result references, review state, reviewer role, reviewed timestamp, decision, notes, warning acknowledgement, report-ready request/grant flags, blockers, and audit summary.
- Added `StatisticalResultReviewService` for:
  - starting review
  - accepting a computed result for draft report use
  - marking a result as needing revision
  - rejecting a result for report use
  - requesting report-ready status
  - granting report-ready status only after M10-compatible gates pass
- Tightened direct M12 transition helpers so they require accepted review metadata, warning acknowledgement, and a report-ready request before `report_ready`.
- Persisted review state beside M12 pairwise executor results under the existing project analysis/pairwise executor area.
- Recorded review actions through the Meta audit log using `record_saved` events and safe user-facing summaries.

## Review-State Semantics

- `not_reviewed`: computed result exists but no review has been started or completed.
- `in_review`: a reviewer has started review or a requested transition was blocked.
- `accepted_for_report`: reviewer accepted the result for the current draft report workflow.
- `needs_revision`: reviewer found issues or missing inputs and the result must not enter report-ready state.
- `rejected_for_report`: reviewer decided the result should not be used in the report.

Warning acknowledgement means warnings were seen by the reviewer. It does not remove warnings and does not resolve critical warnings.

## Report-Ready Transition Rules

- `computed -> user_reviewed` requires:
  - result state is `computed`
  - review decision is `accepted_for_report`
  - warnings are acknowledged when warnings exist
  - no unresolved validation errors
  - no unresolved critical warnings
  - review metadata is persisted
- `user_reviewed -> report_ready` requires:
  - review state and decision are `accepted_for_report`
  - `report_ready_requested=true`
  - no validation errors
  - no unresolved critical warnings
  - M10 `can_enter_report_ready_state` allows the transition
- Blocked states include:
  - `testing_level`
  - `failed_validation`
  - `configured_not_run`
  - `not_run`
  - `computed` without review
  - `computed` with unresolved critical warnings
  - `needs_revision`
  - `rejected_for_report`

Even `report_ready` remains Developer Preview / testing in this worktree. It means safe for the current draft report workflow only; it is not production, clinical, regulatory, submission-ready, or publication-ready status.

## UI and Report Behavior

- Added a minimal Chinese-first review panel to the existing Analysis page:
  - 统计结果审核
  - 尚未审核
  - 审核中
  - 接受进入报告草稿
  - 需要修订
  - 不纳入报告
  - 已确认查看警告
  - 申请报告就绪
  - 报告就绪
  - 阻止进入报告的原因
- The panel displays safe review status and blockers; it does not expose raw JSON, manifest paths, local paths, or internal result IDs in the main UI.
- Report generation now distinguishes:
  - not run
  - configured but not run
  - testing-level
  - failed validation
  - computed but not reviewed
  - user-reviewed but not report-ready
  - report-ready for the current draft workflow
- Report-ready statistical content still carries Developer Preview / testing disclaimers and does not claim formal conclusions.

## Validation Commands and Exact Results

`git diff --check`

Result: passed with no output.

`python3 -m pytest tests/meta_analysis -q`

Result:

```text
527 passed in 4.97s
```

`QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`

Result:

```text
155 passed in 10.31s
```

`QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`

Result:

```text
BioMedPilot / 医研智析
app_version=0.1.0-internal-beta
app_channel=Developer Preview / testing
launch_mode=source
app_root=/Users/changdali/Developer/biomedpilot v1.0/Meta
git_head=ea7d203
workspace_entries=2
bioinformatics_features=5
meta_analysis_features=7
pyside6_available=True
```

Additional local compile check:

```text
python3 -m compileall -q app/meta_analysis/models/result_review.py app/meta_analysis/models/pairwise_meta_executor.py app/meta_analysis/services/result_review_service.py app/meta_analysis/services/pairwise_meta_executor_service.py app/meta_analysis/pages/analysis_page.py app/meta_analysis/services/formal_report_service.py
```

Result: passed with no output.

## Limitations

- M13 does not add or change statistical formulas.
- M13 does not add random-effects, network meta-analysis, diagnostic meta-analysis, plots, subgroup analysis, sensitivity analysis, publication-bias automation, or formal conclusions.
- Review identity is limited to reviewer role text; no authentication or real user identity binding was added.
- Report-ready remains a Developer Preview / testing workflow state and does not make outputs publishable or production-grade.

## Remaining Dirty or Untracked Files at Report Creation

- Expected untracked input artifact remains: `docs/meta_dev_reports/Meta_handoff_report_20260513.md`
- M13 files were dirty before commit.

## Commit

Commit is expected after final validation. The final commit hash is reported in the assistant handoff because embedding a commit's own hash inside this committed report would change that hash.
