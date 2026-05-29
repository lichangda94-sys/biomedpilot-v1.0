# Meta Analysis Result Contract Map

Date: 2026-05-29

## Scope

This Phase 3 audit covers only the Meta Analysis result contract. Bioinformatics is out of scope because the controlled formal DEG single-point L3 proof was completed separately.

The objective is not to claim Meta L3. The objective is to map whether one real Meta statistics run can become the canonical source for the result table, forest plot, and report/export artifact.

## Reference Availability

Read locally:

- `CODEX_UI_BRANCH_MIGRATION_GUIDE.md`
- `CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md`
- `/Users/changdali/Desktop/SOFTWARE_REMEDIATION_PLAN_UI_AND_ANALYSIS_L3.md`

Not found in the current local workspace or Desktop search path:

- `CODEX_L3_MODULE_LINE_CLOSURE_PLAN.md`
- `CODEX_PHASE2_BIOINFORMATICS_L3_CONTROLLED_DEG_CLOSURE.md`
- `CODEX_PHASE3_META_RESULT_CONTRACT_UNIFICATION.md`

The missing files were treated as unavailable local references. The user-provided Phase 3 instructions define the active boundary.

## Current Contract Split

| Surface | Current source | Current output | Contract status |
| --- | --- | --- | --- |
| Statistics v2 | `MetaStatisticsEngineService.run_statistics()` | `analysis/runs/{run_id}.json`, `analysis/results/{run_id}_result.json`, `analysis/analysis_manifest.json` | Canonical statistics run exists. |
| Result table | `FigureResultService.export_result_table_csv()` | `exports/analysis_result_table_{result_id}.csv` | Reads legacy `analysis/analysis_results.json`, not v2 result. |
| Forest plot | `FigureResultService.generate_forest_plot()` | `figures/forest_plot_{result_id}.png` | Reads legacy `analysis/analysis_results.json`, not v2 result. |
| Publication export | `PublicationExportService` | HTML/DOCX/zip from `reports/formal_meta_report.md` and loose artifacts | Does not require v2 `analysis_run_id` or statistics result hash. |
| UI state | `meta_statistics_engine_state_from_project()` | Latest v2 run/result status | Does not expose canonical artifact list yet. |

## Canonical Source

The canonical source for Phase 3 is the v2 statistics result:

- Run ID: `analysis_run_id`
- Run manifest: `analysis/runs/{analysis_run_id}.json`
- Standardized result: `analysis/results/{analysis_run_id}_result.json`
- Statistics result hash: SHA-256 over the standardized result file bytes

All bridged artifacts must carry:

- `source_analysis_run_id`
- `source_statistics_result_path`
- `source_statistics_result_hash`
- `testing_level=true`
- `production_grade=false`
- `medical_conclusion_status=not_generated`

## Narrow Bridge Design

Add a Meta result contract adapter that only reads v2 statistics output and writes derived artifacts under:

```text
analysis/meta_result_contracts/{run_id}/
  meta_result_contract.json
  tables/meta_result_table.csv
  figures/forest_plot_{run_id}.png
  reports/meta_result_export_{run_id}.md
```

The adapter is intentionally narrow:

- It does not create a generic Analysis Runner.
- It does not redesign Meta UI.
- It does not rewrite statistics.
- It does not promote placeholder reports or mock plots.
- It does not claim clinical, production-grade, or Meta L3 output.

## Required Phase 3 Proof

| Proof item | Planned bridge evidence |
| --- | --- |
| One real v2 statistics run has canonical manifest | `meta_result_contract.json` points to `analysis/runs/{run_id}.json` and `analysis/results/{run_id}_result.json`. |
| Forest plot artifact comes from same run | Forest artifact manifest entry carries `source_analysis_run_id={run_id}` and `source_statistics_result_hash`. |
| Result table artifact comes from same run | Table artifact manifest entry carries `source_analysis_run_id={run_id}` and `source_statistics_result_hash`. |
| Report/export artifact comes from same run or blocked | Testing-level markdown export carries same run/hash; no final clinical report is generated. |
| Artifacts preserve source hash | Each artifact entry includes `source_statistics_result_hash`. |
| Current UI handlers can discover contract | `meta_statistics_engine_state_from_project()` exposes canonical contract path and artifact list if present. |

## Blockers Before Bridge

No safety blocker prevents a narrow bridge. The blocker is architectural rather than statistical: current table/plot/export paths are split from v2 statistics output. A read-only v2 adapter can close this without changing statistical computation or replacing UI.

