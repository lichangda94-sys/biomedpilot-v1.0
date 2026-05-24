# B26 Multi-factor DEG Formal Execution Activation

## Scope

B26 activates multi-factor DEG execution only through the audited method-specific
Rscript adapters that already passed B25 gates:

- limma for normalized/log expression.
- DESeq2 for raw integer counts.
- edgeR for raw integer counts.

This stage does not add GSEA, plot, report-ready, survival, clinical
statistics, clinical interpretation, or legacy formal execution.

## Implemented

- Runtime design table generation from the B18 design config.
- Runtime design table columns:
  - `sample`
  - `group`
  - declared covariates, such as `batch` and `age`
- limma Rscript execution now builds a model matrix with group plus covariates
  and runs the configured case/control contrast.
- DESeq2 Rscript execution now builds a design formula with covariates plus
  `group`, then uses the case/control contrast.
- edgeR Rscript execution keeps exactTest for no-covariate two-group designs
  and uses GLM LRT when covariates are present.
- command manifests record:
  - `design_formula`
  - `covariates`
  - method-specific command/log paths
- result registration remains result index v2 only after runtime success,
  output schema validation and result bundle validation.

## Gate Boundary

Formal multi-factor DEG execution still requires:

- B8 resolver package from standardized assets.
- DEG-ready matrix.
- B18 design config and full-rank preflight.
- method-compatible value type:
  - limma: normalized/log expression.
  - DESeq2/edgeR: raw integer counts.
- detect-first R/Bioconductor/method dependency snapshot.
- method-specific parameter confirmation.
- method-specific result schema and result index v2 gates.

The B18 preflight manifest remains `preflight_only`. Only a method-specific
runtime result may become `formal_computed_result` after all B26 gates pass.

## Result Boundary

Registered results keep:

- `plot_artifacts=[]`
- `report_artifacts=[]`
- `report_ready_eligible=False`

No generated DEG result is promoted into plot/report-ready by B26.

## UI Boundary

Analysis UI continues to expose execution through method-specific controls:

- limma Rscript DEG
- DESeq2 count-model DEG
- edgeR count-model DEG

The multi-factor capability row now explains that B26 execution is available
only through those method-specific Rscript gates and still cannot be displayed
as completed without a validated formal result entry.

## Validation

- `git diff --check`: passed
- `python3 -m py_compile app/bioinformatics/deg_engine/runtime_design.py app/bioinformatics/deg_engine/multifactor_gate.py app/bioinformatics/deg_engine/rscript_adapter.py app/bioinformatics/deg_engine/r_deseq2_runtime.py app/bioinformatics/deg_engine/r_edger_runtime.py app/bioinformatics/deg_engine/r_edger_planning.py`: passed
- `python3 -m pytest -q tests/bioinformatics/test_deg_multifactor_preflight_gate.py tests/bioinformatics/test_r_limma_rscript_adapter.py tests/bioinformatics/test_r_deseq2_runtime.py tests/bioinformatics/test_r_edger_planning.py tests/bioinformatics/test_r_edger_ui_activation.py`: 25 passed
- `python3 -m pytest -q tests/bioinformatics/test_deg_multifactor_preflight_gate.py tests/bioinformatics/test_r_limma_rscript_adapter.py tests/bioinformatics/test_r_deseq2_runtime.py tests/bioinformatics/test_r_edger_planning.py tests/bioinformatics/test_r_edger_ui_activation.py tests/bioinformatics/test_analysis_capability_map.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py`: 53 passed
- `python3 -m pytest tests/bioinformatics -q -k "multifactor or multi_factor or r_limma or deseq2 or edger or r_deg or analysis_ui"`: 76 passed, 630 deselected
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or results_browser"`: 18 passed, 98 deselected
- `python3 -m pytest tests/bioinformatics -q`: 706 passed, 1 SciPy precision warning
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`: 273 passed
- source real Rscript multi-factor fixture:
  - limma runtime: passed
  - limma batch+age execution: passed
  - DESeq2 runtime: passed
  - DESeq2 batch+age execution: passed
  - edgeR runtime: passed
  - edgeR batch+age GLM LRT execution: passed
  - all three kept plot/report artifacts empty and report-ready false
- `python3 -m app.main --smoke-test`: passed
- `python3 scripts/package_app.py --smoke-test`: passed
- packaged executable `--bio-r-edger-runtime-check`: passed
- `open -W -n dist/BioMedPilot.app --args --smoke-test`: passed
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`: passed

Packaged runtime evidence:

- architecture: `arm64`
- launch mode: `packaged-local-python`
- Rscript: `/usr/local/bin/Rscript`
- R: `4.4.2`
- BiocManager: `1.30.25`
- edgeR: `4.4.2`
- result index status: passed
- report-ready: false
