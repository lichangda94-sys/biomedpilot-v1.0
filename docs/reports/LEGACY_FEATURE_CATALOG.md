# Legacy Feature Catalog

Date: 2026-06-04

Current baseline:

```text
branch: dev/bioinformatics
HEAD: 9436f03aa0ea3d926f44e3aceef5320bfb0e2781
mode: Phase 2.5 read-only inventory
```

This catalog covers current non-legacy feature surfaces, `app/bioinformatics/legacy/**`, `app/meta_analysis/legacy/**`, `archive/legacy_sources/**`, and branch-discovered historical implementation areas. It is not a current capability claim.

## Evidence Labels

| Label | Meaning |
| --- | --- |
| Current | Present in current non-legacy source and supported by current tests or recent current-line proof. |
| Current scaffold | Present in current source but mock/lite/testing-level or not wired as ordinary user completion. |
| Branch evidence | Present on a local branch by read-only branch/file/diff evidence only. |
| Legacy tests only | Present under `legacy/` or `archive/legacy_sources/**` with historical tests/docs only. |
| Deprecated | Historical, placeholder, fake, no-op, old shell path, or boundary-violating code that must not be migrated directly. |

## Bioinformatics Current Non-Legacy Feature Areas

| Feature area | Current files | Description | Evidence | Production claim allowed? |
| --- | --- | --- | --- | --- |
| Recognition / standardization / resolver | `project_recognition.py`, `project_standardization.py`, `standardized_asset_selection.py`, `analysis_inputs/**`, `deg_ready/**` | Input contract layer for downstream analysis | Current source/tests | No; input contract only |
| TCGA/GTEx/local assets | `data_sources/**`, `tcga/**`, `standard_assets/**`, `search_center/**` | Data source preview/download/build/standardized packages | Current source/tests | No; upstream data preparation only |
| Controlled formal DEG | `deg_engine/formal_runner.py`, `parameter_gate.py`, `result_schema.py`, `python_backend.py`, `runtime_validation.py` | Gated two-group DEG result execution and schema | Current tests and L3 proof reports | Research/statistical only; not clinical/public production |
| DEG production hardening gates | `deg_engine/input_adaptation.py`, `design_quality.py`, `data_quality.py`, `method_recommendation.py`, `audit_package.py`, `cross_project_acceptance.py` | Real project input adaptation, design/data QA, method explanation, audit package | Current tests by file inventory | Candidate; must still be proven per project |
| Multi-factor DEG | `deg_engine/multifactor_*`, `multifactor_r_runner.py` | Controlled multi-factor schema/confirmation/R fixture runners | Current tests under `test_multifactor_deg_*` | Controlled only |
| ORA/GSEA enrichment | flat `enrichment_*`, `gene_set_resources.py`, `services/enrichment_*` | Controlled ORA/GSEA gates, execution/review/plot/report/audit | Current tests under `test_enrichment_*` | MVP/research only |
| Survival / Cox | `survival_clinical/**`, `clinical_analysis/**`, `plots/survival.py`, `plots/cox.py` | Controlled KM/log-rank and Cox univariate; multivariate design/runtime candidates | Current tests under KM/Cox names | Statistical research only |
| Immune infiltration | `immune_infiltration/**` | Signature scoring/readiness/report candidates | Current source/tests | Research only |
| Plot artifacts | `plots/basic_renderers.py`, `formal_deg.py`, `survival.py`, `cox.py`, `schema.py`, `registry.py` | SVG/spec-driven plot artifacts for supported results | Current plot tests | Not a full plotting platform |
| Report/export packages | `reports/**` | Section/package report gates, project report builder, export packages | Current report tests | Statistical package only; no clinical conclusion |
| Standard analysis runtime bridge | `app/analysis_runtime/**`, `analysis/registry/**`, `analysis/runners/run_module.R` | Mock/lite/full-mode runner contract, package catalog foundation, resource governance, and separate input/parameter provenance hashes | Current recent commits/tests | Current scaffold only |
| Lite standard workers | `analysis/modules/{deg,enrichment,survival,univariate,multivariate,immune_infiltration}/**`, corresponding fixtures | Base R lite fixture workers writing standard result packages | Current recent commits | Lite/testing-level only |
| DEG standard module contract | `analysis/modules/deg/module.json`, `analysis/fixtures/inputs/deg/**`, `analysis/runners/run_module.R` | Standard worker DEG mock/lite contract and base R lite fixture output | Current recent commits/tests | Lite/testing-level only; separate from formal DEG engine |
| Enrichment standard package sidecar | `enrichment_r_adapter.py`, `app/analysis_runtime/standard_package.py` | Adds standard package sidecar to controlled ORA/GSEA adapter output | Current-line evidence from `0aa6793`; not rerun in this audit | Sidecar/audit infrastructure; does not make full production ORA/GSEA |
| Multi-factor DEG standard package sidecar | `deg_engine/multifactor_r_runner.py`, `app/analysis_runtime/standard_package.py` | Registers standard package sidecars for controlled multi-factor limma/DESeq2/edgeR fixture outputs | Current-line evidence from `6bdc6e2`; not rerun in this audit | Sidecar/audit infrastructure; does not expand user-facing execution |

