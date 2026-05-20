# Bioinformatics B9.8 Formal DEG Report-Ready Package UX / Review Audit

Date: 2026-05-20

## Scope

B9.8 audits and hardens the B9.7 formal DEG report-ready package UX. It does not add GSEA, survival, clinical association, or broader report sections.

## Package Completeness

The formal DEG package now includes:

- `formal_deg_report.md`
- `tables/` with the DEG result table copy
- `plots/` with formal plot artifact JSON files when plot artifacts exist
- `manifests/result_index_snapshot.json`
- `manifests/formal_deg_result_entry.json`
- `manifests/formal_deg_parameter_confirmation.json`
- `manifests/dependency_snapshot.json`
- `manifests/plot_artifacts.json`
- `manifests/gate_snapshot.json`
- `manifests/package_inventory.json`
- `manifests/provenance.json`
- `manifests/warnings.json`
- `logs/` with copied task-run logs when present
- `README_limitations.md`

## Stable Internal Paths

Each package root uses stable internal directories:

- `tables/`
- `plots/`
- `manifests/`
- `logs/`

To avoid overwriting existing exports, each export writes to a new timestamped directory under:

`report_package/formal_deg/<result_id>/<timestamp>/`

The manifest records:

- `package_path`
- `user_visible_package_path`
- `overwrite_policy=create_new_timestamped_package_directory`
- `package_inventory`

## Table-Only Mode UX

When table-only mode is explicitly enabled, the report includes a dedicated `Table-Only Report Mode` section:

- no plot artifact is included by explicit table-only mode
- this does not mean plot generation failed
- the report must not imply volcano or heatmap figures were generated

## UI Review

Results Browser now shows:

- package output path after successful export
- gate blocker/warning text when export fails
- confirmation timestamp
- dependency versions
- explicit table-only wording in the checkbox/status text

## Eligibility Review

The package includes `gate_snapshot.json`, `provenance.json`, and `package_inventory.json`, so reviewers can inspect:

- gate status
- blockers/warnings
- confirmation path and creation time
- dependency versions
- result index path
- DEG table path
- plot artifact count
- task-run log artifacts

## Boundaries

B9.8 preserves:

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
python3 -m pytest tests/bioinformatics/test_formal_deg_report_ready.py -q
python3 -m pytest tests/bioinformatics/test_formal_deg_plot_artifact.py tests/bioinformatics/test_report_ready_gate.py tests/bioinformatics/test_report_export_package.py -q
python3 -m pytest tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "results_browser or analysis_task or report"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```
