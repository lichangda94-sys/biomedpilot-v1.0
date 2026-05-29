# Project Progress Dashboard

Date: 2026-05-29

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

This dashboard is based only on the source reports listed below. It does not treat branch-only, legacy-only, mock, placeholder, testing-level, developer-preview, service-only, or backend-only evidence as completed UI L3 unless a current UI L3 completion report exists.

## 1. Snapshot

| Date | Current mainline | Current HEAD | Dashboard source reports | Current project control status | Next global priority |
| --- | --- | --- | --- | --- | --- |
| 2026-05-29 | `dev/bioinformatics` | Worktree HEAD `7cd526ad8b2cdc0c3dccab3e95dc1a2b75747b40`; source reports record `dev/bioinformatics` through Phase 2.5/Project Control | All required source reports found: `PROJECT_CONTROL_NEXT_PHASE_PLAN.md`, `BRANCH_INVENTORY.md`, `LEGACY_FEATURE_CATALOG.md`, `MIGRATION_CANDIDATE_LEDGER.md`, `DEPRECATED_LEGACY_REGISTER.md`, `BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md`, `L3_CLOSURE_WORKLOG.md`, `BIOINFORMATICS_L3_COMPLETION_REPORT.md`, `META_RESULT_CONTRACT_UNIFICATION_REPORT.md` | Current UI is the only mainline; old branches and `legacy/**` are material libraries only; all future implementation starts from current mainline feature branches | Meta Phase 4 current UI L3 proof before old feature migration |

Current dashboard coverage count from `BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md`: 25 current UI areas/function-entry groups, consisting of 12 Bioinformatics areas and 13 Meta Analysis areas.

## 2. Overall Completion Summary

| Area | Current status | Evidence level | L3 status | Next action | Risk |
| --- | --- | --- | --- | --- | --- |
| Current UI mainline | Yes | Project control plan and coverage matrix identify current UI as sole mainline | Partial | Keep all future work on feature branches from `dev/bioinformatics` | Old branches can be mistaken for runtime truth |
| Branch audit | Yes | Phase 2.5 branch inventory, legacy catalog, migration ledger, coverage matrix | Yes for audit scope | Use branch material only through current contracts | Direct branch carry-over would overwrite current contracts |
| Bioinformatics controlled DEG | Yes | `BIOINFORMATICS_L3_COMPLETION_REPORT.md` proves current UI single-point controlled formal DEG | Yes | Preserve current path; then harden DEG production gates separately | Full Bioinformatics module is not complete |
| Meta result contract | Partial | Phase 3 proves service/contract bridge from v2 run to table, plot, testing-level report/export | No UI L3 | Prove current Meta UI Phase 4 path end to end | Service-only proof could be overstated as UI L3 |
| Meta UI L3 | No | Source reports explicitly stop before Phase 4 | No | Run current UI proof from confirmed plan to v2 run, canonical contract, table, forest plot, report/export | Must not use legacy workbench or service-only proof |
| Legacy migration | Deferred | Project control and legacy register quarantine old branches and `legacy/**` | No | Select one candidate only after current UI path and contract are named | Legacy/mock/placeholder backflow risk |
| Final UI productization | Deferred | Current reports show testing/developer-preview boundaries remain | No | Wait for stable L3 paths and current-contract-backed outputs | Productization before L3 closure would overclaim readiness |

## 3. Current UI Page-to-Backend Map

