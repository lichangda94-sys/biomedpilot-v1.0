# Meta UI Construction Preparation Report

## Scope

Prepared Meta Analysis for the next UI construction phase without building a new shell or changing packaging. This is Meta-only preparation work.

## Continuity Audit

- Current branch: `codex/biomedpilot-root`
- Baseline HEAD before this preparation: `76c96a2 feat(meta): add internal beta sample pack`
- Existing untracked `test_inputs/` remains untouched.
- Audited:
  - `app/meta_analysis/workspace.py`
  - `app/meta_analysis/pages/*`
  - `app/meta_analysis/services/*`
  - `tests/meta_analysis/*`
  - `docs/meta_internal_beta_walkthrough.md`
  - `docs/meta_known_limitations.md`
  - `docs/meta_dev_reports/*`

## Existing Capabilities Found

- Complete workflow dashboard and page states for protocol, import, diagnostics, duplicate review, screening, full-text, extraction, quality, analysis, reporting, audit, and sample pack.
- Service layer already holds business logic; UI should call page states and services instead of writing artifacts directly.
- Internal beta sample projects exist under `examples/meta_analysis_internal_beta_samples/`.

## Legacy Audit

Legacy directories remain read-only reference:

- `/Users/changdali/Documents/model9`
- `/Users/changdali/Documents/New project 2`
- `/Users/changdali/Documents/New project`

No legacy UI code was migrated in this preparation stage. Current BioMedPilot page-state architecture is more suitable than directly copying legacy PySide demo pages because it is already integrated with manifest, audit, lineage, Data Center, and Task Center.

## New Preparation Artifacts

- Added `app/meta_analysis/services/ui_construction_readiness_service.py`
- Added `docs/meta_ui_construction_preparation.md`
- Added tests for UI readiness state and documentation

## UI Construction Risks

- Extraction and Quality are the highest-risk pages for real users.
- Literature Library / Duplicate Review needs careful language around duplicate risk and merge preview.
- Reporting must keep PDF placeholder and simplified PRISMA limitations obvious.
- All pages must keep Developer Preview / testing visible.

## Recommended Next Step

Start with a narrow internal beta UI slice:

1. Workflow Dashboard
2. Literature Import diagnostics
3. Literature Library duplicate-risk table
4. Single-study Extraction form
5. Single-study Quality form
6. Analysis setup summary
7. Reporting export summary

Then run the AB13 sample projects through the desktop UI and record blocker/major/minor usability issues.
