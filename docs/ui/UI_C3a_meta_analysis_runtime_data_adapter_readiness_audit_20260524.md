# Meta Analysis UI-C3a Runtime Data / Adapter Readiness Audit

Date: 2026-05-24

## 1. Scope

This audit evaluates whether Meta Analysis can move beyond the UI-C2 gated runtime shell into runtime data, storage, import, extraction, analysis, report, or export adapters.

This stage is audit-only. It does not modify runtime UI, tests, assets, scripts, packaging, `dist/**`, App icon, Finder icon, Info.plist, LaunchServices, or packaged app behavior. It does not enable any Meta executor.

Reviewed inputs:

- `docs/ui/UI_C2a_meta_analysis_state_action_gate_contract_20260522.md`
- `docs/ui/UI_C2a_meta_analysis_result_report_export_gate_contract_20260522.md`
- `docs/ui/UI_C2f_meta_analysis_gated_ui_closure_audit_20260523.md`
- `docs/ui/UI_C2f_meta_analysis_runtime_status_matrix_20260523.csv`
- `app/meta_analysis/workspace.py`
- `app/meta_analysis/project_workspace.py`
- `app/shared/result_report_export_shell.py`
- `tests/ui/test_meta_analysis_*.py`
- `tests/shared/test_result_report_export_shell.py`

## 2. Decision

Decision: `not_ready_for_executor_or_export`.

Recommended next action: `plan_meta_runtime_data_adapters`.

Meta Analysis is ready for adapter planning, but not ready to enable real search/import/screening/extraction persistence, pairwise Meta execution, forest plot generation, report-ready package generation, or export.

## 3. Current Runtime Inventory

| Area | Current status | Evidence |
| --- | --- | --- |
| 10-page target IA | stable gated UI | `meta_target_ia_pages()` and C2f tests |
| Project workspace | minimal project manifest support | `project_workspace.py` |
| Question/type draft | UI draft only | `MetaAnalysisWorkspaceWidget` runtime panels |
| Search strategy | English query draft only | C2c tests |
| Reference/import | preview cards only | C2c tests |
| Deduplication | duplicate risk preview only | C2c tests |
| Screening | draft decisions only | C2d tests |
| Extraction | draft fields only | C2d tests |
| Risk of Bias | preview/draft rows only | C2d tests |
| Pairwise input | draft preview only | C2e tests |
| Result/report/export gate | disabled shared shell | C2e/C2f tests |
| Meta executor | absent from active runtime | no executor package under `app/meta_analysis` |
| File write | disabled for report/export | C2f matrix: `file_write_allowed=false` |

## 4. Adapter Readiness Findings

Current ready-for-planning areas:

- project manifest adapter
- local draft data schema
- search strategy draft storage
- reference import adapter contract
- screening draft decision store
- extraction draft store
- RoB draft store
- pairwise input schema contract
- result/report/export gate contract

Current not-ready areas:

- PubMed / Embase / Web of Science execution adapter
- Chinese database direct retrieval
- Chinese PDF extraction
- automatic PDF OCR/table extraction
- AI final decision adapter
- pairwise Meta executor
- Network Meta
- forest plot generation
- pooled effect / heterogeneity / publication bias
- report-ready package builder
- DOCX / HTML / PDF / CSV / XLSX / ZIP export writer

## 5. Required Adapter Stack Before Runtime Enablement

Meta runtime data work should be split into narrow stages:

1. `MetaProjectDataStore`
   - stores draft question, PICO/PECO, selected Meta type, and workflow status
   - no executor
2. `MetaReferenceStore`
   - stores imported references and deduplication review decisions
   - import adapters remain disabled until file-picker and parser contracts exist
3. `MetaScreeningStore`
   - stores draft screening decisions only
   - final included studies remain disabled until reviewer confirmation is defined
4. `MetaExtractionStore`
   - stores draft extraction rows and full-text status
   - no Chinese PDF extraction or automatic extraction
