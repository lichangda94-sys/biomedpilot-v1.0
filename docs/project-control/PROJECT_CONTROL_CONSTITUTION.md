# BioMedPilot Project Control Constitution v2

Date: 2026-05-29

This constitution governs BioMedPilot UI Shell baseline decisions, feature page recovery, legacy feature triage, scoped migration planning, and MainLine acceptance.

## Current Fact Baseline

The user-recognized packaged preview UI is:

`/Users/changdali/Developer/biomedpilot v1.0/Integration/dist/BioMedPilot Integration Preview.app`

Preview identity:

| Item | Value |
| --- | --- |
| `git_head` | `9d4edf3` |
| `launch_mode` | `packaged-local-python` |

The historical UI recovery check is:

`docs/ui/UI线路既往检查.md`

That check records:

| Item | Value |
| --- | --- |
| Recommended UI page recovery source | `codex/integration-labtools-ui-c2-carryover` |
| Recorded carryover HEAD | `e13d0f5f5dfda36a5c60a00ddc7820748fa1677f` |
| Old integration branch issue | old `dev/integration` is missing Bioinformatics / Meta Analysis / LabTools page commits |
| Recovery warning | replaying old UI commits directly has shared UI foundation conflicts |

The relationship between packaged preview `9d4edf3` and historical recovery HEAD `e13d0f5f5dfda36a5c60a00ddc7820748fa1677f` is not yet confirmed and must be audited separately before any migration.

## Core Governance Rule

BioMedPilot must keep these baselines separate:

| Baseline | Meaning | Current Decision |
| --- | --- | --- |
| UI Shell Baseline | Welcome, home visual frame, About, Sidebar, module home visual frame, Settings/release gate shell | Use packaged preview `9d4edf3` as accepted visual evidence. |
| Feature Page Baseline | Bioinformatics, Meta Analysis, and LabTools concrete subpages | Use `codex/integration-labtools-ui-c2-carryover` as main recovery reference; each route still needs scoped audit. |
| Runtime Baseline | Computation, report/export, data write/read, artifacts | Must be judged from service/runtime tests, not shell appearance. |
| MainLine Baseline | Stable branch content | Must receive only scoped, audited, tested changes. |

## Prohibited Actions

- Do not merge whole `codex/integration-labtools-ui-c2-carryover` into MainLine.
- Do not merge whole `9d4edf3` packaged preview source into MainLine.
- Do not merge whole old `dev/integration` into MainLine for UI recovery.
- Do not cherry-pick historical UI commits without a scoped plan and conflict plan.
- Do not treat button presence as feature completion.
- Do not treat old LabTools pages as final Figma/new pages.
- Do not touch `project_storage/` during Project Control audit work.

## Route Completeness Standard

A route may be marked `connected` only when all of these exist:

- user-visible entry
- stable locator such as objectName or route key
- handler
- target page
- runtime/service or explicit no-runtime decision
- visible state, artifact, or output
- test coverage or route smoke
- documentation of functional boundary

Allowed route statuses:

`connected`, `partial`, `placeholder`, `empty-button`, `missing-handler`, `missing-target-page`, `old-page`, `figma/new`, `broken`, `not migrated`, `recovery-source-confirmed`

Allowed page styles:

`figma/new`, `old`, `hybrid`, `placeholder`, `missing`, `unknown`

## Required Project Control Documents

- `docs/project-control/UI_SHELL_BASELINE_DECISION.md`
- `docs/project-control/UI_ROUTE_FEATURE_INVENTORY.md`
- `docs/project-control/LABTOOLS_RECONCILIATION_LEDGER.md`
- `docs/project-control/PROJECT_MANAGEMENT_RESTORE_PLAN.md`
- `docs/project-control/MAINLINE_MIGRATION_LEDGER.md`
- `docs/project-control/LEGACY_FEATURE_TRIAGE.md`

## Migration Ledger Rule

Every migration candidate must be recorded before execution. Planned records are not permission to migrate. Migration may start only after a scoped plan names file scope, forbidden paths, validation commands, and rollback expectations.

Minimum forbidden path check for migration execution:

```bash
git diff --name-status | grep -E 'project_storage/' || true
```

## Current Immediate Decision

This absorption pass is audit-only. It creates Project Control governance documents from the historical UI line check. It does not migrate code, merge branches, cherry-pick commits, or touch `project_storage/`.