| Module | Current UI page/area | Button/action | Current backend/service/contract | Output artifact | L3 state | Branch/legacy material | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Bioinformatics | Data Source | Generate GSE plan; Search GSE dataset; Register local paths | `workflow_pages.py`, data source/search services | Search/download/registration metadata | Partial | `codex/bio-search-ui-main`, `codex/bio-geo-real-download-test`, legacy `geo_tool` as reference only | Preserve current services; do not call legacy GEO tool |
| Bioinformatics | TCGA/GTEx cards | Download/build expression/clinical | `data_sources/**`, `tcga/**`, `standard_assets/**` | Data-source assets | Partial | legacy `tcga_gtex/**` reference only | Rewrite missing facade gaps against current data-source contracts |
| Bioinformatics | Recognition | Run recognition | `project_recognition.py`, recognition reports | Recognition report | Partial | `dev/release-internal-test`, `codex/bio-geo-real-download-test` | Adapter only for branch improvements |
| Bioinformatics | Standardized Assets | Generate assets; confirm candidates | `project_standardization.py`, standardized asset confirmation | Standardized asset registry/confirmation | Partial | `stable/mainline`, `dev/release-internal-test` | Preserve B8 resolver boundary |
| Bioinformatics | Analysis Center DEG | Confirm parameters; dependency gates; run formal DEG | `analysis_ui/**`, `deg_engine/**`, formal runner/result index | Formal DEG TSV and run log | Yes for controlled formal DEG only | `stable/mainline`, `dev/release-internal-test`, `codex/releasebuild-formal-deg-carryover` | Keep proved path; adapt missing R/runtime gates later |
| Bioinformatics | Results Browser DEG | Review/export table; generate plot; report package | Result/review/export, `plots/formal_deg.py`, `reports/formal_deg.py` | Review CSV, real SVG plot, section report package | Yes for controlled formal DEG only | `dev/release-internal-test` renderer candidates | Preserve current proof; do not generalize without tests |
| Bioinformatics | Simple DEG page | Run DEG preflight | `pages/differential_expression_page.py` | Preflight output | Partial | `codex/stage-3.6-deg-preflight` superseded | Do not treat as formal DEG |
| Bioinformatics | Enrichment page / Analysis Center | ORA/GSEA preflight and controlled gates | Current flat `enrichment_*` modules | Enrichment result/plot/report candidates | Partial | `codex/mainline-survival-clinical-carryover`, `dev/release-internal-test` package layout | Prove current UI ORA/GSEA L3 separately |
| Bioinformatics | Correlation page | Run correlation preflight/runner | Current correlation services/tests | Correlation result candidates | Partial | No high-value branch found | Keep separate from clinical/report claims |
| Bioinformatics | Survival/Clinical | KM/log-rank; Cox actions | `survival_clinical/**`, `plots/survival.py`, `plots/cox.py` | Controlled survival/Cox artifacts | Partial | `codex/mainline-survival-clinical-carryover`, risk branch | Prove controlled UI loop; keep clinical conclusions disabled |
| Bioinformatics | Risk score / nomogram | Not fully proven current production UI | Current/branch risk artifacts not current-proven | Candidate risk/nomogram/DCA artifacts | Pending | `codex/releasebuild-formal-deg-carryover` | Rewrite later with strict clinical boundary |
| Bioinformatics | Full integrated report/renderers | Report/export controls | Current reports plus candidate renderer policies | Markdown/DOCX/PDF/export candidates | Partial | `dev/release-internal-test` renderer runtime policy | Back reports with current result contracts before L3 claim |
| Meta Analysis | Protocol/Search | PICO/PECO draft; confirm protocol; search strategy; PubMed search | `protocol_page.py`, search strategy and PubMed services | Protocol/search strategy artifacts; PubMed report when executed | Partial | `codex/meta-search-ui-main`, `codex/bio-ui-download-integration` | Preserve current services; keep non-executed drafts labeled |
| Meta Analysis | Literature Import | Import local exports; diagnostics; warning table | Literature import pages/services | Import diagnostics and warning exports | Partial | legacy `literature/**` reference only | Use current models; no legacy parser backflow without adapter |
| Meta Analysis | Duplicate Review | Generate duplicate candidates; decisions; deduplicated library | Duplicate review pages/services | Duplicate groups, decisions, deduplicated library | Partial | legacy literature dedup reference only | Keep current canonical models |
| Meta Analysis | Screening / Fulltext | Screening queues; fulltext eligibility; attachments | Screening/fulltext pages/services | Screening decisions and fulltext/attachment records | Partial | `dev/meta-analysis` OCR/fulltext history | Non-OCR current flow only; OCR future adapter |
| Meta Analysis | Extraction | Generate pool; save records; export CSV; validation | Extraction pages/services and schema registry | Extraction records, CSV, validation report | Partial | legacy extraction rules reference only | Keep current extraction schema canonical |
| Meta Analysis | Quality | Quality assessment/table/export | Quality services/tests | Quality assessment records/table/export | Partial | legacy bias/reporting reference only | Do not direct-migrate bias legacy |
| Meta Analysis | Analysis Plan | Generate/confirm analysis plan | `analysis_plan_service.py`, current UI handlers | Draft, confirmed plan, manifest | Partial | Current branch and old Meta branches | Required before v2 stats; prove in UI Phase 4 |
| Meta Analysis | Statistics v2 | Run statistics analysis | `MetaStatisticsEngineService`, confirmed plan contract | v2 run manifest and standardized result | Partial | `codex/bio-ui-download-integration` history | Current v2 is canonical; needs current UI L3 proof |
| Meta Analysis | Result contract artifacts | Discover canonical contract/list | `MetaResultContractAdapter`, `meta_statistics_engine_state_from_project()` | Canonical contract, CSV table, PNG forest plot, testing-level markdown export | Partial | No legacy equivalent | Phase 3 proof only; Phase 4 UI proof pending |
| Meta Analysis | Older forest/table path | Generate forest plot; export result table from `analysis_results.json` | `FigureResultService`, older result path | Real PNG/CSV from older split path | Partial | Legacy report/analysis paths | Bridge to v2 canonical result before L3 |
| Meta Analysis | Reporting | Formal Markdown; HTML/Word testing report; supplementary; figure/repro package | `formal_report_service.py`, `publication_export_service.py` | Testing-level reports/packages | Partial | legacy reporting/package scripts | Keep testing/developer-preview label; tie to canonical result |
| Meta Analysis | Workflow dashboard | Refresh workflow step status | `workflow_dashboard_page.py`, `workflow_integration_page.py` | Workflow step states | Partial | `codex/meta-workflow-ui` reference only | Do not replace current UI |
| Meta Analysis | AI suggestions | Candidate-only AI suggestions | AI suggestion page/services | Candidate suggestions | Pending | AI gateway branches | Out of current analysis L3 scope |

