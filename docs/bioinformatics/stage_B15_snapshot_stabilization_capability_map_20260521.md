# Bioinformatics B15 Snapshot Stabilization / Capability Map

Date: 2026-05-21

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Branch: `dev/bioinformatics`

HEAD at audit start: `0e340cf`

## Scope

This stage freezes the current Bioinformatics analysis snapshot and records a capability map for post-closure development. It does not add a new runner, does not enable a new formal analysis path, does not change packaging, and does not promote legacy outputs into formal results.

The governing rule for B15-B22 remains:

- legacy code can only be absorbed through audit -> contract -> gate -> adapter.
- legacy runners cannot directly write `formal_computed_result`.
- all new functions stay disabled until their gates pass.
- result index v2 can only be extended additively.
- UI wording must continue to separate formal, controlled, preflight, exploratory, imported, testing, and legacy states.
- `project_storage/`, old handoff reports, and downloaded validation data remain excluded from commits.

Untracked files intentionally excluded from this stage:

- `docs/bioinformatics/Bioinformatics_handoff_report_20260513.md`
- `project_storage/bioinformatics/`

## Current Branch Observations

The current Bioinformatics worktree is not identical to the later ReleaseBuild candidate described in downstream carry-over notes. In this branch:

- Formal DEG B9 files are present under `app/bioinformatics/deg_engine`, `plots`, `reports`, `results`, and `analysis_ui`.
- B12-B14 survival/clinical controlled KM/log-rank and Cox univariate files are present under `app/bioinformatics/survival_clinical`.
- GSEA resource management is present through `app/bioinformatics/gene_set_resources.py`.
- ORA/GSEA formal controlled runtime packages are not present as dedicated `app/bioinformatics/enrichment` or `app/bioinformatics/gsea` modules in this worktree.
- Existing ORA/enrichment and GSEA surfaces in this branch are primarily preflight/resource/readiness services and UI copy.

This divergence is a planning concern, not a reason to copy ReleaseBuild files directly. B16-B22 must first decide whether to receive later ORA/GSEA work through scoped carry-over or rebuild it against the current branch contracts.

## Capability Matrix

| Capability | Status | Input source | Result semantics | Result index status | Plot status | Report status | UI state | Carry-over status | Unsupported boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Formal DEG | formal MVP | B8 standardized repository / analysis input resolver / DEG-ready package | `formal_computed_result` only after gates pass | v2 registration present | formal DEG plot artifact/spec registration present; full renderer remains future work | formal DEG section/package gate present | gated formal action and disabled reasons shown | implemented in this branch | not limma, DESeq2, edgeR, R backend, multi-factor, batch-aware design |
| Imported DEG review | imported/external review | imported result asset and result browser | `imported_external_result` or conservative migrated semantics | conservative migration / registry support | not a BioMedPilot formal recomputed plot source | excluded from formal report-ready unless explicit allowed mode | visible as imported/external | implemented | cannot be upgraded to formal computed result |
| Controlled ORA | not developed in this branch | DEG result candidate / gene list preflight only | no formal ORA semantics in this worktree | no dedicated ORA result schema/index path found | no controlled ORA formal plot module found | no ORA section package module found | enrichment row/copy remains preflight/config oriented | requires B10/B11 scoped carry-over or rebuild | no formal ORA executor in current branch |
| Controlled preranked GSEA | preflight/resource only in this branch | local GMT selection via gene set resource manager | preflight/resource readiness only | no dedicated GSEA result schema/index path found | no controlled GSEA plot module found | no GSEA section package module found | formal GSEA action remains disabled/hidden | requires B11 scoped carry-over or rebuild | no formal GSEA executor; no pathway conclusion |
| KM/log-rank | controlled MVP | B12 survival/clinical package plus B13 gates | `formal_computed_result` only after KM gates pass | v2 registration present for `survival_km_logrank` | KM plot artifact is spec-only; `image_artifacts=[]` | `report_ready_eligible=False` | two-group KM/log-rank action gate-driven | implemented in this branch | no clinical conclusion, no risk grouping, no report-ready |
| Cox univariate | controlled MVP | B12 survival/clinical package plus B14 gates | `formal_computed_result` only after Cox gates pass | v2 registration present for `cox_univariate` | Cox forest plot artifact is spec-only; `image_artifacts=[]` | `report_ready_eligible=False` | single-variable Cox action gate-driven | implemented in this branch | no multivariate Cox, no risk score, no PH diagnostics claim |
| Cox multivariate design audit | design audit | B12 clinical variables and outcome preflight | design/preflight only | no formal result registration | none | disabled | disabled/design-only row | implemented as audit only | no adjusted HR, no variable selection, no multivariate p-value |
| Plot artifacts/spec | partial controlled artifact layer | result index output artifacts | inherits source result semantics | plot artifact registry/schema present | DEG/KM/Cox specs; survival/Cox spec-only; no full static renderer activation | plots do not imply report-ready | result/plot preview rows | implemented as guarded artifact/spec layer | no broad PNG/SVG/PDF rendering engine yet |
| Section-only report package | partial formal DEG | result index v2, formal DEG result, gate snapshot | formal DEG only when gate passes | report artifacts registered for formal DEG package | accepts gated DEG plot artifact or explicit no-plot mode | formal DEG section/package only | report-ready export gated | implemented for formal DEG | no integrated report; no survival/clinical report-ready |
| Project report builder | preflight/draft | project readiness, recognition, preflight, imported summaries | draft/preflight only | not a formal analysis result | none | draft summary only | report viewer/draft context | implemented legacy-compatible draft | not publication-ready, not formal integrated report |
| Immune / TME score | exploratory | standardized expression / built-in signatures | exploratory/testing-level score | not formal downstream result | exploratory preview only | draft only | separated as exploratory | implemented exploratory | not deconvolution, no clinical conclusion, no DEG/GSEA/KM/Cox |
| Legacy recognition/acquisition assets | legacy-only / candidate for absorption | legacy GEO / TCGA / GTEx modules and adapters | legacy/preflight only | not formal result index | legacy helpers not formal plot sources | legacy report helpers not report-ready | should remain separate until adapterized | available in tree | cannot bypass B8 resolver |
| Full integrated report | not developed | would require selected gated section results | not applicable | not present | not present | not present | not enabled | future B19 | no cross-analysis interpretation or clinical conclusion |

