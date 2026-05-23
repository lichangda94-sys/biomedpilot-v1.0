# B25.8 DESeq2 Real Count Fixture / Output Schema / Result Index Dry-Run Acceptance Planning

Date: 2026-05-23

## Scope

B25.8 adds a DESeq2 dry-run acceptance gate for the next activation step. It
validates the contracts needed before real DESeq2 execution can be enabled, but
it does not invoke DESeq2, does not write result index v2, and does not create a
formal result.

edgeR remains unchanged at planning-only status.

## Implemented Contract Surface

Extended `app/bioinformatics/deg_engine/r_deseq2_planning.py` with:

- `validate_r_deseq2_count_fixture(...)`
- `build_r_deseq2_dry_run_acceptance_gate(...)`

The dry-run acceptance gate validates:

- raw integer count fixture rows and sample ids;
- DESeq2 method-specific output schema via `validate_r_deg_output_schema("deseq2", ...)`;
- candidate formal DEG result-index v2 entry shape;
- result registration bundle gate for DESeq2 output columns;
- report/plot boundary: `plot_artifacts=[]`, `report_artifacts=[]`, `report_ready_eligible=False`.

## Dry-Run Boundary

Even when all dry-run contract checks pass, the gate remains:

- `status=planned_not_enabled`;
- `formal_execution_enabled=False`;
- `can_execute=False`;
- `can_register_formal_result=False`;
- `writes_result_index=False`;
- `result_semantics=not_executed`.

The permanent blocker for this stage is:

- `b25_8_deseq2_dry_run_only_no_result_index_write`.

This prevents a valid dry-run candidate result-index entry from being mistaken
for a registered formal DESeq2 result.

## Blockers

The dry-run gate blocks:

- missing count fixture rows;
- fewer than four fixture samples;
- non-numeric, negative or non-integer count values;
- missing DESeq2 output columns such as `log2FoldChange`, `lfcSE`, `stat`, `pvalue`, `padj`;
- parameter manifest not passed;
- dependency snapshot not passed;
- result registration schema failure;
- formal result-index schema failure.

## Analysis UI Behavior

The DESeq2 count-model plan now carries `dry_run_acceptance_gate` in
`r_count_model_plans.plans.deseq2`. UI actions remain disabled:

- `r_deseq2_parameter_confirmation`;
- `formal_deg_deseq2_rscript`.

## Not Implemented

- No real DESeq2 Rscript execution.
- No generated DESeq2 TSV in project results.
- No result index write.
- No formal `formal_computed_result` registration.
- No plot artifact.
- No report-ready package.
- No edgeR activation.

## Validation Commands

```bash
git diff --check
python3 -m py_compile app/bioinformatics/deg_engine/r_deseq2_planning.py app/bioinformatics/deg_engine/r_count_model_planning.py app/bioinformatics/deg_engine/__init__.py
python3 -m pytest -q tests/bioinformatics/test_r_deseq2_planning.py tests/bioinformatics/test_r_count_model_planning.py
python3 -m pytest -q tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py
python3 -m pytest tests/bioinformatics -q -k "deseq2 or r_deg or count_model or analysis_ui or formal_deg"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or results_browser"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

## Validation Results

Baseline before this B25.8 commit: `df42459`.

- `git diff --check`: passed.
- `python3 -m py_compile app/bioinformatics/deg_engine/r_deseq2_planning.py app/bioinformatics/deg_engine/r_count_model_planning.py app/bioinformatics/deg_engine/__init__.py`: passed.
- `python3 -m pytest -q tests/bioinformatics/test_r_deseq2_planning.py tests/bioinformatics/test_r_count_model_planning.py`: 10 passed.
- `python3 -m pytest -q tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_r_deg_external_handoff.py`: 28 passed.
- `python3 -m pytest tests/bioinformatics -q -k "deseq2 or r_deg or count_model or analysis_ui or formal_deg"`: 78 passed, 612 deselected.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or results_browser"`: 18 passed, 98 deselected.
- `python3 -m pytest tests/bioinformatics -q`: 690 passed, 1 existing scipy precision warning.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`: 273 passed.
- `python3 -m app.main --smoke-test`: passed, source launch, `git_head=df42459`.
- `python3 scripts/package_app.py --smoke-test`: passed, packaged local Python launcher, `git_head=df42459`, ad-hoc signed.
- `open -W -n dist/BioMedPilot.app --args --smoke-test`: passed.
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`: passed.

## ReleaseBuild Recommendation

ReleaseBuild can expose DESeq2 dry-run acceptance diagnostics to developers,
but should continue to present DESeq2 as not executable to users. The next stage
should be real DESeq2 Rscript fixture execution in a controlled runtime; only
after that should result registration be considered.
