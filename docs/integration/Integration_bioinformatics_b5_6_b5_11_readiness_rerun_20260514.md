# Integration Bioinformatics B5.6-B5.11 Readiness Rerun - 2026-05-14

## Decision

Status: `READY_FOR_RELEASEBUILD_PREVIEW_PACKAGING`.

The current Integration candidate includes a scoped Bioinformatics B5.6-B5.11 carry-over and is ready for ReleaseBuild to generate the second `BioMedPilot Integration Preview.app` package.

This decision applies only to the Integration-approved source in the current `dev/integration` worktree. It does not approve whole-branch merges from Bioinformatics, Meta, LabTools, UIShell, or ReleaseBuild. It does not approve overwriting `/Users/changdali/Desktop/BioMedPilot Dev.app` or any existing formal `BioMedPilot.app`.

## Scoped Carry-over

Bioinformatics source commits audited and carried over by scope:

- `6745d7c` Fix Bioinformatics standardization readiness gate
- `71ee27d` Fix Bioinformatics local multi-file import handoff
- `402137f` Fix Bioinformatics recognition standardization gate
- `281c533` docs: audit legacy GEO parser capability
- `d53bc11` Fix Bioinformatics family SOFT recognition parser
- `5824b32` Add Bioinformatics Series Matrix parser MVP
- `730a8e0` Add Bioinformatics standardization confirmation UI
- `32225a9` docs: add Bioinformatics B5.11 desktop manual test checklist

Bioinformatics imported DEG / report loop commits `aff8ba5` and `0617333` were audited but not whole-branch merged. Integration already had the scoped B5 result/report loop via `f67119d`, and the rerun kept that Integration path while validating the imported DEG/report tests.

## Files In Scope

- `app/bioinformatics/**`
- `tests/bioinformatics/**`
- Bioinformatics-specific cases in `tests/ui/test_bioinformatics_workflow_pages.py`
- Bioinformatics B5.6-B5.11 docs under `docs/bioinformatics/**`

No Meta, LabTools, UIShell, ReleaseBuild, `app/main.py`, or shared shell source was intentionally changed by this carry-over.

## Validation

Passed:

```text
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics/test_workflow_adapters.py tests/bioinformatics/test_imported_deg_results.py tests/bioinformatics/test_project_report_builder.py tests/bioinformatics/test_deg_task_plan.py tests/ui/test_bioinformatics_workflow_pages.py -q
156 passed in 4.37s

python3 -m compileall app/bioinformatics
passed

QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py -q
16 passed in 2.98s

QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
185 passed in 14.63s

python3 -m pytest tests/shared tests/test_package_app.py tests/test_versioned_packaged_entry.py -q
228 passed in 29.30s
```

Scope guard:

```text
git diff --name-only | rg '^(app/meta_analysis|app/labtools|ReleaseBuild|release|dist|build|app/main.py|tests/ui/test_meta_|tests/ui/test_labtools_|tests/ui/test_shared_)'
no matches
```

## ReleaseBuild Packaging Constraints

ReleaseBuild may now generate only the second `BioMedPilot Integration Preview.app` from this Integration-approved source.

ReleaseBuild must not:

- package from `dev/bioinformatics` or any other module branch;
- whole-branch merge Bioinformatics, Meta, LabTools, UIShell, or ReleaseBuild into Integration;
- overwrite `/Users/changdali/Desktop/BioMedPilot Dev.app`;
- overwrite any formal `BioMedPilot.app`;
- use ReleaseBuild source as business maturity evidence;
- promote this package to MainLine, stable, production, clinical, regulatory, or publication-grade status.

The package name, `CFBundleName`, `CFBundleDisplayName`, and launcher executable must clearly identify `BioMedPilot Integration Preview`.

## Next Step

Proceed to ReleaseBuild scoped preview packaging. After packaging, ReleaseBuild must record the package path, source git head, build metadata, codesign verification, packaged smoke result, and confirmation that no desktop app was overwritten.
