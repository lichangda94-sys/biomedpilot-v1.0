# UI Route Contract Phase 1 Rollup

- created_at: `2026-06-02T14:25:55.677613+00:00`
- branch: `integration/release-bio-c1-ui-shell`
- head: `f650bfde88b33af780c547bb1b98f41341d05232`
- scope: Shell, Bioinformatics, Meta Analysis, and LabTools route-contract evidence freshness.

## Summary

- batch_count: `24`
- row_count: `477`
- connected: `374`
- disabled_with_reason: `103`
- broken: `0`

## Freshness Classification

| Freshness | Batch count | Meaning |
| --- | ---: | --- |
| `current-head-proof` | 1 | Evidence was generated at the current HEAD. |
| `prior-proof-docs-only-head-drift` | 23 | Evidence HEAD differs, but recorded app/test implementation paths did not change since that evidence. |

## Module Totals

| Module | Batches | Rows | Connected | Disabled | Broken | Current | Docs-only drift | Stale code | Blocked |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Bioinformatics | 12 | 219 | 158 | 61 | 0 | 0 | 12 | 0 | 0 |
| Centers | 1 | 28 | 23 | 5 | 0 | 1 | 0 | 0 | 0 |
| LabTools | 4 | 159 | 144 | 15 | 0 | 0 | 4 | 0 | 0 |
| Meta Analysis | 7 | 71 | 49 | 22 | 0 | 0 | 7 | 0 | 0 |
| Shell | 1 | 28 | 23 | 5 | 0 | 1 | 0 | 0 | 0 |

## Batch Details

| Contract file | Modules | Evidence head | Freshness | Rows | Connected | Disabled | Broken | Changed code paths |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH1.json` | Bioinformatics | `13128f797492` | `prior-proof-docs-only-head-drift` | 27 | 22 | 5 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH10_GEO_ONLINE_RETRIEVAL.json` | Bioinformatics | `dc55902228f5` | `prior-proof-docs-only-head-drift` | 18 | 18 | 0 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH11_TCGA_GTEX_ADAPTERS.json` | Bioinformatics | `4a0577982b6c` | `prior-proof-docs-only-head-drift` | 10 | 6 | 4 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH12_TCGA_GTEX_LIGHT_VALIDATION.json` | Bioinformatics | `4a0577982b6c` | `prior-proof-docs-only-head-drift` | 10 | 10 | 0 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH13_TCGA_GTEX_DATA_CHECK.json` | Bioinformatics | `4a0577982b6c` | `prior-proof-docs-only-head-drift` | 5 | 5 | 0 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH14_FORMAL_ORA.json` | Bioinformatics | `4a0577982b6c` | `prior-proof-docs-only-head-drift` | 7 | 4 | 3 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH4_FORMAL_DEG.json` | Bioinformatics | `4a0577982b6c` | `prior-proof-docs-only-head-drift` | 8 | 8 | 0 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH5_ENRICHMENT.json` | Bioinformatics | `4a0577982b6c` | `prior-proof-docs-only-head-drift` | 9 | 4 | 5 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH6_SURVIVAL.json` | Bioinformatics | `4a0577982b6c` | `prior-proof-docs-only-head-drift` | 9 | 4 | 5 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH7_REPORT_EXPORT.json` | Bioinformatics | `4a0577982b6c` | `prior-proof-docs-only-head-drift` | 13 | 13 | 0 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH8_VISIBLE_BUTTONS.json` | Bioinformatics | `4a0577982b6c` | `prior-proof-docs-only-head-drift` | 94 | 55 | 39 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH9_DATA_PREP_ADAPTERS.json` | Bioinformatics | `4a0577982b6c` | `prior-proof-docs-only-head-drift` | 9 | 9 | 0 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_LABTOOLS_BATCH2.json` | LabTools | `13128f797492` | `prior-proof-docs-only-head-drift` | 21 | 18 | 3 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_LABTOOLS_BATCH3_CELL_EXPERIMENTS.json` | LabTools | `fa4871dee125` | `prior-proof-docs-only-head-drift` | 44 | 38 | 6 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_LABTOOLS_BATCH4_PROTEIN_WB.json` | LabTools | `13128f797492` | `prior-proof-docs-only-head-drift` | 83 | 82 | 1 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_LABTOOLS_BATCH5_SECONDARY_REMAINDER.json` | LabTools | `13128f797492` | `prior-proof-docs-only-head-drift` | 11 | 6 | 5 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_META_BATCH3.json` | Meta Analysis | `4300b4ab1f91` | `prior-proof-docs-only-head-drift` | 33 | 18 | 15 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_META_BATCH4_PUBMED_HANDOFF.json` | Meta Analysis | `4300b4ab1f91` | `prior-proof-docs-only-head-drift` | 13 | 12 | 1 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_META_BATCH5_DEDUP_SCREENING.json` | Meta Analysis | `4300b4ab1f91` | `prior-proof-docs-only-head-drift` | 6 | 3 | 3 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_META_BATCH6_SCREENING_DECISIONS.json` | Meta Analysis | `4300b4ab1f91` | `prior-proof-docs-only-head-drift` | 7 | 7 | 0 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_META_BATCH7_FULLTEXT_EXTRACTION.json` | Meta Analysis | `4300b4ab1f91` | `prior-proof-docs-only-head-drift` | 6 | 4 | 2 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_META_BATCH8_QUALITY_ASSESSMENT.json` | Meta Analysis | `4300b4ab1f91` | `prior-proof-docs-only-head-drift` | 3 | 3 | 0 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_META_BATCH9_ANALYSIS_TASKS.json` | Meta Analysis | `4300b4ab1f91` | `prior-proof-docs-only-head-drift` | 3 | 2 | 1 | 0 | - |
| `docs/project-control/UI_ROUTE_CONTRACT_PHASE1_BATCH0.json` | Centers, Shell | `f650bfde88b3` | `current-head-proof` | 28 | 23 | 5 | 0 | - |

## Release Interpretation

- `current-head-proof` and `prior-proof-docs-only-head-drift` can support Phase 1 release planning if their screenshots and tests remain present.
- `stale-code-proof` must be rerun before the route is claimed as current release evidence.
- `blocked` is a release blocker until the broken rows are fixed or explicitly disabled with reason.
