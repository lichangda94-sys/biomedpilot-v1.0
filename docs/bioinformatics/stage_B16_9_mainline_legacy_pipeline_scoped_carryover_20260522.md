# Bioinformatics B16.9 MainLine Legacy Pipeline Scoped Carry-over Execution

Date: 2026-05-22

Target workspace: `/Users/changdali/Developer/biomedpilot v1.0/MainLine`

Target branch: `codex/mainline-survival-clinical-carryover`

Target base HEAD: `6779f3e carry over Bioinformatics survival clinical MVP to MainLine`

Source workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Source branch: `dev/bioinformatics`

Source HEAD: `70f93df docs(bio): audit MainLine legacy pipeline carry-over preflight`

## Goal

Carry B16 legacy recognition/acquisition/standardized-asset pipeline contracts from `dev/bioinformatics` into the MainLine survival/clinical convergence branch without overwriting existing MainLine B8-B14 analysis contracts.

This stage is scoped carry-over only. It does not enable formal analysis from legacy assets, does not write `analysis_input_repository`, does not write formal result index entries, and does not activate GSEA, survival report-ready, clinical conclusion, or legacy runner execution.

## Files Carried

New B16 package:

- `app/bioinformatics/acquisition_adapters/__init__.py`
- `app/bioinformatics/acquisition_adapters/legacy_contract.py`
- `app/bioinformatics/acquisition_adapters/standardized_bridge.py`
- `app/bioinformatics/acquisition_adapters/materialization.py`
- `app/bioinformatics/acquisition_adapters/repository_merge.py`
- `app/bioinformatics/acquisition_adapters/selection_gate.py`

New B16 tests:

- `tests/bioinformatics/test_legacy_recognition_adapter.py`
- `tests/bioinformatics/test_geo_acquisition_adapter.py`
- `tests/bioinformatics/test_tcga_gtex_adapter_contract.py`
- `tests/bioinformatics/test_legacy_standardized_asset_bridge.py`
- `tests/bioinformatics/test_legacy_candidate_materialization_gate.py`
- `tests/bioinformatics/test_legacy_repository_manifest_merge_gate.py`
- `tests/bioinformatics/test_legacy_asset_selection_gate.py`

B16 documentation:

- `docs/bioinformatics/stage_B16_legacy_recognition_acquisition_absorption_20260521.md`
- `docs/bioinformatics/stage_B16_1_legacy_standardized_asset_bridge_20260521.md`
- `docs/bioinformatics/stage_B16_2_legacy_candidate_materialization_gate_20260521.md`
- `docs/bioinformatics/stage_B16_3_legacy_repository_manifest_merge_gate_20260521.md`
- `docs/bioinformatics/stage_B16_4_legacy_asset_selection_validation_gate_20260521.md`
- `docs/bioinformatics/stage_B16_5_legacy_asset_pipeline_ui_exposure_20260521.md`
- `docs/bioinformatics/stage_B16_6_legacy_asset_pipeline_ui_operations_20260522.md`
- `docs/bioinformatics/stage_B16_7_legacy_pipeline_e2e_acceptance_closure_audit_20260522.md`
- `docs/bioinformatics/stage_B16_8_mainline_legacy_pipeline_carryover_preflight_audit_20260522.md`

## Scoped Merge Decisions

Manually merged B16 changes into these existing MainLine files:

