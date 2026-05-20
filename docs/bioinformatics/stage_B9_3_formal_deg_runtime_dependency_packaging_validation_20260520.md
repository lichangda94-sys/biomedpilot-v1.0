# Bioinformatics B9.3 Formal DEG Runtime Dependency Packaging / Real Environment Validation

Date: 2026-05-20

## Scope

B9.3 validates whether the controlled two-group formal DEG MVP can rely on real runtime dependencies in source and packaged application contexts. It does not add GSEA, survival, plotting, report-ready export, or any fallback statistical backend.

The validation covers:

1. Python runtime dependency declaration for numpy, pandas, scipy, and statsmodels.
2. Importability and version detection for source, packaged executable, and `open -W` LaunchServices entry.
3. A small controlled two-group fixture executed through the audited formal DEG runner, not a mocked backend.
4. Result index v2, task-run log, parameter manifest, and dependency snapshot completeness when the real backend runs.
5. Graceful blocked behavior when scipy or statsmodels is missing.
6. Packaged app size, startup behavior, and codesign verification impact.

## Implementation Notes

- `pyproject.toml` and `requirements.txt` now declare `numpy`, `pandas`, `scipy`, and `statsmodels` as runtime dependencies for formal DEG.
- `app.bioinformatics.deg_engine.runtime_validation.run_formal_deg_runtime_validation()` performs detect-first dependency checks, import checks, packaging context inspection, and a real controlled two-group fixture run.
- `python3 -m app.main --bio-formal-deg-runtime-check` exposes the same validation path to source and packaged app launches.
- Missing dependencies return `blocked_missing_dependency` with explicit blockers. The command exits 0 for this expected blocked state so packaging validation can capture JSON instead of failing with a traceback.

## Validation Matrix

| Environment | Command | Status | Evidence |
| --- | --- | --- | --- |
| Source Python | `python3 -m app.main --bio-formal-deg-runtime-check --bio-formal-deg-runtime-check-output /tmp/biomedpilot_b9_3_source.json` | `blocked_missing_dependency` | arm64; numpy 2.4.4 and pandas 3.0.2 import; scipy/statsmodels missing; fixture blocked gracefully. |
| Packaged executable | `dist/BioMedPilot.app/Contents/MacOS/BioMedPilot --bio-formal-deg-runtime-check --bio-formal-deg-runtime-check-output /tmp/biomedpilot_b9_3_packaged_direct.json` | `blocked_missing_dependency` | arm64 packaged-local-python launcher; same dependency result as source; bundle size 31,291,475 bytes. |
| LaunchServices | `open -W -n dist/BioMedPilot.app --args --bio-formal-deg-runtime-check --bio-formal-deg-runtime-check-output /tmp/biomedpilot_b9_3_open.json` | `blocked_missing_dependency` | arm64 after launcher hardening; same dependency result as source/direct packaged; elapsed 1.26s. |

## Expected Pass Criteria

