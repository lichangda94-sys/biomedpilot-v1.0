# BioMedPilot Project Merge Plan

## Source Projects

- Bioinformatics source: `/Users/changdali/Documents/New project`
- Meta Analysis source: `/Users/changdali/Documents/model9`
- Merge target: `/Users/changdali/Documents/New project 2`

## Audit Summary

The merge target started as an empty git repository on branch `main`.

Bioinformatics source findings:

- Main desktop entry: `geo_tool/run_geo_tool.py`
- Core packages: `geo_tool/`, `geo_pipeline/`, `geo_processing/`, `tcga_gtex/`, `ui/`
- Tests: `tests/`
- Dependencies: `requirements.txt`, `geo_tool/requirements.txt`

Meta Analysis source findings:

- Main desktop entry: `app/__main__.py` / `scripts/run_app.py`
- Core packages: `literature/`, `extraction/`, `analysis/`, `analysis_profiles/`, `reporting/`, `fulltext/`, `bias/`, `core/`
- Existing shell packages: `app/`, `app_meta/`
- Tests: `tests/`
- Dependencies: `pyproject.toml`, `requirements.txt`
- Source working tree had uncommitted changes and generated folders, so it was treated as read-only input.

## Target Structure

The target keeps a new BioMedPilot shell at:

- `app/main.py`
- `app/shell/`
- `app/shared/`
- `app/bioinformatics/`
- `app/meta_analysis/`

Original project snapshots are preserved at:

- `app/bioinformatics/legacy/`
- `app/meta_analysis/legacy/`

Excluded from legacy copies:

- `.git`
- virtual environments
- `__pycache__`
- `.pytest_cache`
- `dist`
- `build`
- `.DS_Store`
- `*.pyc`

## Implementation Strategy

1. Create a new migration branch.
2. Copy source projects into isolated legacy directories.
3. Add a unified `python -m app.main` entry.
4. Add shared Project Center, Task Center, Data Center, Report Center, Settings, and Environment namespaces.
5. Add Bioinformatics and Meta Analysis workspace boundaries with explicit feature status.
6. Add unified test and app scripts.
7. Add migration and user testing documentation.

## Boundary Rules

- Bioinformatics code remains under `app/bioinformatics/`.
- Meta Analysis code remains under `app/meta_analysis/`.
- Shared cross-module services live under `app/shared/`.
- Legacy code is not rewritten in this migration pass.
- Core GEO, TCGA/GTEx, literature screening, extraction, and statistical logic is not changed.

