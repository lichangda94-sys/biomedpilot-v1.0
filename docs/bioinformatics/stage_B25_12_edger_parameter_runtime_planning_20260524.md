# B25.12 edgeR Parameter / Runtime Planning

## Scope

B25.12 adds edgeR parameter-manifest planning and detect-first runtime
validation. It deliberately does not execute edgeR, does not write formal DEG
results, and does not enable a user-facing edgeR run button.

This stage is the edgeR counterpart to the DESeq2 planning/runtime phases before
real fixture execution and UI activation.

## Implemented

- edgeR detect-only runtime check:
  - Rscript path
  - R version/platform
  - BiocManager version
  - edgeR version
  - dependency snapshot with blockers when missing
- edgeR parameter manifest contract:
  - raw integer count input only
  - case/control comparison
  - sample/group alignment
  - threshold/FDR policy
  - normalization method
  - dispersion policy
  - test method
  - dependency snapshot
- edgeR adapter plan:
  - command manifest contract
  - output schema reference
  - result index v2 contract reference
  - explicit planning-only blockers
- Analysis Center integration:
  - edgeR dependency row uses detect-first status
  - edgeR count-model plan exposes parameter/runtime blockers
  - edgeR action remains disabled with concrete disabled reasons
  - capability map labels edgeR as B25.12 parameter/runtime planning
- CLI preflight:
  - `--bio-r-edger-runtime-check`
  - `--bio-r-edger-runtime-check-output`

## Hard Boundaries

edgeR remains blocked by:

- `b25_12_edger_planning_only_no_execution`
- `b25_13_edger_real_fixture_required`
- `b25_14_edger_ui_activation_required`
- `edger_rscript_execution_adapter_not_implemented`

B25.12 does not:

- run edgeR;
- register a formal edgeR result;
- write result index v2 for edgeR;
- generate edgeR p-values/FDR from a fixture;
- expose edgeR parameter confirmation as an executable UI flow;
- generate plot artifacts;
- generate report-ready packages;
- activate GSEA/survival/clinical conclusions;
- install or bundle R/Bioconductor/edgeR.

## Source Runtime Evidence

`python3 -m app.main --bio-r-edger-runtime-check --bio-r-edger-runtime-check-output /tmp/biomedpilot_b25_12_source_edger_runtime_final.json`

Observed in this environment:

- status: `passed`
- architecture: `arm64`
- Rscript: `/usr/local/bin/Rscript`
- R: `4.4.2`
- BiocManager: `1.30.25`
- edgeR: `4.4.2`
- execution activation preflight: `blocked`
- formal execution enabled: `False`
- normal user button enabled: `False`

## Validation

- `python3 -m py_compile app/main.py app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py app/bioinformatics/analysis_ui/capability_map.py app/bioinformatics/workflow_pages.py app/bioinformatics/deg_engine/r_backend_handoff.py app/bioinformatics/deg_engine/r_count_model_planning.py app/bioinformatics/deg_engine/r_edger_runtime.py app/bioinformatics/deg_engine/r_edger_planning.py app/bioinformatics/deg_engine/r_edger_runtime_validation.py app/bioinformatics/deg_engine/__init__.py`: passed
- `python3 -m pytest -q tests/bioinformatics/test_r_edger_planning.py tests/bioinformatics/test_r_count_model_planning.py tests/bioinformatics/test_r_deg_external_handoff.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_capability_map.py`: 39 passed
- `python3 -m pytest tests/bioinformatics -q -k "edger or count_model or r_deg or analysis_ui"`: 50 passed, 650 deselected
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or results_browser"`: 18 passed, 98 deselected
- source edgeR runtime check: passed

Full regression and package/open-W validation are recorded in the final task
handoff after this document.

## Conclusion

B25.12 is a planning and detect-first hardening stage only. ReleaseBuild may
display edgeR runtime availability and parameter blockers, but must continue to
keep edgeR formal execution disabled.

Next recommended stage: B25.13 edgeR real controlled fixture adapter planning
and implementation, still without UI activation until package/open-W/codesign
validation passes.
