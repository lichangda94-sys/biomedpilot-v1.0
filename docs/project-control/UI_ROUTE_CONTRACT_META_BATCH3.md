# UI Route Contract Meta Batch 3

- Created: `2026-06-01T15:19:34.997513+00:00`
- Branch: `integration/release-bio-c1-ui-shell`
- HEAD: `601dea0262874a3e1e38313411937a2fb4b5cc9a`
- Scope: Meta Analysis UIShell mature target IA, adapter gates, and first-level runtime artifact audit.

## Summary

- Rows: 33
- Connected: 18
- Disabled with reason: 15
- Broken: 0

## Approved Structure

- UIShell target IA remains the final visual baseline.
- Old workflow pages and services are capability sources; they do not replace the mature gated shell.
- PubMed/Search/Dedup/Screening capabilities are connected only where a visible UIShell gate or adapter button proves the service/artifact path.

## Rows

| Contract | Surface | Object | Status | Behavior | Evidence |
| --- | --- | --- | --- | --- | --- |
| META-IA-PROJECT_HOME | Meta Target IA | `metaTargetIANavItem` | connected | `navigates_to_meta_target_ia_page_project_home` | current_target_page_key=project_home |
| META-IA-QUESTION_META_TYPE | Meta Target IA | `metaTargetIANavItem` | connected | `navigates_to_meta_target_ia_page_question_meta_type` | current_target_page_key=question_meta_type |
| META-IA-SEARCH_STRATEGY | Meta Target IA | `metaTargetIANavItem` | connected | `navigates_to_meta_target_ia_page_search_strategy` | current_target_page_key=search_strategy |
| META-IA-IMPORT_DEDUP | Meta Target IA | `metaTargetIANavItem` | connected | `navigates_to_meta_target_ia_page_import_dedup` | current_target_page_key=import_dedup |
| META-IA-SCREENING | Meta Target IA | `metaTargetIANavItem` | connected | `navigates_to_meta_target_ia_page_screening` | current_target_page_key=screening |
| META-IA-FULLTEXT_EXTRACTION | Meta Target IA | `metaTargetIANavItem` | connected | `navigates_to_meta_target_ia_page_fulltext_extraction` | current_target_page_key=fulltext_extraction |
| META-IA-QUALITY_ASSESSMENT | Meta Target IA | `metaTargetIANavItem` | connected | `navigates_to_meta_target_ia_page_quality_assessment` | current_target_page_key=quality_assessment |
| META-IA-ANALYSIS_TASKS | Meta Target IA | `metaTargetIANavItem` | connected | `navigates_to_meta_target_ia_page_analysis_tasks` | current_target_page_key=analysis_tasks |
| META-IA-RESULT_REPORT | Meta Target IA | `metaTargetIANavItem` | connected | `navigates_to_meta_target_ia_page_result_report` | current_target_page_key=result_report |
| META-IA-REPORT_EXPORT | Meta Target IA | `metaTargetIANavItem` | connected | `navigates_to_meta_target_ia_page_report_export` | current_target_page_key=report_export |
| META-IA-META_SETTINGS | Meta Target IA | `metaTargetIANavItem` | connected | `navigates_to_meta_target_ia_page_meta_settings` | current_target_page_key=meta_settings |
| META-QUESTION-TYPE-SELECT | Question & Meta Type | `metaActiveTypeSelectButton` | connected | `selects_active_meta_type_and_updates_schema_shell_state` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch3_ly3qd0i9/project/Meta_Batch_3_Contract/ui_runtime/meta_question_type_gate.json; /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch3_ly3qd0i9/project/Meta_Batch_3_Contract/protocol/pico_workspace_draft.json |
| META-SEARCH-COPY-QUERY | Search Strategy | `metaCopyQueryButton` | connected | `copies_search_query_draft_to_clipboard` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch3_ly3qd0i9/project/Meta_Batch_3_Contract/ui_runtime/meta_search_query_copy_manifest.json |
| META-SEARCH-SAVE-UNCONFIRMED-GATE | Search Strategy | `metaSaveSearchDraftButton` | connected | `calls_search_strategy_builder_or_writes_disabled_reason` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch3_ly3qd0i9/project/Meta_Batch_3_Contract/ui_runtime/meta_search_strategy_disabled_reason.json |
| META-SEARCH-SAVE-CONFIRMED-STRATEGY | Search Strategy | `metaSaveSearchDraftButton` | connected | `calls_search_strategy_builder_or_writes_disabled_reason` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch3_ly3qd0i9/confirmed/Meta_Batch_3_Confirmed_Search/ui_runtime/meta_search_strategy_gate.json; /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch3_ly3qd0i9/confirmed/Meta_Batch_3_Confirmed_Search/protocol/search_strategy_v2/search_strategy_drafts.json |
| META-IMPORT-RIS_BIBTEX_ENDNOTE-GATE | Import & Deduplication | `metaImportSourceButton` | disabled | `disabled_import_adapter_needed` | 导入 adapter 接线未完成；不能伪装真实导入。 |
| META-IMPORT-CSV_EXCEL-GATE | Import & Deduplication | `metaImportSourceButton` | disabled | `disabled_import_adapter_needed` | 导入 adapter 接线未完成；不能伪装真实导入。 |
| META-IMPORT-PUBMED_RESULT_FILE-GATE | Import & Deduplication | `metaImportSourceButton` | disabled | `disabled_import_adapter_needed` | 导入 adapter 接线未完成；不能伪装真实导入。 |
| META-IMPORT-MANUAL_ENTRY-GATE | Import & Deduplication | `metaImportSourceButton` | disabled | `disabled_import_adapter_needed` | 导入 adapter 接线未完成；不能伪装真实导入。 |
| META-DEDUP-AUTO-MERGE-GATE | Import & Deduplication | `metaAutoMergeDisabledButton` | disabled | `disabled_dedup_mutation_gate` | 去重写入需要 reviewer-confirmed store；当前只显示 preview。 |
| META-DEDUP-AUTO-DELETE-GATE | Import & Deduplication | `metaAutoDeleteDisabledButton` | disabled | `disabled_dedup_mutation_gate` | 去重写入需要 reviewer-confirmed store；当前只显示 preview。 |
| META-DEDUP-SEND-SCREENING-GATE | Import & Deduplication | `metaSendToScreeningDisabledButton` | disabled | `disabled_dedup_mutation_gate` | 去重写入需要 reviewer-confirmed store；当前只显示 preview。 |
| META-SCREENING-SAVE-DRAFT-DECISION | Screening | `metaSaveDraftScreeningDecisionButton` | connected | `calls_screening_store_or_writes_draft_gate_artifact` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch3_ly3qd0i9/project/Meta_Batch_3_Contract/ui_runtime/meta_screening_draft_decision_gate.json |
| META-EXTRACTION-SAVE-DESIGN | Full-text & Extraction | `metaSaveExtractionDesignButton` | connected | `calls_extraction_schema_registry_and_writes_gate_artifact` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch3_ly3qd0i9/project/Meta_Batch_3_Contract/ui_runtime/meta_extraction_design_gate.json |
| META-QUALITY-ROB-DRAFT-GATE | Quality Assessment | `metaSaveRiskOfBiasDraftButton` | connected | `writes_risk_of_bias_disabled_reason` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch3_ly3qd0i9/project/Meta_Batch_3_Contract/ui_runtime/meta_risk_of_bias_disabled_reason.json |
| META-ANALYSIS-TASKS-FORMAL-ACTION-GATE | Meta Analysis Tasks | `metaTargetBoundaryDisabledAction` | disabled | `writes_disabled_reason_if_project_bound` | 正式执行仍被 gate 阻断。 |
| META-RESULT-REPORT-GENERATE-GATE | Result & Report | `metaGenerateReportDisabledButton` | disabled | `writes_report_ready_disabled_reason` | 缺少正式统计结果与 report-ready package。 |
| META-REPORT-EXPORT-DOCX-GATE | Report Export | `metaExportFormatDisabledButton` | disabled | `disabled_export_gate` | 报告导出需要 report-ready gate 通过。 |
| META-REPORT-EXPORT-HTML-GATE | Report Export | `metaExportFormatDisabledButton` | disabled | `disabled_export_gate` | 报告导出需要 report-ready gate 通过。 |
| META-REPORT-EXPORT-PDF-GATE | Report Export | `metaExportFormatDisabledButton` | disabled | `disabled_export_gate` | 报告导出需要 report-ready gate 通过。 |
| META-REPORT-EXPORT-CSV-GATE | Report Export | `metaExportFormatDisabledButton` | disabled | `disabled_export_gate` | 报告导出需要 report-ready gate 通过。 |
| META-REPORT-EXPORT-XLSX-GATE | Report Export | `metaExportFormatDisabledButton` | disabled | `disabled_export_gate` | 报告导出需要 report-ready gate 通过。 |
| META-REPORT-EXPORT-ZIP-GATE | Report Export | `metaExportFormatDisabledButton` | disabled | `disabled_export_gate` | 报告导出需要 report-ready gate 通过。 |

## Screenshots

Runtime screenshots are stored under `docs/ui/runtime_screenshots/20260601_meta_batch3_route_contract/`.

- `01_project_home.png`
- `02_question_meta_type.png`
- `03_search_strategy.png`
- `04_import_dedup.png`
- `05_screening.png`
- `06_fulltext_extraction.png`
- `07_quality_assessment.png`
- `08_analysis_tasks.png`
- `09_result_report.png`
- `10_report_export.png`
- `11_meta_settings.png`
