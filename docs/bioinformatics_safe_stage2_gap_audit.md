# Bioinformatics Safe Stage 2 Gap Audit

Date: 2026-05-10

Scope: read-only audit of `codex/bioinformatics-safe-stage2` against `dev/bioinformatics`. No code was merged, cherry-picked, copied, or edited during this review.

## 1. Branch Information

| Field | Value |
| --- | --- |
| Base branch | `dev/bioinformatics` |
| Reviewed branch | `codex/bioinformatics-safe-stage2` |
| Base HEAD at review | `1e02b15 docs(repo): audit bio search ui branch gaps` |
| Ahead / behind | `141 61` for `git rev-list --left-right --count dev/bioinformatics...codex/bioinformatics-safe-stage2` |
| Branch-only commit count | 61 |
| Overall risk | Very high for integration; useful only as historical architecture reference |

Interpretation: `dev/bioinformatics` is far ahead of the reviewed branch, while `codex/bioinformatics-safe-stage2` contains a large old architecture line with project workspace, acquisition, recognition, readiness, standardization, analysis, report, packaging, and UI changes. It should not be merged or cherry-picked directly.

## 2. Branch-Only Commit Classification

| Commit | Message | Classification |
| --- | --- | --- |
| `75fe3c3` | `feat(bio): add Chinese project wizard UI` | UI / project workspace |
| `988577a` | `test(bio): add pre-ui workflow acceptance readiness` | tests / acceptance |
| `bdf26b7` | `chore(bio): add local venv bootstrap workflow` | packaging / obsolete |
| `8ace365` | `chore(bio): isolate project local venv packaging` | packaging / obsolete |
| `9a84f92` | `chore(bio): harden local venv packaging` | packaging / obsolete |
| `8ad326d` | `feat(bio): add workflow orchestrator gui entry` | UI / workflow orchestrator |
| `79f992d` | `feat(bio): add project workflow orchestrator` | workflow orchestrator |
| `1ad6c9d` | `feat(bio): add project report builder` | reporting |
| `02a1aad` | `feat(bio): add project result manager` | result manager |
| `0fe96d2` | `feat(bio): add project analysis task center` | analysis task center |
| `f446eac` | `feat(bio): add standardized assets registry` | standardization |
| `def72a5` | `feat(bio): add project readiness matrix` | readiness |
| `a8edd4f` | `feat(bio): strengthen project data recognition routing` | recognition |
| `83a361c` | `feat(bio): add project data recognition report` | recognition |
| `d36c7ac` | `feat(bio): bind acquisition center to project workspace` | acquisition / project workspace |
| `6ae52c0` | `feat(bio): bind acquisition outputs to project workspace` | acquisition / project workspace |
| `7aa1cd5` | `feat(bio): add project workspace contract` | project workspace |
| `3395272` | `feat(bio): add unified data acquisition center` | acquisition center |
| `5a0fe9a` | `chore(bio): audit workspace before data acquisition center` | docs / audit |
| `dc318c8` | `feat(bio): add refreshable asset action panel` | UI |
| `6e72dfe` | `feat(bio): add source navigation asset actions` | UI |
| `b723087` | `feat(bio): add source action handoff state` | workflow / UI |
| `e72416a` | `feat(bio): add source-oriented workflow guidance` | workflow guidance |
| `fea7898` | `feat(bio): add GEO annotation mapping support` | GEO annotation |
| `1857e5c` | `fix(bio): stabilize GSE33630 desktop regression flow` | UI / tests |
| `5fd2403` | `fix(bio): improve GUI workflow handoff` | UI |
| `5132d53` | `docs(bio): record GSE33630 GUI demo issues` | docs |
| `5bf6515` | `fix(bio): improve real GEO report artifacts` | reporting |
| `4a15a48` | `docs(bio): record GSE33630 real dataset test` | docs |
| `5a15ea6` | `docs(bio): record full flow manual test issues` | docs |
| `bdfbb4d` | `fix(shared): stabilize desktop storage and file import` | shared / high risk |
| `8f15c66` | `fix(shared): force desktop light theme` | shell/theme / high risk |
| `a5acd60` | `feat(bio): add report package ui entry` | reporting UI |
| `51a4227` | `feat(bio): add standard report document export` | reporting |
| `1135cc9` | `docs(bio): add real dataset application test log` | docs |
| `74d72f7` | `feat(bio): add runner artifact integration` | reporting / runner artifacts |
| `6e322dd` | `feat(bio): add analysis package exporter` | reporting / export |
| `09e3d9f` | `test(bio): add real dataset fixture plans` | tests / examples |
| `ef17225` | `feat(bio): add artifact manifest v1` | artifact manifest |
| `3121004` | `feat(bio): integrate survival standard report` | reporting |
| `ecf844f` | `feat(bio): integrate gsea standard report` | reporting |
| `d294a5e` | `feat(bio): integrate enrichment standard report` | reporting |
| `e177269` | `feat(bio): integrate correlation standard report` | reporting |
| `6457ee6` | `feat(bio): integrate target gene report` | reporting |
| `d6a78f0` | `feat(bio): integrate deg standard report` | reporting |
| `ff5bcd1` | `feat(bio): upgrade public data source parsing` | acquisition / parsing |
| `40649e5` | `feat(bio): add statistical method upgrades` | analysis / statistical methods |
| `3d5c277` | `feat(bio): add publication figure exports` | reporting / figures |
| `1b62278` | `feat(bio): add data import wizard state` | UI / import wizard |
| `8811a73` | `test(bio): add end-to-end acceptance project` | tests / acceptance |
| `15fa957` | `feat(bio): add report package export` | reporting / export |
| `55b20be` | `feat(bio): add workflow status model` | workflow status |
| `66e73a8` | `feat(bio): add correlation survival runners` | analysis |
| `5359b91` | `feat(bio): add tcga gtex asset entry` | TCGA / GTEx assets |
| `2f76403` | `feat(bio): add geo series matrix ingestion` | GEO ingestion |
| `0457edb` | `feat(bio): add mvp markdown report export` | reporting |
| `3153789` | `feat(bio): add local gmt enrichment runner` | analysis |
| `fc02fff` | `feat(bio): add deg visualization artifacts` | figures |
| `cfe0c88` | `feat(bio): add differential expression runner` | analysis |
| `863dbca` | `feat(bio): add sample grouping comparison config` | sample grouping |
| `a5f6156` | `feat(bio): add expression matrix cleaning runner` | standardization |

