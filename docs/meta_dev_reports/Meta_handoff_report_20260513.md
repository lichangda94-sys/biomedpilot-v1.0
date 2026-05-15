# Meta Handoff Report - 2026-05-15

## 1. Branch / Worktree Summary

| Item | Current State |
| --- | --- |
| Worktree path | `/Users/changdali/Developer/biomedpilot v1.0/Meta` |
| Git branch | `dev/meta-analysis` |
| Meta source HEAD covered by this report | `6a0b77c7427a283b2115200ae46b4727803f9df0` (`6a0b77c`) |
| Latest source commit covered | `docs(meta): align local tools model architecture` |
| Uncommitted changes before this report | Yes; this handoff report was an untracked local file and has now been refreshed before Integration handoff. |
| Upstream tracking | Not shown by `git branch -vv`; no remote push was performed. |
| MainLine comparison | Obvious divergence exists. Merge base with `stable/mainline` is `9084bb8e21bb268151953ef290ae62007468f3e9`. |
| MainLine current HEAD observed | `stable/mainline` at `21e1a0f` (`docs(mainline): carry B5.15 integration handoff audit`). |
| Integration current HEAD observed | `dev/integration` at `59ee32b` (`Close LabTools local engine integration audit`) before the 2026-05-15 Meta carryover resolution. |

Commands executed for branch/worktree status:

```bash
pwd
git status --short
git branch --show-current
git rev-parse --short HEAD
git rev-parse HEAD
git log --oneline -8
git branch -vv --all
git --git-dir="/Users/changdali/Developer/biomedpilot v1.0/_repo.git" worktree list
```

Current branch responsibility:

- Meta Analysis workflow development for PICO / PICOS / PECO, search strategy, literature library/import, deduplication, screening, full text management, extraction, quality assessment, statistics, and reporting.
- This worktree must not perform GEO / TCGA / GTEx expression data analysis.
- This worktree must not be used to package internal beta builds directly. Release packages must come from validated MainLine or validated release source.

Observed MainLine divergence:

- MainLine contains staged Meta/Integration work from earlier passes, but the active Meta branch remains ahead for several workflow steps and Integration-specific validation must be checked in the Integration worktree.
- This Meta branch still contains `app/meta_analysis/legacy/**` as a historical isolation area.
- MainLine has additional governance, shared UI, Bioinformatics, cleanup, and handoff changes that are not part of this Meta worktree.
- Do not use whole-branch merge from Meta into MainLine without staged integration and explicit legacy exclusion.

## 1A. Integration Handoff Candidate List - 2026-05-15

Current Integration handling rule:

- Do not whole-branch merge `dev/meta-analysis` into `dev/integration`.
- Do not carry `app/meta_analysis/legacy/**`.
- Preserve Integration-owned LabTools, Bioinformatics, shared local engine, package-readiness, and UI-shell changes.
- Treat Meta outputs as Developer Preview / testing unless separately validated in Integration or ReleaseBuild.

Already equivalent or already represented in Integration:

- `6a0b77c` `docs(meta): align local tools model architecture` is patch-equivalent to Integration `6fae058` and should not be cherry-picked again.
- `5e27ed4`, `ea7d203`, and `0895d78` have patch-equivalent Integration-side commits for M11-M13 foundations.
- Integration already has scoped M10-M13 runtime/user-path variants: `5702e2f`, `e86de13`, `ba58540`, `141429c`, and `f2b5679`.

Clean documentation or scoped candidates that can be carried if Integration still needs the report artifacts:

- `f06308b` `docs(meta): add full version audit report`
- `9153aab` `docs(meta): audit mainline merge readiness`
- `67d7f96` `docs(meta): audit statistical executor integration`
- `2307ded` `docs(meta): audit runtime integration readiness`

Conflict-prone commits resolved by scoped active-runtime carryover rather than direct cherry-pick:

- `7bb7ceb` `feat(meta): add screening workspace refinement`
- `386000d` `feat(meta): add full-text management workspace`
- `e098cdd` `feat(meta): add structured extraction table`
- `86bc02a` `feat(meta): add quality assessment workspace`
- `24e7625` `feat(meta): add analysis plan confirmation workspace`
- `293a0b5` `feat(meta): add draft report generation`
- `24f43c7` `feat(meta): gate statistical result states`
- `5eaf2b1` `fix(meta): backfill m10 m13 active user path`