## 4. Bioinformatics Analysis Route Dashboard

| Route | Current UI entry | Backend/service | Input required | Parameter confirmation | Real run | Result table | Plot | Report/export | L3 status | Source branches/material | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Controlled formal DEG | Analysis Center DEG; Results Browser DEG | `formal_runner.py`, result registry, formal plot/report services | Standardized count matrix, sample metadata, group design, assets registry | Yes, current UI button `确认 formal DEG 参数` | Yes | Yes | Yes, real SVG | Yes, formal DEG section package | Yes | Current `dev/bioinformatics`; historical `stable/mainline` only as baseline | Preserve; do not broaden claim to full Bio module |
| Multi-factor DEG | Analysis Center multi-factor controls | `multifactor_gate.py`, `multifactor_schema.py`, `multifactor_confirmation.py`, `multifactor_r_runner.py` | Design QA/current result schema | Partial | Partial/current, not L3 rerun in audit | Partial | Partial | Pending | Partial | Current plus `dev/release-internal-test` | Run focused current UI proof |
| limma/DESeq2/edgeR R runtime adapters | Analysis Center DEG method controls | Current runner plus branch `r_*` adapter candidates | External R/Bioc detect-first state | Partial | Partial/branch evidence only | Result tables only | Separate | Pending | Partial | `dev/release-internal-test` and current | Adapt behind current contracts; no branch transplant |
| ORA enrichment | Enrichment page / Analysis Center | Current flat `enrichment_*`; branch package candidates | DEG/result input and gene sets | Partial | Not UI L3 proven | Partial | Candidate plot gates | Candidate report gates | Partial | `codex/mainline-survival-clinical-carryover`, `dev/release-internal-test` | Prove current UI ORA loop |
| GSEA preranked | Analysis Center GSEA rows | Current flat `enrichment_*`; branch `gsea/**` | Preranked gene list and resource/version gates | Partial | Not UI L3 proven | Partial | Candidate plot gates | Candidate report gates | Partial | `dev/release-internal-test` | Add resource gates and current UI proof |
| Enrichment resource registry | Analysis Center enrichment resources | Branch resource/dependency gates; current partial resources | Gene set resource/version/dependency state | Pending | Not current-proven | No | No | No | Pending | `dev/release-internal-test` | Introduce as current service contract |
| Correlation | Correlation page | Current correlation services/tests | Correlation-ready data | Partial | Partial | Partial | Pending | Pending | Partial | No high-value branch found | Define L3 route and proof criteria |
| KM/log-rank survival | Survival/Clinical | `survival_clinical/km_*`, `plots/survival.py` | Survival time/event data | Partial | Controlled current coverage, not UI L3 proved here | Partial | Plot support exists | Clinical report-ready disabled | Partial | Current plus `codex/mainline-survival-clinical-carryover` | Prove controlled UI loop; keep clinical claims disabled |
| Cox survival | Survival/Clinical | `survival_clinical/cox_*`, `plots/cox.py` | Survival variables/outcome gates | Partial | Controlled current coverage, not UI L3 proved here | Partial | Plot support exists | Clinical report-ready disabled | Partial | Current plus `codex/mainline-survival-clinical-carryover` | Prove controlled UI loop with strict clinical boundary |
| Risk score / nomogram / DCA | No proven current production UI | Branch risk/nomogram/calibration/DCA evidence only | Strong clinical variable/outcome gates | No | Not current-proven | Branch evidence only | Branch evidence only | Branch evidence only | No | `codex/releasebuild-formal-deg-carryover` | Rewrite later; no production/clinical claim |
| TCGA/GTEx facade/data-source gaps | TCGA/GTEx cards | Current `data_sources/**`, `tcga/**`, `standard_assets/**`; legacy facade reference | Data-source credentials/local files | Partial | Input workflow only | No analysis table | No | No | Partial | legacy `tcga_gtex/**` reference only | Rewrite gaps after current data-source audit |
| Integrated report/renderers | Report/export controls | Current report/export plus renderer policy candidates | Stable current result contracts | Partial | Not fully current-contract-backed | Partial | Partial | Partial/testing | Partial | `dev/release-internal-test` | Back each export by current result contracts |

