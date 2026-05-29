# Legacy Feature Catalog

Date: 2026-05-29

## Scope

This catalog covers `app/bioinformatics/legacy/**`, `app/meta_analysis/legacy/**`, and branch-discovered historical implementation areas. It is not a current capability claim.

Classification used:

| Evidence class | Meaning |
| --- | --- |
| Current | Present in current non-legacy source and covered by current tests or recent reports. |
| Branch evidence | Present on a local branch by file/log evidence only. Not proven in current UI. |
| Legacy tests only | Present under `legacy/` with historical tests/docs. Not current runtime evidence. |
| Deprecated | Historical or placeholder path that should not be migrated directly. |

## Bioinformatics Legacy Catalog

| Feature area | Source files | Description | Evidence | Current equivalent | Status |
| --- | --- | --- | --- | --- | --- |
| GEO desktop tool | `app/bioinformatics/legacy/geo_tool/**` | Standalone GEO GUI, query, workflow wrappers, MeSH term helpers | Legacy README and tests | Current Bio UI pages plus recognition/standardization/resolver | Deprecated as runtime; reference only |
| GEO pipeline | `app/bioinformatics/legacy/geo_pipeline/**`, `geo_processing/**` | Download/process GEO Family SOFT, detection, matrix classifier, validators | Legacy tests such as `test_geo_downloader`, `test_geo_detector` | Current `search_center`, `download`, `project_recognition`, `analysis_inputs` | Adapter/rewrite only |
| Module 3 sandbox | `app/bioinformatics/legacy/ui/**` | Sandbox formatting/UI for data assets | Legacy tests | Current standardized assets and Analysis Center | UI material only |
| TCGA/GTEx facade | `app/bioinformatics/legacy/tcga_gtex/**` | Query/adapters/facade/lexicon for TCGA/GTEx | Legacy tests and README boundary warning | Current `data_sources`, `tcga`, `standard_assets` | Reference; no direct migration |
| Literature CLI/GUI | `app/bioinformatics/legacy/literature_cli.py`, `literature_gui.py` | Old literature utilities kept with GEO snapshot | Legacy README explicitly excludes from current Bio boundary | Current Meta owns literature workflows | Deprecated for Bio |
| Legacy GEO scripts | `download_geo_full_only.py`, `process_geo_family_soft.py`, `download_supplement_and_sra.py` | Compatibility download/process scripts | Legacy README says compatibility only | Current downloader/recognition services | Deprecated/direct-use forbidden |
| Lexicon resources | `legacy/tcga_gtex/lexicon/**`, `configs/rules/**` | Chinese/English medical term resources and source mappings | Legacy coverage audit files | Shared vocabulary/search center | Reuse as resource only after governance |
| Legacy test harness | `app/bioinformatics/legacy/tests/**`, `scripts/run_smoke_tests.py` | Old unittest gates | Legacy only | Current `tests/bioinformatics` | Do not count as current tests |

## Meta Analysis Legacy Catalog

| Feature area | Source files | Description | Evidence | Current equivalent | Status |
| --- | --- | --- | --- | --- | --- |
| Old workbench shell | `app/meta_analysis/legacy/app/**`, `app_meta/**` | Standalone PySide workbench/dashboard/sidebar/pages | Legacy tests and docs | Current `app/meta_analysis/pages/**` and `workflow_pages.py` | UI reference only |
| Literature import/dedup/screening | `legacy/literature/**` | RIS/NBIB/CSV parsing, dedup, screening services | Legacy tests | Current literature import, library, dedup, screening services | Mostly superseded |
| Extraction rule services | `legacy/extraction/**` | Rule models/store/service | Legacy tests | Current extraction schema registry/form/validation services | Reference only |
| Fulltext and bias services | `legacy/fulltext/**`, `legacy/bias/**` | Fulltext store/service and bias service | Legacy tests | Current fulltext, eligibility, quality services | Adapter/rewrite only |
| Reporting service | `legacy/reporting/**` | Reporting/profile readiness services | Legacy tests | Current reporting, formal report, publication export services | Reference only |
| Analysis profiles and task runner | `legacy/analysis_profiles/**`, `legacy/core/task_*` | Profile config, task lifecycle, no-op and manual runner foundation | Legacy README explicitly dry-run/no-op boundaries | Current task services and Meta result contract bridge | Conceptual reference only |
| Fake GEO readiness | `legacy/geo_readiness/**`, `legacy/analysis/deg_ready_matrix.py` | Fake/controlled GEO readiness and DEG-ready reports | Legacy README labels fake preflight and metadata-only | Current Bioinformatics owns GEO/DEG | Deprecated for Meta current runtime |
| Legacy icons/assets | `legacy/assets/**` | Icon sets, contact sheets, app icons | File inventory | Current UI shell assets | Reuse only through design review |
| Legacy package scripts | `legacy/packaging/**`, `legacy/scripts/**` | Standalone packaging/dev checks | Legacy docs | Current package scripts | Deprecated for current app packaging |

## Branch-Only Feature Catalog

| Feature area | Source branch | Files/areas | Description | Evidence | Current equivalent/status |
| --- | --- | --- | --- | --- | --- |
| R DEG backends | `dev/release-internal-test` | `deg_engine/rscript_adapter.py`, `r_limma_*`, `r_deseq2_*`, `r_edger_*` | limma/DESeq2/edgeR runtime planning/validation/adapters | Branch file/log evidence | Current branch has multi-factor R runner and tests; branch structure may be richer |
| Enrichment production gates | `dev/release-internal-test`, `codex/mainline-survival-clinical-carryover` | `app/bioinformatics/enrichment/**`, `gsea/**`, `plots/ora.py`, `plots/gsea.py` | ORA/GSEA resource/result/report/plot gates | Branch evidence | Current branch has flat enrichment modules and tests |
| Integrated reports/renderers | `dev/release-internal-test` | `reports/integrated.py`, `renderer_capability.py`, `renderer_runtime_policy.py` | Integrated report and renderer policy | Branch evidence | Current branch has report/export modules; exact parity unverified |
| Risk score/nomogram gates | `codex/releasebuild-formal-deg-carryover` | Risk score/report-ready/calibration/DCA commits | Controlled risk score and plot/report gates | Commit evidence only | Current branch has risk-related historical work not audited here |
| Meta OCR fulltext | `dev/meta-analysis` | PaddleOCR worker/runner/package commits | OCR/fulltext integration | Commit evidence only | Not current Meta L3 proof |
| Meta workflow UI | `codex/meta-workflow-ui`, `codex/meta-analysis-refresh` | Meta pages/workflow UI | Old UI later-stage integration | Branch evidence | Current Meta pages supersede most of it |
| GEO search/download UI | `codex/bio-search-ui-main`, `codex/bio-ui-download-integration`, `codex/bio-geo-real-download-test` | GEO page profile/search/download recognition | GEO search/profile/download refinements | Branch evidence | Current Bio search/recognition services are newer |
| Shared AI gateway | `dev/ai-gateway`, `codex/integration-meta-ocr-labtools-carryover` | Shared gateway/provider commits | AI routing and draft isolation | Branch evidence | Out of analysis migration scope |

## Deprecated Legacy Register Cross-Reference

Hard-deprecated items are listed in `docs/reports/DEPRECATED_LEGACY_REGISTER.md`. This catalog intentionally does not recommend direct use of legacy runners, fake GEO preflight, old standalone workbench, or old report placeholders.