Integration resolution applied for these conflict-prone commits:

- Synchronized only the active Meta runtime files touched by those commits, plus their Meta tests and development reports.
- Kept `app/meta_analysis/legacy/**` out of Integration.
- Kept Integration-only files outside the Meta runtime untouched.
- Added this refreshed handoff report so Integration receives current HEAD/status/candidate guidance instead of the stale 2026-05-13 local draft.

## 2. Current Functional Scope

### Implemented and runnable in this worktree

- Meta desktop workspace shell under `app/meta_analysis/workspace.py`.
- Project create/open validation via `app/meta_analysis/project_workspace.py`.
- 8-step Chinese Meta workflow navigation through `MetaWorkspace`.
- PICO / protocol draft and confirmation services.
- Search strategy draft / confirmed strategy generation and export.
- Testing-level PubMed candidate preview, selection, and handoff into literature records.
- Local literature import for NBIB / RIS / CSV, using active runtime parser/normalizer rather than legacy bridge.
- Literature library summary, diagnostics, source filters, notes, and export summary.
- Duplicate review queue, merge preview, manual decision recording, deduplicated set generation, and screening queue preparation.
- Exclusion criteria library and PRISMA reason map.
- Title/abstract screening queue and manual include / exclude / maybe decisions.
- Full text registry, PDF attachment registration, testing-level parsing, and full-text eligibility decisions.
- Manual extraction study units and effect rows, CSV draft import/export, and extraction validation.
- Testing-level AI suggestion queue that requires manual accept/reject/edit/apply; it does not overwrite final screening, extraction, analysis, or report data automatically.
- Quality assessment testing records and CSV export.
- Analysis plan draft/confirmed flow, analysis-ready dataset builder, testing-level statistical runs, forest/funnel figure generation, and result table CSV.
- Reporting draft: PRISMA summary, formal Markdown, HTML/DOCX testing export, supplementary exports, figure package, snapshot, and reproducibility package.

### UI-connected but testing-level / draft

- All Meta features remain `Developer Preview / testing`.
- PubMed search/candidates are testing-level and must not be described as complete systematic-review retrieval.
- Advanced analysis methods are testing implementations or descriptive helpers; they are not production-grade statistical engines.
- AI-assisted review is a candidate suggestion workflow only; no automatic scientific decision is final.
- Full-text parsing is testing-level and does not provide OCR or automated evidence extraction.
- Formal report export is a testing artifact; PDF export remains a placeholder text output.
- Network meta-analysis remains not implemented / placeholder.
- PRISMA counts and report content depend on available testing artifacts and manual decisions; they are not submission-grade outputs.

### Backend/service layer without full production UI maturity

- Some services have broader test coverage than the UI exposes, especially advanced analysis add-ons, governance/audit helpers, report manifests, and reproducibility package generation.
- Service outputs are structured and test-covered, but UI ergonomics and screenshot-level validation are not production complete.

### Documentation or preserved interface only

- `app/meta_analysis/legacy/**` is retained as historical snapshot/reference material, not active runtime.
- Several legacy source labels remain in `app/shared/feature_availability.py` as provenance text, but active runtime must not call legacy services.
- WOS / Embase / CNKI / WanFang / VIP are not active online retrieval backends in this worktree.

## 3. Completed Work Since Last Handoff

- Completed: MainLine merge readiness audit.
  - Involved files: `docs/audit/meta_mainline_merge_readiness_audit_20260513.md`.
  - Behavior change: none; documentation-only audit.
  - UI change: none.
  - Data/manifest change: none.
  - Testing: audit recorded `tests/meta_analysis`, `tests/ui`, smoke, and `git diff --check` at that stage.

- Completed: active Meta UI theme unification.
  - Involved files: `app/ui_style_tokens.py`, `app/meta_analysis/workspace.py`, active Meta pages under `app/meta_analysis/pages/**`, and theme tests.
  - Behavior change: no business workflow change; active UI style helpers now use unified BioMedPilot tokens.
  - UI change: Meta active UI primary colors now align with `#12324A`, `#1BAE9F`, `#F5F7F9`, and `#FFFFFF`.
  - Data/manifest change: none.
  - Testing: `tests/meta_analysis`, `tests/ui`, `tests/shared`, source smoke, and `git diff --check` passed during that stage.