## 5. Meta Analysis Route Dashboard

| Route | Current UI entry | Backend/service | Input required | Parameter/plan confirmation | Real run | Result table | Plot | Report/export | L3 status | Source branches/material | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Protocol/Search | Protocol/Search | `protocol_page.py`, search strategy services, PubMed service | PICO/PECO inputs | Confirm protocol/search strategy where applicable | PubMed can execute; other databases draft/manual | No analysis table | No | Search artifacts/reports | Partial | `codex/meta-search-ui-main` reference only | Keep draft/execution boundaries explicit |
| Literature import | Literature Import | Literature import services | RIS/NBIB/CSV/local exports | Import options | Import real local files | Warning/diagnostic tables | No | Import diagnostics/export | Partial | legacy `literature/**` reference only | Preserve current canonical models |
| Deduplication | Duplicate Review | Dedup review services | Imported literature records | Human decisions | Real dedup service path | Deduplicated library | No | Decision exports | Partial | legacy dedup reference only | Define L3 loop if needed |
| Screening | Screening pages | Screening services | Deduplicated records and criteria | Human decisions | Real screening workflow | Screening queues/tables | No | Screening exports | Partial | legacy screening reference only | Keep current decisions canonical |
| Fulltext/non-OCR | Screening / Fulltext | Fulltext eligibility/attachment services | Local fulltext/attachments | Human fulltext decisions | Non-OCR workflow current-side | Fulltext/attachment records | No | Missing fulltext reports | Partial | `dev/meta-analysis` only for OCR history | Keep non-OCR path current; no OCR migration |
| OCR/fulltext adapter | Fulltext pages not current-proven for OCR | No current-proven OCR adapter | OCR dependency/package chain | No | No | No | No | No | Pending | `dev/meta-analysis` OCR/fulltext history | Rewrite/adapt later after Meta UI L3 |
| Extraction | Extraction | Extraction form/storage/validation services | Screened studies/effect rows | Human save/validation | Real extraction services | Extraction CSV | No | Validation/export artifacts | Partial | legacy extraction rules reference only | Keep schema registry canonical |
| Quality assessment | Quality | Quality assessment services | Included studies/quality domains | Human assessment | Real service path | Quality table/export | No | Quality summary/export | Partial | legacy bias reference only | Do not direct-migrate legacy bias |
| Analysis plan | Analysis Plan | `AnalysisPlanService` | Confirmed protocol, extraction rows, quality summary | Yes, confirmed analysis plan | Does not run stats by itself | No | No | Plan manifest | Partial | Current branch and old Meta references | Required step for Phase 4 UI L3 |
| Statistics v2 | Statistics v2 | `MetaStatisticsEngineService` | Confirmed analysis plan | Yes | Yes, service proof; UI L3 not yet proved in source reports | Statistics result only | No direct plot | No direct report | Partial | Current plus `codex/bio-ui-download-integration` history | Prove current UI triggers v2 run |
| Canonical result contract artifacts | Result contract artifacts | `MetaResultContractAdapter` | v2 run/result | Source run selected by adapter | Service proof yes | CSV table | Real PNG forest plot | Testing-level markdown export | Partial | No legacy equivalent | Phase 4 current UI proof required |
| Forest plot/table export | Older forest/table path | `FigureResultService`, older result path | `analysis_results.json` split path | Dataset/result IDs | Yes in older current services | CSV | PNG | No canonical report | Partial | Legacy report/analysis paths | Bridge to v2 canonical contract |
| Reporting/publication export | Reporting | `formal_report_service.py`, `publication_export_service.py` | Reporting inputs and result artifacts | Partial | Service proof historically | Supplementary/table packages | Figure package support | Testing HTML/DOCX/markdown packages | Partial | legacy reporting reference only | Tie to canonical v2 result and keep testing label |
| Workflow dashboard | Workflow dashboard | Workflow dashboard/integration state | Project artifacts | No analysis confirmation | No analysis run | Status summaries | No | Workflow state | Partial | `codex/meta-workflow-ui` reference only | Keep as status surface, not analysis proof |
| AI suggestions | AI suggestions | AI suggestion services | Context records | Human accept/reject/apply | No analysis run | No | No | Candidate suggestions only | Pending | AI gateway branches | Keep out of L3 completion path |