- `app/bioinformatics/analysis_ui/state.py`
- `app/bioinformatics/analysis_ui/action_rules.py`
- `app/bioinformatics/workflow_pages.py`
- `tests/bioinformatics/test_analysis_ui_state.py`
- `tests/bioinformatics/test_analysis_ui_action_rules.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

Preserved MainLine behavior:

- `load_result_index(root, persist_generated=False)` remains in the Analysis Center state builder to avoid generated result-index side effects during state rendering.
- Existing `count_matrix` recognition/standardization compatibility remains intact.
- B9 formal DEG gates remain controlled by resolver, DEG-ready, dependency, parameter, confirmation, result schema, and activation gates.
- B10/B11 ORA/GSEA result semantics and report boundaries remain unchanged.
- B12-B14 KM/log-rank and Cox controlled-runtime gates remain separate from B16 legacy asset pipeline state.
- Survival/clinical report-ready remains disabled.

Added MainLine behavior:

- Analysis Center now exposes `legacy_asset_pipeline` state from B16 contracts.
- Legacy pipeline actions are review/preflight operations only:
  - build legacy asset candidates
  - materialize standardized asset candidates
  - merge candidate assets into repository manifest
  - confirm legacy asset selection
- UI shows legacy pipeline blockers/warnings and disabled reasons.
- UI operations make candidate/repository/selection manifests visible without presenting them as formal analysis inputs or formal results.

## Boundary Confirmation

The carry-over preserves these hard boundaries:

- No legacy acquisition output is promoted directly to `analysis_input_repository`.
- No legacy pipeline operation writes formal result index entries.
- No legacy operation generates formal DEG/ORA/GSEA/KM/Cox outputs.
- No formal plot or report-ready package is created by legacy pipeline operations.
- GTEx is not treated as TCGA normal control.
- Imported/testing/exploratory/preflight assets are not upgraded to `formal_computed_result`.

## Validation Commands

All commands were run in `/Users/changdali/Developer/biomedpilot v1.0/MainLine`.

| Command | Result |
| --- | --- |
| `git diff --check` | passed |
| `python3 -m py_compile app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py app/bioinformatics/workflow_pages.py` | passed |
| `python3 -m pytest tests/bioinformatics/test_legacy_recognition_adapter.py tests/bioinformatics/test_geo_acquisition_adapter.py tests/bioinformatics/test_tcga_gtex_adapter_contract.py tests/bioinformatics/test_legacy_standardized_asset_bridge.py tests/bioinformatics/test_legacy_candidate_materialization_gate.py tests/bioinformatics/test_legacy_repository_manifest_merge_gate.py tests/bioinformatics/test_legacy_asset_selection_gate.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py -q` | 38 passed |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "legacy_pipeline_operations or userized_main_surface"` | 2 passed, 108 deselected |
| `python3 -m pytest tests/bioinformatics -q -k "legacy or adapter or geo or tcga or gtex or recognition or standardization or resolver or analysis_ui"` | 265 passed, 215 deselected |
| `python3 -m pytest tests/bioinformatics -q -k "formal_deg or ora or gsea or survival or clinical or cox or km or analysis_ui"` | 108 passed, 372 deselected |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or legacy or survival or clinical or results_browser"` | 14 passed, 96 deselected |
| `python3 -m pytest tests/bioinformatics -q` | 480 passed |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | 198 passed |
| `python3 -m app.main --smoke-test` | passed |
| `python3 scripts/package_app.py --smoke-test` | passed |
| `open -W -n dist/BioMedPilot.app --args --smoke-test` | passed |
| `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app` | passed |

## Issues

Blocker:

- None.

Major:

- None after scoped merge.

Minor:

- Legacy asset selection remains auto-confirmed only for unambiguous candidate roles. Multi-candidate/manual picker UX remains future work.
- The legacy pipeline UI is intentionally preflight/review oriented and should not be presented as formal analysis readiness.

## Final Conclusion

完全通过.

B16 legacy recognition/acquisition/standardized-asset pipeline has been carried into the MainLine survival/clinical convergence branch with scoped manual merge. MainLine B8-B14 formal analysis boundaries remain intact.

## ReleaseBuild Recommendation

Recommend entering ReleaseBuild receive preflight for this MainLine snapshot. ReleaseBuild should receive the MainLine scoped result, not the Bioinformatics source tree directly, and should preserve any ReleaseBuild-specific B12/B14 files and package-launch gates.