- Completed: active runtime legacy bridge retirement.
  - Involved files: `app/meta_analysis/literature_import_core.py`, `app/meta_analysis/adapters/**`, `app/meta_analysis/services/literature_batch_import_service.py`, `app/meta_analysis/services/literature_import_service.py`, and legacy guard tests.
  - Behavior change: active adapters and literature import services no longer use `_legacy_path()`, `LEGACY_ROOT`, legacy service loader, or legacy parser/normalizer runtime calls.
  - UI change: no direct UI redesign; literature import panel now depends on active batch service semantics.
  - Data/manifest change: active import diagnostics, warnings CSV, import batches, and normalized literature records are produced by active services.
  - Testing: `tests/meta_analysis` 462 passed, `tests/ui` 154 passed, source smoke passed, and `git diff --check` passed in this handoff verification.

- Completed: staged Integration and MainLine application happened outside this worktree.
  - Involved files in this worktree: none changed by this report.
  - Note: MainLine was observed at `21e1a0f docs(mainline): carry B5.15 integration handoff audit`; this Meta branch remains a module worktree and still contains legacy historical material.
  - Boundary: do not infer MainLine cleanliness from Meta branch contents; inspect MainLine separately before release or packaging.

## 4. Important Files and Entry Points

### Main UI and entry points

- `app/meta_analysis/workspace.py`
  - Main Meta desktop workspace, project home, workflow navigation, page factory, dashboard summary, and PySide UI composition.
- `app/meta_analysis/project_workspace.py`
  - Creates and validates Meta project directories, `meta_project_manifest.json`, `meta_project_config.json`, and standard folder layout.
- `app/meta_analysis/workflow_pages.py`
  - Compatibility exports for protocol/search workflow functions used by tests and shell integration.
- `app/meta_analysis/pages/**`
  - Active page modules for protocol, literature import/library, duplicate review, screening, full text, extraction, quality, analysis, reporting, audit, and workflow dashboard.
- `app/ui_style_tokens.py`
  - Shared color/style token file used by active Meta UI. Meta aliases now map to deep navy/teal/light gray.

### Core services and workflow code

- `app/meta_analysis/literature_import_core.py`
  - Active RIS / NBIB / CSV parsing, record normalization, diagnostics, warnings CSV, and duplicate candidate helper.
- `app/meta_analysis/adapters/**`
  - Active adapter layer for import, dedup, screening, extraction, analysis, and reporting. Must not reintroduce `_legacy_path()`.
- `app/meta_analysis/search/search_strategy_builder_service.py`
  - Search strategy draft/confirmed generation, versions, manifest, and exports.
- `app/meta_analysis/search/pubmed_search_service.py`
  - Testing-level PubMed query execution/parsing support. Do not represent this as comprehensive formal retrieval.
- `app/meta_analysis/search/pubmed_candidates_handoff_service.py`
  - Converts PubMed candidate preview selections into literature library records and dedup preparation artifacts.
- `app/meta_analysis/services/literature_import_service.py`
  - Active single-file import service with task/data asset registration and library update.
- `app/meta_analysis/services/literature_batch_import_service.py`
  - Active batch import service used by literature import panel tests.
- `app/meta_analysis/services/literature_library_service.py`
  - Canonical literature records and literature manifest management.
- `app/meta_analysis/services/dedup_review_v2_service.py`
  - Duplicate queue, decisions, merged/deduplicated set, and manifest update.
- `app/meta_analysis/services/title_abstract_screening_v2_service.py`
  - Title/abstract screening queue and decisions.
- `app/meta_analysis/services/fulltext_management_service.py`, `fulltext_parsing_service.py`, `fulltext_eligibility_service.py`
  - Full-text attachment registry, testing parser, and eligibility decisions.
- `app/meta_analysis/services/manual_extraction_effect_row_service.py`
  - Manual study unit/effect row draft workflow, CSV import/export, validation metadata.
- `app/meta_analysis/services/analysis_dataset_service.py`, `analysis_plan_service.py`, `meta_statistics_engine_service.py`, `analysis_run_service.py`
  - Analysis plan, dataset building, testing statistics, and analysis result persistence.
- `app/meta_analysis/services/formal_report_service.py`, `publication_export_service.py`, `report_manifest_service.py`
  - Testing report artifacts, exports, snapshot, reproducibility package, and report manifests.
