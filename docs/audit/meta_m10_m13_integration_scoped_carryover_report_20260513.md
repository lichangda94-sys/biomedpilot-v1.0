# Meta M10-M13 Integration Scoped Carry-over Report

## Scope

This stage carried Meta M10-M13 into the Integration worktree as a scoped Meta runtime update.

- Integration worktree: `/Users/changdali/Developer/biomedpilot v1.0/Integration`
- Integration branch: `dev/integration`
- Integration HEAD before carry-over: `40b67af`
- Meta source branch: `dev/meta-analysis`
- Meta source state used for M10-M13: M10 `24f43c7`, M11 `5e27ed4`, M12 `ea7d203`, M13 `0895d78`
- MainLine worktree checked for shell stability: `/Users/changdali/Developer/biomedpilot v1.0/MainLine`
- MainLine branch: `stable/mainline`
- MainLine HEAD during verification: `fd0b9a0`

No packaging, remote push, or production-release action was performed.

## Carry-over commits applied to Integration

- `5702e2f feat(meta): gate statistical result states`
- `299279b feat(meta): add effect size normalization service`
- `c02e530 feat(meta): add pairwise meta executor MVP`
- `6c809fb feat(meta): add result review report-ready transition`

The M10 cherry-pick conflicted in `app/meta_analysis/services/formal_report_service.py`. Resolution took the Meta-side safe report-state implementation so M10-M13 report gating and raw-path sanitization remain intact.

## Additional Integration adaptation

After the four scoped commits, `tests/meta_analysis` initially failed because Integration lacked two earlier Meta runtime compatibility pieces that M11 relies on:

- M4C/M5 full-text status constants and compatibility aliases in `app/meta_analysis/services/fulltext_management_service.py`
- M5 structured extraction row helpers in `app/meta_analysis/services/manual_extraction_effect_row_service.py`

The stale Integration report tests also still expected raw artifact paths such as forest plot filenames and local project paths in report bodies. Those expectations contradict the M10-M13 requirement that the user-facing report must not expose raw paths, raw JSON, manifest paths, or internal IDs.

The adaptation therefore carried over the matching safe Meta versions of:

- `app/meta_analysis/services/fulltext_management_service.py`
- `app/meta_analysis/services/manual_extraction_effect_row_service.py`
- `tests/meta_analysis/test_fulltext_management_service.py`
- `tests/meta_analysis/test_manual_extraction_effect_row_service.py`
- report-related Meta tests updated to assert safe M8/M10-M13 report semantics.

## Result semantics preserved

- M10 result states remain canonical: `not_run`, `configured_not_run`, `testing_level`, `failed_validation`, `computed`, `user_reviewed`, `report_ready`.
- M11 normalized effect-size inputs do not create `computed` or `report_ready` results.
- M12 computed results remain Developer Preview / testing and are not report-ready by default.
- M13 requires explicit user review and report-ready gate approval.
- `report_ready` means safe for the current draft report workflow only. It does not mean production, clinical, regulatory, submission-ready, publication-ready, or formal evidence status.
- Old `AnalysisRunService` / `AnalysisResult` output remains `testing_level` and blocked from formal report claims.

## MainLine shell verification

MainLine was not modified. The current MainLine shell was checked separately to verify that the shell remains stable while Integration carries the scoped Meta changes.

MainLine smoke test result:

```text
BioMedPilot / 医研智析
app_version=0.1.0-internal-beta
app_channel=Developer Preview / testing
launch_mode=source
app_root=/Users/changdali/Developer/biomedpilot v1.0/MainLine
git_head=fd0b9a0
workspace_entries=2
bioinformatics_features=5
meta_analysis_features=7
pyside6_available=True
```

MainLine targeted shell/UI test:

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q`
- Result: `16 passed in 2.20s`

## Integration validation

- `git diff --check`
  - Result: passed with no output before and after this report.
- `python3 -m pytest tests/meta_analysis -q`
  - Result: `514 passed in 7.32s`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - Result: `178 passed in 13.30s`
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`
  - Result:

```text
BioMedPilot / 医研智析
app_version=0.1.0-internal-beta
app_channel=Developer Preview / testing
launch_mode=source
app_root=/Users/changdali/Developer/biomedpilot v1.0/Integration
git_head=6c809fb
workspace_entries=3
bioinformatics_features=5
meta_analysis_features=7
labtools_features=4
pyside6_available=True
```

## Cross-module boundary

Runtime changes are scoped to `app/meta_analysis/**`.

Test changes are scoped to `tests/meta_analysis/**` plus the M13 Meta UI test already introduced by the carry-over:

- `tests/ui/test_meta_m13_result_review_ui.py`

No Bioinformatics, LabTools, UIShell, ReleaseBuild, MainLine, or ProjectControl runtime file was modified by this stage.

## Limitations

- Integration now contains M10-M13 plus the minimum full-text/extraction compatibility pieces required by M11.
- This is not a MainLine scoped apply. MainLine was validated but not changed.
- No random-effects, network meta-analysis, diagnostic meta-analysis, formal plots, subgroup automation, sensitivity automation, publication-bias automation, or production statistical conclusion was added.
- A future MainLine scoped apply should carry this Integration state as a coherent Meta set and rerun MainLine validation after applying it.

## Dirty/untracked status before final commit

Before final commit, expected Integration changes are the scoped carry-over adaptation files and this audit report. MainLine remains clean.
