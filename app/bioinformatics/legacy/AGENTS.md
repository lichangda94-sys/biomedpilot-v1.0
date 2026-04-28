# AGENTS.md

## Purpose
- This file defines shared working rules for all Codex threads in this repo.
- Default goal: make minimal, compatible, test-backed changes without broad refactors.
- Unless a task explicitly says otherwise, treat current code and tests as the source of truth even if `README.md` lags behind.

## Working Defaults
- Run commands from repo root by default unless a section explicitly says otherwise.
- Prefer minimal-scope edits in the module you were asked to change.
- Prefer updating generators/scripts over hand-editing generated artifacts.
- Do not add absolute paths or machine-specific paths to source, configs, scripts, or docs.
- Do not introduce new dependencies unless the task explicitly requires them.

## Repo Snapshot
- `geo_pipeline/`: main GEO download and processing implementation.
- `geo_processing/`: shared GEO validation, detector, Module 1 contracts/readers, and shared models.
- `geo_tool/`: desktop GUI, GEO workflow, search entrypoints, launcher scripts, and some legacy-compatible wrappers.
- `ui/`: Module 3 sandbox UI and formatting helpers.
- `tcga_gtex/`: separate TCGA/GTEx facade, adapters, lexicon, models, and search layer.
- `configs/`: shared standards and config contracts.
- `scripts/`: build/audit scripts for lexicon and related assets.
- `tests/`: regression tests and compatibility coverage.
- `docs/`: design and refactor planning notes.

## Module Boundaries
- Module 1: retrieval and data ingress for GEO.
  - Scope: search entry, download planning/execution, validation, semantic classification, handoff outputs.
  - Status: maintain and fix bugs, but not the current main refactor target.
- Module 3: standard assets and asset-facing consumption layer.
  - Current highest priority.
- Module 4: configuration and rules.
  - Includes comparison config, gene panels, keywords, lexicon, mapping/rule logic.
- Module 9: tests, packaging, localization.
- Out of scope unless explicitly requested:
  - DEG / GSEA / survival analysis
  - batch-correction engines
  - GEO main-chain rewrite
  - TCGA/GTEx expansion beyond the requested task
  - broad UI rewrites

## Canonical Entrypoints
- Prefer these public/shared entrypoints:
  - `geo_pipeline.download.download_core_geo_records`
  - `geo_processing.download_validator.validate_downloaded_dataset`
  - `geo_processing.detector.dataset_detector.detect_dataset`
  - `geo_processing.load_module1_dataset_context`
  - `geo_tool.geo_workflow.run_download_and_process_workflow`
  - `tcga_gtex.facade`
- Treat these as legacy/duplicate surfaces unless the task explicitly targets them:
  - `geo_tool/geo_pipeline/`
  - `download_geo_full_only.py`
  - `process_geo_family_soft.py`
  - `download_supplement_and_sra.py`

## Shared Contracts And High-Risk Files
- Change these carefully because they affect multiple modules and threads:
  - `geo_processing/module1_contracts.py`
  - `geo_processing/module1_readers.py`
  - `geo_processing/download_models.py`
  - `geo_processing/download_validator.py`
  - `geo_processing/detector/models.py`
  - `configs/standards/asset_contract_v1.yaml`
  - `tcga_gtex/models/common.py`
  - `tcga_gtex/lexicon/*.csv`
- If you must change a shared file, keep the change incremental and call out:
  - why the shared file had to change
  - which entrypoints are affected
  - compatibility risk
  - the minimum tests you ran

## Module 1 Contract Rules
- `module1_handoff.json` is the default consumption output for Module 1.
- `file_inventory.json`, `parser_hints.json`, and `dataset_manifest_draft.json` are supporting outputs.
- Consumption rule: new schema first, legacy fields as fallback.
- Prefer `load_module1_dataset_context()` over direct scattered JSON field reads.
- Do not delete old fields.
- Do not delete `legacy_status`.
- Do not break `selected_results.csv` legacy export.
- Do not replace `RemoteCandidate`, `FileScoreResult`, or `DownloadValidationResult`.

