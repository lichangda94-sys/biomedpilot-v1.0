# UI Route Contract Meta Batch 4: PubMed Search and Handoff

- Created: `2026-06-02T14:05:02.381879+00:00`
- Branch: `integration/release-bio-c1-ui-shell`
- HEAD: `4300b4ab1f913d88d2278a7ada0ac238c470b66e`
- Scope: Meta mature UIShell PubMed/search/handoff route contract: UI gate state plus deterministic service artifact proof.

## Summary

- Rows: 13
- Connected: 12
- Disabled with reason: 1
- UI gaps recorded: 0
- Broken: 0

## Source Matrix

- UI baseline: UIShell high-fidelity Meta target IA in app/meta_analysis/workspace.py; historical source line: ui: rebuild meta analysis workbench surfaces.
- Policy: Old protocol page buttons are backend capability evidence only; they do not replace mature UIShell pages.

## Screenshots

### search_strategy

![search_strategy](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_meta_batch4_pubmed_handoff/01_search_strategy_pubmed_gate.png)

### import_dedup

![import_dedup](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_meta_batch4_pubmed_handoff/02_import_dedup_pubmed_boundary.png)

## UI Page -> Backend Capability -> Branch Source -> Test

| Contract | UI Page | Backend Capability | Source | Object | Status | Expected Artifact | Observed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| META-PUBMED-UI-SEARCH-DRAFT-GATE | Search Strategy | SearchStrategyBuilderService gate or disabled reason | UIShell Meta mature page; current Integration HEAD | `metaSaveSearchDraftButton` | `connected` | /var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch4_qv6fw_3g/meta_pubmed_ui_project/ui_runtime/meta_search_strategy_disabled_reason.json | draft_gate_artifact_verified |
| META-PUBMED-UI-RUN-PUBMED-ACTION | Search Strategy | PubMed search execution | UIShell Meta mature Search Strategy page with scoped adapter button. | `metaRunPubMedSearchButton` | `connected` | /var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch4_qv6fw_3g/meta_pubmed_ui_project/ui_runtime/meta_pubmed_search_adapter.json | pubmed_execution_adapter_verified |
| META-PUBMED-UI-IMPORT-GATE | Import & Deduplication | PubMed result/candidate handoff adapter | UIShell Meta mature page; current Integration HEAD | `metaImportSourceButton` | `disabled` | protocol/pubmed_candidates/*_candidates_preview.json | disabled_with_reason |
| META-PUBMED-UI-LOAD-PREVIEW | Import & Deduplication | load PubMed candidate preview into reviewer-selection controls | UIShell Meta mature Import & Deduplication page with scoped adapter button. | `metaLoadPubMedPreviewButton` | `connected` | /var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch4_qv6fw_3g/meta_pubmed_ui_project/ui_runtime/meta_pubmed_preview_adapter.json | pubmed_preview_adapter_verified |
| META-PUBMED-UI-IMPORT-SELECTED | Import & Deduplication | import reviewer-selected PubMed candidates to literature library | UIShell Meta mature Import & Deduplication page with scoped adapter button. | `metaImportSelectedPubMedCandidatesButton` | `connected` | /var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch4_qv6fw_3g/meta_pubmed_ui_project/ui_runtime/meta_pubmed_handoff_adapter.json | pubmed_handoff_adapter_verified |
| META-PUBMED-SERVICE-COUNT-PREVIEW | Search Strategy | PubMed count preview | current Integration service; old protocol page capability source where applicable | `PubMedSearchService.preview_pubmed_count` | `connected` | PubMedCountPreview | success=True; result_count=3; errors=() |
| META-PUBMED-SERVICE-EXECUTION | Search Strategy | PubMed search execution | current Integration service; old protocol page capability source where applicable | `PubMedSearchService.search_pubmed` | `connected` | PubMedSearchExecution | success=True; result_count=3; returned_count=3; pmids=['111', '222', '333'] |
| META-PUBMED-ARTIFACTS-EXECUTION-AND-PREVIEW | Search Strategy | search execution report and candidate preview | current Integration service; old protocol page capability source where applicable | `write_pubmed_search_execution_artifacts` | `connected` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch4_qv6fw_3g/meta_pubmed_service_project/protocol/search_execution_report.json; /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch4_qv6fw_3g/meta_pubmed_service_project/protocol/pubmed_candidates/pubmedprev-b9cfe238efe7_candidates_preview.json | execution_report_and_candidate_preview_verified |
| META-PUBMED-HANDOFF-SELECTION | Import & Deduplication | reviewer candidate selection | current Integration service; old protocol page capability source where applicable | `PubMedCandidatesHandoffService.select_candidates` | `connected` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch4_qv6fw_3g/meta_pubmed_service_project/protocol/pubmed_candidates/pubmedprev-b9cfe238efe7_candidate_selection.json | success=True; selected=2; rejected=1; pending=0 |
| META-PUBMED-HANDOFF-IMPORT | Import & Deduplication | selected PubMed candidates imported to literature library | current Integration service; old protocol page capability source where applicable | `PubMedCandidatesHandoffService.import_selected_candidates` | `connected` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch4_qv6fw_3g/meta_pubmed_service_project/literature/literature_records.json | success=True; imported=2; message=Imported 2 selected PubMed candidates into literature library; screening not started. |
| META-PUBMED-LITERATURE-LIBRARY-INDEX | Import & Deduplication | literature library read path | current Integration service; old protocol page capability source where applicable | `literature_library_state_from_project` | `connected` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch4_qv6fw_3g/meta_pubmed_service_project/literature/literature_records.json | total_records=2; sources=['PubMed', 'PubMed'] |
| META-PUBMED-DEDUP-PREP | Import & Deduplication | deduplication preparation queue | current Integration service; old protocol page capability source where applicable | `PubMedCandidatesHandoffService._write_dedup_preparation` | `connected` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch4_qv6fw_3g/meta_pubmed_service_project/deduplication/pubmed_candidate_duplicate_groups.json | dedup_queue=/private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch4_qv6fw_3g/meta_pubmed_service_project/deduplication/pubmed_candidate_duplicate_groups.json; auto_merged=False |
| META-PUBMED-NO-AUTO-SCREENING-OR-PRISMA | Screening / Report | boundary: no automatic screening or PRISMA advancement | current Integration service; old protocol page capability source where applicable | `PubMedCandidatesHandoffService.import_selected_candidates` | `connected` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch4_qv6fw_3g/meta_pubmed_service_project/audit/pubmedbatch-6c294cfa79df_pubmed_handoff_audit.json | screening_dir_exists=False; records_screened=0; studies_included=0 |

## Next Adapter Work

- Add a visually scoped PubMed execution adapter action to the mature Search Strategy page only after confirming the UIShell baseline placement.
- Add reviewer candidate-selection controls to the mature Import & Deduplication page before enabling PubMed handoff from the page itself.
- Keep PubMed candidate import, screening queue creation, and PRISMA count advancement separated by explicit reviewer gates.
