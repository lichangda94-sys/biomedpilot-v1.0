# Meta M14 Runtime Integration Readiness Audit

## Stage

- Stage name: Meta M14 - Runtime Integration Readiness Audit
- Branch: `dev/meta-analysis`
- HEAD before work: `0895d78`
- Date: 2026-05-13
- Scope: audit/report only; no runtime code changes.

## Readiness verdict

M10-M13 are conditionally ready for a scoped Integration / MainLine carry-over if the integration is limited to the Meta Analysis runtime files listed below and preserves the Developer Preview / testing semantics.

This audit does not approve production, clinical, regulatory, submission-ready, or publication-ready status. `report_ready` means only that an M12 computed result has passed the M13 user-review gate and may enter the current draft report workflow with Developer Preview / testing disclaimers.

## Files inspected

- `CODEX.md`
- `README.md`
- `docs/meta_dev_reports/Meta_M10_statistical_result_state_gating_report_20260513.md`
- `docs/meta_dev_reports/Meta_M11_effect_size_normalization_report_20260513.md`
- `docs/meta_dev_reports/Meta_M12_pairwise_meta_executor_mvp_report_20260513.md`
- `docs/meta_dev_reports/Meta_M13_result_review_report_ready_transition_20260513.md`
- `docs/meta_dev_reports/Meta_handoff_report_20260513.md`
- `app/meta_analysis/models/statistical_result_state.py`
- `app/meta_analysis/models/analysis_result.py`
- `app/meta_analysis/models/effect_size_normalization.py`
- `app/meta_analysis/models/pairwise_meta_executor.py`
- `app/meta_analysis/models/result_review.py`
- `app/meta_analysis/services/analysis_run_service.py`
- `app/meta_analysis/services/effect_size_normalization_service.py`
- `app/meta_analysis/services/pairwise_meta_executor_service.py`
- `app/meta_analysis/services/result_review_service.py`
- `app/meta_analysis/services/formal_report_service.py`
- `app/meta_analysis/pages/analysis_page.py`
- `tests/meta_analysis/test_statistical_result_state_gating.py`
- `tests/meta_analysis/test_effect_size_normalization_service.py`
- `tests/meta_analysis/test_pairwise_meta_executor_service.py`
- `tests/meta_analysis/test_result_review_service.py`
- `tests/ui/test_meta_m13_result_review_ui.py`

## Audit findings

### 1. Meta UI analysis page

The active Meta analysis page can carry the M10-M13 runtime surface:

- M11 summary: `效应量标准化预检查`
- M12 summary: `统计执行状态`
- M13 review panel: `统计结果审核`
- M13 actions: acknowledge warnings, accept for draft report, mark needs revision, reject for report, and request report-ready status.

The UI path is still Developer Preview / testing. The main panel uses Chinese user-facing labels and does not intentionally display raw JSON, manifest paths, local paths, or internal object IDs. Current test coverage includes offscreen instantiation and M13 Chinese label checks.

### 2. M12/M13 testing semantics

M12 computed results remain Developer Preview / testing:

- M12 can produce `computed` only after validation gates pass.
- M12 does not automatically produce `user_reviewed` or `report_ready`.
- M12 result objects retain `developer_preview_testing=True` and avoid medical/final-conclusion claims.

M13 adds review semantics without changing statistical formulas:

- Default computed results are `not_reviewed`.
- Results can enter review, be accepted for draft reporting, be marked as needs revision, or be rejected.
- `report_ready` requires explicit report-ready request, accepted review metadata, warning acknowledgement where required, no unresolved validation errors, no unresolved critical warnings, and the M10 gate.

### 3. `report_ready` interpretation

`report_ready` is safe for current draft-report workflow only. It is not a production or publication claim.

The report builder states that report-ready statistical results remain Developer Preview / testing and do not represent production, clinical, regulatory, submission, or formal publication conclusions. This wording should be preserved verbatim or equivalently during scoped integration.

### 4. Old analysis path isolation

The old `AnalysisRunService` / `AnalysisResult` path remains isolated from formal result semantics:

- `AnalysisResult` defaults to `result_state=testing_level`.
- `AnalysisRunService` saves legacy analysis output with testing-level metadata and `blocks_formal_report_claim=True`.
- Tests assert old-path output is not formal, is not report-ready, and blocks formal report claims.

This path should not be removed during integration, but Integration / MainLine must not treat it as a formal statistical executor.

### 5. Report generation safety

The formal report service distinguishes statistical states:

- `not_run`: states no formal statistical analysis has run.
- `configured_not_run`: states a plan is configured but executor has not run.
- `testing_level`: states Developer Preview / testing output cannot be a formal conclusion.
- `failed_validation`: reports validation failure summary only.
- `computed`: states results are computed but not user-reviewed.
- `user_reviewed`: states results were reviewed but are not report-ready.
- `report_ready`: allows draft-workflow statistical section with Developer Preview / testing disclaimer.

