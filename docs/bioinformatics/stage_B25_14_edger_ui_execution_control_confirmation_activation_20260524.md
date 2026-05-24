# B25.14 edgeR UI Execution Control / User Confirmation Activation

## Scope

B25.14 activates the user-facing Analysis Center controls for the controlled
edgeR Rscript adapter. This is limited to raw-count, design-preflighted edgeR
execution through the audited adapter path.

This stage does not activate generic external edgeR handoff, GSEA, survival,
clinical conclusions, formal plot generation, or report-ready export.

## Implemented Gates

edgeR UI execution is enabled only when all project-local gates pass:

- B8 resolver provides a DEG recompute package from standardized assets.
- The selected expression asset is a raw integer count matrix.
- The count-model design preflight is `design_ready`.
- Detect-only Rscript/Bioconductor/edgeR runtime detection passes.
- The edgeR parameter manifest passes.
- The user saves an edgeR parameter confirmation manifest.
- The controlled Rscript adapter can register a result through result index v2.

If any gate fails, the Analysis Center keeps the edgeR run action disabled and
shows the concrete disabled reason.

## UI Changes

Analysis Center now includes:

- `Confirm edgeR parameters`
- `Run edgeR count-model DEG`

The confirmation button is enabled only after design/runtime/parameter manifest
gates pass. The run button is enabled only after confirmation also passes.

The edgeR capability row may show `formal_execution_enabled=True` only for this
audited UI path after all gates pass. It still sets `can_display_as_completed`
to `False` until a run result exists.

## Execution Boundary

The edgeR action writes a formal DEG result only after real Rscript execution
succeeds and the output schema/result bundle/result index gates pass.

Registered result boundaries remain:

- `result_semantics=formal_computed_result`
- `engine_name=r_edger_rscript_adapter`
- canonical DEG table plus edgeR method table
- `plot_artifacts=[]`
- `report_artifacts=[]`
- `report_ready_eligible=False`

Generic external edgeR handoff remains disabled. Users must use the controlled
adapter path; imported or externally produced edgeR tables are not upgraded to
BioMedPilot formal recomputed results.

## Still Disabled

- volcano/heatmap/formal DEG plot generation from edgeR
- report-ready package generation from edgeR
- GSEA activation as part of this flow
- survival or clinical analysis activation
- clinical interpretation, prognosis, or treatment advice
- automatic installation of R, Bioconductor, DESeq2, or edgeR

## Validation

- `git diff --check`: passed
- `python3 -m py_compile ...`: passed
- `python3 -m pytest -q tests/bioinformatics/test_r_edger_planning.py tests/bioinformatics/test_r_count_model_planning.py tests/bioinformatics/test_r_deg_external_handoff.py tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_r_edger_ui_activation.py`: 33 passed
- `python3 -m pytest -q tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_capability_map.py tests/bioinformatics/test_r_deseq2_ui_activation.py tests/bioinformatics/test_r_deseq2_planning.py tests/bioinformatics/test_r_deseq2_runtime.py tests/bioinformatics/test_r_edger_ui_activation.py`: 20 passed
- `python3 -m pytest tests/bioinformatics -q -k "edger or count_model or r_deg or analysis_ui"`: 52 passed, 650 deselected
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or results_browser"`: 18 passed, 98 deselected
- `python3 -m pytest tests/bioinformatics -q`: 702 passed, 1 SciPy precision warning
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`: 273 passed
- `python3 -m app.main --bio-r-edger-runtime-check --bio-r-edger-runtime-check-output /tmp/biomedpilot_b25_14_source_edger_runtime.json`: passed
- `python3 -m app.main --smoke-test`: passed
- `python3 scripts/package_app.py --smoke-test`: passed
- packaged executable `--bio-r-edger-runtime-check`: passed
- `open -W -n dist/BioMedPilot.app --args --bio-r-edger-runtime-check ...`: passed
- `open -W -n dist/BioMedPilot.app --args --smoke-test`: passed
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`: passed

Packaged/open-W runtime evidence:

- architecture: `arm64`
- launch mode: `packaged-local-python`
- Rscript: `/usr/local/bin/Rscript`
- R: `4.4.2`
- BiocManager: `1.30.25`
- edgeR: `4.4.2`
- controlled fixture: passed
- numeric p-value: present
- numeric adjusted p-value/FDR: present
- result index status: passed
- report-ready: false
- plot/report artifacts: empty
- UI runtime preflight: `runtime_preflight_passed_ui_gates_required`
- UI runtime preflight blockers: empty
