# Deprecated Legacy Register

Date: 2026-06-05

Baseline: `dev/bioinformatics` at `81225c3625022d180447b4a3fe4b2d0f7882360f`

## Deprecation Rule

An item is deprecated for direct migration when it bypasses current UI/contract boundaries, depends on old global state or old paths, produces mock/placeholder/testing-level output without clear labeling, or would replace current source of truth.

Deprecated does not mean the idea is useless. It means the code must not be copied directly into current runtime. Requirements, terminology, visual assets, or small helpers can still be re-evaluated in a later scoped adapter/rewrite task.

## Deprecated / Quarantined Items

| Item | Source | Why deprecated or quarantined | Current replacement or safe route | Risk | Final handling |
| --- | --- | --- | --- | --- | --- |
| Whole old branch merge | Any old branch | Branch deltas are large and would overwrite/delete current contracts, standard runtime scaffolds, or UI state | Select one feature and adapt to current contracts | High | deprecated |
| Legacy standalone GEO tool | `app/bioinformatics/legacy/geo_tool/**`, archive mirror | Old standalone entrypoint and wrappers bypass current project/resolver/result contracts | Current data source, recognition, standardization, and resolver pages | High | deprecated |
| Legacy GEO direct download/process scripts | `legacy/download_geo_full_only.py`, `download_supplement_and_sra.py`, `process_geo_family_soft.py`, `geo_pipeline/**` | Network/file effects and old assumptions; no current UI/result contract proof | Current data source requests and standardized repository flow | High | deprecated/adapter only |
| Legacy GEO detector as formal input resolver | `legacy/geo_processing/detector/**` | May be useful, but direct use can bypass B8-style standardized input resolver | Adapt only behind current recognition/standardization contracts | Medium/high | quarantined adapter candidate |
| Legacy TCGA/GTEx facade/task runner | `legacy/tcga_gtex/**` | Old locator/download/task contracts differ from current services | Rewrite around current `data_sources/**`, `search_center/**`, and resolver | High | rewrite |
| Legacy literature CLI/GUI in Bio legacy | `legacy/literature_cli.py`, `literature_gui.py` | Separate old app flow; overlaps Meta but not current Meta runtime | Current Meta literature/search workflow | High | deprecated |
| Legacy Bio sandbox UI | `legacy/ui/module3_sandbox.py` | Standalone sandbox not part of current UI mainline | Current Bio workflow pages | High | deprecated |
| Legacy Meta app shell/workbench | `app/meta_analysis/legacy/app/**`, `app_meta/**` | Old shell, routes, state, and visual structure would replace current UI | Current `app/meta_analysis/pages/**` | High | deprecated |
| Legacy Meta analysis/profile stack | `app/meta_analysis/legacy/analysis/**`, `analysis_profiles/**` | Old profile/result contracts conflict with current v2 statistics contract | Current Meta v2 statistics and result contract bridge | High | deprecated |
| Legacy Meta task runner real-run controls | `legacy/core/task_*.py`, `legacy/tests/test_main_window_reporting_summary.py` | Uses old task state, dry-run/real-run text gates, and old adapter model | Rebuild only through current Meta canonical run/artifact contract | High | deprecated/rewrite |
| Legacy Meta reporting widgets | `legacy/app/reporting_summary_widget.py`, `task_results_summary_widget.py` | Old widgets tied to old shell and output assumptions | Current Meta reporting page/services | Medium/high | UI reference only |
| Legacy Meta bias/profile/readiness stores | `legacy/bias/**`, `legacy/reporting/**`, `legacy/core/profile_*`, `legacy/analysis_profiles/**` | Old profile-store and readiness concepts conflict with current canonical Meta run/artifact contract | Re-evaluate only behind current Meta result contract | Medium/high | quarantined adapter candidate |
| Legacy Meta GEO/local readiness utilities | `legacy/geo_readiness/**`, `legacy/local_data/**` | GEO/local dataset readiness belongs behind current Bio recognition/standardization or a scoped Meta import contract, not old Meta state | Use as requirements/reference only | High | rewrite/reference |
| Legacy Meta packaging scripts | `legacy/packaging/**`, `legacy/scripts/check_packaging_readiness.py` | Old app bundle entrypoints and package names do not match current root package workflow | Current `scripts/package_app.py` and LaunchServices gates | High | deprecated |
| Legacy pycache | `app/**/legacy/**/__pycache__/*.pyc` | Machine-local compiled artifacts | None | High | ignore/remove only in explicit cleanup task |
| Archive mirror code | `archive/legacy_sources/**` | Duplicates old Bio/Meta source snapshots with stale paths | Use only as provenance/reference | High | reference only |
| Mock result packages as real analysis proof | `analysis/fixtures/outputs/*/mock_result_package/**` | Explicit mock packages | Use only for contract tests | Medium | testing-only |
| Lite standard worker fixtures as production proof | `analysis/modules/**`, `analysis/fixtures/inputs/**`, `analysis/runners/run_module.R` | Lite worker scaffolds are useful but not full current production proof | Prove each selected module through current UI and result package | Medium | scaffold only |
| Runtime gene-set downloads as resource readiness proof | old Bio branches, historical enrichment resource code, and any direct Reactome/GO/KEGG download shortcut | Current `25e179d` policy blocks runtime gene-set downloads by default; resource readiness must come from explicit import or prelocked resource packages | Use current resource-lock/import contracts and visible blockers | High | quarantined |
| Branch-only UI shell/screenshots | `dev/ui-shell`, `integration/*ui*`, branch `docs/ui/**` material | Design material cannot replace current UI without selected UI migration task | Use as design reference | Medium | adapter/design review |
| Branch-only risk/nomogram clinical material | ReleaseBuild/internal-test branches | High risk of clinical overclaim and old state coupling | Rewrite under strict non-clinical gates if selected | High | rewrite |
| Branch-only OCR/fulltext engines | `dev/meta-analysis`, OCR branches | External dependency and package divergence; not current-proven | Adapter behind current Meta fulltext contracts | High | rewrite/adapter later |
| Runtime or branch-only resource download behavior | old Bio branches and some resource-manager history | User-triggered or silent resource downloads can conflict with current detect/import/lock governance | Use current resource-lock or explicit import contracts only | High | quarantined |

