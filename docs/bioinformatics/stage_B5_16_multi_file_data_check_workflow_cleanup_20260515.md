# B5.16 Multi-file Import and Data Check Workflow Cleanup

## Stage Goal

B5.16 cleans up the Bioinformatics data import, pending dataset, data check, and standardization preparation workflow. The UI now treats recognition and readiness as one user-facing stage named `数据检查与准备`, while the backend still keeps recognition and ready check as separate artifacts and service calls.

## Multi-file Display Fixes

- Local multi-file import continues to write the full `source_files` list through acquisition records, handoff manifests, and source manifests.
- The pending dataset table expands local multi-file batches into file-level rows instead of showing only the acquisition batch or first file.
- The unified data check page shows each pending file as an independent file status row before and after running checks.
- GEO selected asset download still uses the existing `source_files` based file expansion path; B5.13 / B5.14 selected-download handoff behavior was not collapsed back to dataset-level rows.

## UI Merge

- The main data source bottom button is now `下一步：数据检查与准备`.
- Workspace navigation from data import, Chinese dataset search, and acquisition status now opens the unified readiness/data-check page directly.
- The page title is `数据检查与准备`.
- The page is structured as:
  - `第一步：数据检查`: file-level recognition + ready check status table.
  - `数据集级 readiness 汇总`: dataset-level readiness checks.
  - `推荐分组`: preview-only grouping recommendation and confirmation actions.
  - `GSEA 基因集选择`: post-data-check resource status and resource-manager entry.
  - `待办清单` and analysis capability matrix for non-GSEA data-preparation actions.

## Backend Separation

- Recognition remains in `app/bioinformatics/project_recognition.py`.
- Ready check remains in `app/bioinformatics/project_readiness.py`.
- The unified UI action runs recognition first, then readiness, and stores both outputs separately.
- `logs/recognition/recognition_report.json` and `logs/readiness/readiness_report.json` remain separate artifacts.

## Main Operation Rename

- The old main UI wording `重新检查` was removed from the Bioinformatics workflow page code.
- First run button: `运行数据检查`.
- Existing result button: `重新运行数据检查`.
- The action refreshes recognition and ready check only; it does not run standardization, DEG, GSEA, or any analysis.

## File-level Status Table

The new file-level table is exposed as `dataCheckFileStatusTable` and shows:

- File name.
- Type / suffix.
- Source: local import or GEO download.
- Current status.
- Expected use / pending recognition.
- Available content.
- Missing content / risk.
- Action.

Status colors:

- Gray: not checked.
- Green: check passed / can enter later standardization confirmation.
- Yellow: needs user confirmation or supplementation.
- Red: unusable / unsupported / check failed.

Imported DEG is yellow and explicitly marked as external/imported result, not an expression matrix for recalculation. RAW / heavy files remain red and cannot be standardization input.

## Dataset-level Readiness

`run_project_readiness()` now writes `dataset_readiness` into the readiness report. It summarizes:

- Expression matrix availability.
- Sample metadata availability.
- Confirmed group design or recommended group presence.
- Species and gene ID type evidence.
- Platform annotation need.
- Imported DEG presence and non-recalculation warning.
- Standardization confirmation gate.
- DEG preflight gate.
- GSEA data basis.

File-level state answers "what is each file". Dataset-level readiness answers "can this dataset continue".

## Recommended Group Display

The unified page now renders a `推荐分组` section with:

- Recommended comparison name.
- Case and control group names.
- Per-group sample counts.
- Sample ID previews.
- Evidence field.
- Confidence.
- Explicit status that user confirmation is required.

Actions are present for confirming, modifying, rejecting, or handling later. The recommendation is not written to final group design until the user confirms it.

## GSEA Gene Set / GMT Handling

GMT is no longer treated as a missing GEO / TCGA / GTEx data file in readiness.

The UI now shows:

- `GSEA 基因集：未选择`
- Explanation that gene sets are only for later GSEA and do not block current data check, standardization preparation, or DEG preflight.
- `选择 GSEA 基因集` entry to the lightweight resource-manager placeholder.

The GSEA capability row can still block GSEA preflight / execution through `gsea_gene_set_selection`. This is scoped to GSEA and does not enter the general data-check missing-input list.

## Gene Set Resource Manager Stub

B5.16 adds `app/bioinformatics/gene_set_resources.py` and reserves `manifests/gene_set_registry.json`.

Reserved fields:

- `resource_id`
- `name`
- `collection_type`
- `species`
- `gene_id_type`
- `source_type`
- `source_name`
- `source_url`
- `license_note`
- `version`
- `created_at`
- `updated_at`
- `local_path`
- `status`
- `selected_for_gsea`

Reserved interfaces:

- `list_local_gene_sets()`
- `select_gene_set()`
- `get_selected_gene_set()`
- `validate_gene_set_registry()`

B5.16 does not implement a real gene set downloader, does not bundle default gene set files, and does not silently download MSigDB / GO / Reactome / KEGG resources.

## Business Logic Changes

- Readiness now publishes file-level and dataset-level summaries.
- GSEA gene set selection is removed from general data-check missing inputs.
- GSEA task capability still requires a selected resource before GSEA preflight / execution.
- Imported DEG and RAW/heavy file semantics are made explicit at file status level.
- The shared desktop entry now ignores macOS LaunchServices `-psn_*` arguments during packaged launch.
- The local `.app` packaging script now performs ad-hoc signing when `codesign` is available and disables packaged `.pyc` writes, so the generated bundle can pass the stricter local packaging gate after smoke launch.

Bioinformatics-external changes were limited to `app/main.py`, `scripts/package_app.py`, and their tests for the packaged desktop launch gate.

## Tests

Passed:

```bash
python3 -m pytest tests/bioinformatics/test_workflow_adapters.py tests/bioinformatics/test_dataset_download_service.py tests/ui/test_bioinformatics_workflow_pages.py -q
```

Result: `149 passed`.

```bash
python3 -m pytest tests/test_app_main.py tests/test_package_app.py tests/test_versioned_packaged_entry.py -q
```

Result: `5 passed`.

```bash
QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
dist/BioMedPilot.app/Contents/MacOS/BioMedPilot -psn_0_12345 --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
```

Result: passed. `CFBundleExecutable` is `BioMedPilot`; packaged Python and host are `arm64`.

Added or updated coverage includes:

- Local import of three files shows three pending rows.
- Data check page shows three file-level rows before and after check.
- Each file receives independent status.
- Imported DEG is not treated as expression matrix input.
- RAW/heavy remains blocked.
- GSEA gene set not selected does not become a general data-check failure.
- GSEA gene set not selected blocks only GSEA preflight / execution capability.
- Main button text uses `运行数据检查` / `重新运行数据检查`.
- Workspace navigation enters `数据检查与准备` after data selection.
- Packaged launcher ignores LaunchServices `-psn_*` arguments.
- Package build reports ad-hoc signing status when `codesign` is available, and package tests verify signing after launcher smoke.

## B5.17 Boundary

B5.17 should implement the full GSEA gene set resource manager:

- Local GMT import.
- GMT format validation.
- Copying imported GMT into a local gene set repository.
- Writing full `gene_set_registry.json` records.
- Selecting local resources.
- GO BP / GO CC / GO MF download and cache.
- Reactome download and cache.
- KEGG online retrieval and local cache.
- MSigDB Hallmark user import or licensed configuration.
- Offline reuse.
- GSEA preflight reading the selected resource.
