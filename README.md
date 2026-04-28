# BioMedPilot / 医研智析

BioMedPilot is a unified desktop shell for two independent analysis workspaces:

- Bioinformatics Analysis / 生信分析
- Meta Analysis / 医学 Meta 分析

The current merge keeps both original projects as isolated legacy snapshots under
`app/bioinformatics/legacy/` and `app/meta_analysis/legacy/`. New shared shell,
project, task, data, report, settings, environment, and testing surfaces live in
`app/shared/` and `app/shell/`.

## Run

```bash
python -m app.main
```

or:

```bash
python scripts/run_app.py
```

If `PySide6` is unavailable, the launcher prints a console smoke summary instead
of opening the desktop window.

For automated startup checks without entering the GUI event loop:

```bash
python -m app.main --smoke-test
```

## Test

```bash
python scripts/run_tests.py
```

The unified smoke suite can also be run with:

```bash
python -m pytest -q
```

Legacy project tests are preserved in their source snapshots. Run them in
isolated subprocesses with the source snapshot first on `PYTHONPATH` when doing
full migration validation.
