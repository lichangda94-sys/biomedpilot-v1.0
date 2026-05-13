# Meta M6 Quality Assessment Workspace Report

## Stage name
Meta M6 — Quality Assessment Workspace

## Branch
dev/meta-analysis

## HEAD before work
e098cdd

## Prerequisite check
- M5 structured extraction table commit present: `e098cdd feat(meta): add structured extraction table`
- Confirmed extraction records are supported through M5 `evidence_state=confirmed` / `completed_by_user` extraction rows.
- If a project has no confirmed extraction records yet, the quality workspace shows a safe empty state and does not require JSON editing.

## Files changed
- `app/meta_analysis/services/quality_service.py`
- `app/meta_analysis/pages/quality_page.py`
- `app/meta_analysis/quality/tool_registry.py`
- `app/meta_analysis/workspace.py`
- `tests/meta_analysis/test_stage_s_extraction_quality_hardening.py`
- `tests/meta_analysis/test_meta_workspace_ui_navigation.py`
- `docs/meta_dev_reports/Meta_M6_quality_assessment_report_20260513.md`

## User-facing behavior
- Added a Chinese-first quality assessment workspace inside the existing extraction/quality stage.
- The workspace shows `质量评价`, `偏倚风险`, `评价工具`, `评价维度`, `用户选择`, `评价理由`, `总体判断`, `已确认`, and `下一步：分析计划`.
- NOS is the priority editable workflow, with structured domains:
  `selection`, `comparability`, and `outcome_or_exposure`.
- NOS ratings use safe testing labels:
  `低风险/较好`, `不明确`, `高风险/较差`, and `未评价`.
- Main UI avoids raw JSON, internal IDs, manifest paths, and local paths.

## Developer-facing behavior
- Extended the active `QualityAssessmentService` rather than creating a parallel storage layer.
- Preserved existing ROB2, ROBINS-I, QUADAS-2, JBI, AHRQ, Cochrane RoB, and GRADE placeholder registry entries.
- Added M6 governance states:
  `draft`, `suggested`, `user_accepted`, `user_edited`, `confirmed`, and `rejected`.
- Suggestions remain suggestions and are not counted as confirmed quality assessments.
- Added M6 summary counts:
  `studies_pending_quality`, `studies_with_draft_quality`, `studies_with_confirmed_quality`, `low_risk_or_good`, `unclear`, and `high_risk_or_poor`.
- Quality assessments remain testing-level reviewer-entered records; no official NOS scoring or formal GRADE conclusion is claimed.

## Validation commands and exact results
- `git diff --check`
  - Exit code: 0
  - Output: no output
- `python3 -m pytest tests/meta_analysis -q`
  - Exit code: 0
  - Result: `478 passed in 4.23s`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - Exit code: 0
  - Result: `154 passed in 9.77s`
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`
  - Exit code: 0
  - Output:
    - `BioMedPilot / 医研智析`
    - `app_version=0.1.0-internal-beta`
    - `app_channel=Developer Preview / testing`
    - `launch_mode=source`
    - `app_root=/Users/changdali/Developer/biomedpilot v1.0/Meta`
    - `git_head=e098cdd`
    - `workspace_entries=2`
    - `bioinformatics_features=5`
    - `meta_analysis_features=7`
    - `pyside6_available=True`

## Limitations
- M6 does not implement validated official NOS scoring.
- ROB2, ROBINS-I, QUADAS-2, JBI, AHRQ, Cochrane RoB, and GRADE remain staged/testing form or placeholder surfaces unless separately validated later.
- AI/rule quality recommendations remain suggestions and require user action before they become accepted or confirmed.
- Quality confirmation does not create analysis-ready datasets, run statistics, or produce publication-ready conclusions.

## Remaining untracked or dirty files
- Expected pre-existing untracked input artifact remains:
  `docs/meta_dev_reports/Meta_handoff_report_20260513.md`
- Before commit, M6 in-scope files are modified or newly added as listed above.

## Commit
- Commit made: yes, after validation, with message `feat(meta): add quality assessment workspace`.
- Remote push: no.
