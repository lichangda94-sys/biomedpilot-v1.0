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

## Local Tools and Models

BioMedPilot local tools and local models follow the principle:
`架构上统一，体验上按需`.

- Shared backend management may later live under `app/shared/local_engines/`,
  but the main screen must not expose a large "External Engines" center.
- Features detect their own required local dependency when entered or triggered.
  Missing dependencies should show contextual setup, not a required first-use
  configuration step.
- Settings may contain an advanced `设置 > 本地工具与模型` page for manual
  configuration, diagnostics, and troubleshooting.
- ImageJ/Fiji is the preferred local image-analysis backend for future
  ImageJ-assisted/manual-review image workflows.
- Integration now contains the shared ImageJ/Fiji detection foundation under
  `app/shared/local_engines/`: stable status serialization, local config
  storage, common macOS path probing, executable validation, and a
  non-destructive macro smoke test.
- This foundation is availability infrastructure only. It does not add WB/gel
  grayscale, cell counting, automatic ROI, pathology analysis, or any concrete
  image-analysis workflow.
- Ollama/local LLM is a local environment capability. It must not consume cloud
  AI credits and must not be gated by membership/payment entitlement.
- Cloud AI is separate and may later use account login, membership, AI credits,
  platform API, user API keys, and usage/cost records.
- LabTools, Bioinformatics, and Meta must not each implement separate local
  tool/model configuration stacks; they should consume shared status/config
  concepts when those are implemented.
