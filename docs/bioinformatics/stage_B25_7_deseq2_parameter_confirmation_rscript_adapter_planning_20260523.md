# B25.7 DESeq2 Parameter Confirmation / Rscript Adapter Planning

Date: 2026-05-23

## Scope

B25.7 advances DESeq2 after the B25.6 count-model activation plan. This stage
adds a DESeq2 parameter confirmation contract and a DESeq2 Rscript adapter plan,
but it still does not enable DESeq2 execution.

edgeR remains at B25.6 planning-only status and is not advanced in this stage.

## Implemented Contract Surface

Added:

- `app/bioinformatics/deg_engine/r_deseq2_planning.py`
- `build_r_deseq2_parameter_manifest(...)`
- `validate_r_deseq2_parameter_manifest(...)`
- `save_r_deseq2_parameter_confirmation(...)`
- `load_r_deseq2_parameter_confirmation(...)`
- `validate_r_deseq2_parameter_confirmation(...)`
- `build_r_deseq2_rscript_adapter_plan(...)`

The DESeq2 parameter manifest records:

- input package and DEG-ready package ids;
- case/control comparison and sample lists;
- raw integer count value-type policy;
- gene mapping and sample alignment policy;
- thresholds and FDR policy;
- DESeq2 size factor policy;
- dispersion fit type;
- minimum count filter;
- dependency snapshot;
- expression table path and sample/group map;
- blockers and warnings.

## Blockers

The DESeq2 manifest blocks:

- TPM/FPKM/normalized/log display values;
- non-count or unknown value type;
- missing count table path;
- missing sample/group map;
- missing case/control samples;
- same case/control group;
- dependency snapshot not passed;
- invalid thresholds;
- invalid minimum count filter;
- invalid size factor policy;
- invalid dispersion fit type.

The adapter plan always remains blocked by:

- `b25_7_deseq2_rscript_adapter_planning_only`;
- `deseq2_rscript_execution_adapter_not_implemented`;
- `deseq2_result_registration_handoff_not_implemented`.

## Analysis UI Behavior

Analysis Center now includes:

- DESeq2 parameter manifest state in `r_count_model_plans.plans.deseq2`;
- DESeq2 parameter confirmation gate;
- DESeq2 Rscript adapter plan;
- disabled action row `r_deseq2_parameter_confirmation`;
- disabled action row `formal_deg_deseq2_rscript`.

The UI remains explicit that DESeq2 confirmation is not user-enabled in B25.7
and DESeq2 execution is not enabled.

## Boundaries

- No DESeq2 Rscript invocation.
- No DESeq2 result index write.
- No DESeq2 `formal_computed_result`.
- No DESeq2 plot or report-ready output.
- No edgeR activation.
- No GSEA, survival, clinical conclusion or full integrated report change.
- No automatic R/Bioconductor package installation.

## Validation Commands

```bash
git diff --check
python3 -m py_compile app/bioinformatics/deg_engine/r_deseq2_planning.py app/bioinformatics/deg_engine/r_count_model_planning.py app/bioinformatics/deg_engine/__init__.py app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py app/bioinformatics/deg_engine/r_backend_handoff.py
python3 -m pytest -q tests/bioinformatics/test_r_deseq2_planning.py tests/bioinformatics/test_r_count_model_planning.py tests/bioinformatics/test_r_deg_external_handoff.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py
python3 -m pytest tests/bioinformatics -q -k "deseq2 or r_deg or count_model or multifactor or analysis_ui or formal_deg"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or results_browser"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

## Validation Results

Baseline before this B25.7 commit: `2746ba2`.

- `git diff --check`: passed.
- `python3 -m py_compile app/bioinformatics/deg_engine/r_deseq2_planning.py app/bioinformatics/deg_engine/r_count_model_planning.py app/bioinformatics/deg_engine/__init__.py app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py app/bioinformatics/deg_engine/r_backend_handoff.py`: passed.
- `python3 -m pytest -q tests/bioinformatics/test_r_deseq2_planning.py tests/bioinformatics/test_r_count_model_planning.py tests/bioinformatics/test_r_deg_external_handoff.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py`: 35 passed.
- `python3 -m pytest tests/bioinformatics -q -k "deseq2 or r_deg or count_model or multifactor or analysis_ui or formal_deg"`: 80 passed, 607 deselected.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or results_browser"`: 18 passed, 98 deselected.
- `python3 -m pytest tests/bioinformatics -q`: 687 passed, 1 existing scipy precision warning.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`: 273 passed.
- `python3 -m app.main --smoke-test`: passed, source launch, `git_head=2746ba2`.
- `python3 scripts/package_app.py --smoke-test`: passed, packaged local Python launcher, `git_head=2746ba2`, ad-hoc signed.
- `open -W -n dist/BioMedPilot.app --args --smoke-test`: passed.
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`: passed.

## ReleaseBuild Recommendation

ReleaseBuild can show DESeq2 as a planned count-model method with parameter
confirmation and adapter-plan diagnostics. It must not advertise DESeq2 as an
implemented execution capability until a later stage runs a real count fixture,
validates output schema, registers result index v2, and passes source/package
open-W/codesign checks.
