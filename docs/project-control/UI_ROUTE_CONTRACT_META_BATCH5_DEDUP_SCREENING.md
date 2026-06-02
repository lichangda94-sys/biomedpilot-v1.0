# UI Route Contract Meta Batch 5: Dedup to Screening

- Created: `2026-06-02T02:08:43.649889+00:00`
- Branch: `integration/release-bio-c1-ui-shell`
- HEAD: `8e84d36515afb87f3cc66eaeb6d005ae0a85f59a`
- Scope: Meta mature UIShell Import & Deduplication adapter chain: literature library -> DedupReviewV2 -> deduplicated set -> TitleAbstractScreeningV2 queue.

## Summary

- Rows: 6
- Connected: 3
- Disabled with reason: 3
- UI gaps recorded: 0
- Broken: 0

## Source Matrix

- UI baseline: UIShell high-fidelity Meta target IA in app/meta_analysis/workspace.py; mature page retained.
- Policy: Old duplicate_review_page/screening_page remain backend capability references only; mature UIShell page is not replaced.

## Screenshots

### import_dedup_dedup_adapter

![import_dedup_dedup_adapter](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_meta_batch5_dedup_screening/01_import_dedup_dedup_adapter.png)

### import_dedup_after_build_queue

![import_dedup_after_build_queue](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_meta_batch5_dedup_screening/02_import_dedup_after_build_queue.png)

### import_dedup_after_screening_queue

![import_dedup_after_screening_queue](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_meta_batch5_dedup_screening/03_import_dedup_after_screening_queue.png)

### screening_page_after_queue

![screening_page_after_queue](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_meta_batch5_dedup_screening/04_screening_page_after_queue.png)

## UI Page -> Backend Capability -> Branch Source -> Test

| Contract | UI Page | Backend Capability | Source | Object | Status | Expected Artifact | Observed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| META-DEDUP-UI-AUTO-MERGE-DISABLED | Import & Deduplication | auto merge remains disabled | UIShell high-fidelity Meta page retained; current Integration v2 service adapter. | `metaAutoMergeDisabledButton` | `disabled` | disabledReason | disabled_with_reason |
| META-DEDUP-UI-AUTO-DELETE-DISABLED | Import & Deduplication | auto delete remains disabled | UIShell high-fidelity Meta page retained; current Integration v2 service adapter. | `metaAutoDeleteDisabledButton` | `disabled` | disabledReason | disabled_with_reason |
| META-DEDUP-UI-DIRECT-SEND-DISABLED | Import & Deduplication | direct send without adapter remains disabled | UIShell high-fidelity Meta page retained; current Integration v2 service adapter. | `metaSendToScreeningDisabledButton` | `disabled` | disabledReason | disabled_with_reason |
| META-DEDUP-UI-BUILD-QUEUE | Import & Deduplication | build duplicate review v2 queue | UIShell high-fidelity Meta page retained; current Integration v2 service adapter. | `metaBuildDedupReviewQueueButton` | `connected` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch5_imq5yu1_/Meta_Batch_5_Dedup_Screening/ui_runtime/meta_dedup_review_queue_adapter.json | DedupReviewV2Service.build_review_queue; artifact=meta_dedup_review_queue_adapter.json; payload={"group_count": 1, "service": "DedupReviewV2Service.build_review_queue", "success": true} |
| META-DEDUP-UI-GENERATE-DEDUPLICATED-SET | Import & Deduplication | generate deduplicated literature v2 set | UIShell high-fidelity Meta page retained; current Integration v2 service adapter. | `metaGenerateDeduplicatedSetButton` | `connected` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch5_imq5yu1_/Meta_Batch_5_Dedup_Screening/ui_runtime/meta_deduplicated_set_adapter.json | DedupReviewV2Service.generate_deduplicated_set; artifact=meta_deduplicated_set_adapter.json; payload={"active_record_count": 3, "blocker": "unresolved_duplicate_groups_require_reviewer_decision", "service": "DedupReviewV2Service.generate_deduplicated_set"} |
| META-DEDUP-UI-BUILD-SCREENING-QUEUE | Import & Deduplication | build title/abstract screening v2 queue from deduplicated set | UIShell high-fidelity Meta page retained; current Integration v2 service adapter. | `metaBuildScreeningQueueFromDedupButton` | `connected` | /private/var/folders/15/q7k4g18j2d5fx429w97f2b5c0000gn/T/biomedpilot_meta_batch5_imq5yu1_/Meta_Batch_5_Dedup_Screening/ui_runtime/meta_dedup_to_screening_queue_adapter.json | TitleAbstractScreeningV2Service.build_queue; artifact=meta_dedup_to_screening_queue_adapter.json; payload={"record_count": 3, "service": "TitleAbstractScreeningV2Service.build_queue", "source_type": "deduplicated_literature_v2", "success": true, "warnings": ["dupv2-lit-b5-a-lit-b5-b"]} |

## Boundary

- Auto merge remains disabled.
- Auto delete remains disabled.
- Screening queue creation is explicit and reviewer-gated; queue records remain `not_screened`.
- Unresolved duplicate groups are reported as warnings/blockers and are not hidden.
