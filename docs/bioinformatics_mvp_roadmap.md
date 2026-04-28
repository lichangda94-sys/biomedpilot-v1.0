# Bioinformatics MVP Roadmap

This roadmap upgrades the existing Developer Preview from plan/preflight/testing summaries into a minimal real bulk bioinformatics MVP while preserving all current 11 workspace steps.

## Stage Roadmap

| Stage | Target | Current baseline | MVP upgrade | Stop conditions |
| --- | --- | --- | --- | --- |
| 0 | Developer Preview baseline | Testing/preflight chain exists | Freeze docs and contracts only | Any code behavior change needed |
| 1 | Local expression matrix import | File preflight and `expression_matrix` asset registration | Stable import summary and asset manifest | `openpyxl` required for XLSX and unavailable |
| 2 | Cleaning and normalization | `geo_cleaning_plan` only | Real cleaned/normalized matrix runner | New dependency required |
| 3 | Sample grouping | grouping preflight only | `sample_annotation` and two-group `comparison_config` | User has not selected sample/group/control/case fields |
| 4 | Differential expression | DEG preflight only | Two-group DEG table and summary | `scipy/statsmodels` unavailable or not approved |
| 5 | DEG visualization | No formal figures | Volcano plot and heatmap artifacts | `matplotlib`/plot dependency unavailable or not approved |
| 6 | Enrichment | enrichment preflight only | Local GMT ORA runner | `scipy` unavailable or real database requested |
| 7 | Markdown MVP report | testing summary only | Analysis report and report manifest | Major template/UI decision required |
| 8 | GEO controlled download | download plan only | Explicit-download Series Matrix ingestion | Real network download not explicitly confirmed |
| 9 | TCGA/GTEx local asset entry | legacy code exists, not unified | Local TCGA/GTEx manifests and comparison config | Online download requested |
| 10 | Correlation and survival | preflight only | Minimal correlation and survival runners | `lifelines`/statistics dependency unavailable or not approved |
| 11 | UI workflow status | independent testing panels | Unified step status and previews | Large UI architecture refactor required |
| 12 | Word/PDF and reproducibility package | Markdown testing summary | DOCX/PDF if supported and zip package | `docx`/PDF dependency unavailable or not approved |

## Recommended Execution Order

1. Complete Stage 0 documentation baseline and keep all tests passing.
2. Upgrade local file assets first: Stage 1, Stage 2, Stage 3.
3. Add analysis outputs after stable assets exist: Stage 4, Stage 5, Stage 6.
4. Add report and external source integrations: Stage 7, Stage 8, Stage 9.
5. Add secondary analysis and product polish: Stage 10, Stage 11, Stage 12.

## Feature Availability Policy

- Existing features remain `testing`.
- A stage may update descriptions to say "minimal preview runner" only after a real runner exists and is tested.
- Do not mark Bioinformatics analysis features as `open` or production-ready during this MVP roadmap.

## Non-Goals For This Roadmap

- No single-cell, spatial omics, mutation, methylation, machine learning, or AI interpretation modules.
- No online GEO/TCGA/GTEx access unless a stage explicitly stops for user confirmation first.
- No automatic dependency installation.
- No deletion or renaming of current workspace steps.
