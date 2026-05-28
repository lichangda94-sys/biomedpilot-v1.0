# Meta Analysis UI-C2b Project Home + Question/Type Gated Pages

## Scope

This stage implemented the first Meta Analysis gated runtime surfaces inside the existing PySide target IA shell:

- Project Home / 项目首页
- Question & Meta Type / 研究问题与 Meta 类型

The implementation is layout, state, draft, and gate display only. It does not enable search, import, screening, extraction, risk-of-bias, pairwise meta, result review, report generation, or export.

## Runtime Changes

### Project Home

Added `metaProjectHomeRuntimePanel` with:

- Developer Preview / 本地测试版 chip
- English-first processing chip
- AI suggestion only chip
- Report not ready chip
- workflow overview table for the existing target IA
- project summary table:
  - References: `0 imported`
  - Screening: `not started`
  - Extraction: `not started`
  - Risk of bias: `incomplete`
  - Formal pooled result: `none`
  - Report-ready: `blocked`
  - Export: `disabled`

Gate properties remain explicit:

- `runtimeStatus=shell_only`
- `processingMode=english_first`
- `aiBoundary=advisory_only`
- `resultSemanticKey=no_formal_result`
- `reportStatusKey=report.status.draft`
- `exportGate=disabled_empty_result`
- `formalActionEnabled=false`

### Question & Meta Type

Extended the existing `question_meta_type` target IA page with `metaQuestionTypeDraftPanel`:

- Chinese working question draft
- English question draft
- PICO / PECO draft table
- Suggested Meta type draft
- six mockup-facing Meta type candidate cards:
  - Prognostic factor meta
  - Biomarker expression difference meta
  - Diagnostic accuracy meta
  - Intervention effect meta
  - Adverse event meta
  - Other meta type
- navigation-only `Next Search Strategy` button

The existing 10 active Meta type registry cards remain unchanged, preserving the current IA/test contract. Network Meta remains planned / disabled.

## Explicit Non-Changes

This stage did not:

- implement Search Strategy runtime
- implement Import / Reference / Dedup runtime
- implement Screening runtime
- implement Extraction / Risk of Bias runtime
- enable Pairwise Meta
- enable Network Meta
- enable any Meta executor
- generate pooled effect, forest plot, heterogeneity, or publication-bias output
- generate report-ready package
- enable DOCX / HTML / PDF / CSV / XLSX export
- enable Chinese database direct retrieval
- enable Chinese PDF extraction
- change App icon, Finder icon, `.icns`, `Info.plist`, LaunchServices, `dist/**`, or desktop entry
- package or run the packaged app

## Test Coverage

Added `tests/ui/test_meta_analysis_project_question_gated_pages.py` covering:

- Project Home gated runtime status and project summary
- Question & Meta Type draft fields, PICO / PECO table, candidate cards, and navigation-only next action
- Network Meta planned / disabled boundary
- absence of Chinese database direct retrieval and Chinese PDF extraction surfaces
- preservation of existing target IA, legacy `page_keys()`, and the 10 active type registry

## Validation

| Command | Result |
|---|---|
| `python3 -m pytest -q tests/ui/test_meta_analysis_ia_shell.py` | Passed: 10 tests |
| `python3 -m pytest -q tests/ui/test_meta_analysis_project_question_gated_pages.py` | Passed: 4 tests |
| `python3 -m pytest -q tests/ui/test_meta_analysis_ia_shell.py tests/ui/test_meta_analysis_project_question_gated_pages.py` | Passed: 14 tests |
| `python3 -m pytest -q tests/shared/test_result_report_export_shell.py` | Passed: 5 tests |
| `python3 -m app.main --smoke-test` | Passed; source launch smoke reported PySide6 available |
| `git diff --check` | Passed |

`git diff --cached --check` will be run after staging for the commit gate.

## Current Boundary

Meta Analysis remains Developer Preview / testing. Project Home and Question & Meta Type are safe gated runtime pages only. Result/report/export gates remain disabled, and no formal result semantics are introduced.
