# Bioinformatics B16.8 MainLine Legacy Pipeline Carry-over Preflight Audit

Date: 2026-05-22

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Source branch: `dev/bioinformatics`

Source HEAD: `e50f935 docs(bio): close B16 legacy pipeline audit`

## Audit Goal

Assess whether the closed B16 legacy acquisition/standardization pipeline can be carried to MainLine without overwriting existing MainLine B8-B14 contracts.

This is a preflight audit only. No MainLine checkout was modified, no source tree was overwritten, and no ReleaseBuild receive was attempted.

## Candidate MainLine Targets

| Target | HEAD | Assessment |
| --- | --- | --- |
| `stable/mainline` | `be8c924 carry over Bioinformatics formal DEG MVP to MainLine` | Not recommended as direct B16 target. It has B8/B9 formal DEG baseline, but does not contain the later survival/clinical convergence branch state. |
| `codex/mainline-survival-clinical-carryover` | `6779f3e carry over Bioinformatics survival clinical MVP to MainLine` | Recommended B16 receive target. It contains the survival/clinical MainLine convergence and is the correct base for avoiding B12-B14 regression. |

Merge base for recommended target:

- `git merge-base codex/mainline-survival-clinical-carryover HEAD` -> `2d8b263`

## B16 Carry-over File Coverage

New B16 modules to carry:

- `app/bioinformatics/acquisition_adapters/__init__.py`
- `app/bioinformatics/acquisition_adapters/legacy_contract.py`
- `app/bioinformatics/acquisition_adapters/standardized_bridge.py`
- `app/bioinformatics/acquisition_adapters/materialization.py`
- `app/bioinformatics/acquisition_adapters/repository_merge.py`
- `app/bioinformatics/acquisition_adapters/selection_gate.py`

Existing MainLine files requiring scoped merge:

- `app/bioinformatics/analysis_ui/action_rules.py`
- `app/bioinformatics/analysis_ui/state.py`
- `app/bioinformatics/workflow_pages.py`
- `tests/bioinformatics/test_analysis_ui_action_rules.py`
- `tests/bioinformatics/test_analysis_ui_state.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

New B16 tests to carry:

- `tests/bioinformatics/test_legacy_recognition_adapter.py`
- `tests/bioinformatics/test_geo_acquisition_adapter.py`
- `tests/bioinformatics/test_tcga_gtex_adapter_contract.py`
- `tests/bioinformatics/test_legacy_standardized_asset_bridge.py`
- `tests/bioinformatics/test_legacy_candidate_materialization_gate.py`
- `tests/bioinformatics/test_legacy_repository_manifest_merge_gate.py`
- `tests/bioinformatics/test_legacy_asset_selection_gate.py`

New B16 docs to carry:

- `docs/bioinformatics/stage_B16_legacy_recognition_acquisition_absorption_20260521.md`
- `docs/bioinformatics/stage_B16_1_legacy_standardized_asset_bridge_20260521.md`
- `docs/bioinformatics/stage_B16_2_legacy_candidate_materialization_gate_20260521.md`
- `docs/bioinformatics/stage_B16_3_legacy_repository_manifest_merge_gate_20260521.md`
- `docs/bioinformatics/stage_B16_4_legacy_asset_selection_validation_gate_20260521.md`
- `docs/bioinformatics/stage_B16_5_legacy_asset_pipeline_ui_exposure_20260521.md`
- `docs/bioinformatics/stage_B16_6_legacy_asset_pipeline_ui_operations_20260522.md`
- `docs/bioinformatics/stage_B16_7_legacy_pipeline_e2e_acceptance_closure_audit_20260522.md`

## Merge Risk

`git merge-tree` against `codex/mainline-survival-clinical-carryover` reports same-file changes in:

- `app/bioinformatics/analysis_ui/action_rules.py`
- `app/bioinformatics/analysis_ui/state.py`
- `app/bioinformatics/workflow_pages.py`
- `tests/bioinformatics/test_analysis_ui_action_rules.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

These conflicts are expected because B12-B14 survival/clinical carry-over and B16 both extend Analysis Center state/action/UI. They must be resolved by merging the B16 legacy rows and operations into the existing MainLine survival/clinical rows, not by taking either side wholesale.

## Boundary Requirements For Carry-over

The carry-over must preserve:

- B8 resolver source policy: standardized repository / registry / analysis_input_repository only.
- B9 formal DEG dependency, parameter, confirmation and result schema gates.
- B10/B11 enrichment gates if present in the target branch.
- B12-B14 KM/Cox/survival/clinical gates in `codex/mainline-survival-clinical-carryover`.
- B16 legacy pipeline as acquisition/standardization only.
- No legacy action writes `analysis_input_repository`.
- No legacy action writes `result_index`.
- No legacy action generates formal DEG/ORA/GSEA/KM/Cox/plot/report-ready outputs.
- GTEx must not be treated as TCGA normal control.

## Recommended Carry-over Strategy

Recommendation: scoped carry-over to `codex/mainline-survival-clinical-carryover`, not direct carry-over to `stable/mainline`.

Use a manual scoped merge:

1. Start from the MainLine survival/clinical convergence branch.
2. Add the new `app/bioinformatics/acquisition_adapters/` package from `dev/bioinformatics`.
3. Add B16 tests and docs.
4. Manually merge Analysis Center state/action/UI changes:
   - add `legacy_asset_pipeline` state without removing survival/clinical rows.
   - add legacy action rows without changing formal DEG/KM/Cox/report gates.
   - add legacy UI table/buttons without removing existing result/report/survival panels.
5. Run B16 targeted tests, survival/clinical targeted tests, enrichment/formal DEG targeted tests, full bio/UI tests, and smoke/package gates.

Do not use source tree replacement for `app/bioinformatics` or `tests/ui/test_bioinformatics_workflow_pages.py`.

## Validation Commands Run In Source Branch

- `git diff --check` -> passed.
- `git diff --check codex/mainline-survival-clinical-carryover..HEAD -- app/bioinformatics/acquisition_adapters app/bioinformatics/analysis_ui app/bioinformatics/workflow_pages.py tests/bioinformatics tests/ui/test_bioinformatics_workflow_pages.py docs/bioinformatics` -> passed.
- `python3 -m pytest tests/bioinformatics/test_legacy_recognition_adapter.py tests/bioinformatics/test_geo_acquisition_adapter.py tests/bioinformatics/test_tcga_gtex_adapter_contract.py tests/bioinformatics/test_legacy_standardized_asset_bridge.py tests/bioinformatics/test_legacy_candidate_materialization_gate.py tests/bioinformatics/test_legacy_repository_manifest_merge_gate.py tests/bioinformatics/test_legacy_asset_selection_gate.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py -q` -> 38 passed.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "legacy_pipeline_operations or userized_main_surface"` -> 2 passed, 108 deselected.

B16.7 full validation remains the latest full source/package evidence:

- `python3 -m pytest tests/bioinformatics -q` -> 433 passed.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` -> 177 passed.
- `python3 -m app.main --smoke-test` -> passed.
- `python3 scripts/package_app.py --smoke-test` -> passed.
- `open -W -n dist/BioMedPilot.app --args --smoke-test` -> passed.
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app` -> passed.

## Issues

Blocker:

- None for planning.

Major:

- Direct carry-over to `stable/mainline` is not recommended because it would skip the survival/clinical convergence branch.
- Automated merge will conflict in Analysis Center state/action/UI files. Manual scoped merge is required.

Minor:

- B16 asset selection UI auto-confirms only unambiguous single-role assets. Multi-candidate selection still needs a future manual picker.
- B16 docs should be carried as audit context, but they should not be used as proof that MainLine execution has already passed until tests are run on the target branch.

## Final Conclusion

条件通过.

B16 is ready for scoped MainLine carry-over into `codex/mainline-survival-clinical-carryover`, with manual conflict resolution in Analysis Center files. It is not ready for direct fast-forward or whole-tree replacement into `stable/mainline`.

## Next Commands Suggested

From the MainLine survival/clinical worktree:

```bash
git status
git branch --show-current
git rev-parse --short HEAD
git checkout codex/mainline-survival-clinical-carryover
git checkout dev/bioinformatics -- app/bioinformatics/acquisition_adapters tests/bioinformatics/test_legacy_recognition_adapter.py tests/bioinformatics/test_geo_acquisition_adapter.py tests/bioinformatics/test_tcga_gtex_adapter_contract.py tests/bioinformatics/test_legacy_standardized_asset_bridge.py tests/bioinformatics/test_legacy_candidate_materialization_gate.py tests/bioinformatics/test_legacy_repository_manifest_merge_gate.py tests/bioinformatics/test_legacy_asset_selection_gate.py docs/bioinformatics/stage_B16_legacy_recognition_acquisition_absorption_20260521.md docs/bioinformatics/stage_B16_1_legacy_standardized_asset_bridge_20260521.md docs/bioinformatics/stage_B16_2_legacy_candidate_materialization_gate_20260521.md docs/bioinformatics/stage_B16_3_legacy_repository_manifest_merge_gate_20260521.md docs/bioinformatics/stage_B16_4_legacy_asset_selection_validation_gate_20260521.md docs/bioinformatics/stage_B16_5_legacy_asset_pipeline_ui_exposure_20260521.md docs/bioinformatics/stage_B16_6_legacy_asset_pipeline_ui_operations_20260522.md docs/bioinformatics/stage_B16_7_legacy_pipeline_e2e_acceptance_closure_audit_20260522.md
```

Then manually merge these files from `dev/bioinformatics`:

- `app/bioinformatics/analysis_ui/action_rules.py`
- `app/bioinformatics/analysis_ui/state.py`
- `app/bioinformatics/workflow_pages.py`
- `tests/bioinformatics/test_analysis_ui_action_rules.py`
- `tests/bioinformatics/test_analysis_ui_state.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

Required post-merge checks:

```bash
git diff --check
python3 -m pytest tests/bioinformatics -q -k "legacy or adapter or geo or tcga or gtex or recognition or standardization or resolver or analysis_ui"
python3 -m pytest tests/bioinformatics -q -k "formal_deg or ora or gsea or survival or clinical or cox or km or analysis_ui"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or legacy or survival or clinical or results_browser"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```