- Dependency snapshot status is `passed`.
- scipy and statsmodels are importable with non-empty versions.
- The fixture produces numeric `p_value` and `adjusted_p_value`.
- The registered result index v2 entry is `formal_computed_result` and includes `input_package_id`, engine/version, dependency snapshot, parameter manifest, output artifact, log artifact, and passed validation status.
- The task-run log and result table exist.
- The packaged app validates through direct launcher and `open -W`.
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app` passes.

## Expected Blocked Criteria

If scipy or statsmodels is absent from the active runtime, B9.3 must remain blocked:

- No p-value or FDR is fabricated.
- The formal DEG runner returns blocked status.
- The UI and runtime checks expose explicit `missing_python_package:*` blockers.
- No traceback is required for normal missing-dependency behavior.

## Local Results

### Dependency Declaration

Formal DEG runtime requirements are now declared in both `pyproject.toml` and `requirements.txt`:

- `numpy>=1.26`
- `pandas>=2.0`
- `scipy>=1.11`
- `statsmodels>=0.14`

The app still uses a local-python `.app` launcher, so declaring dependencies does not vendor wheels into the bundle by itself. The packaged app depends on the target Python runtime having importable compatible packages.

### Dependency Detection

Dependency detection now requires actual import success, not only `importlib.find_spec()`. This is required for macOS native extension packages because a module can be discoverable but unusable under the wrong CPU architecture.

Observed states:

| Package | Source | Packaged direct | `open -W` |
| --- | --- | --- | --- |
| numpy | importable, 2.4.4 | importable, 2.4.4 | importable, 2.4.4 |
| pandas | importable, 3.0.2 | importable, 3.0.2 | importable, 3.0.2 |
| scipy | missing | missing | missing |
| statsmodels | missing | missing | missing |

Before launcher hardening, the `open -W` path ran as `x86_64` and numpy failed with an incompatible architecture import error. The launcher now probes and uses `/usr/bin/arch -arm64` on Apple Silicon when the selected Python supports arm64. After that change, source, direct packaged, and `open -W` all report `platform_machine=arm64`.

### Real Fixture Execution

The B9.3 runtime check creates a small standardized two-group project fixture and calls the audited formal DEG runner. In the current environment, the run is blocked before statistics:

- status: `blocked_missing_dependency`
- blockers: `missing_python_package:scipy`, `missing_python_package:statsmodels`
- graceful blocked: true
- p-value/FDR: not produced, correctly not fabricated

Because scipy/statsmodels are not importable, B9.3 cannot claim that real p-value and FDR execution passed in this environment.

### Packaging, Startup, Codesign

- `python3 scripts/package_app.py --smoke-test`: passed.
- `open -W -n dist/BioMedPilot.app --args --smoke-test`: passed.
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`: passed.
- `du -sk dist/BioMedPilot.app`: 33,088 KB.
- source smoke startup measured with `/usr/bin/time -p python3 -m app.main --smoke-test`: real 0.37s.
- `open -W` runtime validation measured with `/usr/bin/time -p`: real 1.26s.

The current package size does not include vendored scipy/statsmodels wheels because the bundle remains a local-python launcher.

## Test Commands

Passed:

```bash
git diff --check
python3 -m pytest tests/bioinformatics/test_deg_dependency_check.py tests/bioinformatics/test_formal_deg_runtime_validation.py -q
python3 -m pytest tests/test_package_app.py tests/test_versioned_packaged_entry.py -q
python3 -m pytest tests/bioinformatics -q -k "deg_dependency or formal_deg_runtime or formal_controlled_deg or deg_engine"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

Runtime validation commands:

```bash
python3 -m app.main --bio-formal-deg-runtime-check --bio-formal-deg-runtime-check-output /tmp/biomedpilot_b9_3_source.json
dist/BioMedPilot.app/Contents/MacOS/BioMedPilot --bio-formal-deg-runtime-check --bio-formal-deg-runtime-check-output /tmp/biomedpilot_b9_3_packaged_direct.json
open -W -n dist/BioMedPilot.app --args --bio-formal-deg-runtime-check --bio-formal-deg-runtime-check-output /tmp/biomedpilot_b9_3_open.json
```

All three runtime validation commands completed without traceback and returned `blocked_missing_dependency`.

## Issues

### Blockers

1. scipy is not importable in the source or packaged Python runtime.
2. statsmodels is not importable in the source or packaged Python runtime.
3. The `.app` is still a local-python launcher and does not bundle formal DEG wheels. B9.3 therefore cannot prove standalone packaged-app scipy/statsmodels reliability yet.
4. Real controlled DEG fixture execution did not produce p-value/FDR because dependency gates correctly blocked before computation.

### Major

1. The initial LaunchServices path exposed an architecture mismatch (`x86_64` process with arm64 numpy). The launcher now forces arm64 on Apple Silicon when supported, and the post-fix `open -W` runtime check reports arm64.

### Minor

1. Bundle size/startup impact of vendored scipy/statsmodels remains unmeasured because those wheels are not included in the current local-python app bundle.

## Conclusion

B9.3 is conditionally blocked. The validation harness, dependency declaration, import-level dependency gate, arm64 LaunchServices hardening, packaged runtime JSON check, and graceful missing-dependency behavior are implemented and tested. However, the current runtime does not include scipy/statsmodels, so B9.3 cannot certify real formal DEG p-value/FDR execution or packaged wheel reliability.

Do not advance to broader formal DEG rollout until a controlled environment with scipy/statsmodels installed or bundled passes the same three runtime validation commands with `status=passed`.
