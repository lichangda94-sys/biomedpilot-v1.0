# B25.4 limma Design Config UX / Controlled Run Acceptance

Date: 2026-05-22

## Scope

B25.4 adds the missing limma design-config preparation step between B25.3 UI
gates and B25.2 Rscript execution. It lets Analysis Center generate a
reviewable `manifests/r_limma_design_config.json` from DEG-ready sample/group
assignments, then verifies the gated path can proceed through user confirmation
and controlled limma Rscript result registration.

## Implemented

- Added `app/bioinformatics/deg_engine/r_limma_design.py`.
- Added `build_r_limma_design_config(...)`.
- Added `save_r_limma_design_config(...)`.
- Added Analysis Center action `r_limma_design_config`.
- Added UI button `prepareRLimmaDesignConfigButton`.
- Extended the B25.4 acceptance test to cover:
  - missing design config blocks limma execution;
  - generated design config records case/control samples;
  - limma parameter confirmation becomes available;
  - confirmed limma Rscript action becomes enabled;
  - controlled fake-Rscript execution registers a formal DEG result through B25 handoff.

## Design Config Output

The generated file is:

```text
manifests/r_limma_design_config.json
```

It contains:

- `sample_table` with `sample_id` and `group`;
- `primary_factor=group`;
- `case_group`;
- `control_group`;
- contrast with case/control samples;
- `status=confirmed` only when groups are valid and each side has at least two samples;
- `semantic_boundary=r_limma_design_config_only_not_execution`.

## UI Gate Behavior

`formal_deg_limma_rscript` remains disabled until:

1. DEG-ready package is present and unblocked.
2. limma design config is generated and preflight is `design_ready`.
3. Rscript/BiocManager/limma detection passes.
4. limma parameter manifest passes.
5. user limma parameter confirmation passes.
6. result schema gate passes.

## Boundaries Preserved

- Design config generation does not execute limma.
- No DESeq2/edgeR activation.
- No automatic R/Bioconductor install.
- No plot/report-ready activation.
- No GSEA/survival/clinical conclusion activation.
- Registered limma result remains `report_ready_eligible=False`.

## Validation

```bash
git diff --check
python3 -m py_compile app/bioinformatics/deg_engine/r_limma_design.py app/bioinformatics/deg_engine/r_limma_confirmation.py app/bioinformatics/deg_engine/rscript_adapter.py app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py app/bioinformatics/workflow_pages.py
python3 -m pytest -q tests/bioinformatics/test_r_limma_design_ui_flow.py tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_r_limma_rscript_adapter.py
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