## 3. File Difference Table

| Path or group | Change | Module | Current `dev/bioinformatics` equivalent | Recommendation |
| --- | --- | --- | --- | --- |
| `app/bioinformatics/project_workspace.py` | A | project workspace | Current `app/bioinformatics/project_workspace.py` and `project_workspace_binding.py` exist in a newer lightweight flow | Reference only |
| `app/bioinformatics/data_acquisition/**` | A | acquisition center | Current workflow uses `download/dataset_download_service.py`, search center, acquisition status UI, and project bindings | Design reference only |
| `app/bioinformatics/data_recognition/**` | A | recognition | Current `project_recognition.py`, `geo_metadata_profile_service.py`, `group_preview.py`, and random GEO audit cover newer recognition needs | Ignore |
| `app/bioinformatics/readiness/**` | A | readiness | Current `project_readiness.py` and readiness dashboard already exist | Ignore |
| `app/bioinformatics/standardization/**` | A | standardization | Current `project_standardization.py` exists | Reference only for registry field ideas |
| `app/bioinformatics/analysis_task_center/**` | A | analysis task center | Current `project_analysis_tasks.py` exists | Design reference only |
| `app/bioinformatics/results/**` | A | result manager | Current `results/project_results.py` exists | Reference only |
| `app/bioinformatics/reports/**` | A | report builder/export | Current `reports/project_report_builder.py` and `services/bio_report_service.py` exist; safe-stage2 is much larger | Selective design reference only |
| `app/bioinformatics/pages/*` | A/M | UI pages | Current `workflow_pages.py` and UI stage pages cover the developer preview workflow | Reference only |
| `app/bioinformatics/services/*runner.py` | A/M | analysis runners | Current services include GEO DEG, enrichment, correlation, TCGA runners, and preflight services | Ignore unless a future task requests a specific method |
| `app/bioinformatics/workflows/project_workflow_orchestrator.py` | A | workflow orchestrator | Current `project_workflow_orchestrator.py` exists | Reference only |
| `app/main.py` | M | app entry | Cross-cutting app entry | Do not integrate from old branch |
| `app/shell/theme.py` | A | shell/theme | Cross-module shell/theme | Do not integrate from Bio branch |
| `app/shared/feature_availability.py`, `app/shared/storage/__init__.py` | M | shared | Cross-module shared changes | Need separate review, not Bio consolidation |
| `scripts/package_app.py` | M | packaging | Packaging script | Do not integrate from old architecture branch |
| `scripts/bootstrap_biomedpilot_venv.py`, `requirements*.txt`, `pyproject.toml` | A/M | local venv/deps | Dependency and local environment changes | Do not integrate without dedicated packaging review |
| `examples/real_dataset_tests/**` | A | examples/test plans | Current docs/tests cover some real-use cases | Reference only |
| `tests/bioinformatics/**` | A/M | tests | Current test suite has newer Bio tests; safe-stage2 tests reflect old architecture | Reference only |
| `tests/test_package_app.py`, `tests/test_unified_entry.py`, `tests/ui/test_feature_availability.py` | M | package/app/shared UI tests | Cross-cutting tests | Do not integrate from Bio branch |
| `docs/stage_*`, `docs/bioinformatics_*` | A/M | docs | Some docs may preserve useful historical rationale | Reference only |

