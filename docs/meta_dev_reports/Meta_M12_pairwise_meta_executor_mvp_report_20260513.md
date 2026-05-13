# Meta M12 Pairwise Meta Executor MVP Report

## Stage

Meta M12 — Pairwise Meta Executor MVP

## Branch

`dev/meta-analysis`

## HEAD Before Work

`5e27ed4`

## Files Changed

- `app/meta_analysis/models/pairwise_meta_executor.py`
- `app/meta_analysis/services/pairwise_meta_executor_service.py`
- `app/meta_analysis/pages/analysis_page.py`
- `app/meta_analysis/services/formal_report_service.py`
- `tests/meta_analysis/test_pairwise_meta_executor_service.py`
- `docs/meta_dev_reports/Meta_M12_pairwise_meta_executor_mvp_report_20260513.md`

## Behavior Changed

- Added a narrow `PairwiseMetaExecutorService` for pairwise fixed-effect inverse-variance pooling from M11 normalized inputs.
- Added a result model with executor schema/version metadata, included/excluded study summaries, pooled estimate, 95% CI, standard error, z value, p value, heterogeneity diagnostics, validation errors, warnings, and reproducibility metadata.
- Successful execution can enter `computed` through the M10 computed gate, but it does not automatically become `user_reviewed` or `report_ready`.
- Added explicit service-level transitions for user review and report-ready marking through M10 report-ready gates.
- Added safe validation failures for:
  - missing confirmed analysis plan
  - fewer than two ready normalized studies
  - inconsistent effect measure type
  - missing or non-finite estimate / SE / variance
  - draft/suggested/unconfirmed source rows
  - unsupported random-effects model in M12
- Added minimal heterogeneity diagnostics: Q, df, and I2, labeled as Developer Preview/testing diagnostics.
- Added safe Chinese UI summary labels on the analysis page:
  - 统计执行状态
  - 模型
  - 纳入研究数
  - 合并效应量
  - 95% CI
  - 异质性 I²
  - 测试阶段提示
  - 需要用户审核后才能进入报告
- Updated draft report generation to summarize M12 computed results only as Developer Preview/testing unless a future result is report-ready.

## Result Semantics

- M12 implements only pairwise fixed-effect inverse-variance pooling.
- M12 does not implement network meta-analysis, diagnostic meta-analysis, random-effects pooling, subgroup analysis, sensitivity analysis, publication-bias analysis, forest plots, funnel plots, or formal conclusions.
- For OR/RR/HR, normalized log-scale values remain the primary reproducible executor scale. Back-transformed ratio values are provided only as auxiliary display fields.
- `computed` means the M12 MVP validation gate passed and a pooled estimate was calculated. It does not mean production, clinical, regulatory, publication-ready, or formal evidence status.
- `report_ready` still requires explicit user review and M10 report-ready gate approval.

## Validation Commands and Exact Results

`git diff --check`

Result: passed with no output.

`python3 -m pytest tests/meta_analysis -q`

Result:

```text
515 passed in 4.73s
```

`QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`

Result:

```text
154 passed in 10.17s
```

`QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`

Result:

```text
BioMedPilot / 医研智析
app_version=0.1.0-internal-beta
app_channel=Developer Preview / testing
launch_mode=source
app_root=/Users/changdali/Developer/biomedpilot v1.0/Meta
git_head=5e27ed4
workspace_entries=2
bioinformatics_features=5
meta_analysis_features=7
pyside6_available=True
```

## Limitations

- Random-effects pooling is intentionally not implemented in M12; requests return validation failure with a not-supported warning.
- Only generic inverse-variance inputs from M11 ready normalized records are pooled.
- M12 does not validate against external statistical packages or publication-grade references.
- M12 does not generate forest/funnel plots or formal interpretation text.
- UI and report integration are summaries only and do not expose raw JSON, manifest paths, local file paths, or internal IDs in the main display/report body.

## Remaining Dirty or Untracked Files at Report Creation

- Expected untracked input artifact remains: `docs/meta_dev_reports/Meta_handoff_report_20260513.md`
- M12 files were dirty before commit.

## Commit

Commit is expected after final validation. The final commit hash is reported in the assistant handoff because embedding a commit's own hash inside this committed report would change that hash.
