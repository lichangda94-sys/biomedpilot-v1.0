# MainLine Migration Ledger

Date: 2026-05-29

Purpose: record planned, in-progress, and completed scoped migrations into MainLine. This ledger does not authorize migration by itself.

## Migration Ledger

| Migration ID | Date | Target | Source | Migration Type | Migration Method | File Scope | Forbidden Path Check | Verification Commands | Verification Result | Audit Report | Status | Closed? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MAINLINE-UI-RECOVERY-PLAN-20260529` | 2026-05-29 | Restore user-recognized UI Shell + three-module page route baseline | `codex/integration-labtools-ui-c2-carryover` / packaged preview `git_head=9d4edf3` / historical check `e13d0f5f5dfda36a5c60a00ddc7820748fa1677f` | shell + feature page recovery planning | scoped plan required | not selected | not run; no migration performed | not run; planning only | planned, not migrated | `docs/ui/UI线路既往检查.md`; Project Control absorption docs | planned, not migrated | no |

## Required Before Execution

Before `MAINLINE-UI-RECOVERY-PLAN-20260529` can move from planned to execution:

- Confirm relationship between packaged preview `9d4edf3` and carryover HEAD `e13d0f5f5dfda36a5c60a00ddc7820748fa1677f`.
- Identify exact file scope for Shell baseline.
- Identify exact file scope for each Bioinformatics / Meta / LabTools page route.
- Classify LabTools page style page-by-page.
- Produce a conflict plan for shared UI foundation files.
- Confirm no `project_storage/` touch.
- Define tests for shell, module route, and page recovery.

## No-Migration Statement

This row is a planned migration record only. It does not move code, merge branches, cherry-pick commits, or approve whole-branch integration.