## Bioinformatics Legacy Catalog

| Feature area | Source files | Description | Evidence | Current equivalent | Status |
| --- | --- | --- | --- | --- | --- |
| Standalone GEO desktop tool | `app/bioinformatics/legacy/geo_tool/**`, archive copy | Old GEO GUI, query helpers, MeSH builders, workflow wrappers | Legacy tests/docs | Current Bio UI plus search/recognition/standardization/resolver | Deprecated runtime; reference only |
| GEO pipeline/processors | `legacy/geo_pipeline/**`, `legacy/geo_processing/**`, archive copy | Old GEO SOFT/download/detector/matrix classifier/validators | Legacy tests | Current downloader, recognition, resolver and standardized assets | Adapter/rewrite only |
| Module 3 sandbox UI | `legacy/ui/**` | Historical asset formatting sandbox | Legacy tests | Current standardized assets and Analysis Center | UI material only |
| TCGA/GTEx facade | `legacy/tcga_gtex/**` | Old adapters/facade/lexicon for TCGA/GTEx | Legacy tests/docs | Current `data_sources`, `tcga`, `standard_assets` | Rewrite/reference only |
| Bio literature CLI/GUI | `legacy/literature_cli.py`, `legacy/literature_gui.py` | Old literature utilities | Legacy only | Current Meta owns literature workflows | Deprecated for Bio |
| Compatibility download scripts | `download_geo_full_only.py`, `process_geo_family_soft.py`, `download_supplement_and_sra.py` | Old direct scripts | Legacy README/tests | Current task/downloader contracts | Deprecated/direct-use forbidden |
| Lexicon resources | `legacy/tcga_gtex/lexicon/**`, `configs/rules/**` | Chinese/English terms and mappings | Legacy coverage audits | Shared vocabulary/search resources | Reuse only through governed resource path |
| Legacy Bio tests | `legacy/tests/**` | Historical unit tests | Legacy tests only | Current `tests/bioinformatics` | Do not count as current tests |

## Meta Analysis Current Non-Legacy Feature Areas

| Feature area | Current files | Description | Evidence | Production claim allowed? |
| --- | --- | --- | --- | --- |
| Protocol/search/literature import | `pages/protocol_page.py`, `search/**`, `services/literature_*` | Current systematic review setup/search/import | Current tests | Internal/developer level unless separately proven |
| Dedup/screening/fulltext/extraction/quality | `pages/**`, `services/**`, `models/**` | Current workflow pages/services | Current test inventory | Not full production claim |
| Meta statistics v2 | `services/meta_statistics_engine_service.py`, `stats/**` | Current v2 statistics run | Current tests | Focused proof only |
| Meta result contract bridge | `services/meta_result_contract_adapter.py`, `pages/analysis_page.py` | One v2 run can drive table, forest plot, and testing markdown artifact with one hash | Current Phase 3/4 reports/tests | Do not claim full Meta L3 beyond focused proof |
| Figure/table/export services | `figure_result_service.py`, `publication_export_service.py`, `formal_report_service.py` | Forest/table/export artifact services | Current tests | Testing-level report/export unless gated |
| Workflow dashboard | `pages/workflow_dashboard_page.py` | Workflow status discovery | Current UI tests | Status UI only |

## Meta Analysis Legacy Catalog

