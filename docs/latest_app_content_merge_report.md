# Latest App Content Merge Report

## Source audit

- `/Users/changdali/Documents/BioMedPilot` is the active app workspace and packaged-app source root.
- Current integration base before this merge was `9bfc88b`, which already contained the shared vocabulary line and the Bioinformatics GEO disease-aware UI.
- `/Users/changdali/Documents/New project 2` contains additional committed Bioinformatics search-center work at `8265892`, but also has uncommitted Meta/PubMed work-in-progress changes.

## Merge decision

The directories are divergent development lines, not a safe fast-forward target. The merge therefore imports only the reusable committed Bioinformatics dataset-search capability from `New project 2`:

- Bioinformatics search center models, query understanding, routing, ranking, GEO adapter, TCGA/GDC adapter, and GTEx adapter.
- Shared search context filtering used to keep Bioinformatics dataset search separate from literature search.
- Search-center tests and search-context tests.

The uncommitted `New project 2` Meta/PubMed changes were not migrated.

## App integration

The active BioMedPilot app keeps its current page/service architecture. The imported search center is wired into the existing `GeoImportService` and `GeoImportPage` so users can test:

- Disease-aware GEO/GSE query drafts and GEO result registration.
- TCGA/GDC project candidates.
- GTEx normal tissue reference candidates.
- Unified dataset candidates across GEO, TCGA/GDC, and GTEx.

The Bioinformatics page remains scoped to:

`GEO/GSE、TCGA/GDC、GTEx、本地数据。`
