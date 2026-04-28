# Stage Y Internal Beta Desktop Package Check Report

## Goal

Confirm that internal beta users can start the desktop application through the app entry path, not only command-line service tests.

## Checks

- `python3 -m app.main --smoke-test`: passed.
- `python3 scripts/package_app.py --smoke-test`: passed.
- Package smoke output app path: `/Users/changdali/Documents/BioMedPilot/dist/BioMedPilot.app`.
- Package mode: local Python launcher.
- Standalone app: false.
- Network downloads during package smoke: false.

## Findings

- App startup smoke reports two workspace entries and seven Meta Analysis feature entries.
- PySide6 is available in the checked environment.
- The package smoke can create/check the local Mac app bundle path.
- No packaging, shell, script, or launcher files were modified in this stage.

## Remaining Internal Beta Risks

- The bundle is a local Python launcher, not a standalone production installer.
- Version and title are acceptable for internal beta but should be reviewed before external distribution.
- Real project restoration should be manually spot-tested by a human tester after the RC commit.

## Validation

- `python -m compileall -q .`: not available in local shell (`python` command missing).
- `pytest -q`: not available in local shell (`pytest` command missing).
- `/Users/changdali/Documents/model9/.venv/bin/python -m compileall -q .`: passed.
- `/Users/changdali/Documents/model9/.venv/bin/python -m pytest -q`: 279 passed.
- `/Users/changdali/Documents/model9/.venv/bin/python scripts/run_tests.py`: 279 passed.
- `python3 -m app.main --smoke-test`: passed.
- `python3 scripts/package_app.py --smoke-test`: passed.
