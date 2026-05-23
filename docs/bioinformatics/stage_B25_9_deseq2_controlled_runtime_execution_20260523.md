# B25.9 DESeq2 Controlled Runtime Execution

Date: 2026-05-23

## Scope

B25.9 adds a controlled DESeq2 Rscript runtime adapter for real count fixtures.
This stage validates that the backend can run DESeq2, produce real `pvalue` and
`padj`, validate output schema, and register result index v2.

The user-facing Analysis UI remains gated: DESeq2 buttons are still disabled.
edgeR remains planning-only.

## Implemented Runtime Surface

Added:

- `app/bioinformatics/deg_engine/r_deseq2_runtime.py`
- `detect_r_deseq2_runtime_capabilities(...)`
- `run_r_deseq2_rscript_execution(...)`

The adapter:

- detects system/user Rscript and DESeq2 without installing packages;
- validates raw integer count table inputs;
- writes command manifest and command log;
- runs DESeq2 through `Rscript`;
- validates DESeq2 output schema;
- writes canonical DEG table and DESeq2 method-specific table;
- validates formal DEG result bundle and result index v2 entry;
- registers result index v2 only after all gates pass.

## Result Boundary

Successful controlled fixture execution writes:

- `result_semantics=formal_computed_result`;
- `engine_name=r_deseq2_rscript_adapter`;
- canonical DEG table;
- DESeq2 method-specific table;
- command manifest/log and run log;
- `plot_artifacts=[]`;
- `report_artifacts=[]`;
- `report_ready_eligible=False`.

Blocked execution writes no result index.

## Small-Fixture Dispersion Policy

The controlled fixture may trigger DESeq2's dispersion fit failure because the
fixture is intentionally small. The adapter records a fallback policy in the
command manifest: if DESeq dispersion fitting fails, use gene-wise dispersion
estimates followed by `nbinomWaldTest`, matching the remediation described by
DESeq2's own runtime error.

This is still real DESeq2 computation. No p-value or FDR is synthesized.

## UI Boundary

B25.9 does not change user-visible DESeq2 execution availability:

- `r_deseq2_parameter_confirmation` remains disabled;
- `formal_deg_deseq2_rscript` remains disabled;
- Analysis Center continues to label DESeq2 as gated/planning until a later UI
  activation stage.

## Not Implemented

- No user-facing DESeq2 run button.
- No edgeR execution.
- No DESeq2 plot artifact.
- No DESeq2 report-ready package.
- No GSEA, survival, clinical conclusion or full integrated report change.
- No automatic R/Bioconductor installation.

## Validation Commands

```bash
git diff --check
python3 -m py_compile app/bioinformatics/deg_engine/r_deseq2_runtime.py app/bioinformatics/deg_engine/r_deseq2_planning.py app/bioinformatics/deg_engine/r_count_model_planning.py app/bioinformatics/deg_engine/__init__.py
python3 -m pytest -q tests/bioinformatics/test_r_deseq2_runtime.py tests/bioinformatics/test_r_deseq2_planning.py tests/bioinformatics/test_r_count_model_planning.py
python3 -m pytest -q tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_r_deg_external_handoff.py
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

- `git diff --check`: passed.
- `py_compile` for DESeq2 runtime/planning/count-model modules: passed.
- `test_r_deseq2_runtime.py`, `test_r_deseq2_planning.py`,
  `test_r_count_model_planning.py`: 12 passed.
- Analysis UI/action/handoff focused tests: 28 passed.
- Bioinformatics selected regression for DESeq2/R DEG/count model/analysis UI/formal DEG:
  80 passed, 612 deselected.
- Focused UI workflow regression: 18 passed, 98 deselected.
- Full `tests/bioinformatics`: 692 passed, 1 expected numeric precision warning from
  an existing GEO DEG fixture.
- Full `tests/ui`: 273 passed.
- Source smoke: passed with `git_head=b704440`.
- Package smoke: passed with `dist/BioMedPilot.app`, local Python launcher, ad-hoc
  signing, and `git_head=b704440`.
- `open -W -n dist/BioMedPilot.app --args --smoke-test`: passed.
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`: passed.

## ReleaseBuild Recommendation

ReleaseBuild can treat the DESeq2 backend as controlled-runtime validated for
internal fixtures. It should still not expose user-facing DESeq2 execution until
a later UI activation stage confirms package/open-W/codesign, user confirmation
flow, and disabled-reason transitions in the Analysis Center.
