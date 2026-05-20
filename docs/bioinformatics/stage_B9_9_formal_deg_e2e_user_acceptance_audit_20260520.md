# Bioinformatics B9.9 Formal DEG End-to-End User Acceptance Audit

Date: 2026-05-20

## Scope

B9.9 audits the full formal DEG user path:

`confirmation -> run formal DEG -> review result -> generate plot artifact -> pass report-ready gate -> export report package`

This stage is audit / gate hardening only. It does not add GSEA, survival, clinical association, clinical conclusions, or treatment recommendations.

## Audit Helper

Added `audit_formal_deg_e2e_acceptance` in `app/bioinformatics/reports/e2e_audit.py`.

The audit is read-only and checks:

- user-visible step status exists for formal DEG, review, plot gate, report gate, and package
- formal DEG action has clear enabled/disabled state and disabled reason
- parameter confirmation output plan traces to result id
- result id traces to result review and report package
- result review row count matches source result table and packaged table
- formal plot artifact is registered and packaged, unless explicit table-only mode is used
- table-only wording does not imply failed plotting or generated volcano/heatmap
- export path is visible, stable, and non-overwriting
- failure diagnostics expose dependency, expired confirmation, missing plot, and invalid table blockers
- package content is independently reviewable
- `report_ready_eligible=True` only appears after B9.7 gate pass
- imported/testing/exploratory/preflight outputs are not upgraded
- statistical-only / no clinical conclusion boundaries remain visible

## Acceptance Results

Implemented tests cover:

- full successful user flow
- missing formal plot artifact blocker
- explicit table-only report mode
- expired confirmation + failed dependency + invalid result table blockers

## UX Findings

Current UI provides:

- Analysis Center gate rows for formal DEG execution, plot eligibility, and formal DEG report-ready
- Results Browser formal DEG review summary and provenance
- formal plot artifact generation status
- formal report-ready status with confirmation timestamp and dependency versions
- export success message including package output path
- export failure message including blockers

## Package Review

B9.8 package hardening remains valid:

- `formal_deg_report.md`
- `tables/`
- `plots/`
- `manifests/`
- `logs/`
- `README_limitations.md`
- result index snapshot
- gate snapshot
- package inventory
- provenance
- warnings/limitations

## Boundaries

B9.9 preserves:

- formal DEG statistical result only
- no clinical conclusion
- no treatment recommendation
- no GSEA interpretation
- no survival/KM/Cox/log-rank/HR interpretation
- no imported/testing/exploratory/preflight upgrade into formal report-ready

## Validation

Expected validation commands:

```bash
git diff --check
python3 -m pytest tests/bioinformatics/test_formal_deg_e2e_acceptance_audit.py -q
python3 -m pytest tests/bioinformatics -q -k "formal_deg_e2e or formal_deg_report or formal_deg_plot or formal_controlled_deg or parameter_confirmation or analysis_ui"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "results_browser or analysis_task or report"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```
