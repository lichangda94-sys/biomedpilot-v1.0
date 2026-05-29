# Branch to Current UI Coverage Matrix

Date: 2026-05-29

## Scope

This matrix maps historical branch/legacy functionality to the current UI pages and buttons. It does not mark branch-only features as available. Current UI remains the only mainline.

## Bioinformatics UI Coverage

| Current UI area | Current button / action | Current implementation evidence | Branch / legacy related material | Coverage verdict | Migration note |
| --- | --- | --- | --- | --- | --- |
| Data Source | Generate GSE plan, Search GSE dataset, Register local paths | Current `workflow_pages.py`, data source/search services | `codex/bio-search-ui-main`, `codex/bio-geo-real-download-test`, Bio legacy `geo_tool` | Covered current-side; branch material mostly wording/profile refinements | Reuse current; do not call legacy GEO tool |
| TCGA/GTEx cards | Download/build expression/clinical | Current `data_sources/**`, `tcga/**`, `standard_assets/**` | Bio legacy `tcga_gtex/**` | Current has separate services; legacy is reference | Rewrite any missing facade logic |
| Recognition | Run recognition | Current `project_recognition.py`, recognition reports | `dev/release-internal-test`, `codex/bio-geo-real-download-test` | Covered current-side | Adapter only for branch improvements |
| Standardized Assets | Generate assets, confirm candidates | Current `project_standardization.py`, standardized asset confirmation | `stable/mainline`, `dev/release-internal-test` | Covered current-side | Preserve B8 resolver boundary |
| Analysis Center DEG | Confirm parameters, dependency gates, run formal DEG | Current `analysis_ui/**`, `deg_engine/**` | `stable/mainline`, `dev/release-internal-test`, `codex/releasebuild-formal-deg-carryover` | Covered current-side for controlled DEG; R packaging/production gates partly branch-rich | Adapter candidate for missing R/runtime polish |
| Results Browser DEG | Review/export table, generate plot, report package | Current result/review/plot/report modules | `dev/release-internal-test` real SVG/report renderer candidates | Covered current-side for controlled DEG | Current proof should remain source of truth |
| Simple DEG page | Run DEG preflight | Current `pages/differential_expression_page.py` | `codex/stage-3.6-deg-preflight` | Preflight only | Do not treat as formal DEG |
| Enrichment page / Analysis Center | ORA/GSEA preflight and controlled gates | Current flat `enrichment_*` modules and tests | `codex/mainline-survival-clinical-carryover`, `dev/release-internal-test` package layout | Partial current coverage; branch has structured package candidates | Adapter/rewrite only |
| Correlation page | Run correlation preflight/runner | Current correlation services/tests | No high-value branch found | Partial/current | Keep separate from formal clinical claims |
| Survival/Clinical | KM/log-rank, Cox rows/actions | Current `survival_clinical/**`, `plots/survival.py`, `plots/cox.py` | `codex/mainline-survival-clinical-carryover`, risk score branch | Controlled current coverage | Keep report-ready/clinical conclusions disabled |
| Risk score / nomogram | No fully proven current production UI | Current/branch risk artifacts not audited in this phase | `codex/releasebuild-formal-deg-carryover` | Not current production coverage | Rewrite with strict clinical boundary |
| Full integrated report/renderers | Report/export controls | Current reports plus branch renderer policies | `dev/release-internal-test` renderer runtime policy | Partial | Adapter candidate, not direct copy |

## Meta Analysis UI Coverage

| Current UI area | Current button / action | Current implementation evidence | Branch / legacy related material | Coverage verdict | Migration note |
| --- | --- | --- | --- | --- | --- |
| Protocol/Search | PICO/PECO draft, confirm protocol, search strategy, PubMed search | Current `protocol_page.py`, search services/tests | `codex/meta-search-ui-main`, `codex/bio-ui-download-integration` | Covered current-side | Current services supersede old search branch |
| Literature Import | Import local exports, diagnostics, warning table | Current literature pages/services/tests | Meta legacy `literature/**` | Covered current-side | Legacy parsers only as reference |
| Duplicate Review | Generate duplicate candidates, decisions, deduplicated library | Current duplicate pages/services/tests | Meta legacy literature dedup | Covered current-side | Current models should remain canonical |
| Screening / Fulltext | Screening queues, fulltext eligibility, attachments | Current pages/services/tests | `dev/meta-analysis` OCR/fulltext branch | Covered for non-OCR workflow; OCR not current-proven | OCR requires future adapter |
| Extraction | Generate pool, save records, export CSV, validation | Current extraction pages/services/tests | Meta legacy extraction rules | Covered current-side | Legacy rules reference only |
| Quality | Quality assessment/table/export | Current quality services/tests | Meta legacy bias/reporting | Covered current-side | Bias legacy not direct migration |
| Analysis Plan | Generate/confirm analysis plan | Current `analysis_plan_service.py`, UI handlers | Current branch and old Meta branches | Covered current-side | Required before v2 stats |
| Statistics v2 | Run statistics analysis | Current `MetaStatisticsEngineService` and tests | `codex/bio-ui-download-integration` history | Covered current-side | Current v2 is canonical |
| Result contract artifacts | Discover canonical contract/list | Current `MetaResultContractAdapter` and UI state | No legacy equivalent | Covered by Phase 3, not full L3 | Stop before Phase 4 |
| Older forest/table path | Generate forest plot, export result table from `analysis_results.json` | Current `FigureResultService` tests | Legacy report/analysis paths | Current but split contract | Adapter bridge required for v2 |
| Reporting | Formal Markdown, HTML/Word testing report, supplementary, figure/repro package | Current reporting services/tests | Meta legacy reporting and package scripts | Current but testing-level | Must stay labeled and tied to canonical result before L3 |
| Workflow dashboard | Refresh status across workflow steps | Current workflow dashboard page | `codex/meta-workflow-ui` | Covered current-side | Do not replace current UI |
| AI suggestions | Candidate-only AI suggestions | Current AI suggestions page | AI gateway branches | Partial; not analysis result | Out of current migration scope |

## Coverage Summary

| Area | Current coverage | Branch value | Migration action |
| --- | --- | --- | --- |
| Bio DEG | Strong current controlled coverage | R/runtime/report polish candidates | Reuse current; adapter for missing R gates |
| Bio ORA/GSEA | Current MVP exists; branch has package restructuring | Resource registry and production hardening candidates | Adapter/rewrite |
| Bio survival/Cox/risk | Controlled current survival/Cox; risk branch evidence only | Clinical/risk artifacts | Strict rewrite/adapt with clinical boundary |
| Meta statistics/table/plot/report | Current services exist; Phase 3 unifies contract bridge | Legacy workbench/reporting mostly superseded | Reuse current bridge; Phase 4 proof pending |
| Meta OCR/fulltext | Current fulltext services, branch OCR history | OCR worker/package candidate | Future adapter only |
| Legacy standalone UI | Historical only | UI inspiration | Deprecated as runtime |

