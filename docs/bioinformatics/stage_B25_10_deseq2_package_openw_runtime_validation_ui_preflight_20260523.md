# B25.10 DESeq2 Package/Open-W Runtime Validation + UI Activation Preflight

Date: 2026-05-23

## Scope

B25.10 validates the DESeq2 controlled Rscript runtime across source and packaged
launch paths, and updates Analysis Center state so DESeq2 is no longer described
as missing an adapter. This is still not user-facing DESeq2 activation.

## Implemented

- Added `app/bioinformatics/deg_engine/r_deseq2_runtime_validation.py`.
- Added CLI:
  - `python3 -m app.main --bio-r-deseq2-runtime-check`
  - optional `--bio-r-deseq2-runtime-check-output <path>`
- The runtime validation records:
  - launch mode, git head, Python executable and architecture;
  - Rscript path, R version/platform, BiocManager version and DESeq2 version;
  - package context, bundle size and external-R policy;
  - real controlled count fixture execution;
  - result index v2 registration checks;
  - UI activation preflight with `b25_11_deseq2_ui_activation_required`.

## Runtime Boundary

The validation uses the B25.9 controlled DESeq2 adapter and does not install or
bundle R/Bioconductor/DESeq2. If Rscript or DESeq2 is missing, the check returns
`blocked_missing_dependency` instead of traceback.

When dependencies pass, the controlled fixture must produce:

- `result_semantics=formal_computed_result`;
- `engine_name=r_deseq2_rscript_adapter`;
- numeric `p_value` and `adjusted_p_value`;
- canonical DEG table and DESeq2 method table;
- result index v2 registration;
- `plot_artifacts=[]`;
- `report_artifacts=[]`;
- `report_ready_eligible=False`.

## UI Activation Preflight

Analysis Center now distinguishes:

- DESeq2 controlled adapter/runtime path: available for validation.
- DESeq2 parameter confirmation: still disabled.
- DESeq2 formal run button: still disabled.
- Remaining blocker: `b25_11_deseq2_ui_activation_required`.

The old DESeq2 blockers `deseq2_rscript_execution_adapter_not_implemented` and
`deseq2_result_registration_handoff_not_implemented` are no longer used for the
controlled DESeq2 adapter path. edgeR remains planning-only.

## Not Implemented

- No user-facing DESeq2 execution button.
- No DESeq2 parameter confirmation UI activation.
- No edgeR execution.
- No DESeq2 plot or report-ready output.
- No GSEA/survival/clinical/full integrated report change.
- No automatic R/Bioconductor installation.

## Validation Commands

```bash
git diff --check
python3 -m py_compile app/main.py app/bioinformatics/deg_engine/r_deseq2_runtime_validation.py app/bioinformatics/deg_engine/r_deseq2_runtime.py app/bioinformatics/deg_engine/r_deseq2_planning.py app/bioinformatics/deg_engine/r_count_model_planning.py app/bioinformatics/deg_engine/r_backend_handoff.py app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py app/bioinformatics/analysis_ui/capability_map.py app/bioinformatics/workflow_pages.py app/bioinformatics/deg_engine/__init__.py
python3 -m pytest -q tests/bioinformatics/test_r_deseq2_runtime.py tests/bioinformatics/test_r_deseq2_planning.py tests/bioinformatics/test_r_count_model_planning.py tests/bioinformatics/test_r_deg_external_handoff.py tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py
python3 -m app.main --bio-r-deseq2-runtime-check --bio-r-deseq2-runtime-check-output /tmp/biomedpilot_b25_10_source_deseq2_runtime.json
python3 -m pytest tests/bioinformatics -q -k "deseq2 or r_deg or count_model or analysis_ui or formal_deg"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or results_browser"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
dist/BioMedPilot.app/Contents/MacOS/BioMedPilot --bio-r-deseq2-runtime-check --bio-r-deseq2-runtime-check-output /tmp/biomedpilot_b25_10_packaged_deseq2_runtime.json
open -W -n dist/BioMedPilot.app --args --bio-r-deseq2-runtime-check --bio-r-deseq2-runtime-check-output /tmp/biomedpilot_b25_10_openw_deseq2_runtime.json
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

## Validation Results

- `git diff --check`: passed.
- `py_compile` for app CLI, DESeq2 runtime validation/runtime/planning,
  count-model planning, R handoff, Analysis UI, workflow pages and DEG exports:
  passed.
- Focused B25.10 tests:
  - `test_r_deseq2_runtime.py`
  - `test_r_deseq2_planning.py`
  - `test_r_count_model_planning.py`
  - `test_r_deg_external_handoff.py`
  - `test_analysis_ui_action_rules.py`
  - `test_analysis_ui_state.py`
  - Result: 41 passed.
- Source DESeq2 runtime check:
  - status: passed
  - launch mode: source
  - architecture: arm64
  - Rscript: `/usr/local/bin/Rscript`
  - R: `R version 4.4.2 (2024-10-31)`
  - BiocManager: `1.30.25`
  - DESeq2: `1.46.0`
  - controlled fixture: passed with numeric `p_value` and `adjusted_p_value`
  - UI blocker retained: `b25_11_deseq2_ui_activation_required`
- Selected bioinformatics regression:
  - 81 passed, 612 deselected.
- Focused UI workflow regression:
  - 18 passed, 98 deselected.
- Full `tests/bioinformatics`:
  - 693 passed, 1 existing GEO numeric precision warning.
- Full `tests/ui`:
  - 273 passed.
- Source smoke:
  - passed.
- Package smoke:
  - passed, ad-hoc signed, standalone=false, network_downloads=false.
- Packaged executable DESeq2 runtime check:
  - status: passed
  - launch mode: packaged-local-python
  - architecture: arm64
  - Rscript: `/usr/local/bin/Rscript`
  - R/BiocManager/DESeq2 versions match source
  - bundle size from runtime payload: 32,933,436 bytes
  - `.app` size: 34M
  - `rscript_is_bundled_in_app=false`
  - controlled fixture: passed with numeric `p_value` and `adjusted_p_value`
  - `plot_artifacts=[]`, `report_artifacts=[]`, `report_ready_eligible=False`
- `open -W` DESeq2 runtime check:
  - status: passed
  - launch mode: packaged-local-python
  - architecture: arm64
  - Rscript: `/usr/local/bin/Rscript`
  - controlled fixture: passed with numeric `p_value` and `adjusted_p_value`
  - UI blocker retained: `b25_11_deseq2_ui_activation_required`
- `open -W` smoke:
  - passed.
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`:
  - passed.

## ReleaseBuild Recommendation

ReleaseBuild can treat DESeq2 as runtime/package/open-W validated for controlled
fixtures after these checks pass. The next stage should be B25.11 DESeq2 UI
execution control / user confirmation activation, still gated by resolver,
count-model design preflight, runtime detection, parameter confirmation, result
schema and result index v2.
