# Meta M5 Structured Extraction Table Report

## Stage name
Meta M5 — Structured Extraction Table

## Branch
dev/meta-analysis

## HEAD before work
386000d

## Prerequisite check
- M4B screening workspace commit present: `7bb7ceb feat(meta): add screening workspace refinement`
- M4C full-text management workspace commit present: `386000d feat(meta): add full-text management workspace`
- Ready-for-extraction state exists through M4C `full_text_confirmed` / `ready_for_extraction` full-text management status.

## Files changed
- `app/meta_analysis/services/manual_extraction_effect_row_service.py`
- `app/meta_analysis/workspace.py`
- `tests/meta_analysis/test_manual_extraction_effect_row_service.py`
- `tests/meta_analysis/test_meta_workspace_ui_navigation.py`
- `docs/meta_dev_reports/Meta_M5_extraction_table_report_20260513.md`

## User-facing behavior
- Added a Chinese-first structured extraction table workflow inside the existing Meta extraction workspace.
- The page now surfaces `数据提取`, `研究基本信息`, `PICO/PECO`, `效应量数据`, `统计字段`, `提取状态`, `用户确认`, and `下一步：质量评价`.
- Eligible records prefer prior full-text confirmation (`full_text_confirmed`) and clearly label manual fallback sources such as unavailable full text or library fallback.
- Users can save structured extraction drafts and explicitly confirm structured extraction rows.
- Main UI list labels avoid raw JSON, local paths, manifest paths, and internal record/effect row IDs.

## Developer-facing behavior
- Extended the existing `ManualExtractionEffectRowService` instead of introducing a detached extraction storage layer.
- Added M5 structured extraction constants for study fields, PICO/PECO fields, effect/statistical fields, supported effect measure types, field labels, and evidence states.
- Structured rows persist into the existing extraction study unit/effect row artifacts and continue to write extraction manifest, audit, and research governance events.
- Added evidence-state governance for `empty`, `draft`, `suggested`, `user_accepted`, `user_edited`, `confirmed`, and `rejected`.
- Added lightweight validation for numeric fields, non-negative sample sizes/counts, CI lower/upper ordering, known effect measure types, and confirmed-row minimum requirements.
- Confirmed structured extraction rows still do not create analysis-ready datasets, run statistics, or advance PRISMA.

## Validation commands and exact results
- `git diff --check`
  - Exit code: 0
  - Output: no output
- `python3 -m pytest tests/meta_analysis -q`
  - Exit code: 0
  - Result: `474 passed in 4.19s`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - Exit code: 0
  - Result: `154 passed in 10.98s`
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`
  - Exit code: 0
  - Output:
    - `BioMedPilot / 医研智析`
    - `app_version=0.1.0-internal-beta`
    - `app_channel=Developer Preview / testing`
    - `launch_mode=source`
    - `app_root=/Users/changdali/Developer/biomedpilot v1.0/Meta`
    - `git_head=386000d`
    - `workspace_entries=2`
    - `bioinformatics_features=5`
    - `meta_analysis_features=7`
    - `pyside6_available=True`

## Limitations
- M5 is structured manual extraction only.
- This stage does not run formal meta-analysis statistics.
- Suggested parser/AI values remain suggestions and are not confirmed until user action.
- Confirmation marks extraction rows as user-completed but does not create an analysis-ready dataset.
- The extraction UI is still Developer Preview / testing and optimized for safe structured entry rather than production publication workflow.

## Remaining untracked or dirty files
- Expected pre-existing untracked input artifact remains:
  `docs/meta_dev_reports/Meta_handoff_report_20260513.md`
- Before commit, M5 in-scope files are modified or newly added as listed above.

## Commit
- Commit made: yes, after validation, with message `feat(meta): add structured extraction table`.
- Remote push: no.
