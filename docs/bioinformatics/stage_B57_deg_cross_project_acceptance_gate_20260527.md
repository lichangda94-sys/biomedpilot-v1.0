# B57 DEG Cross-Project Consistency Acceptance

## Audit

The DEG line had individual gates, but no single acceptance matrix to verify that local count, TCGA-like count, GEO microarray, TPM/log, batch-confounded, sample-mismatch, and missing-dependency scenarios produce stable readiness decisions.

## Implementation

- Added `biomedpilot.deg_cross_project_acceptance_gate.v1`.
- Each scenario runs DEG-ready, real-project input adaptation, design QA, data quality, method recommendation, and dependency status checks.
- The aggregate gate reports passed and blocked scenarios with stable blockers.
- Positive count fixtures can pass all gates without creating a formal result.
- Negative fixtures block deterministically for unmapped GEO probes, TPM count-model requests, batch confounding, sample mismatch, and missing dependencies.

## Boundaries

- The acceptance gate is not execution.
- Passing acceptance only means formal result creation may proceed through the existing runner, confirmation, and result index gates.
- No GSEA, survival, plotting, report-ready, clinical conclusion, or automatic dependency installation was added.

## Stage Result

B57 adds cross-project consistency coverage for DEG production-readiness candidates.

## Validation

- `python3 -m pytest tests/bioinformatics/test_deg_cross_project_acceptance_gate.py -q`: passed.
- `python3 -m pytest tests/bioinformatics -q -k "deg or analysis_ui or result_index or report_ready"`: passed.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or results_browser"`: passed.
- `python3 -m pytest tests/bioinformatics -q`: 455 passed.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`: 177 passed.
- `python3 scripts/package_app.py --smoke-test`: passed.
- `open -W -n dist/BioMedPilot.app --args --smoke-test`: passed.
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`: passed.
- `python3 scripts/releasebuild_formal_deg_gate.py --skip-full-tests --json-output /tmp/biomedpilot_deg_production_gate.json`: not run in this worktree because the script is absent.