| Feature area | Source files | Description | Evidence | Current equivalent | Status |
| --- | --- | --- | --- | --- | --- |
| Old workbench shell | `app/meta_analysis/legacy/app/**`, `app_meta/**`, archive `model9/app/**` | Standalone old dashboard/sidebar/pages | Legacy tests/docs | Current `app/meta_analysis/pages/**` and `workflow_pages.py` | Deprecated runtime; UI reference only |
| Literature import/dedup/screening | `legacy/literature/**` | RIS/NBIB/CSV parsing, dedup, screening | Legacy tests | Current literature/import/dedup/screening services | Mostly superseded |
| Extraction rules | `legacy/extraction/**` | Rule models/store/service | Legacy tests | Current extraction schema registry/form/validation | Reference only |
| Fulltext and bias services | `legacy/fulltext/**`, `legacy/bias/**` | Old fulltext/bias services | Legacy tests | Current fulltext, eligibility, quality services | Adapter/rewrite only |
| Reporting service | `legacy/reporting/**` | Reporting/profile readiness | Legacy tests | Current formal report/publication export services | Adapter/rewrite only |
| Analysis profiles/task runner | `legacy/analysis_profiles/**`, `legacy/core/task_*` | Historical profile/task lifecycle/no-op runner foundation | Legacy docs/tests | Current result/task contracts only if reimplemented | Conceptual reference only |
| Fake GEO readiness / DEG | `legacy/geo_readiness/**`, `legacy/analysis/deg_ready_matrix.py` | Fake/controlled GEO readiness and DEG-ready reports inside Meta snapshot | Legacy labels/docs | Current Bio owns GEO/DEG | Deprecated for Meta |
| Legacy icons/assets | `legacy/assets/**` | Icons/contact sheets/app icons | File inventory | UI design review only | Visual reference |
| Legacy package scripts | `legacy/packaging/**`, `legacy/scripts/**` | Standalone packaging/dev checks | Legacy docs | Current root packaging scripts | Deprecated |

## Branch-Only Feature Catalog

| Feature area | Source branch | Files/areas | Description | Evidence | Current equivalent/status |
| --- | --- | --- | --- | --- | --- |
| Structured R DEG adapters | `dev/release-internal-test`, `codex/releasebuild-formal-deg-carryover` | `rscript_adapter.py`, `r_limma_*`, `r_deseq2_*`, `r_edger_*` | limma/DESeq2/edgeR runtime planning and adapters | Branch evidence | Current has `multifactor_r_runner.py`; adapter candidate |
| Packaged ORA/GSEA modules | `dev/release-internal-test` | `app/bioinformatics/enrichment/**`, `gsea/**` | Structured package layout for ORA/GSEA gates | Branch evidence | Current has flat enrichment modules; adapter/rewrite only |
| Real SVG renderer split | `dev/release-internal-test` | `plots/real_svg.py`, `plots/ora.py`, `plots/gsea.py`, `plots/survival_real.py` | Broader split of plot renderers | Branch evidence | Current has formal DEG/survival/cox/basic renderers; parity unverified |
| Integrated report renderer policy | `dev/release-internal-test` | `reports/integrated.py`, `renderer_capability.py`, `renderer_runtime_policy.py` | Renderer capability and runtime policy | Branch evidence | Current report/export modules exist; parity unverified |
| Risk score / nomogram / calibration / DCA | ReleaseBuild/internal-test branches | `risk_score_*`, calibration/DCA files/tests | Risk score and advanced visualization gates | Branch/current mixed evidence | Must remain non-clinical and gated if revisited |
| Meta OCR fulltext | `dev/meta-analysis` | OCR workers and PaddleOCR subprocess runner | OCR worker/runtime/package history | Branch evidence | Not current-proven; adapter later |
| UI shell/result export surfaces | `dev/ui-shell`, `integration/*ui*` | `docs/ui/**`, screenshots, shell tests | UI design and shell material | Branch evidence | Design reference only |

## Evidence Boundary

Mock outputs, placeholder reports, no-op task runners, fake preflight, legacy-only tests, branch-only tests, and testing-level exports must never be listed as completed current functionality. Current scaffold items are useful architecture material but are not proof of full Bioinformatics or Meta Analysis module closure.

## 2026-06-04 Refresh Notes

Current `dev/bioinformatics` has advanced to `9436f03` since the previous catalog baseline. The only newly promoted catalog items are current-line scaffolds:

- DEG standard analysis module contract.
- DEG lite standard worker fixture.
- Multi-factor DEG standard package sidecar.
- Standard R worker provenance hardening with separate `input_hash` and `parameter_hash`.

These are not legacy migrations and are not production claims. They remain testing-level or controlled-sidecar evidence unless a later scoped phase proves a current UI path, current contract mapping, real output, and tests.

## Phase 2.5 Stop Point

No item in this catalog was migrated or promoted during this audit. Legacy entries remain quarantined. Branch-only features require a current UI handler, current input/result contract mapping, current tests, and real output evidence before they can move from catalog entry to implementation candidate.