## Not Deprecated, But Not Automatically Available

| Item | Status |
| --- | --- |
| Current formal DEG loop | Current implementation exists, but availability still depends on gates and prior proofs; not generalized to every DEG scenario. |
| Current Meta v2 result contract bridge | Current implementation exists and remains testing-level; not production-grade Meta. |
| Current ORA/GSEA/survival/Cox/risk/report/immune/correlation modules | Current or branch material exists. Each module remains governed by its current gate and proof status. |
| Current standard analysis runtime | Useful scaffold; mock/lite/full modes must stay labeled and gated. Recent full-mode environment snapshots are blocker evidence, not proof that full production analyses ran. |
| Current external R command boundary | Useful isolation boundary; does not by itself prove any module's full scientific output. |
| Current docking lite command-manifest contract | Current testing-level contract only; no AutoDock Vina execution or scientific docking result. |

## Register Conclusion

Deprecated and quarantined items must not be used as shortcuts. The next migration phase must choose one candidate, one current UI entry, one contract bridge, and one focused test plan.

## 2026-06-05 Refresh Notes

This register was refreshed after current-line standard package gate hardening reached HEAD `81225c3625022d180447b4a3fe4b2d0f7882360f`. The refresh did not remove any item from quarantine. The stronger current package gates make direct legacy migration less acceptable, not more acceptable, because legacy code still has to preserve current provenance, semantics, task logs, artifact validation, and UI disabled-reason boundaries.

Additional direct-migration blockers retained:

| Blocker | Reason |
| --- | --- |
| Old branch as source of truth | Would bypass the current UI-only mainline and may overwrite newer standard package/runtime contracts. |
| Legacy or archive runner path | May rely on old state directories, fake/dry-run controls, or old project stores. |
| Branch-only report/plot/output | Not current runtime evidence unless a current UI path and current result contract prove it. |
| Mock/lite standard package | Useful for contract tests only; cannot be called production or clinical output. |

No deprecated or quarantined item was promoted in this audit.
