# Deprecated Legacy Register

Date: 2026-06-04

Baseline: `dev/bioinformatics` at `a471a25a9153b23c224ea7a96e425c44de92ee5e`

## Deprecation Rule

An item is deprecated for direct migration when it bypasses current UI/contract boundaries, depends on old global state or old paths, produces mock/placeholder/testing-level output without clear labeling, or would replace current source of truth.

Deprecated does not mean the idea is useless. It means the code must not be copied directly into current runtime. Requirements or small helpers can still be re-evaluated in a later scoped adapter/rewrite task.

## Deprecated / Quarantined Items

| Item | Source | Why deprecated or quarantined | Current replacement or safe route | Risk | Final handling |
| --- | --- | --- | --- | --- | --- |
| Whole old branch merge | Any old branch | Branch deltas are large and would overwrite/delete current contracts, standard runtime scaffolds, or UI state | Select one feature and adapt to current contracts | High | deprecated |
| Legacy standalone GEO tool | `app/bioinformatics/legacy/geo_tool/**` | Old standalone entrypoint and wrappers bypass current project/resolver/result contracts | Current data source, recognition, standardization, and resolver pages | High | deprecated |
| Legacy GEO direct download/process scripts | `legacy/download_geo_full_only.py`, `download_supplement_and_sra.py`, `process_geo_family_soft.py`, `geo_pipeline/**` | Network/file effects and old assumptions; no current UI/result contract proof | Current data source requests and standardized repository flow | High | deprecated/adapter only |
| Legacy GEO detector as formal input resolver | `legacy/geo_processing/detector/**` | May be useful, but direct use can bypass B8-style standardized input resolver | Adapt only behind current recognition/standardization contracts | Medium/high | quarantined adapter candidate |
| Legacy TCGA/GTEx facade/task runner | `legacy/tcga_gtex/**` | Old locator/download/task contracts differ from current services | Rewrite around current `data_sources/**`, `search_center/**`, and resolver | High | rewrite |
| Legacy literature CLI/GUI in Bio legacy | `legacy/literature_cli.py`, `literature_gui.py` | Separate old app flow; overlaps Meta but not current Meta runtime | Current Meta literature/search workflow | High | deprecated |
| Legacy Bio sandbox UI | `legacy/ui/module3_sandbox.py` | Standalone sandbox not part of current UI mainline | Current Bio workflow pages | High | deprecated |
| Legacy Meta app shell/workbench | `app/meta_analysis/legacy/app/**`, `app_meta/**` | Old shell, routes, state, and visual structure would replace current UI | Current `app/meta_analysis/pages/**` | High | deprecated |
| Legacy Meta analysis/profile stack | `app/meta_analysis/legacy/analysis/**`, `analysis_profiles/**` | Old profile/result contracts conflict with current v2 statistics contract | Current Meta v2 statistics and result contract bridge | High | deprecated |
| Legacy Meta reporting widgets | `legacy/app/reporting_summary_widget.py`, `task_results_summary_widget.py` | Old widgets tied to old shell and output assumptions | Current Meta reporting page/services | Medium/high | UI reference only |
| Legacy pycache | `app/**/legacy/**/__pycache__/*.pyc` | Machine-local compiled artifacts | None | High | ignore/remove only in explicit cleanup task |
| Mock result packages as real analysis proof | `analysis/fixtures/outputs/*/mock_result_package/**` | Explicit mock packages | Use only for contract tests | Medium | testing-only |
| Lite standard worker fixtures as production proof | `analysis/modules/**`, `analysis/fixtures/inputs/**`, `analysis/runners/run_module.R` | Lite worker scaffolds are useful but not current production proof | Prove each selected module through current UI and result package | Medium | scaffold only |
| Branch-only UI shell/screenshots | `dev/ui-shell`, `integration/*ui*`, branch `docs/ui/**` material | Design material cannot replace current UI without selected UI migration task | Use as design reference | Medium | adapter/design review |
| Branch-only risk/nomogram clinical material | ReleaseBuild/internal-test branches | High risk of clinical overclaim and old state coupling | Rewrite under strict non-clinical gates if selected | High | rewrite |
| Branch-only OCR/fulltext engines | `dev/meta-analysis`, OCR branches | External dependency and package divergence; not current-proven | Adapter behind current Meta fulltext contracts | High | rewrite/adapter later |

## Not Deprecated, But Not Automatically Available

| Item | Status |
| --- | --- |
| Current formal DEG loop | Current implementation exists, but availability still depends on gates and prior proofs; not generalized to every DEG scenario. |
| Current Meta v2 result contract bridge | Current implementation exists and remains testing-level; not production-grade Meta. |
| Current ORA/GSEA/survival/Cox/risk/report modules | Current or branch material exists, but each remains governed by its current gate and proof status. |
| Current standard analysis runtime | Useful scaffold; mock/lite/full modes must stay labeled and gated. |

## Register Conclusion

Deprecated and quarantined items must not be used as shortcuts. The next migration phase must choose one candidate, one current UI entry, one contract bridge, and one focused test plan.
