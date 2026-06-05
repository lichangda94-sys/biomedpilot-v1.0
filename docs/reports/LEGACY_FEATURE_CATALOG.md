# Legacy Feature Catalog

Date: 2026-06-05

Baseline: `dev/bioinformatics` at `a6ccd8c2ed8d30a769dd7eb849b0daad29e0e43f`

## Scope

This catalog covers historical code under:

```text
app/bioinformatics/legacy/**
app/meta_analysis/legacy/**
archive/legacy_sources/**
```

Current scan count for this boundary is 920 files. The count includes source, tests, static assets, archived mirrors, docs, demo data, and cached artifacts when present. It is an inventory size, not a current-feature count. The scan was refreshed at current `dev/bioinformatics` HEAD `a6ccd8c2`; no legacy file was executed or imported.

Legacy code was read only. It was not imported, executed, adapted, merged, or promoted. Legacy tests are evidence that historical code once had checks, not evidence that the current UI can run those features.

## Bioinformatics Legacy Catalog

| Legacy area | Representative files | Developed material | Current UI page/button mapping | Existing current implementation? | Real run in this audit? | Tests? | Real figure/table/report? | Old state/path dependency | Risk | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GEO standalone tool | `app/bioinformatics/legacy/geo_tool/main.py`, `geo_workflow.py`, `run_geo_tool.py`, `geo_info_fetcher.py` | Standalone GEO search/download/workflow utilities and term dictionaries | Current Bio Data Source/Search pages only conceptually | No direct current UI call should use it | No | Legacy tests/scripts only | No current output | Standalone app paths, wrappers, old requirements | High | deprecated |
| GEO processing and detector | `legacy/geo_processing/detector/*.py`, `module1_readers.py`, `module3_assets.py` | Dataset/matrix classification, readers, asset helpers | Current Recognition/Standardization/Resolver pages | Partly superseded by current contracts | No | Legacy tests only | No current output | Old detector models/config/output assumptions | Medium/high | adapter only if selected |
| GEO pipeline scripts | `legacy/geo_pipeline/*.py`, `download_geo_full_only.py`, `download_supplement_and_sra.py`, `process_geo_family_soft.py` | Historical download/process pipeline | Current data request/download pages | Current services supersede direct use | No | Legacy smoke scripts only | No current output | Network/runtime/filesystem assumptions | High | deprecated/adapter |
| TCGA/GTEx facade | `legacy/tcga_gtex/facade.py`, `adapters/*.py`, `processing/*.py`, `download/task_runner.py` | Old TCGA/GTEx search, download, parsing, normalization facade | Current TCGA/GTEx source cards and standardization pages | Current `search_center/**`, `tcga/**`, and resolver paths supersede it | No | Legacy tests only | No current output | Old locator/task-run contracts | High | rewrite |
| Lexicon and term resources | `legacy/tcga_gtex/lexicon/*.csv`, `geo_tool/*_terms.py` | Chinese/English concept dictionaries and search terms | Current search/query builder material | Resource-like overlap only | No | Legacy lexicon tests | No current output | Static curated data with unclear version lock | Medium | adapter/resource review |
| Literature CLI/GUI | `legacy/literature_cli.py`, `legacy/literature_gui.py` | Historical literature search/import tools | Meta literature import/search pages are separate current line | No | No | Legacy tests only | No current output | Old UI/runtime | High | deprecated |
| Legacy sandbox UI | `legacy/ui/module3_sandbox.py` | Old sandbox for asset viewing | No current mainline page | No | No | Legacy tests only | No current output | Old widgets and state | High | deprecated |
| Legacy docs/rules | `legacy/docs/*.md`, `configs/rules/*.json`, `configs/standards/*.yaml` | Historical contracts and audits | Current docs only by reference | No runtime | No | N/A | No current output | Stale task definitions | Medium | reference only |

## Meta Analysis Legacy Catalog

