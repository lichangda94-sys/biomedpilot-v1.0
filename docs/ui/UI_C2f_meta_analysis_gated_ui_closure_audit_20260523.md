# Meta Analysis UI-C2f Gated UI Implementation Closure Audit

## 1. Scope

This audit closes Meta UI-C2b through UI-C2e gated runtime implementation.

Audited implementation commits:

- `bf6aaf8` - `feat(ui): implement Meta Analysis project and question gated pages`
- `e551f44` - `feat(ui): implement Meta Analysis search and reference gated pages`
- `557b645` - `feat/ui: implement Meta Analysis screening extraction gated pages`
- `6fe2295` - `feat(ui): implement Meta Analysis result report export gates`

This stage is documentation-only. It does not modify `app/**`, `tests/**`, `assets/**`, `scripts/**`, or `dist/**`.

## 2. Audited Inputs

- `docs/ui/UI_C2a_meta_analysis_implementation_gate_plan_20260522.md`
- `docs/ui/UI_C2a_meta_analysis_state_action_gate_contract_20260522.md`
- `docs/ui/UI_C2a_meta_analysis_result_report_export_gate_contract_20260522.md`
- `docs/ui/UI_C2b_meta_analysis_project_question_gated_pages_20260523.md`
- `docs/ui/UI_C2c_meta_analysis_search_reference_gated_pages_20260523.md`
- `docs/ui/UI_C2d_meta_analysis_screening_extraction_rob_gated_pages_20260523.md`
- `docs/ui/UI_C2e_meta_analysis_result_report_export_gates_20260523.md`
- `tests/ui/test_meta_analysis_project_question_gated_pages.py`
- `tests/ui/test_meta_analysis_search_reference_gated_pages.py`
- `tests/ui/test_meta_analysis_screening_extraction_rob_gated_pages.py`
- `tests/ui/test_meta_analysis_result_report_export_gates.py`
- `tests/ui/test_meta_analysis_ia_shell.py`
- `tests/shared/test_result_report_export_shell.py`

## 3. IA Closure

The Meta target IA remains stable:

- 10 main-flow pages remain present:
  - Project Home
  - Question & Meta Type
  - Search Strategy
  - Import & Deduplication
  - Screening
  - Full-text & Extraction
  - Quality Assessment
  - Meta Analysis Tasks
  - Result & Report
  - Report Export
- auxiliary `Meta Settings` remains present.
- legacy `page_keys()` remains compatible with the mainline shell contract:
  - `workflow_home`
  - `project_contract`
  - `dev_branch`
- Network Meta remains `planned_disabled`.
- the 10 active Meta type registry cards remain unchanged.

## 4. C2b Audit: Project Home + Question & Type

Closure status: complete.

Confirmed surfaces:

- `metaProjectHomeRuntimePanel`
- `metaQuestionTypeDraftPanel`
- PICO / PECO draft table
- Chinese working question draft
- English question draft
- suggested Meta type draft
- six mockup-facing Meta type candidate cards
- existing 10 active Meta type registry cards
- Network Meta planned / disabled

Confirmed boundaries:

- no result/report/export enabled state
- no final protocol confirmation
- no Network Meta activation
- no executor connection
- no report-ready package or export

## 5. C2c Audit: Search Strategy + Reference / Deduplication

Closure status: complete.

Confirmed surfaces:

- `metaSearchStrategyRuntimePanel`
- English term groups
- Boolean logic preview
- PubMed-style query draft
- database draft scope for PubMed / Embase / Web of Science
- `Copy Query` safe action
- disabled `Save Draft - adapter needed`
- `metaReferenceDedupRuntimePanel`
- import source cards for RIS / BibTeX / EndNote XML, CSV / Excel, PubMed result file, Manual entry
- reference table preview
- duplicate risk preview

Confirmed boundaries:

- no PubMed / Embase / Web of Science execution
- no CNKI / WanFang / VIP direct retrieval
- no Chinese database execution
- no real RIS / BibTeX / CSV / EndNote import
- no automatic merge
- no automatic delete
- no automatic send-to-screening
- no final included studies

## 6. C2d Audit: Screening + Extraction + Risk of Bias

Closure status: complete.

Confirmed surfaces:

- `metaScreeningRuntimePanel`
- draft counts
- reference queue
- reference detail
- draft decision buttons
- `Save Draft Decision`
- AI advisory-only card
- `metaFulltextExtractionPanel`
- required four-tab structure:
  - 全文管理
  - 提取表设计
  - 提取完成核查
  - 历史记录
- full-text status preview
- draft extraction fields for biomarker/prognostic Meta
- disabled `Mark as Draft Extracted - adapter needed`
- `metaRiskOfBiasRuntimePanel`
- NOS / ROBINS-I / QUADAS-2 preview rows

Confirmed boundaries:

- no AI final screening
- no final included studies
- no final PRISMA counts
- no automatic full-text inclusion
- no Chinese PDF extraction
- no PDF OCR / table extraction
- no automatic extraction completion
- no automatic RoB judgement
- no formal quality score

## 7. C2e Audit: Result Review + Report-ready / Export Gate

Closure status: complete.

Confirmed surfaces:

- `metaResultReviewRuntimePanel`
- human review notice concentrated on Result Review
- result readiness summary
- draft pairwise input preview
- report-ready blocker checklist
- disabled `Generate Report`
- `metaReportExportGateRuntimePanel`
- export gate reason table
- disabled DOCX / HTML / PDF / CSV / XLSX / ZIP buttons
- `Export will be enabled after gate.` wording
- shared `resultReportExportAdoptionPanel` remains gated

Confirmed boundaries:

- no Pairwise Meta executor
- no Network Meta
- no formal pooled effect
- no HR / OR / RR pooled result
- no forest plot artifact
- no heterogeneity result
- no publication-bias result
- no report-ready package
- no Generate Report action
- no export action
- no file write
- draft extraction / draft screening / draft RoB do not upgrade to formal result

## 8. Global Forbidden Capability Closure

All forbidden capabilities remain closed:

| Capability | Closure status |
|---|---|
| Meta executor | closed |
| Pairwise Meta | closed |
| Network Meta | planned / disabled |
| Chinese database direct retrieval | closed |
| Chinese PDF extraction | closed |
| formal pooled effect | closed |
| forest plot | closed |
| heterogeneity / publication bias | closed |
| report-ready package | closed |
| DOCX / HTML / PDF / CSV / XLSX / ZIP export | closed |
| file write | closed |
| packaged app runtime | not run |
| UI-B10 App icon / Finder / Info.plist / LaunchServices | untouched |

## 9. Runtime Status Matrix

The runtime status matrix is recorded in:

- `docs/ui/UI_C2f_meta_analysis_runtime_status_matrix_20260523.csv`

Summary:

- implemented gated runtime pages: Project Home, Question & Type, Search Strategy, Reference Management / Deduplication, Screening, Full-text / Extraction, Risk of Bias, Result Review, Report Export
- planned-disabled runtime surface: Meta Analysis Tasks
- auxiliary shell: Meta Settings
- all rows have `executor_connected=false`
- all rows have `file_write_allowed=false`

## 10. Validation

Commands required for this closure audit:

```bash
python3 -m pytest -q tests/ui/test_meta_analysis_ia_shell.py
python3 -m pytest -q tests/ui/test_meta_analysis_project_question_gated_pages.py
python3 -m pytest -q tests/ui/test_meta_analysis_search_reference_gated_pages.py
python3 -m pytest -q tests/ui/test_meta_analysis_screening_extraction_rob_gated_pages.py
python3 -m pytest -q tests/ui/test_meta_analysis_result_report_export_gates.py
python3 -m pytest -q tests/shared/test_result_report_export_shell.py
python3 -m app.main --smoke-test
git diff --check
git diff --cached --check
```

Results:

| Command | Result |
|---|---|
| `python3 -m pytest -q tests/ui/test_meta_analysis_ia_shell.py` | Passed: 10 tests |
| `python3 -m pytest -q tests/ui/test_meta_analysis_project_question_gated_pages.py` | Passed: 4 tests |
| `python3 -m pytest -q tests/ui/test_meta_analysis_search_reference_gated_pages.py` | Passed: 4 tests |
| `python3 -m pytest -q tests/ui/test_meta_analysis_screening_extraction_rob_gated_pages.py` | Passed: 4 tests |
| `python3 -m pytest -q tests/ui/test_meta_analysis_result_report_export_gates.py` | Passed: 4 tests |
| `python3 -m pytest -q tests/shared/test_result_report_export_shell.py` | Passed: 5 tests |
| `python3 -m app.main --smoke-test` | Passed; source launch smoke reported PySide6 available |
| `git diff --check` | Passed |

`git diff --cached --check` will be run after staging for the commit gate.

## 11. Next Stage Options

Recommended next-stage options:

- Option A: Meta UI-C3a Runtime Data / Adapter Readiness Audit
- Option B: LabTools C3 save/export/history adapter track
- Option C: Bioinformatics UI-C3a formal DEG carry-over readiness audit
- Option D: Integration / MainLine scoped carry-over audit

Preferred next step: Option A if the product focus remains Meta Analysis; otherwise Option D if the goal is to stabilize the mainline carry-over state across modules before adding adapters.

## 12. Business Code Change Declaration

This C2f audit stage only adds documentation and a status matrix. It does not modify runtime UI code, tests, assets, scripts, distribution output, packaged app metadata, App icon, Finder icon, `.icns`, `Info.plist`, LaunchServices, or desktop entry.