Existing tests assert report output does not leak raw pairwise result refs, temporary paths, or raw JSON markers.

### 6. MainLine scoped integration file set

Carry over M10-M13 together. Do not cherry-pick M12 or M13 without M10/M11.

Required runtime files:

- `app/meta_analysis/models/analysis_result.py`
- `app/meta_analysis/models/statistical_result_state.py`
- `app/meta_analysis/models/effect_size_normalization.py`
- `app/meta_analysis/models/pairwise_meta_executor.py`
- `app/meta_analysis/models/result_review.py`
- `app/meta_analysis/services/advanced_analysis_service.py`
- `app/meta_analysis/services/analysis_run_service.py`
- `app/meta_analysis/services/analysis_setup_service.py`
- `app/meta_analysis/services/figure_result_service.py`
- `app/meta_analysis/services/meta_statistics_engine_service.py`
- `app/meta_analysis/services/effect_size_normalization_service.py`
- `app/meta_analysis/services/pairwise_meta_executor_service.py`
- `app/meta_analysis/services/result_review_service.py`
- `app/meta_analysis/services/formal_report_service.py`
- `app/meta_analysis/pages/analysis_page.py`

Required tests:

- `tests/meta_analysis/test_statistical_result_state_gating.py`
- `tests/meta_analysis/test_effect_size_normalization_service.py`
- `tests/meta_analysis/test_pairwise_meta_executor_service.py`
- `tests/meta_analysis/test_result_review_service.py`
- `tests/ui/test_meta_m13_result_review_ui.py`

Recommended documentation carry-over:

- `docs/meta_dev_reports/Meta_M10_statistical_result_state_gating_report_20260513.md`
- `docs/meta_dev_reports/Meta_M11_effect_size_normalization_report_20260513.md`
- `docs/meta_dev_reports/Meta_M12_pairwise_meta_executor_mvp_report_20260513.md`
- `docs/meta_dev_reports/Meta_M13_result_review_report_ready_transition_20260513.md`
- `docs/meta_dev_reports/Meta_M14_runtime_integration_readiness_audit_20260513.md`

Do not carry `app/meta_analysis/legacy/**` as runtime proof. It remains historical and isolated.

### 7. Cross-module contamination risk

Observed M10-M13 changes are contained to:

- `app/meta_analysis/**`
- `tests/meta_analysis/**`
- `tests/ui/test_meta_m13_result_review_ui.py`
- `docs/meta_dev_reports/**`

No Bioinformatics, LabTools, UIShell, ReleaseBuild, MainLine, Integration, or ProjectControl file changes are required for the M10-M13 runtime semantics themselves. Cross-module contamination risk is low if scoped integration preserves the file boundary above and does not infer active behavior from `app/meta_analysis/legacy/**`.

## Integration requirements

- Preserve Developer Preview / testing labels in UI and reports.
- Preserve M10 result-state gates before enabling M12/M13.
- Preserve M11 normalization as pre-executor input validation, not a statistical result.
- Preserve M12 fixed-effect inverse-variance MVP scope only.
- Preserve M13 review and report-ready transitions.
- Run the full Meta and UI validation suite after scoped integration.
- Do not package or promote to production in this audit stage.

## Known limitations

- M12 supports only a narrow fixed-effect inverse-variance pairwise executor MVP.
- No random-effects executor is approved by this audit.
- No network meta-analysis, diagnostic meta-analysis, subgroup automation, sensitivity automation, publication-bias automation, forest plot, or funnel plot is approved by this audit.
- `report_ready` is workflow readiness for the current draft report, not formal publication readiness.
- MainLine / Integration must rerun validation after applying the scoped file set.

## Validation

- `git diff --check`
  - Result: passed with no output before and after adding this report.
- `python3 -m pytest tests/meta_analysis -q`
  - Result: `527 passed in 5.99s`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - Result: `155 passed in 10.77s`
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`
  - Result:

```text
BioMedPilot / 医研智析
app_version=0.1.0-internal-beta
app_channel=Developer Preview / testing
launch_mode=source
app_root=/Users/changdali/Developer/biomedpilot v1.0/Meta
git_head=0895d78
workspace_entries=2
bioinformatics_features=5
meta_analysis_features=7
pyside6_available=True
```

## Remaining dirty or untracked files

At report creation time:

- `docs/meta_dev_reports/Meta_M14_runtime_integration_readiness_audit_20260513.md` - new in-scope M14 report.
- `docs/meta_dev_reports/Meta_handoff_report_20260513.md` - pre-existing untracked input artifact, intentionally preserved.

## Commit status

Commit is expected after final `git diff --check` passes. Final commit hash is recorded in the assistant handoff because the report cannot self-reference the commit hash before the commit exists.
