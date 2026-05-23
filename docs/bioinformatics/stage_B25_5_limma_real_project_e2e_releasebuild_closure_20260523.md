# B25.5 limma Real-Project E2E / ReleaseBuild Closure

Date: 2026-05-23

## Scope

B25.5 closes the limma-first R backend path with a real `Rscript + limma`
end-to-end acceptance test and ReleaseBuild audit. The scope remains limited to
limma DEG execution through the B25 handoff/result-index gates.

## Accepted Flow

The accepted flow is:

1. Build a DEG-ready standardized project fixture.
2. Analysis Center shows `formal_deg_limma_rscript` disabled while design config is missing.
3. Generate `manifests/r_limma_design_config.json`.
4. Analysis Center enables limma parameter confirmation but keeps execution disabled.
5. Save `manifests/r_limma_parameter_confirmation.json`.
6. Analysis Center enables `formal_deg_limma_rscript`.
7. Execute real system `Rscript` with limma.
8. Register the result through B25 handoff and result index v2.

## Result Contract

The real limma E2E test verifies:

- `result_semantics=formal_computed_result`;
- `engine_name=r_limma_rscript_adapter`;
- output artifacts include canonical DEG table and limma method-specific table;
- log artifacts include handoff log, command manifest, and command log;
- canonical table contains real `p_value` and `adjusted_p_value`;
- `plot_artifacts=[]`;
- `report_artifacts=[]`;
- `report_ready_eligible=False`.

## Boundary Checks

- DESeq2 remains disabled.
- edgeR remains disabled.
- No GSEA activation.
- No survival activation.
- No formal plot activation.
- No report-ready activation.
- R/Bioconductor packages are detected from the user/system environment; they are not installed or bundled.

## Fix Included

The B25.5 E2E test exposed an Analysis Center gate mismatch: after a user
confirmed non-default limma thresholds, the limma parameter gate was rebuilt
with default thresholds and the confirmation gate reported threshold mismatch.

This is fixed by rebuilding the current limma parameter manifest from confirmed
thresholds when a limma confirmation manifest exists.

## ReleaseBuild Recommendation

ReleaseBuild can treat the limma Rscript path as a gated MVP candidate:

- ready for internal tester validation with system R/limma installed;
- not ready to advertise as DESeq2/edgeR support;
- not ready to advertise as integrated report support;
- not ready to advertise as clinical or survival interpretation.

## Validation Results

Baseline before this B25.5 commit: `7ddef05`.

- `git diff --check`: passed.
- `python3 -m py_compile app/bioinformatics/analysis_ui/state.py`: passed.
- `python3 -m pytest -q tests/bioinformatics/test_r_limma_real_runtime_e2e.py tests/bioinformatics/test_r_limma_design_ui_flow.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_r_limma_rscript_adapter.py`: 30 passed.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or results_browser"`: 18 passed, 98 deselected.
- `python3 -m pytest tests/bioinformatics -q -k "r_deg or r_limma or multifactor or analysis_ui or formal_deg"`: 76 passed, 603 deselected.
- `python3 -m pytest tests/bioinformatics -q`: 679 passed, 1 existing scipy precision warning.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`: 273 passed.
- `python3 -m app.main --smoke-test`: passed, source launch, `git_head=7ddef05`.
- `python3 scripts/package_app.py --smoke-test`: passed, packaged local Python launcher, `git_head=7ddef05`, ad-hoc signed.
- `open -W -n dist/BioMedPilot.app --args --smoke-test`: passed.
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`: passed.

## Validation Commands

```bash
git diff --check
python3 -m py_compile app/bioinformatics/analysis_ui/state.py
python3 -m pytest -q tests/bioinformatics/test_r_limma_real_runtime_e2e.py tests/bioinformatics/test_r_limma_design_ui_flow.py tests/bioinformatics/test_analysis_ui_state.py
python3 -m pytest -q tests/bioinformatics/test_r_limma_real_runtime_e2e.py tests/bioinformatics/test_r_limma_design_ui_flow.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_r_limma_rscript_adapter.py
python3 -m pytest tests/bioinformatics -q -k "r_deg or r_limma or multifactor or analysis_ui or formal_deg"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or results_browser"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```
