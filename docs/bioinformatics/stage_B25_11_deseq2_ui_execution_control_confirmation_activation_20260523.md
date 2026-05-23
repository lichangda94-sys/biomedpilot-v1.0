# B25.11 DESeq2 UI Execution Control / User Confirmation Activation

## Scope

B25.11 activates the user-facing Analysis Center controls for the controlled
DESeq2 Rscript adapter. This is limited to raw-count, two-group/multi-factor
design-preflighted DESeq2 execution through the audited adapter path.

This stage does not activate edgeR, GSEA, survival, clinical conclusions,
formal plot generation, or report-ready export.

## Implemented Gates

DESeq2 UI execution is enabled only when all of these project-local gates pass:

- B8 resolver provides a DEG recompute package from standardized assets.
- The selected expression asset is a raw integer count matrix.
- The count-model design preflight is `design_ready`.
- Detect-only Rscript/Bioconductor/DESeq2 runtime detection passes.
- The DESeq2 parameter manifest passes.
- The user saves a DESeq2 parameter confirmation manifest.
- The controlled Rscript adapter can register a result through result index v2.

If any gate fails, the Analysis Center keeps the DESeq2 run action disabled and
shows the concrete disabled reason.

## UI Changes

Analysis Center now includes:

- `Confirm DESeq2 parameters`
- `Run DESeq2 count-model DEG`

The confirmation button is enabled only after design/runtime/parameter manifest
gates pass. The run button is enabled only after confirmation also passes.

The DESeq2 capability row may show `formal_execution_enabled=True` only for this
audited UI path after all gates pass. It still sets `can_display_as_completed`
to `False` until a run result exists.

## Execution Boundary

The DESeq2 action writes a formal DEG result only after real Rscript execution
succeeds and the output schema/result bundle/result index gates pass.

Registered result boundaries remain:

- `result_semantics=formal_computed_result`
- `engine_name=r_deseq2_rscript_adapter`
- canonical DEG table plus DESeq2 method table
- `plot_artifacts=[]`
- `report_artifacts=[]`
- `report_ready_eligible=False`

Generic external DESeq2 handoff remains disabled. Users must use the controlled
adapter path; imported or externally produced DESeq2 tables are not upgraded to
BioMedPilot formal recomputed results.

## Still Disabled

- edgeR Rscript execution
- volcano/heatmap/formal DEG plot generation from DESeq2
- report-ready package generation from DESeq2
- GSEA activation as part of this flow
- survival or clinical analysis activation
- clinical interpretation, prognosis, or treatment advice
- automatic installation of R, Bioconductor, DESeq2, or edgeR

## Validation

- `git diff --check`: passed
- `python3 -m py_compile ...`: passed
- `python3 -m pytest -q tests/bioinformatics/test_r_deg_external_handoff.py tests/bioinformatics/test_r_deseq2_ui_activation.py tests/bioinformatics/test_r_deseq2_runtime.py tests/bioinformatics/test_r_deseq2_planning.py tests/bioinformatics/test_r_count_model_planning.py tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py`: 43 passed
- `python3 -m pytest tests/bioinformatics -q -k "deseq2 or r_deg or count_model or analysis_ui or formal_deg"`: 83 passed, 612 deselected
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or results_browser"`: 18 passed, 98 deselected
- `python3 -m pytest tests/bioinformatics -q`: 695 passed, 1 SciPy precision warning
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`: 273 passed
- `python3 -m app.main --smoke-test`: passed
- `python3 scripts/package_app.py --smoke-test`: passed
- packaged executable `--bio-r-deseq2-runtime-check`: passed
- `open -W -n dist/BioMedPilot.app --args --bio-r-deseq2-runtime-check ...`: passed
- `open -W -n dist/BioMedPilot.app --args --smoke-test`: passed
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`: passed

Packaged/open-W runtime evidence:

- architecture: `arm64`
- Rscript: `/usr/local/bin/Rscript`
- R: `4.4.2`
- BiocManager: `1.30.25`
- DESeq2: `1.46.0`
- controlled fixture: passed
- numeric `p_value`: present
- numeric `adjusted_p_value`: present
- result index v2 registration: passed
- report-ready: false
- plot/report artifacts: empty

## Conclusion

B25.11 passes. ReleaseBuild can expose DESeq2 controlled UI execution behind the
resolver, raw-count design, dependency detection, user confirmation, and result
schema gates.

Next recommended stage: B25.12 edgeR parameter/runtime planning, still without
execution until real fixture, result index, package/open-W, and UI gate checks
pass independently.
