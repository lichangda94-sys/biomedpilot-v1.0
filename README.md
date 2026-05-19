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
python3 -m app.main
```

or:

```bash
python3 scripts/run_app.py
```

If `PySide6` is unavailable, the launcher prints a console smoke summary instead
of opening the desktop window.

For automated startup checks without entering the GUI event loop:

```bash
python3 -m app.main --smoke-test
```

## Test

```bash
python3 scripts/run_tests.py
```

The unified smoke suite can also be run with:

```bash
python3 -m pytest -q
```

Legacy project tests are preserved in their source snapshots. Run them in
isolated subprocesses with the source snapshot first on `PYTHONPATH` when doing
full migration validation.

## Package

The current package step is a local macOS `.app` launcher. It does not download
dependencies and is not a fully standalone installer. It copies the BioMedPilot
project files into `dist/BioMedPilot.app` and launches them with the Python
executable used at build time.

```bash
python3 scripts/package_app.py --smoke-test
```

Open the generated app from:

```text
dist/BioMedPilot.app
```

For a portable standalone app, the next packaging phase should use PyInstaller
or py2app after dependency installation is explicitly approved.
