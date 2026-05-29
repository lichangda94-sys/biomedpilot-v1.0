# MainLine Migration Ledger

Date: 2026-05-29

Purpose: record every scoped change accepted into `stable/mainline`.

## Migration Ledger

| Migration ID | Date | Target | Source | Migration Type | Migration Method | File Scope | Forbidden Path Check | Verification Commands | Verification Result | Audit Report | Closed? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ML-20260529-001 | 2026-05-29 | `stable/mainline` | `9d4edf3` packaged preview | shell decision | audit only | no code migrated | empty for audit output | provenance audit | passed/read-only | pending report file | no |

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
