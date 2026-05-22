# Bioinformatics B24.3 Renderer Runtime Packaging Policy

## Decision

B24.3 resolves the ReleaseBuild runtime policy for full integrated DOCX/PDF renderers.

ReleaseBuild does not bundle Pandoc, TeX, wkhtmltopdf, or Quarto. It does not download or install renderer tools. Renderer binaries stay external system dependencies and are detected only.

## DOCX

- Runtime provider: user/system installed Pandoc on the renderer search path.
- Bundled in ReleaseBuild: no.
- Activation status: disabled until an explicit DOCX renderer activation stage.
- Missing dependency behavior: graceful block with `renderer_dependency_missing:pandoc`.
- Current preflight remains preflight-only and still adds `full_integrated_docx_export_activation_required_b24_2`.
- No `.docx` file is created and no rendered artifact is registered.

## PDF

- Current activation status: disabled.
- Future selected backend, if explicitly activated: Pandoc + `xelatex`.
- Required dependencies when activated: `pandoc`, `xelatex`.
- `wkhtmltopdf` remains detect-only and is not selected as the formal full integrated statistical report backend.
- Quarto remains disabled / detect-only for this export path.

## Packaging

`scripts/package_app.py` writes `renderer_runtime_packaging_policy` into build metadata. The policy records:

- no external renderer bundling,
- no network downloads,
- no automatic installation,
- no third-party renderer binary redistribution under app codesign,
- package-size impact remains zero for external renderer payloads.

The packaged launcher exports:

- `BIOMEDPILOT_EXTERNAL_RENDERER_POLICY=b24_3_system_path_no_bundled_renderers`
- `BIOMEDPILOT_RENDERER_SEARCH_PATHS=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin`

The launcher prepends those paths to `PATH`, so `open -W` and Finder launches use the same detect-first system-path policy as source runs.

## Runtime Surfaces

The policy is exposed through:

- `build_full_integrated_renderer_runtime_packaging_policy()`
- `build_report_renderer_capability_snapshot()`
- `evaluate_full_integrated_report_renderer_gate()`
- `evaluate_full_integrated_docx_preflight_gate()`
- `build_full_integrated_report_package_plan()`

## Boundaries

- No Pandoc invocation.
- No DOCX generation.
- No PDF generation.
- No renderer artifact registration.
- No clinical diagnosis, prognosis, treatment recommendation, risk score, or nomogram.
- Markdown-only full integrated report package behavior is unchanged.

## Validation

Expected focused checks:

- `python3 -m pytest -q tests/bioinformatics/test_integrated_report_package.py`
- `python3 -m pytest -q tests/test_package_app.py`
- `python3 -m app.main --smoke-test`
- `git diff --check`
