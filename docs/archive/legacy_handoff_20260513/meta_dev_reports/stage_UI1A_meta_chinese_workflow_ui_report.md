# Stage UI1A Meta Chinese Workflow UI Report

Status: Developer Preview / testing.

## Goal

UI Phase 1A adds a Chinese-friendly Meta Analysis workflow entry and workflow dashboard foundation without adding new analysis, import, extraction, report, OCR, PDF download, AI automation, Network Meta, HSROC, or meta-regression functionality.

## test_inputs/ Housekeeping

`test_inputs/` was audited in AB14.1 and is intentionally local-only.

- Contents: Bioinformatics demo expression matrix, sample annotation, and GMT gene set files.
- Decision: ignore with `.gitignore`.
- UI1A did not migrate, delete, or commit those files.

## Implementation

Added centralized Meta UI copy in `app/meta_analysis/ui_text.py`:

- 15 workflow step Chinese names and English subtitles.
- Chinese status mapping:
  - `Not started` -> `未开始`
  - `In progress` -> `进行中`
  - `Needs review` -> `需要复核`
  - `Ready` -> `已就绪`
  - `Completed` -> `已完成`
  - `Developer Preview` -> `内部测试`
- Shared user-facing copy for internal beta status, missing output warnings, and developer information labels.

Enhanced workflow dashboard page state:

- Preserves existing English fields and status constants for compatibility.
- Adds Chinese display fields for title, status, input summary, output summary, next step, entry label, and warning summary.
- Empty or missing-artifact projects remain warning-based and do not crash.

Enhanced Meta workspace entry:

- Main title: `Meta 分析模块`.
- Status label: `0.1.0-internal-beta · 内部测试版 / Developer Preview / testing`.
- Left navigation uses Chinese-first labels with English subtitles, such as `文献导入 Literature Import`.
- Testing notice is Chinese and states results cannot be used as formal clinical, submission, or production conclusions.

Updated app Dashboard subtitle:

- The top-level Dashboard now includes `0.1.0-internal-beta · 内部测试版 / Developer Preview / testing`.
- This is a small shell text change required by UI1A acceptance.

## Modified Files

- `app/meta_analysis/ui_text.py`
- `app/meta_analysis/pages/workflow_dashboard_page.py`
- `app/meta_analysis/workspace.py`
- `app/shell/dashboard.py`
- `tests/meta_analysis/test_stage_ui1a_meta_chinese_workflow_ui.py`
- `tests/meta_analysis/test_meta_workspace_ui_navigation.py`
- `docs/meta_dev_reports/stage_UI1A_meta_chinese_workflow_ui_report.md`
- `docs/meta_internal_beta_gap_list.md`
- `docs/tester_guide.md`

## Tests

Focused tests added or updated:

- `test_inputs/` is ignored.
- Chinese status mapping is complete.
- All 15 workflow steps have Chinese names and English subtitles.
- Empty project dashboard returns Chinese warning copy and does not crash.
- Meta workspace entry title/status/navigation is Chinese friendly.
- Source smoke output still includes app version, git head, and app root.

Validation results before commit:

| Command | Result |
| --- | --- |
| `python3 -m compileall -q .` | Failed on unrelated hidden worktree virtualenv template: `.worktrees/bioinformatics-safe-stage2/.venv/.../PySide6/__init__.tmpl.py` contains Jinja syntax and is not valid Python source. The file was not modified. |
| `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .` | Same unrelated hidden worktree virtualenv template failure. |
| `python3 -m compileall -q -x '(^|/)\\.worktrees/' .` | Passed. |
| `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q -x '(^|/)\\.worktrees/' .` | Passed. |
| `python3 -m pytest -q` | `422 passed` |
| `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q` | `422 passed` |
| `python3 scripts/run_tests.py` | `422 passed` |
| `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py` | `422 passed` |
| `python3 -m app.main --smoke-test` | Passed; version `0.1.0-internal-beta`, source launch mode, git head before commit `63aa55c`. |
| `python3 scripts/package_app.py --no-clean --smoke-test` | Passed; packaged local Python launcher, git head before commit `63aa55c`. |
| `/Users/changdali/Desktop/BioMedPilot.app/Contents/MacOS/BioMedPilot --smoke-test` | Passed; desktop packaged local Python launcher, git head before commit `63aa55c`. |

After commit, refresh the desktop app so packaged metadata points to the UI1A commit.

## Known UI Gaps

- No full literature import wizard yet.
- No Zotero-style editable literature table yet.
- No full duplicate review interaction UI yet.
- No complete extraction table editor yet.
- No complete quality assessment table UI yet.
- No report designer or production PDF flow.
- Developer details are still partly present in service/page-state fields for testing and auditability.

## Next Step

UI Phase 1B: Literature Import Wizard + Zotero-style Literature Table Chinese UI.