## 6. Minimum Real Loop Checklist

### Bio

| Bio route | UI input/select | Parameter config | Real run | Status/log | Table | Plot | Report/export | Same run/provenance | L3 decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Controlled formal DEG | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Multi-factor DEG | Partial | Partial | Partial | Partial | Partial | Partial | Pending | Partial | Partial |
| limma/DESeq2/edgeR R runtime | Partial | Partial | Partial/branch evidence | Partial | Partial | Pending | Pending | Pending | Partial |
| ORA enrichment | Partial | Partial | Partial | Partial | Partial | Partial | Partial | Pending | Partial |
| GSEA preranked | Partial | Partial | Partial | Partial | Partial | Partial | Partial | Pending | Partial |
| Correlation | Partial | Partial | Partial | Partial | Partial | Pending | Pending | Pending | Partial |
| KM/log-rank survival | Partial | Partial | Partial | Partial | Partial | Partial | Blocked for clinical report | Pending | Partial |
| Cox survival | Partial | Partial | Partial | Partial | Partial | Partial | Blocked for clinical report | Pending | Partial |
| Risk score / nomogram / DCA | No | No | No | No | No | No | No | No | No |
| Integrated report/renderers | Partial | Partial | Partial | Partial | Partial | Partial | Partial/testing | Pending | Partial |

### Meta