- `app/meta_analysis/services/research_governance_service.py`, `audit_log_service.py`
  - Governance and audit event records for draft, confirmation, and user-review actions.

### Schema / model files

- `app/meta_analysis/models/protocol.py`
- `app/meta_analysis/models/publication.py`
- `app/meta_analysis/models/dedup.py`
- `app/meta_analysis/models/extraction.py`
- `app/meta_analysis/models/analysis_dataset.py`
- `app/meta_analysis/models/analysis_result.py`
- `app/meta_analysis/models/figures.py`
- `app/meta_analysis/models/prisma.py`
- `app/meta_analysis/models/ai_suggestion.py`
- `app/meta_analysis/extraction/schema_registry.py`
- `app/meta_analysis/stats/**`

### Tests

- `tests/meta_analysis/test_active_runtime_legacy_bridge_retirement.py`
  - Guard test preventing active runtime legacy bridge regression.
- `tests/meta_analysis/test_meta_ui_theme_tokens.py`
  - Guard test preventing retired Meta purple and old hardcoded active colors from returning.
- `tests/meta_analysis/test_stage_6_literature_import_panel.py`
  - Active batch literature import panel/service contract.
- `tests/meta_analysis/test_stage_m_end_to_end_validation.py`
  - E2E testing chain from import through reporting/reproducibility on fixture data.
- `tests/meta_analysis/test_stage_z_release_candidate_freeze.py`
  - Internal beta candidate guard and Bioinformatics-change blocker logic.
- `tests/ui/test_meta_analysis_workflow_pages.py`
- `tests/ui/test_meta_search_stage_m2.py`
- `tests/ui/test_meta_stage_m3_dedup_workflow.py`
- `tests/ui/test_module_selection.py`

### Current reports / audits / handoff candidates

- `docs/audit/meta_mainline_merge_readiness_audit_20260513.md`
- `docs/audit/meta_ui_theme_unification_report_20260513.md`
- `docs/audit/meta_active_runtime_legacy_bridge_retirement_report_20260513.md`
- `docs/meta_dev_reports/stage_Z_internal_beta_release_candidate_report.md`
- `docs/meta_dev_reports/stage_M_end_to_end_validation_report.md`
- `docs/meta_dev_reports/Meta_handoff_report_20260513.md`

### Packaging / desktop note

- This Meta worktree is not the release packaging worktree.
- Use `ReleaseBuild` for package metadata validation and packaged smoke tests after MainLine validation.
- Do not package from this unvalidated module worktree.

## 5. Runtime / User Flow

Current active user flow in the Meta workspace:

1. Open BioMedPilot / 医研智析.
2. Choose Meta Analysis / 医学 Meta 分析 workspace.
3. Create or open a Meta project.
4. Project home shows workflow status and next-step guidance.
5. PICO / Protocol: create draft, edit fields, confirm protocol.
6. Search Strategy: generate draft strategy from confirmed PICO, edit/confirm, export strategy.
7. Literature Import / Library: import local NBIB / RIS / CSV or hand off selected testing PubMed candidates; review diagnostics and library records.
8. Dedup / Screening Prep: build duplicate review queue, make manual duplicate decisions, generate deduplicated set, prepare screening queue.
9. Criteria and Title/Abstract Screening: manage exclusion reasons and manually record include/exclude/maybe decisions.
10. Full Text: register full-text status/PDF attachment, run testing parser, record eligibility decisions.
11. Extraction / Quality: manually create study units/effect rows, import CSV drafts, complete quality records.
12. Analysis: create analysis plan, build analysis-ready dataset, run testing statistics and generate figures/tables.
13. Reporting: generate testing PRISMA/formal report artifacts, supplementary exports, snapshot, and reproducibility package.

Flow closure status:

- Testing fixture workflows can run end-to-end through report and reproducibility package.
- Real user workflow still requires manual extraction, manual quality assessment, and human review of all screening/report/statistical outputs.
- PDF report, network meta-analysis, OCR, automatic screening, automatic extraction, automatic quality assessment, and production report writing are not complete.

## 6. Data Contracts / Manifest Contracts

