# Bioinformatics B9.3b Formal DEG Controlled Runtime Validation

Date: 2026-05-20

## Scope

B9.3b validates the B9.3 runtime harness in a controlled Python runtime where scipy and statsmodels are installed. The scope remains controlled two-group DEG MVP only.

Out of scope:

- No GSEA activation.
- No survival statistics.
- No formal plotting activation.
- No report-ready activation.
- No fake fallback statistics.

## Controlled Runtime

Runtime path:

```bash
/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/.venv-b9-3b/bin/python
```

Installed formal DEG runtime packages:

| Package | Version | Status |
| --- | --- | --- |
| numpy | 2.4.6 | importable |
| pandas | 3.0.3 | importable |
| scipy | 1.17.1 | importable |
| statsmodels | 0.14.6 | importable |

Python: 3.14.4

Architecture: arm64

Note: this venv was created as a local controlled validation runtime and is not committed. PySide6 full UI wheels were not installed because B9.3b validates formal DEG runtime dependencies, not GUI runtime packaging. Package smoke and `open -W` smoke still passed in console smoke mode.

## Runtime Validation Results

| Environment | Command | Status | Architecture |
| --- | --- | --- | --- |
| Source | `.venv-b9-3b/bin/python -m app.main --bio-formal-deg-runtime-check --bio-formal-deg-runtime-check-output /tmp/biomedpilot_b9_3b_source.json` | passed | arm64 |
| Packaged executable | `dist/BioMedPilot.app/Contents/MacOS/BioMedPilot --bio-formal-deg-runtime-check --bio-formal-deg-runtime-check-output /tmp/biomedpilot_b9_3b_packaged_direct.json` | passed | arm64 |
| LaunchServices | `open -W -n dist/BioMedPilot.app --args --bio-formal-deg-runtime-check --bio-formal-deg-runtime-check-output /tmp/biomedpilot_b9_3b_open.json` | passed | arm64 |

All three environments used the same formal DEG runtime dependency policy and reported:

- dependency snapshot status: `passed`
- missing packages: none
- install action: `none_detect_first_only`
- numpy/pandas/scipy/statsmodels import checks: passed

## Controlled DEG Fixture

The B9.3b runtime check creates a temporary standardized two-group fixture and runs the audited controlled formal DEG runner.

Observed in source, packaged direct, and `open -W` runs:

- fixture status: `passed`
- result semantics: `formal_computed_result`
- result rows: 3
- p-value present: yes
- adjusted p-value/FDR present: yes
- result index v2 status: `passed`
- result index registry path: `results/summaries/result_index.json`
- task-run log present: yes
- parameters manifest status: `passed`
- dependency snapshot status: `passed`
- blockers: none

Boundary checks:

- `plot_artifacts=[]`
- `report_artifacts=[]`
- `report_ready_eligible=False`
- no GSEA/survival/formal plot/report-ready activation
- no fallback statistics used

## Packaging Evidence

Packaging command:

```bash
python3 scripts/package_app.py --python "$PWD/.venv-b9-3b/bin/python" --smoke-test
```

Result:

- package mode: `local-python-launcher`
- package Python: `.venv-b9-3b/bin/python`
- package smoke: passed
- `open -W -n dist/BioMedPilot.app --args --smoke-test`: passed
- codesign: passed
- bundle size: 33,096 KB
- packaged executable smoke time: real 0.27s
- `open -W` runtime validation time: real 1.51s

The bundle remains a local-python launcher. scipy/statsmodels are validated through the controlled venv bound into the launcher, not as vendored wheels inside the `.app` bundle.

## Test Commands

Passed:

```bash
git diff --check
.venv-b9-3b/bin/python -m pytest tests/bioinformatics/test_formal_deg_runtime_validation.py tests/bioinformatics/test_deg_dependency_check.py -q
.venv-b9-3b/bin/python -m app.main --bio-formal-deg-runtime-check --bio-formal-deg-runtime-check-output /tmp/biomedpilot_b9_3b_source.json
python3 scripts/package_app.py --python "$PWD/.venv-b9-3b/bin/python" --smoke-test
dist/BioMedPilot.app/Contents/MacOS/BioMedPilot --bio-formal-deg-runtime-check --bio-formal-deg-runtime-check-output /tmp/biomedpilot_b9_3b_packaged_direct.json
open -W -n dist/BioMedPilot.app --args --bio-formal-deg-runtime-check --bio-formal-deg-runtime-check-output /tmp/biomedpilot_b9_3b_open.json
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

## Conclusion

B9.3b passed for the controlled local-python runtime. Source runtime check, packaged executable runtime check, and `open -W` runtime check all returned `status=passed`; the real controlled DEG fixture produced p-value and adjusted p-value; result index v2 and task-run provenance fields were present; and plot/report/report-ready remained disabled.

Recommended next stage: B9.4 Formal DEG User Parameter Confirmation Flow.