| Meta route | UI input/select | Plan/config | Real statistics run | Status/log | Canonical contract | Table | Forest plot | Report/export | Same run/hash | L3 decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Protocol/Search | Yes | Partial | Not a statistics run | Partial | No | No | No | Search report only | No | Partial |
| Literature import | Yes | Partial | No | Partial | No | Import diagnostics only | No | Import exports | No | Partial |
| Deduplication | Yes | Partial | No | Partial | No | Dedup table/library | No | Decision exports | No | Partial |
| Screening/fulltext non-OCR | Yes | Partial | No | Partial | No | Screening/fulltext tables | No | Missing fulltext reports | No | Partial |
| Extraction | Yes | Partial | No | Partial | No | Extraction CSV | No | Validation export | No | Partial |
| Quality assessment | Yes | Partial | No | Partial | No | Quality table | No | Quality export | No | Partial |
| Analysis plan | Yes | Yes | No | Yes | No | No | No | Plan manifest | No | Partial |
| Statistics v2 | Partial in current UI | Yes | Yes by service proof | Yes | No | Statistics result only | No | No | No | Partial |
| Canonical result contract artifacts | Discovery only in source reports | Yes | Yes by service proof | Yes | Yes | Yes | Yes | Testing-level only | Yes | Partial |
| Forest plot/table export older path | Yes | Partial | Older service path | Partial | No | Yes | Yes | No | No | Partial |
| Reporting/publication export | Yes | Partial | No canonical v2 UI proof | Partial | Partial | Partial | Partial | Testing-level only | Pending | Partial |
| OCR/fulltext adapter | No current-proven OCR UI | No | No | No | No | No | No | No | No | No |
| AI suggestions | Yes | Human accept/apply required | No | Partial | No | No | No | Candidate-only | No | Pending |

## 7. Migration and Legacy Control Summary

| Source branch/legacy | Relevant area | Allowed use | Direct migration allowed? | Reason | Next control action |
| --- | --- | --- | --- | --- | --- |
| `dev/release-internal-test` | Bio DEG R adapters, enrichment/resource gates, report renderer policies | Material library for adapters | No | Divergent tree; direct carry-over would overwrite current contracts | Select narrow candidate and adapt behind current UI/result contracts |
| `stable/mainline` | Historical Bio formal DEG/MainLine baseline | Historical baseline only | No | Older than current Bio L3 and Meta Phase 3 | Reference only for comparison |
| `dev/meta-analysis` | Meta OCR/fulltext/package history | Selective reference only | No | Diverges from current Bio tree; OCR dependency/package risks | Use later for adapter research only |
| `dev/integration` | Integration registry and UI rebuild history | Contract reference | No | Not current source of truth for Bio/Meta analysis runtime | Reference integration contracts only |
| `codex/releasebuild-formal-deg-carryover` | Risk score, nomogram, calibration/DCA | Requirements source for rewrite | No | Clinical overclaim risk; not current production coverage | Rewrite later under strict clinical boundary |
| `codex/mainline-survival-clinical-carryover` | Enrichment convergence, survival/clinical material | Adapter/rewrite source | No | Needs mapping before reuse; clinical/report boundaries remain disabled | Prove current UI loops first |
| `codex/meta-workflow-ui` | Old Meta workflow UI | UI reference only | No | Superseded by current Meta pages | Do not replace current UI |
| `codex/meta-analysis-refresh` | Old Meta project home/UI refinements | UI reference only | No | Mostly superseded by current pages | Use only for copy/layout ideas after design review |
| `app/bioinformatics/legacy/**` | GEO tool/pipeline, TCGA/GTEx facade, legacy scripts/tests | Requirements archaeology, fixtures, wording, resource reference | No | Deprecated runtime, old contracts, compatibility wrappers | Keep quarantined; rewrite only when selected |
| `app/meta_analysis/legacy/**` | Old workbench, literature/extraction/fulltext/reporting, fake GEO readiness, no-op runners | Requirements archaeology and design reference only | No | Historical snapshot; fake/dry-run/no-op paths not real current evidence | Keep quarantined; do not count as current capability |

## 8. Blockers and Next Actions

