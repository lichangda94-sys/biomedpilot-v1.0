# B25.3 limma UI Execution Control / User Confirmation Gate

Date: 2026-05-22

## Scope

B25.3 connects the B25.2 audited `Rscript + limma` execution adapter to the
Analysis Center as a gated UI action. This stage does not make limma look
completed by dependency availability alone, and it does not enable DESeq2,
edgeR, GSEA, survival, formal plotting, or report-ready export.

## Implemented

- Added `app/bioinformatics/deg_engine/r_limma_confirmation.py`.
- Added limma Rscript UI gate state in `analysis_ui/state.py`.
- Added two Analysis Center actions:
  - `r_limma_parameter_confirmation`
  - `formal_deg_limma_rscript`
- Added two UI buttons:
  - `confirmRLimmaParametersButton`
  - `runRLimmaRscriptDegButton`
- Updated capability map with `deg_limma_rscript_execution`.
- Added tests for action rules, Analysis Center state, and workflow page UI.

## Required Gate Conjunction

The limma Rscript execution button is enabled only when all of these pass:

1. B8 resolver package is present and unblocked.
2. DEG-ready package exists.
3. limma design preflight is `design_ready`.
4. Rscript/BiocManager/limma runtime detection passes.
5. B19 R adapter runtime gate is `ready_for_external_runtime_execution`.
6. limma parameter manifest passes.
7. user limma parameter confirmation passes.
8. result schema gate passes.

If any gate fails, the UI action remains disabled and the disabled reason lists
the contract blocker.

## User Confirmation Manifest

The limma confirmation manifest is:

```text
manifests/r_limma_parameter_confirmation.json
```

It records:

- comparison, case/control groups and samples;
- method `limma`;
- thresholds;
- value type and policy;
- R/BiocManager/limma dependency snapshot;
- expression table path;
- sample/group map;
- output plan and task-run id.

Confirmation is invalidated when confirmed parameters or R/limma dependency
versions no longer match the current gate snapshot.

## Design Config Input

The limma UI gate reads a design config from:

```text
manifests/r_limma_design_config.json
manifests/deg_multifactor_design_config.json
```

If no design config exists, the limma action is blocked with
`multi_factor_design_config_missing`. This is intentional; dependency detection
alone is not execution readiness.

## Boundaries Preserved

- No automatic installation of R/Bioconductor/limma.
- No `.app`-bundled R runtime.
- No DESeq2/edgeR execution.
- No formal GSEA or survival activation.
- No formal plot or report-ready activation.
- limma outputs still register through B25 handoff and result index v2.

## Validation

```bash
git diff --check
python3 -m py_compile app/bioinformatics/deg_engine/r_limma_confirmation.py app/bioinformatics/deg_engine/rscript_adapter.py app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py app/bioinformatics/analysis_ui/capability_map.py app/bioinformatics/workflow_pages.py
python3 -m pytest -q tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_r_limma_rscript_adapter.py
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task"
python3 -m pytest tests/bioinformatics -q -k "r_deg or r_limma or multifactor or analysis_ui or formal_deg"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or results_browser"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```
