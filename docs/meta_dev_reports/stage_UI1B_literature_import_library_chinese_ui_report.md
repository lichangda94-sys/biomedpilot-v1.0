# Stage UI1B Literature Import And Library Chinese UI Report

Status: Developer Preview / testing.

## Goal

UI Phase 1B makes the existing Literature Import Wizard and Zotero-style Literature Library page states more usable for Chinese-speaking testers.

This stage does not rewrite parsers, add online retrieval, auto-merge duplicates, auto-delete records, auto-download PDFs, add OCR, or change statistical/reporting behavior.

## Continuity Audit

Current baseline:

- Branch: `codex/biomedpilot-root`
- Baseline HEAD: `0f48fd7 feat(meta-ui): add chinese workflow dashboard`
- `test_inputs/` remains ignored and local-only.

Existing BioMedPilot capabilities reused:

- AB3 `LiteratureBatchImportService` and `LiteratureImportWizardState`.
- Existing RIS / NBIB / CSV preview and import execution.
- Existing import diagnostics summary, warning table, failed record preview, and warnings CSV paths.
- AB4 `LiteratureLibraryState` and duplicate risk table.
- Existing duplicate group, screening, fulltext, and extraction status readers.

Legacy capability audit:

- Legacy UI had demo-oriented import/library panels, but they did not use the current manifest/audit/page-state architecture.
- No legacy code was migrated. UI1B extends current BioMedPilot page-state objects instead.

## Implementation

Extended centralized Chinese UI copy in `app/meta_analysis/ui_text.py`:

- Import wizard title and step labels.
- Import source labels: local export, Zotero, EndNote, PubMed, CSV/TXT.
- Dedup mode labels.
- Diagnostics field labels and warning explanations.
- Literature table column labels.
- Duplicate risk Chinese labels and color labels.

Enhanced Literature Import page state:

- Keeps legacy/English fields such as `title`, `next_step`, `label`, and `message`.
- Adds Chinese fields such as `title_zh`, `status_label_zh`, `description_zh`, `current_step_zh`, `step_labels_zh`, `source_option_labels_zh`, `dedup_mode_labels_zh`, `label_zh`, and `message_zh`.
- Lightweight PySide panel headings now use Chinese-first labels.

Enhanced Literature Library page state:

- Keeps existing duplicate risk keys and English labels for compatibility.
- Adds Chinese table column labels, duplicate risk labels, color labels, Chinese status label, and Chinese next-step copy.
- Keeps the rule that green means only `未发现明显重复风险`; it is not a quality or trust claim.

## Modified Files

- `app/meta_analysis/ui_text.py`
- `app/meta_analysis/pages/literature_import_page.py`
- `app/meta_analysis/pages/literature_library_page.py`
- `tests/meta_analysis/test_stage_ui1b_literature_import_library_ui.py`
- `docs/meta_dev_reports/stage_UI1B_literature_import_library_chinese_ui_report.md`
- `docs/meta_internal_beta_gap_list.md`
- `docs/tester_guide.md`

## Tests

Focused tests added:

- Import wizard has Chinese title, step labels, source labels, dedup labels, and internal beta status.
- File preview updates the Chinese step name.
- Diagnostics rows keep English compatibility while adding Chinese labels and messages.
- Literature library initial state exposes Chinese title, table columns, and next step.
- Duplicate risk rows expose Chinese labels and color names without using `可信`.

Focused validation:

- `python3 -m pytest -q tests/meta_analysis/test_stage_ui1b_literature_import_library_ui.py tests/meta_analysis/test_stage_ab3_literature_import_wizard.py tests/meta_analysis/test_stage_ab4_literature_library_table.py tests/meta_analysis/test_literature_import_ui_construction.py tests/meta_analysis/test_stage_2_import_diagnostics_visual_summary.py tests/meta_analysis/test_stage_6_literature_import_panel.py tests/meta_analysis/test_meta_workspace_ui_navigation.py`
- Result: `31 passed`

Full validation:

- `python3 -m compileall -q .`: failed only because `.worktrees/bioinformatics-safe-stage2/.venv/.../PySide6/__init__.tmpl.py` is a Jinja template that is not valid Python source.
- `python3 -m compileall -q -x '(^|/)\\.worktrees/' .`: passed.
- `python3 -m pytest -q`: `427 passed`.
- `python3 scripts/run_tests.py`: `427 passed`.
- `python3 -m app.main --smoke-test`: passed, `app_version=0.1.0-internal-beta`, `git_head=0f48fd7`.
- `python3 scripts/package_app.py --no-clean --smoke-test`: passed, packaged smoke `git_head=0f48fd7`.
- `/Users/changdali/Desktop/BioMedPilot.app/Contents/MacOS/BioMedPilot --smoke-test`: passed, packaged desktop entry `git_head=0f48fd7`.
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`: same `.worktrees` PySide6 template failure.
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q -x '(^|/)\\.worktrees/' .`: passed.
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`: `427 passed`.
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`: `427 passed`.

## Remaining UI Gaps

- Import wizard is still a lightweight local-file UI; no live PubMed/WOS/CNKI/WanFang import UI.
- Literature Library remains read-only; no batch edit, batch merge, tagging UI, or advanced column filtering.
- Duplicate review interactions remain in the existing Duplicate Review page and are not part of UI1B.
- Full-text, extraction, quality, analysis, PRISMA, and reporting Chinese workflow pages still need UI Phase 1C-1E.

## Next Step

UI Phase 1C: Duplicate Review + Inclusion/Exclusion Criteria + Title/Abstract Screening Chinese UI.