## Legacy Absorption Inventory

| Legacy asset | Current location | Classification | Absorption path | Boundary |
| --- | --- | --- | --- | --- |
| GEO detector and matrix classifier | `app/bioinformatics/legacy/geo_processing/detector/*` | minimum migration candidate | wrap as acquisition/recognition adapter producing provenance and blockers | no formal analysis input; no direct result index writes |
| GEO search / text query helpers | `app/bioinformatics/legacy/geo_tool/*`, `retrieval/geo_search_service.py` | design reference plus selective migration | route through acquisition manifest and standardized asset registry | no automatic formal DEG/GSEA |
| GEO Series Matrix / SOFT readers | `legacy/geo_processing/module1_readers.py`, `legacy/process_geo_family_soft.py` | minimum migration candidate | adapter contract with checksum, file type, organism, platform, probe mapping hints | no probe collapse without mapping report |
| GEO download validators | `legacy/geo_processing/download_validator.py`, `services/geo_download_service.py` | directly retain after contract audit | acquisition receipt with source version and file checksum | no uncontrolled download-to-analysis shortcut |
| TCGA/GDC preview and download | `data_sources/tcga_preview.py`, `data_sources/tcga_download_executor.py`, `search_center/tcga_gdc_adapter.py` | directly retain with B16 audit | acquisition manifest -> standardized TCGA asset | no TCGA+GTEx merge without batch/design gate |
| TCGA expression builder | `data_sources/tcga_expression_builder.py`, `tcga/expression_importer.py`, `tcga/prepared_package.py` | directly retain with resolver alignment | standardized repository plus analysis input package | raw counts/TPM policy must remain explicit |
| TCGA clinical importer/mapper | `data_sources/tcga_clinical_builder.py`, `tcga/clinical_importer.py` | directly retain with B12 alignment | clinical repository -> survival/clinical preflight package | no automatic KM/Cox/report-ready |
| GTEx preview/download/builders | `data_sources/gtex_preview.py`, `data_sources/gtex_download_executor.py`, `data_sources/gtex_expression_builder.py` | minimum migration candidate | independent standardized GTEx asset with tissue metadata | no default normal-control merge |
| Legacy TCGA/GTEx facade/adapters | `legacy/tcga_gtex/*` | design reference | compare against current data_sources and keep only missing contract-safe behavior | do not restore old facade as runtime authority |
| Medical vocabulary / lexicon | `legacy/tcga_gtex/lexicon/*`, `legacy/geo_tool/*_terms.py` | minimum migration candidate | versioned vocabulary resource with provenance and coverage report | no hidden query expansion that changes analysis scope |
| Matrix parser/normalizer/standardizer | `legacy/tcga_gtex/processing/*` | design reference plus selective migration | standardized asset builder tests and validation reports | no hidden normalization; no silent ID conversion |
| Clinical metadata mapper | `legacy/tcga_gtex/processing/bundle_builder.py`, current TCGA clinical builder | minimum migration candidate | B12 outcome/clinical-variable gate inputs | no clinical conclusion |
| Legacy report/plot helpers | `adapters/bio_report_adapter.py`, `services/bio_report_service.py`, legacy UI helpers | design reference only | keep as draft/report preview source if labeled | prohibited from formal report-ready and formal plot paths |
| Legacy DEG runners | `services/geo_differential_expression_runner.py`, `tcga/deg_runner.py` | prohibited for formal promotion | may remain developer/testing-level only unless fully rebuilt through B8/B9 contracts | cannot emit formal p-value/FDR/result semantics |

