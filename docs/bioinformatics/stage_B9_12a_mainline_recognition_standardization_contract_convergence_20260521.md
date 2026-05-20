# Bioinformatics B9.12a MainLine Recognition / Standardization Contract Convergence

Date: 2026-05-21

## Scope

This audit covers the MainLine carry-over convergence needed before retrying the formal DEG MVP carry-over:

- integrated RNA-seq recognition and content-block standardization
- GEO Series Matrix / GEO expression recognition and comparison handoff
- TCGA expression, clinical metadata, and GDC manifest boundaries
- GTEx expression and sample metadata boundaries
- standardized asset selection and repository manifest generation
- group comparison / comparison_config convergence
- B8 analysis input resolver outputs from standardized repository / registry / analysis_input_repository

This stage does not enable GSEA, survival statistics, clinical conclusions, report-ready bypass, or any imported/testing/preflight upgrade to formal DEG.

## Merge Resolution

MainLine governance/package files were preserved for global app behavior:

- CODEX.md
- docs/architecture.md
- scripts/package_app.py
- tests/test_package_app.py

Bioinformatics B8/B9 modules were carried over, then reconciled with MainLine compatibility requirements:

- app/bioinformatics/project_recognition.py
- app/bioinformatics/project_standardization.py
- app/bioinformatics/deg_task_plan.py
- app/bioinformatics/results/project_results.py
- app/bioinformatics/reports/project_report_builder.py
- app/bioinformatics/analysis_ui/state.py
- app/bioinformatics/workflow_pages.py
- app/main.py

## Contract Convergence Results

| Area | Result | Evidence |
| --- | --- | --- |
| Integrated RNA-seq | Passed | Integrated tables produce count matrix, normalized expression, imported DEG result, and gene annotation assets with stable IDs. |
| GEO / Series Matrix | Passed | GEO ID_REF/probe assets remain blocked for formal DEG until mapping is available; group confirmation can create a group design asset without bypassing probe mapping. |
| TCGA | Passed | TCGA expression creates expression and sample metadata repository assets; clinical metadata is separated from GDC manifest/reference-only files. |
| GTEx | Passed | GTEx TPM expression and sample attributes converge into expression and sample metadata repositories. |
| Standardized asset selection | Passed | Multi-asset selection remains explicit; single candidate defaults are recorded without becoming formal analysis. |
| Group comparison | Passed | comparison_config and confirmed group preview converge into group_design repository assets for preflight/task planning. |
| B8 resolver | Passed | Resolver consumes standardized repository manifest, registry, and analysis_input_repository outputs; recognition_report.json is not used as the formal analysis input source. |
| Analysis UI state | Passed | Analysis UI result index access is read-only during state building via persist_generated=False. |
| Report manifest compatibility | Passed | B9 semantic fields and MainLine report manifest sections are both present; draft/report copy keeps imported and preflight results non-formal. |

## Boundary Checks

- Formal DEG remains limited to two-group controlled MVP paths already guarded by B9 gates.
- Imported DEG remains imported/exploratory and does not become BioMedPilot recomputed formal DEG.
- Preflight/testing/exploratory outputs do not become formal_computed_result.
- Plot/report-ready activation is not broadened by this convergence work.
- GSEA and survival remain disabled/design-only unless separately audited in later stages.

## Test Results

Commands run from MainLine:

- `git diff --check` passed.
- `python3 -m pytest tests/bioinformatics/test_recognition_compatibility_matrix.py tests/bioinformatics/test_standardized_asset_registry.py tests/bioinformatics/test_standardized_asset_selection.py tests/bioinformatics/test_group_comparison_design.py tests/bioinformatics/test_analysis_task_runs.py tests/bioinformatics/test_result_report_manifest.py -q` passed during targeted convergence.
- `python3 -m pytest tests/bioinformatics -q -k "analysis_input or resolver or deg_ready or formal_deg or analysis_ui"` passed: 47 passed, 367 deselected.
- `python3 -m pytest tests/bioinformatics -q` passed: 414 passed.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` passed: 197 passed.
- `python3 -m app.main --smoke-test` passed.
- `python3 scripts/package_app.py --smoke-test` passed.
- `open -W -n dist/BioMedPilot.app --args --smoke-test` passed.
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app` passed.

## Findings

Blockers: none.

Major issues fixed:

- Standardization now writes MainLine-compatible repository assets while preserving B9 repository manifest and analysis input package contracts.
- GEO/TCGA/GTEx recognition and standardization no longer collapse expression, metadata, clinical, or manifest records into the wrong repository role.
- count_matrix and raw_count_matrix are both accepted by downstream preflight and resolver gates.
- Report manifest generation keeps both B9 semantics and MainLine legacy section fields.

Minor issues fixed:

- Analysis UI state builder avoids writing generated result indexes while reading gate state.
- Project report draft copy explicitly avoids fake volcano/heatmap and keeps imported/preflight semantics clear.

## Conclusion

B9.12a passes. The recognition / standardization / group comparison / resolver convergence is sufficient to retry and complete MainLine formal DEG MVP carry-over under the existing B9 boundaries.

Recommended next step: complete the MainLine carry-over merge commit, then proceed to MainLine / ReleaseBuild carry-over audit only from this reconciled state.
