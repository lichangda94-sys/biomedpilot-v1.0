# Legacy Feature Catalog

Date: 2026-06-04

Baseline: `dev/bioinformatics` at `a471a25a9153b23c224ea7a96e425c44de92ee5e`

## Scope

This catalog covers historical code under:

```text
app/bioinformatics/legacy/**
app/meta_analysis/legacy/**
```

Legacy code was read only. It was not imported, executed, adapted, or promoted. Legacy tests are evidence that historical code once had checks, not evidence that the current UI can run those features.

## Bioinformatics Legacy Catalog

| Legacy area | Representative files | Developed material | Current UI/page mapping | Current implementation? | Real run evidence in this audit? | Tests? | Real output claim allowed? | Old state/path dependency | Risk | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GEO standalone tool | `legacy/geo_tool/main.py`, `geo_workflow.py`, `run_geo_tool.py`, `geo_info_fetcher.py` | Standalone GEO search/download/workflow utilities with term dictionaries | Current Bio data source/search pages only indirectly related | No direct current UI call should use it | No | Legacy tests/scripts only | No | Standalone app paths and old wrappers | High | deprecated |
| GEO processing and detector | `legacy/geo_processing/detector/*.py`, `module1_readers.py`, `module3_assets.py` | Dataset/matrix classification, readers, asset helpers | Current recognition/standardization/resolver pages | Partly superseded by current recognition and standardization contracts | No | Legacy tests | No | Old detector models and config | Medium/high | adapter only if selected |
| GEO pipeline scripts | `legacy/geo_pipeline/*.py`, `download_geo_full_only.py`, `download_supplement_and_sra.py`, `process_geo_family_soft.py` | Historical download/process pipeline | Current data source request/download pages | Current services supersede direct use | No | Legacy smoke scripts only | No | Network/runtime/filesystem assumptions | High | deprecated/adapter |
| TCGA/GTEx facade | `legacy/tcga_gtex/facade.py`, `adapters/*.py`, `processing/*.py`, `download/task_runner.py` | Old TCGA/GTEx search, download, parsing, normalization facade | Current TCGA/GTEx source cards and standardization pages | Current `data_sources/**` and `search_center/**` supersede it | No | Legacy tests | No | Old locator/task-run contracts | High | rewrite |
| Lexicon and term resources | `legacy/tcga_gtex/lexicon/*.csv`, `geo_tool/*_terms.py` | Chinese/English concept dictionaries and search terms | Current search/query builder material | Resource-like overlap only | No | Legacy lexicon tests | No | Static curated data; version unclear | Medium | adapter/resource review |
| Literature CLI/GUI | `legacy/literature_cli.py`, `legacy/literature_gui.py` | Historical literature search/import tools | Meta literature import/search pages are separate current line | No | No | Legacy tests | No | Old UI/runtime | High | deprecated |
| Legacy sandbox UI | `legacy/ui/module3_sandbox.py` | Old sandbox for asset viewing | No current mainline page | No | No | Legacy tests | No | Old widgets and state | High | deprecated |
| Legacy docs/rules | `legacy/docs/*.md`, `configs/rules/*.json`, `configs/standards/*.yaml` | Historical contracts and audits | Current docs only by reference | No runtime | No | N/A | No | Stale task definitions | Medium | reference only |
| Pycache under legacy | `legacy/**/__pycache__/*.pyc` | Compiled artifacts | None | No | No | No | No | Machine-local cache | High | ignore/deprecated |

## Meta Analysis Legacy Catalog

| Legacy area | Representative files | Developed material | Current UI/page mapping | Current implementation? | Real run evidence in this audit? | Tests? | Real output claim allowed? | Old state/path dependency | Risk | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Old app/workbench shell | `legacy/app/main_window.py`, `project_shell_widget.py`, `workbench_home_widget.py`, `app_meta/main_window.py` | Standalone dashboard/sidebar/workbench UI | Current Meta pages are under `app/meta_analysis/pages/**` | No | No | Legacy only | No | Old app state and shell | High | deprecated |
| Old Meta page set | `legacy/app_meta/ui/*.py` | Literature import, PICO search, screening, extraction, output pages | Current Meta workflow pages cover similar concepts separately | No direct current use | No | Legacy only | No | Old routes/state | High | reference/rewrite |
| Legacy analysis profile stack | `legacy/analysis/*.py`, `analysis_profiles/*.py` | Readiness/profile/DEG-like analysis summaries | Current v2 statistics and result contract supersede it | No | No | Legacy only | No | Old profile store | High | deprecated |
| Legacy extraction/rule models | `legacy/extraction/**`, `legacy/rules/**` | Data extraction schemas and rule helpers | Current extraction pages/services may use similar concepts | No direct current use | No | Legacy only | No | Old model names and path layout | Medium/high | adapter if selected |
| Legacy reporting assets/widgets | `legacy/app/reporting_summary_widget.py`, `task_results_summary_widget.py`, `assets/icons/**` | Old reporting summaries and icons | Current reporting page and UI shell are separate | No runtime | No | No current proof | No | Old app resources | Medium | UI reference only |
| Legacy icon/contact sheets | `legacy/assets/icons/**`, `legacy/assets/meta_icons/**` | Visual asset library | UI design material | No runtime | No | No | No analysis output | Static assets | Low/medium | adapter/design review |

## Cross-Legacy Findings

| Finding | Impact |
| --- | --- |
| Legacy directories mix runnable scripts, old UI shells, tests, configs, static resources, and pycache. | They cannot be imported as a coherent current module. |
| Some legacy utilities overlap with current recognition, standardization, resolver, search, literature, and reporting features. | Reuse must happen through adapters or rewrites, not direct calls. |
| Legacy tests are stored inside legacy directories. | They validate historical behavior only and must not be counted as current UI proof. |
| Legacy code contains old task systems and old result contracts. | Direct migration would risk bypassing current result/package gates. |

## Catalog Conclusion

Legacy contains useful requirements, terminology, and possible helper algorithms, but no legacy feature is considered current available from this audit alone. Every item requires a scoped migration task with a current UI entry, current contract mapping, focused tests, and real output proof before any availability claim.
