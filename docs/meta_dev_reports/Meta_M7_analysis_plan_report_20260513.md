# Meta M7 Analysis Plan Report - 2026-05-13

## Stage name

Meta M7 - Confirmed Analysis Plan Workspace

## Branch

`dev/meta-analysis`

## HEAD before work

`86bc02a` (`feat(meta): add quality assessment workspace`)

## Files changed

- `app/meta_analysis/services/analysis_plan_service.py`
- `app/meta_analysis/pages/analysis_page.py`
- `app/meta_analysis/workspace.py`
- `tests/meta_analysis/test_analysis_plan_builder_v1.py`
- `tests/meta_analysis/test_meta_workspace_ui_navigation.py`
- `docs/meta_dev_reports/Meta_M7_analysis_plan_report_20260513.md`

## User-facing behavior

- The workflow route for `statistics_analysis` now opens a Chinese-first analysis plan confirmation workspace instead of exposing the testing statistics executor as the normal next step.
- The page shows the required M7 labels: 分析计划, 研究类型, 效应量类型, 固定效应, 随机效应, 异质性, 亚组分析, 敏感性分析, 发表偏倚, 纳入研究数量, 确认分析计划, 下一步：结果与报告.
- Users can generate a draft, edit plan fields, choose effect measure type and model preference, and confirm the analysis plan.
- Main UI text avoids raw JSON, manifest paths, local paths, and internal IDs. File paths remain only in collapsed developer diagnostics.
- The page states that the plan is Developer Preview / testing and does not represent formal statistical conclusions.

## Developer-facing behavior

- Existing `analysis_plan_draft_v1.json`, `analysis_plan_confirmed_v1.json`, and `analysis_plan_manifest_v1.json` remain the persistence path.
- M7 fields were added inside the existing analysis plan artifacts for compatibility: `m7_schema_version`, PICO plan fields, `model_preference`, `effect_measure_type`, `heterogeneity_metrics`, `included_study_ids`, `included_study_refs`, `plan_state`, readiness warnings, and future-executor eligibility.
- Added M7 plan states: `draft`, `suggested`, `user_edited`, `confirmed`, `needs_revision`.
- Added readiness checks for confirmed extraction rows, study count, missing or mixed effect measures, missing CI/SE or insufficient fields, and incomplete M6 quality assessment.
- Suggested plans are not eligible for future statistical execution; only `plan_state == confirmed` is eligible for a future validated executor path.
- Existing testing statistics service code was not modified and no formal statistical computation was added.

## Validation commands and exact results

```bash
git diff --check
```

Result: passed with no output.

```bash
python3 -m pytest tests/meta_analysis -q
```

Result: `481 passed in 5.36s`

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

Result: `154 passed in 11.54s`

```bash
QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
```

Result:

```text
BioMedPilot / 医研智析
app_version=0.1.0-internal-beta
app_channel=Developer Preview / testing
launch_mode=source
app_root=/Users/changdali/Developer/biomedpilot v1.0/Meta
git_head=86bc02a
workspace_entries=2
bioinformatics_features=5
meta_analysis_features=7
pyside6_available=True
```

Focused checks also passed:

- `python3 -m pytest tests/meta_analysis/test_analysis_plan_builder_v1.py -q` -> `8 passed in 0.29s`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis/test_meta_workspace_ui_navigation.py -q` -> `12 passed in 1.47s`
- `python3 -m pytest tests/meta_analysis/test_meta_statistics_engine_v2.py -q` -> `6 passed in 0.40s`

## Limitations

- M7 does not run pooled effects, forest plots, funnel plots, or any formal statistical meta-analysis.
- Readiness findings are warnings for user review, not formal blockers, unless a future validated executor explicitly enforces them.
- Confirmed analysis plans only mark a future executor path as eligible; they are not publication-, clinical-, regulatory-, or submission-ready outputs.
- Quality completeness depends on M6 records and confirmed extraction study IDs available in the current project state.

## Remaining untracked / dirty files

Before commit, the expected untracked input artifact remains:

- `docs/meta_dev_reports/Meta_handoff_report_20260513.md`

The M7 report and implementation files are stage-owned and intended for the M7 commit.

## Commit status

Commit planned after final diff check with message:

`feat(meta): add analysis plan confirmation workspace`

No remote push performed.
