# B25.2 Audited limma Rscript Execution Adapter

Date: 2026-05-22

## Scope

B25.2 activates a controlled limma execution adapter through a user/system
`Rscript`. It is not a general R backend activation and it does not install or
bundle R, Bioconductor, limma, DESeq2, edgeR, Pandoc, or LaTeX.

## Implemented

- Added `app/bioinformatics/deg_engine/rscript_adapter.py`.
- Added `detect_r_limma_runtime_capabilities(...)`.
- Added `run_r_limma_rscript_execution(...)`.
- Exported both functions from `app.bioinformatics.deg_engine`.
- Added `tests/bioinformatics/test_r_limma_rscript_adapter.py`.

## Execution Contract

The adapter uses:

```text
subprocess.run([Rscript, run_limma.R, expression.tsv, design.tsv, limma_output.tsv, contrast], shell=False)
```

The adapter writes:

- `analysis/r_deg/limma_rscript/<task_run_id>/run_limma.R`
- `analysis/r_deg/limma_rscript/<task_run_id>/design.tsv`
- `analysis/r_deg/limma_rscript/<task_run_id>/command_manifest.json`
- `analysis/r_deg/limma_rscript/<task_run_id>/command_log.json`
- `analysis/r_deg/limma_rscript/<task_run_id>/limma_output.tsv`

Only after `Rscript` exits with code 0 and the limma output exists does the
adapter call the B25 handoff gate. The handoff gate remains responsible for:

- B19 runtime gate validation;
- limma output schema validation;
- canonical DEG result table conversion;
- result index v2 validation;
- formal result registration.

## Success Result Semantics

A successful run registers:

- `result_semantics=formal_computed_result`
- `engine_name=r_limma_rscript_adapter`
- `engine_version=0.1.0`
- command manifest and command log in `log_artifacts`
- canonical DEG table and method-specific limma table in `output_artifacts`
- `plot_artifacts=[]`
- `report_artifacts=[]`
- `report_ready_eligible=False`

## Failure Behavior

The adapter blocks without writing a result index entry when:

- expression table is missing;
- sample/group mapping does not match expression sample columns;
- case/control group is missing or identical;
- R runtime gate fails;
- `Rscript` is missing;
- `Rscript` times out;
- `Rscript` exits non-zero;
- limma output file is missing;
- B25 handoff validation fails.

Failures still write command manifest/log when execution was attempted so they
can be audited without becoming formal analysis results.

## Explicitly Not Implemented

- No automatic installation of R or Bioconductor packages.
- No bundled R runtime inside `.app`.
- No DESeq2/edgeR execution.
- No GSEA or survival activation.
- No formal plot or report-ready activation.
- No clinical interpretation.

## Validation

Required validation:

```bash
git diff --check
python3 -m py_compile app/bioinformatics/deg_engine/rscript_adapter.py app/bioinformatics/deg_engine/r_backend_handoff.py app/bioinformatics/deg_engine/__init__.py
python3 -m pytest -q tests/bioinformatics/test_r_limma_rscript_adapter.py tests/bioinformatics/test_r_deg_external_handoff.py tests/bioinformatics/test_r_deg_adapter_contract.py
python3 -m pytest tests/bioinformatics -q -k "r_deg or r_limma or multifactor or analysis_ui or formal_deg"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or results_browser"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

Optional local external engine validation can use the system Rscript that passed
B25.1, but CI-style tests use a fake Rscript so they do not require R to be
installed.
