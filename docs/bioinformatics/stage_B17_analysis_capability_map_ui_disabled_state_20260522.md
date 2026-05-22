# Bioinformatics B17 Analysis Capability Map and UI Disabled State

Date: 2026-05-22

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`

Baseline: `59506d3 carry over Bioinformatics B16 legacy pipeline to ReleaseBuild`

Task source: `/Users/changdali/Desktop/bioinformatic/Bioinformatics_Deep_Analysis_Module_Plan.md`

## Goal

Implement the first deep-analysis planning stage: a UI-facing analysis capability map that makes current formal, controlled, planned, disabled, design-audit and spec-only capabilities explicit.

This stage prevents UI overclaiming. It does not add new formal execution.

## Implemented

New capability map contract:

- `app/bioinformatics/analysis_ui/capability_map.py`
- `build_analysis_capability_map(...)`
- Schema: `biomedpilot.deep_analysis_capability_map.v1`

The map covers:

- DEG two-group controlled MVP.
- limma.
- DESeq2.
- edgeR.
- multi-factor DEG.
- ORA controlled MVP.
- preranked GSEA controlled MVP.
- KM/log-rank controlled MVP.
- Cox univariate controlled MVP.
- Cox multivariate.
- risk score / nomogram.
- KM/Cox real plot artifact.
- full integrated report.
- legacy formal execution.

Analysis Center state now exposes:

- `analysis_capability_map`
- capability rows in `developer_diagnostics`
- external engine required capability keys for future handoff

Analysis Center UI now includes:

- `analysisCapabilityMapTable`
- capability label / category / implementation status / UI state / formal enablement / capability keys / reason

## External Engine Boundary

B17 only records capability keys. It does not detect, install, configure, or run external engines.

Initial keys represented in the map include:

- `runtime.r.available`
- `runtime.bioconductor.available`
- `package.r.limma.available`
- `package.r.deseq2.available`
- `package.r.edger.available`
- `package.r.survival.available`
- `package.r.glmnet.available`
- `package.python.matplotlib.available`
- `renderer.pandoc.available`
- `renderer.quarto.available`
- `renderer.latex.available`
- `renderer.wkhtmltopdf.available`

Dependency availability is explicitly not enough to mark a feature complete. R methods remain blocked/planned until B18/B19 contracts and adapters exist.

## Boundary Confirmation

B17 does not implement:

- limma execution.
- DESeq2 execution.
- edgeR execution.
- multi-factor DEG execution.
- Cox multivariate execution.
- risk score execution.
- real KM/Cox plot rendering.
- full integrated report generation.
- legacy formal execution.
- automatic dependency installation.
- clinical conclusion, prognosis or treatment recommendation.

No new code path writes `result_semantics=formal_computed_result`.

## UI Disabled State Checks

The capability map enforces:

- limma / DESeq2 / edgeR are not displayed as completed.
- Cox multivariate is design-audit / disabled, not completed.
- risk score is disabled.
- full integrated report is planned.
- KM/Cox real plot remains spec-only/planned.
- legacy formal execution remains disabled.
- every blocked/planned/disabled row has a reason and, where relevant, external capability keys.

## Tests

Focused validation run:

| Command | Result |
|---|---|
| `python3 -m py_compile app/bioinformatics/analysis_ui/capability_map.py app/bioinformatics/analysis_ui/state.py app/bioinformatics/workflow_pages.py` | passed |
| `python3 -m pytest tests/bioinformatics/test_analysis_capability_map.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py -q` | 20 passed |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task_center_userized_main_surface"` | 1 passed, 111 deselected |

Final validation:

| Command | Result |
|---|---|
| `git diff --check` | passed |
| `python3 -m pytest tests/bioinformatics -q -k "capability_map or analysis_ui or formal_deg or ora or gsea or survival or clinical or cox or km"` | 213 passed, 381 deselected |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or settings or results_browser or report"` | 17 passed, 95 deselected |
| `python3 -m app.main --smoke-test` | passed |
| `python3 -m pytest tests/bioinformatics -q` | 594 passed |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | 269 passed |
| `python3 scripts/package_app.py --smoke-test` | passed |
| `open -W -n dist/BioMedPilot.app --args --smoke-test` | passed |
| `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app` | passed |

## Issues

Blocker:

- None.

Major:

- None.

Minor:

- The capability map currently uses an optional in-memory `external_capabilities` dict. B19 should replace this with the formal external engine capability registry/snapshot handoff once E1/E2/E5/E6 exist.
- The UI table is contract-complete but visually dense; UI design should turn it into grouped cards or a compact status matrix.

## Conclusion

B17 is implemented as a UI/contract hardening layer. It is safe to enter B18 multi-factor DEG contract and preflight planning next.
