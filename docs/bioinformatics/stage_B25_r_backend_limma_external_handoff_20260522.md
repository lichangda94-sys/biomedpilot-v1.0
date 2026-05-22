# B25 R Backend Integration Planning / Execution - limma First

Date: 2026-05-22

## Scope

B25 starts R backend integration with limma only. This stage does not invoke R,
install R packages, bundle Bioconductor, or enable DESeq2/edgeR formal
execution. It adds a controlled external limma handoff surface that can accept
audited method output and register a formal DEG result only when all upstream
contracts pass.

## Implemented

- Added `app/bioinformatics/deg_engine/r_backend_handoff.py`.
- Added `register_r_limma_external_handoff_result(...)`.
- Added `build_r_deg_external_handoff_plan(...)`.
- Exported the B25 handoff functions from `app.bioinformatics.deg_engine`.
- Added B25 tests in `tests/bioinformatics/test_r_deg_external_handoff.py`.

## limma Gate Chain

The limma handoff writes a `formal_computed_result` only after:

1. B18 multi-factor design preflight is `design_ready`.
2. B19 R runtime capability gate is ready for external runtime execution.
3. External execution status is `succeeded`.
4. limma output schema contains `feature_id`, `logFC`, `AveExpr`, `t`,
   `P.Value`, and `adj.P.Val`.
5. statistical columns are numeric and feature IDs are present.
6. `input_package_id` is present.
7. canonical DEG result bundle validation passes.
8. R DEG result registration bundle validation passes.
9. formal DEG result index v2 validation passes.

## Output Registration

Successful limma handoff writes:

- canonical DEG table under `results/tables/<result_id>.tsv`;
- method-specific limma table under `results/tables/r_limma/<result_id>_limma.tsv`;
- run log under `analysis/r_deg/limma/<result_id>_run_log.json`;
- result index v2 entry with:
  - `result_semantics=formal_computed_result`;
  - `engine_name=r_limma_external_handoff`;
  - dependency snapshot;
  - parameters manifest;
  - output artifacts for canonical and limma tables;
  - `plot_artifacts=[]`;
  - `report_artifacts=[]`;
  - `report_ready_eligible=False`.

## Explicitly Not Implemented

- No R invocation from BioMedPilot.
- No automatic installation of R, Bioconductor, limma, DESeq2, or edgeR.
- No DESeq2 formal result registration.
- No edgeR formal result registration.
- No GSEA, survival, formal plot, or report-ready activation.
- No clinical conclusion generation.

## DESeq2 / edgeR Plan

`build_r_deg_external_handoff_plan("DESeq2")` and
`build_r_deg_external_handoff_plan("edgeR")` return `planned_not_enabled` with
method-specific blockers. They should only move forward after limma handoff has
been accepted and method-specific parameter, output, and result review contracts
are added.

## Validation

Required validation for this stage:

```bash
git diff --check
python3 -m py_compile app/bioinformatics/deg_engine/r_backend_handoff.py app/bioinformatics/deg_engine/__init__.py
python3 -m pytest -q tests/bioinformatics/test_r_deg_external_handoff.py tests/bioinformatics/test_r_deg_adapter_contract.py
python3 -m pytest tests/bioinformatics -q -k "r_deg or multifactor or analysis_ui or formal_deg"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or results_browser"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```