| Legacy area | Representative files | Developed material | Current UI page/button mapping | Existing current implementation? | Real run in this audit? | Tests? | Real figure/table/report? | Old state/path dependency | Risk | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Old app/workbench shell | `legacy/app/main_window.py`, `project_shell_widget.py`, `workbench_home_widget.py`, `app_meta/main_window.py` | Standalone dashboard/sidebar/workbench UI | Current Meta pages are under `app/meta_analysis/pages/**` | No | No | Legacy only | No current output | Old app state and shell | High | deprecated |
| Old Meta page set | `legacy/app_meta/ui/*.py` | Literature import, PICO search, screening, extraction, output pages | Current Meta workflow pages cover similar concepts separately | No direct current use | No | Legacy only | No current output | Old routes/state | High | reference/rewrite |
| Legacy analysis profile stack | `legacy/analysis/*.py`, `analysis_profiles/*.py` | Readiness/profile/DEG-like analysis summaries | Current v2 statistics and result contract supersede it | No | No | Legacy only | No current output | Old profile store | High | deprecated |
| Legacy extraction/rule models | `legacy/extraction/**`, `legacy/literature/**` | Data extraction schemas, import parsers, dedup, and rule helpers | Current extraction/literature pages may use similar concepts | No direct current use | No | Legacy only | No current output | Old model names/path layout | Medium/high | adapter if selected |
| Legacy fulltext/OCR/task support | `legacy/fulltext/**`, `legacy/core/task_*.py`, `legacy/scripts/run_task_once.py` | Historical fulltext and task management patterns | Current Meta fulltext/workflow dashboard pages | No direct current use | No | Legacy tests | No current output | Old task store/filesystem assumptions | High | rewrite/adapter later |
| Legacy reporting assets/widgets | `legacy/app/reporting_summary_widget.py`, `task_results_summary_widget.py`, `assets/icons/**` | Old reporting summaries and icons | Current reporting page and UI shell are separate | No runtime | No | No current proof | No current output | Old app resources | Medium | UI reference only |
| Legacy demo projects | `legacy/demo_projects/MP-2024-0007/**` | Historical sample project/logs | No direct current UI mapping | No | No | Legacy only | No current output | Fixed demo state | Medium | reference only |
| Legacy bias/readiness/profile helpers | `legacy/bias/**`, `legacy/reporting/**`, `legacy/core/dataset_readiness.py`, `legacy/core/profile_*` | Bias/readiness/profile/reporting service patterns | Current Meta quality/reporting pages only conceptually related | No direct current use | No | Legacy tests only | No current output | Old project/profile store | Medium/high | adapter only after contract mapping |
| Legacy GEO readiness under Meta | `legacy/geo_readiness/**`, `legacy/local_data/**` | Historical GEO/local-data readiness utilities inside Meta legacy tree | Current Bio recognition/standardization, not current Meta runtime | No | No | Legacy tests only | No current output | Old GEO readiness/local-data assumptions | High | rewrite/reference |
| Legacy packaging scripts | `legacy/packaging/**`, `legacy/scripts/check_packaging_readiness.py` | Old standalone Meta app packaging helpers | Current root package script only by concept | No | No | Legacy tests only | No current output | Old app bundle names and entrypoints | High | deprecated |

## Archive Findings

| Archive area | Relationship to in-app legacy | Handling |
| --- | --- | --- |
| `archive/legacy_sources/bioinformatics_project/**` | Duplicates or older snapshot of Bio legacy GEO/TCGA/literature code | Do not migrate directly; use only for provenance/reference if a current adapter task needs it. |
| `archive/legacy_sources/model9/**` | Duplicates or older snapshot of Meta legacy workbench, services, tests, docs, packaging scripts | Do not migrate directly; use only as requirements/reference after mapping to current Meta pages and contracts. |
| `dist/**` package mirrors, if present in other worktrees | Runtime package mirrors, not source-of-truth migration inputs | Exclude from source migration decisions. |

## Cross-Legacy Findings

| Finding | Impact |
| --- | --- |
| Legacy directories mix runnable scripts, old UI shells, tests, configs, static resources, demo data, and archived mirrors. | They cannot be imported as coherent current modules. |
| Some legacy utilities overlap with current recognition, standardization, resolver, search, literature, fulltext, and reporting features. | Reuse must happen through adapters or rewrites, not direct calls. |
| Legacy tests live inside legacy/archive trees. | They validate historical behavior only and must not be counted as current UI proof. |
| Legacy code contains old task systems, old result contracts, fake/dry-run paths, and standalone package scripts. | Direct migration would risk bypassing current result/package gates. |
| Static icons/contact sheets are useful for UI design, not analysis implementation. | Treat as design assets only. |

## Catalog Conclusion

Legacy contains useful requirements, terminology, visual assets, and possible helper algorithms, but no legacy feature is considered currently available from this audit alone. Every item requires a scoped migration task with a current UI entry, current contract mapping, focused tests, and real output proof before any availability claim.
