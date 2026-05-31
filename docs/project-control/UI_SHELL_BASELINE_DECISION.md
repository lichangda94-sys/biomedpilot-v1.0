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

## Provenance Addendum: `9d4edf3` / `e13d0f5`

`docs/ui/UI线路既往检查.md` records `codex/integration-labtools-ui-c2-carryover` as the preferred historical UI recovery source. In that check, `e13d0f5f5dfda36a5c60a00ddc7820748fa1677f` is the recorded carryover HEAD and `9d4edf3` is the later packaged preview identity accepted by the user.

| Item | Decision |
| --- | --- |
| Accepted packaged preview | `9d4edf3` remains the UI Shell / visual preview baseline. |
| Historical carryover HEAD | `e13d0f5f5dfda36a5c60a00ddc7820748fa1677f` is the recorded UI recovery line HEAD in `docs/ui/UI线路既往检查.md`. |
| Relationship | `e13d0f5` is part of the carryover line used as UI recovery evidence; `9d4edf3` is the later accepted preview identity. |
| Migration boundary | Neither `9d4edf3` nor `e13d0f5` authorizes whole-branch merge or direct cherry-pick. |
| Governance result | Use `9d4edf3` for Shell baseline evidence; use `codex/integration-labtools-ui-c2-carryover` and the commit matrices as feature-page recovery evidence subject to scoped audit. |

`e13d0f5..9d4edf3` is treated as UI gate / Settings detect-first / release preview refinement evidence, not proof of feature completeness.
