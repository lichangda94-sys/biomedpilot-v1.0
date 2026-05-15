# Integration Preview Packaging Readiness Re-check - 2026-05-13

## Decision

`READY_FOR_RELEASEBUILD_PREVIEW_PACKAGING`

Current `dev/integration` source is ready to hand off to `ReleaseBuild` for controlled generation of `BioMedPilot Integration Preview.app`.

This readiness decision applies only to packaging execution from the current Integration-approved source. It does not authorize business-scope expansion, whole-branch merges, desktop app overwrite, remote push, or promotion to a formal public/stable release.

## Current Integration state

| Item | Observed state |
| --- | --- |
| Worktree | `Integration` |
| Branch | `dev/integration` |
| Validated source HEAD before this report update | `f67119d` (`feat(integration): scope bioinformatics b5 result report loop`) |
| This re-check report update | documentation-only; no source/runtime code change |
| Dirty status before report update | clean |
| Source smoke reported git head | `f67119d` |
| Packaging in this re-check | not run |
| Desktop app overwrite | not performed |
| Remote push | not performed |

## Source content decision

### MainLine baseline

Status: included as the current Integration foundation.

Integration previously refreshed onto the MainLine baseline before LabTools L6A.1 and Bioinformatics B5 scoped integrations. This re-check validates the current `dev/integration` source rather than any individual module branch.

### LabTools L6A.1

Status: present and approved for preview candidate source.

Evidence:
- `app/labtools/**` is present.
- `tests/labtools/**` is present and passing.
- `docs/integration/Integration_labtools_l6a1_scoped_integration_report_20260513.md` is present.
- `labtools_roi_export_manifest.v1` is present in LabTools export package code and tests.
- Fluorescence manual ROI export and wound/scratch manual ROI + threshold export package tests are present.

Semantic boundary remains:
- LabTools is Developer Preview / testing.
- Fluorescence ROI and scratch/wound ROI are manual-review auxiliary analysis.
- Export packages are auxiliary analysis materials, not formal scientific conclusions.
- No automatic ROI, automatic cell counting, grayscale/WB/gel grayscale, OpenCV, scikit-image, ImageJ/Fiji, AI, network, database, autosave, history, batch export, or formal report system is opened by this readiness decision.

### Bioinformatics B5 result/report loop

Status: present and approved for preview candidate source.

Evidence:
- `app/bioinformatics/imported_deg_results.py` is present.
- `app/bioinformatics/reports/project_report_builder.py` contains B5-compatible report semantics and safe text handling.
- `docs/bioinformatics/stage_B5_result_report_loop_stabilization_20260513.md` is present.
- `tests/bioinformatics/test_imported_deg_results.py` is present.
- `tests/bioinformatics/test_project_report_builder.py` is present.
- `docs/integration/Integration_bioinformatics_b5_scoped_integration_20260513.md` is present.

Important ancestry note:
- Source commit `0617333` from `dev/bioinformatics` is still not an ancestor of current `HEAD`.
- This is expected and acceptable because the B5 work was applied by scoped integration, not whole-branch merge.
- The key B5 content is present in current Integration source and passed validation.

Integrated B5 scope:
- imported DEG `ready` / `report_candidate` conditions are stricter;
- abnormal imported DEG inputs, duplicate genes, and non-numeric logFC or p values require confirmation;
- Chinese column names and CSV/TSV/TXT/GZ/XLSX imported DEG inputs are covered;
- project report builder keeps real-computed DEG closed;
- report warnings and visible Markdown data-source text are sanitized to avoid raw absolute paths;
- old, empty, and missing result index states are handled safely;
- semantic safety tests are present.

Explicit exclusions remain:
- no real DEG executor;
- no volcano plot;
- no heatmap;
- no enrichment;
- no GSEA;
- no survival analysis;
- no correlation analysis;
- no network search or download;
- no AI, local model, or external model call.

### UIShell

Status: excluded from this preview source as a module branch.

The current source includes only the shell compatibility needed for the current Integration candidate, MainLine navigation, LabTools entry, and existing UI tests. It does not promote the `dev/ui-shell` branch as a preview content source. UIShell remains outside this preview package until its separate blockers are resolved and audited.

### Meta

Status: docs/status layer only for this readiness decision.

No new Meta formal runtime analysis capability is approved by this re-check. Meta remains constrained to current documented/status surfaces. A formal Meta statistics executor, formal analysis run, pooled effect estimation, forest/funnel output, publication-grade report workflow, or new formal runtime analysis surface is not opened by this source.

### ReleaseBuild

Status: packaging executor only.

`ReleaseBuild` may be used only to package from this Integration-approved source and run packaged smoke validation. It must not be used as a business maturity source and must not decide module readiness.

## Packaging side effect record

Earlier background reported that `python3 scripts/package_app.py --smoke-test` was accidentally run and passed, updating `dist/BioMedPilot.app` to the then-current HEAD.

Local re-check in this worktree did not find `dist/BioMedPilot.app` at report time. Regardless of local artifact visibility, any app produced by that accidental `package_app.py --smoke-test` run remains explicitly non-official:

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
| `python3 -m app.main --smoke-test` | pass; reported `git_head=f67119d`, `workspace_entries=3`, `bioinformatics_features=5`, `meta_analysis_features=7`, `labtools_features=4` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q` | pass; `277 passed` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q` | pass; `130 passed` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | pass; `177 passed` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_module_boundary_contract.py -q` | pass; `5 passed` |

## ReleaseBuild allowed next step

ReleaseBuild is now allowed to execute the minimum preview packaging scope:

- generate only `BioMedPilot Integration Preview.app`;
- do not overwrite `/Users/changdali/Desktop/BioMedPilot Dev.app`;
- do not overwrite any old formal `BioMedPilot.app`;
- package name, metadata, `CFBundleName`, and `CFBundleExecutable` must clearly identify `Integration Preview`;
- packaged smoke must pass;
- ReleaseBuild must generate a preview package report after packaging.

## Not allowed in ReleaseBuild next step

ReleaseBuild must not:

- change business module code;
- broaden Bioinformatics, Meta, LabTools, or UIShell scope;
- treat Meta docs/status surfaces as formal runtime statistics capability;
- treat the accidental `dist/BioMedPilot.app` side-effect artifact as official;
- package or overwrite `BioMedPilot Dev.app`;
- package or overwrite an old formal `BioMedPilot.app`;
- push remote.

## Recommendation

Proceed to ReleaseBuild scoped preview packaging only under the minimum allowed scope above.

Do not perform additional module integration in ReleaseBuild. If any packaged smoke or metadata validation fails, return to Integration with a scoped failure report rather than expanding ReleaseBuild responsibilities.
