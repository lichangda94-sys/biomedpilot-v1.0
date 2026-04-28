# Meta Analysis Internal Beta Readiness

BioMedPilot Meta Analysis is an internal beta candidate, not production software.

Current readiness:

- Developer Preview / testing status remains visible.
- Stage M sample inputs are available under `examples/meta_analysis_e2e_project/`.
- Project manifests can be generated at the project root.
- Reports and reproducibility packages include manifest references.
- Statistical applicability warnings are preserved for review.

Required validation before user handoff:

- Run `python3 -m app.main --smoke-test`.
- Run the unified test suite.
- Confirm sample project workflow produces manifests, report, figure paths, and reproducibility package.
- Confirm missing artifacts produce warnings, not crashes.