## 4. Functional Gap Table

| Function point | safe-stage2 implementation | Current `dev/bioinformatics` implementation | Covered? | Suggested follow-up | Risk |
| --- | --- | --- | --- | --- | --- |
| Project home / project wizard | `project_workspace.py`, `pages/data_import_wizard_page.py`, wizard UI commits | `project_home.py`, `workflow_pages.py`, `project_workspace.py`, UI stage docs | Mostly covered | Review wording only if needed | Medium |
| Data import and retrieval | `data_acquisition/**`, source planners | `search_center/**`, `download/dataset_download_service.py`, `workflow_pages.py` | Covered with newer flow | None | Low |
| Acquisition center | `data_acquisition/acquisition_center_service.py` | Current acquisition is spread across search/download/status pages rather than old center | Partially covered | Design concept can inform future consolidated acquisition panel | Medium |
| Project workspace contract | `project_workspace.py`, contract docs | Current `project_workspace.py`, `project_workspace_binding.py` | Covered in newer lightweight form | Reference old directory taxonomy only | Medium |
| Recognition / readiness | `data_recognition/project_recognition.py`, `readiness/project_readiness.py` | Current `project_recognition.py`, `project_readiness.py`, metadata profile, group preview, random GEO audit | Covered | None | Low |
| Standardization | `standardization/project_standardization.py` | Current `project_standardization.py` | Covered | Maybe compare registry field names in a future design-only task | Medium |
| Analysis task center | `analysis_task_center/project_analysis_tasks.py` | Current `project_analysis_tasks.py` and workflow pages | Covered | Reference status vocabulary only | Medium |
| Result manager | `results/project_results.py` | Current `results/project_results.py` | Covered | None unless report UX needs richer result grouping | Medium |
| Report builder | `reports/project_report_builder.py`, standard report/export/package docs | Current `reports/project_report_builder.py`, `services/bio_report_service.py`, `bioinformatics_standard_report_v1.md` | Covered at a lighter level | Selectively review report section schema later | Medium |
| Workflow orchestrator | `workflows/project_workflow_orchestrator.py` | Current `project_workflow_orchestrator.py` | Covered | None | Low |
| Project manifest / config / audit | `project_workspace.py`, artifact manifest docs | Current project workspace, binding, report/results artifacts | Partially covered | Consider artifact manifest field ideas later | Medium |
| TCGA / GTEx / GEO input paths | `data_acquisition/tcga/**`, `gtex/**`, `tcga_gtex_asset_service.py` | Current TCGA/GTEx adapters, TCGA prepared packages, search center, download manifests | Covered for current scope | Do not replace current adapters | Medium |
| UI workflow navigation | `workspace.py`, multiple page additions | Current `workspace.py` and `workflow_pages.py` have newer desktop flow | Covered | Reference only | Medium |
| Chinese copy and user guidance | project wizard/UI docs | Current Bio UI has newer Chinese copy plus AI Gateway local AI copy | Covered | Some wording may be useful | Low |
| Test coverage | many `tests/bioinformatics/*` additions | Current Bio tests: 215 passing in previous round, plus UI tests in current suite | Covered for current architecture | Review old acceptance fixtures only if designing E2E fixtures | Low |

