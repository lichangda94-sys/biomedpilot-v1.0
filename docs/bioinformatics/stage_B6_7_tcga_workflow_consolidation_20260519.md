# Bioinformatics B6.7 TCGA Workflow Consolidation

Date: 2026-05-19

## Goal

B6.7 consolidates the B6.2-B6.6 TCGA data source work into one state-driven user path:

1. Preview downloadable data
2. Download TCGA raw files
3. Build TCGA expression matrices
4. Fetch TCGA clinical metadata
5. Enter data check and preparation

This stage does not add new GDC data types, does not advance B5.19, and does not execute DEG, GSEA, KM, Cox, log-rank, or reporting.

## Modified Files

- `app/bioinformatics/data_sources/tcga_workflow.py`
- `app/bioinformatics/data_sources/__init__.py`
- `app/bioinformatics/workflow_pages.py`
- `tests/bioinformatics/test_tcga_workflow.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

## Workflow State Logic

`TCGAWorkflowState` summarizes local TCGA progress from existing project artifacts:

- download plan
- download receipt / source manifest
- raw acquisition record
- expression build manifest
- clinical build manifest

When multiple records exist, the workflow prefers the highest stage:

`clinical > expression_build > raw_download > plan > request`

The state exposes five `TCGAWorkflowStep` rows with status, enablement, user summary, blocking reason, warning, and developer diagnostics.

## UI Changes

The TCGA data source card now shows a five-step workflow table and a compact current-state summary. Primary user text avoids manifest paths, source file internals, file UUIDs, GDC filters, and raw paths. Those details remain in the collapsed developer diagnostics panel.

Existing B6.2-B6.6 actions are preserved, but their buttons are now controlled by workflow state:

- initial state only enables preview
- a plan enables raw download
- a successful raw acquisition enables expression build
- an expression build enables clinical metadata and data check
- a clinical build shows expression-clinical readiness and basic OS readiness

## Boundaries Preserved

- No GTEx download.
- No TCGA + GTEx automatic merge.
- No GTEx normal-control substitution for TCGA.
- No DEG/GSEA execution.
- No KM/Cox/log-rank execution.
- No clinical conclusion or report-ready output.
- No ReleaseBuild changes.

## Tests

Added unit coverage for empty state, request/plan/download/expression/clinical transitions, highest-stage recovery, failed download blocking, RAW/controlled warnings, clinical preview downgrade, and TCGA+GTEx boundary messaging.

Added UI coverage for the five-step workflow, initial button gating, plan/download/expression/clinical state transitions, collapsed developer diagnostics, and restored clinical manifest summaries.

Validation run:

- `git diff --check` passed
- `python3 -m pytest tests/bioinformatics -q`: 290 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`: 169 passed
- `python3 -m app.main --smoke-test` passed

## Unfinished

- No async progress runner; `running_or_requested` remains a reserved state.
- Clinical project preview remains callable by service code, but the main workflow does not present it as expression-clinical mapping ready without B6.4 expression build.

## Next Stage

The next stage can focus on data-check/preflight UX for TCGA expression plus clinical readiness: comparison confirmation, value-type confirmation, and survival preflight configuration without executing analyses.
