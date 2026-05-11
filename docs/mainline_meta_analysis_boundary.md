# Mainline / Meta Analysis Boundary

## Goal

`stable/mainline` is the application trunk. It keeps the desktop shell, module
selection, project binding, and the minimal Meta Analysis workspace contract.
Full Meta Analysis feature development belongs on `dev/meta-analysis`.

## What Mainline Keeps

- The Meta module entry in the desktop shell.
- `MetaAnalysisWorkspaceWidget` as a lightweight placeholder workspace.
- Meta project create/open manifest contract.
- Dashboard feature labels and module smoke tests.
- A clear UI notice that complete Meta workflows are developed on
  `dev/meta-analysis`.

## What Moves To `dev/meta-analysis`

- PICO and protocol workflow implementation.
- Search strategy, PubMed handoff, and literature import.
- Literature library, duplicate review, screening, full-text handling.
- Extraction, quality assessment, analysis setup, statistics, figures, reports.
- Meta service/model/page implementations and detailed feature tests.
- Legacy Meta snapshots and historical app assets.

## Runtime Contract

Mainline must be able to start, render the dashboard, enter the Meta module,
bind a project record, and open a Meta project manifest without importing full
Meta workflow services.

The complete workflow can be refreshed from mainline on a dedicated branch,
currently represented by `codex/meta-analysis-refresh`, and later moved or
fast-forwarded into `dev/meta-analysis` after human review.