## 5. Content Not Recommended For Integration

- The old large architecture as a whole.
  - It adds many parallel modules under `data_acquisition`, `data_recognition`, `readiness`, `standardization`, `analysis_task_center`, `results`, and `reports`.
  - Current `dev/bioinformatics` already has equivalent lightweight modules with current UI and AI Gateway boundaries.
- Old UI workflow and wizard code.
  - Current `workflow_pages.py` and workspace flow are newer and already connected to local AI, search, metadata profile, group preview, and project binding.
- Old manifest contract and directory taxonomy.
  - Useful as design reference, but direct adoption would risk breaking current project data layout.
- Old readiness / standardization logic.
  - It overlaps current readiness and standardization services and should not replace them.
- Packaging and environment changes.
  - `scripts/package_app.py`, `requirements*.txt`, `pyproject.toml`, and local venv bootstrap changes are high risk and out of Bio branch consolidation scope.
- Cross-module shell/shared changes.
  - `app/main.py`, `app/shell/theme.py`, `app/shared/feature_availability.py`, and `app/shared/storage/__init__.py` should not be pulled from this Bio branch.
- Legacy references to PubMed/Meta or broad legacy tree content.
  - Bioinformatics must remain separate from Meta literature search workflows.

## 6. Possibly Worth Reference

These are design-level references only, not direct code migration candidates:

- Project workspace contract and directory taxonomy in `docs/bioinformatics_project_workspace_contract.md` and `app/bioinformatics/project_workspace.py`.
- Acquisition center page model and source-oriented workflow language in `data_acquisition/**` and `services/source_oriented_workflow.py`.
- Analysis task center status model and missing-asset vocabulary in `analysis_task_center/project_analysis_tasks.py`.
- Result manager and report builder section structure in `results/project_results.py` and `reports/project_report_builder.py`.
- Artifact manifest and report package ideas in `docs/bioinformatics_artifact_manifest_v1.md`, `docs/bioinformatics_analysis_package_v1.md`, and related docs.
- Acceptance/real-use test plans under `examples/real_dataset_tests/**` and `tests/bioinformatics/test_project_workflow_e2e_acceptance.py`.
- UI status wording from stage reports, if a later UX pass needs copy examples.

## 7. Boundary Check

High-risk paths in the diff:

- `app/main.py`
- `app/shell/theme.py`
- `app/shared/feature_availability.py`
- `app/shared/storage/__init__.py`
- `scripts/package_app.py`
- `pyproject.toml`
- `requirements.txt`
- `requirements-dev.txt`
- `tests/test_package_app.py`
- `tests/test_unified_entry.py`
- `tests/ui/test_feature_availability.py`

No active diff paths were found under:

- `app/shared/query_intelligence/`
- `app/shared/ai_gateway/`
- `app/meta_analysis/`

Keyword scans show legacy PubMed references under `app/bioinformatics/legacy/**`, and local Ollama placeholder wording in old Bio UI adapter code. These are not current integration candidates.

## 8. Overall Conclusion

Conclusion: **仅保留为历史架构参考**.

`codex/bioinformatics-safe-stage2` should not be merged or cherry-picked. Current `dev/bioinformatics` already covers the user-facing workflow, recognition, readiness, standardization, runner, result, and report surfaces in a newer shape. The branch is still useful as a historical design archive for project workspace contracts, acquisition-center concepts, task/result/report vocabulary, artifact manifest ideas, and E2E fixture planning.

Recommended next action: end Bio branch consolidation unless a future task explicitly asks for a design-only extraction from this archive branch.
