# Bioinformatics B23.2 Full Integrated Report Package Skeleton

Date: 2026-05-22

## Scope

B23.2 adds the full integrated report package skeleton API while preserving the B23.1 full integrated report gate boundary.

This stage does not enable full integrated report export in normal runtime because the gate is still blocked by missing survival/clinical report-ready support.

## Implemented Files

- `app/bioinformatics/reports/integrated.py`
- `app/bioinformatics/reports/__init__.py`
- `tests/bioinformatics/test_integrated_report_package.py`
- `docs/bioinformatics/stage_B23_2_full_integrated_report_package_skeleton_20260522.md`

## API

New functions:

- `create_full_integrated_report_package(project_root, section_result_ids=None, include_sections=None, export_format="markdown")`
- `build_full_integrated_report_package_plan(project_root, gate=None, export_format="markdown")`

The package function always evaluates the B23.1 gate first.

If the gate is blocked, it returns:

- `status=blocked`
- empty `package_path`
- empty `user_visible_package_path`
- gate snapshot
- package layout plan
- blockers and warnings

No directories are written when the gate is blocked.

## Package Layout

Planned package root:

- `report_package/integrated/<timestamp>_<project_name>/`

Required directories:

- `sections/`
- `tables/`
- `plots/`
- `manifests/`
- `logs/`
- `provenance/`

Required files:

- `integrated_report.md`
- `README_limitations.md`
- `integrated_report_package_manifest.json`
- `manifests/full_integrated_gate_snapshot.json`
- `manifests/result_index_snapshot.json`
- `manifests/section_manifest.json`
- `manifests/dependency_snapshot.json`
- `manifests/warnings_limitations.json`
- `manifests/package_inventory.json`

## Artifact Policy

The skeleton copies only registered artifacts:

- source result `output_artifacts` to `tables/`
- registered plot artifacts and image artifacts to `plots/`
- task-run `log_artifacts` to `logs/`
- gate/result/section/dependency/warnings snapshots to `manifests/`

It does not copy runner temp files.

Forbidden sources remain:

- `preflight_only`
- `testing_level`
- `exploratory`
- `imported_external_result`
- legacy-only acquisition/standardization outputs

## Renderer Policy

B23.2 allows only Markdown package creation after the full integrated gate passes.

PDF/DOCX and other formats are blocked with:

- `full_integrated_export_format_not_enabled:<format>`

No renderer is installed or invoked.

## Current Runtime Status

Normal runtime remains blocked because B23.1 gate includes:

- `survival_clinical_report_ready_not_implemented`
- `full_integrated_report_export_not_enabled_in_b23_1`

This is intentional. The skeleton write path is covered by a test-stubbed passed gate only to verify package structure and non-overwriting behavior.

## Preserved Boundaries

- No full integrated package is created from current real project state.
- Section-only DEG/ORA/GSEA report packages are not upgraded.
- KM/Cox formal results and real SVG plot artifacts do not enable survival report-ready.
- No clinical diagnosis, prognosis, treatment recommendation, or risk score interpretation is produced.
- No PDF/DOCX renderer is activated.
- No dependency auto-install action is added.

## Validation

Focused validation completed:

- `python3 -m py_compile app/bioinformatics/reports/integrated.py app/bioinformatics/reports/__init__.py`
  - passed
- `python3 -m pytest tests/bioinformatics/test_integrated_report_gate.py tests/bioinformatics/test_integrated_report_package.py -q`
  - 8 passed

Full validation is recorded in the final completion report.

Full validation completed:

- `git diff --check`
  - passed
- `python3 -m pytest tests/bioinformatics -q -k "integrated or report or formal_deg or ora or gsea or survival or cox or plot or analysis_ui or capability_map"`
  - 247 passed, 390 deselected
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "report or results_browser or analysis_task"`
  - 16 passed, 96 deselected
- `python3 -m pytest tests/bioinformatics -q`
  - 637 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - 269 passed
- `python3 -m app.main --smoke-test`
  - passed
- `python3 scripts/package_app.py --smoke-test`
  - passed
- `open -W -n dist/BioMedPilot.app --args --smoke-test`
  - passed
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`
  - passed

## Conclusion

B23.2 provides an auditable package skeleton and stable package plan, but full integrated export remains disabled until the B23 gate can pass in a later audited stage.
