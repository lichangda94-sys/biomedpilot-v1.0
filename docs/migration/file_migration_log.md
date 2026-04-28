# File Migration Log

Date: 2026-04-28

Final project root created:

- `/Users/changdali/Documents/BioMedPilot`

No original source directory was deleted, moved, emptied, or overwritten.

## Operations Performed

| Operation | Source | Target | Notes |
|---|---|---|---|
| created directory | none | `/Users/changdali/Documents/BioMedPilot` | New final project root. |
| copied active project | `/Users/changdali/Documents/New project 2/` | `/Users/changdali/Documents/BioMedPilot/` | Excluded `.git`, virtual environments, caches, build/dist, generated runtime JSON, and `.DS_Store`. |
| copied Meta source subset | `/Users/changdali/Documents/model9/` | `/Users/changdali/Documents/BioMedPilot/archive/legacy_sources/model9/` | Excluded `.git`, `.venv`, `.venv-meta`, caches, `dist`, `build`, and `.DS_Store`. |
| copied Bioinformatics source subset | `/Users/changdali/Documents/New project/` | `/Users/changdali/Documents/BioMedPilot/archive/legacy_sources/bioinformatics_project/` | Excluded `.git`, `.venv`, caches, `dist`, `build`, and `.DS_Store`. |
| created duplicate candidate notes | `model9-main-clean`, `model9-module*` directories | `/Users/changdali/Documents/BioMedPilot/archive/duplicate_candidates/*.txt` | Logged as needs-review instead of copying full old snapshots. |
| created old docs note | none | `/Users/changdali/Documents/BioMedPilot/archive/old_docs/README.md` | Older docs remain inside legacy archives unless promoted later. |

## Exclusions

Excluded from copies:

- `.git`
- `.venv`
- `.venv-meta`
- `__pycache__`
- `.pytest_cache`
- `dist`
- `build`
- `*.pyc`
- `.DS_Store`
- generated `project_storage/projects/*.json`
- generated `project_storage/tasks/*.json`
- generated `project_storage/test_feedback/*.md`

## Copied Active Areas

- `README.md`
- `pyproject.toml`
- `requirements.txt`
- `app/`
- `docs/`
- `tests/`
- `scripts/`
- `assets/`
- `examples/`
- `project_storage/` structure

## Archive Areas

- `archive/legacy_sources/model9/`
- `archive/legacy_sources/bioinformatics_project/`
- `archive/duplicate_candidates/`
- `archive/old_docs/`

## Size Check

After exclusions:

- `/Users/changdali/Documents/BioMedPilot`: approximately 25M
- `archive/legacy_sources/model9`: approximately 11M
- `archive/legacy_sources/bioinformatics_project`: approximately 1.7M

The much larger source sizes were avoided by excluding virtual environments and generated outputs.

## Verification Commands

Run from `/Users/changdali/Documents/BioMedPilot`:

```bash
python3 -m app.main --smoke-test
'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py
```

