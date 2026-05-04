# BioMedPilot Mainline Boundary Notice

This directory is a historical Bioinformatics snapshot. It is not the current
BioMedPilot Bioinformatics mainline runtime path.

`literature_cli.py` and `literature_gui.py` are legacy-compatible literature
utilities kept with the old GEO snapshot. They do not belong to the current
Bioinformatics product boundary. Current Bioinformatics does not own PubMed,
PICO/PICOS, literature screening, NBIB/RIS/Zotero/EndNote import, or Meta
Analysis workflows.

New BioMedPilot feature work must not import these legacy literature files.
They may be moved to an archive or removed only in a separately approved
housekeeping stage.

# GEO Mainline, Module Map, and Utilities

This repository is organized around one GEO mainline plus shared module layers:

- `geo_tool/`: desktop GUI, launcher wrappers, and the main end-user entrypoint
- `geo_pipeline/`: Module 1 GEO retrieval and processing pipeline entry surfaces
- `geo_processing/`: shared validator, detector, Module 1 contracts/readers, and Module 3 asset helpers
- `ui/`: Module 3 sandbox UI and formatting helpers
- `configs/`, `scripts/`, `tcga_gtex/`: Module 4 rules, generators, and TCGA/GTEx facade resources
- `tests/`: regression, compatibility, smoke, and structure checks
- `literature_cli.py` / `literature_gui.py`: legacy-compatible literature utilities kept alongside the GEO mainline

The canonical cross-platform GUI entrypoint is:

```bash
python geo_tool/run_geo_tool.py
```

Detailed structure and audit notes live in [`docs/repo_structure_audit.md`](docs/repo_structure_audit.md).
The current staged acceptance baseline lives in
[`docs/mainline_acceptance_baseline.md`](docs/mainline_acceptance_baseline.md).

## Repo-root quickstart

Run commands from the repo root unless a script explicitly says otherwise.

