# Stage UI1C Duplicate Review, Criteria, And Screening Chinese UI Report

Status: Developer Preview / testing.

## Goal

UI Phase 1C makes the existing Duplicate Review, Criteria Builder, and Title / Abstract Screening page states easier for Chinese-speaking testers to understand.

This stage does not rewrite deduplication, criteria, or screening services. It does not add automatic merge, automatic exclusion, full-text automation, OCR, AI extraction, or new statistical behavior.

## Continuity Audit

Current baseline:

- Branch: `codex/biomedpilot-root`
- Baseline HEAD: `c203676 feat(meta-ui): add chinese literature import library UI`
- Working tree was clean before implementation.

Existing BioMedPilot capabilities audited:

- `app/meta_analysis/pages/duplicate_review_page.py`
- `app/meta_analysis/pages/criteria_page.py`
- `app/meta_analysis/pages/screening_page.py`
- `app/meta_analysis/services/dedup_decision_service.py`
- `app/meta_analysis/services/criteria_service.py`
- `app/meta_analysis/services/screening_service.py`
- AB5 / AB6 / Stage 7 tests and reports.

Existing capabilities reused:

- Duplicate candidate group loading, merge preview, field conflict summary, and interactive decisions.
- Criteria Builder artifacts and hints.
- Screening queue loading, source links, progress summary, export artifacts, and old decision format compatibility.
- Existing audit, manifest, Data Center, and Task Center behavior.

Legacy capability audit:

- Legacy screening UI files exist under `/Users/changdali/Documents/model9` and `/Users/changdali/Documents/New project 2`.
- They are demo-oriented and do not use the current BioMedPilot manifest/audit/page-state architecture.
- No legacy code was migrated. This stage extends current BioMedPilot page-state objects instead.

## Implementation

Extended centralized Chinese UI copy in `app/meta_analysis/ui_text.py`:

- Duplicate Review title, description, decision labels, group type labels, and conflict field labels.
- Criteria Builder title, description, section labels, and readiness status labels.
- Title / Abstract Screening title, description, decision labels, filter labels, and progress labels.

Enhanced Duplicate Review page state:

- Adds Chinese fields for page title, status, description, input/output summary, next step, empty state, warning summary, and developer information title.
- Adds Chinese decision option labels for `keep_both`, `mark_not_duplicate`, `exclude_duplicate`, and `merge`.
- Adds Chinese group type labels and field conflict labels while preserving old field names and decisions.

Enhanced Criteria Builder page state:

- Adds Chinese title, status, description, input/output summary, next step, empty state, section labels, and readiness status.
- Keeps existing criteria JSON artifacts, hints, readiness status, and warnings unchanged.

Enhanced Title / Abstract Screening page state:

- Adds Chinese title, status, description, input/output summary, next step, empty state, warning summary, and developer information title.
- Adds Chinese decision labels, filter labels, progress labels, source link labels, and per-record decision label.
- Keeps old `pending/included/excluded/maybe` save compatibility; `needs_review` remains a UI view label.

## Modified Files

- `app/meta_analysis/ui_text.py`
- `app/meta_analysis/pages/duplicate_review_page.py`
- `app/meta_analysis/pages/criteria_page.py`
- `app/meta_analysis/pages/screening_page.py`
- `tests/meta_analysis/test_stage_ui1c_duplicate_criteria_screening_chinese_ui.py`
- `docs/meta_dev_reports/stage_UI1C_duplicate_criteria_screening_chinese_ui_report.md`
- `docs/meta_internal_beta_gap_list.md`
- `docs/tester_guide.md`

## Tests

Focused tests added:

- Duplicate Review has Chinese copy and keeps English decision compatibility.
- Duplicate Review conflict summary has Chinese field names.
- Criteria Builder has Chinese section labels and readiness status.
- Screening has Chinese decisions, filters, progress labels, source link labels, and missing queue empty state.

Focused validation:

- `python3 -m pytest -q tests/meta_analysis/test_stage_ui1c_duplicate_criteria_screening_chinese_ui.py tests/meta_analysis/test_stage_7_duplicate_review_light_interaction.py tests/meta_analysis/test_stage_ab5_criteria_builder.py tests/meta_analysis/test_stage_ab6_title_abstract_screening_ux.py tests/meta_analysis/test_meta_workspace_ui_navigation.py`
- Result: `21 passed`

Full validation:

- `python3 -m compileall -q .`: failed only because `.worktrees/bioinformatics-safe-stage2/.venv/.../PySide6/__init__.tmpl.py` is a Jinja template that is not valid Python source.
- `python3 -m compileall -q -x '(^|/)\\.worktrees/' .`: passed.
- `python3 -m pytest -q`: `432 passed`.
- `python3 scripts/run_tests.py`: `432 passed`.
- `python3 -m app.main --smoke-test`: passed, `app_version=0.1.0-internal-beta`, `git_head=c203676`.
- `python3 scripts/package_app.py --no-clean --smoke-test`: passed, packaged smoke `git_head=c203676`.
- `/Users/changdali/Desktop/BioMedPilot.app/Contents/MacOS/BioMedPilot --smoke-test`: passed, packaged desktop entry `git_head=c203676`.
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`: same `.worktrees` PySide6 template failure.
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q -x '(^|/)\\.worktrees/' .`: passed.
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`: `432 passed`.
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`: `432 passed`.

## Remaining UI Gaps

- Duplicate Review still needs a denser record comparison table for high-volume projects.
- Criteria Builder does not yet provide a full desktop form editor for custom criteria.
- Title / Abstract Screening still needs a richer card/table UI for real reviewer speed.
- Full-text, extraction, quality, analysis, PRISMA, and reporting Chinese workflow pages still need UI Phase 1D-1E.

## Next Step

UI Phase 1D: Full-text status + Data Extraction + Quality Assessment Chinese UI.
