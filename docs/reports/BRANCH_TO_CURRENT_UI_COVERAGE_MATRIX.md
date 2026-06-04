# Branch To Current UI Coverage Matrix

Date: 2026-06-04

Baseline: `dev/bioinformatics` at `ccf7967609a283cddfbb83bdf6d68ceb7bc12b63`

## Rule

The current UI is the only mainline. A branch feature is not available merely because matching code exists elsewhere. This matrix records whether historical material maps to a current page/button and whether the current implementation has evidence of real output.

## Bioinformatics UI Coverage

| Current UI area / button family | Current files | Current behavior/evidence | Related old branches / legacy | Coverage status | Migration action |
| --- | --- | --- | --- | --- | --- |
| Module entry / Bio project home | `app/bioinformatics/project_home.py`, `workflow_pages.py`, `tests/ui/test_bioinformatics_project_home.py` | Current UI exists; project workspace validation and page navigation tests exist by inventory | Early wizard branches | Covered current | Reuse current |
| Data source search / GEO / TCGA / GTEx cards | `workflow_pages.py`, `search_center/**`, `data_sources/**`, `download/**` | Current services and UI tests exist; some searches/downloads are gated/testing-level | `codex/bio-geo-real-download-test`, bio search UI branches, legacy GEO/TCGA/GTEx | Partly covered current | Adapter only for selected helpers |
| Recognition / readiness / standardization | `project_recognition.py`, `project_readiness.py`, `project_standardization.py`, `analysis_inputs/**`, `workflow_pages.py` | Current contract layer exists; used by downstream gates | Legacy GEO detector, asset contracts | Covered current | Reuse current; do not bypass resolver |
| Analysis Center / DEG gates | `analysis_ui/**`, `deg_ready/**`, `deg_engine/**`, `workflow_pages.py` | Current gate state exists; formal DEG/multifactor DEG paths are gated | ReleaseBuild DEG branches, `stable/mainline` | Covered but gated | Reuse/adapt branch engine pieces only through gates |
| Formal DEG run/review/export | `deg_engine/formal_runner.py`, `result_review.py`, `plots/formal_deg.py`, `reports/formal_deg.py` | Prior L3 proof exists in current reports/tests; not rerun here | ReleaseBuild DEG carry-over | Covered current for controlled DEG | Reuse |
| limma/DESeq2/edgeR controls | `deg_engine/multifactor_r_runner.py`, `dependency_check.py`, UI gates | Current controlled runner/gate material exists; runtime is external/detect-first | ReleaseBuild R adapter branches | Partly covered | Adapter; no direct branch merge |
| ORA/GSEA enrichment | current `enrichment_*`, `gene_set_resources.py`, `enrichment_r_adapter.py` | Current flat modules exist with gates/results/plot/report history; not rerun here | ReleaseBuild structured `enrichment/**`, `gsea/**` | Partly covered | Adapter/rewrite to current flat/contracts |
| Plot artifacts | `plots/**`, Results Browser in `workflow_pages.py` | Real SVG artifacts exist for supported gated sources; not a full plot platform | ReleaseBuild plot split | Covered for selected outputs | Adapter style/system only |
| Report/export | `reports/**`, report viewer/gates in `workflow_pages.py` | Section/full-package and renderer gate history exists; no clinical conclusion | ReleaseBuild report/renderer branches | Partly covered | Adapter with current report-ready gates |
| Survival / Cox | `survival_clinical/**`, `plots/survival.py`, `plots/cox.py` | Controlled statistical paths exist; clinical report-ready remains restricted | survival clinical carry-over branch | Covered but strictly gated | Reuse with clinical boundary |
| Risk score / nomogram / calibration / DCA | mixed current/branch evidence | Not production-current; clinical interpretation restricted | ReleaseBuild/internal-test branches | Not fully covered | Rewrite only after selected scope |
| Immune infiltration | `immune_infiltration/**`, `analysis/modules/immune_infiltration/**` | Current scoring and lite worker scaffold exist; proof not rerun here | ReleaseBuild/current branches | Partly covered | Reuse with focused proof |
| Standard analysis worker/package catalog | `app/analysis_runtime/**`, `analysis/**` | Current mock/lite scaffolds, external R command boundary, package catalog, and docking lite command-manifest contract exist | Not old-branch driven | Scaffold covered | Keep labeled testing/lite until selected proof |
| Legacy GEO check/settings | `workflow_pages.py`, legacy adapters | UI can expose environment/status style checks, but legacy execution cannot become formal analysis | `app/bioinformatics/legacy/**` | Quarantined | Deprecated/adapter only |

