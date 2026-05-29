# UI Feature Entry Map

Date: 2026-05-29

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Branch: `dev/bioinformatics`

HEAD audited: `0ea88c15520165b70299d715ef2645dcb79dee2b`

Scope: Phase 1 of `SOFTWARE_REMEDIATION_PLAN_UI_AND_ANALYSIS_L3.md`.

Classification:

| Class | Meaning |
| --- | --- |
| A | Current UI has an entry and real lower-level capability exists; missing UI L3 proof. |
| B | Current UI has an entry and partial capability exists; adapter/result-contract work is needed. |
| C | Current UI has an entry but lower-level capability is missing or only preflight/testing. |
| D | Current UI entry exists but source is legacy/deprecated/untrusted for formal completion. |
| E | Old code has capability but current UI has no verified entry; do not migrate in Phase 1. |

## Bioinformatics Entries

| Module | Current page | Button / entry | Handler | Service / API | Expected behavior | Current status | Real output? | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Bioinformatics | Data Source | Generate GSE plan | `BioinformaticsDataSourceWidget.generate_gse_plan` | acquisition/data source services | Create a source request or plan from GSE input | Current UI entry exists | Plan/artifact output, not analysis result | B: upstream input path only |
| Bioinformatics | Data Source | Search GSE dataset | `search_gse_dataset` | GEO search/profile services | Retrieve candidate dataset metadata | Current UI entry exists | Candidate metadata | B: not an analysis loop |
| Bioinformatics | Data Source | Register local paths | `register_local_paths` | local data source registration | Register real local matrix/clinical files | Current UI entry exists | Registered project source | A/B: likely L3 input source, still needs downstream proof |
| Bioinformatics | TCGA/GTEx cards | Download/build expression/clinical | `download_tcga_raw_files`, `build_tcga_expression_matrix`, `fetch_tcga_clinical_metadata`, `download_gtex_raw_files`, `build_gtex_expression_matrix` | TCGA/GTEx data-source services | Build standardized assets from public sources | Current UI entry exists | Download/build artifacts | B: input preparation, not analysis result |
| Bioinformatics | Recognition | Run recognition | `BioinformaticsRecognitionWidget.run_recognition` | recognition/report services | Recognize candidate files/assets | Current UI entry exists | Recognition report | B: asset recognition only |
| Bioinformatics | Readiness | Run readiness check | `BioinformaticsReadinessDashboardWidget.run_readiness_check` | readiness services | Validate dataset readiness and missing information | Current UI entry exists | Readiness artifacts | B: gate/preflight only |
| Bioinformatics | Standardized Assets | Generate assets | `BioinformaticsStandardizedAssetsWidget.generate_assets` | standardized asset services | Build standardized asset repository | Current UI entry exists | Standardized asset artifacts | A/B: required upstream for L3 |
| Bioinformatics | Standardized Assets | Confirm expression/species/gene/group candidates | `confirm_expression_candidate`, `confirm_species_candidate`, `confirm_gene_id_type`, `confirm_group_candidate` | standardized asset confirmation services | Confirm user-selected standardized inputs | Current UI entry exists | Confirmation manifests | A/B: required upstream for L3 |
| Bioinformatics | Analysis Task Center | Confirm formal DEG parameters | formal DEG confirmation controls in `workflow_pages.py` | `app.bioinformatics.analysis_ui.state`, `action_rules`, DEG parameter/confirmation gates | Confirm comparison, thresholds, method, dependency snapshot | Current UI entry exists | Parameter confirmation if gates pass | A: no complete UI L3 run proof |
| Bioinformatics | Analysis Task Center | Run formal DEG | formal DEG action in `workflow_pages.py` | `app.bioinformatics.deg_engine.formal_runner.run_formal_deg` through current gate state | Run controlled formal DEG and write result index v2 | Backend/CLI evidence exists | Real result table/log/index from backend; UI path not proven | A: closest Bio L3 candidate |
| Bioinformatics | Results Browser | Export DEG TSV/CSV | `export_formal_deg_review_tsv`, `export_formal_deg_review_csv` | `export_formal_deg_review_table` | Export formal DEG review table | Current UI entry exists | Table export from result index | A: requires prior formal result |
| Bioinformatics | Results Browser | Generate formal DEG plot artifact | `generate_formal_deg_plot_artifact` | `create_formal_deg_plot_artifact` | Generate real SVG plot from formal DEG result | Current UI entry exists | Real SVG artifact if source result exists | A: requires formal source result |
| Bioinformatics | Results Browser | Generate formal DEG report-ready package | `generate_formal_deg_report_ready_package` | `create_formal_deg_report_ready_package` | Generate section report package only if report gate passes | Current UI entry exists | Report package or explicit gate blockers | A: requires result/plot/confirmation/dependency gates |
| Bioinformatics | Simple Differential Expression page | Run DEG preflight | `DifferentialExpressionPage._create_preflight` | differential expression adapter/service | Generate DEG preflight | Current UI entry exists | Preflight only | C: not formal analysis |
| Bioinformatics | Simple Enrichment page | Run enrichment preflight | `EnrichmentPage._create_preflight` | enrichment adapter/service | Generate enrichment preflight | Current UI entry exists | Preflight only | C: not formal ORA/GSEA loop |
| Bioinformatics | Simple Correlation page | Run correlation preflight | `CorrelationPage._create_preflight` | correlation adapter/service | Generate correlation preflight | Current UI entry exists | Preflight only | C: not formal analysis |
| Bioinformatics | Simple Survival page | Run survival preflight | `SurvivalPage._create_preflight` | survival adapter/service | Generate survival preflight | Current UI entry exists | Preflight only | C: not formal clinical loop |
| Bioinformatics | Legacy folders | Legacy GEO/TCGA/GEO-tool scripts | None verified as current UI mainline | `app/bioinformatics/legacy/**` | Historical material | Not current UI completion evidence | Not counted | D/E: reference only |