| Priority | Blocker / gap | Affected area | Why it matters | Required next action | Owner line | Must finish before |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | Meta UI L3 not yet proved | Meta Analysis | Phase 3 is service/contract proof, not current UI L3 | Prove current UI from confirmed plan to v2 run, canonical contract, table, forest plot, report/export | Meta Analysis | Old feature migration and final productization |
| P2 | Bio ORA/GSEA current UI L3 not yet proved | Bioinformatics enrichment | Current MVP/branch material cannot be claimed L3 without UI proof | Select ORA then GSEA route and run focused current UI L3 proof | Bioinformatics | Enrichment release claims |
| P3 | Bio R/runtime hardening not yet adapted | Bio DEG runtime | Branch R adapters and external dependencies are not current-contract-backed | Adapt detect-first runtime gates behind current DEG contracts | Bioinformatics | DEG production hardening |
| P4 | Integrated report/renderers not fully current-contract-backed | Bio and Meta reports | Reports can overstate completion if not tied to current result provenance | Tie report/export to current canonical result contracts and mark testing-level where applicable | Shared reports | Productization |
| P5 | Risk/nomogram/DCA not production current | Bio survival/clinical | Clinical overclaim risk is high | Rewrite later with strict clinical boundary and disabled conclusions | Bioinformatics | Any clinical/report-ready claim |
| P6 | OCR/fulltext adapter not current-proven | Meta fulltext | Branch OCR history is not current UI proof | Defer until after Meta UI L3; adapt only if selected | Meta Analysis | OCR-related capability claims |
| P7 | Legacy branch direct migration forbidden | All routes | Direct migration can reintroduce old contracts, mocks, placeholders, or fake paths | Keep legacy as material library; require current UI, contract, tests, real output | Project control | Any migration work |
| P8 | Final UI productization waits for stable L3 paths | Productization | Current work remains testing/developer-preview in many areas | Stabilize L3-proved routes and block unsupported claims | Project control / UI shell | Release/product packaging claims |

## 9. Executive Progress Table

| Item | Done? | What is done | What is not done | Next step |
| --- | --- | --- | --- | --- |
| UI baseline and page/button map | Yes | Phase 0/1 baseline and entry map; coverage matrix lists 25 UI areas | Button-level count beyond source reports not recomputed in this dashboard | Keep map current when new UI proof lands |
| Branch inventory | Yes | Phase 2.5 branch inventory and legacy catalogs completed | No branch migrated | Use as material-control input only |
| Project control plan | Yes | Current mainline and next priority recorded | Does not implement features | Enforce branch and legacy guardrails |
| Bio controlled DEG L3 | Yes | Current UI single-point controlled formal DEG proved through table, SVG plot, and section report package | Full Bio module not complete | Preserve path and harden next DEG gates |
| Meta result contract unification | Partial | Phase 3 service/contract bridge proves same-run table, forest plot, testing report/export artifacts | Not current UI L3 | Run Meta Phase 4 UI proof |
| Meta UI L3 | No | Source reports identify target and blocker | Current UI L3 proof not present in required source reports | Prove current UI end to end |
| Bio enrichment L3 | No | Current MVP/branch candidates identified | ORA/GSEA current UI L3 not proved | Prove ORA then GSEA under current contracts |
| Bio survival/clinical controlled proof | Partial | Controlled current survival/Cox code/tests exist by inventory | UI L3 and clinical/report-ready claims not proved | Prove controlled loops; keep clinical conclusions disabled |
| Final UI productization | Deferred | Current guardrails and testing labels are documented | Stable full L3 route set not ready | Wait for L3 closure and contract-backed outputs |
| Old branch migration | Blocked | Candidate ledger identifies material sources | Direct migration is forbidden | Select narrow adapter/rewrite candidates only after current UI path is named |

## Dashboard Decision

The current project has one proved current UI L3 route: Bioinformatics controlled formal DEG. Meta Phase 3 has a valid canonical result contract bridge, but it remains partial until the current Meta UI proves the same end-to-end loop. Branches and legacy directories remain material libraries only and must not be merged, cherry-picked, or counted as current capability.
