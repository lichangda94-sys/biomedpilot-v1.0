# UI Shell Baseline Decision

Date: 2026-05-29

## Decision

`9d4edf3` is the user-recognized UI Shell / visual preview baseline for BioMedPilot.

It is not a feature-complete baseline and must not be used as proof that module features are connected, migrated, or release-ready.

## Source Preview

| Item | Value |
| --- | --- |
| Preview bundle | `/Users/changdali/Developer/biomedpilot v1.0/Integration/dist/BioMedPilot Integration Preview.app` |
| app_root | `/Users/changdali/Developer/biomedpilot v1.0/Integration/dist/BioMedPilot Integration Preview.app/Contents/Resources/app` |
| git_head | `9d4edf3` |
| launch_mode | `packaged-local-python` |
| Containing branch | `codex/integration-labtools-ui-c2-carryover` |
| Screenshot evidence | `/tmp/biomedpilot_integration_preview_app_20260529.png` |

## Baseline Boundaries

| Area | Decision | Notes |
| --- | --- | --- |
| Welcome | UI Shell baseline candidate | Visual shell only; verify source file scope before MainLine migration. |
| Home visual frame | UI Shell baseline candidate | Does not prove Project Management completeness. |
| About | UI Shell baseline candidate | Validate route and dialog/page behavior before migration. |
| Sidebar | UI Shell baseline candidate | Verify module navigation and object names. |
| Module home visual frames | UI Shell baseline candidate | Buttons must still be inventoried route by route. |
| Settings / release gate shell | UI Shell baseline candidate | Gate semantics must remain testing/developer-preview where applicable. |
| Shared UI primitives | UI Shell baseline candidate | Must be scoped and tested before entering MainLine. |
| Bioinformatics feature pages | Not decided | Must use feature inventory and route audit. |
| Meta Analysis feature pages | Not decided | Must preserve Phase 4 L3 evidence separately. |
| LabTools feature pages | Not decided | Must use LabTools reconciliation ledger. |
| Project Management | Regressed in preview | Must be restored from best source; image-only state is not complete. |

## Prohibited Interpretations

- Do not treat `9d4edf3` as a feature-complete version.
- Do not merge `codex/integration-labtools-ui-c2-carryover` into `stable/mainline`.
- Do not cherry-pick `9d4edf3`.
- Do not treat old pages, empty buttons, or placeholders as connected features.
- Do not continue MainLine Meta L3 migration until the UI Shell baseline plan is confirmed.

## Required Next Audit

| Audit Item | Status | Required Output |
| --- | --- | --- |
| UI Shell scoped migration plan | pending | Approved file list and forbidden-path check |
| Project Management restore source search | pending | `PROJECT_MANAGEMENT_RESTORE_PLAN.md` updates |
| Module route inventory | pending | `UI_ROUTE_FEATURE_INVENTORY.md` filled rows |
| LabTools reconciliation | pending | `LABTOOLS_RECONCILIATION_LEDGER.md` filled rows |