5. `MetaRiskOfBiasStore`
   - stores reviewer draft RoB rows
   - no automatic final judgement
6. `MetaPairwiseInputStore`
   - validates effect-row compatibility
   - does not execute pooled effect
7. `MetaResultRegistry`
   - only after executor readiness
   - must distinguish draft/preflight from formal pooled result
8. `MetaReportReadyGate`
   - only after formal result and reviewer acceptance
9. `MetaExportAdapter`
   - only after report-ready and file-picker contracts

## 6. Gate Requirements Before Executor Activation

Before any pairwise Meta executor can be enabled:

- study inclusion must be final and reviewer-confirmed
- extraction rows must be complete and schema-compatible
- risk-of-bias status must be reviewer-confirmed or explicitly allowed as missing
- effect measure compatibility must pass
- model selection must be explicit
- zero-cell/continuity-correction policy must be explicit where applicable
- heterogeneity/publication-bias output contracts must be defined
- forest plot output contract must be defined
- formal result registry must be implemented
- report-ready gate must remain blocked until review is complete
- export must remain disabled until report-ready and file picker are implemented

## 7. Boundary Decisions

| Capability | Decision | Reason |
| --- | --- | --- |
| English query draft | can plan storage | safe draft-only artifact |
| database execution | blocked | no retrieval adapter contract |
| reference import | adapter planning only | parser/file-picker/error model missing |
| deduplication | reviewer draft only | no auto merge/delete |
| screening | draft decision store planning | no final AI/human inclusion gate yet |
| extraction | draft store planning | no PDF/OCR/auto extraction |
| RoB | draft store planning | no final automated judgement |
| pairwise Meta | blocked | executor/result schema gates missing |
| Network Meta | planned_disabled | out of current scope |
| report-ready | blocked | no formal result/review gate |
| export | disabled | no report-ready and no export adapter |

## 8. Recommended Next Stages

Recommended sequence:

1. `Meta UI-C3b Runtime Data Store Contract`
2. `Meta UI-C3c Reference Import / Dedup Adapter Planning`
3. `Meta UI-C3d Screening / Extraction / RoB Draft Store Pilot`
4. `Meta UI-C3e Pairwise Input Schema Readiness Audit`
5. `Meta UI-C3f Executor Readiness Audit`
6. `Meta UI-C3g Result / Report / Export Adapter Planning`

Do not jump directly to pairwise Meta execution, forest plot, report-ready, or export.

## 9. Verification

Verification commands:

- `python3 -m pytest -q tests/ui/test_meta_analysis_ia_shell.py tests/ui/test_meta_analysis_project_question_gated_pages.py tests/ui/test_meta_analysis_search_reference_gated_pages.py tests/ui/test_meta_analysis_screening_extraction_rob_gated_pages.py tests/ui/test_meta_analysis_result_report_export_gates.py tests/shared/test_result_report_export_shell.py`
- CSV structure check for `docs/ui/UI_C3a_meta_analysis_runtime_data_adapter_readiness_matrix_20260524.csv`
- `python3 -m app.main --smoke-test`

Results are recorded after the verification run.

Verification results:

| Command | Result |
| --- | --- |
| `python3 -m pytest -q tests/ui/test_meta_analysis_ia_shell.py tests/ui/test_meta_analysis_project_question_gated_pages.py tests/ui/test_meta_analysis_search_reference_gated_pages.py tests/ui/test_meta_analysis_screening_extraction_rob_gated_pages.py tests/ui/test_meta_analysis_result_report_export_gates.py tests/shared/test_result_report_export_shell.py` | passed, 31 tests |
| CSV structure check for `docs/ui/UI_C3a_meta_analysis_runtime_data_adapter_readiness_matrix_20260524.csv` | passed, 14 rows |
| `python3 -m app.main --smoke-test` | passed |

## 10. Conclusion

Meta Analysis is ready for runtime data adapter planning, not runtime execution. The correct next move is to define stores and adapters for draft workflow data while keeping executor, result, report-ready, and export gates disabled.
