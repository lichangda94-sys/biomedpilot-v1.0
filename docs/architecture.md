# BioMedPilot Architecture

BioMedPilot is a unified desktop shell with two independent business modules.

## Layers

- `app/shell/`: desktop window, dashboard, navigation, status panel.
- `app/shared/`: cross-module project, data, task, report, settings, UI, logging, storage, and environment services.
- `app/bioinformatics/`: Bioinformatics Analysis workspace, adapters, services, pipelines, pages, reports.
- `app/meta_analysis/`: Meta Analysis workspace, services, profiles, screening, extraction, analysis, reports.
- `app/*/legacy/`: read-only snapshots of the original independent projects.

## Runtime Entry

`python -m app.main` launches the PySide6 desktop shell when PySide6 is installed.
If PySide6 is missing, the same entry prints a console smoke summary for
environment testing.

## Shared Centers

- Project Center stores project metadata and project type.
- Data Center reserves common data type names.
- Task Center stores task metadata and lifecycle state.
- Report Center reserves common report artifact categories.
- Settings reserves cross-module configuration fields.
- Environment checks Python, PySide6, R, and storage paths.

