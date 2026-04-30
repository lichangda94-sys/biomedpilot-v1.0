# Stage AB14 Internal Beta Acceptance Report

Status: Developer Preview / testing.

## Scope

Stage AB14 performed an internal beta acceptance audit for the Meta Analysis workflow, sample project pack, analysis/PRISMA/report artifacts, version metadata, and packaged desktop entry.

This stage did not add new statistical methods, production PDF export, automatic PDF download, OCR, institutional full-text access, AI auto-extraction, payment/subscription logic, or Bioinformatics business changes.

## Start State

- Branch: `codex/biomedpilot-root`
- Starting HEAD: `ff8c298 fix(app): add versioned unified launcher metadata`
- Git status at start: `test_inputs/` was already untracked; AB14 added acceptance tests and documentation.
- Unified desktop entry: `/Users/changdali/Desktop/BioMedPilot.app`
- Old entry backup paths:
  - `/Users/changdali/Desktop/BioMedPilot旧入口备份/BioMedPilot Meta Analysis.app`
  - `/Users/changdali/Desktop/BioMedPilot旧入口备份/BioMedPilot.app.20260429-225832`

## Version Metadata Acceptance

Expected version identity:

- Version: `0.1.0-internal-beta`
- Bundle version: `0.1.0`
- Channel: `Developer Preview / testing`

Checked locations:

- `app/version.py`
- source smoke test: `python3 -m app.main --smoke-test`
- packaged app smoke test: `/Users/changdali/Desktop/BioMedPilot.app/Contents/MacOS/BioMedPilot --smoke-test`
- packaged `BUILD_INFO.json`
- packaged `Info.plist`
- tester guide and packaging documentation

Observed source smoke output before AB14 commit:

```text
BioMedPilot / 医研智析
app_version=0.1.0-internal-beta
app_channel=Developer Preview / testing
launch_mode=source
app_root=/Users/changdali/Documents/BioMedPilot
git_head=ff8c298
workspace_entries=2
bioinformatics_features=11
meta_analysis_features=7
pyside6_available=True
```

Observed packaged smoke output before AB14 commit:

```text
BioMedPilot / 医研智析
app_version=0.1.0-internal-beta
app_channel=Developer Preview / testing
launch_mode=packaged-local-python
app_root=/Users/changdali/Desktop/BioMedPilot.app/Contents/Resources/app
git_head=ff8c298
workspace_entries=2
bioinformatics_features=11
meta_analysis_features=7
pyside6_available=True
```

`BUILD_INFO.json` and `Info.plist` contain the same version, channel, and git head fields. The AB14 packaged-entry test now verifies these fields on a temporary app bundle.

## Workflow Dashboard Acceptance

The Meta workflow dashboard still exposes the 15 internal beta steps:

1. Project Setup
2. Protocol / Research Question
3. Literature Import
4. Import Diagnostics
5. Duplicate Review
6. Criteria Builder
7. Title / Abstract Screening
8. Full-text / Attachment
9. Extraction
10. Quality Assessment
11. Analysis-ready Dataset
12. Meta-analysis Run
13. Figures / Tables
14. PRISMA / Report
15. Reproducibility Package

AB14 tests assert that these steps remain discoverable, warning based for missing artifacts, and marked Developer Preview / testing.

## Sample Project Acceptance

Validated AB13 sample manifests:

- `examples/meta_analysis_internal_beta_samples/treatment_effect_binary_or/manifest.json`
- `examples/meta_analysis_internal_beta_samples/biomarker_prevalence_correlation/manifest.json`

The treatment-effect sample and biomarker sample source inputs remain committed as compact fixtures only. Generated reports, figures, and ZIP packages are produced in temporary project directories during tests and are not committed.

## Analysis, PRISMA, Report, And Package Artifacts

The AB14 E2E acceptance test builds a disposable Meta project and verifies generation of:

- `analysis/analysis_plan.json`
- `analysis/analysis_ready_dataset.json`
- `analysis/analysis_ready_datasets.json`
- `analysis/analysis_result.json`
- `analysis/analysis_results.json`
- `analysis/applicability_warnings.json`
- `reports/prisma_summary.json`
- `reports/prisma_flow.md`
- `reports/prisma_flow.svg`
- `reports/formal_meta_report.md`
- `exports/reproducibility_package_*.zip`

PRISMA source references are checked for import, screening, and extraction sources. The report is checked for Developer Preview / testing language and applicability warning references.

