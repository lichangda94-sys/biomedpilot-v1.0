# Branch to Current UI Coverage Matrix

Date: 2026-06-04

## Scope

This matrix maps historical branch/legacy functionality to the current UI pages and buttons. It does not mark branch-only features as available. Current UI remains the only mainline.

Current audit baseline:

```text
branch: dev/bioinformatics
HEAD: b77805c242d4f1a47a4cca20fcf21fb3ac4c6e15
audit mode: Phase 2.5 read-only inventory refresh
```

Existing uncommitted analysis worker/univariate lite fixture changes are excluded from current UI coverage claims.

## Bioinformatics UI Coverage

| Current UI area | Current button / action | Current implementation evidence | Branch / legacy related material | Coverage verdict | Migration note |
| --- | --- | --- | --- | --- | --- |
| Project Home | Project state and workflow entry | Current `project_home.py`, `workflow_pages.py`, UI tests | UI shell branches have visual/layout material | Covered current-side | Do not replace current UI shell in Phase 2.5 |
| Data Source | Generate GSE plan, Search GSE dataset, Register local paths, TCGA/GTEx cards | Current data source/search/download services | `codex/bio-search-ui-main*`, `codex/bio-geo-real-download-test`, legacy `geo_tool` | Covered current-side; branch material mostly wording/profile refinements | Reuse current; do not call legacy GEO tool |
| TCGA/GTEx assets | Download/build expression/clinical, standardized package creation | Current `data_sources/**`, `tcga/**`, `standard_assets/**` | Legacy `tcga_gtex/**` | Current has separate services; legacy is reference | Rewrite any missing facade logic |
| Recognition | Run recognition | Current `project_recognition.py`, recognition reports | `dev/release-internal-test`, old GEO branches | Covered current-side | Adapter only for branch improvements |
| Standardized Assets | Generate assets, confirm candidates | Current `project_standardization.py`, standardized asset confirmation | `stable/mainline`, `dev/release-internal-test` | Covered current-side | Preserve resolver boundary |
| Analysis Center DEG | Confirm parameters, dependency gates, run formal DEG, show disabled reasons | Current `analysis_ui/**`, `deg_engine/**` | `stable/mainline`, `dev/release-internal-test`, `codex/releasebuild-formal-deg-carryover` | Covered current-side for controlled DEG; R packaging/production polish may be branch-rich | Adapter candidate only |
| Multi-factor DEG controls | Show design QA, contrast, method, dependency, confirmation | Current `deg_engine/multifactor_*`, tests | ReleaseBuild branches with R backend details | Partial controlled coverage | Require focused proof before marking production-like |
| Results Browser DEG | Review/export table, generate plot, report/audit package | Current result/review/plot/report modules | `dev/release-internal-test` real SVG/report renderer candidates | Covered for controlled DEG | Current proof remains source of truth |
| Simple DEG page | Run DEG preflight | Current `pages/differential_expression_page.py` | `codex/stage-3.6-deg-preflight` | Preflight only | Do not treat as formal DEG |
| Enrichment page / Analysis Center | ORA/GSEA gates, resource status, controlled execution/review | Current flat `enrichment_*` modules and tests | `dev/release-internal-test` `enrichment/**`, `gsea/**` package layout | Current MVP exists; structured branch layout is candidate | Adapter/rewrite only |
| Correlation page | Run correlation preflight/runner | Current correlation services/tests | No high-value branch found | Partial/current | Keep separate from clinical claims |
| Survival/Clinical | KM/log-rank, Cox rows/actions, disabled reasons | Current `survival_clinical/**`, `plots/survival.py`, `plots/cox.py` | `codex/mainline-survival-clinical-carryover`, ReleaseBuild branch | Controlled current coverage | Keep clinical conclusion/report-ready restrictions |
| Risk score / nomogram | Risk rows if present; no proven production UI completion | Current/branch risk artifacts not rerun in this audit | `codex/releasebuild-formal-deg-carryover`, `dev/release-internal-test` | Not current production coverage | Rewrite/adapt with strict clinical boundary |
| Plot actions | Formal result-driven SVG/spec artifacts | Current `plots/**` | Branch `plots/real_svg.py`, `plots/ora.py`, `plots/gsea.py`, `plots/survival_real.py` | Partial current coverage | Branch split can inform adapter, not direct copy |
| Report/export controls | Section package, report-ready gates, renderer status | Current `reports/**` | Branch `reports/integrated.py`, renderer capability/runtime policy | Partial | Adapter candidate, no placeholder report promotion |
| Analysis runtime bridge | Mock/lite standard package task bridge and package catalog discovery | Current `app/analysis_runtime/**`, `analysis/**`; committed lite enrichment/survival scaffold | No old equivalent | Current scaffold only | Do not show as full R analysis execution; ordinary user UI completion not proven |

