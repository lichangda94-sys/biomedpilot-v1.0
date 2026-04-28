# Unified Project Layout Plan

## Recommendation

Create a new final project root:

```text
/Users/changdali/Documents/BioMedPilot
```

Reason:

- `/Users/changdali/Documents/New project 2` is a working integration folder with a temporary name.
- `BioMedPilot` is clearer for external testers, packaging, documentation, and future handoff.
- The old source directories can remain untouched for rollback.

Do not delete:

- `/Users/changdali/Documents/model9`
- `/Users/changdali/Documents/New project`
- `/Users/changdali/Documents/New project 2`

## Target Layout

```text
BioMedPilot/
  README.md
  pyproject.toml
  requirements.txt
  app/
    main.py
    shell/
    bioinformatics/
      legacy/
    meta_analysis/
      legacy/
    shared/
  assets/
    icons/
    images/
    styles/
  docs/
    architecture.md
    module_boundaries.md
    migration/
    user_testing/
  tests/
    bioinformatics/
    meta_analysis/
    shared/
    integration/
    ui/
  scripts/
    run_app.py
    run_tests.py
    package_app.py
  examples/
    bioinformatics/
    meta_analysis/
  project_storage/
    projects/
    data/
    tasks/
    reports/
    test_feedback/
  archive/
    legacy_sources/
      model9/
      bioinformatics_project/
    old_docs/
    duplicate_candidates/
```

## Active Project Rules

| Area | Rule |
|---|---|
| `app/shell` | Owns Dashboard, navigation, Testing Mode, and app-level UI. |
| `app/shared` | Owns Project Center, Task Center, feature availability, testing feedback, settings, storage, and environment checks. |
| `app/bioinformatics` | Owns Bioinformatics workspace, adapters, services, pipelines, reports, and Bioinformatics legacy snapshot. |
| `app/meta_analysis` | Owns Meta Analysis workspace, profiles, screening, extraction, analysis, reports, and Meta legacy snapshot. |
| `docs` | Active documentation only. Older docs go to `archive/old_docs` or remain in legacy archives. |
| `tests` | Active unified tests only. Legacy tests remain inside legacy archives until isolated runners are added. |
| `project_storage` | Runtime storage skeleton. Do not commit generated project JSON or user data by default. |
| `archive` | Read-only historical material and duplicate candidates. Nothing under `archive` should be imported by active app code. |

## Copy Strategy

1. Copy current `New project 2` active files to `/Users/changdali/Documents/BioMedPilot`.
2. Exclude `.git`, `__pycache__`, `.pytest_cache`, virtual environments, build/dist output, and generated runtime JSON.
3. Copy `model9` source subset into `archive/legacy_sources/model9`.
4. Copy `New project` source subset into `archive/legacy_sources/bioinformatics_project`.
5. Add small marker files under `archive/old_docs` and `archive/duplicate_candidates` with lists rather than copying every old snapshot immediately.

## Validation Commands

Run from `/Users/changdali/Documents/BioMedPilot`:

```bash
python3 -m app.main --smoke-test
python3 scripts/run_tests.py
```

If system Python lacks pytest:

```bash
'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py
```