## Meta Analysis UI Coverage

| Current UI area / button family | Current files | Current behavior/evidence | Related old branches / legacy | Coverage status | Migration action |
| --- | --- | --- | --- | --- | --- |
| Meta protocol / PICO / search strategy | `pages/protocol_page.py`, `search/**`, UI tests | Current draft, confirmation, PubMed execution/import tests exist | `codex/meta-search-ui-main`, old workbench | Covered current for PubMed/drafts | Reuse current |
| Literature import | `pages/literature_import_page.py`, services | Current import diagnostics/warnings paths exist | old Meta workbench | Covered current for tested paths | Reuse |
| Duplicate review | `pages/duplicate_review_page.py`, services | Current duplicate review queue and dedup generation UI exists | old workbench | Covered current for tested paths | Reuse |
| Screening/fulltext workflow dashboard | `pages/workflow_dashboard_page.py`, fulltext services | Current dashboard reports status and fallbacks; not all outputs are L3-proven | `dev/meta-analysis` OCR/fulltext | Partly covered | Adapter later |
| Meta analysis run | `pages/analysis_page.py`, `services/meta_statistics_engine_service.py` | Current v2 statistics run exists; result is testing-level and not production-grade | `feature/meta-l3-ui-loop`, old analysis stack | Covered current for L3 proof path | Reuse |
| Meta canonical artifacts | `services/meta_result_contract_adapter.py`, `tests/ui/test_meta_analysis_l3_loop.py` | Current proof creates result table, forest plot PNG, and markdown report artifact sharing run/hash; still testing-level | Phase 3/4 branches | Covered current as testing-level | Reuse |
| Older figure/result table path | `analysis_run_service.py`, `figure_result_service.py` | Existing tests by inventory; can create PNG/CSV, but some paths are separate from v2 contract | old Meta branches | Partly covered | Adapter to canonical run/hash |
| Reporting/export | `pages/reporting_page.py`, `services/publication_export_service.py`, `formal_report_service.py` | Testing report/export path exists; not production/clinical | old reporting widgets | Partly covered | Adapter to canonical contract |
| OCR/fulltext | `dev/meta-analysis`, current fulltext pages/services | Branch has extra OCR/fulltext history; current proof not refreshed | `dev/meta-analysis`, OCR branch | Not fully covered | Rewrite/adapter later |
| Legacy dashboard/sidebar | `app/meta_analysis/legacy/app/**`, `app_meta/**` | No current mainline mapping | old Meta workbench | Not covered | Deprecated |

## Branch Coverage Summary

| Branch/source | UI features that map to current pages | Output evidence classification | Coverage decision |
| --- | --- | --- | --- |
| `dev/bioinformatics` | Bio project flow, Analysis Center, Results Browser, report/export gates, Meta pages, standard analysis package catalog | Current implementation evidence; not all rerun in this audit | Mainline |
| `dev/release-internal-test` | DEG/enrichment/survival/risk/report candidates map conceptually to current Bio pages | Branch-only evidence; current layout diverges and would delete current scaffold paths | Candidate library |
| `codex/releasebuild-formal-deg-carryover` | DEG/runtime/report gates map to Analysis Center/Results Browser | Branch-only; older contracts | Candidate library |
| `codex/mainline-survival-clinical-carryover` | Survival/Cox rows map to current survival clinical UI | Branch-only | Candidate library |
| `stable/mainline` | Formal DEG baseline maps to current DEG area | Historical | Baseline reference |
| `feature/meta-l3-ui-loop` | Meta Analysis page canonical artifact proof maps to current Meta UI | Already in current history | Reference |
| `dev/meta-analysis` | OCR/fulltext/package material maps partly to Meta pages | Branch-only | Candidate library |
| `dev/ui-shell` / integration UI branches | Design and shell material maps broadly to UI shell | Visual/design only | UI reference |
| `app/bioinformatics/legacy/**` | GEO/TCGA/GTEx/literature ideas map conceptually to current data/search pages | Legacy-only | Deprecated or adapter |
| `app/meta_analysis/legacy/**` | Old Meta workbench maps conceptually but not structurally | Legacy-only | Deprecated/reference |
| `archive/legacy_sources/**` | Mirrors older Bio/Meta source trees | Archive-only | Reference/deprecated |

## Matrix Conclusion

Current UI coverage is strongest for controlled Bio DEG and current Meta v2 testing-level L3 proof paths. Enrichment, survival/Cox, reports, standard workers, and several resource gates have current or branch material, but they must remain governed by current contracts. Old branches fill a migration backlog, not a replacement UI.
