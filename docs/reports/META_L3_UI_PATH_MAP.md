# Meta Analysis L3 UI Path Map

Date: 2026-05-29

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Branch: `feature/meta-l3-ui-loop`

Base mainline HEAD: `7cd526ad8b2cdc0c3dccab3e95dc1a2b75747b40`

## Scope

This Phase 4 map covers one current Meta Analysis UI single-point L3 loop only:

```text
Current Meta UI
-> confirmed analysis plan
-> v2 statistics run
-> canonical contract
-> result table artifact
-> forest plot artifact
-> report/export artifact
```

This phase does not modify Bioinformatics, does not create a generic analysis runner, does not redesign Meta UI, does not rewrite Meta statistics, and does not merge, cherry-pick, or migrate old branches, legacy workbench code, OCR, or fulltext.

## Current UI Handler Path

| Step | Current UI element / handler | Current service boundary | Output evidence |
| --- | --- | --- | --- |
| Select project | `AnalysisPage._project_dir_input` | Existing project directory input on current Analysis page | Project root used by all later UI handlers |
| Generate analysis plan draft | Button `生成分析计划草稿` -> `AnalysisPage._build_analysis_plan_draft()` | `AnalysisPlanService.generate_draft()` | `analysis/analysis_plan_draft_v1.json` |
| Confirm analysis plan | Button `确认分析计划` -> `AnalysisPage._confirm_analysis_plan()` | `AnalysisPlanService.confirm_plan()` | `analysis/analysis_plan_confirmed_v1.json`, `locked_for_analysis_run=true` |
| Run v2 statistics | Button `运行统计分析` -> `AnalysisPage._run_statistics_v2()` | `MetaStatisticsEngineService.run_statistics()` | `analysis/runs/{analysis_run_id}.json`, `analysis/results/{analysis_run_id}_result.json` |
| Discover latest v2 state | `meta_statistics_engine_state_from_project()` | Current statistics manifest and Phase 3 contract discovery | latest run id, result path, input validation, canonical artifact fields |
| Generate canonical artifacts | Button `生成 canonical result artifacts` -> `AnalysisPage.generate_meta_result_contract_artifacts()` | `MetaResultContractAdapter` bound to the same current `MetaStatisticsEngineService` | canonical contract, result table CSV, forest plot PNG, testing-level report/export markdown |
| Rediscover canonical artifacts | `meta_statistics_engine_state_from_project()` after artifact generation | Current canonical contract discovery | `canonical_contract_path`, `canonical_statistics_result_hash`, `canonical_artifact_count=3`, artifact list |

## Artifact Contract Path

For the UI-created `analysis_run_id`, Phase 4 uses the existing Phase 3 canonical contract locations:

| Artifact | Path pattern | Required provenance |
| --- | --- | --- |
| Canonical contract | `analysis/meta_result_contracts/{analysis_run_id}/meta_result_contract.json` | `analysis_run_id`, `source_statistics_result_hash`, `testing_level=true`, `production_grade=false` |
| Result table | `analysis/meta_result_contracts/{analysis_run_id}/tables/meta_result_table.csv` | `source_analysis_run_id={analysis_run_id}`, same `source_statistics_result_hash` |
| Forest plot | `analysis/meta_result_contracts/{analysis_run_id}/figures/forest_plot_{analysis_run_id}.png` | Real PNG from standardized v2 result, same run/hash |
| Report/export | `analysis/meta_result_contracts/{analysis_run_id}/reports/meta_result_export_{analysis_run_id}.md` | Markdown developer-preview/testing-level export, same run/hash |

The report/export artifact remains testing-level developer preview. It is not a formal medical conclusion, not clinical guidance, not diagnostic, not treatment guidance, and not production-grade output.

## UI L3 Test Path

Focused proof file:

```text
tests/ui/test_meta_analysis_l3_loop.py
```

The test drives the current UI handlers by clicking:

```text
生成分析计划草稿
确认分析计划
运行统计分析
生成 canonical result artifacts
```

The test then verifies:

- the analysis plan was confirmed by the current UI path;
- the v2 statistics run was triggered by the current UI path;
- the canonical contract is discovered by current UI state;
- result table, forest plot, and report/export artifacts exist;
- all artifacts carry the same `source_analysis_run_id`;
- all artifacts carry the same `source_statistics_result_hash`;
- the forest plot is a real PNG artifact;
- the report/export is labeled Developer Preview / testing-level;
- no `analysis/analysis_results.json` old split-result path is used as completion evidence.

## Explicit Non-Evidence

The following are not counted as Phase 4 UI L3 proof:

| Non-evidence | Reason |
| --- | --- |
| Service-only `MetaStatisticsEngineService.run_statistics()` tests | Useful regression coverage, but not UI L3 proof by itself |
| Service-only `MetaResultContractAdapter` tests | Useful contract coverage, but not UI L3 proof by itself |
| Legacy Meta workbench pages | Deprecated runtime source |
| OCR/fulltext branch history | Not part of this current UI single-point proof |
| Mock plots, placeholder reports, dry-run/no-op runners | Forbidden as completion evidence |
| Testing report/export text alone | Must be tied to same `analysis_run_id` and source hash to count |

## Result

The current Meta Analysis UI has one focused L3 proof path for v2 statistics result contract closure. The claim is limited to this single path and remains developer-preview/testing-level.
