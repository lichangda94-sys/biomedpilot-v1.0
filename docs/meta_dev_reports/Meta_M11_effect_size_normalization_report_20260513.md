# Meta M11 Effect Size Normalization Report

## Stage

Meta M11 — Effect Size Normalization Service

## Branch

`dev/meta-analysis`

## HEAD Before Work

`24f43c7`

## Files Changed

- `app/meta_analysis/models/effect_size_normalization.py`
- `app/meta_analysis/services/effect_size_normalization_service.py`
- `app/meta_analysis/pages/analysis_page.py`
- `tests/meta_analysis/test_effect_size_normalization_service.py`
- `docs/meta_dev_reports/Meta_M11_effect_size_normalization_report_20260513.md`

## Behavior Changed

- Added a narrow per-study effect-size normalization model for confirmed extraction rows.
- Added `EffectSizeNormalizationService` with:
  - `normalize_extraction_rows`
  - `normalize_single_effect`
  - `validate_effect_input`
  - `summarize_normalization`
- Added readiness handling for `OR`, `RR`, `HR`, `MD`, `SMD`, `proportion`, `correlation`, `diagnostic_accuracy`, and `other`.
- For confirmed `OR`/`RR`/`HR` rows with valid positive estimate and CI, the service derives log estimate, log CI, standard error, and variance.
- For confirmed `MD`/`SMD` rows with valid estimate and CI, the service derives standard error and variance on the original scale.
- Draft or suggested extraction rows are marked `needs_user_review` and are not executor-ready.
- Invalid CI, invalid numeric fields, non-positive ratio inputs, negative counts, and unsupported effect types are blocked with explicit statuses and warnings.
- Added a Chinese-first safe precheck summary to the existing analysis page:
  - 效应量标准化预检查
  - 可用于后续统计的研究数
  - 需要用户检查
  - 字段不完整
  - 不支持的效应量类型

## Result Semantics

- M11 does not run pooled meta-analysis.
- M11 does not create `computed`, `user_reviewed`, or `report_ready` statistical results.
- Normalization summaries set `creates_computed_result=false` and `result_state=configured_not_run`.
- Ready normalized inputs only prepare future executor validation. M10 result-state gates still block formal computed results without a real executor, confirmed plan, sufficient inputs, and reproducibility metadata.

## Validation Commands and Exact Results

`git diff --check`

Result: passed with no output.

`python3 -m pytest tests/meta_analysis -q`

Result:

```text
503 passed in 4.63s
```

`QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`

Result:

```text
154 passed in 10.07s
```

`QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`

Result:

```text
BioMedPilot / 医研智析
app_version=0.1.0-internal-beta
app_channel=Developer Preview / testing
launch_mode=source
app_root=/Users/changdali/Developer/biomedpilot v1.0/Meta
git_head=24f43c7
workspace_entries=2
bioinformatics_features=5
meta_analysis_features=7
pyside6_available=True
```

## Limitations

- This stage implements normalization readiness, not a formal statistical executor.
- `proportion`, `correlation`, `diagnostic_accuracy`, and `other` are safely classified for future mapping rather than fully normalized into executor formulas.
- Normalized inputs are not persisted as formal result artifacts and must not be used as publication-ready statistical outputs.
- The analysis page preview exposes only aggregate counts and safe Chinese labels; raw paths, raw JSON, manifest paths, and internal row IDs are not shown in the main UI.

## Remaining Dirty or Untracked Files at Report Creation

- Expected untracked input artifact remains: `docs/meta_dev_reports/Meta_handoff_report_20260513.md`
- M11 files were dirty before commit.

## Commit

Commit is expected after final validation. The final commit hash is reported in the assistant handoff because embedding a commit's own hash inside this committed report would change that hash.
