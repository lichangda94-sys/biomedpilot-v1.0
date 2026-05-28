# Meta Analysis UI-C2d Screening + Extraction / Risk of Bias Gated Pages

## Scope

This stage implemented the third Meta Analysis gated runtime batch:

- Screening / 文献筛选
- Full-text / Extraction / 全文与数据提取
- Risk of Bias / 质量评价预览

The implementation is draft and preview UI only. It does not create final included studies, extract data automatically, judge risk of bias automatically, run pairwise meta, generate results, generate reports, or enable export.

## Runtime Changes

### Screening

Added `metaScreeningRuntimePanel` for `screening` with:

- draft counts table
- reference queue
- reference detail panel
- draft decision buttons:
  - Include draft
  - Exclude draft
  - Uncertain
  - Need full text
- AI suggestion advisory card
- `Save Draft Decision` action

Gate properties:

- `screeningState=draft_decisions_only`
- `aiBoundary=advisory_only`
- `resultSemanticKey=no_formal_result`
- `reportStatusKey=report.status.draft`
- `exportGate=disabled_empty_result`
- `formalActionEnabled=false`

### Full-text / Extraction

Extended the existing `metaFulltextExtractionPanel` while preserving the established tab contract:

- 全文管理
- 提取表设计
- 提取完成核查
- 历史记录

Added:

- full-text status preview table
- type-specific draft extraction fields:
  - `first_author`
  - `year`
  - `cancer_type`
  - `marker_name`
  - `effect_measure`
  - `effect_value`
  - `ci_lower`
  - `ci_upper`
  - `adjusted_model`
  - `outcome_name`
- mockup-only / draft extraction marking for effect value and CI fields
- disabled `Mark as Draft Extracted - adapter needed`

The existing compatibility object names remain intact for prior IA tests.

### Risk of Bias

Added `metaRiskOfBiasRuntimePanel` for `quality_assessment` with:

- NOS Selection
- NOS Comparability
- NOS Outcome
- ROBINS-I Confounding
- QUADAS-2 not-applicable preview
- preview score notice
- disabled `Save RoB Draft - adapter needed`

Gate properties:

- `riskOfBiasState=preview_in_progress`
- `aiBoundary=advisory_only`
- `resultSemanticKey=no_formal_result`
- `reportStatusKey=report.status.draft`
- `exportGate=disabled_empty_result`
- `formalActionEnabled=false`

## Explicit Non-Changes

This stage did not:

- enable AI final screening
- create final included studies
- create final PRISMA counts
- automatically advance to full-text inclusion
- enable non-English PDF extraction
- enable PDF OCR or table extraction
- automatically complete extraction
- automatically judge risk of bias
- enable Pairwise Meta
- generate aggregate estimates
- generate plot outputs
- enable result / report / export
- enable Network Meta
- package or run the packaged app
- touch UI-B10 / App icon / Finder icon / `.icns` / `Info.plist` / LaunchServices

## Test Coverage

Added `tests/ui/test_meta_analysis_screening_extraction_rob_gated_pages.py` covering:

- Screening page opens and remains draft-only.
- `Save Draft Decision` exists and `Submit Decision` is absent.
- AI suggestion is advisory only.
- Screening counts are draft counts, not final PRISMA counts.
- Full-text / Extraction tab structure remains unchanged.
- Draft extraction fields are present.
- effect value / CI fields are marked mockup-only / draft.
- `Mark as Draft Extracted` is disabled / adapter-needed.
- Risk of Bias page opens with draft / in-progress preview states.
- No automatic RoB final judgement or formal quality score is introduced.
- Shared Result / Report / Export and Network Meta gates remain disabled.

## Validation

| Command | Result |
|---|---|
| `python3 -m pytest -q tests/ui/test_meta_analysis_screening_extraction_rob_gated_pages.py` | Passed: 4 tests |
| `python3 -m pytest -q tests/ui/test_meta_analysis_ia_shell.py` | Passed: 10 tests |
| `python3 -m pytest -q tests/ui/test_meta_analysis_project_question_gated_pages.py tests/ui/test_meta_analysis_search_reference_gated_pages.py` | Passed: 8 tests |
| `python3 -m pytest -q tests/ui/test_meta_analysis_ia_shell.py tests/ui/test_meta_analysis_project_question_gated_pages.py tests/ui/test_meta_analysis_search_reference_gated_pages.py tests/ui/test_meta_analysis_screening_extraction_rob_gated_pages.py tests/shared/test_result_report_export_shell.py` | Passed: 27 tests |
| `python3 -m app.main --smoke-test` | Passed; source launch smoke reported PySide6 available |
| `git diff --check` | Passed |

`git diff --cached --check` will be run after staging for the commit gate.

## Current Boundary

Meta Analysis remains Developer Preview / testing. Screening, extraction, and risk-of-bias pages are gated draft shells. They do not produce final evidence decisions, formal quality scores, analysis-ready datasets, results, reports, or exportable artifacts.