| Contract / artifact | Location | Generated by | Read by | Status | Dependency guidance |
| --- | --- | --- | --- | --- | --- |
| Meta project manifest | `<project>/meta_project_manifest.json` | `create_meta_analysis_project()` | `validate_meta_analysis_project()`, workspace | Testing but stable enough for Meta project detection | Other modules should not depend on it directly. |
| Meta project config | `<project>/meta_project_config.json` | `create_meta_analysis_project()` | workspace/UI | Testing | Meta-only. |
| Project folders | `<project>/{research_question,search_strategy,literature_library,screening,extraction,quality_assessment,analysis,prisma,reports,logs,exports,...}` | `project_workspace.py` | Meta services | Testing contract | Keep compatible; avoid deleting directories. |
| PICO draft/confirmed | `<project>/protocol/pico_workspace_draft.json`, `<project>/protocol/pico_workspace_confirmed.json` | `PicoWorkspaceService` | search strategy, workspace | Testing | Meta-only; requires human confirmation. |
| Search strategy draft/confirmed | `<project>/search_strategy/search_strategy_draft_set_v2.json`, confirmed set, versions, manifest | `SearchStrategyBuilderService` | workspace, PubMed candidate flow | Testing | Do not treat as exhaustive formal search. |
| PubMed candidate preview/selection | `<project>/protocol/pubmed_candidates/*_candidates_preview.json`, selection JSON | `PubMedCandidatesHandoffService` | literature import/handoff | Testing | PubMed-only testing surface; no WOS/Embase/CNKI claim. |
| Literature records | `<project>/literature/literature_records.json`; compatibility import outputs under project literature/import paths | `LiteratureImportService`, `MultiSourceLiteratureImportService`, handoff service | library, dedup, screening, reporting | Testing | Downstream Meta may depend on fields, but human review required. |
| Import diagnostics / warnings | `<project>/literature/import_diagnostics/*_import_diagnostics.json`, warnings CSV | `literature_import_core.py`, import services | workspace dashboard, tests | Testing | Useful for QA; not a scientific result. |
| Literature manifest | `<project>/literature/literature_manifest.json` | `LiteratureLibraryService` | library, dedup/reporting | Testing | Meta-only. |
| Dedup queue / decisions / deduplicated set | `<project>/deduplication/dedup_review_queue_v2.json`, decisions JSON, deduplicated set JSON | `DedupReviewV2Service` | screening/reporting | Testing | Depends on manual decisions; no automatic final exclusion. |
| Screening queue / decisions | `<project>/screening/title_abstract_screening_queue_v2.json`, decisions JSON | `TitleAbstractScreeningV2Service` | full text, PRISMA/reporting | Testing | Human decisions required. |
| Exclusion criteria library | `<project>/screening/exclusion_criteria_library.json`, PRISMA reason map | `ExclusionCriteriaLibraryService` | screening/full-text/reporting | Testing | Meta-only; can change before production. |
| Full-text registry / parsed text / eligibility | `<project>/fulltext/**` | full text services | extraction/reporting | Testing | No OCR; parser is testing-level. |
| Extraction study units/effect rows | `<project>/extraction/study_units.json`, `effect_rows.json`, validation reports | `ManualExtractionEffectRowService` | dataset builder, analysis, reporting | Testing | Manual data entry; not automatically verified. |
| Quality records | `<project>/quality/quality_assessment_records_v1.json` and CSV exports | `QualityService` | reporting | Testing | Not formal GRADE. |
| Analysis plan | `<project>/analysis/analysis_plan_draft_v1.json`, confirmed plan | `AnalysisPlanService` | dataset/statistics | Testing | Requires method validation before production reliance. |
| Analysis-ready datasets | `<project>/analysis/analysis_ready_datasets.json` | `AnalysisDatasetService` | statistics engine | Testing | Depends on extraction completeness. |
| Analysis results / figures | `<project>/analysis/analysis_results.json`, `<project>/figures/**`, `<project>/exports/analysis_result_table_*.csv` | `AnalysisRunService`, `FigureResultService`, stats services | reporting/export | Testing | Not submission-grade. |
| Report artifacts | `<project>/reports/formal_meta_report.md`, `.html`, `.docx`, PDF placeholder | `FormalReportService`, `PublicationExportService` | user export / package | Testing / placeholder for PDF | May be used as internal beta validation artifact only. |
| Supplementary/reproducibility exports | `<project>/exports/**`, snapshots, package zip | `PublicationExportService` | user/export tests | Testing | Preserve provenance; not a regulated archive. |
| Audit/governance logs | service-specific audit JSON and governance records | `AuditLogService`, `ResearchGovernanceService` | tests/reporting | Testing | Useful for traceability; schema may evolve. |

