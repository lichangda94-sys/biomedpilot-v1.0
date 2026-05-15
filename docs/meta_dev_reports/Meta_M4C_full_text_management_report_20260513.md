# Meta M4C Full-text Management Workspace Report

## Stage name
Meta M4C — Full-text Management Workspace

## Branch
dev/meta-analysis

## HEAD before work
7bb7ceb

## Files changed
- `app/meta_analysis/services/fulltext_management_service.py`
- `app/meta_analysis/workspace.py`
- `app/meta_analysis/models/systematic_review.py`
- `app/meta_analysis/ui_text.py`
- `tests/meta_analysis/test_fulltext_management_service.py`
- `tests/meta_analysis/test_meta_workspace_ui_navigation.py`
- `docs/meta_dev_reports/Meta_M4C_full_text_management_report_20260513.md`

## User-facing behavior
- Added a Chinese-first full-text management workspace inside the existing Meta screening stage.
- The page shows `全文管理`, `全文筛选`, `全文状态`, `上传全文`, `标记无法获取`, `全文确认`, and `下一步：数据提取`.
- Eligible records from title/abstract screening are shown with title, author/year, journal, screening decision, full-text status, safe file availability labels, and full-text exclusion reason labels.
- PDF registration uses the existing project full-text service and displays only safe labels such as `已登记全文文件` plus a sanitized filename. Raw local paths and internal record IDs are not shown in the normal list.
- The main page reports compact full-text counts for needed, uploaded, pending review, confirmed, unavailable, excluded, and ready-for-extraction records.

## Developer-facing behavior
- Introduced structured M4C full-text statuses:
  `not_required`, `full_text_needed`, `full_text_uploaded`, `full_text_pending_review`, `full_text_confirmed`, `full_text_unavailable`, and `full_text_excluded`.
- Kept backward-compatible aliases for earlier full-text management status names used by existing parser and eligibility integration tests.
- Added structured M4C full-text exclusion reason codes and Chinese labels.
- Added validation for full-text statuses, exclusion reasons, transition rules, safe file labels, and summary counts.
- Existing parser behavior remains testing-level and does not create confirmed extraction evidence.
- Developer diagnostics remain collapsed by default.

## Validation commands and exact results
- `git diff --check`
  - Exit code: 0
  - Output: no output
- `python3 -m pytest tests/meta_analysis -q`
  - Exit code: 0
  - Result: `468 passed in 4.47s`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - Exit code: 0
  - Result: `154 passed in 9.99s`
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`
  - Exit code: 0
  - Output:
    - `BioMedPilot / 医研智析`
    - `app_version=0.1.0-internal-beta`
    - `app_channel=Developer Preview / testing`
    - `launch_mode=source`
    - `app_root=/Users/changdali/Developer/biomedpilot v1.0/Meta`
    - `git_head=7bb7ceb`
    - `workspace_entries=2`
    - `bioinformatics_features=5`
    - `meta_analysis_features=7`
    - `pyside6_available=True`

## Limitations
- M4C manages full-text status and user decisions only.
- This stage does not implement formal PDF scientific extraction.
- Parsed PDF text, parser diagnostics, AI hints, or rule hints remain suggestions/testing artifacts only and do not become confirmed evidence automatically.
- User confirmation is required before a record becomes `full_text_confirmed`.
- Statistical analysis and report-ready evidence conclusions remain out of scope.

## Remaining untracked or dirty files
- Expected pre-existing untracked input artifact remains:
  `docs/meta_dev_reports/Meta_handoff_report_20260513.md`
- Before commit, M4C in-scope files are modified or newly added as listed above.

## Commit
- Commit made: yes, after validation, with message `feat(meta): add full-text management workspace`.
- Remote push: no.
