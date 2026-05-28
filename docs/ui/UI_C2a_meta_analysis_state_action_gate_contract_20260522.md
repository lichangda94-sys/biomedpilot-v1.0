# Meta Analysis UI-C2a State / Action Gate Contract

## 1. Scope

This contract defines the state and action gate model required before implementing Meta Analysis runtime pages from the UI-C1d/C1d2 mockups.

It is a planning artifact only. It does not implement UI pages, modify runtime code, add backend features, or enable executors.

## 2. Global Page State Model

Every Meta Analysis runtime page must expose a compact state model with these fields:

| field | values | rule |
|---|---|---|
| `page_key` | stable page id | Must map to current target IA keys or planned subpage ids. |
| `module_key` | `module.meta_analysis` | Required for tests and icon/status adoption. |
| `runtime_status` | `shell_only`, `testing`, `planned`, `blocked_until_backend` | Must not imply production readiness. |
| `processing_mode` | `english_first`, `local_draft_only`, `reviewer_controlled` | English-first and reviewer control are default. |
| `ai_boundary` | `advisory_only`, `not_available` | AI must never write final decisions. |
| `network_meta_state` | `planned_disabled` | Network Meta remains inactive. |
| `result_semantic` | `testing_summary_only`, `no_formal_result` | No formal pooled result. |
| `report_status` | `draft`, `blocked`, `not_ready` | No report-ready package. |
| `export_gate` | `disabled_empty_result`, `report_not_ready`, `adapter_missing` | All export remains disabled. |

## 3. Workflow State Model

| workflow_state | owner page | state purpose | default status |
|---|---|---|---|
| `project_home` | Project Home | project shell, workflow overview, gate summary | shell_only |
| `question_type` | Question & Meta Type | research question draft and active Meta type selection | testing |
| `search_strategy` | Search Strategy | English search query draft and database draft scope | testing |
| `reference_management` | Import / Reference Management | reference table preview and import-source shell | testing |
| `deduplication` | Deduplication | duplicate risk review and manual decision preview | testing |
| `screening` | Screening | draft reviewer screening decisions | testing |
| `fulltext_extraction` | Full-text / Extraction | full-text status and type-specific extraction draft | testing |
| `risk_of_bias` | Risk of Bias | draft RoB domains and reviewer confirmation boundary | planned/testing |
| `pairwise_input` | Pairwise Meta Input | effect-row review and analysis preflight shell | planned |
| `result_review` | Result Review | no-formal-result review and limitation acknowledgement | shell_only |
| `report_ready_gate` | Report-ready Gate | blocker checklist and draft gate state | shell_only |
| `export` | Report Export | format-readiness and disabled export gate | shell_only |

## 4. Action Gate Categories

| category | description | examples | implementation rule |
|---|---|---|---|
| `allowed_navigation` | Route/view changes only | Next step, back, select workflow step | Allowed if it does not mutate data or run services. |
| `draft_only` | Local UI draft action with no final semantic | edit draft question, edit PICO fields, draft query text | Must show draft state and not produce final artifacts. |
| `reviewer_controlled` | Human decision action that may later save draft/final after adapter design | Save Draft Decision, Mark as Draft Extracted | C2 runtime must keep draft/advisory wording unless backend adapter is explicitly planned. |
| `disabled` | Visible but not actionable | Generate Report, Export DOCX, Run Formal Meta | Button disabled and gate reason visible. |
| `blocked_until_backend` | Requires backend/store/adapter contract | real import, save extraction, formal RoB completion | Must stay blocked until separate backend readiness stage. |
| `future_planned` | Future product direction | Network Meta, production PDF export | Disabled/planned state only. |

## 5. Page-Level Action Matrix

### Project Home

Allowed:

- view workflow overview
- view project summary
- navigate to next step

Disabled:

- report generation
- export
- formal result actions
- statistical analysis

State:

- `Developer Preview / testing`
- `report not ready`
- `no formal result`

### Question & Meta Type

Allowed:

- edit draft Chinese research question
- edit English question draft
- edit PICO/PECO/PICOS draft fields
- choose an active Meta type as a workflow-control draft

Disabled:

- Network Meta activation
- final protocol confirmation
- search execution
- result/report/export actions

State:

- `testing`
- `schema_shell`
- `Network Meta = planned_disabled`

### Search Strategy

Allowed:

- build English query draft
- edit term groups and Boolean logic
- choose database draft scope
- copy query text

Disabled:

- Chinese database direct retrieval
- PubMed/Embase/Web of Science execution in the ordinary C2 shell
- auto import
- final search confirmation

State:

- `English-first processing`
- `draft_only`
- `AI suggestion only`

### Import / Reference Management + Deduplication

Allowed:

- view import source cards
- view reference table preview
- view duplicate risk groups
- compare duplicates as draft

Disabled:

- real file import
- automatic merge
- automatic delete
- auto-send to screening
- final included-study status

State:

- `local_draft_only`
- `reviewer_dedup_required`

### Screening

Allowed:

- view reference queue and details
- save draft include / exclude / uncertain / need full text decision if adapter exists
- record exclusion reason draft

Disabled:

- AI final decision
- final included studies
- final PRISMA counts
- automatic full-text inclusion

State:

- `manual_review`
- `draft_counts`
- `AI suggestion advisory`

### Extraction + Risk of Bias

Allowed:

- view full-text library
- edit draft extraction fields
- view draft RoB domain table
- mark draft extracted only if adapter exists

Disabled:

- Chinese PDF extraction
- automatic PDF OCR/table extraction
- final extraction save
- automatic RoB judgement
- formal analysis input promotion

State:

- `draft_extraction`
- `risk_of_bias_preview`
- `reviewer_confirmation_required`

### Pairwise Input

Allowed:

- view effect-row draft table
- validate input package preview
- show model/preflight blocker state

Disabled:

- run pooled effect
- run Network Meta
- create formal result
- generate forest plot

State:

- `planned`
- `preflight/testing boundary`

### Result Review + Report-ready Gate

Allowed:

- view result readiness summary
- view draft pairwise input preview
- view report-ready blockers
- acknowledge gate state

Disabled:

- formal pooled result
- forest plot rendering
- heterogeneity/publication bias output
- mark report-ready
- generate report
- export

State:

- `result.semantic.testing_summary_only`
- `report.status.draft`
- `report_ready=blocked`
- `exportGate=disabled_empty_result`

### Report Export

Allowed:

- view report template preview
- view export readiness and disabled reasons

Disabled:

- DOCX export
- HTML export
- PDF export
- CSV export
- XLSX export
- ZIP/reproducibility package export

State:

- `report.status.draft`
- `report_ready gate_not_passed`
- `exportGate disabled`
- `no_file_write`

## 6. Forbidden Claims

Runtime UI must not display or imply:

- production systematic review capability
- clinical/regulatory evidence output
- Network Meta active support
- Chinese database direct retrieval
- Chinese PDF extraction
- AI automatic screening/extraction/conclusion
- formal pooled effect
- real forest plot without formal result
- heterogeneity/publication bias results
- report-ready package
- active export package

## 7. Required Test Assertions

Future implementation tests should assert:

- 10 main-flow pages plus Meta Settings remain stable.
- Network Meta button/card is disabled and `planned_disabled`.
- Search page contains no Chinese direct retrieval action.
- Extraction page contains no Chinese PDF extraction action.
- AI suggestion widgets expose advisory-only properties/copy.
- Forest plot area is empty/boundary until formal result exists.
- Result/report/export shell remains gated.
- Export buttons are disabled and write no files.
- `python3 -m app.main --smoke-test` passes.
