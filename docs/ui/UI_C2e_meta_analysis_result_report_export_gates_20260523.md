# Meta Analysis UI-C2e Result Review + Report-ready / Export Gate Pages

## Scope

This stage implemented the final Meta Analysis gated runtime batch:

- Result Review / 结果复核
- Report-ready Gate / 报告就绪门控
- Report Export / 报告导出门控

The implementation only displays result, report, export, and human-review boundaries. It does not enable pairwise execution, Network Meta, pooled effects, plots, heterogeneity, publication-bias output, report-ready packages, report generation, export, or file writes.

## Runtime Changes

### Result Review

Added `metaResultReviewRuntimePanel` for `result_report` with:

- human review notice concentrated on the result review page
- result readiness summary table
- draft pairwise input preview
- no-formal-result state

Gate properties:

- `resultSemanticKey=testing_summary_only`
- `formalResultSemanticKey=no_formal_result`
- `reportStatusKey=report.status.draft`
- `reportReadyState=blocked`
- `exportGate=disabled_empty_result`
- `fileWriteAllowed=false`
- `formalActionEnabled=false`

Displayed gate states:

- `formal_pooled_effect = none`
- `forest_plot = disabled_boundary`
- `heterogeneity = none`
- `publication_bias = none`
- `ai_suggestion = advisory_only`

### Report-ready Gate

Added `metaReportReadyBlockerChecklist` on the result/report page with blockers:

- research question/type confirmation missing or draft
- search strategy draft
- references not finalized
- screening not final
- extraction not final
- risk of bias not final
- pairwise input not formal
- formal result missing

`metaGenerateReportDisabledButton` remains disabled and file-write blocked.

### Report Export

Added `metaReportExportGateRuntimePanel` for `report_export` with:

- export gate reason table
- all export format buttons disabled:
  - DOCX
  - HTML
  - PDF
  - CSV
  - XLSX
  - ZIP
- `Export will be enabled after gate.` notice

Gate properties:

- `resultSemanticKey=no_formal_result`
- `reportStatusKey=report.status.draft`
- `reportReadyState=blocked`
- `exportGate=disabled_empty_result`
- `fileWriteAllowed=false`
- `formalActionEnabled=false`

## Shared RRE Compatibility

The shared `resultReportExportAdoptionPanel` remains in place and gated:

- `resultSemanticKey` is not `formal_computed_result`
- `reportStatusKey` is not `report_ready`
- `exportGate=disabled_empty_result`
- `reportReadyPackageAllowed=false`
- export buttons remain disabled

## Explicit Non-Changes

This stage did not:

- enable Pairwise Meta executor
- enable Network Meta
- generate formal pooled effects
- generate HR / OR / RR pooled results
- generate heterogeneity or publication-bias output
- generate plot output
- generate report-ready package
- enable Generate Report
- enable DOCX / HTML / PDF / CSV / XLSX / ZIP export
- write any report or export file
- upgrade draft extraction / draft screening / draft RoB into formal result
- package or run the packaged app
- touch UI-B10 / App icon / Finder icon / `.icns` / `Info.plist` / LaunchServices

## Test Coverage

Added `tests/ui/test_meta_analysis_result_report_export_gates.py` covering:

- Result Review opens and remains no-formal-result / testing summary only.
- formal pooled effect, plot, heterogeneity, and publication-bias outputs remain absent as computed results.
- Report-ready blocker checklist is complete.
- Generate Report remains disabled and file-write blocked.
- Report Export opens and all formats are disabled.
- export gate reasons remain visible.
- shared Result / Report / Export shell remains gated.
- Network Meta remains planned / disabled.

## Validation

| Command | Result |
|---|---|
| `python3 -m pytest -q tests/ui/test_meta_analysis_result_report_export_gates.py` | Passed: 4 tests |
| `python3 -m pytest -q tests/ui/test_meta_analysis_project_question_gated_pages.py tests/ui/test_meta_analysis_search_reference_gated_pages.py tests/ui/test_meta_analysis_screening_extraction_rob_gated_pages.py` | Passed: 12 tests |
| `python3 -m pytest -q tests/ui/test_meta_analysis_ia_shell.py tests/shared/test_result_report_export_shell.py` | Passed: 15 tests |
| `python3 -m pytest -q tests/ui/test_meta_analysis_ia_shell.py tests/ui/test_meta_analysis_project_question_gated_pages.py tests/ui/test_meta_analysis_search_reference_gated_pages.py tests/ui/test_meta_analysis_screening_extraction_rob_gated_pages.py tests/ui/test_meta_analysis_result_report_export_gates.py tests/shared/test_result_report_export_shell.py` | Passed: 31 tests |
| `python3 -m app.main --smoke-test` | Passed; source launch smoke reported PySide6 available |
| `git diff --check` | Passed |

`git diff --cached --check` will be run after staging for the commit gate.

## Current Boundary

Meta Analysis remains Developer Preview / testing. Result review, report-ready, and export surfaces are gate previews only. They do not produce computed results, plot artifacts, report-ready packages, exports, or file writes.
