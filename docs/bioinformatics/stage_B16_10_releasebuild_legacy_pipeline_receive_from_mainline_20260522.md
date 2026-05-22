# Bioinformatics B16.10 ReleaseBuild Legacy Pipeline Receive From MainLine

Date: 2026-05-22

ReleaseBuild workspace: `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`

ReleaseBuild branch: `codex/releasebuild-formal-deg-carryover`

ReleaseBuild base HEAD: `4f9d8dd`

MainLine source: `7bcdb7f carry over Bioinformatics B16 legacy pipeline to MainLine`

## Goal

Receive the MainLine B16 legacy recognition/acquisition/standardized-asset pipeline into the ReleaseBuild candidate without overwriting ReleaseBuild-only content.

This receive is scoped to B16. It does not publish a release, does not replace the desktop entry point, does not remove ORA/GSEA/survival/clinical content already present in ReleaseBuild, and does not expand formal analysis capability.

## Scoped Files Received

New B16 package:

- `app/bioinformatics/acquisition_adapters/__init__.py`
- `app/bioinformatics/acquisition_adapters/legacy_contract.py`
- `app/bioinformatics/acquisition_adapters/standardized_bridge.py`
- `app/bioinformatics/acquisition_adapters/materialization.py`
- `app/bioinformatics/acquisition_adapters/repository_merge.py`
- `app/bioinformatics/acquisition_adapters/selection_gate.py`

Existing ReleaseBuild files manually merged:

- `app/bioinformatics/analysis_ui/state.py`
- `app/bioinformatics/analysis_ui/action_rules.py`
- `app/bioinformatics/workflow_pages.py`
- `tests/bioinformatics/test_analysis_ui_state.py`
- `tests/bioinformatics/test_analysis_ui_action_rules.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

New B16 tests:

- `tests/bioinformatics/test_legacy_recognition_adapter.py`
- `tests/bioinformatics/test_geo_acquisition_adapter.py`
- `tests/bioinformatics/test_tcga_gtex_adapter_contract.py`
- `tests/bioinformatics/test_legacy_standardized_asset_bridge.py`
- `tests/bioinformatics/test_legacy_candidate_materialization_gate.py`
- `tests/bioinformatics/test_legacy_repository_manifest_merge_gate.py`
- `tests/bioinformatics/test_legacy_asset_selection_gate.py`

New B16 docs from MainLine:

- `docs/bioinformatics/stage_B16_legacy_recognition_acquisition_absorption_20260521.md`
- `docs/bioinformatics/stage_B16_1_legacy_standardized_asset_bridge_20260521.md`
- `docs/bioinformatics/stage_B16_2_legacy_candidate_materialization_gate_20260521.md`
- `docs/bioinformatics/stage_B16_3_legacy_repository_manifest_merge_gate_20260521.md`
- `docs/bioinformatics/stage_B16_4_legacy_asset_selection_validation_gate_20260521.md`
- `docs/bioinformatics/stage_B16_5_legacy_asset_pipeline_ui_exposure_20260521.md`
- `docs/bioinformatics/stage_B16_6_legacy_asset_pipeline_ui_operations_20260522.md`
- `docs/bioinformatics/stage_B16_7_legacy_pipeline_e2e_acceptance_closure_audit_20260522.md`
- `docs/bioinformatics/stage_B16_8_mainline_legacy_pipeline_carryover_preflight_audit_20260522.md`
- `docs/bioinformatics/stage_B16_9_mainline_legacy_pipeline_scoped_carryover_20260522.md`

## ReleaseBuild Preservation Checks

Preserved ReleaseBuild content:

- ORA package, plot, report-ready, and E2E gates.
- GSEA preranked package, plot, report-ready, and E2E gates.
- Formal DEG MVP result, plot, report package gates.
- KM/log-rank and Cox univariate controlled-runtime gates.
- Cox multivariate, risk score, survival report-ready, and clinical association statistics remain disabled/design-only where previously scoped.
- ReleaseBuild package launcher, code signing, app smoke, and LabTools feature count remain intact.
- Untracked `docs/release/ReleaseBuild_handoff_report_20260513.md` remains excluded from this commit.

Manual merge decisions:

- Kept `load_result_index(root, persist_generated=False)` in Analysis Center state rendering.
- Kept ReleaseBuild ORA/GSEA/survival gate rows and added B16 `legacy_asset_pipeline` alongside them.
- Added B16 legacy pipeline operations as controlled preflight/standardization artifact writes only.
- Did not write `analysis_input_repository` from legacy pipeline UI operations.
- Did not write formal result index entries from legacy pipeline UI operations.

## Boundary Confirmation

The ReleaseBuild receive preserves these hard boundaries:

- Legacy acquisition assets are not formal analysis inputs until B8 resolver and downstream task gates pass.
- Legacy pipeline operations do not generate formal DEG/ORA/GSEA/KM/Cox results.
- Legacy pipeline operations do not generate formal plot artifacts or report-ready packages.
- Imported/testing/exploratory/preflight assets are not upgraded to `formal_computed_result`.
- GTEx is not treated as TCGA normal control.
- No GSEA/survival/clinical capability is newly enabled by B16.

## Validation Commands

All commands were run in `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`.

| Command | Result |
| --- | --- |
| `git diff --check` | passed |
| `python3 -m py_compile app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py app/bioinformatics/workflow_pages.py` | passed |
| `python3 -m pytest tests/bioinformatics/test_legacy_recognition_adapter.py tests/bioinformatics/test_geo_acquisition_adapter.py tests/bioinformatics/test_tcga_gtex_adapter_contract.py tests/bioinformatics/test_legacy_standardized_asset_bridge.py tests/bioinformatics/test_legacy_candidate_materialization_gate.py tests/bioinformatics/test_legacy_repository_manifest_merge_gate.py tests/bioinformatics/test_legacy_asset_selection_gate.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py -q` | 43 passed |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "legacy_pipeline_operations or userized_main_surface"` | 2 passed, 110 deselected |
| `python3 -m pytest tests/bioinformatics -q -k "legacy or adapter or geo or tcga or gtex or recognition or standardization or resolver or analysis_ui"` | 271 passed, 321 deselected |
| `python3 -m pytest tests/bioinformatics -q -k "formal_deg or ora or gsea or survival or clinical or cox or km or analysis_ui"` | 211 passed, 381 deselected |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or legacy or survival or clinical or results_browser or ora or gsea"` | 17 passed, 95 deselected |
| `python3 -m pytest tests/bioinformatics -q` | 592 passed |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | 269 passed |
| `python3 -m app.main --smoke-test` | passed |
| `python3 scripts/package_app.py --smoke-test` | passed |
| `open -W -n dist/BioMedPilot.app --args --smoke-test` | passed |
| `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app` | passed |

## Issues

Blocker:

- None.

Major:

- None after scoped receive.

Minor:

- Legacy asset selection still auto-confirms only unambiguous candidate roles. Manual multi-candidate picker remains future UI work.
- B16 legacy pipeline is visible as preflight/standardization review only; product copy must continue to avoid presenting it as formal analysis readiness.

## Final Conclusion

完全通过.

ReleaseBuild can retain this candidate snapshot with B16 legacy pipeline received from MainLine `7bcdb7f`. The receive is scoped, ReleaseBuild-only ORA/GSEA/survival/clinical content remains intact, and packaging/open-W/codesign gates pass.

## Next Recommendation

Keep the current ReleaseBuild branch as the candidate snapshot. The next development stage should be planned separately and should not use whole-tree carry-over unless a new preflight audit confirms that ReleaseBuild-only content will be preserved.