Minimal reproduction path:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r geo_tool/requirements.txt
python geo_tool/run_geo_tool.py --check
python scripts/run_smoke_tests.py
python geo_tool/run_geo_tool.py
```

On macOS/Linux you can still use the wrapper scripts:

```bash
./geo_tool/bootstrap_geo_tool.sh
./geo_tool/run_geo_tool.sh
```

Windows wrappers are also available:

```bat
geo_tool\bootstrap_geo_tool.bat
geo_tool\run_geo_tool.bat --check
geo_tool\run_geo_tool.bat
```

Windows note:

- use `py -3 -m venv .venv`
- use `.venv\Scripts\python.exe -m pip install --upgrade pip`
- use `.venv\Scripts\python.exe -m pip install -r geo_tool/requirements.txt`
- check with `.venv\Scripts\python.exe geo_tool\run_geo_tool.py --check`
- smoke test with `.venv\Scripts\python.exe scripts\run_smoke_tests.py`
- launch with `py -3 geo_tool/run_geo_tool.py`

The canonical cross-platform entrypoint is:

```bash
python geo_tool/run_geo_tool.py
```

`geo_tool/requirements.txt` layers GUI dependencies on top of the repo-root `requirements.txt`.

## Mainline Surface Contract

The current GEO mainline is frozen around one minimal formal surface set. New
mainline work should extend only these canonical surfaces.

Canonical surface:

- `geo_tool/run_geo_tool.py`
- `geo_tool/main.py`
- `geo_tool/geo_workflow.py`
- `geo_pipeline.download.download_core_geo_records`
- `geo_pipeline.process.process_from_local_family_soft`
- `geo_processing.validate_downloaded_dataset`
- `geo_processing.detect_dataset`
- `geo_processing.load_module1_dataset_context`

Wrapper surface:

- `geo_tool/run_geo_tool.sh`
- `geo_tool/run_geo_tool.bat`
- `geo_tool/bootstrap_geo_tool.sh`
- `geo_tool/bootstrap_geo_tool.bat`

Legacy surface:

- `download_geo_full_only.py`
- `process_geo_family_soft.py`
- `download_supplement_and_sra.py`

Duplicate surface:

- `geo_tool/geo_pipeline/`
- `geo_pipeline.download.download_full_family_soft`

Rules:

- Only the canonical surface above may continue as the formal GEO mainline.
- Wrapper surfaces are compatibility launch helpers and must continue to
  delegate to `geo_tool/run_geo_tool.py`.
- Legacy and duplicate surfaces are kept for compatibility only and should not
  be reattached to `geo_tool/main.py` or `geo_tool/geo_workflow.py`.
- Module 4 resources such as `tcga_gtex/` remain outside the canonical GEO
  workflow stage. They are exposed only as a `geo_tool/main.py` routed optional
  runtime path through the query/result routing layer.

## Module 4 Main.py Routed Optional Runtime Contract

Module 4 is currently `main.py routed optional runtime path`.

Frozen rules:

- The only allowed integration point for Module 4 is `geo_tool/main.py` during
  the query/result routing stage.
- `geo_tool/geo_workflow.py` is a forbidden integration point for Module 4.
- `search_tcga_gtex` and `resolve_tcga_gtex_files` are reachable from the main
  GUI as an optional TCGA/GTEx query/result route.
- For records with `local_path`, `download_url`, or metadata locator,
  `download_tcga_gtex_dataset -> build_tcga_gtex_bundle ->
  get_tcga_gtex_summary` can run as a minimal local/mockable runtime.
- Missing locators must return a clear failed result; they must not be reported
  as successful downloads.
- Module 4 must not be described as a canonical GEO workflow stage or as a
  production-grade TCGA/GDC/GTEx downloader.

## Stage Acceptance Baseline

The repository currently has a reusable staged acceptance baseline for the GEO
mainline. This is not a final product release.

Current baseline statements:

- The canonical GEO mainline is
  `geo_tool/run_geo_tool.py -> geo_tool/main.py -> geo_tool/geo_workflow.py`.
- Module 1 is the current formal GEO download / validation / detection /
  processing path.
- Module 3 is currently `mainline post-workflow action`: workflow results show
  Module 3 handoff / standard asset status, and the current GSE can be opened
  into the Module 3 workspace after workflow completion.
- Module 4 is currently `main.py routed optional runtime path`: the main GUI can
  route TCGA/GTEx search / resolve results and optionally run the minimal local
  runtime when records provide a locator.
- Module 9 is the current minimal mainline viability gate.

The current baseline must not be described as:

- a final product release;
- a fully completed multi-module platform;
- `Module 3` as a canonical workflow stage;
- `Module 4` as a canonical GEO workflow stage;
- `Module 4` as a production-grade TCGA/GDC/GTEx downloader.

## Directory map

- `configs/`: shared standards, rule JSON, comparison configs, and gene panels
- `docs/`: design notes and structure audit documentation
- `geo_pipeline/`: reusable GEO download / process package
- `geo_processing/`: shared contracts, validators, detector models, and Module 3 asset layout helpers
- `geo_tool/`: GUI app, launch scripts, MeSH assets, and workflow wrappers
- `scripts/`: smoke/test runners and Module 4 lexicon build/audit scripts
- `tcga_gtex/`: separate TCGA/GTEx facade, adapters, models, and lexicon layer
- `tests/`: repo smoke, Module 1, Module 3, Module 4, downloader, detector, facade, and literature regression tests
- `ui/`: Module 3 sandbox window and formatting-only helpers

## Minimal verification path

Key structure checks:

```bash
python geo_tool/run_geo_tool.py --check
./geo_tool/run_geo_tool.sh --check
python -m unittest tests.test_repo_smoke
python scripts/run_smoke_tests.py
```

`python scripts/run_smoke_tests.py` is the repo-root minimal gate for GEO
mainline viability and should cover the frozen surface contract, detector smoke,
workflow integration smoke, and launcher `--check`.

Mainline and Module 1 / Module 3 regression checks:

```bash
python -m unittest tests.test_download_validator
python -m unittest tests.test_geo_downloader
python -m unittest tests.test_module1_readers
python -m unittest tests.test_geo_workflow_integration
python -m unittest tests.test_module3_sandbox
```

Module 4 and facade checks:

```bash
python -m unittest tests.test_english_core_lexicon
python -m unittest tests.test_lexicon_coverage_audit
python -m unittest tests.test_module4_mainline_bridge
python -m unittest tests.test_tcga_gtex_facade
```

## Desktop GUI

Run directly from the project:

```bash
python3 literature_gui.py
```

If the desktop launcher has been created, double-click:

- `~/Desktop/Literature Search App.command`

GUI features:

- keyword search
- cached result loading
- paginated viewing
- multi-select results
- fetch more results
- fetch all results
- download selected items
- translate selected items

## CLI

Interactive menu:

```bash
python3 literature_cli.py --menu
```

The search cache is stored in `literature_output/_cache/`.

Direct command examples:

```bash
python3 literature_cli.py --query "thyroid cancer" --max-results 1000 --page-size 20 --show-page 1
python3 literature_cli.py --query "thyroid cancer" --max-results 1000 --page-size 20 --fetch-more 200 --show-page 5
python3 literature_cli.py --query "thyroid cancer" --max-results all --page-size 50 --show-page 1
python3 literature_cli.py --query "thyroid cancer" --load-cache --show-page 1
python3 literature_cli.py --query "thyroid cancer" --max-results 1000 --page-size 20 --select 1,3-5 --download
python3 literature_cli.py --query "thyroid cancer" --max-results 1000 --page-size 20 --select 1-2 --download --translate
```

## Search behavior

- Search parameters are centralized in `SearchConfig`
- `max_results`, `page_size`, and `start` are configurable
- Default safety cap is `1000`; pass `--max-results all` to fetch everything
- Search loops through PubMed pages until it reaches `max_results` or no more results are available
- Result IDs are deduplicated across pages to avoid duplicates
- Search, selection, download, and translation are separate functions and can be run independently
- The UI shows `已抓取 / 总命中 / 是否抓完整` so you can tell whether you are choosing from a complete set
- Search cache is written after search, fetch-more, and selection so you can resume without re-querying PubMed

## Output

Outputs are saved to `literature_output/<query>_<timestamp>/`:

- `search_results.json`
- `search_results.csv`
- `translations.json`
- downloaded PDFs when PubMed Central full text is available

Cache files are saved to `literature_output/_cache/<query>.json`.

## Existing GEO modules

Compatibility-only GEO scripts still present at repo root:

- `download_geo_full_only.py`
- `process_geo_family_soft.py`
- `download_supplement_and_sra.py`

They are preserved as compatibility surfaces and are not part of the frozen
mainline formal call set.

For new work, mark the target line explicitly at the start of the prompt, for example:

- `【主线】`
- `【模块1】`
- `【模块3】`
- `【模块4】`
- `【模块9】`
- `【仓库整理】`
- `【新线路：xxx】`
