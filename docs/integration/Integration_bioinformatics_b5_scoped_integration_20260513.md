# Integration Bioinformatics B5 Scoped Integration - 2026-05-13

## Decision

Bioinformatics B5 result/report loop stabilization has been scoped-integrated into the current Integration worktree.

This is not a whole-branch merge. Commit `0617333` is not merged as an ancestor; its B5-required content was applied as a bounded file/logic integration onto current `dev/integration`.

## Baseline

| Item | Value |
| --- | --- |
| Integration branch | `dev/integration` |
| Starting HEAD | `903cd36` (`docs(integration): recheck preview packaging readiness`) |
| Source B5 commit | `0617333` (`Stabilize Bioinformatics result report loop`) from `dev/bioinformatics` |
| Starting dirty status | clean |
| Packaging | not run |
| Desktop app overwrite | not performed |
| Remote push | not performed |

## Scoped apply files

Applied from B5 source:

- `app/bioinformatics/imported_deg_results.py`
- `docs/bioinformatics/stage_B5_result_report_loop_stabilization_20260513.md`
- `tests/bioinformatics/test_imported_deg_results.py`
- `tests/bioinformatics/test_project_report_builder.py`

Manually integrated into current Integration baseline:

- `app/bioinformatics/reports/project_report_builder.py`

New Integration report:

- `docs/integration/Integration_bioinformatics_b5_scoped_integration_20260513.md`

## Dependency and compatibility notes

B5 source commit `0617333` was built on top of earlier Bioinformatics result/report-loop work. Current Integration did not contain:

- `app/bioinformatics/imported_deg_results.py`
- B5 imported DEG tests
- B5 project report builder semantic-safety tests
- B5 stage report

Those files were added as the minimum B5 runtime/test dependency set.

`project_report_builder.py` was not copied wholesale from `dev/bioinformatics`, because current Integration already contains the newer MainLine report manifest/draft section structure and uses `deg_executor_preflight`. The B5 behavior was manually ported into the current builder:

- import and render B5 imported DEG result objects;
- include B5 imported DEG result IDs in report manifests;
- add semantic policy fields without removing existing `bioinformatics_report_manifest.v1` structure;
- sanitize result-index warnings and data-source/user text before Markdown rendering;
- keep real-computed DEG wording closed;
- keep existing MainLine section manifest and draft report layout intact.

B5 tests were adapted only where the Bioinformatics branch used the older `build_deg_preflight` helper. Integration uses `run_deg_executor_preflight`, so assertions were mapped to the current preflight result dictionary while preserving the same boundary: imported DEG is not a real DEG executor input and no real DEG execution is opened.

## Integrated B5 capabilities

- Imported DEG `ready` / `report_candidate` is now stricter:
  - missing gene/logFC/significance columns require confirmation;
  - empty/header-only files require confirmation;
  - duplicate gene symbols require confirmation;
  - non-numeric logFC or p value/FDR rows require confirmation.
- Chinese column names are detected for gene, logFC, p value, and adjusted p value/FDR.
- CSV, TSV, TXT, GZ, and no-new-dependency XLSX imported DEG tables are covered.
- Ready imported DEG results can be written as report candidates with explicit imported-result semantics.
- Report builder includes imported DEG result summaries while keeping wording as external imported results.
- Report builder keeps real computed DEG closed: no real DEG executor, no BioMedPilot-computed DEG claim.
- Report warnings and visible Markdown data-source text are sanitized to avoid raw absolute paths.
- Old, empty, and missing result index states are handled safely.

## Explicit exclusions

Not introduced:

- real DEG executor;
- volcano plot;
- heatmap;
- enrichment;
- GSEA;
- survival analysis;
- correlation analysis;
- network search or download;
- AI, local model, or external model call;
- ReleaseBuild packaging changes;
- LabTools, Meta, UIShell, or ReleaseBuild business-code changes.

## Validation

| Command | Result |
| --- | --- |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics/test_imported_deg_results.py tests/bioinformatics/test_project_report_builder.py -q` | pass; `12 passed` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q` | pass; `277 passed` |
| `python3 -m app.main --smoke-test` | pass; reported `git_head=903cd36`, `workspace_entries=3`, `bioinformatics_features=5`, `meta_analysis_features=7`, `labtools_features=4` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | pass; `177 passed` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_module_boundary_contract.py -q` | pass; `5 passed` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q` | pass; `130 passed` |
| `git diff --check` | pass |

## Packaging gate

Do not hand off to ReleaseBuild immediately from this integration step alone. The correct next step is another Integration Preview packaging readiness re-check from the new Integration HEAD.

ReleaseBuild remains packaging executor only. It must not decide business maturity and must not package until Integration explicitly concludes `READY_FOR_RELEASEBUILD_PREVIEW_PACKAGING`.

If the next re-check is ready, ReleaseBuild may then package only `BioMedPilot Integration Preview.app` with Integration Preview naming and metadata, without overwriting `BioMedPilot Dev.app` or any old formal `BioMedPilot.app`.
