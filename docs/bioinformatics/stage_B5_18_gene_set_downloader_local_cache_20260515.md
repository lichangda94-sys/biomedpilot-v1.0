# B5.18 GO / Reactome / KEGG Gene Set Downloader And Local Cache

## Stage Goal

B5.18 extends the B5.17 GSEA gene set resource manager with user-triggered download, conversion, local cache, registry registration, and offline reuse for common Reactome, GO, and KEGG resources.

This stage only handles gene set resource acquisition and cache management. It does not implement real GSEA, DEG, enrichment analysis, plotting, or report expansion.

## B5.17 Audit

B5.17 registry and local repository design were suitable for extension:

- The registry schema already supported `source_type=downloaded`, `source_url`, `license_note`, validation status, selected resource, local paths, and preview counts.
- The local repository root `user_data/bioinformatics/gene_sets/` was reused.
- GMT validation, selection, missing-file checks, and GSEA preflight readiness were reused.
- Data check / standardization / DEG preflight behavior remains unchanged: unselected gene set resources do not block them.

## Downloader Interfaces

The service layer now exposes:

- `list_downloadable_gene_set_resources()`
- `download_gene_set_resource()`
- `refresh_downloaded_gene_set()`
- `validate_downloaded_gene_set()`
- `build_gmt_from_mapping()`
- `register_downloaded_gene_set()`

Downloaded resources are written to:

```text
user_data/bioinformatics/gene_sets/downloaded/
```

Each downloaded resource is registered into the existing B5.17 registry with:

- `source_type=downloaded`
- `source_name`
- `source_url`
- `license_note`
- `version`
- `downloaded_at`
- `file_size`
- `checksum`
- `validation_summary`
- `gene_set_count`
- `gene_count_preview`

Registry writes are atomic via temp file replace. Downloads write temporary files first, validate GMT output, then move into the final repository path. Failed downloads do not overwrite existing usable cache or selected resources.

## Reactome

Implemented `reactome_pathways`.

Flow:

1. User triggers download.
2. Service downloads `ReactomePathways.gmt.zip` from Reactome current downloads.
3. Zip is saved temporarily.
4. First GMT inside the zip is extracted.
5. GMT is validated.
6. Valid GMT is stored under `gene_sets/downloaded/reactome/`.
7. Registry is updated as `collection_type=Reactome`, `source_type=downloaded`, `species=all_species`, `gene_id_type=symbol`.

The UI says `下载 Reactome pathways 到本地`, not that Reactome is bundled.

## GO BP / CC / MF

Implemented human GO BP, GO CC, and GO MF from the human GO annotation GAF.

Flow:

1. User triggers GO resource download.
2. Service downloads `goa_human.gaf.gz`.
3. GAF is parsed by aspect:
   - `P` -> GO BP
   - `C` -> GO CC
   - `F` -> GO MF
4. `NOT` qualified annotations are skipped.
5. Each GO term becomes one GMT gene set.
6. GMT is validated and stored under `gene_sets/downloaded/go/`.
7. Registry is updated with `collection_type=GO_BP`, `GO_CC`, or `GO_MF`, `species=human`, `gene_id_type=symbol`.

The registry records `license_note=GO annotation data are used with CC BY 4.0 attribution required.`

## KEGG

Implemented `kegg_hsa_pathways`.

Flow:

1. User triggers online retrieval/cache.
2. Service calls KEGG REST pathway list and pathway-gene link endpoints for `hsa`.
3. Pathway mappings are converted into GMT.
4. GMT is validated and stored under `gene_sets/downloaded/kegg/`.
5. Registry is updated with `collection_type=KEGG`, `species=human`, `gene_id_type=entrez`.

The UI and registry keep the licensing boundary explicit: KEGG REST API is for academic users and academic use, and users must confirm their usage rights. The feature is user-triggered online retrieval and local cache, not bundled KEGG.

## MSigDB Hallmark

MSigDB Hallmark automatic download is still not implemented.

The UI continues to show:

```text
请导入用户已下载的 MSigDB GMT，或在授权配置后支持
```

Users can still import a Hallmark GMT through the B5.17 local GMT import path.

## UI Changes

The GSEA gene set resource manager now shows a common resource table with:

- Resource name.
- Description.
- Source.
- License / usage note.
- Local status.
- Local version / download date.
- Operation.

Supported rows:

- Reactome pathways.
- GO Biological Process (GO BP).
- GO Cellular Component (GO CC).
- GO Molecular Function (GO MF).
- KEGG human pathways.
- MSigDB Hallmark.
- Custom GMT.

Actions:

- `下载到本地 / 在线获取并缓存`
- `更新缓存`
- `导入 GMT`

After download or refresh, the local resource table refreshes and the resource can be selected as the current GSEA gene set.

## Offline Reuse And Failure Protection

- Existing available cache is reused without network access unless refresh is requested.
- Refresh failures do not modify existing cache.
- Download failures surface as UI status text and keep current registry / selection untouched.
- Missing cached files are marked `missing` by `validate_gene_set_registry()`.
- Only available resources can be selected.
- HTTPS downloads use the local `certifi` CA bundle when available and send a BioMedPilot User-Agent, which is required by the GO annotation endpoint in the tested Python 3.14 environment.

## Data Check Boundary

GMT / gene set resources are still not GEO / TCGA / GTEx data file requirements.

Unselected gene set resources do not block:

- Data check.
- Standardization preparation.
- DEG preflight.

Only GSEA preflight / execution treats missing gene set selection as blocking.

## Bioinformatics-External Scope

No Bioinformatics-external modules were intentionally changed. Changes are limited to `app/bioinformatics`, `tests/bioinformatics`, `tests/ui`, and this report.

No packaging, desktop entry overwrite, or remote push was performed.

## Tests

Targeted tests passed during development:

```bash
python3 -m pytest tests/bioinformatics/test_gene_set_resources.py -q
```

Result: `13 passed`.

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py::test_gene_set_resource_manager_shows_downloadable_resources_and_refreshes_after_download tests/ui/test_bioinformatics_workflow_pages.py::test_gsea_gene_set_resource_manager_displays_and_selects_local_resource tests/ui/test_bioinformatics_workflow_pages.py::test_readiness_gene_set_button_opens_manager_and_status_updates -q
```

Result: `3 passed`.

Final validation passed:

```bash
python3 -m pytest tests/bioinformatics -q
```

Result: `266 passed`.

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

Result: `159 passed`.

```bash
python3 -m app.main --smoke-test
```

Result: passed. Source launch smoke reported `launch_mode=source`, `bioinformatics_features=5`, and `pyside6_available=True`.

```bash
git diff --check
```

Result: passed.

`git diff --cached --check` should be run after staging the B5.18 files.

Live network validation was also run after the committed stage implementation:

```text
Reactome pathways: 2855 gene sets, cached as available.
GO BP: 11248 gene sets, cached as available.
GO CC: 1840 gene sets, cached as available.
GO MF: 4812 gene sets, cached as available.
KEGG human pathways: 371 gene sets, cached as available.
```

Second calls for all five resources returned `cached=True` and reused the local repository without network fetches. Selecting `kegg_hsa_pathways` produced no GSEA gene set readiness blocking errors.

## Next Stage

The next stage should wire the downloaded resource readiness into a concrete GSEA preflight manifest and execution preparation flow. Real GSEA execution, visualization, and reporting should remain separate follow-up stages.
