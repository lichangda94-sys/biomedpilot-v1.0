# Migration Candidate Ledger

Date: 2026-05-29

## Rules

No candidate below is marked as current available solely because it exists on a branch or under `legacy/`. A candidate is reusable only after it is adapted to the current UI and current result/input contracts, with current tests.

Legend:

| Recommendation | Meaning |
| --- | --- |
| `reuse` | Current implementation is already present; preserve and test. |
| `adapter` | Historical implementation may be wrapped behind current contracts. |
| `rewrite` | Use as requirements/reference; reimplement against current architecture. |
| `deprecated` | Do not migrate directly. |
| `ignore` | Out of scope for Bio/Meta analysis migration. |

## Candidate Ledger

| Candidate feature | Source branch / path | Involved files | Description | Current UI page/button | Current implementation? | Real run? | Tests? | Real figure/table/report? | Old state/path dependency | Risk | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Bio formal DEG single-point loop | current `dev/bioinformatics` | `deg_engine/formal_runner.py`, `plots/formal_deg.py`, `reports/formal_deg.py`, `workflow_pages.py` | Controlled DEG from formal result to table/plot/report package | Bio Analysis Task Center / Results Browser | Yes | Yes, previously proven for controlled formal DEG | Yes, current tests | Yes: table, SVG plot, section package | Current B8/B9 contracts | Medium | reuse |
| Bio DEG production hardening gates | current + `dev/release-internal-test` | `deg_engine/input_adaptation.py`, `design_quality.py`, `data_quality.py`, `method_recommendation.py`, `audit_package.py`, branch `r_*` files | Real project input, batch/design, data quality, method recommendation, audit package | Analysis Center DEG readiness preview | Partial/current; branch contains divergent R packaging work | Current proof varies by gate | Current tests exist for many gates | Audit package, not necessarily figure/report | Must use current resolver/result index | Medium/high | adapter |
| limma/DESeq2/edgeR R runtime adapters | `dev/release-internal-test` and current | `deg_engine/rscript_adapter.py`, `r_limma_*`, `r_deseq2_*`, `r_edger_*`, current `multifactor_r_runner.py` | Mature R backend adapter candidates | Analysis Center DEG method controls | Partial/current plus branch-only files | Branch has runtime validation evidence by history, not rerun here | Branch/current tests exist by file evidence | Result tables only; plot/report separate | External R/Bioc detect-first state | High | adapter |
| Multi-factor DEG | current + `dev/release-internal-test` | `multifactor_gate.py`, `multifactor_schema.py`, `multifactor_confirmation.py`, `multifactor_r_runner.py` | Controlled multi-factor DEG schema/confirmation/fixture runners | Analysis Center multi-factor DEG controls | Yes/partial current | Not rerun in this audit | Current tests present | May enter plot/report only after gates | Requires design QA/current result schema | Medium | reuse with focused proof |
| ORA enrichment MVP | current + `codex/mainline-survival-clinical-carryover` | Current flat `enrichment_*`; branch `app/bioinformatics/enrichment/**` | Controlled ORA input/result/review/plot/report gates | Bio Enrichment/Analysis Center | Yes/current flat implementation; branch has reorganized modules | Not rerun here | Current tests listed | Plot/report gates exist | Current flat paths vs branch package paths diverge | Medium | adapter/rewrite |
| GSEA preranked MVP | current + `dev/release-internal-test` | Current `enrichment_*`; branch `gsea/**`, `plots/gsea.py`, `reports/gsea.py` | Controlled preranked GSEA | Analysis Center GSEA rows | Partial/current flat; branch package richer | Not rerun here | Current/branch tests by file evidence | Plot/report gates exist | Branch package paths differ | Medium/high | adapter |
| Enrichment production resource registry | `dev/release-internal-test` | `enrichment/gene_set_gate.py`, `gsea/gene_set_gate.py`, `enrichment/dependency_check.py` | Resource/version/dependency gates | Analysis Center enrichment resources | Not fully current as package structure | Not rerun | Branch tests by file evidence | Not primary output | ReactomePA/msigdbr/external R state | Medium | adapter |
| Real SVG plot renderer | current + `dev/release-internal-test` | current `plots/basic_renderers.py`, `plots/formal_deg.py`; branch `plots/real_svg.py`, `plots/ora.py`, `plots/gsea.py` | DEG/ORA/GSEA/SK survival SVG rendering candidates | Results Browser plot actions | Current has real DEG/SVG and plot modules; branch has generalized renderer | Some current proof for DEG; not all plot types here | Current tests present | Yes for supported plot artifacts | Must preserve source result semantics | Medium | adapter |
| KM/log-rank survival | current | `survival_clinical/km_*`, `plots/survival.py`, tests | Controlled KM/log-rank result schema/review/plot spec/runtime | Bio Survival page / Analysis Center survival rows | Yes/controlled | Not rerun here | Current tests present | Plot artifact support exists | Clinical report-ready remains disabled | High clinical overclaim risk | reuse with strict gate |
| Cox univariate | current | `survival_clinical/cox_*`, `plots/cox.py`, tests | Controlled Cox univariate result/review | Bio Survival/Clinical UI rows | Yes/controlled | Not rerun here | Current tests present | Plot artifact support exists | Clinical report-ready remains disabled | High clinical overclaim risk | reuse with strict gate |
| Cox multivariate | current + `codex/releasebuild-formal-deg-carryover` | `cox_multivariate_design.py`, current/branch risk-report commits | Controlled design/execution/review candidates | Survival clinical rows | Partial/current | Not rerun here | Current tests present by inventory | Section package only, no clinical conclusion | Requires strong clinical variable/outcome gates | High | adapter/rewrite |
| Risk score / nomogram | `codex/releasebuild-formal-deg-carryover` | Commit evidence: `risk score report-ready`, `calibration decision curve plot gate` | Risk score/nomogram/calibration/DCA candidates | No proven current public UI completion | Not current-proven | Not rerun | Branch evidence only | Candidate plots/reports by commits only | Clinical interpretation risk | High | rewrite |
| Full integrated report/renderers | `dev/release-internal-test` | `reports/integrated.py`, `renderer_capability.py`, `renderer_runtime_policy.py` | Full integrated report package and renderer gates | Bio report/export controls | Partial current/branch diverged | Not rerun | Branch tests by evidence | Markdown/DOCX/PDF policies by history | External pandoc/xelatex detect-first | Medium/high | adapter |
| Bio recognition / standardized asset selection | current + `stable/mainline` + `dev/release-internal-test` | `project_recognition.py`, `project_standardization.py`, `standardized_asset_selection.py`, `recognition_next_steps.py` | Recognition and standardized asset selection | Bio Recognition / Standardized Assets | Yes/current | Input workflow, not analysis result | Current tests present | No analysis artifact | Must feed resolver only | Medium | reuse |
| Legacy GEO desktop tool | `app/bioinformatics/legacy/geo_tool/**` | `geo_tool/main.py`, `geo_workflow.py`, wrappers | Standalone GEO workflow | No current UI button should call directly | No | Legacy only | Legacy tests only | Not current analysis report | Old standalone paths | High | deprecated |
| Legacy TCGA/GTEx facade | `app/bioinformatics/legacy/tcga_gtex/**` | adapters/facade/lexicon | Old TCGA/GTEx optional runtime | Current Data Source cards have newer services | No direct | Legacy only | Legacy tests only | No current output | Old locator/mock contracts | High | rewrite |
| Meta result contract bridge | current `dev/bioinformatics` | `meta_result_contract_adapter.py`, `analysis_page.py` | v2 statistics run drives table, plot, report/export artifact via one hash | Meta Analysis page state discovery | Yes | Yes focused Phase 3 proof | Yes current test | Yes: CSV, PNG, markdown export | Current v2 run/result contract | Medium | reuse |
| Meta v2 statistics engine | current + `codex/bio-ui-download-integration` | `meta_statistics_engine_service.py`, `analysis_plan_service.py` | Real v2 meta statistics from confirmed plan | Meta Analysis / Run statistics analysis | Yes | Yes current tests | Yes | Statistics result only | Current v2 contract | Medium | reuse |
| Meta older analysis result path | current | `analysis_run_service.py`, `figure_result_service.py` | Older dataset -> `analysis_results.json` -> forest/table path | Meta Analysis basic run, forest plot, result table | Yes | Yes tests | Yes | Real PNG/CSV | Split from v2 contract | Medium/high | adapter |
| Meta publication export | current | `publication_export_service.py`, `formal_report_service.py` | Testing HTML/DOCX/supplementary/figure/repro packages | Meta Reporting page | Yes | Service tests pass historically | Yes | Real files but testing-level | Not always tied to v2 run | Medium/high | adapter |
| Meta OCR/fulltext | `dev/meta-analysis` | PaddleOCR worker/runner/package commits | OCR fulltext integration | Fulltext pages not proven here | Not current-proven | Not rerun | Branch evidence only | No analysis result | External OCR dependency/package divergence | High | rewrite/adapt later |
| Meta old workbench | `app/meta_analysis/legacy/app/**`, `app_meta/**` | old dashboard/sidebar/pages/icons | Standalone old UI | None; current UI is only mainline | No | Legacy only | Legacy tests only | Some old reporting summaries | Old app shell/state | High | deprecated |
| Meta literature import/dedup/screening legacy | `app/meta_analysis/legacy/literature/**` | parsers, dedup, screening | Older systematic review pipeline services | Current Meta literature pages | Mostly superseded | Legacy only | Legacy tests only | No final report claim | Old stores/models | Medium | ignore/reference |
| Shared AI gateway | `dev/ai-gateway`, `codex/integration-meta-ocr-labtools-carryover` | gateway/provider/role isolation commits | AI draft routing | AI suggestions pages | Not analysis runtime | Not relevant | Branch tests unknown | No analysis output | Shared provider state | Medium | ignore |
| Shared vocabulary | `dev/shared-vocabulary`, vocab branches | vocabulary resources | Medical term expansion | Search/query builders | Not analysis runtime | Not relevant | Branch tests unknown | No analysis output | Resource governance | Low | ignore |

## Immediate Migration Guidance

1. Do not carry over any old branch wholesale.
2. Prefer current implementations when a current service and current tests already exist.
3. Treat branch-only R/enrichment/report renderer work as adapter candidates only.
4. Treat old standalone workbenches, fake GEO preflights, and placeholder reporting as deprecated.
5. Require a current UI button/path mapping and a current test before marking any candidate as usable.