## Owned Areas For Parallel Work
- Default owned areas:
  - Module 3 thread: `ui/`, Module 3 consumption code in `geo_processing/`, and related tests.
  - Module 4 thread: `configs/`, `scripts/`, `tcga_gtex/lexicon/`, mapping/rule logic, and related tests.
  - Module 9 thread: `tests/`, packaging scripts, launch/bootstrap scripts, localization-related assets.
  - Module 1 maintenance thread: `geo_processing/`, `geo_pipeline/`, `geo_tool/geo_info_fetcher.py`, `geo_tool/geo_workflow.py`, and related Module 1 tests.
- Use these owned areas by default.
- Cross-area edits require an explicit reason in the final report.
- Keep cross-area changes to the smallest possible shared surface.

## Running And Testing
- Default working directory: repo root.
- Environment/bootstrap references:
  - `geo_tool/requirements.txt`
  - `geo_tool/bootstrap_geo_tool.sh`
  - `geo_tool/run_geo_tool.sh`
- Common commands:
  - GUI: `cd geo_tool && ./run_geo_tool.sh`
  - GEO tests: `python3 -m unittest ...`
  - Literature CLI: `python3 literature_cli.py --menu`

## Minimal Test Matrix
- If you change Module 1 contracts/readers/validator/workflow, run at least:
  - `python3 -m unittest tests.test_module1_readers`
  - `python3 -m unittest tests.test_download_validator`
  - `python3 -m unittest tests.test_geo_workflow_integration`
  - Add `tests.test_geo_downloader` when download planning/execution changes.
- If you change Module 3 sandbox or standard-asset-facing UI consumption, run at least:
  - `python3 -m unittest tests.test_module3_sandbox`
- If you change Module 4 lexicon/rules/query mapping, run at least:
  - `python3 -m unittest tests.test_english_core_lexicon`
  - `python3 -m unittest tests.test_lexicon_coverage_audit`
  - Add `tests.test_tcga_gtex_facade` when facade behavior may shift.
- If you change TCGA/GTEx facade/adapters/models, run at least:
  - `python3 -m unittest tests.test_tcga_gtex_facade`

## Verifying Contracts Are Not Broken
- Confirm relevant outputs still generate and remain consumable:
  - `selected_results.json`
  - `download_plan.json`
  - `download_receipt.json`
  - `file_inventory.json`
  - `parser_hints.json`
  - `dataset_manifest_draft.json`
  - `module1_handoff.json`
- Confirm readers still support:
  - new schema first
  - legacy fallback
- Confirm workflow/UI/sandbox consumers still read through shared adapters where expected.
- When changing generated artifacts or lexicon/config outputs, prefer updating the generator or source data and regenerate, rather than patching only the emitted file.

## Forbidden Moves
- Do not refactor unrelated modules while touching a local bug or feature.
- Do not change UI, main workflow, or facade layers unless the task explicitly requires it.
- Do not rewrite GEO main-chain behavior unless explicitly requested.
- Do not touch DEG / GSEA / survival analysis unless explicitly requested.
- Do not modify TCGA/GTEx code for a GEO-only task unless explicitly requested.
- Do not delete legacy paths or outputs just because a newer path exists.
- Do not add unrelated new dependencies.
- Do not commit machine-local paths, temporary directories, or environment-specific assumptions.

## Done Criteria
- Change scope is narrow and matches the requested module.
- Shared contracts remain compatible, or compatibility impact is explicitly documented.
- Minimum relevant tests pass.
- No unrelated files or modules were opportunistically changed.

## Final Report Format
- Use this exact section order in final summaries:
  - `修改文件`
  - `改动摘要`
  - `兼容性影响`
  - `测试结果`
  - `风险点`
  - `遗留问题`
  - `下一步建议`
