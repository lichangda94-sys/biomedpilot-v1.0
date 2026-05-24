# B25.13 edgeR Controlled Runtime Execution

## Scope

B25.13 adds a controlled edgeR Rscript execution adapter for real count fixtures.
This validates that edgeR can produce real `PValue` and `FDR`, that output
schema checks pass, and that the result can be registered through result index
v2.

This stage does not activate the user-facing edgeR UI execution button.

## Implemented

- Controlled edgeR Rscript adapter.
- Raw integer count table validation.
- Design table generation from confirmed sample/group assignments.
- edgeR exact-test output schema validation:
  - `feature_id`
  - `logFC`
  - `logCPM`
  - `PValue`
  - `FDR`
- Canonical DEG table registration.
- edgeR method-specific table registration.
- result index v2 formal DEG registration.
- task-run command manifest and command log.
- source/package/open-W runtime check path through:
  - `--bio-r-edger-runtime-check`
  - `--bio-r-edger-runtime-check-output`

## Formal Result Boundary

The controlled runtime adapter can register `formal_computed_result` only after:

- Rscript/edgeR dependency detection passes;
- raw count fixture validation passes;
- edgeR output schema passes;
- result bundle validation passes;
- result index v2 validation passes.

Registered edgeR fixture results keep:

- `plot_artifacts=[]`
- `report_artifacts=[]`
- `report_ready_eligible=False`

## UI Boundary

Analysis Center still blocks user-facing edgeR execution with:

- `b25_14_edger_ui_activation_required`

Generic external edgeR handoff remains disabled:

- `r_edger_generic_external_handoff_disabled_use_controlled_rscript_adapter`

## Still Disabled

- edgeR UI run button.
- edgeR user confirmation flow.
- edgeR plot artifacts.
- edgeR report-ready package.
- GSEA activation.
- survival/clinical activation.
- clinical interpretation.
- automatic installation or bundling of R/Bioconductor/edgeR.

## Source Runtime Evidence

`python3 -m app.main --bio-r-edger-runtime-check --bio-r-edger-runtime-check-output /tmp/biomedpilot_b25_13_source_edger_runtime_dev.json`

Observed:

- status: `passed`
- architecture: `arm64`
- Rscript: `/usr/local/bin/Rscript`
- R: `4.4.2`
- BiocManager: `1.30.25`
- edgeR: `4.4.2`
- controlled fixture: passed
- numeric p-value: present
- numeric adjusted p-value/FDR: present
- result index: passed
- UI activation preflight: blocked

## Validation

- `python3 -m py_compile app/main.py app/bioinformatics/deg_engine/r_edger_runtime.py app/bioinformatics/deg_engine/r_edger_runtime_validation.py app/bioinformatics/deg_engine/r_edger_planning.py app/bioinformatics/deg_engine/r_count_model_planning.py app/bioinformatics/analysis_ui/action_rules.py app/bioinformatics/analysis_ui/capability_map.py app/bioinformatics/workflow_pages.py app/bioinformatics/deg_engine/__init__.py`: passed
- `python3 -m pytest -q tests/bioinformatics/test_r_edger_planning.py tests/bioinformatics/test_r_count_model_planning.py tests/bioinformatics/test_r_deg_external_handoff.py tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_capability_map.py`: 39 passed
- `python3 -m pytest tests/bioinformatics -q -k "edger or count_model or r_deg or analysis_ui"`: 50 passed, 650 deselected
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or results_browser"`: 18 passed, 98 deselected
- `python3 -m pytest tests/bioinformatics -q`: 700 passed, 1 SciPy precision warning
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`: 273 passed
- `python3 -m app.main --smoke-test`: passed
- `python3 scripts/package_app.py --smoke-test`: passed
- packaged executable `--bio-r-edger-runtime-check`: passed
- `open -W -n dist/BioMedPilot.app --args --bio-r-edger-runtime-check ...`: passed
- `open -W -n dist/BioMedPilot.app --args --smoke-test`: passed
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`: passed

Packaged/open-W runtime evidence:

- architecture: `arm64`
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
- activation preflight: blocked with `b25_14_edger_ui_activation_required`

## Conclusion

B25.13 validates controlled edgeR runtime execution and result-index registration
for fixtures. The next stage should be B25.14 edgeR UI activation preflight, and
only after it proves user confirmation, result schema gates, package/open-W and
codesign remain stable.