## Meta Analysis Entries

| Module | Current page | Button / entry | Handler | Service / API | Expected behavior | Current status | Real output? | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Meta Analysis | Protocol | Save protocol/search drafts | `ProtocolPage` methods in `workflow_pages.py` | protocol/search strategy builders | Build PICO/search drafts and confirmed protocol | Current UI entry exists | Draft/confirmed protocol artifacts | B: upstream only |
| Meta Analysis | Literature Import | Import | `LiteratureImportPage._run_batch_import` | literature import services | Import citation records | Current UI entry exists | Literature records | B: upstream only |
| Meta Analysis | Screening / Duplicate / Extraction | Prepare queues/save decisions/export extraction records | handlers in `app/meta_analysis/pages/*.py` | screening/extraction services | Produce extraction rows and analysis-ready material | Current UI entry exists | Extraction records | B: required upstream for L3 |
| Meta Analysis | Analysis | Run Analysis preflight | `AnalysisPage._run_preflight` | preflight service | Validate extraction output for analysis | Current UI entry exists | Preflight output | B/C: not full analysis |
| Meta Analysis | Analysis | Generate / confirm analysis plan | `_build_analysis_plan_draft`, `_confirm_analysis_plan` | analysis plan service | Create and confirm plan before statistics | Current UI entry exists | Plan manifest | B: required upstream |
| Meta Analysis | Analysis | Run statistics analysis | `_run_statistics_v2` | `MetaStatisticsEngineService.run_statistics` | Run real v2 statistics and write run/result/manifest/log | Current UI entry exists | Real statistics output | B: result contract not unified with figure/report |
| Meta Analysis | Analysis | Build analysis-ready dataset | `_build_dataset` | `AnalysisDatasetService` / `AnalysisRunService` path | Build older analysis-ready dataset | Current UI entry exists | Dataset artifact | B/D: separate from v2 result contract |
| Meta Analysis | Analysis | Run basic Meta analysis | `_run_meta_analysis` | `AnalysisRunService.run_meta_analysis` | Produce `analysis/analysis_results.json` | Current UI entry exists | Real/testing-level analysis result | B: separate from v2 statistics |
| Meta Analysis | Analysis | Generate forest plot PNG | `_generate_forest_plot` | `FigureResultService.generate_forest_plot` | Render forest plot from `analysis/analysis_results.json` | Current UI entry exists | Real PNG if older result exists | B: not same contract as v2 result |
| Meta Analysis | Analysis | Export result table CSV | `_export_result_table` | `FigureResultService.export_result_table_csv` | Export result table from `analysis/analysis_results.json` | Current UI entry exists | CSV if older result exists | B: not same contract as v2 result |
| Meta Analysis | Reporting | Export testing report summary | `_export_report` | report preflight service | Export test report summary | Current UI entry exists | Testing summary | C: not formal L3 completion |
| Meta Analysis | Reporting | Generate formal Markdown report | `_generate_formal_report` | `FormalMarkdownReportBuilder` / PRISMA services | Generate Markdown report | Current UI entry exists | Report artifact if inputs exist | B/C: must prove same result contract |
| Meta Analysis | Reporting | Export HTML/Word testing report | `_export_html_report`, `_export_word_report` | `PublicationExportService` | Export testing report formats | Current UI entry exists | HTML/DOCX testing report | B/C: testing label and contract gap |
| Meta Analysis | Reporting | Export supplementary/figure/repro packages | `_export_supplementary_exports`, `_export_figure_package`, `_export_reproducibility_package` | `PublicationExportService` | Export package artifacts | Current UI entry exists | Package artifacts | B: must prove same run/result source |
| Meta Analysis | Legacy folders | Older workbench/dashboard/reporting | None verified as current UI mainline | `app/meta_analysis/legacy/**` | Historical material | Not current UI completion evidence | Not counted | D/E: reference only |

## L3 Blockers Identified

| Module | Blocker | Classification |
| --- | --- | --- |
| Bioinformatics | Formal DEG backend can run, but current UI input -> confirmation -> run -> status/log -> table/plot/report path is not proven as one user loop. | A blocker |
| Bioinformatics | Simple analysis pages are mostly preflight/test paths and cannot be promoted as formal L3 completion. | C blocker |
| Bioinformatics | Report package can be gate-blocked; UI must expose exact blockers rather than generating placeholder reports. | A/B blocker |
| Meta Analysis | v2 statistics output and older plot/table services use different result paths/contracts. | B blocker |
| Meta Analysis | Testing report exports exist, but cannot be counted as formal/minimum loop unless tied to the same canonical result and visibly labeled. | B/C blocker |
| Both | Legacy directories contain useful material but also placeholders; direct UI replacement or direct legacy calls are forbidden. | D/E blocker |

## Closest L3 Candidates

| Module | Candidate | Reason |
| --- | --- | --- |
| Bioinformatics | Controlled Formal DEG | Has the strongest current contract stack: standardized input, DEG gates, runtime validation, result index, review, plot artifact, report gate. Needs UI path proof. |
| Meta Analysis | v2 statistics engine with canonical adapter to figure/report services | Real statistics exists, but result contract must be unified before claiming L3. |

## Phase 1 Verdict

Phase 1 map is complete at the audit level. No feature was implemented. The next remediation stage must choose one module and one path only; this document identifies Bioinformatics controlled formal DEG as the closest Bioinformatics L3 candidate, and Meta result-contract unification as the required Meta prerequisite.