## B16-B22 Development Plan

| Stage | Goal | Priority | Entry condition | Output | Regression gate |
| --- | --- | --- | --- | --- | --- |
| B16 Legacy Recognition / Acquisition Absorption | absorb GEO/TCGA/GTEx recognition and acquisition through adapters | high | B15 snapshot accepted; no direct legacy formal path | adapter contracts, tests, B16 audit | B8 resolver and current DEG/KM/Cox tests pass |
| B17 Default Runtime Dependency Activation | make default GUI package dependency checks pass for formal analysis runtime | high | dependency policy updated; packaging risk accepted | runtime dependency audit, package/open-W/codesign evidence | source/package/open-W runtime checks pass |
| B18 Formal Plot Rendering Activation | convert safe plot specs into rendered static images | medium-high | matplotlib policy approved; source-result gates stable | rendered plot artifacts and artifact registration | no preflight/testing/exploratory formal plots |
| B19 Integrated Report Builder | build multi-section report from result index and manifests | medium | DEG/ORA/GSEA section gates stable; plot policy known | integrated report package | no clinical claims; no non-formal sections |
| B20 Survival / Clinical Expansion | extend from KM/Cox MVP to advanced gates | medium | B12-B14 remain green; explicit clinical boundary approved | Cox multivariate gate/executor planning and later implementation | no automatic variable selection or clinical advice |
| B21 R / Bioconductor DEG Planning | plan limma/DESeq2/edgeR as optional R backend | medium-low | Python DEG stable; R runtime policy accepted | R detection/package/script contract docs/tests | no auto-install, no rpy2 hard dependency |
| B22 Full Upstream Harmonization | build cohort-ready standardized repository across GEO/TCGA/GTEx | medium | B16 adapters pass; fixture strategy approved | repository/registry/resolver validation reports | no raw legacy manifest -> formal analysis |

## Current Gaps And Risks

Blocker:

- None for B15 because this is a documentation/audit snapshot stage.

Major:

- Current branch lacks dedicated controlled ORA/GSEA execution modules even though later roadmap text treats ORA/GSEA controlled MVP as part of the desired post-closure baseline. Before B18/B19, decide whether to scoped carry-over B10/B11 from the candidate branch or rebuild ORA/GSEA against the current contracts.
- Default GUI runtime dependency packaging is not closed for all formal-analysis dependencies; B17 must avoid breaking PySide6/package launch.
- Legacy GEO/TCGA/GTEx code remains broad and useful, but only parts should be migrated. Directly restoring legacy facades would bypass the B8 resolver boundary.

Minor:

- Several UI/report draft paths still mention enrichment/GSEA as task-center concepts, but in this branch they should remain preflight/config wording until formal ORA/GSEA is present.
- Plot artifacts exist as guarded specs for several analysis types, but static image rendering is not a general capability yet.
- Full integrated report remains future work; current formal package scope is formal DEG section only.

## B15 Acceptance

| Requirement | Result | Evidence |
| --- | --- | --- |
| Capability matrix covers requested surfaces | Passed | This document covers DEG, imported DEG, ORA, GSEA, KM/log-rank, Cox, plot, report, integrated report and legacy assets. |
| Legacy assets classified | Passed | Inventory classifies retain/minimum migration/design reference/prohibited paths. |
| No formal analysis expansion | Passed | Documentation-only stage; no app or test code changed. |
| Current branch divergence recorded | Passed | ORA/GSEA controlled runtime absence is recorded as a major planning gap. |
| `project_storage` and old handoff files excluded | Passed | Both are listed as intentionally untracked and excluded. |

## Test Record

Commands run:

- `git diff --check` -> passed.
- `python3 -m pytest tests/bioinformatics -q -k "formal_deg or ora or gsea or survival or clinical or cox or km or analysis_ui"` -> 92 passed, 314 deselected.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or results_browser or report"` -> 13 passed, 96 deselected.
- `python3 -m pytest tests/bioinformatics -q` -> 406 passed.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` -> 176 passed.
- `python3 -m app.main --smoke-test` -> passed, `git_head=0e340cf`, `pyside6_available=True`.

## Recommendation

Proceed to B16 only after accepting that current-branch B15 treats ORA/GSEA controlled execution as absent unless B10/B11 are explicitly scoped into this branch. The next implementation stage should therefore be either:

1. B16 legacy acquisition adapter absorption, if the priority is improving data entry and standardization; or
2. a scoped ORA/GSEA convergence stage, if the priority is restoring the later enrichment-layer controlled MVP before plot/report integration.
