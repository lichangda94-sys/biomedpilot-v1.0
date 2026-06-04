# Legacy Feature Catalog

Date: 2026-06-04

## Scope

This catalog covers current `app/bioinformatics/legacy/**`, `app/meta_analysis/legacy/**`, `archive/legacy_sources/**`, and branch-discovered historical implementation areas. It is not a current capability claim.

Classification used:

| Evidence class | Meaning |
| --- | --- |
| Current | Present in current non-legacy source and supported by current tests or recent current-line reports. |
| Branch evidence | Present on a local branch by file/log evidence only. Not proven in current UI. |
| Legacy tests only | Present under `legacy/` or `archive/legacy_sources/**` with historical tests/docs. Not current runtime evidence. |
| Deprecated | Historical, placeholder, mock, no-op, fake preflight, or old shell path that should not be migrated directly. |

## Bioinformatics Current Non-Legacy Feature Areas

| Feature area | Current files | Description | Evidence | Production claim allowed? |
| --- | --- | --- | --- | --- |
| Recognition / standardization / resolver | `project_recognition.py`, `project_standardization.py`, `standardized_asset_selection.py`, `analysis_inputs/**`, `deg_ready/**` | Current input contract layer for downstream analysis | Current source and tests | No; input contract only |
| Controlled formal DEG | `deg_engine/formal_runner.py`, `parameter_gate.py`, `result_schema.py`, `python_backend.py`, `runtime_validation.py` | Controlled DEG execution and result schema gates | Current tests under `tests/bioinformatics/test_formal_*`, `test_deg_*` | No clinical/public production claim |
| Multi-factor DEG | `deg_engine/multifactor_*`, `multifactor_r_runner.py` | Controlled multi-factor schema, confirmation, R fixture runners | Current tests under `test_multifactor_deg_*` | Controlled only |
| DEG hardening gates | `input_adaptation.py`, `design_quality.py`, `data_quality.py`, `method_recommendation.py`, `audit_package.py`, `cross_project_acceptance.py` | Real project adaptation, design/data quality, method recommendation, audit package | Current tests under `test_deg_*_gate.py` | Candidate only |
| ORA/GSEA enrichment | flat `enrichment_*`, `gene_set_resources.py`, `services/enrichment_*` | Controlled ORA/GSEA input/resource/result/review/plot/report/audit gates | Current tests under `test_enrichment_*` | MVP/research only |
| Survival / Cox | `survival_clinical/**`, `clinical_analysis/**`, `plots/survival.py`, `plots/cox.py` | Controlled KM/log-rank and Cox univariate; partial multivariate design/runtime history | Current tests under survival/cox names | Statistical research only |
| Risk score | `survival_clinical/risk_score_*` on some branch/current inventories | Controlled risk score gates and review candidates | Branch/current file evidence varies; not rerun here | Not clinical risk system |
| Plot artifacts | `plots/basic_renderers.py`, `formal_deg.py`, `survival.py`, `cox.py`, `schema.py`, `registry.py` | SVG/spec-driven plot artifacts for supported current analysis results | Current plot tests | Not a full plotting platform |
| Report/export packages | `reports/formal_deg.py`, `reports/export_package.py`, `reports/readiness.py`, `reports/project_report_builder.py` | Section/package report gates and export packages | Current report tests | Statistical package only, no clinical conclusion |
| Analysis runtime mock bridge | `app/analysis_runtime/**`, `analysis/**` | Mock-mode standard result package bridge | Current recent commits and tests | Mock only; not full R analysis execution |

## Bioinformatics Legacy Catalog

