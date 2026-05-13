# Integration Preview Packaging Readiness Re-check - 2026-05-13

## Decision

`NOT_READY`

Current `dev/integration` source is not ready to hand off to `ReleaseBuild` for `BioMedPilot Integration Preview.app` packaging.

The blocker is not test failure. The blocker is source-state mismatch: the current checked-out Integration HEAD is `a2e9c99`, while the expected Bioinformatics B5 scoped integration commit `0617333` is not contained in the current Integration branch. Therefore the current source cannot be treated as Integration-approved source containing both LabTools L6A.1 and Bioinformatics B5.

## Current Integration state

| Item | Observed state |
| --- | --- |
| Worktree | `Integration` |
| Branch | `dev/integration` |
| HEAD | `a2e9c99` (`feat(integration): scope labtools l6a1 onto mainline baseline`) |
| Dirty status before report | clean |
| Requested expected HEAD context | Background stated `6745d7c` and B5 commit `0617333` included |
| Actual B5 ancestry check | `0617333` is not an ancestor of current `HEAD` |
| Branch containing `0617333` | `dev/bioinformatics` |

## Scoped integration content check

### LabTools L6A.1

Status: present in current Integration source.

Evidence:
- `app/labtools/**` is present.
- `tests/labtools/**` is present.
- `docs/integration/Integration_labtools_l6a1_scoped_integration_report_20260513.md` is present.
- `labtools_roi_export_manifest.v1` is present in LabTools export package code and tests.
- Fluorescence manual ROI export and wound/scratch manual ROI + threshold export tests are present and passing.

Semantic boundary remains:
- LabTools is still Developer Preview / testing.
- Fluorescence ROI and scratch/wound ROI remain manual-review auxiliary analysis.
- Export packages are auxiliary analysis materials, not formal scientific conclusions.

### Bioinformatics B5 result/report loop

Status: not confirmed in current Integration source.

Evidence:
- Commit object `0617333` exists locally as `Stabilize Bioinformatics result report loop`.
- `git merge-base --is-ancestor 0617333 HEAD` returned non-zero.
- `git branch --contains 0617333 --all` shows `dev/bioinformatics`, not current `dev/integration`.
- Key B5 files from `0617333` are missing from current `HEAD`:
  - `app/bioinformatics/imported_deg_results.py`
  - `docs/bioinformatics/stage_B5_result_report_loop_stabilization_20260513.md`
  - `tests/bioinformatics/test_imported_deg_results.py`
  - `tests/bioinformatics/test_project_report_builder.py`
- `app/bioinformatics/reports/project_report_builder.py` exists, but differs materially from the B5 commit version.

Conclusion: Bioinformatics B5 result/report loop scoped integration must not be considered approved in this current checkout until the expected Integration commit containing B5 is actually present on `dev/integration` and revalidated.

### UIShell

Status: excluded from this preview source as a module source.

The current source includes shell-level compatibility wiring needed for MainLine and LabTools navigation, but it does not promote the `dev/ui-shell` module branch as a preview content source. UIShell remains outside this preview candidate until its earlier MainWindow/test blockers are separately resolved and audited.

### Meta

Status: docs/status level only for this readiness decision.

No new Meta formal runtime analysis capability is approved by this re-check. Meta remains constrained to current documented/status surfaces. A formal Meta statistics executor, formal analysis run, pooled effect estimation, forest/funnel output, or publication-grade report workflow is not opened by this source.

### ReleaseBuild

Status: packaging executor only.

`ReleaseBuild` remains responsible only for packaging from an Integration-approved or MainLine-stable source and for packaged smoke validation. It must not be used as a business maturity source and must not be used to convert unvalidated module state into an internal preview package.

## Packaging side effect record

Background note reports that `python3 scripts/package_app.py --smoke-test` was accidentally run and passed, updating `dist/BioMedPilot.app` to the then-current HEAD.

Local re-check in this worktree did not find `dist/BioMedPilot.app` at report time. Regardless of local artifact visibility, any app produced by that accidental `package_app.py --smoke-test` run is explicitly non-official:

- It is not `BioMedPilot Integration Preview.app`.
- It is not a ReleaseBuild-approved package.
- It must not be treated as a formal Integration Preview package.
- It must not overwrite `/Users/changdali/Desktop/BioMedPilot Dev.app`.
- It must not overwrite any old formal `BioMedPilot.app`.
- It must not be distributed or used as release evidence.

This re-check did not run packaging.

## Validation

| Command | Result |
| --- | --- |
| `git diff --check` | pass |
| `python3 -m app.main --smoke-test` | pass; reported `git_head=a2e9c99`, `workspace_entries=3`, `bioinformatics_features=5`, `meta_analysis_features=7`, `labtools_features=4` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q` | pass; `265 passed` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q` | pass; `130 passed` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | pass; `177 passed` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_module_boundary_contract.py -q` | pass; `5 passed` |

The validation commands passed, but the pass result applies to the actual current source at `a2e9c99`, not to the expected `6745d7c` source described in the task background.

## Blockers

P0:
- Current Integration HEAD does not match the expected source state described for this re-check.
- Bioinformatics B5 commit `0617333` is not contained in current `dev/integration`.
- Required B5 files/tests are absent from current `HEAD`, so current source cannot be claimed to include Bioinformatics B5 result/report loop scoped integration.

P1:
- The accidental packaging side effect must remain quarantined as a non-official local artifact. If a `dist/BioMedPilot.app` exists in another local context, it should be discarded or ignored for release evidence.

## Recommendation

Do not hand this current `dev/integration` source to `ReleaseBuild` for `BioMedPilot Integration Preview.app` packaging.

Next allowed step:
1. Locate or switch to the intended Integration commit that actually contains Bioinformatics B5 scoped integration, if it exists.
2. If it does not exist, perform the Bioinformatics B5 scoped integration as a separate, audited step.
3. Re-run the same validation matrix.
4. Generate a new readiness re-check report from the actual B5-containing Integration HEAD.

Only after the re-check concludes `READY_FOR_RELEASEBUILD_PREVIEW_PACKAGING` may ReleaseBuild execute the minimal packaging scope:
- generate only `BioMedPilot Integration Preview.app`;
- do not overwrite `BioMedPilot Dev.app`;
- do not overwrite old formal `BioMedPilot.app`;
- ensure package name, metadata, `CFBundleName`, and `CFBundleExecutable` clearly identify Integration Preview;
- pass packaged smoke;
- generate a ReleaseBuild preview package report.
