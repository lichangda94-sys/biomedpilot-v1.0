# B5.17 GSEA Gene Set Resource Manager

## Stage Goal

B5.17 implements the Bioinformatics GSEA gene set resource manager on top of the B5.16 registry stub. The scope is limited to local GMT import, validation, registry management, selection, local cache state, and stable readiness interfaces for later GSEA preflight / execution.

GMT / gene set resources remain separate from GEO / TCGA / GTEx data files. They do not enter acquisition, recognition, standardization input, DEG input, plotting, report, or real GSEA execution flows in this stage.

## Registry Capabilities

The registry now lives under project-local user data:

```text
user_data/bioinformatics/gene_sets/gene_set_registry.json
```

The service keeps a compatibility read path for the B5.16 stub location:

```text
manifests/gene_set_registry.json
```

Each resource records:

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
- `validation_summary`
- `gene_set_count`
- `gene_count_preview`

Implemented service interfaces:

- `initialize_gene_set_registry()`
- `list_local_gene_sets()`
- `get_gene_set()`
- `get_selected_gene_set()`
- `select_gene_set()`
- `unselect_gene_set()`
- `validate_gene_set_registry()`
- `remove_gene_set()`

Selection is single-resource only. Selecting a resource clears `selected_for_gsea` from all other resources. Registry validation marks missing cached files as `missing`, invalid GMT content as `invalid`, and normal usable GMT files as `available`.

All registered local paths are resolved inside the Bioinformatics project root. Imported GMT files are copied into the local repository instead of modifying or replacing the original user file.

## GMT Import

Implemented `import_gmt_file()` for local user GMT import.

Validation checks:

- File exists.
- Path is a file.
- File is non-empty.
- Empty lines are skipped.
- Each non-empty line must contain at least gene set name, description column, and one gene.
- Gene set count is recorded.
- Up to five preview rows record gene set name, gene count, and first genes.
- Malformed files are registered as `invalid` with a validation summary.

Imported files are copied to:

```text
user_data/bioinformatics/gene_sets/custom/<safe_resource_id>.gmt
```

The original GMT is not modified. Imported GMT resources do not enter the ordinary data acquisition / recognition file chain.

## Resource Manager UI

The `选择 GSEA 基因集` button now opens `GSEA 基因集资源管理器`.

The manager contains:

- Local resource table with name, type, species, Gene ID type, source, version/date, status, gene set count, current selection, and operations.
- Action buttons: `选择`, `查看详情`, `移除`, `刷新状态`.
- `导入本地 GMT` section.
- Future resource section for GO BP, GO CC, GO MF, Reactome, KEGG, MSigDB Hallmark, and custom GMT.

The future resource section is intentionally non-downloading. GO / Reactome rows are marked as later download support. KEGG is described as later online retrieval/cache or user configuration. MSigDB Hallmark is described as user-import or authorized configuration only.

## Data Check Integration

The data check and preparation page still displays:

- `GSEA 基因集：未选择` when no resource is selected.
- `GSEA 基因集：已选择 <resource name>` after selecting an available local resource.
- `GSEA 基因集资源不可用` when a selected resource becomes missing or invalid.

Selecting or importing a resource refreshes the page status immediately.

Unselected gene set resources do not block:

- Current data check.
- Standardization preparation.
- DEG preflight.

They only affect the GSEA capability row and later GSEA preflight / execution.

## GSEA Preflight Interface

Implemented stable future-facing interfaces:

- `get_selected_gene_set_for_gsea()`
- `validate_selected_gene_set_for_gsea()`
- `build_gsea_gene_set_readiness()`

Returned readiness includes:

- `selected`
- `resource_id`
- `name`
- `local_path`
- `species`
- `gene_id_type`
- `status`
- `gene_set_count`
- `blocking_errors`
- `warnings`

Blocking rules:

- No selected gene set: blocking for GSEA preflight only.
- Selected resource with missing file: blocking for GSEA preflight.
- Selected resource with invalid content: blocking for GSEA preflight.
- `gene_id_type=unknown`: warning for GSEA preflight, not an automatic blocker.

## License And Source Boundaries

B5.17 does not claim bundled Hallmark, KEGG, Reactome, or GO resources.

MSigDB Hallmark is not presented as automatically downloadable. The UI says to import a user-downloaded MSigDB GMT or use future authorized configuration. KEGG is described as future online retrieval/cache or user configuration, not as built-in.

The registry keeps `license_note` and `source_url` for future provenance and licensing workflows.

## Not Implemented In B5.17

- No true GO downloader.
- No true Reactome downloader.
- No KEGG online retrieval.
- No MSigDB download or bundled Hallmark.
- No real GSEA analysis.
- No DEG, enrichment, plotting, or report extension.
- No packaging.
- No remote push.

## Bioinformatics-External Scope

No Bioinformatics-external app modules were intentionally changed. Changes are limited to `app/bioinformatics`, `tests/bioinformatics`, `tests/ui`, and this report.

## Tests

Targeted tests passed during development:

```bash
python3 -m pytest tests/bioinformatics/test_gene_set_resources.py -q
```

Result: `7 passed`.

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py::test_gsea_gene_set_resource_manager_displays_and_selects_local_resource tests/ui/test_bioinformatics_workflow_pages.py::test_readiness_gene_set_button_opens_manager_and_status_updates -q
```

Result: `2 passed`.

Final validation passed:

```bash
python3 -m pytest tests/bioinformatics -q
```

Result: `260 passed`.

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

Result: `158 passed`.

```bash
python3 -m app.main --smoke-test
```

Result: passed. Source launch smoke reported `launch_mode=source`, `bioinformatics_features=5`, and `pyside6_available=True`.

```bash
git diff --check
```

Result: passed.

`git diff --cached --check` should be run after staging the B5.17 files.

## Next Stage

The next GSEA stage should connect `build_gsea_gene_set_readiness()` into a real GSEA preflight manifest, then later implement controlled resource download / cache flows for GO, Reactome, KEGG, and authorized MSigDB workflows without bundling restricted resources.