## Developer Preview Boundary

AB14 confirms the internal beta remains non-production:

- Meta feature availability entries remain `testing`.
- Reports continue to state Developer Preview / testing.
- Extraction values in sample projects are validation seeds where documented.
- No automatic PDF download, OCR, institutional full-text access, AI auto-overwrite, Network Meta, HSROC, or meta-regression workflow is enabled.
- The local macOS app is a testing launcher bundle, not a standalone production installer.

## Tests Added

- `tests/meta_analysis/test_stage_ab14_internal_beta_acceptance.py`
- `tests/test_versioned_packaged_entry.py`

Coverage includes:

- version metadata readability
- smoke-test metadata fields
- temporary packaged app `BUILD_INFO.json` and `Info.plist`
- workflow dashboard 15-step integrity
- sample manifest validation
- disposable project artifact generation
- missing artifact warning behavior
- Developer Preview/testing status regression guard

## Test Results

AB14 verification run before commit:

| Command | Result |
| --- | --- |
| `python3 -m compileall -q .` | Failed on unrelated hidden worktree virtualenv template: `.worktrees/bioinformatics-safe-stage2/.venv/.../PySide6/__init__.tmpl.py` contains Jinja syntax and is not valid Python source. The file was not modified. |
| `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .` | Same unrelated hidden worktree virtualenv template failure. |
| `python3 -m compileall -q -x '(^|/)\\.worktrees/' .` | Passed. |
| `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q -x '(^|/)\\.worktrees/' .` | Passed. |
| `python3 -m pytest -q` | `415 passed` |
| `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q` | `415 passed` |
| `python3 scripts/run_tests.py` | `415 passed` |
| `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py` | `415 passed` |
| `python3 -m app.main --smoke-test` | Passed; source launch mode, version `0.1.0-internal-beta`, channel `Developer Preview / testing`, git head `ff8c298` before commit. |
| `python3 scripts/package_app.py --no-clean --smoke-test` | Passed; packaged local Python launcher, version `0.1.0-internal-beta`, git head `ff8c298` before commit. |
| `/Users/changdali/Desktop/BioMedPilot.app/Contents/MacOS/BioMedPilot --smoke-test` | Passed; unified desktop entry, packaged local Python launcher, version `0.1.0-internal-beta`, git head `ff8c298` before commit. |

After the AB14 commit, the package should be refreshed once so packaged `git_head` points at the AB14 commit rather than the pre-AB14 launcher commit.

AB14 follow-up acceptance audit after package refresh:

| Check | Result |
| --- | --- |
| Current branch | `codex/biomedpilot-root` |
| Current HEAD | `de1e328 test(meta): add internal beta packaged acceptance audit` |
| Source smoke | Passed; `app_version=0.1.0-internal-beta`, `app_channel=Developer Preview / testing`, `launch_mode=source`, `git_head=de1e328` |
| Desktop packaged smoke | Passed; `app_version=0.1.0-internal-beta`, `app_channel=Developer Preview / testing`, `launch_mode=packaged-local-python`, `git_head=de1e328` |
| Desktop `BUILD_INFO.json` | Version `0.1.0-internal-beta`, bundle version `0.1.0`, channel `Developer Preview / testing`, git head `de1e328` |
| Desktop `Info.plist` | `BioMedPilotVersion=0.1.0-internal-beta`, `BioMedPilotChannel=Developer Preview / testing`, `BioMedPilotGitHead=de1e328`, `CFBundleShortVersionString=0.1.0` |
| AB14 focused tests | `6 passed` |

Current unified desktop entry:

```text
/Users/changdali/Desktop/BioMedPilot.app
```

The desktop entry now opens the refreshed internal beta bundle built from `de1e328`.

## Internal Beta Candidate Judgment

AB14 is intended to qualify the current build as an internal beta candidate for tester-facing trials, subject to the final full test run and packaged desktop smoke result.

It is not production-ready because statistical interpretation, report language, full-text handling, sample extraction data, packaging, and several advanced methods remain explicitly testing or placeholder.

## Next Stage Recommendations

- Run a tester walkthrough from the unified desktop entry on a clean user account or separate test machine.
- Keep collecting usability blockers around Protocol, Import Wizard, Screening, Extraction, Quality, and Report pages.
- Do not upgrade feature status beyond testing until real user trial feedback and method validation are complete.
