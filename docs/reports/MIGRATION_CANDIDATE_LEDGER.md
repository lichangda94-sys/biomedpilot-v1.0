# Migration Candidate Ledger

Date: 2026-06-04

Current audit baseline:

```text
branch: dev/bioinformatics
HEAD: db5bef1a224a8a6983c011da9260658364c25c7f
audit mode: Phase 2.5 read-only inventory
```

No candidate below is marked current available solely because it exists on a branch, under `legacy/`, or in archived material. A candidate is reusable only after it is adapted to the current UI and current result/input contracts, with current tests and real output evidence.

| Recommendation | Meaning |
| --- | --- |
| `reuse` | Current implementation is already present; preserve and test through the current UI/contract. |
| `adapter` | Historical implementation may be wrapped behind current contracts. |
| `rewrite` | Use as requirements/reference; reimplement against current architecture. |
| `deprecated` | Do not migrate directly. |
| `ignore` | Out of scope for Bio/Meta analysis migration. |

## Candidate Ledger

| Candidate feature | Source branch / path | Involved files | Description | Current UI page/button | Current implementation? | Real run? | Tests? | Real figure/table/report? | Old state/path dependency | Risk | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Bio controlled formal DEG loop | current `dev/bioinformatics` | `app/bioinformatics/deg_engine/formal_runner.py`, `plots/formal_deg.py`, `reports/formal_deg.py`, `workflow_pages.py` | Gated DEG run to review, plot artifact, and DEG section package | Bio Analysis Task Center / Results Browser | Yes | Prior L3 reports/tests; not rerun in this audit | Yes by current test inventory | Table, SVG plot, DEG section package when gates pass | Current B8/B9+ contracts | Medium | reuse |
| DEG hardening gates | current | `deg_engine/input_adaptation.py`, `design_quality.py`, `data_quality.py`, `method_recommendation.py`, `audit_package.py`, `cross_project_acceptance.py` | Real project adaptation, design/data QA, recommendations, audit package | Analysis Center DEG readiness | Yes | Not rerun here | Yes by inventory | Audit/table packages, not clinical report | Current resolver/result index | Medium | reuse with focused proof |
| Python DEG backend | current | `python_backend.py`, `dependency_check.py`, `runtime_validation.py` | Controlled scipy/statsmodels DEG backend and dependency gate | DEG method/runtime status | Yes | Not rerun here | Yes by inventory | Result table only; plot/report separate | Python dependency availability | Medium | reuse |
| limma/DESeq2/edgeR R adapters | current + ReleaseBuild branches | `multifactor_r_runner.py`; branch-only `rscript_adapter.py`, `r_limma_*`, `r_deseq2_*`, `r_edger_*` | R DEG backends and runtime validation history | DEG method controls | Partial current plus richer branch-only structured files | Not rerun here | Current/branch evidence by inventory | Result tables only; plots/reports separate | External R/Bioc detect-first state | High | adapter |
| Multi-factor DEG | current | `multifactor_gate.py`, `multifactor_schema.py`, `multifactor_confirmation.py`, `multifactor_r_runner.py` | Controlled multi-factor DEG schema, confirmation, and fixture runners | Analysis Center multi-factor DEG controls | Yes/controlled | Not rerun here | Yes by inventory | Candidate plot/report integration exists | Current design QA/result schema | Medium | reuse with proof |
| Standard analysis runtime | current | `app/analysis_runtime/**`, `analysis/**` | Mock/lite/full-mode result package task bridge with resource governance and external R command boundary | Package catalog / future task bridge | Current scaffold | Mock/lite only by current design; not production | Current focused tests by history | Mock/lite package artifacts only | Full mode intentionally blocked by resource policy | Medium | keep quarantined until selected proof |
| DEG standard worker fixture | current | `analysis/modules/deg/module.json`, `analysis/fixtures/inputs/deg/**`, `analysis/runners/run_module.R` | Base R DEG lite fixture package | Package catalog scaffold | Yes/current scaffold | Not rerun here | Current focused tests by history | Fixture TSV/package, testing-level | Lite worker mode | Medium | reuse as scaffold |
| Enrichment standard worker fixture | current | `analysis/modules/enrichment/**`, fixtures, `run_module.R` | Base R ORA/GSEA-like lite fixture | Package catalog scaffold | Yes/current scaffold | Not rerun here | Current focused tests by history | Fixture TSV/package, testing-level | Lite worker mode | Medium | reuse as scaffold |
| Docking lite external-tool contract | current | `analysis/modules/docking/**`, `analysis/fixtures/inputs/docking/**`, `run_module.R` | Vina command-manifest fixture without external-tool execution | Package catalog scaffold | Yes/current scaffold | Not scientific docking run | Current focused tests by history | Command manifest only, no scientific docking result | Full external-tool environment not part of current proof | Medium | reuse as scaffold |
| Survival/univariate/multivariate/immune lite workers | current | `analysis/modules/{survival,univariate,multivariate,immune_infiltration}/**` | Lite R fixtures and packages for future module proof | Package catalog scaffold | Yes/current scaffold | Not rerun here | Current focused tests by history | Fixture tables/SVG where applicable, testing-level | Lite worker mode | Medium/high | reuse as scaffold |
| ORA enrichment MVP | current flat modules + ReleaseBuild structured modules | `enrichment_*`, `gene_set_resources.py`; branch `app/bioinformatics/enrichment/**` | Controlled ORA gates/execution/review/plot/report history | Enrichment page / Analysis Center | Yes current flat; branch has structured layout | Not rerun here | Yes by inventory | Plot/report gates exist for controlled outputs | Current flat paths vs branch package paths | Medium | adapter/rewrite for structure |
| GSEA preranked MVP | current flat modules + ReleaseBuild structured modules | `enrichment_*`; branch `gsea/**`, `plots/gsea.py`, `reports/gsea.py` | Controlled preranked GSEA history | Analysis Center GSEA rows | Partial/current flat; branch package richer | Not rerun here | Current/branch evidence | Plot/report gates exist by inventory | Branch package paths differ | Medium/high | adapter |
| Enrichment resource registry | current + ReleaseBuild branches | `gene_set_resources.py`, `enrichment_resources.py`, branch `gene_set_gate.py` | Gene set resource/version/dependency gates | Enrichment resources panel | Partial/current | Not rerun here | Yes by inventory | Resource/gate output, not analysis result | External R/resource availability | Medium | reuse/adapter |
| Real SVG plot renderers | current + ReleaseBuild branches | current `plots/basic_renderers.py`, `formal_deg.py`, `survival.py`, `cox.py`; branch `plots/real_svg.py`, `ora.py`, `gsea.py` | Plot artifact renderers | Results Browser plot actions | Current for supported modules; branch has broader split | Not rerun here | Current plot tests by inventory | SVG artifacts when source result gate passes | Must inherit result semantics | Medium | adapter |
| KM/log-rank survival | current | `survival_clinical/km_*`, `plots/survival.py` | Controlled KM/log-rank | Survival/Clinical UI rows | Yes/controlled | Not rerun here | Yes by inventory | Plot artifact support exists | Clinical report-ready restricted | High | reuse with strict gate |
| Cox univariate | current | `survival_clinical/cox_*`, `plots/cox.py` | Controlled Cox univariate | Survival/Clinical UI rows | Yes/controlled | Not rerun here | Yes by inventory | Plot artifact support exists | Clinical report-ready restricted | High | reuse with strict gate |
| Cox multivariate | current + survival carry-over branches | `cox_multivariate_*` files and branch history | Controlled design/execution/review candidates | Survival/Clinical rows | Partial/current | Not rerun here | Current/branch inventory | Section package only if gated | Strong clinical variable/outcome gates | High | adapter/rewrite |
| Risk score / nomogram / calibration / DCA | ReleaseBuild/internal-test branches, mixed current evidence | `risk_score_*`, calibration/DCA files/tests | Risk score and advanced visualization candidates | No proven production UI completion | Not production-current | Not rerun here | Branch/current evidence only | Candidate plots/reports by branch evidence only | Clinical interpretation risk | High | rewrite |
| Full integrated report/renderers | current + ReleaseBuild branches | current `reports/**`; branch `reports/integrated.py`, `renderer_capability.py`, `renderer_runtime_policy.py` | Integrated report package and renderer gates | Bio report/export controls | Partial current/branch diverged | Not rerun here | Current/branch tests by inventory | Markdown/DOCX/PDF policy history | External renderer detect-first | Medium/high | adapter |
| Bio recognition / standardized asset selection | current + old branches | `project_recognition.py`, `project_standardization.py`, `standardized_asset_selection.py`, `analysis_inputs/**` | Recognition and standardized asset selection | Bio Recognition / Standardized Assets | Yes/current | Input workflow only | Current tests | No analysis artifact | Must feed resolver only | Medium | reuse |
| Immune infiltration | current | `immune_infiltration/**`, standard lite worker fixture | Bulk immune/TME scoring candidate | Bio immune pages / package catalog scaffold | Yes/current candidate | Not rerun here | Current tests by inventory | Score/report scaffold exists | Signature/resource policy | Medium | reuse with proof |
| Legacy GEO desktop tool | `app/bioinformatics/legacy/geo_tool/**`, `archive/legacy_sources/bioinformatics_project/geo_tool/**` | Standalone GEO workflow | No current UI button should call directly | No | Legacy only | Legacy tests only | Not current formal output | Old standalone paths | High | deprecated |
| Legacy TCGA/GTEx facade | `app/bioinformatics/legacy/tcga_gtex/**`, archive mirror | Old TCGA/GTEx optional runtime | Current Data Source cards use newer services | No direct current use | Legacy only | Legacy tests only | No current output | Old locator/mock contracts | High | rewrite |
| Meta current v2 statistics | current | `meta_statistics_engine_service.py`, `stats/**`, `analysis_page.py` | Real v2 statistics from confirmed plan, still marked testing-level | Meta Analysis / Run statistics analysis | Yes | Prior focused tests/reports; not rerun here | Yes | Statistics result | Current v2 contract | Medium | reuse |
| Meta result contract bridge | current | `meta_result_contract_adapter.py`, `analysis_page.py` | v2 run drives table, forest plot, testing markdown artifact with one hash | Meta Analysis page state discovery | Yes | Prior Phase 3/4 proof; not rerun here | Yes | CSV, PNG, markdown artifact, testing-level | Current v2 run/result contract | Medium | reuse |
| Meta older forest/table path | current | `analysis_run_service.py`, `figure_result_service.py` | Older `analysis_results.json` forest/table path | Meta figure/table buttons | Yes | Tests exist by inventory | Yes | PNG/CSV | Split from v2 contract in some paths | Medium/high | adapter |
| Meta publication export | current | `publication_export_service.py`, `formal_report_service.py`, `reporting_page.py` | Testing HTML/DOCX/supplementary/figure/repro packages | Meta Reporting page | Yes | Service tests by inventory | Yes | Real files but testing-level | Not always tied to v2 run | Medium/high | adapter |
| Meta literature import/dedup/screening | current + old Meta branches | `pages/literature_import_page.py`, `duplicate_review_page.py`, services | Literature import, dedup queue, screening flow | Current Meta workflow pages | Yes/current for parts | Not rerun here | UI/service tests by inventory | Tables/diagnostics; not final stats | Current workflow state | Medium | reuse with proof |
| Meta OCR/fulltext | `dev/meta-analysis` | OCR worker/runtime files | Fulltext pages, not proven current | Not current-proven | Not rerun | Branch evidence only | No current result claim | External OCR dependency/package divergence | High | rewrite/adapter later |
| Meta old workbench | `app/meta_analysis/legacy/app/**`, `app_meta/**`, archive mirror | old dashboard/sidebar/pages/icons | None | No | Legacy only | Legacy tests only | Old reporting summaries | Old app shell/state | High | deprecated |
| UI shell/status/icon/export design | `dev/ui-shell`, `integration/*ui*` | `docs/ui/**`, screenshots, shell tests | UI design and shell material | Shared UI shell/report export shell | Branch-only/design material | Not analysis run | Branch evidence only | Visual assets only | UI branch state | Medium | adapter only after UI owner selection |
| Shared AI gateway | `dev/ai-gateway`, OCR/AI branches | gateway/provider/role isolation | AI draft routing | AI suggestions pages | Not analysis runtime | Not relevant | Branch tests unknown | No analysis output | Shared provider state | Medium | ignore |
| Shared vocabulary | `dev/shared-vocabulary`, vocabulary branches | vocabulary resources | Medical term expansion | Search/query builders | Not analysis runtime | Not relevant | Branch tests unknown | No analysis output | Resource governance | Low | ignore |

## Immediate Migration Guidance

1. Do not carry over any old branch wholesale.
2. Prefer current implementations when current services and tests already exist.
3. Treat branch-only R/enrichment/report/renderer/risk/OCR work as adapter or rewrite candidates only.
4. Treat old standalone workbenches, fake GEO preflights, no-op task runners, and placeholder reporting as deprecated.
5. Require a current UI button/path mapping, current contract mapping, current tests, and real output evidence before marking any candidate usable.
6. Treat current standard worker mock/lite modules as scaffolds unless a later phase proves an ordinary current UI path and module-specific real output contract.

## Stop Point

This ledger is a planning artifact, not a migration approval. No `reuse`, `adapter`, or `rewrite` recommendation changes runtime availability.
