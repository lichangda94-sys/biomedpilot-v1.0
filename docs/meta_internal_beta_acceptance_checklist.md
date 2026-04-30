# Meta Internal Beta Acceptance Checklist

Status: Developer Preview / testing.

Use this checklist before handing a BioMedPilot build to an internal tester.

| Area | Check | Expected Result | Status |
| --- | --- | --- | --- |
| Desktop entry | Open `/Users/changdali/Desktop/BioMedPilot.app` | Opens BioMedPilot, not an old Meta-only app | Required |
| Source smoke | Run `python3 -m app.main --smoke-test` | Prints app version, channel, source launch mode, app root, git head | Required |
| Packaged smoke | Run `/Users/changdali/Desktop/BioMedPilot.app/Contents/MacOS/BioMedPilot --smoke-test` | Prints same version/channel and packaged launch mode | Required |
| Build metadata | Inspect `Contents/Resources/app/BUILD_INFO.json` | Contains version, bundle version, channel, launch mode, source root, git head | Required |
| Bundle metadata | Inspect `Contents/Info.plist` | Contains version, channel, git head, display name | Required |
| Dashboard | Open BioMedPilot Dashboard | Header shows `0.1.0-internal-beta · Developer Preview / testing` | Required |
| Meta workflow | Open Meta workflow dashboard | Shows 15 workflow steps with warning-based status | Required |
| Empty project | Open a new/empty Meta project | Missing artifacts produce warnings, not crashes | Required |
| Treatment sample | Validate treatment-effect sample manifest | Sample source files and expected manifest pass validation | Required |
| Biomarker sample | Validate biomarker/prevalence/correlation sample manifest | Sample source files and expected manifest pass validation | Required |
| Analysis artifacts | Generate analysis plan, dataset, result, and applicability warnings in a temp project | Artifacts exist under `analysis/` | Required |
| PRISMA artifacts | Generate PRISMA summary, markdown, and simplified SVG | Numbers trace to import/dedup/screening/full-text/final included sources | Required |
| Report artifact | Generate internal beta report | Report includes Developer Preview/testing disclaimer and artifact references | Required |
| Reproducibility package | Generate reproducibility ZIP in temp project | ZIP contains manifests and report manifest | Required |
| Feature status | Review Meta feature availability | All Meta features remain testing, not production/open | Required |
| Known limitations | Open limitations docs | Automatic PDF download, OCR, production PDF, AI auto-overwrite, and advanced methods limits are explicit | Required |

## Required Commands

```bash
python3 -m compileall -q .
python3 -m pytest -q
python3 scripts/run_tests.py
python3 -m app.main --smoke-test
python3 scripts/package_app.py --no-clean --smoke-test
/Users/changdali/Desktop/BioMedPilot.app/Contents/MacOS/BioMedPilot --smoke-test
```

If using the legacy model9 virtual environment for compatibility validation:

```bash
'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .
'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q
'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py
```

## Acceptance Rule

The build may be called an internal beta candidate only if the commands above pass or any failure is documented as a known blocker. It must not be described as production-ready.