| Feature area | Source files | Description | Evidence | Current equivalent | Status |
| --- | --- | --- | --- | --- | --- |
| GEO desktop tool | `app/bioinformatics/legacy/geo_tool/**`, `archive/legacy_sources/bioinformatics_project/geo_tool/**` | Standalone GEO GUI, query helpers, MeSH term helpers, workflow wrappers | Legacy README and tests | Current Bio UI plus search/recognition/standardization/resolver | Deprecated as runtime; reference only |
| GEO pipeline and processors | `legacy/geo_pipeline/**`, `legacy/geo_processing/**`, archive copies | Download/process GEO SOFT, detector, matrix classifier, validators | Legacy tests such as `test_geo_downloader`, `test_geo_detector` | Current `search_center`, `download`, `project_recognition`, `analysis_inputs` | Adapter/rewrite only |
| Module 3 sandbox | `legacy/ui/**` | Sandbox formatting/UI for data assets | Legacy tests | Current standardized assets and Analysis Center | UI material only |
| TCGA/GTEx facade | `legacy/tcga_gtex/**` | Query/adapters/facade/lexicon for TCGA/GTEx | Legacy tests and docs | Current `data_sources`, `tcga`, `standard_assets` | Rewrite/reference only |
| Literature CLI/GUI | `legacy/literature_cli.py`, `legacy/literature_gui.py` | Old literature utilities kept with GEO snapshot | Legacy README boundary warning | Current Meta owns literature workflows | Deprecated for Bio |
| Legacy GEO scripts | `download_geo_full_only.py`, `process_geo_family_soft.py`, `download_supplement_and_sra.py` | Compatibility download/process scripts | Legacy README and archive duplicate | Current downloader/recognition services | Deprecated/direct-use forbidden |
| Lexicon resources | `legacy/tcga_gtex/lexicon/**`, `configs/rules/**` | Chinese/English medical term resources and source mappings | Legacy coverage audit files | Shared vocabulary/search center | Reuse only as governed resources |
| Legacy test harness | `legacy/tests/**`, `scripts/run_smoke_tests.py` | Old unittest gates | Legacy only | Current `tests/bioinformatics` | Do not count as current tests |

## Meta Analysis Current Non-Legacy Feature Areas

| Feature area | Current files | Description | Evidence | Production claim allowed? |
| --- | --- | --- | --- | --- |
| Protocol/search/literature import | `pages/protocol_page.py`, `search/**`, `services/literature_*` | Current systematic review setup, PubMed/search, import | Current tests under `tests/meta_analysis` | Developer/internal level unless separately proven |
| Dedup/screening/fulltext/extraction/quality | `pages/*`, `services/*`, `models/*` | Current workflow services and pages | Current test suite includes stage and service tests | Not full production claim |
| Meta statistics v2 | `services/meta_statistics_engine_service.py`, `stats/**` | Current v2 statistics run | Current tests `test_meta_statistics_engine_v2.py` | Current proof is focused, not full production |
| Result contract bridge | `services/meta_result_contract_adapter.py`, `pages/analysis_page.py` | One v2 run can drive table, forest plot, and testing markdown artifact with one hash | Current Phase 3/4 tests | Do not claim full Meta L3 beyond focused proof |
| Figure/table/export services | `figure_result_service.py`, `publication_export_service.py`, `formal_report_service.py` | Forest/table/export artifact services | Current tests | Testing-level report/export unless gated |
| Workflow dashboard | `pages/workflow_dashboard_page.py` | Current workflow status discovery | Current UI tests | Status UI only |

## Meta Analysis Legacy Catalog

