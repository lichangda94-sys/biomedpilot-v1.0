# Meta Analysis UI-C2a Result / Report / Export Gate Contract

## 1. Purpose

This document defines the Result / Report / Export gate semantics for Meta Analysis runtime UI planning. It translates UI-C1d/C1d2 result, report-ready, and export mockups into a safe gate contract.

This is not an implementation task and does not enable result generation, report generation, or export.

## 2. Global RRE State

| key | allowed values in C2 implementation | default |
|---|---|---|
| `result_semantic` | `result.semantic.testing_summary_only`, `no_formal_result` | `result.semantic.testing_summary_only` |
| `report_status` | `report.status.draft`, `blocked`, `not_ready` | `report.status.draft` |
| `export_gate` | `disabled_empty_result`, `report_not_ready`, `adapter_missing` | `disabled_empty_result` |
| `forest_plot` | `disabled_boundary` | `disabled_boundary` |
| `pooled_effect` | `none` | `none` |
| `heterogeneity` | `none` | `none` |
| `publication_bias` | `none` | `none` |
| `network_meta` | `planned_disabled` | `planned_disabled` |
| `report_ready_package_allowed` | `false` | `false` |
| `file_write_allowed` | `false` | `false` |

## 3. Result Review Gate

The Result Review page may display:

- upstream workflow readiness summary
- draft pairwise input preview
- missing formal result explanation
- disabled forest/table boundary
- limitation acknowledgement
- blockers for report-ready gate

It must not display:

- fake forest plot
- fake pooled HR / OR / RR / MD / SMD
- fake heterogeneity Q / I2 / tau2
- fake publication bias or Egger result
- formal clinical interpretation
- report-ready success state

Required properties or equivalent testable state:

- `resultSemanticKey != result.semantic.formal_computed_result`
- `resultSemanticKey in {result.semantic.testing_summary_only, no_formal_result}`
- `formalActionEnabled=false`
- `forestPlotState=disabled_boundary`
- `pooledEffectState=none`

## 4. Report-ready Gate

The Report-ready Gate may display:

- checklist of blocker items
- status for research question/type confirmation
- search strategy confirmation
- deduplication confirmation
- screening completion
- extraction completion
- risk-of-bias completion
- pairwise input confirmation
- analysis plan consistency
- result reportability check

It must not display:

- final pass state unless all gates are genuinely implemented in a later stage
- publication-ready or submission-ready copy
- clinical/regulatory report copy
- automatic report-ready transition

Required state:

- `report_status=report.status.draft`
- `report_ready=blocked`
- `reportReadyPackageAllowed=false`
- `generateReportEnabled=false`

## 5. Export Gate

Export page may display disabled format options:

- DOCX
- HTML
- PDF
- CSV
- XLSX
- ZIP / reproducibility package

All format actions remain disabled in C2 unless a later explicit export-adapter stage changes this contract.

Required state:

- `exportGate=disabled_empty_result` or `report_not_ready` or `adapter_missing`
- `exportEnabled=false`
- `fileWriteAllowed=false`
- `allExportButtonsDisabled=true`

Forbidden:

- writing report files
- writing CSV/XLSX output
- writing ZIP/reproducibility packages
- opening save dialogs as active export
- displaying export history as if real exports happened

## 6. Mapping From Mockups

| mockup | page | gate interpretation |
|---|---|---|
| META-MOCK-007 | Result Review + Report-ready Gate | Use as late-stage gate page; pairwise table is draft input preview, not analysis output. |
| META-MOCK-008 | Report Export Gate | Use as export-gate shell; all formats disabled; `Enable Export after Gate` must be disabled or reworded. |

## 7. Shared Shell Adoption

Current Meta Analysis runtime already adopts `make_result_report_export_adoption_panel(module="meta_analysis")`. UI-C2 implementation may continue using shared shell semantics and add page-specific wrappers, but must preserve:

- `resultSemanticKey=result.semantic.testing_summary_only`
- `reportStatusKey=report.status.draft`
- `exportGate=disabled_empty_result`
- disabled export buttons
- no report-ready package

## 8. Page-Level Gate States

| page | result_semantic | report_status | export_gate | note |
|---|---|---|---|---|
| Project Home | testing_summary_only | draft | disabled_empty_result | Overview only. |
| Question & Meta Type | no_formal_result | draft | disabled_empty_result | Workflow control draft only. |
| Search Strategy | no_formal_result | draft | disabled_empty_result | English query draft only. |
| Import / Reference + Dedup | no_formal_result | draft | disabled_empty_result | Local draft/reference preview only. |
| Screening | no_formal_result | draft | disabled_empty_result | Draft reviewer decisions only. |
| Extraction + Risk of Bias | no_formal_result | draft | disabled_empty_result | Draft extraction/ROB preview only. |
| Pairwise Input | no_formal_result | draft | disabled_empty_result | Effect-row preflight only. |
| Result Review | testing_summary_only | draft / blocked | disabled_empty_result | No formal pooled effect. |
| Report-ready Gate | testing_summary_only | draft / blocked | report_not_ready | Report-ready blocked. |
| Report Export | testing_summary_only | draft / not_ready | disabled_empty_result / adapter_missing | All formats disabled. |

## 9. Tests Required Before Runtime Implementation Closure

Future C2 tests should check:

- no `result.semantic.formal_computed_result` appears on result/review/export shell pages
- no enabled `Generate Report` button exists
- no enabled `Export DOCX/HTML/PDF/CSV/XLSX/ZIP` button exists
- forest/table preview has empty/boundary state only
- pairwise table is labelled draft input preview
- report-ready button is disabled
- export action does not write files
- shared Result/Report/Export shell tests still pass

## 10. Future Change Gate

Any future stage that wants to enable formal results, report-ready transition, or export must first provide:

- executor readiness audit
- result schema and artifact manifest contract
- report template gate contract
- export/file-picker adapter contract
- no-fake-output tests
- file-write tests
- failure-state tests

Until then, all RRE surfaces remain gated.