## 7. Tests and Validation

Actual validation run for this handoff:

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q
```

Result: `462 passed in 4.08s`.

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

Result: `154 passed in 9.87s`.

```bash
python3 -m app.main --smoke-test
```

Result: passed.

Observed smoke output:

```text
app_version=0.1.0-internal-beta
app_channel=Developer Preview / testing
launch_mode=source
app_root=/Users/changdali/Developer/biomedpilot v1.0/Meta
git_head=6a0b77c
workspace_entries=3
bioinformatics_features=5
meta_analysis_features=7
pyside6_available=True
```

```bash
git diff --check
```

Result: passed.

Additional focused scans:

```bash
rg -n "#6B4FD8|#F0EDFF|#0F766E|#E6FFFB|#99F6E4|#D8DEE9|#111827|#B42318" app/meta_analysis app/ui_style_tokens.py tests/meta_analysis tests/ui
```

Result: retired colors are absent from active Meta runtime and `app/ui_style_tokens.py`. Remaining hits are expected guard-test literals, `tests/ui/test_app_theme.py`, and `app/meta_analysis/legacy/**`.

```bash
rg -n "_legacy_path|LEGACY_ROOT|app/meta_analysis/legacy|meta_analysis\\.legacy|legacy service loader|legacy parser|legacy normalizer" app/meta_analysis tests/meta_analysis
```

Result: active runtime legacy bridge terms are absent from active app files. Remaining hits are guard-test literals.

Tests not run in this handoff:

- `tests/shared` was not rerun because this handoff report does not change shared code.
- package build / packaged smoke was not run because this is a Meta module worktree and packaging must be done from ReleaseBuild after validated MainLine/release sync.
- MainLine full matrix was not run from this worktree.

## 8. Known Issues / Risks

1. Current Meta branch still contains `app/meta_analysis/legacy/**` with 334 tracked files. It is a historical isolation area and must not be merged wholesale into MainLine or ReleaseBuild active source.
2. This branch diverges from `stable/mainline`; whole-branch merge is unsafe without staged integration rules.
3. `CODEX.md` is stale relative to current code: it still states the current priority as M4, while this worktree has testing-level surfaces through analysis/reporting and later internal beta stages.
4. `README.md` still describes both original projects as isolated legacy snapshots under `app/meta_analysis/legacy/`; that statement is historically true for this branch but does not describe the current active runtime boundary after legacy bridge retirement.
5. Many Meta features are testing-level. Do not market them as production-ready, clinical-grade, or submission/submission-ready.
6. PubMed testing-level candidate retrieval is not a complete multi-database systematic-review search. WOS / Embase / Cochrane / CNKI / WanFang / VIP are not active online retrieval backends.
7. Full text parsing does not include OCR and must not be described as automated evidence extraction.
8. AI-assisted review remains suggestion-only and human-gated; do not enable model calls or automatic application outside AI Gateway policy.
9. Statistical outputs are testing-level and require method validation before any production or formal research use.
10. PDF export remains placeholder; HTML/DOCX/Markdown are testing artifacts.
11. Historical docs mention old paths such as `/Users/changdali/Documents/BioMedPilot`; treat these as historical unless refreshed by current project-control docs.
12. Packaging from this worktree is prohibited by the global manual for internal beta/release builds.

## 9. Do Not Touch / Boundary Rules

- Do not modify other worktrees from this Meta handoff task.
- Do not directly edit MainLine, Integration, ReleaseBuild, Bioinformatics, Vocabulary, AI, UIShell, or LabTools from the Meta worktree.
- Do not perform a whole-branch merge from `dev/meta-analysis` into MainLine.
- Do not delete `app/meta_analysis/legacy/**` without a dedicated cleanup task and explicit human confirmation.
- Do not reintroduce `_legacy_path()`, `LEGACY_ROOT`, legacy service loader, legacy parser, or `app.meta_analysis.legacy` imports into active runtime.
- Do not let Meta call Bioinformatics business code.
- Do not add GEO / TCGA / GTEx expression analysis to Meta.
- Do not say WOS / Embase / CNKI / WanFang / VIP online retrieval is supported unless implemented and tested.
- Do not automatically screen, extract, assess quality, run final statistics, write final conclusions, or overwrite final report data without human review.
- Do not bypass AI Gateway or enable model/network calls by default.
- Do not generate fake statistics, fake PRISMA counts, fake screening decisions, fake figures, or fake reports.
- Do not package internal beta builds from this module branch.
- Do not overwrite desktop app, release bundle, or user testing entry from this worktree.

## 10. Recommended Next Tasks

### Immediate Next Step

1. Update Meta branch-local docs to match current runtime truth:
   - refresh `CODEX.md` so it no longer implies only M0-M3/M4 are current.
   - refresh `README.md` wording so active runtime and `app/meta_analysis/legacy/**` isolation are not confused.
   - keep Developer Preview / testing wording.

2. Add a small docs-only legacy isolation note if needed:
   - explicitly state that `app/meta_analysis/legacy/**` is retained only for historical reference in this branch.
   - state that active adapters/services must remain legacy-bridge-free.

### Before Integration

1. Re-run staged integration from a clean Integration worktree if Meta changes continue after `6a0b77c`.
2. Do not import `app/meta_analysis/legacy/**` into Integration/MainLine active source.
3. Re-run:
   - `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q`
   - `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
   - `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/shared -q`
   - `python3 -m app.main --smoke-test`
   - `git diff --check`
4. Confirm `app/ui_style_tokens.py` still maps Meta to `#12324A`, `#1BAE9F`, `#F5F7F9`, `#FFFFFF`.
5. Confirm no active runtime `legacy` bridge and no `app.bioinformatics` import in Meta.

### Later / Optional

1. Expand real-world literature import fixture coverage for more RIS/NBIB/CSV variants.
2. Add screenshot-level UI validation for key Meta pages if UI shell tooling becomes available.
3. Improve advanced analysis method validation and documented assumptions.
4. Replace PDF placeholder with an approved lightweight PDF export strategy only after dependency and packaging approval.
5. Decide whether `legacy_decision` compatibility field should be renamed or documented before production hardening.
6. Archive historical docs with old paths after project-control cleanup approval.

## 11. Suggested Codex Instruction for Next Stage

```text
请在 BioMedPilot v1.0 的 Meta worktree 中执行 docs-only handoff alignment。

Worktree:
/Users/changdali/Developer/biomedpilot v1.0/Meta

目标：
1. 只更新 Meta 分支本地文档，使 CODEX.md、README.md 和必要的 docs note 与当前 active runtime 状态一致。
2. 明确 active Meta runtime 已退休 legacy bridge，app/meta_analysis/legacy/** 仅为历史隔离区。
3. 明确当前 Meta 功能仍为 Developer Preview / testing，不是生产级、临床级或投稿级。
4. 不修改业务代码、不修改测试、不修改其他 worktree。

允许修改：
- CODEX.md
- README.md
- docs/meta_dev_reports/ 或 docs/audit/ 中新增一份 docs-only 对齐报告

禁止事项：
- 不要删除 app/meta_analysis/legacy/**
- 不要修改 app/meta_analysis active runtime 代码
- 不要修改 Bioinformatics、MainLine、Integration、ReleaseBuild、Vocabulary、AI、UIShell、LabTools
- 不要整分支 merge
- 不要打包
- 不要 push
- 不要把 testing-level 功能描述为 production-ready

必须先读取：
- /Users/changdali/Developer/biomedpilot v1.0/README_总说明.md
- /Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md
- /Users/changdali/Developer/biomedpilot v1.0/Meta/docs/meta_dev_reports/Meta_handoff_report_20260513.md
- /Users/changdali/Developer/biomedpilot v1.0/Meta/docs/audit/meta_active_runtime_legacy_bridge_retirement_report_20260513.md

验证命令：
git status --short
git diff --check
python3 -m app.main --smoke-test

如果只改文档，可不运行完整 pytest，但必须在最终报告中说明未运行完整业务测试的原因。

停止条件：
- 发现当前 worktree 有非本任务未提交改动。
- 需要修改业务代码或其他 worktree。
- 需要删除 legacy 或历史报告。
- 发现文档更新会改变模块边界或成熟度表述。
```
