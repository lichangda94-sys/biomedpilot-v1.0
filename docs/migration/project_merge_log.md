# BioMedPilot Project Merge Log

## 2026-04-28

Created branch:

- `codex/merge-biomedpilot`

Created unified target directories:

- `app/shell/`
- `app/shared/`
- `app/bioinformatics/`
- `app/meta_analysis/`
- `docs/migration/`
- `docs/user_testing/`
- `tests/bioinformatics/`
- `tests/meta_analysis/`
- `tests/shared/`
- `tests/integration/`
- `tests/ui/`
- `scripts/`
- `project_storage/`

Copied source snapshots:

- `/Users/changdali/Documents/New project` -> `app/bioinformatics/legacy/`
- `/Users/changdali/Documents/model9` -> `app/meta_analysis/legacy/`

Kept source projects read-only. No files were modified in either source project.

Added unified entry:

- `app/main.py`
- `scripts/run_app.py`

Added unified tests:

- `scripts/run_tests.py`
- `tests/test_unified_entry.py`
- `tests/bioinformatics/test_smoke.py`
- `tests/meta_analysis/test_smoke.py`
- `tests/shared/test_project_center.py`
- `tests/shared/test_task_center.py`
- `tests/integration/test_workspace_switching.py`
- `tests/ui/test_feature_availability.py`

Import changes:

- No legacy imports were rewritten.
- New shell imports only use `app.bioinformatics`, `app.meta_analysis`, and `app.shared`.
- `app/bioinformatics/adapters/legacy_geo.py` provides a subprocess adapter to the preserved GEO launcher.

Tests moved:

- No source tests were deleted.
- Original tests remain inside each legacy snapshot.
- New unified smoke tests were added under the target repository `tests/`.

Temporarily not connected:

- Full legacy Meta UI inside the new shell.
- Full legacy GEO GUI inside the new shell.
- Formal DEG/enrichment/statistical Meta execution.
- Packaging build.

Startup:

```bash
python -m app.main
python scripts/run_app.py
python -m app.main --smoke-test
```

Testing:

```bash
python scripts/run_tests.py
python -m pytest -q
```

Next steps:

1. Replace workspace status cards with adapter-backed entry buttons for stable legacy workflows.
2. Move selected legacy tests into isolated compatibility runners.
3. Add project metadata migration from legacy project formats.
4. Add packaging once the unified shell is accepted by testers.
