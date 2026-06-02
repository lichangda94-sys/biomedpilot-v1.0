# UI Route Contract Meta Batch 6: Screening Decisions

- Created: `2026-06-02T02:25:30.185214+00:00`
- Branch: `integration/release-bio-c1-ui-shell`
- HEAD: `d2d2f8ebe99f3597ef7c3796a0de0820329a10b7`
- Scope: Meta mature UIShell Screening page: decision selection, reviewer save, compatible screening decisions, and next-step navigation.

## Summary

- Rows: 7
- Connected: 7
- Disabled with reason: 0
- UI gaps recorded: 0
- Broken: 0

## Source Matrix

- UI baseline: UIShell high-fidelity Meta target IA Screening Workspace in app/meta_analysis/workspace.py.
- Policy: AI suggestions remain advisory only; reviewer save is explicit; no automatic screening or report-ready advancement.

## Screenshots

### screening_decision_workspace

![screening_decision_workspace](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_meta_batch6_screening_decisions/01_screening_decision_workspace.png)

### screening_after_decision_save

![screening_after_decision_save](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_meta_batch6_screening_decisions/02_screening_after_decision_save.png)

### fulltext_after_next_navigation

![fulltext_after_next_navigation](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_meta_batch6_screening_decisions/03_fulltext_after_next_navigation.png)

## UI Page -> Backend Capability -> Branch Source -> Test

| Contract | UI Page | Backend Capability | Source | Object | Status | Expected Artifact | Observed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| META-SCREENING-DECISION-SELECT-INCLUDE_DRAFT | Screening | reviewer decision selection state | UIShell high-fidelity Meta Screening page retained; current Integration v2 service adapter. | `metaScreeningDecisionDraftButton` | `connected` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch6_mf58_2mq/Meta_Batch_6_Screening_Decisions/ui_runtime/meta_screening_decision_selection_adapter.json | selection_payload={"auto_decided": false, "mapped_decision": "include", "selected_decision_id": "include_draft"} |
| META-SCREENING-DECISION-SELECT-EXCLUDE_DRAFT | Screening | reviewer decision selection state | UIShell high-fidelity Meta Screening page retained; current Integration v2 service adapter. | `metaScreeningDecisionDraftButton` | `connected` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch6_mf58_2mq/Meta_Batch_6_Screening_Decisions/ui_runtime/meta_screening_decision_selection_adapter.json | selection_payload={"auto_decided": false, "mapped_decision": "exclude", "selected_decision_id": "exclude_draft"} |
| META-SCREENING-DECISION-SELECT-UNCERTAIN | Screening | reviewer decision selection state | UIShell high-fidelity Meta Screening page retained; current Integration v2 service adapter. | `metaScreeningDecisionDraftButton` | `connected` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch6_mf58_2mq/Meta_Batch_6_Screening_Decisions/ui_runtime/meta_screening_decision_selection_adapter.json | selection_payload={"auto_decided": false, "mapped_decision": "uncertain", "selected_decision_id": "uncertain"} |
| META-SCREENING-DECISION-SELECT-NEED_FULL_TEXT | Screening | reviewer decision selection state | UIShell high-fidelity Meta Screening page retained; current Integration v2 service adapter. | `metaScreeningDecisionDraftButton` | `connected` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch6_mf58_2mq/Meta_Batch_6_Screening_Decisions/ui_runtime/meta_screening_decision_selection_adapter.json | selection_payload={"auto_decided": false, "mapped_decision": "needs_review", "selected_decision_id": "need_full_text"} |
| META-SCREENING-SAVE-DRAFT-DECISION | Screening | save reviewer title/abstract decision | UIShell high-fidelity Meta Screening page retained; current Integration v2 service adapter. | `metaSaveDraftScreeningDecisionButton` | `connected` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch6_mf58_2mq/Meta_Batch_6_Screening_Decisions/ui_runtime/meta_screening_decision_adapter.json | save_payload={"advance_requested": false, "auto_decided": false, "decision": "include", "decision_counts": {"exclude": 0, "include": 1, "needs_review": 0, "not_screened": 0, "total": 1, "uncertain": 0}, "record_id": "lit-pubmed-600001", "selected_decision_id": "include_draft", "service": "TitleAbstractScreeningV2Service.save_decision", "success": true} |
| META-SCREENING-SAVE-NEXT-DECISION | Screening | save reviewer decision and move to next unscreened record | UIShell high-fidelity Meta Screening page retained; current Integration v2 service adapter. | `metaScreeningSaveNextButton` | `connected` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch6_mf58_2mq/Meta_Batch_6_Screening_Decisions/ui_runtime/meta_screening_decision_adapter.json | save_next_payload={"advance_requested": true, "auto_decided": false, "decision": "exclude", "decision_counts": {"exclude": 1, "include": 1, "needs_review": 0, "not_screened": 0, "total": 2, "uncertain": 0}, "record_id": "lit-pubmed-600002", "selected_decision_id": "exclude_draft", "service": "TitleAbstractScreeningV2Service.save_decision", "success": true} |
| META-SCREENING-NAV-NEXT-FULLTEXT | Screening | navigate to mature Full-text & Extraction page | UIShell high-fidelity Meta Screening page retained; current Integration v2 service adapter. | `metaScreeningNextFulltextButton` | `connected` | current_target_page_key=fulltext_extraction | current_target_page_key=fulltext_extraction |

## Boundary

- Decision selection writes UI state only; it does not write final screening decisions.
- Save actions call `TitleAbstractScreeningV2Service.save_decision` with reviewer actor.
- Exclude uses a structured exclusion reason; AI suggestion remains advisory only.
- Navigation to Full-text is route-only; extraction and report gates remain separate batches.