| Feature area | Source files | Description | Evidence | Current equivalent | Status |
| --- | --- | --- | --- | --- | --- |
| Old workbench shell | `app/meta_analysis/legacy/app/**`, `app_meta/**`, archive `model9/app/**` | Standalone PySide workbench/dashboard/sidebar/pages | Legacy tests and docs | Current `app/meta_analysis/pages/**` and `workflow_pages.py` | Deprecated as runtime; UI reference only |
| Literature import/dedup/screening | `legacy/literature/**` | RIS/NBIB/CSV parsing, dedup, screening services | Legacy tests | Current literature import, library, dedup, screening services | Mostly superseded |
| Extraction rules | `legacy/extraction/**` | Rule models/store/service | Legacy tests | Current extraction schema registry/form/validation services | Reference only |
| Fulltext and bias services | `legacy/fulltext/**`, `legacy/bias/**` | Fulltext store/service and bias service | Legacy tests | Current fulltext, eligibility, quality services | Adapter/rewrite only |
| Reporting service | `legacy/reporting/**` | Reporting/profile readiness services | Legacy tests | Current reporting, formal report, publication export services | Adapter/rewrite only |
| Analysis profiles and task runner | `legacy/analysis_profiles/**`, `legacy/core/task_*` | Profile config, task lifecycle, no-op/manual runner foundation | Legacy README dry-run/no-op boundaries | Current task/result contracts only if reimplemented | Conceptual reference only |
| Fake GEO readiness / DEG | `legacy/geo_readiness/**`, `legacy/analysis/deg_ready_matrix.py`, archive copies | Fake/controlled GEO readiness and DEG-ready reports inside Meta snapshot | Legacy README labels fake preflight and metadata-only | Current Bioinformatics owns GEO/DEG | Deprecated for Meta current runtime |
| Legacy icons/assets | `legacy/assets/**` | Icons, contact sheets, app icons | File inventory | Current UI shell assets and design docs | Reuse only through design review |
| Legacy package scripts | `legacy/packaging/**`, `legacy/scripts/**` | Standalone packaging/dev checks | Legacy docs | Current root `scripts/package_app.py` | Deprecated for current app packaging |

## Branch-Only Feature Catalog

| Feature area | Source branch | Files/areas | Description | Evidence | Current equivalent/status |
| --- | --- | --- | --- | --- | --- |
| Structured R DEG adapters | `dev/release-internal-test`, `codex/releasebuild-formal-deg-carryover` | `deg_engine/rscript_adapter.py`, `r_limma_*`, `r_deseq2_*`, `r_edger_*` | limma/DESeq2/edgeR runtime planning/validation/adapters | Branch file evidence | Current has multi-factor R runner files; branch structure may be richer |
| Packaged ORA/GSEA modules | `dev/release-internal-test` | `app/bioinformatics/enrichment/**`, `gsea/**` | Structured package layout for ORA/GSEA gates | Branch file evidence | Current has flat enrichment modules; adapter/rewrite candidate |
| Real SVG plot split | `dev/release-internal-test` | `plots/real_svg.py`, `plots/ora.py`, `plots/gsea.py`, `plots/survival_real.py` | Broader plot renderer split | Branch file evidence | Current has formal DEG/survival/cox/basic renderer modules; parity unverified |
| Integrated report renderer policy | `dev/release-internal-test` | `reports/integrated.py`, `renderer_capability.py`, `renderer_runtime_policy.py` | Renderer capability and runtime policy | Branch evidence | Current report/export modules exist; exact parity unverified |
| Risk score / nomogram / calibration / DCA | `codex/releasebuild-formal-deg-carryover`, `dev/release-internal-test` | `risk_score_*`, calibration/DCA docs/tests by branch evidence | Risk score and advanced clinical visualization gates | Branch/current mixed evidence | Must remain non-clinical and gated if revisited |
| Meta OCR fulltext | `dev/meta-analysis` | `fulltext/image_ocr_worker.py`, `pdf_ocr_worker.py`, `ocr_runtime_service.py`, `paddleocr_subprocess_runner.py` | OCR worker/runtime/package history | Branch file and test evidence | Not current-proven; future adapter only |
| UI shell/icon/result export surfaces | `dev/ui-shell`, `integration/release-ui-shell-scoped-migration` | `docs/ui/**`, `app/shared/ui_components/**`, screenshot assets | UI design and shell material | Branch evidence | Design reference only; not analysis runtime |

## Deprecated Legacy Register Cross-Reference

Hard-deprecated items are listed in `docs/reports/DEPRECATED_LEGACY_REGISTER.md`. This catalog intentionally does not recommend direct use of old standalone workbenches, fake GEO preflight, no-op runners, old package scripts, or placeholder reporting.
