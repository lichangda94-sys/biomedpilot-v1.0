# Meta Analysis Result Contract Unification Report

Date: 2026-05-29

## Scope

Phase 3 only: unify the Meta Analysis result contract around one current statistics v2 run. This phase did not work on Bioinformatics, did not redesign the Meta UI, did not create a generic Analysis Runner, and did not claim Meta L3.

## Implemented Bridge

Added `MetaResultContractAdapter` as a narrow adapter from the existing Meta statistics v2 result:

- Canonical source: `analysis/results/{analysis_run_id}_result.json`
- Canonical run manifest: `analysis/runs/{analysis_run_id}.json`
- Canonical contract: `analysis/meta_result_contracts/{analysis_run_id}/meta_result_contract.json`
- Result table artifact: `analysis/meta_result_contracts/{analysis_run_id}/tables/meta_result_table.csv`
- Forest plot artifact: `analysis/meta_result_contracts/{analysis_run_id}/figures/forest_plot_{analysis_run_id}.png`
- Report/export artifact: `analysis/meta_result_contracts/{analysis_run_id}/reports/meta_result_export_{analysis_run_id}.md`

Each artifact carries:

- `source_analysis_run_id`
- `source_statistics_result_path`
- `source_statistics_result_hash`
- `testing_level=true`
- `production_grade=false`
- `medical_conclusion_status=not_generated`

## Proof

| Required proof | Result |
| --- | --- |
| One real v2 statistics run has canonical manifest | Passed. Focused test runs `MetaStatisticsEngineService.run_statistics()` and writes a canonical contract for the real run. |
| Forest plot artifact comes from same run_id | Passed. Forest plot artifact is generated from the v2 standardized result and carries the same `source_analysis_run_id`. |
| Result table artifact comes from same run_id | Passed. Result table is generated from the v2 standardized result and carries the same `source_analysis_run_id`. |
| Report/export artifact comes from same run_id or formal gate block | Passed. A testing-level markdown export is generated from the same v2 run and carries the same source hash. |
| Artifacts preserve `source_statistics_result_hash` | Passed. All three artifact entries preserve the hash of `analysis/results/{run_id}_result.json`. |
| Current Meta UI handlers can discover canonical run/artifact list | Passed. `meta_statistics_engine_state_from_project()` now exposes `canonical_contract_path`, `canonical_statistics_result_hash`, `canonical_artifact_count`, and `canonical_artifacts`. |

## Boundaries Preserved

- No Bioinformatics code was modified.
- No Meta statistics computation was rewritten.
- No legacy branch was merged.
- No placeholder report or mock plot was promoted as real output.
- No clinical or production-grade output was claimed.
- Meta Analysis is still not claimed L3; Phase 4 is still required for full current-UI L3 proof.

## Validation Commands

| Command | Result |
| --- | --- |
| `python3 -m pytest tests/meta_analysis/test_meta_result_contract_adapter.py -q` | Passed, `2 passed` |
| `python3 -m pytest tests/meta_analysis/test_meta_statistics_engine_v2.py -q` | Passed, `6 passed` |
| `python3 -m pytest tests/meta_analysis/test_analysis_core_mvp.py tests/meta_analysis/test_figure_result_table_mvp.py tests/meta_analysis/test_publication_export_reproducibility.py -q` | Passed, `15 passed` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_meta_analysis_workflow_pages.py -q` | Passed, `21 passed` |
| `python3 -m app.main --smoke-test` | Passed, `git_head=8036e50` |
| `git diff --check` | Passed |

## Remaining Phase 4 Work

Meta Analysis still needs a full current UI L3 proof before it can be claimed as a closed loop. This Phase 3 bridge proves the canonical contract and artifact provenance only.

