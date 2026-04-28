# Module 9 Packaging And Localization Readiness

Module 9 starts with a lightweight readiness audit for future local packaging and localization work. The audit is reporting-only: it checks whether baseline project files and package directories are present, then prints recommended validation commands.

It also includes a requirements export helper for migration readiness. The helper reads declared project dependencies from `pyproject.toml` and writes a minimal `requirements.txt`. It does not inspect the active Python environment.

The local environment readiness check reports whether the current checkout has the files needed for a later manual bootstrap. It does not create a virtual environment, install dependencies, or modify `requirements.txt`.

The developer verification script chains local readiness checks, packaging readiness, requirements consistency, smoke checks, and unittest discovery. It is a check runner only and does not install dependencies, create a virtual environment, or build packages.

The project status snapshot script prints repository and module readiness context. It is read-only and does not modify git state.

`docs/development_baseline_index.md` collects the current module baseline, boundaries, common commands, Module 9 scripts, and actual `v0.*` tag summaries.

`v0.17-local-readiness-baseline` marks the first local readiness and migration preparation baseline for Module 9.

## Checks

`scripts/check_packaging_readiness.py` reports:

- `pyproject.toml`
- `README.md`
- `scripts/run_smoke_tests.py`
- `scripts/run_task_once.py`
- `scripts/run_fake_geo_preflight.py`
- core package directories: `core`, `app`, `reporting`, `analysis`, and `extraction`
- missing items
- recommended validation commands

The output is stable and does not depend on real GEO, TCGA, GDC, or GTEx data.

## Requirements Export

`scripts/export_requirements.py` reports and writes a minimal `requirements.txt` from `[project].dependencies` in `pyproject.toml`.

Current behavior:

- exports only explicitly declared project dependencies
- writes stable, readable `requirements.txt` content
- reports a stable message if no dependencies are declared
- supports `--check` to compare `requirements.txt` with the current export
- returns non-zero in `--check` mode when `requirements.txt` is missing or out of sync
- does not run `pip freeze`
- does not install dependencies
- does not create a virtual environment

## Local Environment Readiness

`scripts/check_local_environment.py` reports:

- current Python version
- whether the Python version satisfies the project minimum
- `requirements.txt`
- `pyproject.toml`
- `scripts/run_smoke_tests.py`
- `scripts/check_packaging_readiness.py`
- `scripts/export_requirements.py`
- `scripts/run_task_once.py`
- `scripts/run_fake_geo_preflight.py`
- missing items
- recommended manual bootstrap commands

Recommended manual bootstrap steps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/run_smoke_tests.py
python3 -m unittest discover -s tests
```

The readiness check only prints these commands. It does not run them.

## Developer Verification

`scripts/run_dev_checks.py` runs the standard local verification sequence:

```bash
python3 scripts/check_local_environment.py
python3 scripts/check_packaging_readiness.py
python3 scripts/run_task_once.py --help
python3 scripts/run_fake_geo_preflight.py
python3 scripts/export_requirements.py --check
python3 scripts/run_smoke_tests.py
python3 -m unittest discover -s tests
```

`scripts/run_dev_checks.py --quick` runs a shorter check sequence:

```bash
python3 scripts/check_local_environment.py
python3 scripts/check_packaging_readiness.py
python3 scripts/run_task_once.py --help
python3 scripts/run_fake_geo_preflight.py
python3 scripts/run_smoke_tests.py
```

The script prints pass/fail status for each step and returns non-zero when any step fails. The `run_task_once.py --help` check only verifies command availability; it does not pass a task id or execute a task. The fake GEO preflight check uses in-memory fixtures only; it does not download GEO data, create task results, create artifacts, or run analysis. The developer check script does not install dependencies, create `.venv`, generate `build/` or `dist/`, or run packaging commands.

## Manual Runner Command

`scripts/run_task_once.py` is available for explicit local task execution through the Module 7 lifecycle wrapper. It defaults to dry-run:

```bash
python3 scripts/run_task_once.py --task-id <id> --state-dir <path> --dry-run
python3 scripts/run_task_once.py --task-id <id> --state-dir <path> --real-run
```

The command requires one task id and one state directory. It does not scan tasks, run a scheduler, expose a UI button, install dependencies, build packages, or use production downloaders. Readiness checks only verify `--help`.

## Fake GEO Preflight

`scripts/run_fake_geo_preflight.py` is available for local readiness checks before real GEO files are used:

```bash
python3 scripts/run_fake_geo_preflight.py
python3 scripts/run_fake_geo_preflight.py --json
```

It uses in-memory fake fixtures to validate dataset asset, gene mapping, sample mapping, comparison, and analysis preflight summaries. It does not download real GEO data, execute DEG/enrichment analysis, create `TaskResultRecord` entries, create artifacts, or write execution logs.

## Project Status Snapshot

`scripts/project_status_snapshot.py` reports:

- current git branch, when available
- current HEAD short SHA, when available
- whether the working tree is clean
- `v0.*` tags
- key module directories: `core`, `analysis`, `reporting`, `extraction`, `app`, `scripts`, `docs`, and `tests`
- key readiness scripts: smoke checks, packaging readiness, requirements export, local environment readiness, and developer checks

If git is unavailable or the directory is not a git repository, the script prints stable `unavailable` or `unknown` values instead of failing.

## v0.17 Baseline

The v0.17 local readiness baseline includes:

- packaging readiness check
- requirements export and `--check`
- local environment readiness check
- developer verification script
- project status snapshot
- documented migration/bootstrap flow

The v0.24 CLI manual runner baseline adds:

- `scripts/run_task_once.py`
- default `dry_run=True`
- explicit `--real-run` / `--no-dry-run` for non-dry-run execution
- readiness and developer checks for command presence and `--help`
- no scheduler, no automatic task scan, and no UI execute button

Recommended migration flow:

```bash
git clone <repo-url>
cd model9
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/run_dev_checks.py
```

This flow is documentation for a later local setup. The readiness scripts do not create a virtual environment, install dependencies, build a package, generate `dist/` or `build/`, or execute real analysis tasks.

## Boundaries

- no package build
- no `dist/` generation
- no `build/` generation
- no real packaging from v0.17 readiness scripts
- no `pyproject.toml` changes
- no dependency installation
- no virtual environment creation
- no real analysis execution
- no `.venv` creation from readiness checks
- no `.venv` creation from developer verification
- no `requirements.txt` modification from local environment checks
- no package build from developer verification
- no git state changes from project status snapshots
- no `pip freeze` against the global environment
- no business logic changes
- no `geo_workflow.py` changes
- no Module 4/5/6/7 schema changes
- no production downloader integration

## Validation

```bash
python3 scripts/check_packaging_readiness.py
python3 scripts/export_requirements.py
python3 scripts/export_requirements.py --check
python3 scripts/check_local_environment.py
python3 scripts/run_fake_geo_preflight.py
python3 scripts/run_dev_checks.py --quick
python3 scripts/run_dev_checks.py
python3 scripts/project_status_snapshot.py
python3 -m unittest tests.test_packaging_readiness
python3 -m unittest tests.test_requirements_export
python3 -m unittest tests.test_local_environment_check
python3 -m unittest tests.test_dev_checks_script
python3 -m unittest tests.test_project_status_snapshot
python3 scripts/run_smoke_tests.py
python3 -m unittest discover -s tests
```
