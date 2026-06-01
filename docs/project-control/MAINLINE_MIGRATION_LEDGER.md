# MainLine Migration Ledger

Date: 2026-05-29

Purpose: record every scoped change accepted into `stable/mainline`.

## Migration Ledger

| Migration ID | Date | Target | Source | Migration Type | Migration Method | File Scope | Forbidden Path Check | Verification Commands | Verification Result | Audit Report | Closed? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ML-20260529-001 | 2026-05-29 | `stable/mainline` | `9d4edf3` packaged preview | shell decision | audit only | no code migrated | empty for audit output | provenance audit | passed/read-only | pending report file | no |
| MAINLINE-UI-RECOVERY-PLAN-20260529 | 2026-05-29 | `stable/mainline` | `codex/integration-labtools-ui-c2-carryover`; packaged preview `9d4edf3`; historical check `e13d0f5f5dfda36a5c60a00ddc7820748fa1677f` | shell + feature page recovery planning | scoped plan required | not selected | not run; no migration performed | not run; planning only | planned, not migrated | `docs/ui/UI线路既往检查.md`; Project Control absorption docs | no |
| MAINLINE-UI-ROUTE-CONTRACT-PHASE1-20260601 | 2026-06-01 | `integration/release-bio-c1-ui-shell` | current Integration HEAD `58d06df1b3d38c8c60ef3aba859f24088f76062c`; UI Shell baseline decision; release validation report | route contract rebuild, shared shell freeze, adapter-bound module recovery plan | Phase 1 plan created | not selected | not run; plan only | not run; plan only | planned, not migrated | `docs/project-control/UI_ROUTE_CONTRACT_PHASE1_PLAN.md`; `docs/release_validation/20260601_ui_shell_and_live_validation.md` | no |

## Required Before Any New Row Is Closed

- `git diff --stat`
- `git diff --name-status`
- `git diff --check`
- Forbidden path check:

```bash
git diff --name-status | grep -E 'app/bioinformatics/|app/labtools/|app/meta_analysis/legacy/|scripts/package_app.py|requirements.txt|pyproject.toml|project_storage/' || true
```

- Module-specific tests for any touched module.
- Post-merge or post-migration audit if accepted into `stable/mainline`.

`MAINLINE-UI-RECOVERY-PLAN-20260529` is a planned row only. It does not move code, merge branches, cherry-pick commits, or approve whole-branch integration.