## Meta Analysis UI Coverage

| Current UI area | Current button / action | Current implementation evidence | Branch / legacy related material | Coverage verdict | Migration note |
| --- | --- | --- | --- | --- | --- |
| Protocol/Search | PICO/PECO draft, confirm protocol, search strategy, PubMed search | Current `protocol_page.py`, search services/tests | `codex/meta-search-ui-main`, old search branches | Covered current-side | Current services supersede old search branch |
| Literature Import | Import local exports, diagnostics, warning table | Current literature pages/services/tests | Meta legacy `literature/**` | Covered current-side | Legacy parsers only as reference |
| Duplicate Review | Generate duplicate candidates, decisions, deduplicated library | Current duplicate pages/services/tests | Meta legacy literature dedup | Covered current-side | Current models stay canonical |
| Screening / Fulltext | Screening queues, fulltext eligibility, attachments | Current pages/services/tests | `dev/meta-analysis` OCR/fulltext branch | Covered for non-OCR workflow; OCR not current-proven | OCR requires future adapter |
| Extraction | Generate pool, save records, export CSV, validation | Current extraction pages/services/tests | Meta legacy extraction rules | Covered current-side | Legacy rules reference only |
| Quality | Quality assessment/table/export | Current quality services/tests | Meta legacy bias/reporting | Covered current-side | Bias legacy not direct migration |
| Analysis Plan | Generate/confirm analysis plan | Current `analysis_plan_service.py`, UI handlers | Current branch and old Meta branches | Covered current-side | Required before v2 stats |
| Statistics v2 | Run statistics analysis | Current `MetaStatisticsEngineService` and tests | Earlier Meta branches | Covered current-side | Current v2 is canonical |
| Result contract artifacts | Discover canonical contract/list | Current `MetaResultContractAdapter` and UI state | No legacy equivalent | Covered by current Phase 3/4 proof | Do not claim full Meta production |
| Older forest/table path | Generate forest plot, export result table from `analysis_results.json` | Current `FigureResultService` tests | Legacy report/analysis paths | Current but split contract | Keep bridge explicit |
| Reporting | Formal Markdown, HTML/Word testing report, supplementary, figure/repro package | Current reporting services/tests | Meta legacy reporting and package scripts | Current but testing-level | Must stay labeled and tied to canonical result before stronger claims |
| Workflow dashboard | Refresh status across workflow steps | Current workflow dashboard page | `codex/meta-workflow-ui`, UI shell branches | Covered current-side | Do not replace current UI |
| AI suggestions | Candidate-only AI suggestions | Current AI suggestions page | AI gateway branches | Partial; not analysis result | Out of current migration scope |
| OCR fulltext | No current L3 proof | Branch `dev/meta-analysis` OCR workers/tests | Branch-only evidence | Not current coverage | Future adapter only after dependency/package audit |

## Current UI Mapping Rules For Candidates

| Candidate evidence | UI coverage rule |
| --- | --- |
| Current non-legacy code with current tests and current UI handler | May be marked `covered current-side`, with exact scope only |
| Current non-legacy code without ordinary user UI path | Mark as `current scaffold` or `backend candidate`, not UI-complete |
| Branch-only files or branch-only tests | Mark as `branch material`, not current coverage |
| Legacy folder code or legacy tests | Mark as `legacy material`; no current UI coverage |
| Mock/lite/testing-level output | May support developer preview only; cannot satisfy formal analysis or production coverage |

## Coverage Summary

| Area | Current coverage | Branch value | Migration action |
| --- | --- | --- | --- |
| Bio DEG | Strong controlled current coverage with hardening gates | R runtime/report/renderer polish candidates | Reuse current; adapter for selected missing pieces |
| Bio ORA/GSEA | Current MVP exists; branch has package restructuring | Resource registry, structured module layout, production hardening candidates | Adapter/rewrite |
| Bio survival/Cox/risk | Controlled current survival/Cox; risk branch/current evidence mixed | Clinical/risk artifacts | Strict rewrite/adapt with clinical boundary |
| Bio plots/reports | Current section packages and SVG artifacts for supported modules | Broader renderer split and integrated report policy | Adapter only, no placeholder promotion |
| Meta statistics/table/plot/report | Current services and contract bridge exist | Legacy workbench/reporting mostly superseded | Reuse current bridge; OCR/fulltext future adapter |
| UI shell/design | Current UI is active; UI shell branches have visual assets | Design and component material | UI owner selection required before any migration |
| Legacy standalone UI | Historical only | UI inspiration | Deprecated as runtime |
