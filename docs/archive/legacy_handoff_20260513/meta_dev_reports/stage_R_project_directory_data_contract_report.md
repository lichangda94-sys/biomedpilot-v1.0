# Stage R Project Directory And Data Contract Report

## Goal

Stabilize Meta project structure so local projects are migratable, reproducible, and warning-safe when artifacts are missing.

## Completed

- Added root manifest generation for `project.json`, `data_manifest.json`, `artifact_manifest.json`, `task_manifest.json`, and `lineage_manifest.json`.
- Defined canonical Meta project paths for literature, screening, extraction, quality, analysis, figures, reports, exports, snapshots, locks, and retrieval history.
- Extended traceability audit with manifest saving.
- Reproducibility export now refreshes manifests before packaging.

## Data / Task Types

No new shared Data Center or Task Center types were added.

## Testing Status

Focused Stage R tests cover Stage M project manifest generation, missing artifact warnings, old testing project readability, and reproducibility package manifest inclusion.

Validation completed on 2026-04-28:

- `python -m compileall -q .`: not available in local shell (`python` command missing).
- `pytest -q`: not available in local shell (`pytest` command missing).
- `/Users/changdali/Documents/model9/.venv/bin/python -m compileall -q .`: passed.
- `/Users/changdali/Documents/model9/.venv/bin/python -m pytest -q`: 273 passed.
- `/Users/changdali/Documents/model9/.venv/bin/python scripts/run_tests.py`: 273 passed.
- `python3 -m app.main --smoke-test`: passed.

## Known Limits

The contract is a local JSON manifest contract, not a full JSON Schema migration framework yet.
